import os
from configparser import ConfigParser


class UserSettings:
    def __init__(self, args):
        self.args = args
        self.conn = self.args.sqlite_db if hasattr(self.args, 'sqlite_db') else None
        self.csv_file = self.args.csv_file
        self.account_alias = self.args.account_alias
        self.commit = self.args.commit
        self.import_config = self.get_import_config() if hasattr(self.args, 'import_config') else None

    def get_import_config(self):
        import_config_filepath = self.args.import_config
        if not os.path.isfile(import_config_filepath):
            raise FileNotFoundError(f"Could not locate config file:\n{import_config_filepath}")
        cp = ConfigParser()
        cp.read(import_config_filepath)
        return cp
