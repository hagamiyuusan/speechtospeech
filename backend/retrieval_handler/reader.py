from pathlib import Path
from typing import Any, Dict, List, Optional

from llama_index.core.readers.base import BaseReader
from base import Document
from llama_index.core.readers.file.base import default_file_metadata_func


class UnstructuredReader(BaseReader):
    def __init__(self, *args: Any, **kwargs: Any):
        self.api = False
    def load_data(
        self,
        file: Path,
        extra_info: Optional[Dict] = None,
        split_documents: Optional[bool] = False,
        **kwargs,
    ) -> List[Document]:
        """If api is set, parse through api"""
        file_path_str = str(file)
        if self.api:
            from unstructured.partition.api import partition_via_api

            elements = partition_via_api(
                filename=file_path_str,
                api_key=self.api_key,
                api_url=self.server_url + "/general/v0/general",
            )
        else:
            """Parse file locally"""
            from unstructured.partition.auto import partition

            elements = partition(filename=file_path_str)

        """ Process elements """
        docs = []
        file_name = Path(file).name
        file_path = str(Path(file).resolve())
        if split_documents:
            for node in elements:
                metadata = {"file_name": file_name, "file_path": file_path}
                if hasattr(node, "metadata"):
                    """Load metadata fields"""
                    for field, val in vars(node.metadata).items():
                        if field == "_known_field_names":
                            continue
                        # removing coordinates because it does not serialize
                        # and dont want to bother with it
                        if field == "coordinates":
                            continue
                        # removing bc it might cause interference
                        if field == "parent_id":
                            continue
                        metadata[field] = val

                if extra_info is not None:
                    metadata.update(extra_info)

                metadata["file_name"] = file_name
                docs.append(Document(text=node.text, metadata=metadata))

        else:
            text_chunks = [" ".join(str(el).split()) for el in elements]
            metadata = {"file_name": file_name, "file_path": file_path}

            if extra_info is not None:
                metadata.update(extra_info)

            # Create a single document by joining all the texts
            docs.append(Document(text="\n\n".join(text_chunks), metadata=metadata))

        return docs


