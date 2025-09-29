from sqlmodel import create_engine, Session, SQLModel
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "app.db")
DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    # 在 main.py 启动时调用，创建表
    SQLModel.metadata.create_all(engine)