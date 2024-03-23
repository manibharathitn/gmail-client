from sqlalchemy import Column, String, DateTime, and_
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from session import Session
session = Session()

class Email(Base):
    __tablename__ = 'emails'

    msg_id = Column(String, primary_key=True)
    sender = Column(String)
    subject = Column(String)
    date_received = Column(DateTime)
    content = Column(String)
    synced_at = Column(DateTime)
    recipient = Column(String)
    cc = Column(String)

    @classmethod
    def filter(cls, **kwargs):
        filters = []
        for key, value in kwargs.items():
            if isinstance(value, dict):
                for op, v in value.items():
                    if op == 'contains':
                        filters.append(getattr(cls, key).like(f"%{v}%"))
                    elif op == 'not':
                        filters.append(getattr(cls, key) != v)
                    elif op == 'lt':
                        filters.append(getattr(cls, key) < v)
            else:
                filters.append(getattr(cls, key) == value)
        return session.query(cls).filter(and_(*filters))

    @classmethod
    def get_by_msg_id(cls, msg_id):
        return session.query(cls).filter_by(msg_id=msg_id).first()

    def save(self):
        session.add(self)
        session.commit()
