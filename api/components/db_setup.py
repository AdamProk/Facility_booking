from orm import models, schemas, crud
from passlib.context import CryptContext
from components import credentials_manager as cm


class DBSetup:
    def __init__(self, db_session_creator):
        self._db_session_creator = db_session_creator
        self._db_session = None

    def _create_in_db(self, model, data):
        added_count = 0
        for row in data:
            search_query = row.copy()
            if search_query.get("password"):
                del search_query['password']
            item = self._db_session.query(model).filter_by(**search_query).first()
            if not item:
                item = model(**row)
                self._db_session.add(item)
                added_count += 1
        self._db_session.commit()
        if added_count > 0:
            print(
                "Added {} of {} objects.".format(added_count, model.__name__)
            )

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
                "user_role_id": crud.get_user_roles(self._db_session, name="User")[0].id_user_role,
                "email": "user@user.com",
                "password": cm.get_password_hash("user"),
                "name": "User_name",
                "lastname": "User_lastname",
                "phone_number": "123123123",
            },

            {
                "user_role_id": crud.get_user_roles(self._db_session, name="Admin")[0].id_user_role,
                "email": "admin@admin.com",
                "password": cm.get_password_hash("admin"),
                "name": "Admin_name",
                "lastname": "Admin_lastname",
                "phone_number": "123123123",
            },
        ]

        self._create_in_db(models.User, valid_users)

    def setup(self):
        self._db_session = self._db_session_creator()
        self._create_valid_days()
        self._create_valid_statuses()
        self._create_valid_user_roles()
        self._create_valid_test_users()
        self._db_session.close()
        print("Setup complete.")
