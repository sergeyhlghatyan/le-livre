"""Database connection management."""
import psycopg
from neo4j import GraphDatabase
from contextlib import contextmanager
from .config import get_settings

settings = get_settings()


# PostgreSQL connection string
POSTGRES_CONN_STRING = (
    f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)


@contextmanager
def get_postgres_conn():
    """Get PostgreSQL connection context manager."""
    conn = psycopg.connect(POSTGRES_CONN_STRING)
    try:
        yield conn
    finally:
        conn.close()


# Neo4j driver (singleton)
_neo4j_driver = None


def get_neo4j_driver():
    """Get Neo4j driver (singleton)."""
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password)
        )
    return _neo4j_driver


def close_neo4j_driver():
    """Close Neo4j driver."""
    global _neo4j_driver
    if _neo4j_driver is not None:
        _neo4j_driver.close()
        _neo4j_driver = None
