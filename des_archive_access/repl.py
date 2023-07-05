import os

import click
from click_repl import repl
from prompt_toolkit.history import FileHistory

from des_archive_access.dbfiles import get_des_archive_access_db_conn
from des_archive_access.sql import parse_and_execute_query


@click.group(invoke_without_command=True)
@click.option("-l", "--loadsql", default=None, type=str)
@click.option("-c", "--command", default=None, type=str)
@click.pass_context
def cli(ctx, command, loadsql):
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
    query = " ".join(query)
    parse_and_execute_query(query)
