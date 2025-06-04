from database.base import Base
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://root:root@localhost:5432/affiliate_db")
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)