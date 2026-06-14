from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select

from database import engine, create_db
from model import User, UserCreate, UserRead, UserUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield


app = FastAPI(lifespan=lifespan)

@app.post("/users", response_model=UserRead)
def create_user(user: UserCreate):
    db_user = User.model_validate(user)

    with Session(engine) as session:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

        return db_user

@app.get("/users", response_model=list[UserRead])
def get_users():
    with Session(engine) as session:
        users = session.exec(
            select(User)
        ).all()

        return users


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return user


@app.put("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserUpdate
):
    with Session(engine) as session:
        user = session.get(User, user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        update_data = user_update.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(user, key, value)

        session.add(user)
        session.commit()
        session.refresh(user)

        return user

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        session.delete(user)
        session.commit()

        return {
            "message": "User deleted successfully"
        }