''' config module '''
import logging
import json
import os


class Config():
    ''' config class to hold program global config '''

    CONFIG_FILE = 'pmax_config.json'
    RECONNECT_INTERVAL = 300  # 5m interval to retry connections
    RECONNECT_RETRY = 30  # retries for reconnect
    SLEEP = 5  # internal sleep interval (for faster thread stopping)

    SECTION_KEYS = ["defaults", "unispheres"]
    DEFAULTS_KEYS = {
        "username": False,
        "password": False,
        "unisphere_port": True,
        "verify": True,
        "interval": True,
        "exposed_port": True,
        "categories": True,
        "disabled_categories": False
    }
    UNISPHERE_KEYS = ["username", "password", "unisphere_port", "verify", "interval", "categories"]

    def update_config_from_file(self):
        ''' read configfile and update config '''
        if not os.path.isfile(self.config_file):
            return
        logging.info("Loading config file %s", self.config_file)
        try:
            with open(self.config_file, 'r', encoding="UTF-8") as f_handle:
                self.cfg = json.load(f_handle)
        except (OSError, IOError) as err:
            raise ValueError(f'Uable to open {self.config_file}: {err.strerror}')
        except json.decoder.JSONDecodeError as err:
            raise ValueError(f'Error parsing {self.config_file}: {err}')

        # required sections
        for key in Config.SECTION_KEYS:
            if key not in self.cfg:
                raise ValueError(f"Missing section '{key}' in {self.config_file}")

        # required keys
        for key in Config.DEFAULTS_KEYS:
            if key not in self.cfg["defaults"] and Config.DEFAULTS_KEYS[key]:
                raise ValueError(f"Missing key '{key}' in section 'defaults' in {self.config_file}")

        # fill in defaults for each unisphere
        for unisphere in self.cfg["unispheres"]:
            for key in Config.UNISPHERE_KEYS:
                if key not in unisphere:
                    if key not in self.cfg["defaults"]:
                        raise ValueError(f"Key '{key}' missing in both unisphere and defaults section in {self.config_file}")
                    unisphere[key] = self.cfg["defaults"][key]
                if not unisphere[key] and key != "verify":  # verify is allowed to be false
                    raise ValueError(f"Empty value for {key} in unisphere section in {self.config_file}")

            # hostname is the only required field
            if "hostname" not in unisphere:
                raise ValueError(f"Missing key 'hostname' in unisphere section in {self.config_file}")
            if not unisphere["hostname"]:
                raise ValueError(f"Empty value for hostname in unisphere section in {self.config_file}")

            # resolve secrets
            for key in ["username", "password"]:
                if isinstance(unisphere[key], dict) and "fromEnvironment" in unisphere[key]:
                    logging.debug("Checking for environment variable %s", unisphere[key]["fromEnvironment"])
                    if unisphere[key]["fromEnvironment"] not in os.environ:
                        raise ValueError(f'environment variable {unisphere[key]["fromEnvironment"]} not found')
                    logging.debug("Env variable content: %s", os.environ.get(unisphere[key]["fromEnvironment"]))
                    if not os.environ.get(unisphere[key]["fromEnvironment"]):
                        raise ValueError(f'Empty value for {key}. Environment variable {unisphere[key]["fromEnvironment"]} empty')
                    unisphere[key] = os.environ.get(unisphere[key]["fromEnvironment"])
                if not unisphere[key]:
                    raise ValueError(f'Empty value for {unisphere["hostname"]} {key}.')

    def __init__(self, args):
        ''' constructor '''
        self.cfg = {}
        self.config_file = Config.CONFIG_FILE
        if args.config_file:
            self.config_file = args.config_file
        self.update_config_from_file()
