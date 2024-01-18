from typing import Annotated
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Response,
    Request,
    Query,
    status,
    Security,
)
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from sqlalchemy.orm import Session
import uvicorn
from contextlib import asynccontextmanager
import datetime
from orm import crud, models, schemas
from orm.database import SessionLocal, engine
from sqlalchemy.exc import IntegrityError, NoResultFound
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from components import availability_checker
from components import facility_reserver
from components import credentials_manager as cm
from pydantic import ValidationError
import components

models.Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setupper = components.DBSetup(SessionLocal)
    setupper.setup()
    del setupper
    yield


app = FastAPI(
    title="Facility Booking API",
    description="Facility Booking API written for Software Engineering class",
    version="0.0.1",
    lifespan=lifespan,
)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "user": "Permissions of a user.",
        "admin": "Permissions of an admin.",
    },
)


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


# region SECURITY


@app.get("/me", response_model=schemas.User, tags=['Security'])
async def get_current_user(
    security_scopes: SecurityScopes,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
):
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    try:
        payload = jwt.decode(token, cm.SECRET_KEY, algorithms=[cm.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        token_data = schemas.TokenData(scopes=token_scopes, username=username)
    except (JWTError, ValidationError):
        raise credentials_exception
    users = crud.get_users(db, email=token_data.username)
    if not users:
        raise credentials_exception
    user = users[0]
    for scope in security_scopes.scopes:
        if scope not in token_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
    return user


@app.put("/me", response_model=schemas.User, tags=["Security"])
def update_me(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    email: str = Query(None),
    password: str = Query(None),
    name: str = Query(None),
    lastname: str = Query(None),
    phone_number: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.update_user(
            db=db,
            id_user=current_user.id_user,
            email=email,
            password=cm.get_password_hash(password) if password else None,
            name=name,
            lastname=lastname,
            phone_number=phone_number,
        )
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


@app.delete("/me/delete_reservation/", tags=["Security"])
def delete_reservation(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    reservation_id: int,
    db: Session = Depends(get_db),
):
    try:
        user_reservation_ids = [r.id_reservation for r in current_user.reservations]
        if reservation_id not in user_reservation_ids:
            raise NoResultFound("Reservation not found in user's reservations.")
        crud.delete_reservation(db, reservation_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})




@app.post("/token", response_model=schemas.Token, tags=['Security'])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    user = cm.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(
        minutes=cm.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    user_role = user.user_role.name.lower()
    scopes = ["user", "admin"] if user_role == "admin" else ["user"]
    access_token = cm.create_access_token(
        data={
            "sub": user.email,
            "scopes": scopes,
        },  # ser_role},#form_data.scopes},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


# endregion SECURITY

# region CRUD

# region USER ROLES


@app.post("/user_role/", response_model=schemas.UserRole, tags=["User Roles"])
def add_user_role(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    user_role: schemas.UserRoleCreate,
    db: Session = Depends(get_db),
):
    try:
        result = crud.add_user_role(db, user_role)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    return result


@app.delete("/user_role/", tags=["User Roles"])
def delete_user_role(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    user_role_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_user_role(db, user_role_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get(
    "/user_role/", response_model=list[schemas.UserRole], tags=["User Roles"]
)
def get_user_roles(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_user_role: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_user_roles(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/user_role/", response_model=schemas.UserRole, tags=["User Roles"])
def update_user_role(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_user_role: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_user_role(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect user_role information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion USER ROLES

# region USER


@app.post("/user/", response_model=schemas.User, tags=["Users"])
def add_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    try:
        user.password = cm.get_password_hash(user.password)
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
def delete_user(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    user_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_user(db, user_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/user/", response_model=list[schemas.User], tags=["Users"])
def get_users(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_user: int = Query(None),
    email: str = Query(None),
    # password: str = Query(None),
    name: str = Query(None),
    lastname: str = Query(None),
    phone_number: str = Query(None),
    user_role_name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_users(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.get("/actions/check_if_email_exists", tags=["Actions"])
def check_if_username_in_db(
    email: str,
    db: Session = Depends(get_db),
):
    results = crud.get_users(**locals())
    if results:
        return JSONResponse({"result": True}, 200)
    return JSONResponse({"result": False}, 200)


@app.put("/user/", response_model=schemas.User, tags=["Users"])
def update_user(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
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
        del current_user
        password = cm.get_password_hash(password)
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
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    reservation_status: schemas.ReservationStatusCreate,
    db: Session = Depends(get_db),
):
    try:
        result = crud.add_reservation_status(db, reservation_status)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    return result


@app.delete("/reservation_status/", tags=["Reservation Statuses"])
def delete_reservation_status(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    reservation_status_id: int,
    db: Session = Depends(get_db),
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
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_reservation_status: int = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_reservation_statuses(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put(
    "/reservation_status/",
    response_model=schemas.ReservationStatus,
    tags=["Reservation Statuses"],
)
def update_reservation_status(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_reservation_status: int = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_reservation_status(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect reservation_status information. Unique constraint violated.",
        )
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
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    facility_type: schemas.FacilityTypeCreate,
    db: Session = Depends(get_db),
):
    try:
        response = crud.add_facility_type(db, facility_type)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    return response


@app.delete("/facility_type/", tags=["Facility Types"])
def delete_facility_type(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    facility_type_id: int,
    db: Session = Depends(get_db),
):
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
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    id_facility_type: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_facility_types(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put(
    "/facility_type/",
    response_model=schemas.FacilityType,
    tags=["Facility Types"],
)
def update_facility_type(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_facility_type: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_facility_type(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect facility_type information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion FACILITY TYPES


# region CITIES
@app.post("/city/", response_model=schemas.City, tags=["Cities"])
def add_city(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    city: schemas.CityCreate,
    db: Session = Depends(get_db),
):
    try:
        response = crud.add_city(db, city)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    return response


@app.delete("/city/", tags=["Cities"])
def delete_city(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    city_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_city(db, city_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/city/", response_model=list[schemas.City], tags=["Cities"])
def get_cities(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    id_city: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_cities(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/city/", response_model=schemas.City, tags=["Cities"])
def update_city(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_city: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_city(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect city information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion CITIES


# region STATES
@app.post("/state/", response_model=schemas.State, tags=["States"])
def add_state(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    state: schemas.StateCreate,
    db: Session = Depends(get_db),
):
    try:
        response = crud.add_state(db, state)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    return response


@app.delete("/state/", tags=["States"])
def delete_state(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    state_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_state(db, state_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/state/", response_model=list[schemas.State], tags=["States"])
def get_states(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    id_state: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_states(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/state/", response_model=schemas.State, tags=["States"])
def update_state(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_state: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_state(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect state information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion STATES


# region ADRESSES


@app.post("/address/", response_model=schemas.Address, tags=["Addresses"])
def add_address(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    address: schemas.AddressCreate,
    db: Session = Depends(get_db),
):
    try:
        response = crud.add_address(db, address)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    return response


@app.delete("/address/", tags=["Addresses"])
def delete_address(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    address_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_address(db, address_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/address/", response_model=list[schemas.Address], tags=["Addresses"])
def get_addresses(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    id_address: int = Query(None),
    street_name: str = Query(None),
    building_number: int = Query(None),
    postal_code: str = Query(None),
    city_name: str = Query(None),
    state_name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_addresses(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/address/", response_model=schemas.Address, tags=["Addresses"])
def update_address(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_address: int = Query(None),
    street_name: str = Query(None),
    building_number: int = Query(None),
    postal_code: str = Query(None),
    city_name: str = Query(None),
    state_name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_address(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion ADDRESSES


# region DAYS
@app.post("/day/", response_model=schemas.Day, tags=["Days"])
def add_day(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    day: schemas.DayCreate,
    db: Session = Depends(get_db),
):
    try:
        response = crud.add_day(db, day)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    return response


@app.delete("/day/", tags=["Days"])
def delete_day(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    day_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_day(db, day_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/day/", response_model=list[schemas.Day], tags=["Days"])
def get_days(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    id_day: int = Query(None),
    day: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_days(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/day/", response_model=schemas.Day, tags=["Days"])
def update_day(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_day: int = Query(None),
    day: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_day(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect day information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion DAYS


# region OPEN HOURS


@app.post("/open_hour/", response_model=schemas.OpenHour, tags=["Open Hours"])
def add_open_hour(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    open_hour: schemas.OpenHourCreate,
    db: Session = Depends(get_db),
):
    try:
        response = crud.add_open_hour(db, open_hour)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return response


@app.delete("/open_hour/", tags=["Open Hours"])
def delete_open_hour(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    open_hour_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_open_hour(db, open_hour_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get(
    "/open_hour/", response_model=list[schemas.OpenHour], tags=["Open Hours"]
)
def get_open_houres(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    id_open_hours: int = Query(None),
    day_name: str = Query(None),
    start_hour: datetime.time = Query(None),
    end_hour: datetime.time = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_open_hours(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/open_hour/", response_model=schemas.OpenHour, tags=["Open Hours"])
def update_open_hour(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_open_hours: int = Query(None),
    day_name: str = Query(None),
    start_hour: datetime.time = Query(None),
    end_hour: datetime.time = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_open_hour(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion OPEN HOURS


# region COMPANIES


@app.post("/company/", response_model=schemas.Company, tags=["Companies"])
def add_company(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    company: schemas.CompanyCreate,
    db: Session = Depends(get_db),
):
    try:
        response = crud.add_company(db, company)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return response


@app.delete("/company/", tags=["Companies"])
def delete_company(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    company_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_company(db, company_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/company/", response_model=list[schemas.Company], tags=["Companies"])
def get_companies(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    id_company: int = Query(None),
    name=Query(None),
    nip=Query(None),
    phone_number=Query(None),
    id_address=Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_companies(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/company/", response_model=schemas.Company, tags=["Companies"])
def update_company(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_company: int = Query(None),
    name=Query(None),
    nip=Query(None),
    phone_number=Query(None),
    id_address=Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_company(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion COMPANIES


# region IMAGES
@app.post("/image/", response_model=schemas.Image, tags=["Images"])
def add_image(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    image: schemas.ImageCreate,
    db: Session = Depends(get_db),
):
    try:
        response = crud.add_image(db, image)
    except IntegrityError as e:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    return response


@app.delete("/image/", tags=["Images"])
def delete_image(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    image_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_image(db, image_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/image/", response_model=list[schemas.Image], tags=["Images"])
def get_images(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    id_image: int = Query(None),
    image_path: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_images(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/image/", response_model=schemas.Image, tags=["Images"])
def update_image(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_image: int = Query(None),
    image_path: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_image(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect image information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion IMAGES

# region FACILITIES


@app.post("/facility/", response_model=schemas.Facility, tags=["Facilities"])
def add_facility(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    facility: schemas.FacilityCreate,
    db: Session = Depends(get_db),
):
    try:
        response = crud.add_facility(db, facility)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return response


@app.delete("/facility/", tags=["Facilities"])
def delete_facility(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    facility_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_facility(db, facility_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get(
    "/facility/", response_model=list[schemas.Facility], tags=["Facilities"]
)
def get_facilities(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    id_facility: int = Query(None),
    name: str = Query(None),
    description: str = Query(None),
    price_hourly: float = Query(None),
    id_facility_type: int = Query(None),
    id_address: int = Query(None),
    id_company: int = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_facilities(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results



@app.get(
    "/facility/search", response_model=list[schemas.Facility], tags=["Facilities"]
)
def search_facility(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    name: str = Query(None),
    description: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.search_facilities(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put(
    "/facility/", response_model=schemas.FacilityCreate, tags=["Facilities"]
)
def update_facility(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_facility: int = Query(None),
    name: str = Query(None),
    description: str = Query(None),
    price_hourly: float = Query(None),
    id_facility_type: int = Query(None),
    id_address: int = Query(None),
    id_company: int = Query(None),
    ids_open_hours: list[int] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_facility(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion FACILITIES


# region RESERVATIONS


@app.post(
    "/reservation/", response_model=schemas.Reservation, tags=["Reservations"]
)
def add_reservation(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    reservation: schemas.ReservationCreate,
    db: Session = Depends(get_db),
):
    try:
        response = crud.add_reservation(db, reservation)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return response


@app.delete("/reservation/", tags=["Reservations"])
def delete_reservation(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    reservation_id: int,
    db: Session = Depends(get_db),
):
    try:
        crud.delete_reservation(db, reservation_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get(
    "/reservation/",
    response_model=list[schemas.Reservation],
    tags=["Reservations"],
)
def get_reservations(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_reservation: int = Query(None),
    date: datetime.date = Query(None),
    start_hour: datetime.time = Query(None),
    end_hour: datetime.time = Query(None),
    price_final: float = Query(None),
    id_user: int = Query(None),
    id_facility: int = Query(None),
    id_status: int = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.get_reservations(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put(
    "/reservation/", response_model=schemas.Reservation, tags=["Reservations"]
)
def update_reservation(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["admin"])
    ],
    id_reservation: int = Query(None),
    date: datetime.date = Query(None),
    start_hour: datetime.time = Query(None),
    end_hour: datetime.time = Query(None),
    price_final: float = Query(None),
    id_user: int = Query(None),
    id_facility: int = Query(None),
    id_status: int = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del current_user
        results = crud.update_reservation(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


# endregion RESERVATIONS

# endregion CRUD


# region ACTIONS


@app.get("/actions/check_availability/", tags=["Actions"])
def check_availability(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    id_facility: int,
    date: datetime.date,
    start_hour: datetime.time,
    end_hour: datetime.time,
    db: Session = Depends(get_db),
):
    try:
        del current_user
        result = availability_checker.check_availability(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": result})


@app.get("/actions/reserve/", tags=["Actions"])
def reserve(
    current_user: Annotated[
        schemas.User, Security(get_current_user, scopes=["user"])
    ],
    id_facility: int,
    id_user: int,
    date: datetime.date,
    start_hour: datetime.time,
    end_hour: datetime.time,
    db: Session = Depends(get_db),
):
    try:
        del current_user
        result = availability_checker.check_availability(**locals())
        if result:
            result = facility_reserver.reserve(**locals())

    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated or one of the object ids not in the database.",
        )
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": result})


# endregion ACTIONS


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, workers=1)
