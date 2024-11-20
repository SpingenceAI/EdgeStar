from typing import Optional, Callable
from langchain_core.documents import Document
from langchain.retrievers import EnsembleRetriever, BM25Retriever

from langchain_core.vectorstores import VectorStore
from langchain_core.retrievers import BaseRetriever
from pydantic import BaseModel
from enum import Enum


class VectorStoreProvider(Enum):
    Memory = "memory"
    LanceDB = "lancedb"
    Chroma = "chroma"


class VectorStoreConfig(BaseModel):
    """Vector store config"""

    provider: Optional[VectorStoreProvider] = VectorStoreProvider.Memory
    name: Optional[str] = None  # collection name or table name
    connection_string: Optional[str] = None
    args: Optional[dict] = None


def init_chromma_vector_store(config: VectorStoreConfig, embedding_function: Callable):
    """init chroma vector store"""
    import chromadb
    from langchain_chroma import Chroma

    if "http" not in config.connection_string:
        # use local chroma
        persistant_client = chromadb.PersistentClient(
            path=config.connection_string,
        )
        collection = persistant_client.get_or_create_collection(config.name)
        vector_store_from_client = Chroma(
            client=persistant_client,
            collection_name=config.name,
            embedding_function=embedding_function,
            persist_directory=config.connection_string,
        )
        return vector_store_from_client
    # TODO: add http client
    raise ValueError(f"Invalid provider: {config.provider}")


def init_memory_vector_store(embedding_function: Callable):
    """init memory vector store"""
    from langchain_core.vectorstores import InMemoryVectorStore

    return InMemoryVectorStore(embedding_function)


def vector_store_factory(config: VectorStoreConfig, embedding_function: Callable):
    """vector store factory"""
    args = config.args or {}
    if config.provider == VectorStoreProvider.Memory:
        return init_memory_vector_store(embedding_function)
    elif config.provider == VectorStoreProvider.Chroma:
        return init_chromma_vector_store(config, embedding_function, **args)
    elif config.provider == VectorStoreProvider.LanceDB:
        raise NotImplementedError("LanceDB is not implemented")
    else:
        raise ValueError(f"Invalid provider: {config.provider}")


def ensemble_retriever_factory(
    vector_stores: list, top_k: int, weights: list[float]
):
    """retriver factory"""
    retrievers = []
    for store in vector_stores:
        if isinstance(store, VectorStore):
            retriever = store.as_retriever(search_kwargs={"k": top_k})
        elif isinstance(store, BaseRetriever):
            retriever = store
        else:
            raise ValueError(f"Invalid vector store: {store}")
        retrievers.append(retriever)
    return EnsembleRetriever(retrievers=retrievers, weights=weights)


def bm25_retriever_factory(docs: list[Document],top_k:int):
    """bm25 retriever factory"""
    retriever = BM25Retriever.from_documents(docs)
    retriever.k = top_k
    return retriever
