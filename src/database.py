import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Dict, Any, Optional

Base = declarative_base()

class ExperimentResult(Base):
    __tablename__ = 'results'

    id: str = Column(String, primary_key=True)
    experiment_id: str = Column(String, nullable=False, index=True)
    session_id: str = Column(String, nullable=False, index=True)
    query_id: str = Column(String, nullable=False, index=True)
    query_text: str = Column(Text, nullable=False)
    query_category: str = Column(String, nullable=False)
    iteration: int = Column(Integer, nullable=False)
    model_name: str = Column(String, nullable=False, index=True)
    model_type: str = Column(String, nullable=False)
    response_raw: str = Column(Text)
    sources_extracted: Dict[str, Any] = Column(JSON)
    chain_of_thought: Optional[str] = Column(Text)
    response_time_ms: int = Column(Integer)
    timestamp: datetime.datetime = Column(DateTime, default=datetime.datetime.utcnow)
    extra_metadata: Dict[str, Any] = Column(JSON)

engine = None
SessionLocal = None

def initialize_database(db_url: str):
    global engine, SessionLocal
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    if not SessionLocal:
        raise Exception("Database not initialized.")
    return SessionLocal()