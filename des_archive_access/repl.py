import os

import click
from click_repl import repl
from prompt_toolkit.history import FileHistory

from des_archive_access.dbfiles import get_des_archive_access_db_conn
from des_archive_access.sql import parse_and_execute_query

IN_REPL = False


class _Group(click.Group):
    def __init__(self, *args, **kwargs):
        self._default_cmd = kwargs.pop("default", None)
        super().__init__(*args, **kwargs)

    def invoke(self, ctx):
        if (
            IN_REPL
            and ctx.protected_args
            and (ctx.protected_args[0] not in ctx.command.list_commands(ctx))
        ):
            ctx.protected_args = [self._default_cmd] + ctx.protected_args
        return super().invoke(ctx)


@click.group(cls=_Group, invoke_without_command=True, default="sql")
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
    """DES archive access CLI

    Execute `des-archive-access` at the command line to run queries
    in an interactive SQL shell.

    Alternatively, use the options below to execute queries directly.
    """
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
    global IN_REPL

    prompt_kwargs = {
        "history": FileHistory(
            os.path.join(
                os.path.expanduser("~/.des_archive_access"),
                "history",
            ),
        ),
    }
    try:
        IN_REPL = True
        repl(click.get_current_context(), prompt_kwargs=prompt_kwargs)
    finally:
        IN_REPL = False
        get_des_archive_access_db_conn().close()


@cli.command()
@click.argument("query", nargs=-1, required=True)
def sql(query):
    """Execute a QUERY."""
    query = " ".join(query)
    parse_and_execute_query(query)
