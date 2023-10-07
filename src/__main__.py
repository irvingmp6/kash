import argparse
import textwrap

from _version import __version__

from src.controllers.controller import Controller
from src.interface.interface_text import get_help_menu
from src.interface.interface_funcs import db_connection
from src.interface.interface_funcs import pathlib_csv_path
from src.interface.interface_funcs import WrongFileExtension
from src.interface.interface_funcs import TransactionsTableDoesNotExist

def get_args():
    help_menu = get_help_menu()
    cli = argparse.ArgumentParser(
        prog='kash',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(help_menu['desc'])
    )
    cli.add_argument(
        'sqlite_db',
        metavar='<SQLITE DB>',
        type=db_connection,
        help=textwrap.dedent(help_menu['sqlite_db'])
    )
    cli.add_argument(
        '--add-transactions', '-a',
        nargs='+',
        default=None,
        type=pathlib_csv_path,
        help=textwrap.dedent(help_menu['add_transactions'])
        )
    cli.add_argument(
        '--commit', '-c',
        action='store_true',
        default=False,
        help=textwrap.dedent(help_menu['commit'])
    )
    cli.add_argument(
        '--reconcile', '-r',
        action='store_true',
        help=textwrap.dedent(help_menu['reconcile'])
    )
    cli.add_argument(
        '--update-financials', '-u',
        action='store_true',
        help=textwrap.dedent(help_menu['add_transactions'])

    )
    cli.add_argument(
        '--forecast', '-f',
        action='store_true'
    )
    return cli.parse_args()

def main():
    args = None

    try:
        args = get_args()
        controller = Controller(args)
        controller.start_process()

    except (WrongFileExtension, FileNotFoundError) as e:
        print(f"Error: {e}")

    finally:
        if args:
            args.sqlite_db.close()



if __name__ == "__main__":
    main()