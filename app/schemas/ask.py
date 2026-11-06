from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000, examples=["How many days of annual leave do I get?"])


class CitationOut(BaseModel):
    id: int = Field(description="The [n] number used in the answer")
    source: str = Field(description="PDF file name")
    page: int
    score: float = Field(description="Similarity between the question and this passage (0-1)")


class AskResponse(BaseModel):
    answer: str
    covered: bool = Field(description="False when the policies don't cover the question")
    citations: list[CitationOut]
