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
            status_code=404, detail="No occurence found in the database."
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
            status_code=404, detail="No occurence found in the database."
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
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion USER



# region RESERVATION STATUSES
@app.post("/reservation_status/", response_model=schemas.ReservationStatus, tags=["Reservation Statuses"])
def add_reservation_status(
    reservation_status: schemas.ReservationStatusCreate, db: Session = Depends(get_db)
):
    return crud.add_reservation_status(db, reservation_status)


@app.delete("/reservation_status/", tags=['Reservation Statuses'])
def delete_reservation_status(reservation_status_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_reservation_status(db, reservation_status_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get(
    "/reservation_status/", response_model=list[schemas.ReservationStatus], tags=["Reservation Statuses"]
)
def get_reservation_statuses(
    id_reservation_status: int = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_reservation_statuses(
            db,
            id_reservation_status=id_reservation_status,
            status=status,
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion RESERVATION STATUSES


# region FACILITY TYPES
@app.post("/facility_type/", response_model=schemas.FacilityType, tags=["Facility Types"])
def add_facility_type(
    facility_type: schemas.FacilityTypeCreate, db: Session = Depends(get_db)
):
    return crud.add_facility_type(db, facility_type)


@app.delete("/facility_type/", tags=['Facility Types'])
def delete_facility_type(facility_type_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_facility_type(db, facility_type_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get(
    "/facility_type/", response_model=list[schemas.FacilityType], tags=["Facility Types"]
)
def get_facility_types(
    id_facility_type: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_facility_types(
            db,
            id_facility_type=id_facility_type,
            name=name,
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion FACILITY TYPES




if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, workers=1)
