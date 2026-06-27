from rag_engine.config.settings import settings

"""
Given: Application environment variables are defined in the .env file
When: The Settings singleton is created
Then: The PostgreSQL configuration is loaded and mapped correctly
"""
def test_postgres_settings_loaded_from_env():
    assert settings.postgres.host == "localhost"
    assert settings.postgres.port == 5432
    assert settings.postgres.database == "rag_db"
    assert settings.postgres.user == "postgres"
    assert settings.postgres.password == "postgres"