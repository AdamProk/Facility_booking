from orm import crud, models, schemas
from sqlalchemy.exc import IntegrityError, NoResultFound


def check_availability(db, id_facility, date, start_hour, end_hour, **kwargs):
    facilities = crud.get_facilities(db, id_facility=id_facility)
    if len(facilities) < 1:
        raise NoResultFound("No facility with specified id in the database.")

    facility = facilities[0]

    day_of_week = date.strftime("%A")
    open_hours_on_that_day = list(
        filter(lambda x: x.day.day == day_of_week, facility.open_hours)
    )
    if not open_hours_on_that_day:
        raise NoResultFound(
            "No open hours specified for that facility on that day of the week."
        )
    open_hours_on_that_day = open_hours_on_that_day[0]

    # Check if requested reservation time before or after open hours
    if (
        start_hour < open_hours_on_that_day.start_hour
        or end_hour > open_hours_on_that_day.end_hour
    ):
        return False

    # Check if there isnt any reservation collision
    for reservation in facility.reservations:
        if (
            reservation.date == date and
            (start_hour >= reservation.start_hour and
            start_hour <= reservation.end_hour) or
            (end_hour >= reservation.start_hour and
            end_hour <= reservation.end_hour)
        ):
            return False

    return True
