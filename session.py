import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Load the .env file
load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL'))
session_factory = sessionmaker(bind=engine)

# scoped_session creates a new Session that is scoped to the current thread of execution
# This ensures that if you call Session() multiple times in the same thread, you will get the same Session object
Session = scoped_session(session_factory)