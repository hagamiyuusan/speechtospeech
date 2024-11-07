import sys
sys.path.append("..")
from base import Document
from llama_index.core.readers.file.base import default_file_metadata_func
from unstructured.partition.auto import partition
from llama_index.core.text_splitter import TokenTextSplitter
import tiktoken
from itertools import islice
import re

PATTERN_INTEGER: re.Pattern = re.compile(r"([+-]?[1-9][0-9]*|0)")

def re_0_10_rating(s: str) -> int:
    matches = PATTERN_INTEGER.findall(s)
    if not matches:
        raise AssertionError
    vals = set()
    for match in matches:
        try:
            vals.add(validate_rating(int(match)))
        except ValueError:
            pass
    if not vals:
        raise AssertionError
    return min(vals)


def validate_rating(rating) -> int:
    if not 0 <= rating <= 10:
        raise ValueError("Rating must be between 0 and 10")
    return rating

def splitDocument(doc):
    splitter=TokenTextSplitter(
                chunk_size=1024,
                chunk_overlap=256,
                separator="\n\n",
                backup_separators=["\n", ".", "\u200B"],
                )
    docs =  splitter(doc)
    return [Document.from_dict(doc.to_dict()) for doc in docs]


def load_document(file_path):
    elements = partition(filename=file_path)
    extra_info = default_file_metadata_func(str(file_path))
    docs = []
    text_chunks = [" ".join(str(el).split()) for el in elements]
    metadata = {"file_name": file_path.split("/")[-1], "file_path": file_path}

    if extra_info is not None:
        metadata.update(extra_info)

    docs.append(Document(text="\n\n".join(text_chunks), metadata=metadata))
    return docs


def prepare_input( text: str | list[str] | Document | list[Document]) -> list[Document]:
    if isinstance(text, (str, Document)):
        return [Document(content=text)]
    elif isinstance(text, list):
        return [Document(content=_) for _ in text]



def split_text_by_chunk_size(text: str, chunk_size: int = 8191) -> list[list[int]]:
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = iter(encoding.encode(text))
    result = []
    while chunk := list(islice(tokens, chunk_size)):
        result.append(chunk)
    return result