
import sys
sys.path.append("..")

from openai import OpenAI
from base import Document, DocumentWithEmbedding, IEmbedder
from .utils import prepare_input, split_text_by_chunk_size
import numpy as np

    
class OpenAIEmbedder(IEmbedder):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def fetch_embeddings(self, tokenized):
        response = self.client.embeddings.create(
            model="text-embedding-3-large",
            input = tokenized
        )
        return response
    
    def get_embedding(self, docs):
        splitted_indices = {}
        input_doc = prepare_input(docs)
        input_ = []
        for idx, doc in enumerate(input_doc):
            splitted_indices[doc.id_] = split_text_by_chunk_size(doc.text)
            chunks = split_text_by_chunk_size(doc.text)
            splitted_indices[idx] = (len(input_), len(input_) + len(chunks))
            input_.extend(chunks)
        
        resp = self.fetch_embeddings(tokenized = input_).model_dump()
        output_ = list(sorted(resp["data"], key=lambda x: x["index"]))
        output = []
        for idx, doc in enumerate(input_doc):
            embs = output_[splitted_indices[idx][0] : splitted_indices[idx][1]]
            if len(embs) == 1:
                    output.append(
                        DocumentWithEmbedding(embedding=embs[0]["embedding"], content=doc)
                    )
                    continue

            chunk_lens = [
                len(_)
                for _ in input_[splitted_indices[idx][0] : splitted_indices[idx][1]]
            ]
            vs: list[list[float]] = [_["embedding"] for _ in embs]
            emb = np.average(vs, axis=0, weights=chunk_lens)
            emb = emb / np.linalg.norm(emb)
            output.append(DocumentWithEmbedding(embedding=emb.tolist(), content=doc))

        return output

        


        