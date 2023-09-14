from pathlib import Path
from typing import cast

import click
from noneprompt import CancelledError, Choice, ConfirmPrompt, InputPrompt, ListPrompt

from kirami_cli import _
from kirami_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedGroup, run_async, run_sync
from kirami_cli.cli.utils import find_exact_package
from kirami_cli.config import GLOBAL_CONFIG
from kirami_cli.handlers import (
    call_pip_install,
    call_pip_uninstall,
    call_pip_update,
    create_plugin,
    format_package_results,
    list_plugins,
)


@click.group(
    cls=ClickAliasedGroup, invoke_without_command=True, help=_("Manage bot plugins.")
)
@click.pass_context
@run_async
async def plugin(ctx: click.Context):
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


@plugin.command(
    name="list", help=_("List kiramibot plugins published on kiramibot homepage.")
)
@run_async
async def get_list():
    plugins = await list_plugins()
    click.echo(format_package_results(plugins))


@plugin.command(help=_("Search for kiramibot plugins published on kiramibot homepage."))
@click.argument("name", nargs=1, required=False, default=None)
@run_async
async def search(name: str | None):
    if name is None:
        name = await InputPrompt(_("Plugin name to search:")).prompt_async(
            style=CLI_DEFAULT_STYLE
        )
    plugins = await list_plugins(name)
    click.echo(format_package_results(plugins))


@plugin.command(
    aliases=["add"],
    context_settings={"ignore_unknown_options": True},
    help=_("Install kiramibot plugin to current project."),
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def install(ctx: click.Context, name: str | None, pip_args: list[str] | None):
    try:
        plugin = await find_exact_package(
            _("Plugin name to install:"), name, await list_plugins()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    try:
        GLOBAL_CONFIG.add_plugin(plugin.module_name)
    except RuntimeError as e:
        click.echo(
            _("Failed to add plugin {plugin.name} to config: {e}").format(
                plugin=plugin, e=e
            )
        )

    proc = await call_pip_install(plugin.project_link, pip_args)
    await proc.wait()


@plugin.command(
    context_settings={"ignore_unknown_options": True},
    help=_("Update kiramibot plugin."),
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def update(ctx: click.Context, name: str | None, pip_args: list[str] | None):
    try:
        plugin = await find_exact_package(
            _("Plugin name to update:"), name, await list_plugins()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    proc = await call_pip_update(plugin.project_link, pip_args)
    await proc.wait()


@plugin.command(
    aliases=["remove"],
    context_settings={"ignore_unknown_options": True},
    help=_("Uninstall kiramibot plugin from current project."),
)
@click.argument("name", nargs=1, required=False, default=None)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def uninstall(ctx: click.Context, name: str | None, pip_args: list[str] | None):
    try:
        plugin = await find_exact_package(
            _("Plugin name to uninstall:"), name, await list_plugins()
        )
    except CancelledError:
        ctx.exit()
    except Exception:
        ctx.exit(1)

    try:
        GLOBAL_CONFIG.remove_plugin(plugin.module_name)
    except RuntimeError as e:
        click.echo(
            _("Failed to remove plugin {plugin.name} from config: {e}").format(
                plugin=plugin, e=e
            )
        )

    proc = await call_pip_uninstall(plugin.project_link, pip_args)
    await proc.wait()


@plugin.command(aliases=["new"], help=_("Create a new kiramibot plugin."))
@click.argument("name", nargs=1, required=False, default=None)
@click.option("-s", "--sub-plugin", is_flag=True, default=None)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option("-t", "--template", default=None, help=_("The plugin template to use."))
@click.pass_context
@run_async
async def create(
    ctx: click.Context,
    name: str | None,
    sub_plugin: bool | None,
    output_dir: str | None,
    template: str | None,
):
    if name is None:
        try:
            name = await InputPrompt(_("Plugin name:")).prompt_async(
                style=CLI_DEFAULT_STYLE
            )
        except CancelledError:
            ctx.exit()
    if sub_plugin is None:
        try:
            sub_plugin = await ConfirmPrompt(
                _("Use nested plugin?"), default_choice=False
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit()

    if output_dir is None:
        config = GLOBAL_CONFIG.get_kiramibot_config()
        detected: list[Choice[None]] = [
            Choice(str(d)) for d in config.plugin_dirs if Path(d).is_dir()
        ]
        try:
            output_dir = (
                await ListPrompt(
                    _("Where to store the plugin?"), detected + [Choice(_("Other"))]
                ).prompt_async(style=CLI_DEFAULT_STYLE)
            ).name
            if output_dir == _("Other"):
                output_dir = await InputPrompt(
                    _("Output Dir:"),
                    validator=lambda x: len(x) > 0,
                    error_message=_("Invalid output dir!"),
                ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit()

    if not Path(output_dir).is_dir():
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        GLOBAL_CONFIG.add_plugin_dir(output_dir)

    create_plugin(name, output_dir, sub_plugin=sub_plugin, template=template)
