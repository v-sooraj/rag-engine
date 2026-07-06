from pydantic import BaseModel, ConfigDict, Field


class GeneratedAnswer(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str = Field(min_length=1)