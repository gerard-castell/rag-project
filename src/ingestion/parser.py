"""Document parser using LlamaParse."""

import os
from typing import cast

from llama_index.core.schema import Document
from llama_parse import LlamaParse, ResultType

from src.core.settings import settings


class DocumentParser:
    """Class to parse documents using LlamaParse."""

    def __init__(self) -> None:
        self.parser = LlamaParse(
            result_type=ResultType.MD,
            api_key=settings.llama_parse_api_key,  # type: ignore
        )

    def parse(self, file_path: str) -> list[Document]:
        """Parse the document at the given file path."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        return cast("list[Document]", self.parser.load_data(file_path))
