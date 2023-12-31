from orm import models, schemas


class DBSetup:
    def __init__(self, db_session_creator):
        self._db_session_creator = db_session_creator
        self._db_session = None

    def _create_in_db(self, model, data):
        added_count = 0
        for row in data:
            item = self._db_session.query(model).filter_by(**row).first()
            if not item:
                item = model(**row)
                self._db_session.add(item)
                added_count += 1
        self._db_session.commit()
        if added_count > 0:
            print("Added {} of {} objects.".format(added_count, model.__name__))

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

    def setup(self):
        self._db_session = self._db_session_creator()
        self._create_valid_days()
        self._create_valid_statuses()
        self._db_session.close()
        print("Setup complete.")
