from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from src.retriever.dataset_models import Base, Document, DocumentChunk
from loguru import logger


def get_db(connection_string: str):
    DATABASE_URL = connection_string
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def check_id_exist(db, id: str) -> bool:
    return db.query(Document).filter(Document.id == id).first() is not None


def update_document(db, document: Document):
    old_document = get_document_by_id(db, document.id)
    for k, v in document.__dict__.items():
        setattr(old_document, k, v)
    db.commit()
    return document


def get_document_by_id(db, id: str) -> Document:
    return db.query(Document).filter(Document.id == id).first()


def insert_document(db, document: Document):
    if check_id_exist(db, document.id):
        logger.warning(f"Document {document.id} already exists,update it!")
        update_document(db, document)
    else:
        db.add(document)
        db.commit()
        db.refresh(document)
        return document


def insert_chunk(db, chunk: DocumentChunk):
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


def list_documents(db) -> list[Document]:
    return db.query(Document).all()


def list_chunks(db,document_id:str) -> list[DocumentChunk]:
    return db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
