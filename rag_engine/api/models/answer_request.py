from pydantic import BaseModel, Field, field_validator


class AnswerRequest(BaseModel):

    query: str = Field(
        min_length=1,
    )

    @field_validator("query")
    @classmethod
    def validate_query(
        cls,
        query: str,
    ) -> str:
        if not query.strip():
            raise ValueError(
                "query must not be empty or blank"
            )

        return query