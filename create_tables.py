# create_tables.py
from psql import Base, engine
from models import User, UserCredits

Base.metadata.create_all(bind=engine)
