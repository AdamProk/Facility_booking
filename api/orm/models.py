from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship


from .database import Base, engine


class UserRole(Base):
    __tablename__ = "user_roles"

    id_user_role = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    users = relationship("User", back_populates="user_role")


class User(Base):
    __tablename__ = "users"

    id_user = Column(Integer, primary_key=True, index=True)

    user_role_id = Column(
        Integer, ForeignKey("user_roles.id_user_role"), default=1
    )
    user_role = relationship("UserRole", back_populates="users")

    email = Column(String, unique=True)
    password = Column(String)
    name = Column(String)
    lastname = Column(String)
    phone_number = Column(String)


class ReservationStatus(Base):
    __tablename__ = "reservation_statuses"

    id_reservation_status = Column(Integer, primary_key=True)
    status = Column(String, nullable=False, unique=True)

    # users = relationship('User', back_populates='user_role')


class FacilityType(Base):
    __tablename__ = "facility_types"

    id_facility_type = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    # users = relationship('User', back_populates='user_role')


class City(Base):
    __tablename__ = "cities"

    id_city = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    addresses = relationship("Address", back_populates="city")


class State(Base):
    __tablename__ = "states"

    id_state = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    addresses = relationship("Address", back_populates="state")


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = (UniqueConstraint("id_city", "id_state", "street_name", "building_number"),)

    id_address = Column(Integer, primary_key=True)

    id_city = Column(Integer, ForeignKey("cities.id_city"), default=1)
    city = relationship("City", back_populates="addresses")

    id_state = Column(Integer, ForeignKey("states.id_state"), default=1)
    state = relationship("State", back_populates="addresses")

    street_name = Column(String, nullable=False)
    building_number = Column(Integer, nullable=False)
    postal_code = Column(String, nullable=False)
