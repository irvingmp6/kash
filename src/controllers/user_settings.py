import os
from configparser import ConfigParser


class UserSettings:
    def __init__(self, args):
        self.args = args
        self.conn = args.sqlite_db
        self.new_transactions_csv_list = args.import_csv
        self.commit = self.args.commit