from pymongo import MongoClient
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status

# connection to mongodb:
client = MongoClient("mongodb://localhost:27017")
db = client["library"]
book_collection = db["book"]
user_collection = db["user"]
member_collection = db["members"]

# define authentication settings:
oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/token")
pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

secret_key = "c8c4e0c39ace11095aa2806f5874bc807c237d6f10fd9e964e6fbbe9097a6a07"
algorithm = "HS256"
access_token_expire_minutes = 30

def create(data):
    data = dict(data)
    response = book_collection.insert_one(data)
    return str(response.inserted_id)

def all():
    data = []
    response = book_collection.find()
    for i in response:
        i["_id"] = str(i["_id"])
        data.append(i)
    return data

def get_one(condition):
    response = book_collection.find_one({"id": condition})
    response["_id"] = str(response["_id"])
    return response

def update(data):
    data = dict(data)
    response = book_collection.update_one({"id": data["id"]}, {"$set": {"title": data["title"]}})
    return response.matched_count

def delete(id):
    response = book_collection.delete_one({"id": id})
    return response.deleted_count

# verify user password:
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# authenticate user and generate access token:
def authenticate_user(username: str, password: str):
    user = user_collection.find_one({"username": username})
    if not user or not verify_password(password, user["password"]):
        return None
    return user

# creating access token:
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm = algorithm)
    return encoded_jwt

# generate jwt token:
def generate_token(username: str):
    expire_time = datetime.utcnow() + timedelta(minutes = access_token_expire_minutes)
    payload = {"sub": username, "exp": expire_time}
    token = jwt.encode(payload, secret_key, algorithm = algorithm)
    return token

# create dependency function for authentication:
def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "invalid authentication credentials", headers = {"WWW-Authentication": "Bearer"})
    try:
        payload = jwt.decode(token, secret_key, algorithms = [algorithm])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        # user = user_collection.find_one({"username": username})
        # if user is None:
        #     raise credentials_exception
        # return user
    except JWTError:
        raise credentials_exception
    return username


