from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


from .database import Base, engine


class UserRole(Base):
    __tablename__ = "user_roles"

    id_user_role = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    users = relationship('User', back_populates='user_role')



class User(Base):
    __tablename__ = "users"

    id_user = Column(Integer, primary_key=True, index=True)
    user_role_id = Column(Integer, ForeignKey("user_roles.id_user_role"), default=1)

    email = Column(String, unique=True)
    password = Column(String)
    name = Column(String)
    lastname = Column(String)
    phone_number = Column(String)

    user_role = relationship("UserRole", back_populates="users")



class ReservationStatus(Base):
    __tablename__ = "reservation_statuses"

    id_reservation_status = Column(Integer, primary_key=True)
    status = Column(String, nullable=False)

    # users = relationship('User', back_populates='user_role')



class FacilityType(Base):
    __tablename__ = "facility_types"

    id_facility_type = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    # users = relationship('User', back_populates='user_role')