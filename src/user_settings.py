import os
from configparser import ConfigParser


class UserSettings:
    def __init__(self, cli_args):
        self.cli_args = cli_args
        self.conn = self.cli_args.sqlite_db if hasattr(self.cli_args, 'sqlite_db') else None
        self.commit = self.cli_args.commit if hasattr(self.cli_args, 'commit') else None

    def get_config_object(self, config_file):
        if not os.path.isfile(config_file):
            raise FileNotFoundError(f"Could not locate config file:\n{config_file}")
        cp = ConfigParser()
        cp.read(config_file)
        return cp

class ImportParserUserSettings(UserSettings):
    def __init__(self, cli_args):
        super(ImportParserUserSettings, self).__init__(cli_args)
        self.csv_file = self.cli_args.csv_file
        self.account_alias = self.cli_args.account_alias
        self.import_config = self.get_config_object(self.cli_args.import_config) \
            if hasattr(self.cli_args, 'import_config') else None

class GetQueryUserSettings(UserSettings):
    def __init__(self, cli_args):
        super(GetQueryUserSettings, self).__init__(cli_args)
        self.queries_config_path = self.cli_args.queries_config
        self.queries_config = self.get_config_object(self.queries_config_path)
        self.query_calls = self.cli_args.query_calls

