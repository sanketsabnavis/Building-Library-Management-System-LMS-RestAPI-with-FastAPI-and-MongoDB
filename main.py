from fastapi import FastAPI, HTTPException, status, Depends
import db
from models import Book, User
from passlib.hash import bcrypt
from fastapi.security import  OAuth2PasswordRequestForm
from jose import JWTError


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

@app.post('/create_book')
def create(data: Book):
    data = Book(id = data.id, title = data.title, author = data.author)
    res = db.create(data)
    return {"message": "book created successfully", "inserted_id": res}

@app.get('/get_all_data')
def all():
    data = db.all()
    return {"book_details": data}

@app.get('/get/{id}')
def get_one(id: str):
    data = db.get_one(id)
    return {"selected_book": data}

@app.put('/update_book')
def update(data: Book):
    data = db.update(data)
    return {"message": "book updated successfully", "updated_count": data}

@app.delete('/delete_book')
def delete(id: str):
    data = db.delete(id)
    return {"message": "book deleted successfully", "delete_count": data}

# add a new member
# @app.post('/members')
# def create_member(mem: Member):
#     mem_dict = mem.dict()
#     inserted_mem = db.member_collection.insert_one(mem_dict)
#     mem_id = str(inserted_mem.inserted_id)
#     return {"message": "member created successfully", "member_id": mem_id}




