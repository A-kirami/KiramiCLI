from pathlib import Path
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
    create_adapter,
    format_package_results,
    list_adapters,
)


@click.group(
    cls=ClickAliasedGroup, invoke_without_command=True, help=_("Manage bot adapters.")
)
@click.pass_context
@run_async
async def adapter(ctx: click.Context):
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


@adapter.command(
    name="list", help=_("List kiramibot adapters published on kiramibot homepage.")
)
@run_async
async def get_list():
    adapters = await list_adapters()
    click.echo(format_package_results(adapters))


@adapter.command(
    help=_("Search for kiramibot adapters published on kiramibot homepage.")
)
@click.argument("name", nargs=1, default=None)
@run_async
async def search(name: str | None):
    if name is None:
        name = await InputPrompt(_("Adapter name to search:")).prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    adapters = await list_adapters(name)
    click.echo(format_package_results(adapters))


@adapter.command(
    aliases=["add"],
    context_settings={"ignore_unknown_options": True},
    help=_("Install kiramibot adapter to current project."),
)
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def install(ctx: click.Context, name: str | None, pip_args: list[str] | None):
    try:
        adapter = await find_exact_package(
            _("Adapter name to install:"), name, await list_adapters()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    try:
        GLOBAL_CONFIG.add_adapter(adapter.module_name)
    except RuntimeError as e:
        click.echo(
            _("Failed to add adapter {adapter.name} to config: {e}").format(
                adapter=adapter, e=e
            )
        )

    proc = await call_pip_install(adapter.project_link, pip_args)
    await proc.wait()


@adapter.command(
    context_settings={"ignore_unknown_options": True},
    help=_("Update kiramibot adapter."),
)
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def update(ctx: click.Context, name: str | None, pip_args: list[str] | None):
    try:
        adapter = await find_exact_package(
            _("Adapter name to update:"), name, await list_adapters()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    proc = await call_pip_update(adapter.project_link, pip_args)
    await proc.wait()


@adapter.command(
    aliases=["remove"],
    context_settings={"ignore_unknown_options": True},
    help=_("Uninstall kiramibot adapter from current project."),
)
@click.argument("name", nargs=1, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def uninstall(ctx: click.Context, name: str | None, pip_args: list[str] | None):
    try:
        adapter = await find_exact_package(
            _("Adapter name to uninstall:"), name, await list_adapters()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    try:
        GLOBAL_CONFIG.remove_adapter(adapter.module_name)
    except RuntimeError as e:
        click.echo(
            _("Failed to remove adapter {adapter.name} from config: {e}").format(
                adapter=adapter, e=e
            )
        )

    proc = await call_pip_uninstall(adapter.project_link, pip_args)
    await proc.wait()


@adapter.command(aliases=["new"], help=_("Create a new kiramibot adapter."))
@click.argument("name", default=None)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option("-t", "--template", default=None, help=_("The adapter template to use."))
@click.pass_context
@run_async
async def create(
    ctx: click.Context,
    name: str | None,
    output_dir: str | None,
    template: str | None,
):
    if name is None:
        try:
            name = await InputPrompt(_("Adapter name:")).prompt_async(
                style=CLI_DEFAULT_STYLE
            )
        except CancelledError:
            ctx.exit()
    if output_dir is None:
        detected: list[Choice[None]] = [
            Choice(str(x))
            for x in Path(".").glob("**/adapters/")
            if x.is_dir()
            and not any(
                p.name.startswith(".") or p.name.startswith("_") for p in x.parents
            )
        ] or [
            Choice(f"{x}/adapters/")
            for x in Path(".").glob("*/")
            if x.is_dir() and not x.name.startswith(".") and not x.name.startswith("_")
        ]
        try:
            output_dir = (
                await ListPrompt(
                    _("Where to store the adapter?"), detected + [Choice(_("Other"))]
                ).prompt_async(style=CLI_DEFAULT_STYLE)
            ).name
            if output_dir == _("Other"):
                output_dir = await InputPrompt(
                    _("Output Dir:"),
                    validator=lambda x: len(x) > 0,
                ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit()

    if not Path(output_dir).is_dir():
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    create_adapter(name, output_dir, template=template)
