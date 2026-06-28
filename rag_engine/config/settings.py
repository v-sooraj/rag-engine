from pydantic import BaseModel
from pydantic_settings import (BaseSettings, SettingsConfigDict)

class PostgresSettings(BaseModel):
    host: str
    port: int
    database: str
    user: str
    password: str

    @property
    def connection_uri(self) -> str:
        return (
            f"postgresql://"
            f"{self.user}:{self.password}@"
            f"{self.host}:{self.port}/"
            f"{self.database}"
        )

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_nested_delimiter='_', env_nested_max_split=1, env_file_encoding='utf-8')
    postgres: PostgresSettings

settings = Settings()
