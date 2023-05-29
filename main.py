from fastapi import FastAPI
from pymongo import MongoClient
from pydantic import BaseModel

app = FastAPI()


client = MongoClient("mongodb://localhost:27017/")
db = client["library"]
collection = db['booklet']


class Book(BaseModel):
    title: str
    author: str


@app.post("/books/")
async def create_book(book: Book, book_id: int):
    # Code to create the book in the database
    # Save the book data using your database library, e.g., 
    collection.insert_one(book.dict())
    return {"message": "Book created successfully"}

@app.get("/books/{book_id}")
async def get_book(book_id: str):
    # Code to retrieve the book from the database
    # Fetch the book data using your database library, e.g., 
    collection.find_one({"_id": book_id})
    return {"book_id": book_id, "book title": 'title', "author name": "author"}

@app.put("/books/{book_id}")
async def update_book(book_id: str, book: Book):
    # Code to update the book in the database
    # Update the book data using your database library, e.g., 
    collection.update_one({"_id": book_id}, {"$set": book.dict()})
    return {"message": "Book updated successfully"}

@app.delete("/books/{book_id}")
async def delete_book(book_id: str):
    # Code to delete the book from the database
    # Delete the book data using your database library, e.g., 
    collection.delete_one({"_id": book_id})
    return {"message": "Book deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app)
