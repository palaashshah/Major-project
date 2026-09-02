from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

load_dotenv()  # reads the .env file

DATABASE_URL = os.getenv("DATABASE_URL") # gets the URL

engine = create_engine(DATABASE_URL) 
# The engine is the raw connection to your database. You set it once and then its used as needed

SessionLocal = sessionmaker(autocommit = False, autoflush= False, bind= engine)
# Each request gets its own DB session, then it closes. This is the standard pattern.

Base = declarative_base()

def get_db():
    db = SessionLocal()   # open a session
    try:
        yield db          # hands it over, but PAUSES here
                          # return db hands it over, function is DONE, no cleanup possible
    finally:
        db.close()        # ALWAYS close it, even if an error occurred, "run this no matter what — success or crash."