import sys
sys.path.append("..")
import chromadb
from llama_index.core import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.vector_stores.types import VectorStoreQuery
from base import Document, DocumentWithEmbedding
from typing import List
from base import IVectorStore
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo

class VectorStoreHandler(IVectorStore):
    def __init__(self, collection_name: str, path: str = "./vectorstore"):
        self.chroma_client = chromadb.PersistentClient(path=path)
        self.chroma_collection = self.chroma_client.get_or_create_collection(collection_name)
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection, stores_text=True)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    def add_documents(self, documents: List[DocumentWithEmbedding] | list[list[float]] ):
            if isinstance(documents[0], list):
                nodes: list[DocumentWithEmbedding] = [
                    DocumentWithEmbedding(embedding=embedding) for embedding in documents
                ]
            else:
                nodes = documents  # type: ignore
            
            for node in nodes:
                node.relationships = {
                    NodeRelationship.SOURCE: RelatedNodeInfo(node_id=node.id_)
                }
            return self.vector_store.add(nodes=nodes)


    def query(self, query_embedding, top_k: int = 10) :
        results = self.vector_store.query(
            query=VectorStoreQuery(query_embedding=query_embedding, similarity_top_k=top_k)
        )
        embeddings = []
        if results.nodes:
            for node in results.nodes:
                embeddings.append(node.embedding)
        similarities = results.similarities if results.similarities else []
        out_ids = results.ids if results.ids else []
        return embeddings, similarities, out_ids