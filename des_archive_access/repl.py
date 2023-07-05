import os
import click
from click_repl import repl
from prompt_toolkit.history import FileHistory

from des_archive_access.dbfiles import get_des_archive_access_db_conn


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        ctx.invoke(sqlrepl)


@cli.command()
def sqlrepl():
    prompt_kwargs = {
        'history': FileHistory(
            os.path.join(
                os.path.expanduser("~/.des_archive_access"),
                "history",
            )),
    }
    try:
        repl(click.get_current_context(), prompt_kwargs=prompt_kwargs)
    finally:
        conn = get_des_archive_access_db_conn()
        conn.close()


@cli.command()
@click.argument("query", nargs=-1, required=True)
def sql(query):
    conn = get_des_archive_access_db_conn()
    query = " ".join(query)
    for row in conn.execute(query):
        click.echo(row)
