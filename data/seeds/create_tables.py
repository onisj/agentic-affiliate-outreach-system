from database.models import Base
from database.session import engine
from sqlalchemy import inspect

def create_tables():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    # Only create tables that don't exist
    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("Tables created successfully (if they didn't already exist)")

if __name__ == "__main__":
    create_tables()