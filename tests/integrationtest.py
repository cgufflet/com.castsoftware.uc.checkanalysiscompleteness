#import cast_upgrade_1_6_5 # @UnusedImport
import unittest
from cast.application.test import run
import logging
from cast.application import create_engine

logging.root.setLevel(logging.DEBUG)


class TestIntegration(unittest.TestCase):

    """
    def test_Imaging(self):
        engine = create_engine("postgresql+pg8000://operator:CastAIP@localhost:2282/postgres")

        run(kb_name='imaging_local', application_name='Imaging', engine=engine)

    def test_eCommerce(self):
        engine = create_engine("postgresql+pg8000://operator:CastAIP@localhost:2282/postgres")

        run(kb_name='ecommerce_local', application_name='eCommerce', engine=engine)

    def test_hr_mgt(self):
        engine = create_engine("postgresql+pg8000://operator:CastAIP@localhost:2282/postgres")

        run(kb_name='hr_mgt_local', application_name='HR_MGT', engine=engine)

    """
    def test_etraq(self):
        engine = create_engine("postgresql+pg8000://operator:CastAIP@localhost:2282/postgres")
        run(kb_name='etraq_01_local', application_name='eTraq', engine=engine)


if __name__ == "__main__":
    unittest.main()