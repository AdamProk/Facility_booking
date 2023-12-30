from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy import and_, or_
from . import models, schemas


class ElementNotFound(Exception):
    pass


class NoConnectionWithDB(Exception):
    pass


def dict_query_and(model, query_dict, db=None):
    db = query_dict.pop("db", None)
    if db is None:
        raise NoConnectionWithDB(
            "No connection with the database was provided"
        )
    if len(query_dict) > 1:  # If query contains any criteria
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
    db=None,
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


# endregion USER ROLES

# region USERS


def add_user(db: Session, user: schemas.UserCreate):
    user_dict = user.model_dump()
    user_dict["password"] = user.password + "notreallyhashed"
    matching_user_roles = get_user_roles(
        db, name=user_dict.pop("user_role_name")
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
    db=None,
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
        roles = get_user_roles(db, name=query_dict.pop("user_role_name"))
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
    db=None,
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
    db=None,
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


# endregion RESERVATION STATUSES


# region FACILITY TYPES


def add_facility_type(db: Session, facility_type: schemas.FacilityTypeCreate):
    new_obj = models.FacilityType(**facility_type.model_dump())
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_facility_types(
    db=None,
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


# endregion CITIES


# region STATES


def add_state(db: Session, state: schemas.StateCreate):
    new_obj = models.State(**state.model_dump())
    db.add(new_obj)
    db.commit()
    db.refresh(new_obj)
    return new_obj


def get_states(
    db=None,
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


# endregion STATES


# region ADDRESSES


def add_address(db: Session, address: schemas.AddressCreate):

    cities = get_cities(db, name=address.city_name)
    states = get_states(db, name=address.state_name)
    if len(cities) < 1:
        raise NoResultFound("No city with specified name in the database.")
    if len(states) < 1:
        raise NoResultFound("No state with specified name in the database.")

    address_dict = address.model_dump(exclude=['city_name', 'state_name'])
    address_dict['id_city'] = cities[0].id_city
    address_dict['id_state'] = states[0].id_state

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
        results = get_cities(db, name=query_dict.pop("city_name"))
        if len(results) < 1:
            return []
        query_dict["id_city"] = results[0].id_city


    if state_name is not None:
        results = get_states(db, name=query_dict.pop("state_name"))
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


# endregion ADDRESSES
