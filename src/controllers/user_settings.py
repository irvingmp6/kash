class UserSettings:
    def __init__(self, args):
        self.args = args
        self.conn = args.sqlite_db
        self.new_transactions_csv_list = args.add_transactions
        self.update_financials = self.args.update_financials
        self.reconcile = self.args.reconcile
