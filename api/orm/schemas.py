from pydantic import BaseModel, validator
from typing import List, Optional, ForwardRef

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
