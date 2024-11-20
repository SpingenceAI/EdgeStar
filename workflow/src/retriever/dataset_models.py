from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON,Boolean
from datetime import datetime

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)  # name of the document(file name)
    created_at = Column(DateTime, default=datetime.now)
    embedding_config = Column(JSON)  # embedding model config (LLMConfig)
    knowledge_base_name = Column(String)  # knowledge base name
    source = Column(String)  # save file path or url
    uploader = Column(String)  # uploader name
    additional_info = Column(JSON)  # additional info
    success = Column(Boolean, default=False)
    path = Column(String) # document path


class DocumentChunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, index=True)
    vector_store_id = Column(String, index=True)
    content = Column(Text)