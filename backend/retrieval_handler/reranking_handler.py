import sys
sys.path.append("..")
from concurrent.futures import ThreadPoolExecutor, as_completed
from base import RetrievedDocument, BaseLLM, IRerankingHandler
from .utils import re_0_10_rating
import asyncio
SYSTEMPROMPT_RERANKING = """You are a RELEVANCE grader; providing the relevance of the given CONTEXT to the given QUESTION.
        Respond only as a number from 0 to 10 where 0 is the least relevant and 10 is the most relevant.

        A few additional scoring guidelines:

        - Long CONTEXTS should score equally well as short CONTEXTS.

        - RELEVANCE score should increase as the CONTEXTS provides more RELEVANT context to the QUESTION.

        - RELEVANCE score should increase as the CONTEXTS provides RELEVANT context to more parts of the QUESTION.

        - CONTEXT that is RELEVANT to some of the QUESTION should score of 2, 3 or 4. Higher score indicates more RELEVANCE.

        - CONTEXT that is RELEVANT to most of the QUESTION should get a score of 5, 6, 7 or 8. Higher score indicates more RELEVANCE.

        - CONTEXT that is RELEVANT to the entire QUESTION should get a score of 9 or 10. Higher score indicates more RELEVANCE.

        - CONTEXT must be relevant and helpful for answering the entire QUESTION to get a score of 10.

        - Never elaborate."""

USER_PROMPT_TEMPLATE = """QUESTION: {question}

    CONTEXT: {context}

    RELEVANCE: """


class RerankingHandler(IRerankingHandler):
    def __init__(self, llm:BaseLLM):
        self.llm = llm
        self.threshold = 0.8

    async def rerank_documents(self, query:str, documents:list[RetrievedDocument]) -> list[RetrievedDocument]:
        filtered_documents = []
        documents = sorted(documents, key=lambda x: x.content)
        async def process_document(doc):
            messages = [
                {"role": "system", "content": SYSTEMPROMPT_RERANKING},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(question=query, context=doc.content)}
            ]
            result = await self.llm.generate_response(messages)
            return result
        with ThreadPoolExecutor() as executor:
            futures = []
            for doc in documents:
                futures.append(executor.submit(lambda: asyncio.run(process_document(doc))))
        results = [future.result() for future in as_completed(futures)]
        print(results)
        results = [
            (r_idx, float(re_0_10_rating(result)) / 10)
            for r_idx, result in enumerate(results)
        ]

        results.sort(key=lambda x: x[1], reverse=True)
        for r_idx, score in results:
            doc = documents[r_idx]
            doc.metadata["llm_trulens_score"] = score
            filtered_documents.append(doc)
        filtered_documents = [doc for doc in filtered_documents if doc.metadata["llm_trulens_score"] >=self.threshold]
        print(
            "LLM rerank scores",
            [doc.metadata["llm_trulens_score"] for doc in filtered_documents])
        return filtered_documents

