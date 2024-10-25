from operator import index
from tkinter.font import names
from venv import create

import bcrypt

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session, foreign

# Настройки для базы данных
DATABASE_URL = "sqlite:///./test.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Конфигурация для JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)


def get_user(db, email: str):
    return db.query(User).filter(User.email == email).first()


def get_users(db):
    return db.query(User).all()

def remove_user(db, email: str):
    db.query(User).filter(User.email == email).delete()
    db.commit()


def create_user(db: Session, email: str, name: str, password: str):
    hashed_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
    db_user = User(email=email, name=name, hashed_password=hashed_password.decode('utf8'))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)


def add_new_token(db, token: str):
    new_token = Token(token=token)
    db.add(new_token)
    db.commit()

def get_token(db, token: str):
    return db.query(Token).filter(Token.token == token).first()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)

def add_new_task(db, project_id: int, name: str, description: str):
    new_task = Task(project_id=project_id, name=name, description=description)
    db.add(new_task)
    db.commit()

def get_tasks(db):
    return db.query(Task).all()

def get_task(db, name: str):
    return db.query(Task).filter(Task.name == name).first()

def delete_task(db, name: str):
    db.quety(Task).filter(Task.name == name).delete()
    db.commit()


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)

def add_new_project(db, name: str, description: str):
    new_project = Project(name=name, description=description)
    db.add(new_project)
    db.commit()

def get_projects(db):
    return db.query(Project).all()

def get_project_by_id(db, cid: int):
    return db.query(Project).filter(Project.id == cid).first()

def get_project(db, name: str):
    return db.query(Project).filter(Project.name == name).first()

def delete_project(db, name: str):
    db.query(Project).filter(Project.name == name).delete()
    db.commit()


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, index=True)
    task_id = Column(Integer, index=True)
    message = Column(String, index=True)

def add_new_comment(db, author_id: int, task_id: int, message: str):
    new_comment = Comment(author_id=author_id, task_id=task_id, message=message)
    db.add(new_comment)
    db.commit()

def get_comments(db, task_id: int):
    return db.query(Comment).filter(Comment.task_id == task_id).all()

def delete_comment(db, cid: int):
    db.query(Comment).filter(Comment.id == cid).delete()
    db.commit()

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

def add_new_category(db, name: str):
    new_category = Category(name=name)
    db.add(new_category)
    db.commit()

def get_categories(db):
    return db.query(Category).all()

def delete_categories(db, name: str):
    db.query(Category).filter(Category.name == name).delete()
    db.commit()

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, index = True)
    name = Column(String, index = True)
    body = Column(String)

def add_new_note(db, author_id: int, body: str, name: str):
    new_note = Note(author_id=author_id, body=body, name=name)
    db.add(new_note)
    db.commit()

def get_notes_by_author(db, author_id: int):
    return db.query(Note).filter(Note.author_id == author_id).all()

def get_notes(db):
    return db.query(Note).all()

def delete_note(db, name: str):
    db.query(Note).filter(Note.name == name).delete()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)
