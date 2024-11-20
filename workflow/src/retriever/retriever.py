import os
import requests
from typing import Optional, Union
from src.retriever.vector_store import (
    VectorStoreConfig,
    vector_store_factory,
)
from src.retriever.parser import splitter_factory, PARSERS
from src.retriever.vector_store import (
    VectorStoreProvider,
    bm25_retriever_factory,
    ensemble_retriever_factory,
)

from src.llm.config import LLMConfig
from src.llm.lc import llm_factory
import hashlib
import tempfile
from loguru import logger

from src.retriever.db import (
    get_db,
    insert_document,
    Document,
    DocumentChunk,
    insert_chunk,
    list_documents,
    list_chunks,
)
from pydantic import BaseModel


class RetrieverConfig(BaseModel):
    vector_store: VectorStoreConfig
    embedding: LLMConfig
    save_folder_path: Optional[str] = None
    sqlite_db_path: Optional[str] = None
    use_bm25: bool = False
    top_k: int = 3
    bm25_weight: float = 0.3
    chunk_size: int = 1024
    chunk_overlap: int = 200

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.vector_store.provider != VectorStoreProvider.Memory:
            if self.save_folder_path is None or self.sqlite_db_path is None:
                raise ValueError("save_folder_path and sqlite_db_path is required")


class Retriever:
    """Retriever controls dataset storage and retrieval"""

    def __init__(
        self,
        retriever_config: RetrieverConfig,
    ):
        vector_store_config = retriever_config.vector_store
        embedding_config = retriever_config.embedding
        if isinstance(vector_store_config, dict):
            vector_store_config = VectorStoreConfig(**vector_store_config)
        if isinstance(embedding_config, dict):
            embedding_config = LLMConfig(**embedding_config)
        self.use_memory = (
            VectorStoreProvider(vector_store_config.provider)
            == VectorStoreProvider.Memory
        )
        self.vector_store_config = vector_store_config
        self.embedding_config = embedding_config
        self.chunk_size = retriever_config.chunk_size
        self.chunk_overlap = retriever_config.chunk_overlap
        if not self.use_memory:
            self.save_folder_path = retriever_config.save_folder_path
            self.sqlite_db_path = (
                f"sqlite:///{os.path.abspath(retriever_config.sqlite_db_path)}"
            )
        else:
            self.sqlite_db_path = None
            self.save_folder_path = None
        self.temp_dir = tempfile.TemporaryDirectory()
        self.use_bm25 = retriever_config.use_bm25
        self.vector_store = None
        self.splitter = None
        self.bm25_retriever = None
        self.bm25_weight = retriever_config.bm25_weight
        self.top_k = retriever_config.top_k
        self.setup()
        self.insert_batch_size = 5

    @property
    def kb_name(self):
        """knowledge base name"""
        return self.vector_store_config.name

    def setup(self):
        """setup embedding, vector store and splitter"""
        self.embedding = llm_factory(self.embedding_config)
        self.vector_store = vector_store_factory(
            self.vector_store_config, self.embedding
        )
        self.splitter = splitter_factory(self.chunk_size, self.chunk_overlap)

    def insert_data(self, data: str, uploader: Optional[str] = None):
        """insert data into vector store and sqlite databse

        data: str, could be url or file path
        uploader: str, optional, who upload the data
        """
        if data.startswith("http"):
            # download data from url
            file_name = data.split("/")[-1]
            # get extension
            if "." in file_name:
                data_extension = file_name.split(".")[-1]
            else:
                data_extension = "html"
                file_name += ".html"
            temp_file_path = os.path.join(self.temp_dir.name, file_name)
            response = requests.get(data)
            response.raise_for_status()
            with open(temp_file_path, "wb") as f:
                f.write(response.content)
            data_path = temp_file_path
        else:
            data_path = data
        data_extension = data_path.split(".")[-1]
        if data_extension not in PARSERS:
            raise ValueError(f"Invalid data extension: {data_extension}")
        logger.debug(f"Start insert data: {data_path}")
        loader = PARSERS[data_extension](data_path)
        docs = loader.load_and_split(self.splitter)
        for idx in range(0, len(docs), self.insert_batch_size):
            for doc in docs[idx : idx + self.insert_batch_size]:
                doc.metadata["source"] = data_path
                doc.metadata["file_name"] = os.path.basename(data_path)
                doc.metadata["enabled"] = True
            self.vector_store.add_documents(docs[idx : idx + self.insert_batch_size])
            logger.debug(f"Progress:[{idx+1}/{len(docs)}]-{data_path}")

        if not self.use_memory:
            # save data to folder
            save_path = os.path.join(
                self.save_folder_path, self.kb_name, os.path.basename(data_path)
            )
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w") as f:
                f.write(data)
            # save to sqllite
            db = get_db(self.sqlite_db_path)
            title = os.path.basename(data_path)
            doc_id = hashlib.sha256(title.encode()).hexdigest()
            db_document = Document(
                id=doc_id,
                name=os.path.basename(data_path),
                embedding_config=self.embedding_config.dict(exclude_none=True),
                knowledge_base_name=self.kb_name,
                source=data_path,
                uploader=uploader,
                additional_info={},
                success=True,
                path=os.path.abspath(save_path),
            )
            insert_document(db, db_document)
            for doc in docs:
                db_chunk = DocumentChunk(
                    document_id=db_document.id,
                    vector_store_id=self.kb_name,
                    content=doc.page_content,
                )
                insert_chunk(db, db_chunk)
        logger.debug(f"Data inserted: {data_path}")
        return docs

    def insert_data_list(self, data_list: list[str], uploader: Optional[str] = None):
        """insert data list into vector store and sqlite databse

        data_list: list[str], list of data
        uploader: str, optional, who upload the data
        """
        all_docs = []
        for idx, data in enumerate(data_list):
            logger.debug(f"Start Inserting data: {data}")
            docs = self.insert_data(data, uploader)
            logger.debug(f"Progress:[{idx+1}/{len(data_list)}] {data} loaded")
            all_docs.extend(docs)
        if self.use_bm25 and len(all_docs) > 0:
            self.bm25_retriever = bm25_retriever_factory(all_docs, self.top_k)
        return all_docs

    def setup_rag_retriever(self, top_k: int):
        """setup rag retriever"""
        if self.bm25_retriever:
            self.bm25_retriever.k = top_k
            return ensemble_retriever_factory(
                [self.vector_store, self.bm25_retriever],
                top_k=top_k,
                weights=[1 - self.bm25_weight, self.bm25_weight],
            )
        else:
            return self.vector_store.as_retriever(search_kwargs={"k": top_k})

    def retrieve_data(self, query: str, top_k: Optional[int] = None):
        """retrieve data from vector store"""
        retriever = self.setup_rag_retriever(top_k or self.top_k)
        return retriever.invoke(query)

    def list_documents(self):
        """list all documents in sqlite database"""
        db = get_db(self.sqlite_db_path)
        return list_documents(db)

    def list_chunks(self, document_id: str):
        """list all chunks in sqlite database"""
        db = get_db(self.sqlite_db_path)
        return list_chunks(db, document_id)


def list_knowledge_bases(save_folder: str) -> list[str]:
    """list all knowledge bases in sqlite database"""
    if os.path.exists(save_folder):
        return os.listdir(save_folder)
    else:
        os.makedirs(save_folder, exist_ok=True)
        return []
