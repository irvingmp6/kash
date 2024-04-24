import argparse
import textwrap

from _version import __version__

from src.controller import Controller
from src.interface_text import get_help_menu
from src.interface_funcs import db_connection
from src.interface_funcs import WrongFileExtension
from src.interface_funcs import ConfigSectionIncompleteError

def get_args():
    help_menu = get_help_menu()
    cli = argparse.ArgumentParser(
        prog='kash',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(help_menu['desc'])
    )
    subparsers = cli.add_subparsers(help=help_menu['subparsers'])

    # Import Subparser
    import_parser = subparsers.add_parser(
        'import',
        help=help_menu['import']['desc']
    )
    import_parser.add_argument(
        'sqlite_db',
        metavar='<SQLITE DB>',
        type=db_connection,
        help=textwrap.dedent(help_menu['import']['sqlite_db'])
    )
    import_parser.add_argument(
        'csv_file',
        metavar='<CSV FILE>',
        default=None,
        help=textwrap.dedent(help_menu['import']['csv_file'])
        )
    import_parser.add_argument(
        '--account-alias', '-a',
        type=str,
        default='',
        help=textwrap.dedent(help_menu['import']['account_alias'])
    )
    import_parser.add_argument(
        '--commit', '-c',
        action='store_true',
        default=False,
        help=textwrap.dedent(help_menu['import']['commit'])
    )

    # Import Raw Subparser
    import_raw_parser = subparsers.add_parser(
        'import-raw',
        help=help_menu['import']['desc']
    )
    import_raw_parser.add_argument(
        'sqlite_db',
        metavar='<SQLITE DB>',
        type=db_connection,
        help=textwrap.dedent(help_menu['import']['sqlite_db'])
    )
    import_raw_parser.add_argument(
        'config',
        metavar='<CONFIG>',
        help=textwrap.dedent(help_menu['import-raw']['config'])
    )
    import_raw_parser.add_argument(
        'csv_file',
        metavar='<CSV FILE>',
        default=None,
        help=textwrap.dedent(help_menu['import']['csv_file'])
        )
    import_raw_parser.add_argument(
        '--account-alias', '-a',
        type=str,
        default='',
        help=textwrap.dedent(help_menu['import']['account_alias'])
    )
    import_raw_parser.add_argument(
        '--commit', '-c',
        action='store_true',
        default=False,
        help=textwrap.dedent(help_menu['import']['commit'])
    )

    # SQL Subparser
    # sql_parser = subparsers.add_parser('sql')
    # sql_parser.add_argument(
    #     'config'
    #     metavar='<CONFIG>',
    #     type=pathlib_config_path,
    # )
    # sql_parser.add_argument(
    #     'key'
    #     metavar='<KEY>'
    # )
    # import pdb; pdb.set_trace()
    return cli.parse_args()


def main():
    args = None

    try:
        args = get_args()
        controller = Controller(args)
        controller.start_process()

    except (FileNotFoundError, ConfigSectionIncompleteError) as e:
        print(f"Error: {e}")

    finally:
        if args:
            args.sqlite_db.close()

if __name__ == "__main__":
    main()