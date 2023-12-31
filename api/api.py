from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Response, Request, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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
from passlib.context import CryptContext
import components

models.Base.metadata.create_all(bind=engine)

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


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
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db, username: str, password: str):
    users = crud.get_users(db, email=username)
    if not users:
        return False
    user = users[0]
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.get("/me", response_model=schemas.User)
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=email)
    except JWTError:
        raise credentials_exception
    with SessionLocal() as db:
        users = crud.get_users(db, email=token_data.username)
        if users is None:
            raise credentials_exception
        return users[0]



@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}



# endregion SECURITY

# region CRUD

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
    token: Annotated[str, Depends(oauth2_scheme)],
    id_user_role: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        del token
        results = crud.get_user_roles(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/user_role/", response_model=schemas.UserRole, tags=["User Roles"])
def update_user_role(
    id_user_role: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
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
def add_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        user.password = get_password_hash(user.password)
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
    # password: str = Query(None),
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


@app.put(
    "/reservation_status/",
    response_model=schemas.ReservationStatus,
    tags=["Reservation Statuses"],
)
def update_reservation_status(
    id_reservation_status: int = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
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


@app.put(
    "/facility_type/",
    response_model=schemas.FacilityType,
    tags=["Facility Types"],
)
def update_facility_type(
    id_facility_type: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
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


@app.put("/city/", response_model=schemas.City, tags=["Cities"])
def update_city(
    id_city: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
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


@app.put("/state/", response_model=schemas.State, tags=["States"])
def update_state(
    id_state: int = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
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
def add_address(address: schemas.AddressCreate, db: Session = Depends(get_db)):
    try:
        response = crud.add_address(db, address)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
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


@app.put("/day/", response_model=schemas.Day, tags=["Days"])
def update_day(
    id_day: int = Query(None),
    day: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
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
    open_hour: schemas.OpenHourCreate, db: Session = Depends(get_db)
):
    try:
        response = crud.add_open_hour(db, open_hour)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
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
    id_open_hours: int = Query(None),
    day_name: str = Query(None),
    start_hour: datetime.time = Query(None),
    end_hour: datetime.time = Query(None),
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
    id_open_hours: int = Query(None),
    day_name: str = Query(None),
    start_hour: datetime.time = Query(None),
    end_hour: datetime.time = Query(None),
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
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
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


# region IMAGES
@app.post("/image/", response_model=schemas.Image, tags=["Images"])
def add_image(image: schemas.ImageCreate, db: Session = Depends(get_db)):
    try:
        response = crud.add_image(db, image)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    return response


@app.delete("/image/", tags=["Images"])
def delete_image(image_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_image(db, image_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get("/image/", response_model=list[schemas.Image], tags=["Images"])
def get_images(
    id_image: int = Query(None),
    image_path: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
        results = crud.get_images(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put("/image/", response_model=schemas.Image, tags=["Images"])
def update_image(
    id_image: int = Query(None),
    image_path: str = Query(None),
    db: Session = Depends(get_db),
):
    try:
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
    facility: schemas.FacilityCreate, db: Session = Depends(get_db)
):
    try:
        response = crud.add_facility(db, facility)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return response


@app.delete("/facility/", tags=["Facilities"])
def delete_facility(facility_id: int, db: Session = Depends(get_db)):
    try:
        crud.delete_facility(db, facility_id)
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": True})


@app.get(
    "/facility/", response_model=list[schemas.Facility], tags=["Facilities"]
)
def get_facilities(
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
        results = crud.get_facilities(**locals())
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return results


@app.put(
    "/facility/", response_model=schemas.FacilityCreate, tags=["Facilities"]
)
def update_facility(
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
        results = crud.update_facility(**locals())
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


# endregion FACILITIES


# region RESERVATIONS


@app.post(
    "/reservation/", response_model=schemas.Reservation, tags=["Reservations"]
)
def add_reservation(
    reservation: schemas.ReservationCreate, db: Session = Depends(get_db)
):
    try:
        response = crud.add_reservation(db, reservation)
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    except NoResultFound:
        raise HTTPException(
            status_code=404, detail="No occurence found in the database."
        )
    return response


@app.delete("/reservation/", tags=["Reservations"])
def delete_reservation(reservation_id: int, db: Session = Depends(get_db)):
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
        results = crud.update_reservation(**locals())
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


# endregion RESERVATIONS

# endregion CRUD


# region ACTIONS


@app.get("/actions/check_availability/", tags=["Actions"])
def check_availability(
    id_facility: int,
    date: datetime.date,
    start_hour: datetime.time,
    end_hour: datetime.time,
    db: Session = Depends(get_db),
):
    try:
        result = availability_checker.check_availability(**locals())
    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": result})


@app.get("/actions/reserve/", tags=["Actions"])
def reserve(
    id_facility: int,
    id_user: int,
    date: datetime.date,
    start_hour: datetime.time,
    end_hour: datetime.time,
    db: Session = Depends(get_db),
):
    try:
        result = availability_checker.check_availability(**locals())
        if result:
            result = facility_reserver.reserve(**locals())

    except IntegrityError:
        raise HTTPException(
            status_code=500,
            detail="Incorrect information. Unique constraint violated.",
        )
    except NoResultFound as e:
        raise HTTPException(status_code=404, detail=e.args[0])
    return JSONResponse({"result": result})


# endregion ACTIONS


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, workers=1)
