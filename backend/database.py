from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

#config da conexão com o docker
DATABASE_URL = "postgresql://user:password@localhost:5432/ans_database"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

#dependência para pegar o banco de dados em cada requisiçao
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()