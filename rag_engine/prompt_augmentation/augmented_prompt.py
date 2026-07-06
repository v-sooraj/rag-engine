from pydantic import BaseModel, ConfigDict, Field


class AugmentedPrompt(BaseModel):
    model_config = ConfigDict(frozen=True)

    system_instruction: str = Field(min_length=1)
    context: str
    question: str = Field(min_length=1)