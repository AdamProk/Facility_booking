from orm import models, schemas, crud
from sqlalchemy.exc import IntegrityError, NoResultFound
import logging
from passlib.context import CryptContext
from components import credentials_manager as cm

LOGGER = logging.getLogger(__name__)


class DBSetup:
    def __init__(self, db_session_creator):
        self._db_session_creator = db_session_creator
        self._db_session = None

    def _create_in_db(self, model, data):
        try:
            added_count = 0
            for row in data:
                search_query = row.copy()
                if search_query.get("password"):
                    del search_query["password"]
                item = (
                    self._db_session.query(model)
                    .filter_by(**search_query)
                    .first()
                )
                if not item:
                    item = model(**row)
                    try:
                        self._db_session.add(item)
                    except IntegrityError:
                        pass
                    added_count += 1
            self._db_session.commit()
            if added_count > 0:
                LOGGER.info(
                    "Added {} of {} objects.".format(
                        added_count, model.__name__
                    )
                )
        except Exception as e:
            LOGGER.error(str(e))

    def _create_valid_days(self):
        valid_day_names = [
            {"day": "Monday"},
            {"day": "Tuesday"},
            {"day": "Wednesday"},
            {"day": "Thursday"},
            {"day": "Friday"},
            {"day": "Saturday"},
            {"day": "Sunday"},
        ]

        self._create_in_db(models.Day, valid_day_names)

    def _create_valid_test_facility_types(self):
        valid_facility_types = [
            {"name": "Tennis court"},
            {"name": "Gym"},
        ]

        self._create_in_db(models.FacilityType, valid_facility_types)

    def _create_valid_statuses(self):
        valid_statuses = [
            {"status": "Finished"},
            {"status": "Pending"},
            {"status": "Confirmed"},
        ]

        self._create_in_db(models.ReservationStatus, valid_statuses)

    def _create_valid_user_roles(self):
        valid_user_roles = [
            {"name": "User"},
            {"name": "Admin"},
        ]

        self._create_in_db(models.UserRole, valid_user_roles)

    def _create_valid_test_users(self):
        valid_users = [
            {
                "user_role_id": crud.get_user_roles(
                    self._db_session, name="User"
                )[0].id_user_role,
                "email": "user@user.com",
                "password": cm.get_password_hash("user"),
                "name": "User_name",
                "lastname": "User_lastname",
                "phone_number": "123123123",
            },
            {
                "user_role_id": crud.get_user_roles(
                    self._db_session, name="Admin"
                )[0].id_user_role,
                "email": "admin@admin.com",
                "password": cm.get_password_hash("admin"),
                "name": "Admin_name",
                "lastname": "Admin_lastname",
                "phone_number": "123123123",
            },
        ]

        self._create_in_db(models.User, valid_users)

    def _create_valid_test_cities(self):
        valid = [
            {"name": "Kraków"},
        ]

        self._create_in_db(models.City, valid)

    def _create_valid_test_states(self):
        valid = [
            {"name": "Małopolska"},
        ]

        self._create_in_db(models.State, valid)

    def _create_valid_test_addresses(self):
        valid = [
            {
                "id_city": crud.get_cities(self._db_session, name="Kraków")[
                    0
                ].id_city,
                "id_state": crud.get_states(
                    self._db_session, name="Małopolska"
                )[0].id_state,
                "street_name": "Warszawska",
                "building_number": 0,
                "postal_code": "3212",
            }
        ]

        self._create_in_db(models.Address, valid)

    def _create_valid_test_open_hours(self):
        valid = [
            {
                "id_day": crud.get_days(self._db_session, day="Monday")[
                    0
                ].id_day,
                "start_hour": "10:00",
                "end_hour": "11:00",
            },
            {
                "id_day": crud.get_days(self._db_session, day="Tuesday")[
                    0
                ].id_day,
                "start_hour": "10:00",
                "end_hour": "11:00",
            },
            {
                "id_day": crud.get_days(self._db_session, day="Wednesday")[
                    0
                ].id_day,
                "start_hour": "10:00",
                "end_hour": "11:00",
            },
            {
                "id_day": crud.get_days(self._db_session, day="Thursday")[
                    0
                ].id_day,
                "start_hour": "10:00",
                "end_hour": "11:00",
            },
            {
                "id_day": crud.get_days(self._db_session, day="Friday")[
                    0
                ].id_day,
                "start_hour": "10:00",
                "end_hour": "11:00",
            },
            {
                "id_day": crud.get_days(self._db_session, day="Saturday")[
                    0
                ].id_day,
                "start_hour": "10:00",
                "end_hour": "11:00",
            },
            {
                "id_day": crud.get_days(self._db_session, day="Sunday")[
                    0
                ].id_day,
                "start_hour": "10:00",
                "end_hour": "11:00",
            },
        ]
        self._create_in_db(models.OpenHour, valid)

    def _create_valid_test_companies(self):
        valid = [
            {
                "id_address": crud.get_addresses(
                    self._db_session, street_name="Warszawska"
                )[0].id_address,
                "name": "TennisCompany",
                "nip": "123124124",
                "phone_number": "1412421",
            }
        ]
        self._create_in_db(models.Company, valid)

    def _create_valid_test_facilities(self):
        valid = [
            {
                "name": "Kort1",
                "description": "Description",
                "price_hourly": 20,
                "id_facility_type": crud.get_facility_types(
                    self._db_session, name="Tennis court"
                )[0].id_facility_type,
                "id_address": crud.get_addresses(
                    self._db_session, street_name="Warszawska"
                )[0].id_address,
                "id_company": crud.get_companies(
                    self._db_session, name="TennisCompany"
                )[0].id_company,
                "ids_open_hours": [1, 2, 3, 4, 5, 6, 7],
            }
        ]
        added_count = 0
        for row in valid:
            search_query = row.copy()
            del search_query["ids_open_hours"]
            item = (
                self._db_session.query(models.Facility)
                .filter_by(**search_query)
                .first()
            )
            if not item:
                item = models.Facility(**search_query)
                for open_hour_id in row["ids_open_hours"]:
                    item.open_hours.append(
                        crud.get_open_hours(
                            self._db_session, id_open_hours=open_hour_id
                        )[0]
                    )
                self._db_session.add(item)
                added_count += 1
        self._db_session.commit()
        if added_count > 0:
            LOGGER.info(
                "Added {} of {} objects.".format(
                    added_count, models.Facility.__name__
                )
            )

    def setup(self):
        self._db_session = self._db_session_creator()
        self._create_valid_days()
        self._create_valid_statuses()
        self._create_valid_user_roles()
        #self._create_valid_test_users()
        #self._create_valid_test_cities()
        #self._create_valid_test_states()
        #self._create_valid_test_open_hours()
        #self._create_valid_test_facility_types()
        #self._create_valid_test_addresses()
        #self._create_valid_test_companies()
        #self._create_valid_test_facilities()
        self._db_session.close()
        LOGGER.info("Setup complete.")
