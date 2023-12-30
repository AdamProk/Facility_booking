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
    try:
        result = crud.add_user_role(db, user_role)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    return result


@app.delete("/user_role/", tags=["User Roles"])
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
        results = crud.get_user_roles(**locals())
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
        results = crud.get_users(**locals())
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
    try:
        results = crud.update_user(**locals())
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
@app.post(
    "/reservation_status/",
    response_model=schemas.ReservationStatus,
    tags=["Reservation Statuses"],
)
def add_reservation_status(
    reservation_status: schemas.ReservationStatusCreate,
    db: Session = Depends(get_db),
):
    try:
        result = crud.add_reservation_status(db, reservation_status)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    return result


@app.delete("/reservation_status/", tags=["Reservation Statuses"])
def delete_reservation_status(
    reservation_status_id: int, db: Session = Depends(get_db)
):
    try:
        crud.delete_reservation_status(db, reservation_status_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get(
    "/reservation_status/",
    response_model=list[schemas.ReservationStatus],
    tags=["Reservation Statuses"],
)
def get_reservation_statuses(
    id_reservation_status: int = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_reservation_statuses(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion RESERVATION STATUSES


# region FACILITY TYPES
@app.post(
    "/facility_type/",
    response_model=schemas.FacilityType,
    tags=["Facility Types"],
)
def add_facility_type(
    facility_type: schemas.FacilityTypeCreate, db: Session = Depends(get_db)
):
    try:
        response = crud.add_facility_type(db, facility_type)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    return response


@app.delete("/facility_type/", tags=["Facility Types"])
def delete_facility_type(facility_type_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_facility_type(db, facility_type_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get(
    "/facility_type/",
    response_model=list[schemas.FacilityType],
    tags=["Facility Types"],
)
def get_facility_types(
    id_facility_type: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_facility_types(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion FACILITY TYPES


# region CITIES
@app.post("/city/", response_model=schemas.City, tags=["Cities"])
def add_city(city: schemas.CityCreate, db: Session = Depends(get_db)):
    try:
        response = crud.add_city(db, city)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    return response


@app.delete("/city/", tags=["Cities"])
def delete_city(city_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_city(db, city_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/city/", response_model=list[schemas.City], tags=["Cities"])
def get_cities(
    id_city: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_cities(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion CITIES


# region STATES
@app.post("/state/", response_model=schemas.State, tags=["States"])
def add_state(state: schemas.StateCreate, db: Session = Depends(get_db)):
    try:
        response = crud.add_state(db, state)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    return response


@app.delete("/state/", tags=["States"])
def delete_state(state_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_state(db, state_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/state/", response_model=list[schemas.State], tags=["States"])
def get_states(
    id_state: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_states(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion STATES


# region ADRESSES


@app.post("/address/", response_model=schemas.Address, tags=["Addresses"])
def add_address(address: schemas.AddressCreate, db: Session = Depends(get_db)):
    try:
        response = crud.add_address(db, address)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    return response


@app.delete("/address/", tags=["Addresses"])
def delete_address(address_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_address(db, address_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/address/", response_model=list[schemas.Address], tags=["Addresses"])
def get_addresses(
    id_address: int = Query(None),
    street_name: str = Query(None),
    building_number: int = Query(None),
    postal_code: str = Query(None),
    city_name: str = Query(None),
    state_name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_addresses(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/address/", response_model=schemas.Address, tags=["Addresses"])
def update_address(
    id_address: int = Query(None),
    street_name: str = Query(None),
    building_number: int = Query(None),
    postal_code: str = Query(None),
    city_name: str = Query(None),
    state_name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.update_address(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion ADDRESSES


# region DAYS


@app.post("/day/", response_model=schemas.Day, tags=["Days"])
def add_day(day: schemas.DayCreate, db: Session = Depends(get_db)):
    try:
        response = crud.add_day(db, day)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    return response


@app.delete("/day/", tags=["Days"])
def delete_day(day_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_day(db, day_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/day/", response_model=list[schemas.Day], tags=["Days"])
def get_days(
    id_day: int = Query(None),
    day: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_days(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion DAYS


# region OPEN HOURS


@app.post("/open_hour/", response_model=schemas.OpenHour, tags=["Open Hours"])
def add_open_hour(
    open_hour: schemas.OpenHourCreate, db: Session = Depends(get_db)
):
    try:
        response = crud.add_open_hour(db, open_hour)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    return response


@app.delete("/open_hour/", tags=["Open Hours"])
def delete_open_hour(open_hour_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_open_hour(db, open_hour_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get(
    "/open_hour/", response_model=list[schemas.OpenHour], tags=["Open Hours"]
)
def get_open_houres(
    id_open_hour: int = Query(None),
    day_name: str = Query(None),
    start_hour: str = Query(None),
    end_hour: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_open_hours(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/open_hour/", response_model=schemas.OpenHour, tags=["Open Hours"])
def update_open_hour(
    id_open_hour: int = Query(None),
    day_name: str = Query(None),
    start_hour: str = Query(None),
    end_hour: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.update_open_hour(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion OPEN HOURS


# region COMPANIES


@app.post("/company/", response_model=schemas.Company, tags=["Companies"])
def add_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    try:
        response = crud.add_company(db, company)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    return response


@app.delete("/company/", tags=["Companies"])
def delete_company(company_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_company(db, company_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/company/", response_model=list[schemas.Company], tags=["Companies"])
def get_companies(
    id_company: int = Query(None),
    name=Query(None),
    nip=Query(None),
    phone_number=Query(None),
    id_address=Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_companies(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/company/", response_model=schemas.Company, tags=["Companies"])
def update_company(
    id_company: int = Query(None),
    name=Query(None),
    nip=Query(None),
    phone_number=Query(None),
    id_address=Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.update_company(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion ADDRESSES


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, workers=1)
