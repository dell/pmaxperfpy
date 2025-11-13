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

    # value = True means required, False is for optional
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

    #
    # Constructor
    def __init__(self, args):
        ''' constructor '''
        self.cfg = {}
        self.config_file = Config.CONFIG_FILE
        if args.config_file:
            self.config_file = args.config_file
        self.update_config_from_file()
        self.check_required_sections_and_keys()
        self.check_and_set_unisphere_defaults()
        self.check_certificates_exist()

    #
    # update_config_from_file
    def update_config_from_file(self):
        ''' read configfile and update config '''
        if not os.path.isfile(self.config_file):
            return
        logging.info("Loading config file %s", self.config_file)
        try:
            with open(self.config_file, 'r', encoding="UTF-8") as f_handle:
                self.cfg = json.load(f_handle)
        except (OSError, IOError) as err:
            raise ValueError(f'Uable to open {self.config_file}: {err.strerror}') from err
        except json.decoder.JSONDecodeError as err:
            raise ValueError(f'Error parsing {self.config_file}: {err}') from err

    #
    # check_required_sections_and_keys
    def check_required_sections_and_keys(self):
        ''' verify all rquired sections and keys exist '''

        # required sections
        for key in Config.SECTION_KEYS:
            if key not in self.cfg:
                raise ValueError(f"Missing section '{key}' in {self.config_file}")

        # required keys
        for key, required_value in Config.DEFAULTS_KEYS.items():
            if key not in self.cfg["defaults"] and required_value:
                raise ValueError(f"Missing key '{key}' in section 'defaults' in {self.config_file}")

    #
    # check_and_set_unisphere_defaults
    def check_and_set_unisphere_defaults(self):
        ''' fill unisphere sections with defaults and check for required keys '''

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

    #
    # check_certificates_exist
    def check_certificates_exist(self):
        ''' if certificates are given check the files exist '''
        for key in ["keyfile", "certfile"]:
            if key in self.cfg["defaults"] and self.cfg["defaults"][key]:
                fname = os.path.join(os.path.dirname(__file__), "..", self.cfg["defaults"][key])
                if not os.path.exists(fname) or not os.path.isfile(fname):
                    raise ValueError(f'File {fname} does not exist')
