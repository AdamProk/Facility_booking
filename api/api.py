from fastapi import Depends, FastAPI, HTTPException, Response, Request, Query
from sqlalchemy.orm import Session
import uvicorn
from orm import crud, models, schemas
from orm.database import SessionLocal, engine
from sqlalchemy.exc import IntegrityError, NoResultFound
from fastapi.responses import JSONResponse

models.Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Facility Booking API",
    description="Facility Booking API written for Software Engineering class",
    version="0.0.1",
)
tags_metadata = [
    {
        "name": "Users",
        "description": "",
    },
    {
        "name": "User Roles",
        "description": "",
    },
]


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response


# Dependency
def get_db(request: Request):
    return request.state.db


# region USER ROLES


@app.post("/user_role/", response_model=schemas.UserRole, tags=["User Roles"])
def add_user_role(
    user_role: schemas.UserRoleCreate, db: Session = Depends(get_db)
):
    return crud.add_user_role(db, user_role)


@app.delete("/user_role/", tags=['User Roles'])
def delete_user_role(user_role_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_user_role(db, user_role_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get(
    "/user_role/", response_model=list[schemas.UserRole], tags=["User Roles"]
)
def get_user_roles(
    id_user_role: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_user_roles(
            db,
            id_user_role=id_user_role,
            name=name,
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No user found in the database."
        )
    return results


# endregion USER ROLES

# region USER


@app.post("/user/", response_model=schemas.User, tags=["Users"])
def add_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        response = crud.add_user(db, user)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect user information. Unique constraint violated.",
        )
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])

    return response


@app.delete("/user/", tags=["Users"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_user(db, user_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/user/", response_model=list[schemas.User], tags=["Users"])
def get_users(
    id_user: int = Query(None),
    email: str = Query(None),
    password: str = Query(None),
    name: str = Query(None),
    lastname: str = Query(None),
    phone_number: str = Query(None),
    user_role_name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_users(
            db,
            id_user,
            email,
            password,
            name,
            lastname,
            phone_number,
            user_role_name,
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No user found in the database."
        )
    return results


@app.put("/user/", response_model=schemas.User, tags=["Users"])
def update_user(
    id_user: int = Query(None),
    email: str = Query(None),
    password: str = Query(None),
    name: str = Query(None),
    lastname: str = Query(None),
    phone_number: str = Query(None),
    user_role_name: str = Query(None),
    db: Session = Depends(get_db),
):
    update_data = {
        "email": email,
        "password": password,
        "name": name,
        "lastname": lastname,
        "phone_number": phone_number,
        "user_role_name": user_role_name,
    }
    try:
        results = crud.update_user(db, id_user, update_data)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect user information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No user found in the database."
        )
    return results


# endregion USER

# region RESERVATIONS


# endregion RESERVATIONS

# @app.get("/users/", response_model=list[schemas.User])
# def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = crud.get_users(db, skip=skip, limit=limit)
#     return users


# @app.get("/users/{user_id}", response_model=schemas.User)
# def read_user(user_id: int, db: Session = Depends(get_db)):
#     db_user = crud.get_user(db, user_id=user_id)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user


# @app.post("/users/{user_id}/items/", response_model=schemas.Item)
# def create_item_for_user(
#     user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
# ):
#     return crud.create_user_item(db=db, item=item, user_id=user_id)


# @app.get("/items/", response_model=list[schemas.Item])
# def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     items = crud.get_items(db, skip=skip, limit=limit)
#     return items


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, workers=1)
