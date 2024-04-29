def get_help_menu() -> dict:
    menu = {
        'desc': """A command-line tool that opens a local db connection and imports or fetches bank activity.""",
        'subparsers': """""",
        'import': {
            'desc': """Subcommand that works directly with a local database""",
            'sqlite_db': """Path to new or existing sqlite db""",
            'csv_file': """Imports new records from csv file(s)""",
            'account_alias': """The alias given to the set of transactions during import""",
            'commit': """Commits changes to database based on analysis""",
        },
        'import-raw': {
            'import_config': """Config file containing mapping definitions"""
        },
    }

    return menu
