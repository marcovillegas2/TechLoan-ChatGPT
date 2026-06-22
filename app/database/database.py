from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.equipment import Base

DATABASE_URL = "sqlite:///./techloan.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)