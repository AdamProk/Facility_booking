from sqlalchemy import (
    CheckConstraint,
    Boolean,
    Date,
    Table,
    Text,
    Float,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Time,
)
from sqlalchemy.orm import relationship, validates
from .database import Base, engine


facility_open_hours_association = Table(
    "facility_open_hours_association",
    Base.metadata,
    Column("id_facility", Integer, ForeignKey("facilities.id_facility")),
    Column("id_open_hours", Integer, ForeignKey("open_hours.id_open_hours")),
)


class UserRole(Base):
    __tablename__ = "user_roles"

    id_user_role = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    users = relationship("User", back_populates="user_role")

    @validates("name")
    def convert_upper(self, key, value):
        return value.capitalize()


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

    reservations = relationship("Reservation", back_populates="user")

    @validates("name", "lastname")
    def convert_upper(self, key, value):
        return value.capitalize()


class ReservationStatus(Base):
    __tablename__ = "reservation_statuses"

    id_reservation_status = Column(Integer, primary_key=True)
    status = Column(String, nullable=False, unique=True)

    reservations = relationship("Reservation", back_populates="status")

    @validates("status")
    def convert_upper(self, key, value):
        return value.capitalize()


class FacilityType(Base):
    __tablename__ = "facility_types"

    id_facility_type = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    facilities = relationship("Facility", back_populates="facility_type")

    @validates("name")
    def convert_upper(self, key, value):
        return value.capitalize()


class City(Base):
    __tablename__ = "cities"

    id_city = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    addresses = relationship("Address", back_populates="city")

    @validates("name")
    def convert_upper(self, key, value):
        return value.capitalize()


class State(Base):
    __tablename__ = "states"

    id_state = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    addresses = relationship("Address", back_populates="state")

    @validates("name")
    def convert_upper(self, key, value):
        return value.capitalize()


class Company(Base):
    __tablename__ = "companies"

    id_company = Column(Integer, primary_key=True)

    id_address = Column(Integer, ForeignKey("addresses.id_address"))
    address = relationship("Address", back_populates="company")

    name = Column(String, nullable=False, unique=True)
    nip = Column(String, nullable=False, unique=True)
    phone_number = Column(String, nullable=False)

    facilities = relationship("Facility", back_populates="company")

    @validates("name")
    def convert_upper(self, key, value):
        return value.capitalize()


class Address(Base):
    __tablename__ = "addresses"
    __table_args__ = (
        UniqueConstraint(
            "id_city", "id_state", "street_name", "building_number"
        ),
    )

    id_address = Column(Integer, primary_key=True)

    id_city = Column(Integer, ForeignKey("cities.id_city"), default=1)
    city = relationship("City", back_populates="addresses")

    id_state = Column(Integer, ForeignKey("states.id_state"), default=1)
    state = relationship("State", back_populates="addresses")

    street_name = Column(String, nullable=False)
    building_number = Column(Integer, nullable=False)
    postal_code = Column(String, nullable=False)

    company = relationship("Company", back_populates="address")
    facilities = relationship("Facility", back_populates="address")

    @validates("street_name")
    def convert_upper(self, key, value):
        return value.capitalize()


class Day(Base):
    __tablename__ = "days"

    id_day = Column(Integer, primary_key=True)
    day = Column(String, nullable=False)
    hours = relationship("OpenHour", back_populates="day")

    @validates("day")
    def convert_upper(self, key, value):
        return value.capitalize()


class OpenHour(Base):
    __tablename__ = "open_hours"
    __table_args__ = (UniqueConstraint("start_hour", "end_hour"),)

    id_open_hours = Column(Integer, primary_key=True)
    start_hour = Column(Time)
    end_hour = Column(Time)

    id_day = Column(Integer, ForeignKey("days.id_day"))
    day = relationship("Day", back_populates="hours")

    facilities = relationship(
        "Facility",
        secondary=facility_open_hours_association,
        back_populates="open_hours",
    )


class Image(Base):
    __tablename__ = "images"

    id_image = Column(Integer, primary_key=True)
    image_path = Column(String, nullable=False, unique=True)

    id_facility = Column(Integer, ForeignKey("facilities.id_facility"))
    facility = relationship("Facility", back_populates="images")


class Facility(Base):
    __tablename__ = "facilities"

    id_facility = Column(Integer, primary_key=True)

    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=False, unique=True)
    price_hourly = Column(Float)

    id_facility_type = Column(
        Integer, ForeignKey("facility_types.id_facility_type")
    )
    facility_type = relationship("FacilityType", back_populates="facilities")

    id_address = Column(Integer, ForeignKey("addresses.id_address"))
    address = relationship("Address", back_populates="facilities")

    id_company = Column(Integer, ForeignKey("companies.id_company"))
    company = relationship("Company", back_populates="facilities")

    reservations = relationship("Reservation", back_populates="facility")

    open_hours = relationship(
        "OpenHour",
        secondary=facility_open_hours_association,
        back_populates="facilities",
    )

    images = relationship("Image", back_populates="facility")

    @validates("name", "description")
    def convert_upper(self, key, value):
        return value.capitalize()


class Reservation(Base):
    __tablename__ = "reservations"

    id_reservation = Column(Integer, primary_key=True)

    date = Column(Date)
    start_hour = Column(Time)
    end_hour = Column(Time)
    price_final = Column(Float)

    id_user = Column(Integer, ForeignKey("users.id_user"))
    user = relationship("User", back_populates="reservations")

    id_facility = Column(Integer, ForeignKey("facilities.id_facility"))
    facility = relationship("Facility", back_populates="reservations")

    id_status = Column(
        Integer, ForeignKey("reservation_statuses.id_reservation_status")
    )
    status = relationship("ReservationStatus", back_populates="reservations")
