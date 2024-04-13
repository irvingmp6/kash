import os
from configparser import ConfigParser


class UserSettings:
    def __init__(self, args):
        self.args = args
        self.conn = args.sqlite_db if hasattr(self.args, 'sqlite_db') else None
        self.new_csv_files = self.args.new_csv_files
        self.account_alias = self.args.account_alias
        self.commit = self.args.commit
        self.config = self.get_config() if hasattr(self.args, 'config') else None
        
    def get_config(self):
        config_filepath = self.args.config
        if not os.path.isfile(config_filepath):
            raise FileNotFoundError(f"Could not locate config file:\n{config_filepath}")
        cp = ConfigParser()
        cp.read(config_filepath)
        return cp