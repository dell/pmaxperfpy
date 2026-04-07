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

    def test_alerts_config_valid(self):
        cfg = config.Config(Testfile("app/tests/config_a.json"))
        self.assertIn('alerts', cfg.cfg['unispheres'][0])
        self.assertEqual(cfg.cfg['unispheres'][0]['alerts']['severity'], 'WARNING')

    def test_alerts_config_missing_is_ok(self):
        cfg = config.Config(Testfile("app/tests/config_alert_missing.json"))
        self.assertNotIn('alerts', cfg.cfg['unispheres'][0])

    def test_alerts_bad_severity_rejected(self):
        with self.assertRaises(ValueError) as error:
            config.Config(Testfile("app/tests/config_alert_bad_severity.json"))
        self.assertIn("Invalid alerts severity", str(error.exception))

    def test_alerts_bad_type_rejected(self):
        with self.assertRaises(ValueError) as error:
            config.Config(Testfile("app/tests/config_alert_bad_type.json"))
        self.assertIn("Invalid alerts type", str(error.exception))

    def test_alerts_inherited_from_defaults(self):
        cfg = config.Config(Testfile("app/tests/config_a.json"))
        self.assertEqual(cfg.cfg['unispheres'][0]['alerts']['interval'], 900)
