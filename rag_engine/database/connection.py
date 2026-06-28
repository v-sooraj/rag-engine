import psycopg

from rag_engine.config.settings import settings


def create_connection():
    return psycopg.connect(settings.postgres.connection_uri)
