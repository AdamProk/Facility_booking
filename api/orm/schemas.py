from pydantic import BaseModel
from typing import List, Optional, ForwardRef



class UserRole(BaseModel):
    id_user_role: int
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

