from typing import List
from pydantic import BaseModel

class TreeNode(BaseModel):
    id: int
    data: str
    children: List["TreeNode"] = []

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

TreeNode = TreeNode.model_rebuild()

class TreeResponse(BaseModel):
    tree: TreeNode
    message: str