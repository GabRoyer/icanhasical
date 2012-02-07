import os
import pickle

class Schedule:
    '''Class that represents the semester's schedule'''
    @classmethod
    def load(cls):
        '''Load the schedule as it was las saved'''
        if os.path.exists(cls._FILE_PATH):
            with open(cls._FILE_PATH, 'r+b') as f:
                return pickle.load(f)
        else:
            return Schedule()

    def save(self):
        '''Ensure the persistance of the schedule'''
        directory = os.path.dirname(self._FILE_PATH)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(self._FILE_PATH, 'w+b') as f:
            pickle.dump(self, f)

    _FILE_PATH = "settings/schedule"

    # Both are list of date objects for the first b1 or b2 days of the semester
    b1_first_days = []
    b2_first_days = []

    # Represent the first day of the "study_week"
    study_week_start = None

    # Date objects representing the first and last days of the semester
    first_day = None
    last_day = None

    # List of date objects representing days off
    days_off = []