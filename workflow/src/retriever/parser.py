from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    CSVLoader,
    JSONLoader,
    UnstructuredMarkdownLoader,
    UnstructuredHTMLLoader,
    UnstructuredFileLoader,
    UnstructuredImageLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredPDFLoader,
    UnstructuredExcelLoader,
    UnstructuredODTLoader,
    UnstructuredRTFLoader,
    WebBaseLoader,
    UnstructuredXMLLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

PARSERS = {
    "pdf": PyPDFLoader,
    "txt": TextLoader,
    "docx": Docx2txtLoader,
    "csv": CSVLoader,
    "json": JSONLoader,
    "md": UnstructuredMarkdownLoader,
    "html": UnstructuredHTMLLoader,
    "file": UnstructuredFileLoader,
    "image": UnstructuredImageLoader,
    "doc": UnstructuredWordDocumentLoader,
    "xls": UnstructuredExcelLoader,
    "xlsx": UnstructuredExcelLoader,
    "ppt": UnstructuredPowerPointLoader,
    "pptx": UnstructuredPowerPointLoader,
    "xml": UnstructuredXMLLoader,
    "http": WebBaseLoader,
}


def splitter_factory(chunk_size: int, chunk_overlap: int):
    """splitter factory"""
    # TODO: add more splitter
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            " ",
            ".",
            ",",
            "\u200b",  # Zero-width space
            "\uff0c",  # Fullwidth comma ，
            "\u3001",  # Ideographic comma 、
            "\uff0e",  # Fullwidth full stop ．
            "\u3002",  # Ideographic full stop 。
            "",
        ],
    )
