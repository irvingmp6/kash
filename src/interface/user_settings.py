class UserSettings:
    def __init__(self, args):
        self.args = args
        self.conn = args.sqlite_db
        self.new_transactions_csv = args.add_transactions
