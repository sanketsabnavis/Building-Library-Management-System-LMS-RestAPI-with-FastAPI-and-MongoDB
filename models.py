from pydantic import BaseModel
# from typing import List

class Book(BaseModel):
    id: str
    title: str
    author: str

class User(BaseModel):
    username: str
    password: str

# class Member(BaseModel):
#     name: str
#     contact: str
#     borrowed_books: List[str] = []
