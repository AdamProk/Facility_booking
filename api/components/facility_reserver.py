from orm import models, schemas, crud
from sqlalchemy.exc import IntegrityError, NoResultFound
import datetime


def reserve(db, id_facility, id_user, date, start_hour, end_hour, **kwargs):
    facilities = crud.get_facilities(db, id_facility=id_facility)
    if not facilities:
        raise NoResultFound("No facility with specified id in the database.")
    facility = facilities[0]

    users = crud.get_users(db, id_user=id_user)
    if not users:
        raise NoResultFound("No user with specified id in the database.")
    user = users[0]


    statuses = crud.get_reservation_statuses(db, status="Confirmed")
    if not statuses:
        raise NoResultFound("No status with name 'Confirmed' in the database.")
    status = statuses[0]

    t1 = datetime.datetime.combine(date, start_hour)
    t2 = datetime.datetime.combine(date, end_hour)
    price_final = int((t2 - t1).total_seconds() / 3600 * facility.price_hourly)

    crud.add_reservation(db, schemas.ReservationCreate(
        date=date,
        start_hour=start_hour,
        end_hour=end_hour,
        price_final=price_final,
        id_user=user.id_user,
        id_facility=facility.id_facility,
        id_status=status.id_reservation_status
    ))

    return True