import os
import unittest

# Add project root to the PYTHONPATH
import sys
sys.path.append("..")

from model.course import CourseLoader

class CourseLoaderTestCase(unittest.TestCase):
    '''Class that contains test cases for the CourseLoader'''
    def setUp(self):
        self.loader = CourseLoader()

    def test_basic_course(self):
        '''Basic test case with one course'''
        results = self.loader.load(("mth1101", "THEORY", 1))
        self.assertEqual(len(results), 1)
        
        mth1101 = results[0]
        self.assertEqual(mth1101.sigil, "MTH1101")
        self.assertEqual(mth1101.title, "Calcul I")
        self.assertEqual(mth1101.credits, 2.0)
        self.assertEqual(mth1101.weekly_theory, 2.0)
        self.assertEqual(mth1101.type, "Cours")
        self.assertEqual(mth1101.group, 1)

    def test_multiple_courses(self):
        '''Test for multiples classes'''
        results = self.loader.load(("mth1101", "THEORY", 1),
                                   ("mth1101", "LAB", 1),
                                   ("mth1102", "THEORY", 2))
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0].sigil, "MTH1101")
        self.assertEqual(results[0].title, "Calcul I")
        self.assertEqual(results[0].type, "Cours")
        self.assertEqual(results[0].group, 1)

        self.assertEqual(results[1].sigil, "MTH1101")
        self.assertEqual(results[1].title, "Calcul I")
        self.assertEqual(results[1].type, "Travaux pratiques")
        self.assertEqual(results[1].group, 1)

        self.assertEqual(results[2].sigil, "MTH1102")
        self.assertEqual(results[2].title, "Calcul II")
        self.assertEqual(results[2].type, "Cours")
        self.assertEqual(results[2].group, 2)

    def test_cache_clearing(self):
        '''Tests that the clean_cache method effectively cleans the cache'''
        self.loader.load(("mth1101", "THEORY", 1),
                         ("mth1101", "THEORY", 1),
                         ("mth1101", "LAB", 1),
                         ("mth1102", "THEORY", 2),
                         ("inf1010", "LAB", 1),
                         ("inf1010", "THEORY", 1),
                         ("INF2010", "THEORY", 1))
        
        self.loader.clear_cache()
        cache_files = os.listdir(self.loader.CACHE_DIRECTORY)
        self.assertEqual(len(cache_files), 0)

    def test_no_course(self):
        '''Tests the behavior of the course loader when attempting to call the
        load method without any argument
        '''
        result = self.loader.load()
        self.assertListEqual(result, [])

    def tearDown(self):
        self.loader.clear_cache()