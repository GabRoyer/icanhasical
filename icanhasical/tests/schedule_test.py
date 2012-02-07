import os
import unittest
from datetime import date

# Add project root to the PYTHONPATH
import sys
sys.path.append("..")

from model.schedule import Schedule

class ScheduleTestCase(unittest.TestCase):
    '''Class that contains test case for the schedule class'''

    def test_save_and_load(self):
        '''Test the persistance of the schedule settings'''
        initial_schedule = Schedule()
        initial_schedule.first_day = date(2012, 1, 12)
        initial_schedule.last_day = date(2012, 12, 21) # End of the world
        initial_schedule.save()

        loaded_schedule = Schedule.load()
        self.assertEqual(loaded_schedule.first_day, initial_schedule.first_day)
        self.assertEqual(loaded_schedule.last_day, initial_schedule.last_day)
