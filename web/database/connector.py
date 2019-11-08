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
        engine = create_engine('postgres://aoytkblbpsqoaw:18452ab6923dccefc3e50b26db3a020f7b837c873a793c0e06bc5b7ef1a97081@ec2-174-129-253-162.compute-1.amazonaws.com:5432/df0fv72p3is861' )
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
