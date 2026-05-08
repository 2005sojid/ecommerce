import uuid
from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=120)
    parent_id: uuid.UUID | None = None

class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    parent_id: uuid.UUID | None = None

    class Config:
        from_attributes = True

class CategoryNode(CategoryOut):
    children: list['CategoryNode'] = []
CategoryNode.model_rebuild()
