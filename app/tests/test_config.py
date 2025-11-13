import unittest
from app.modules import config


class Testfile():
    config_file = "none"

    def __init__(self, file_name):
        self.config_file = file_name


class ConfigTests(unittest.TestCase):

    def test_instance(self):
        self.assertIsInstance(config.Config(Testfile("app/tests/config_a.json")), config.Config)

    def test_section_nodefault(self):
        with self.assertRaises(ValueError) as error:
            config.Config(Testfile("app/tests/config_b.json"))
        self.assertEqual(str(error.exception), "Missing section 'defaults' in app/tests/config_b.json")

    def test_certfile_not_existing(self):
        with self.assertRaises(ValueError) as error:
            config.Config(Testfile("app/tests/config_c.json"))
        self.assertTrue(str(error.exception).endswith("invalid does not exist"))
