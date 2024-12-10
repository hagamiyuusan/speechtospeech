import sys
sys.path.append("..")
from typing import List
from base import  BaseLLM, RetrievedDocument, IRAGHandler, IRetriever
# from .retriever_handler import IRetriever

@staticmethod
def prepare_envidence(docs:List[RetrievedDocument]):
    text_evidence = ""
    for retrieved_document in docs:
            if retrieved_document.text not in text_evidence:
                text_evidence += (
                        f"<br><b>Content from {retrieved_document.metadata['file_name']}: </b> "
                        + retrieved_document.text
                    + " \n<br>"
                )
    return text_evidence

SYSTEM_PROMPT_RAG = """You are the chatbot for the ASEAN center, specializing in ASEAN information.
Your task is to provide information and support to users who have questions about ASEAN with provided context."""

USER_PROMPT_RAG = """Use the following pieces of context to answer the question at the end in detail with clear explanation.
If you don't know the answer, just say that you don't know, don't try to make up an answer. Give answer in Vietnamese
{context}
Question: {question}
Helpful Answer:"""

class RAGHandler(IRAGHandler):
    def __init__(self, retriever:IRetriever, llm:BaseLLM):
        self.retriever = retriever
        self.llm = llm

    async def generate_response(self, table_name:str, query:str, top_k:int = 10, model_name:str = "gpt-4o"):
        documents = await self.retriever.retrieve(table_name, query, top_k)
        evidence = prepare_envidence(documents)
        rag_template = []
        rag_template.append({"role": "system", "content": SYSTEM_PROMPT_RAG})
        rag_template.append({"role": "user", "content": USER_PROMPT_RAG.format(context=evidence, question=query)})
        response = await self.llm.generate_response(messages=rag_template, model_name=model_name)
        return response

        
    

