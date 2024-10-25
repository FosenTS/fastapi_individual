from pydantic import BaseModel

# Модели данных для API
class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str

class UserRemove(BaseModel):
    email: str

class UserLogin(BaseModel):
    email: str
    password: str

class Task(BaseModel):
    project_id: int
    name: str
    description: str

class Project(BaseModel):
    name: str
    description: str

class Comment(BaseModel):
    author_id: int
    message: str

class Category(BaseModel):
    name: str

class Note(BaseModel):
    author_id: int
    name: str
    body: str