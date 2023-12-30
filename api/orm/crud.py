from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from . import models, schemas


class ElementNotFound(Exception):
    pass


def add_user(db: Session, user: schemas.UserCreate):
    user_dict = user.dict()
    user_dict["password"] = user.password + "notreallyhashed"
    user_role_id = get_user_role_by_name(
        db, user_dict.pop("user_role_name")
    ).id_user_role
    db_user = models.User(**user_dict)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_role_by_name(db, name):
    return (
        db.query(models.UserRole).filter(models.UserRole.name == name).first()
    )


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
    query_dict = { k: v for k,v in locals().items() if v is not None }
    del query_dict['db']

    q = db.query(models.User).filter(
        and_(
            *(
                getattr(models.User, key) == value
                for key, value in query_dict.items()
            )
        )
    )
    return q.all()


# def get_user(db: Session, user_id: int):
#     return db.query(models.User).filter(models.User.id == user_id).first()


# def get_user_by_email(db: Session, email: str):
#     return db.query(models.User).filter(models.User.email == email).first()


# def get_users(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.User).offset(skip).limit(limit).all()


# def create_user(db: Session, user: schemas.UserCreate):
#     fake_hashed_password = user.password + "notreallyhashed"
#     db_user = models.User(
#         email=user.email, hashed_password=fake_hashed_password
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user


# def get_items(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Item).offset(skip).limit(limit).all()


# def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
#     db_item = models.Item(**item.dict(), owner_id=user_id)
#     db.add(db_item)
#     db.commit()
#     db.refresh(db_item)
#     return db_item
