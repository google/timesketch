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

import datetime
import os
import re

from flask import abort
from flask_login import current_user
from flask_sqlalchemy.query import Query
from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import event
from sqlalchemy import func
from sqlalchemy import inspect
from sqlalchemy import Integer
from sqlalchemy.orm import scoped_session, sessionmaker, as_declarative
from sqlalchemy.ext.declarative import declared_attr

from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN

# The database session
engine = None
session_maker = sessionmaker(future=True)
db_session = scoped_session(session_maker)


def configure_engine(url, engine_options):
    """Configure and setup the database session."""
    # These needs to be global because of the way Flask works.
    # pylint: disable=global-statement,global-variable-not-assigned
    # TODO: Can we wrap this in a class?
    # Ensure pool_pre_ping is enabled by default.
    if "pool_pre_ping" not in engine_options:
        engine_options["pool_pre_ping"] = True
    global engine, session_maker, db_session
    engine = create_engine(url, future=True, **engine_options)
    # Configure the session
    session_maker.configure(
        autocommit=False, autoflush=False, bind=engine, query_cls=Query
    )

    # Attach watchdog listeners if configured
    if os.environ.get("TIMESKETCH_DB_WATCHDOG_LOG"):
        try:
            event.listen(engine, "before_cursor_execute", _sql_watchdog_listener)
            # Ensure the ORM listener is also attached to the session maker
            # if not already.
            if not event.contains(db_session, "after_flush", _db_watchdog_listener):
                event.listen(db_session, "after_flush", _db_watchdog_listener)
        except Exception:  # pylint: disable=broad-exception-caught
            pass


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
class BaseModel:
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


def _get_obj_repr(obj):
    """Returns a readable representation of a model instance."""
    try:
        class_name = obj.__class__.__name__
        obj_id = getattr(obj, "id", "N/A")

        # Handle Status and Label objects specially to show their values
        if "Status" in class_name and hasattr(obj, "status"):
            return f"<{class_name} id={obj_id} status='{obj.status}'>"
        if "Label" in class_name and hasattr(obj, "label"):
            return f"<{class_name} id={obj_id} label='{obj.label}'>"

        # Try common name/title attributes
        obj_name = getattr(
            obj, "name", getattr(obj, "username", getattr(obj, "title", ""))
        )
        if obj_name:
            return f"<{class_name} id={obj_id} name='{obj_name}'>"
        return f"<{class_name} id={obj_id}>"
    except Exception:  # pylint: disable=broad-exception-caught
        return str(obj)


def _get_val_repr(val):
    """Returns a readable representation of a value or list of values."""
    if isinstance(val, (list, tuple, set)):
        return "[" + ", ".join([_get_obj_repr(i) for i in val]) + "]"
    if hasattr(val, "__table__"):  # It's likely a model instance
        return _get_obj_repr(val)
    return repr(val)


def _db_watchdog_listener(session, flush_context):
    """Log database changes to a file."""
    # pylint: disable=unused-argument
    log_file = os.environ.get("TIMESKETCH_DB_WATCHDOG_LOG")
    if not log_file:
        return

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().isoformat()

            # Log new instances
            for obj in session.new:
                if "view" in obj.__class__.__name__.lower():
                    continue
                f.write(f"[{timestamp}] [INSERT] {_get_obj_repr(obj)}\n")

            # Log dirty instances (updates)
            for obj in session.dirty:
                if "view" in obj.__class__.__name__.lower():
                    continue
                f.write(f"[{timestamp}] [UPDATE] {_get_obj_repr(obj)}\n")
                try:
                    state = inspect(obj)
                    for attr in state.attrs:
                        if attr.history.has_changes():
                            deleted = _get_val_repr(attr.history.deleted)
                            added = _get_val_repr(attr.history.added)
                            f.write(f"    CHANGED: {attr.key}: {deleted} -> {added}\n")
                except Exception:  # pylint: disable=broad-exception-caught
                    pass

            # Log deleted instances
            for obj in session.deleted:
                if "view" in obj.__class__.__name__.lower():
                    continue
                f.write(f"[{timestamp}] [DELETE] {_get_obj_repr(obj)}\n")

    except Exception:  # pylint: disable=broad-exception-caught
        # Fail silently to not impact app
        pass


def _sql_watchdog_listener(conn, cursor, statement, parameters, context, executemany):
    """Log raw SQL statements."""
    # pylint: disable=unused-argument
    log_file = os.environ.get("TIMESKETCH_DB_WATCHDOG_LOG")
    if not log_file:
        return

    # Prettify the statement
    sql = statement.strip()
    if not sql:
        return

    # Extract command type
    cmd = sql.split()[0].upper()

    # Ignore SELECT statements
    if cmd == "SELECT":
        return

    # Ignore anything related to the view table(s)
    if re.search(r"\bview(_\w+)?\b", sql.lower()):
        return

    # Add newlines for readability
    for kw in ["FROM", "WHERE", "JOIN", "SET", "VALUES", "GROUP BY", "ORDER BY"]:
        sql = sql.replace(f" {kw} ", f"\n    {kw} ")

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().isoformat()
            f.write(f"[{timestamp}] [SQL:{cmd}] {sql}\n")
            if parameters:
                f.write(f"    PARAMS: {parameters}\n")
    except Exception:  # pylint: disable=broad-exception-caught
        pass


# Attach the listener if configured
if os.environ.get("TIMESKETCH_DB_WATCHDOG_LOG"):
    event.listen(db_session, "after_flush", _db_watchdog_listener)
