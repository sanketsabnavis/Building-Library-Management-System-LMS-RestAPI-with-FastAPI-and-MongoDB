from pydantic import BaseModel, Field
from typing import Optional

class Book(BaseModel):
    id: str
    title: str
    author: str
    quantity: Optional[str] = Field(None, alias='quantity')

class User(BaseModel):
    username: str
    password: str

# class Member(BaseModel):
#     name: str
#     contact: str
#     borrowed_books: List[str] = []

class Borrowbook(BaseModel):
    username: str
    id: str
