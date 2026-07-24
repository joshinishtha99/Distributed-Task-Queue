"""Declarative base for all ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """All database models inherit from this.

    SQLAlchemy uses it to collect table metadata, which Alembic reads
    when generating migrations.
    """
