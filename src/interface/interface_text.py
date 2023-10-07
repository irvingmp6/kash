def get_help_menu() -> dict:
    menu = {}
    menu['add_transactions'] = """Imports new records from csv file(s)"""
    menu['commit'] = """Commits changes to database based on analysis"""
    menu['desc'] = """A command-line tool that forecasts financial climate based on bank transactions."""
    menu['sqlite_db'] = """Path to new or existing sqlite db"""
    menu['update_financials'] = """Automatically ingests src/config/reconcileable.csv and updates reconcileable table"""
    menu['reconcile'] = """Looks up transactions releated to each row in reconcilables.csv"""
    return menu
