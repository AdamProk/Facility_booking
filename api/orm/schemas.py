from pydantic import BaseModel, validator
from typing import List, Optional, ForwardRef
import datetime

from pydantic import Field


class UserRole(BaseModel):
    id_user_role: int
    name: str


class UserRoleCreate(BaseModel):
    name: str


class User(BaseModel):
    id_user: int
    email: str
    password: str
    name: str
    lastname: str
    phone_number: str

    user_role: UserRole


class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    lastname: str
    phone_number: str
    user_role_name: str


class ReservationStatus(BaseModel):
    id_reservation_status: int
    status: str


class ReservationStatusCreate(BaseModel):
    status: str


class FacilityType(BaseModel):
    id_facility_type: int
    name: str


class FacilityTypeCreate(BaseModel):
    name: str


class City(BaseModel):
    id_city: int
    name: str


class CityCreate(BaseModel):
    name: str


class State(BaseModel):
    id_state: int
    name: str


class StateCreate(BaseModel):
    name: str


class Address(BaseModel):
    id_address: int

    city: City

    state: State
    street_name: str
    building_number: int
    postal_code: str


class AddressCreate(BaseModel):
    city_name: str
    state_name: str
    street_name: str
    building_number: int
    postal_code: str


class Day(BaseModel):
    id_day: int
    day: str


class DayCreate(BaseModel):
    day: str


class OpenHour(BaseModel):
    id_open_hours: int

    day: Day

    start_hour: datetime.time
    end_hour: datetime.time


class OpenHourCreate(BaseModel):
    day_name: str

    start_hour: datetime.time
    end_hour: datetime.time


class Company(BaseModel):
    id_company: int
    address: Address
    name: str
    nip: str
    phone_number: str


class CompanyCreate(BaseModel):
    id_address: int
    name: str
    nip: str
    phone_number: str