from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from starlette_admin.contrib.sqla import Admin

DATABASE_URL = "postgresql://postgre:postgre@localhost:5434/ships_vts"
#DATABASE_URL = "sqlite:///./ships_vts.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

admin = Admin(engine, title="Gateway Admin")
