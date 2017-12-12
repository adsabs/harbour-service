"""
Models use to define the database
The database is not initiated here, but a pointer is created named db. This is
to be passed to the app creator within the Flask blueprint.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Users(Base):
    """
    Users table
    Foreign-key absolute_uid is the primary key of the user in the user
    database microservice.
    """
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    absolute_uid = Column(Integer, unique=True, nullable=False)
    classic_email = Column(String, default='')
    classic_mirror = Column(String, default='')
    classic_cookie = Column(String, default='')
    twopointoh_email = Column(String, default='')

    def __repr__(self):
        return '<' \
               'User: id {0}, ' \
               'absolute_uid {1}, ' \
               'classic_cookie "{2}", ' \
               'classic_email "{3}", ' \
               'classic_mirror "{4}", ' \
               'twopointoh_email "{5}"' \
               '>'\
            .format(self.id,
                    self.absolute_uid,
                    self.classic_cookie,
                    self.classic_email,
                    self.classic_mirror,
                    self.twopointoh_email)
