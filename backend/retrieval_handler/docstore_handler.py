
import sys
sys.path.append("..")
from abc import ABC, abstractmethod
from base import Document
from typing import List
import json
import lancedb
from base import IDocumentStore

class DocumentStoreHandler(IDocumentStore):
    def __init__(self, uri, table_name, top_k=10):
        self.connection = lancedb.connect(uri)
        self.table_name = table_name
        self.top_k = top_k 


    def query(self, query: str, top_k: int = 10) -> List[Document]:
        document_collection = self.connection.open_table(self.table_name)
        results = document_collection.search(query, query_type="fts").limit(top_k).to_list()
        return [
            Document(
                id_=doc["id"],
                text=doc["text"] if doc["text"] else "<empty>",
                metadata=json.loads(doc["attributes"]),
            )
            for doc in results
        ]
    
    def add_documents(self, docs: List[Document]):
        doc_ids = [doc.doc_id for doc in docs]
        data: list[dict[str, str]] | None = [
                {
                    "id": id,
                    "text": doc.text,
                    "attributes": json.dumps(doc.metadata),
                }
                for id, doc in zip(doc_ids, docs)
            ]
        if self.table_name not in self.connection.table_names():
            if data:
                schema = {
                    "id": str,
                    "text": str,  # The column for full-text search
                    "attributes": str,
                }
                self.connection.create_table(name=self.table_name, data=data, mode="overwrite")
                document_collection = self.connection.open_table(self.table_name)
                document_collection.create_fts_index("text", tokenizer_name="en_stem", use_tantivy=True, replace=True)

        else:
            document_collection = self.connection.open_table(self.table_name)
            if data:
                document_collection.add(data)
                document_collection.create_fts_index("text", tokenizer_name="en_stem", use_tantivy=True, replace=True)
    
    def get_document(self, doc_ids: str) -> List[Document]:
        if not isinstance(doc_ids, list):
            doc_ids = [doc_ids]
        id_filter = ", ".join([f"'{_id}'" for _id in doc_ids])
        query_filter = f"id in ({id_filter})"
        try:
                document_collection = self.connection.open_table(self.table_name)
                query_filter = f"id in ({id_filter})"
                docs = (
                    document_collection.search()
                    .where(query_filter)
                    .limit(10000)
                    .to_list()
                )
        except (ValueError, FileNotFoundError):
            docs = []
        return [
            Document(
                id_=doc["id"],
                text=doc["text"] if doc["text"] else "<empty>",
                metadata=json.loads(doc["attributes"]),
            )
            for doc in docs
        ]