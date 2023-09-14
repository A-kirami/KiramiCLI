import re
from typing import cast

import click
from noneprompt import CancelledError, Choice, InputPrompt, ListPrompt

from kirami_cli import _
from kirami_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedGroup, run_async, run_sync
from kirami_cli.cli.utils import find_exact_package
from kirami_cli.config import GLOBAL_CONFIG
from kirami_cli.handlers import (
    call_pip_install,
    call_pip_uninstall,
    call_pip_update,
    format_package_results,
    list_drivers,
)


@click.group(
    cls=ClickAliasedGroup, invoke_without_command=True, help=_("Manage bot driver.")
)
@click.pass_context
@run_async
async def driver(ctx: click.Context):
    if ctx.invoked_subcommand is not None:
        return

    command = cast(ClickAliasedGroup, ctx.command)

    choices: list[Choice[click.Command]] = []
    for sub_cmd_name in await run_sync(command.list_commands)(ctx):
        if sub_cmd := await run_sync(command.get_command)(ctx, sub_cmd_name):
            choices.append(
                Choice(
                    sub_cmd.help
                    or _("Run subcommand {sub_cmd.name!r}").format(sub_cmd=sub_cmd),
                    sub_cmd,
                )
            )

    try:
        result = await ListPrompt(
            _("What do you want to do?"), choices=choices
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    except CancelledError:
        ctx.exit()

    sub_cmd = result.data
    await run_sync(ctx.invoke)(sub_cmd)


@driver.command(
    name="list", help=_("List kiramibot drivers published on kiramibot homepage.")
)
@run_async
async def get_list():
    drivers = await list_drivers()
    click.echo(format_package_results(drivers))


@driver.command(help=_("Search for kiramibot drivers published on kiramibot homepage."))
@click.argument("name", nargs=1, default=None)
@run_async
async def search(name: str | None):
    if name is None:
        name = await InputPrompt(_("Driver name to search:")).prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    drivers = await list_drivers(name)
    click.echo(format_package_results(drivers))


@driver.command(
    aliases=["add"],
    context_settings={"ignore_unknown_options": True},
    help=_("Install kiramibot driver to current project."),
)
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def install(ctx: click.Context, name: str | None, pip_args: list[str] | None):
    try:
        driver = await find_exact_package(
            _("Driver name to install:"), name, await list_drivers()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    try:
        GLOBAL_CONFIG.add_driver(driver.module_name)
    except RuntimeError as e:
        click.echo(
            _("Failed to add driver {driver.name} to config: {e}").format(
                driver=driver, e=e
            )
        )

    proc = await call_pip_install(driver.project_link, pip_args)
    await proc.wait()


@driver.command(
    context_settings={"ignore_unknown_options": True},
    help=_("Update kiramibot driver."),
)
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def update(ctx: click.Context, name: str | None, pip_args: list[str] | None):
    try:
        driver = await find_exact_package(
            _("Driver name to update:"), name, await list_drivers()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    proc = await call_pip_update(driver.project_link, pip_args)
    await proc.wait()


@driver.command(
    aliases=["remove"],
    context_settings={"ignore_unknown_options": True},
    help=_("Uninstall kiramibot driver from current project."),
)
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def uninstall(ctx: click.Context, name: str | None, pip_args: list[str] | None):
    try:
        driver = await find_exact_package(
            _("Driver name to uninstall:"), name, await list_drivers()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    try:
        GLOBAL_CONFIG.remove_driver(driver.module_name)
    except RuntimeError as e:
        click.echo(
            _("Failed to remove driver {driver.name} from config: {e}").format(
                driver=driver, e=e
            )
        )

    if match := re.match(r"^nonebot2\[(.*?)\]$", package := driver.project_link):
        package = match[1]

    proc = await call_pip_uninstall(package, pip_args)
    await proc.wait()
