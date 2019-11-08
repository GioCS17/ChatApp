from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta
import json

class Manager:
    Base = declarative_base()
    session = None

    def createEngine(self):
        #engine = create_engine('sqlite:///message.db?check_same_thread=False', echo=False)
        #engine = create_engine('postgresql://postgres:postgres@localhost/chatdb' )
        engine = create_engine('postgres://wzluksutgwskdb:f7e5ca57dc3c6658da8fcebe3b66acd5d00ddeb92cc11b1ca70acd780bf60d8c@ec2-54-197-238-238.compute-1.amazonaws.com:5432/df9ihc326h07d4',echo=False)
        self.Base.metadata.create_all(engine)
        return engine

    def getSession(self, engine):
        if self.session == None:
            Session = sessionmaker(bind=engine)
            session = Session()

        return session

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data)
                    fields[field] = data
                except TypeError:
                    fields[field] = None

            return fields

        return json.JSONEncoder.default(self, obj)
