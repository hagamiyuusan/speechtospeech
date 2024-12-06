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
    def __init__(self,path: str = "./vectorstore"):
        self.chroma_client = chromadb.PersistentClient(path=path)
        self._collections = {}

    
    def get_collection(self, collection_name: str):
        if collection_name not in self._collections:
            chrome_collection = self.chroma_client.get_or_create_collection(collection_name)
            vector_store = ChromaVectorStore(chroma_collection=chrome_collection, stores_text=True)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            self._collections[collection_name] = storage_context
        return self._collections[collection_name]


    def add_documents(self, collection_name: str, documents: List[DocumentWithEmbedding] | list[list[float]] ):
            vector_store = self.get_collection(collection_name)
            if isinstance(documents[0], list):
                nodes: list[DocumentWithEmbedding] = [
                    DocumentWithEmbedding(embedding=embedding) for embedding in documents
                ]
            else:
                nodes = documents  
            for node in nodes:
                node.relationships = {
                    NodeRelationship.SOURCE: RelatedNodeInfo(node_id=node.id_)
                }
            return vector_store.add(nodes=nodes)


    def query(self, collection_name: str, query_embedding, top_k: int = 10) :
        vector_store = self.get_collection(collection_name)
        results = vector_store.query(
            query=VectorStoreQuery(query_embedding=query_embedding, similarity_top_k=top_k)
        )
        embeddings = []
        if results.nodes:
            for node in results.nodes:
                embeddings.append(node.embedding)
        similarities = results.similarities if results.similarities else []
        out_ids = results.ids if results.ids else []
        return embeddings, similarities, out_ids