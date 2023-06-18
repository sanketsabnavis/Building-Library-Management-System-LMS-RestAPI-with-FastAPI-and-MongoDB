from fastapi import FastAPI, HTTPException, status, Depends
import db
from models import Book, User, Borrowbook
from passlib.hash import bcrypt
from fastapi.security import  OAuth2PasswordRequestForm
from jose import JWTError
from bson import ObjectId


app = FastAPI()

@app.get('/')
def home():
    return {"message": "welcome to library management system...!"}


# register user route
@app.post("/register")
def register_user(user: User):
    hashed_password = bcrypt.hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    inserted_user = db.user_collection.insert_one(user_dict)
    
    if not inserted_user.inserted_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )
    
    return {"message": "User created successfully"}

@app.post('/login')
def login(user: User):
    stored_user = db.user_collection.find_one({"username": user.username})
    if stored_user and db.verify_password(user.password, stored_user["password"]):
        token = db.generate_token(user.username)
        return {"token": token}
    raise HTTPException(status_code = 401, detail = "invalid username or password")

# token route
@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code = 401, detail = "invalid username or password", headers = {"WWW-Authenticate": "Bearer"})
    access_token_expires = db.timedelta(minutes = db.access_token_expire_minutes)
    access_token = db.create_access_token(
        data = {"sub": user["username"]},
        expires_delta = access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# protected route
@app.get("/protected")
def protected_route(token: str = Depends(db.oauth2_scheme)):
    try:
        payload = db.jwt.decode(token, db.secret_key, algorithms = [db.algorithm])
        username = payload.get('sub')
        if not username:
            raise HTTPException(status_code = 401, detail = 'invalid token',headers = {"WWW-Authenticate": "bearer"})
        return ({"message": "protected route accessed successfully"})
    except JWTError:
        raise HTTPException(status_code = 401, detail = 'invalid token',headers = {"WWW-Authenticate": "bearer"})


@app.post("/books")
def create_book(data: Book, token: str = Depends(db.oauth2_scheme)):
    try:
        payload = db.jwt.decode(token, db.secret_key, algorithms=[db.algorithm])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        data = Book(id = data.id, title = data.title, author = data.author)
        res = db.create(data)
        return {"message": "Book created successfully", "inserted_id": res}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get('/get_all_data')
def all(token: str = Depends(db.oauth2_scheme)):
    try:
        payload = db.jwt.decode(token, db.secret_key, algorithms = [db.algorithm])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="invalid token")
        data = db.all()
        return {"book_details": data}
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid token")

@app.get('/get/{id}')
def get_one(id: str, token: str = Depends(db.oauth2_scheme)):
    try:
        payload = db.jwt.decode(token, db.secret_key, algorithms = [db.algorithm])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="invalid token")
        data = db.get_one(id)
        return {"selected_book": data}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")

@app.put('/update_book')
def update(data: Book, token: str = Depends(db.oauth2_scheme)):
     try:
        payload = db.jwt.decode(token, db.secret_key, algorithms = [db.algorithm])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="invalid token")
        data = db.update(data)
        return {"message": "book updated successfully", "updated_count": data}
     except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token")

@app.delete('/delete_book')
def delete(id: str, token:str = Depends(db.oauth2_scheme)):
     try:
        payload = db.jwt.decode(token, db.secret_key, algorithms = [db.algorithm])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="invalid token")
        data = db.delete(id)
        return {"message": "book deleted successfully", "delete_count": data}
     except JWTError:
        raise HTTPException(status_code=401, detail="Invalid Token") 
     

# # add a new member
# @app.post('/members')
# def create_member(mem: Member):
#     mem_dict = mem.dict()
#     inserted_mem = db.member_collection.insert_one(mem_dict)
#     mem_id = str(inserted_mem.inserted_id)
#     return {"message": "member created successfully", "member_id": mem_id}

# borrow books:
@app.post("/books/borrow_book")
def borrow_book(id: str, username: str = Depends(db.get_current_user)):
    # book_collection = db["books"]
    # user_collection = db["users"]
    try:
        book_object_id = ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail="Invalid id")
    # Check if the book exists
    book = db.book_collection.find_one({"_id": book_object_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Check if the book is already borrowed by the user
    if id in db.user_collection.find_one({"username": username}).get("borrowed_books", []):
        raise HTTPException(status_code=400, detail="Book already borrowed by user")

    # Check if the book is available for borrowing
    if book["quantity"] is None or book["quantity"] <= 0:
        raise HTTPException(status_code=400, detail="Book is not available")

    # Update the book quantity and user's borrowed books
    db.book_collection.update_one({"_id": book_object_id}, {"$inc": {"quantity": -1}})
    db.user_collection.update_one({"username": username}, {"$push": {"borrowed_books": id}})

    return {"message": "Book borrowed successfully"}


# return bboks:
@app.post('/books/return_books')
def return_book(data: Borrowbook):
    book = db.book_collection.find_one({"_id": data.id, "availability": False})
    if book is None:
        raise HTTPException(status_code=404, detail="book not borrowd by the user")
    db.book_collection.update_one({"_id": data.id}, {"$set": {"availabilty": True}})
    db.user_collection.update_one({"username": data.username}, {"$pull": {"borrowed_books": data.id}})
    return {"message": "book returned successfully"}







