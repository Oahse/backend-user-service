from pydantic import BaseModel, Field
from uuid import UUID

class TagBase(BaseModel):
    name: str = Field(..., max_length=100)

class TagCreate(TagBase):
    pass

class TagRead(TagBase):
    id: UUID

    class Config:
        from_attributes = True

