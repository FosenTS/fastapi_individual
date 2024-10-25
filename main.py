from typing import Optional, List
from unicodedata import category

from sqlalchemy.ext.asyncio import async_session
from sqlalchemy.orm import Session
import bcrypt
import jwt
import datetime

from starlette.datastructures import UploadFile

from db import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, add_new_token, \
    create_user, get_user, get_users, get_db, get_token, remove_user, SessionLocal, get_project, get_project_by_id, \
    add_new_project, add_new_task, get_task, delete_task, delete_categories, delete_note, get_projects, delete_project, \
    add_new_comment, \
    get_comments, delete_comment, add_new_category, add_new_note
from fastapi import FastAPI, Depends, Request, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from model import UserCreate, UserLogin, Token, UserRemove, Task, Project, Comment, Category, Note
import os
app = FastAPI()
upload_folder = "./uploads"
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)

class TokenValidatorMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next, ):
        if request.url.path in ["/register", "/login", "/docs"]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=403, detail="Token missing or invalid")

        token = auth_header.split(" ")[1]

        db = SessionLocal()
        if not validate_token(db, token):
            raise HTTPException(status_code=403, detail="Invalid token")

        return await call_next(request)


def validate_token(db, token: str) -> bool:
    return get_token(db, token) is not None

app.add_middleware(TokenValidatorMiddleware)


# Маршрут для регистрации
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    create_user(db, email=user.email, name=user.name, password=user.password)
    return {"msg": "User registered successfully"}

@app.get("/users")
def users(db: Session = Depends(get_db)):
    users = get_users(db)
    if not users:
        raise HTTPException(status_code=400, detail="Not found users")
    return users

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.delete("/user")
def user_remove(user: UserRemove, db: Session = Depends(get_db)):
    remove_user(db, user.email)

# Маршрут для входа
@app.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user(db, email=user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not bcrypt.checkpw(user.password.encode('utf8'), db_user.hashed_password.encode('utf8')):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": db_user.email}, expires_delta=access_token_expires)

    add_new_token(db, access_token)
    return {"access_token": access_token, "token_type": "bearer"}


# Задачи
@app.post("/task")
async def add_task(task: Task, db: Session = Depends(get_db)):
    project = get_project_by_id(db, task.project_id)
    if not project:
        raise HTTPException(status_code=422, detail="invalid project id")

    add_new_task(db, task.project_id, task.name, task.description)
    return {"msg": "task created"}

@app.get("/task/{name}")
async def get_task_by_name(name: str, db: Session =Depends(get_db)):
    task = get_task(db, name)
    if not task:
        raise HTTPException(status_code=400, detail="Incorrect task name")
    return task

@app.get("/tasks")
async def get_tasks(db: Session = Depends(get_db)):
    tasks = get_tasks(db)
    if not tasks:
        raise HTTPException(status_code=400, detail="not found tasks")

    return tasks

@app.put("/task/{name}")
async def update_task(task: Task, name: str, db: Session =Depends(get_db)):
    delete_task(db, name)
    project = get_project_by_id(db, task.project_id)
    if not project:
        raise HTTPException(status_code=422, detail="invalid project id")

    add_new_task(db, task.project_id, task.name, task.description)
    return {"msg": "task update"}

@app.delete("/task/{name}")
async def remove_task(name: str, db: Session =Depends(get_db)):
    delete_task(db, name)
    return {"msg": "task delete"}

# Проекты

@app.post("/project")
async def add_project(project: Project,  db: Session=Depends(get_db)):
    add_new_project(db, project.name, project.description)
    return {"msg":"project added"}

@app.get("/projects")
async def get_projects_req(db: Session =Depends(get_db)):
    projects = get_projects(db)
    if not projects:
        raise HTTPException(status_code=400, detail="not found projects")

    return projects

@app.get("/project/{name}")
async def get_project_by_name(name: str, db: Session = Depends(get_db)):
    project = get_project(db, name)
    if not project:
        raise HTTPException(status_code=422, detail="not found project")

    return project

@app.put("/project/{name}")
async def update_project(project: Project, name: str, db: Session = Depends(get_db)):
    delete_project(db, name)
    add_new_project(db, project.name, project.description)
    return {"msg": "project updated"}

@app.delete("/project/{name}")
async def remove_project(name: str, db: Session = Depends(get_db)):
    delete_project(db, name)
    return {"msg": "project deleted"}

# Комментарии

@app.post("task/{name_task}/comments")
async def add_comment(name_task: str, comment: Comment, db: Session = Depends(get_db)):
    task = get_task(db, name_task)
    if not task:
        raise HTTPException(status_code=422, detail="invalid task")

    add_new_comment(db, comment.author_id, task.id, comment.message)
    return {"msg": "comment added"}

@app.get("task/{name_task}/comments")
async def get_comms(name_task: str, db: Session = Depends(get_db)):
    task = get_task(db, name_task)
    if not task:
        raise HTTPException(status_code=422, detail="invalid task")

    comments = get_comments(db, task.id)
    if not comments:
        raise HTTPException(status_code=400, detail="not found comments")

    return comments

@app.put("/task/{name_task}/comments/{id}")
async def update_comment(comment: Comment, name_task: str, id: int, db: Session = Depends(get_db)):
    task = get_task(db, name_task)
    if not task:
        raise HTTPException(status_code=422, detail="invalid task")

    delete_comment(db, id)
    add_new_comment(db, comment.author_id, task.id, comment.message)
    return {"msg":"comment update"}


@app.delete("/task/{name_task}/comments/{id}")
async def remove_comment(name_task: str, id: int, db: Session = Depends(get_db)):
    task = get_task(db, name_task)
    if not task:
        raise HTTPException(status_code=422, detail="invalid task")

    delete_comment(db, id)
    return {"msg":"comment deleted"}


# Категории
@app.post("/category")
async def add_category(category: Category, db: Session = Depends(get_db)):
    add_new_category(db, category.name)
    return {"msg":"category added"}

@app.get("/category")
async def get_category(db: Session = Depends(get_db)):
    category = get_category(db)
    if not category:
        raise HTTPException(status_code=400, detail="not found category")
    return category

@app.put("/category/{name}")
async def update_category(name: str, category: Category, db: Session = Depends(get_db)):
    delete_categories(db, name)
    add_new_category(db, category.name)
    return {"msg": "category updated"}

@app.delete("/category/{name}")
async def remove_category(name: str, db: Session = Depends(get_db)):
    delete_categories(db, name)
    return {"msg": "category deleted"}


# Заметки
@app.post("/note")
async def add_nore(note: Note, db: Session = Depends(get_db)):
    add_new_note(db, author_id=note.author_id, name=note.name, body=note.body)
    return {"msg": "note added"}

@app.get("/notes")
async def get_notes(db: Session=Depends(get_db)):
    notes = get_notes(db)
    if not notes:
        raise HTTPException(status_code=400, detail="not found notes")

    return notes

@app.put("/note/{name}")
async def update_note(name: str, note: Note, db: Session = Depends(get_db)):
    delete_note(db, name)
    add_new_note(db, author_id=note.author_id, name=note.name, body=note.body)
    return {"msg": "note updated"}

@app.delete("/note/{name}")
async def remove_note(name: str, db: Session = Depends(get_db)):
    delete_note(db, name)
    return {"msg":"note deleted"}

# Файлы

@app.post("/upload/", response_model=str)
async def upload_file(file: UploadFile = File(...)):
    file_location = os.path.join(upload_folder, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())
    return {"filename": file.filename}


@app.get("/files/", response_model=List[str])
async def list_files():
    return os.listdir(upload_folder)


@app.get("/download/{filename}", response_class=FileResponse)
async def download_file(filename: str):
    file_location = os.path.join(upload_folder, filename)
    if not os.path.isfile(file_location):
        raise HTTPException(status_code=404, detail="Файл не найден")
    return file_location


@app.delete("/delete/{filename}", response_model=str)
async def delete_file(filename: str):
    file_location = os.path.join(upload_folder, filename)
    if not os.path.isfile(file_location):
        raise HTTPException(status_code=404, detail="Файл не найден")
    os.remove(file_location)
    return {"message": f"Файл '{filename}' успешно удален"}


@app.put("/update/{filename}/", response_model=str)
async def update_file(new_file: UploadFile = File(...), filename: str = None):
    if not filename:
        raise HTTPException(status_code=400, detail="Имя файла обязательно")

    file_location = os.path.join(upload_folder, filename)

    if not os.path.isfile(file_location):
        raise HTTPException(status_code=404, detail="Файл для замены не найден")

    # Сохраняем новый файл под тем же именем
    with open(file_location, "wb") as f:
        f.write(await new_file.read())

    return {"message": f"Файл '{filename}' успешно обновлен"}

@app.get("/protected")
async def protected():
    return {"message": "This is a protected route"}