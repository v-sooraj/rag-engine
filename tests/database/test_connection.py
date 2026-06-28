from rag_engine.database.connection import create_connection

"""
Given: valid PostgreSQL configuration
When: a connection is established
Then: the database version can be queried successfully
"""
def test_db_connection():
    query = "SELECT version();"

    with create_connection() as conn:

        with conn.cursor() as cursor:
            cursor.execute(query)
            assert "PostgreSQL" in cursor.fetchone()[0]