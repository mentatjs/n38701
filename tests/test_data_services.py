import logging
import unittest

import sys

from services.data_services import DataServices

logger = logging.getLogger('tests')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('tests.log')
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '[%(asctime)s] [%(threadName)s] %(levelname)s [%(filename)s.%(funcName)s:%(lineno)d] %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S')
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)


class TestDataServices(unittest.TestCase):

    def test_load_data(self):
        data = DataServices()
        data.load_csvs(path='../data')

    def test_load_csv(self):
        data = DataServices()
        # data.load_csv(path='../data/Flt0595_20230521F.csv')
        data.load_csv(path='../data/Flt0552_20230418F.csv')


    def test_analyze_error(self):
        data = DataServices()
        data.analyze_error(database='../n38701.db')
        self.assertTrue(False)