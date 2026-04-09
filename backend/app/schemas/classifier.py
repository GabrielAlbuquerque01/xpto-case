from datetime import datetime
from pydantic import BaseModel


class ClassifierResponse(BaseModel):
    id: int
    name: str
    description: str | None = None