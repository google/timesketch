# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This package handles setting up and providing the database connection."""

from __future__ import unicode_literals

from flask import abort
from flask_login import current_user
from flask_sqlalchemy.query import Query
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, as_declarative
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import func
from sqlalchemy import Integer

from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN

# The database session
engine = None
session_maker = sessionmaker(future=True)
db_session = scoped_session(session_maker)


def configure_engine(url):
    """Configure and setup the database session."""
    # These needs to be global because of the way Flask works.
    # pylint: disable=global-statement,global-variable-not-assigned
    # TODO: Can we wrap this in a class?
    global engine, session_maker, db_session
    engine = create_engine(url, future=True)
    # Configure the session
    session_maker.configure(
        autocommit=False, autoflush=False, bind=engine, query_cls=Query
    )


def init_db():
    """Initialize the database based on the implemented models. This will setup
    the database on the first run.
    """
    BaseModel.metadata.create_all(bind=engine)
    BaseModel.query = db_session.query_property()
    BaseModel.session = db_session
    return BaseModel


def drop_all():
    """Drop all tables in the database."""
    BaseModel.metadata.drop_all(bind=engine)


@as_declarative()
class BaseModel(object):
    """Base class used for database models. It adds common model fields to all
    models classes that subclass it.
    """

    @declared_attr
    def __tablename__(self):
        return self.__name__.lower()

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(), default=func.now())
    updated_at = Column(DateTime(), default=func.now(), onupdate=func.now())

    def update_modification_time(self):
        """Set updated_at field to current time."""
        self.updated_at = func.now()

    @classmethod
    def get_with_acl(cls, model_id, user=current_user):
        """Get a database object with permission check enforced.

        Args:
            model_id: The integer ID of the model to get.
            user: User (instance of timesketch.models.user.User)

        Returns:
            A BaseQuery instance.
        """
        result_obj = db_session.get(cls, model_id)
        if not result_obj:
            abort(HTTP_STATUS_CODE_NOT_FOUND)
        try:
            if result_obj.get_status.status == "deleted":
                abort(HTTP_STATUS_CODE_NOT_FOUND)
        except AttributeError:
            pass
        if result_obj.is_public:
            return result_obj
        if not result_obj.has_permission(user=user, permission="read"):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        return result_obj

    @classmethod
    def get_by_id(cls, model_id):
        """Get model instance by id.

        Args:
            model_id: The integer ID of the model to get.

        Returns:
            A model instance.
        """
        return db_session.get(cls, model_id)

    @classmethod
    def get_or_create(cls, **kwargs):
        """Get or create a database object.

        Returns:
            A model instance.
        """
        instance = cls.query.filter_by(**kwargs).first()
        if not instance:
            instance = cls(**kwargs)
            db_session.add(instance)
            db_session.commit()
        return instance
