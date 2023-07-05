import os

import click
from click_repl import repl
from prompt_toolkit.history import FileHistory

from des_archive_access.dbfiles import get_des_archive_access_db_conn
from des_archive_access.sql import parse_and_execute_query


@click.group(invoke_without_command=True)
@click.option(
    "-l",
    "--loadsql",
    default=None,
    type=str,
    help="Load a SQL command from a file and execute it.",
)
@click.option(
    "-c",
    "--command",
    default=None,
    type=str,
    help="Load a SQL command from the command line and execute it.",
)
@click.pass_context
def cli(ctx, command, loadsql):
    """DES archive access CLI. Execute the CLI to start the SQL shell."""
    query = None

    if command is not None:
        query = command

    if loadsql is not None:
        with open(loadsql) as fp:
            query = fp.read()

    if query is not None:
        try:
            parse_and_execute_query(query)
        finally:
            get_des_archive_access_db_conn().close()
    else:
        if ctx.invoked_subcommand is None:
            ctx.invoke(sqlrepl)


@cli.command()
def sqlrepl():
    """Alternative way of staring the SQL shell."""
    prompt_kwargs = {
        "history": FileHistory(
            os.path.join(
                os.path.expanduser("~/.des_archive_access"),
                "history",
            ),
        ),
    }
    try:
        repl(click.get_current_context(), prompt_kwargs=prompt_kwargs)
    finally:
        get_des_archive_access_db_conn().close()


@cli.command()
@click.argument("query", nargs=-1, required=True)
def sql(query):
    """Alternative way of loading a sql command from the
    QUERY arguemnt and executing it."""
    query = " ".join(query)
    parse_and_execute_query(query)
