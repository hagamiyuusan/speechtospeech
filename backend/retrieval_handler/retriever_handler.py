from pathlib import Path
import sys
sys.path.append("..")
from concurrent.futures import ThreadPoolExecutor
from base import Document, RetrievedDocument, IRetriever
from typing import List
from .docstore_handler import DocumentStoreHandler
from .vectorstore_handler import VectorStoreHandler
from .embedding_handler import OpenAIEmbedder
from .reranking_handler import RerankingHandler
from .reader import UnstructuredReader
from .utils import splitDocument
# class IRetriever(ABC):
#     @abstractmethod
#     def retrieve(self, query: str, top_k: int) -> List[RetrievedDocument]:
#         pass

class HybridRetriever(IRetriever):
    def __init__(self, vector_store: VectorStoreHandler,
                 document_store: DocumentStoreHandler,
                 embedder: OpenAIEmbedder,
                 reranker: RerankingHandler,
                 reader: UnstructuredReader):
        self.vector_store = vector_store
        self.document_store = document_store
        self.embedder = embedder
        self.reranker = reranker
        self.reader = reader
        self.chunk_batch_size = 200



    def add_documents(self, file_path: Path, table_name: str):
        docs = self.reader.load_data(file_path)
        all_chunks = splitDocument(docs)
        print("Splitted into ",len(all_chunks),"chunks")
        chunks = []
        n_chunks = 0
        chunk_size = self.chunk_batch_size * 4
        for start_idx in range(0, len(all_chunks), chunk_size):
            chunks = all_chunks[start_idx : start_idx + chunk_size]
            self.document_store.add_documents(table_name, chunks)
            docsWithEmbedding = self.embedder.get_embedding(chunks)
            self.vector_store.add_documents(table_name, docsWithEmbedding)



    async def retrieve(self, table_name: str,  query: str, top_k: int = 10) -> List[RetrievedDocument]:
        vs_docs = []
        vs_ids = []
        vs_scores = [] 
        ds_docs: list[RetrievedDocument] = []
        def query_vector_store():
            nonlocal vs_docs , vs_ids, vs_scores
            query_embedding = self.embedder.get_embedding(query)[0].embedding
            _, vs_scores, vs_ids = self.vector_store.query(table_name, query_embedding, top_k)
            print(f"vs_ids: {vs_ids}")
            print(f"vs_scores: {vs_scores}")
            if vs_ids:
                vs_docs = self.document_store.get_document(table_name, vs_ids)

        def query_document_store():
            nonlocal ds_docs
            if self.document_store is not None:
                ds_docs = self.document_store.query(table_name, query, top_k)

        with ThreadPoolExecutor() as executor:
            future_vs = executor.submit(query_vector_store)
            future_ds = executor.submit(query_document_store)
        
            future_vs.result()
            future_ds.result()
        
        print(f"ds_docs: {len(ds_docs)}")
        print(f"vs_docs: {len(vs_docs)}")
        differences = [doc.id_ for doc in ds_docs if doc.id_ in vs_ids]



        not_in_vs = [
            RetrievedDocument(**doc.to_dict(),score=-1.0) for doc in ds_docs 
            if doc.id_ not in vs_ids]
        combine_not_in_vs_and_vs = [
            RetrievedDocument(**doc.to_dict(),score=score) for doc,score in zip(vs_docs,vs_scores)
        ]
        sort_by_score = sorted(combine_not_in_vs_and_vs, key=lambda x: x.score, reverse=True)
        reranked = await self.reranker.rerank_documents(query, sort_by_score)
        results = reranked[:top_k]
        return results

