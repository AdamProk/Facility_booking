from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy import and_, or_
from . import models, schemas


def dict_query_and(model, query_dict, db=None):
    db = query_dict.pop("db", None)
    if db is None:
        raise NoConnectionWithDB(
            "No connection with the database was provided"
        )
    if len(query_dict) > 0:  # If query contains any criteria
        q = db.query(model).filter(
            and_(
                *(
                    getattr(model, key) == value
                    for key, value in query_dict.items()
                )
            )
        )
    else:  # If query is empty: return all users
        q = db.query(model)

    return q.all()


# region USER ROLES


def add_user_role(db: Session, user_role: schemas.UserRoleCreate):
    db_user_role = models.UserRole(**user_role.model_dump())
    db.add(db_user_role)
    db.commit()
    db.refresh(db_user_role)
    return db_user_role


def get_user_roles(
    db,
    id_user_role=None,
    name=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    return dict_query_and(models.UserRole, query_dict)


def delete_user_role(db: Session, user_role_id: int):
    query = db.query(models.UserRole).filter(
        models.UserRole.id_user_role == user_role_id
    )
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_user_role(
    db,
    id_user_role=None,
    name=None,
):
    user_role = (
        db.query(models.UserRole)
        .filter(models.UserRole.id_user_role == id_user_role)
        .first()
    )

    if user_role is None:
        raise NoResultFound("No user_role found with this id in the database.")

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(user_role, key, value)

    db.commit()

    return user_role


# endregion USER ROLES

# region USERS


def add_user(db: Session, user: schemas.UserCreate):
    user_dict = user.model_dump()
    user_dict["password"] = user.password + "notreallyhashed"
    matching_user_roles = get_user_roles(
        db, name=user_dict.pop("user_role_name").capitalize()
    )
    if len(matching_user_roles) < 1:
        raise NoResultFound("User role not found.")

    user_dict["user_role_id"] = matching_user_roles[0].id_user_role

    db_user = models.User(**user_dict)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(
    db,
    id_user=None,
    email=None,
    password=None,
    name=None,
    lastname=None,
    phone_number=None,
    user_role_name=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    if user_role_name:
        roles = get_user_roles(db, name=query_dict.pop("user_role_name").capitalize())
        if len(roles) < 1:
            return []
        query_dict["user_role_id"] = roles[0].id_user_role

    return dict_query_and(models.User, query_dict)


def delete_user(db: Session, user_id: int):
    query = db.query(models.User).filter(models.User.id_user == user_id)
    if query.first() is None:
        raise NoResultFound(
            "No occurence was found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_user(
    db,
    id_user=None,
    email=None,
    password=None,
    name=None,
    lastname=None,
    phone_number=None,
    user_role_name=None,
):
    user = db.query(models.User).filter(models.User.id_user == id_user).first()

    if user is None:
        raise NoResultFound("No user found with this id in the database.")

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(user, key, value)

    db.commit()

    return user


# endregion USERS

# region RESERVATION STATUSES


def add_reservation_status(
    db: Session, reservation_status: schemas.ReservationStatusCreate
):
    new_obj = models.ReservationStatus(**reservation_status.model_dump())
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_reservation_statuses(
    db,
    id_reservation_status=None,
    status=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    return dict_query_and(models.ReservationStatus, query_dict)


def delete_reservation_status(db: Session, reservation_status_id: int):
    query = db.query(models.ReservationStatus).filter(
        models.ReservationStatus.id_reservation_status == reservation_status_id
    )
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_reservation_status(
    db,
    id_reservation_status=None,
    status=None,
):
    reservation_status = (
        db.query(models.ReservationStatus)
        .filter(
            models.ReservationStatus.id_reservation_status
            == id_reservation_status
        )
        .first()
    )

    if reservation_status is None:
        raise NoResultFound(
            "No reservation_status found with this id in the database."
        )

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(reservation_status, key, value)

    db.commit()

    return reservation_status


# endregion RESERVATION STATUSES

# region FACILITY TYPES


def add_facility_type(db: Session, facility_type: schemas.FacilityTypeCreate):
    new_obj = models.FacilityType(**facility_type.model_dump())
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_facility_types(
    db,
    id_facility_type=None,
    name=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    return dict_query_and(models.FacilityType, query_dict)


def delete_facility_type(db: Session, facility_type_id: int):
    query = db.query(models.FacilityType).filter(
        models.FacilityType.id_facility_type == facility_type_id
    )
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_facility_type(
    db,
    id_facility_type=None,
    name=None,
):
    facility_type = (
        db.query(models.FacilityType)
        .filter(models.FacilityType.id_facility_type == id_facility_type)
        .first()
    )

    if facility_type is None:
        raise NoResultFound(
            "No facility_type found with this id in the database."
        )

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(facility_type, key, value)

    db.commit()

    return facility_type


# endregion FACILITY TYPE

# region CITIES


def add_city(db: Session, city: schemas.CityCreate):
    new_obj = models.City(**city.model_dump())
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_cities(
    db,
    id_city=None,
    name=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    return dict_query_and(models.City, query_dict)


def delete_city(db: Session, city_id: int):
    query = db.query(models.City).filter(models.City.id_city == city_id)
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_city(
    db,
    id_city=None,
    name=None,
):
    city = db.query(models.City).filter(models.City.id_city == id_city).first()

    if city is None:
        raise NoResultFound("No city found with this id in the database.")

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(city, key, value)

    db.commit()

    return city


# endregion CITIES

# region STATES


def add_state(db: Session, state: schemas.StateCreate):
    new_obj = models.State(**state.model_dump())
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_states(
    db,
    id_state=None,
    name=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    return dict_query_and(models.State, query_dict)


def delete_state(db: Session, state_id: int):
    query = db.query(models.State).filter(models.State.id_state == state_id)
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_state(
    db,
    id_state=None,
    name=None,
):
    state = (
        db.query(models.State)
        .filter(models.State.id_state == id_state)
        .first()
    )

    if state is None:
        raise NoResultFound("No state found with this id in the database.")

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(state, key, value)

    db.commit()

    return state


# endregion STATES

# region ADDRESSES


def add_address(db: Session, address: schemas.AddressCreate):
    cities = get_cities(db, name=address.city_name.capitalize())
    states = get_states(db, name=address.state_name.capitalize())
    if len(cities) < 1:
        raise NoResultFound("No city with specified name in the database.")
    if len(states) < 1:
        raise NoResultFound("No state with specified name in the database.")

    address_dict = address.model_dump(exclude=["city_name", "state_name"])
    address_dict["id_city"] = cities[0].id_city
    address_dict["id_state"] = states[0].id_state

    new_obj = models.Address(**address_dict)
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_addresses(
    db,
    id_address=None,
    street_name=None,
    building_number=None,
    postal_code=None,
    city_name=None,
    state_name=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    if city_name is not None:
        results = get_cities(db, name=query_dict.pop("city_name").capitalize())
        if len(results) < 1:
            return []
        query_dict["id_city"] = results[0].id_city

    if state_name is not None:
        results = get_states(db, name=query_dict.pop("state_name").capitalize())
        if len(results) < 1:
            return []
        query_dict["id_state"] = results[0].id_state

    return dict_query_and(models.Address, query_dict)


def delete_address(db: Session, address_id: int):
    query = db.query(models.Address).filter(
        models.Address.id_address == address_id
    )
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_address(
    db,
    id_address=None,
    street_name=None,
    building_number=None,
    postal_code=None,
    city_name=None,
    state_name=None,
):
    address = (
        db.query(models.Address)
        .filter(models.Address.id_address == id_address)
        .first()
    )

    if address is None:
        raise NoResultFound("No address found with this id in the database.")

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(address, key, value)

    db.commit()

    return address


# endregion ADDRESSES

# region DAYS


def add_day(db: Session, day: schemas.DayCreate):
    new_obj = models.Day(**day.model_dump())
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_days(
    db,
    id_day=None,
    day=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    return dict_query_and(models.Day, query_dict)


def delete_day(db: Session, day_id: int):
    query = db.query(models.Day).filter(models.Day.id_day == day_id)
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_day(
    db,
    id_day=None,
    day=None,
):
    day = db.query(models.Day).filter(models.Day.id_day == id_day).first()

    if day is None:
        raise NoResultFound("No day found with this id in the database.")

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(day, key, value)

    db.commit()

    return day


# endregion DAYS


# region OPEN HOURS
def add_open_hour(db: Session, open_hour: schemas.OpenHourCreate):
    days = get_days(db, day=open_hour.day_name.capitalize())
    if len(days) < 1:
        raise NoResultFound("No day with specified name in the database.")

    open_hour_dict = open_hour.model_dump(exclude=["day_name"])
    open_hour_dict["id_day"] = days[0].id_day

    new_obj = models.OpenHour(**open_hour_dict)
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_open_hours(
    db,
    id_open_hours=None,
    start_hour=None,
    end_hour=None,
    day_name=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    if day_name is not None:
        results = get_days(db, day=query_dict.pop("day_name").capitalize())
        if len(results) < 1:
            return []
        query_dict["id_day"] = results[0].id_day

    return dict_query_and(models.OpenHour, query_dict)


def delete_open_hour(db: Session, open_hour_id: int):
    query = db.query(models.OpenHour).filter(
        models.OpenHour.id_open_hour == open_hour_id
    )
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_open_hour(
    db,
    id_open_hours=None,
    start_hour=None,
    end_hour=None,
    day_name=None,
):
    open_hour = (
        db.query(models.OpenHour)
        .filter(models.OpenHour.id_open_hours == id_open_hours)
        .first()
    )

    if open_hour is None:
        raise NoResultFound("No open_hour found with this id in the database.")

    update_dict = locals()
    del update_dict["db"]

    days = get_days(db, day=day_name.capitalize())
    if len(days) < 1:
        raise NoResultFound("No day with specified name in the database.")
    update_dict["id_day"] = days[0].id_day

    for key, value in update_dict.items():
        if value is not None:
            setattr(open_hour, key, value)

    db.commit()

    return open_hour


# endregion OPEN HOURS

# region COMPANIES


def add_company(db: Session, company: schemas.CompanyCreate):
    addresses = get_addresses(db, id_address=company.id_address)
    if len(addresses) < 1:
        raise NoResultFound("No such address in the database.")

    new_obj = models.Company(**company.model_dump())
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_companies(
    db,
    id_company=None,
    name=None,
    nip=None,
    phone_number=None,
    id_address=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}
    return dict_query_and(models.Company, query_dict)


def delete_company(db: Session, company_id: int):
    query = db.query(models.Company).filter(
        models.Company.id_company == company_id
    )
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_company(
    db,
    id_company=None,
    name=None,
    nip=None,
    phone_number=None,
    id_address=None,
):
    company = (
        db.query(models.Company)
        .filter(models.Company.id_company == id_company)
        .first()
    )

    if company is None:
        raise NoResultFound("No company found with this id in the database.")

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(company, key, value)

    db.commit()

    return company


# endregion COMPANIES

# region IMAGES


def add_image(db: Session, image: schemas.ImageCreate):
    new_obj = models.Image(**image.model_dump())
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_images(
    db,
    id_image=None,
    image_path=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    return dict_query_and(models.Image, query_dict)


def delete_image(db: Session, image_id: int):
    query = db.query(models.Image).filter(models.Image.id_image == image_id)
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_image(
    db,
    id_image=None,
    name=None,
    nip=None,
    phone_number=None,
    id_address=None,
):
    image = (
        db.query(models.Image)
        .filter(models.Image.id_image == id_image)
        .first()
    )

    if image is None:
        raise NoResultFound("No image found with this id in the database.")

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(image, key, value)

    db.commit()

    return image


# endregion IMAGES

# region FACILITIES


def add_facility(db: Session, facility: schemas.FacilityCreate):
    addresses = get_addresses(db, id_address=facility.id_address)
    facility_types = get_facility_types(
        db, id_facility_type=facility.id_facility_type
    )
    companies = get_companies(db, id_company=facility.id_company)
    if len(addresses) < 1:
        raise NoResultFound("No address with specified id in the database.")
    if len(facility_types) < 1:
        raise NoResultFound(
            "No facility type with specified name in the database."
        )
    if len(companies) < 1:
        raise NoResultFound("No company with specified id in the database.")

    facility_dict = facility.model_dump()
    ids_open_hours = facility_dict.pop("ids_open_hours")
    new_obj = models.Facility(**facility_dict)
    for id_open_hour in ids_open_hours:
        results = get_open_hours(db, id_open_hours=id_open_hour)
        if len(results) < 1:
            raise NoResultFound(
                "No open_hours with specified id in the database."
            )
        new_obj.open_hours.append(results[0])
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_facilities(
    db,
    id_facility=None,
    name=None,
    description=None,
    price_hourly=None,
    id_facility_type=None,
    id_address=None,
    id_company=None,
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    return dict_query_and(models.Facility, query_dict)


def delete_facility(db: Session, facility_id: int):
    query = db.query(models.Facility).filter(
        models.Facility.id_facility == facility_id
    )
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_facility(
    db,
    id_facility=None,
    name=None,
    description=None,
    price_hourly=None,
    id_facility_type=None,
    id_address=None,
    id_company=None,
    ids_open_hours=None,
):
    facility = (
        db.query(models.Facility)
        .filter(models.Facility.id_facility == id_facility)
        .first()
    )

    if facility is None:
        raise NoResultFound("No facility found with this id in the database.")

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(facility, key, value)

    for id_open_hour in ids_open_hours:
        results = get_open_hours(db, id_open_hours=id_open_hour)
        if len(results) < 1:
            raise NoResultFound(
                "No open_hours with specified id in the database."
            )
        facility.open_hours.append(results[0])

    db.commit()

    return facility


# endregion FACILITIES


# region RESERVATIONS

def add_reservation(db: Session, reservation: schemas.ReservationCreate):
    users = get_users(db, id_user=reservation.id_user)
    statuses = get_reservation_statuses(
        db, id_reservation_status=reservation.id_status
    )
    facilities = get_facilities(db,id_facility=reservation.id_facility)

    if len(users) < 1:
        raise NoResultFound("No user with specified id in the database.")
    if len(statuses) < 1:
        raise NoResultFound(
            "No status with specified id in the database."
        )
    if len(facilities) < 1:
        raise NoResultFound("No facility with specified id in the database.")

    new_obj = models.Reservation(**reservation.model_dump())
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_reservations(
    db,
    id_reservation=None,
    date=None,
    start_hour=None,
    end_hour=None,
    price_final=None,
    id_user=None,
    id_facility=None,
    id_status=None
):
    query_dict = {k: v for k, v in locals().items() if v is not None}

    return dict_query_and(models.Reservation, query_dict)


def delete_reservation(db: Session, reservation_id: int):
    query = db.query(models.Reservation).filter(
        models.Reservation.id_reservation == reservation_id
    )
    if query.first() is None:
        raise NoResultFound(
            "No occurence found with this id was found in the database."
        )
    query.delete()
    db.commit()


def update_reservation(
    db,
    id_reservation=None,
    date=None,
    start_hour=None,
    end_hour=None,
    price_final=None,
    id_user=None,
    id_facility=None,
    id_status=None
):
    reservation = (
        db.query(models.Reservation)
        .filter(models.Reservation.id_reservation == id_reservation)
        .first()
    )

    if reservation is None:
        raise NoResultFound(
            "No reservation found with this id in the database."
        )

    update_dict = locals()
    del update_dict["db"]

    for key, value in update_dict.items():
        if value is not None:
            setattr(reservation, key, value)

    db.commit()

    return reservation


# endregion RESERVATIONS
