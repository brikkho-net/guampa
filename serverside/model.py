import sqlalchemy

from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    password = Column(String)

    def __init__(self, name, fullname, password):
        self.name = name
        self.fullname = fullname
        self.password = password

    def __repr__(self):
       return ("<User('%s','%s', '%s')>"
                % (self.name, self.fullname, self.password))

"""
things about Documents:
    have a source language (and a target language??!)
    have many sentences (which have an order)
    have many tags
    have a user who uploaded them
    have a title
"""

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    user = Column(String)
    sl = Column(String) ## string?

    def __init__(self, title, user, sl):
        self.title = title
        self.user = user 
        self.sl = sl

    def __repr__(self):
       return ("<Document(%d, '%s', '%s', '%s')>"
                % (self.id, self.title, self.user, self.sl))

class Sentence(Base):
    __tablename__ = 'sentences'

    id = Column(Integer, primary_key=True)
    text = Column(String)
    docid = Column(Integer)

    def __init__(self, text, docid):
        self.text = text
        self.docid = docid

    def __repr__(self):
       return ("<Sentence(%d, '%s')>" % (self.id, self.text))