import json
import re
import sys
from dataclasses import dataclass, field
from functools import partial
from logging import Logger
from pathlib import Path
from typing import Any

import click
from noneprompt import (
    CancelledError,
    CheckboxPrompt,
    Choice,
    ConfirmPrompt,
    InputPrompt,
)

from kirami_cli import _
from kirami_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedCommand, run_async
from kirami_cli.config import ConfigManager
from kirami_cli.consts import DEFAULT_ADAPTER, DEFAULT_DRIVER
from kirami_cli.exceptions import ModuleLoadFailed
from kirami_cli.handlers import (
    FileFilter,
    Reloader,
    call_pip_install,
    create_project,
    create_virtualenv,
    get_project_root,
    list_adapters,
    list_drivers,
    run_project,
    terminate_process,
)
from kirami_cli.log import ClickHandler

VALID_PROJECT_NAME = r"^[a-zA-Z][a-zA-Z0-9 _-]*$"
BLACKLISTED_PROJECT_NAME = {"kiramibot", "kirami", "bot"}

BLACKLISTED_PROJECT_NAME.update(sys.stdlib_module_names)


@dataclass
class ProjectContext:
    """项目模板生成上下文

    参数:
        variables: 模板渲染变量字典
        packages: 项目需要安装的包
    """

    variables: dict[str, Any] = field(default_factory=dict)
    packages: list[str] = field(default_factory=list)


def project_name_validator(name: str) -> bool:
    return (
        bool(re.match(VALID_PROJECT_NAME, name))
        and name not in BLACKLISTED_PROJECT_NAME
    )


async def prompt_common_context(context: ProjectContext) -> ProjectContext:
    click.secho(_("Loading adapters..."))
    all_adapters = await list_adapters()
    click.secho(_("Loading drivers..."))
    all_drivers = await list_drivers()
    click.clear()

    project_name = await InputPrompt(
        _("Project Name:"),
        validator=project_name_validator,
        error_message=_("Invalid project name!"),
    ).prompt_async(style=CLI_DEFAULT_STYLE)
    context.variables["project_name"] = project_name

    drivers = await CheckboxPrompt(
        _("Which driver(s) would you like to use?"),
        [Choice(f"{driver.name} ({driver.desc})", driver) for driver in all_drivers],
        default_select=[
            index
            for index, driver in enumerate(all_drivers)
            if driver.name in DEFAULT_DRIVER
        ],
        validator=bool,
        error_message=_("Chosen drivers is not valid!"),
    ).prompt_async(style=CLI_DEFAULT_STYLE)
    context.variables["drivers"] = json.dumps(
        {d.data.project_link: d.data.model_dump() for d in drivers}
    )
    context.packages.extend(
        [d.data.project_link for d in drivers if d.data.project_link]
    )

    confirm = False
    adapters = []
    while not confirm:
        adapters = await CheckboxPrompt(
            _("Which adapter(s) would you like to use?"),
            [
                Choice(f"{adapter.name} ({adapter.desc})", adapter)
                for adapter in all_adapters
            ],
            default_select=[
                index
                for index, adapter in enumerate(all_adapters)
                if adapter.name in DEFAULT_ADAPTER
            ],
        ).prompt_async(style=CLI_DEFAULT_STYLE)
        confirm = (
            True
            if adapters
            else await ConfirmPrompt(
                _("You haven't chosen any adapter! Please confirm."),
                default_choice=False,
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        )

    context.variables["adapters"] = json.dumps(
        {a.data.project_link: a.data.model_dump() for a in adapters}
    )
    context.packages.extend([a.data.project_link for a in adapters])

    return context


@click.command(
    cls=ClickAliasedCommand,
    aliases=["init"],
    context_settings={"ignore_unknown_options": True},
    help=_("Create a KiramiBot project."),
)
@click.option(
    "-o",
    "--output-dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.option("-t", "--template", default=None, help=_("The project template to use."))
@click.option(
    "-p",
    "--python-interpreter",
    default=None,
    help=_("The python interpreter virtualenv is installed into."),
)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def create(
    ctx: click.Context,
    output_dir: str | None,
    template: str | None,
    python_interpreter: str | None,
    pip_args: list[str] | None,
):
    context = ProjectContext()
    try:
        context = await prompt_common_context(context)
    except ModuleLoadFailed as e:
        click.secho(repr(e), fg="red")
        ctx.exit()
    except CancelledError:
        ctx.exit()

    create_project(template, {"kiramibot": context.variables}, output_dir)

    try:
        install_dependencies = await ConfirmPrompt(
            _("Install dependencies now?"), default_choice=True
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    except CancelledError:
        ctx.exit()

    project_dir_name = context.variables["project_name"].replace(" ", "-")
    project_dir = Path(output_dir or ".") / project_dir_name

    if install_dependencies:
        use_venv = False
        venv_dir = project_dir / ".venv"

        try:
            use_venv = await ConfirmPrompt(
                _("Create virtual environment?"), default_choice=True
            ).prompt_async(style=CLI_DEFAULT_STYLE)
        except CancelledError:
            ctx.exit()

        if use_venv:
            click.secho(
                _("Creating virtual environment in {venv_dir} ...").format(
                    venv_dir=venv_dir
                ),
                fg="yellow",
            )
            await create_virtualenv(
                venv_dir, prompt=project_dir_name, python_path=python_interpreter
            )

        config_manager = ConfigManager(working_dir=project_dir, use_venv=use_venv)

        proc = await call_pip_install(
            ["kiramibot", *context.packages],
            pip_args,
            python_path=config_manager.python_path,
        )
        await proc.wait()

        if proc.returncode != 0:
            click.secho(
                _(
                    "Failed to install dependencies! "
                    "You should install the dependencies manually."
                ),
                fg="red",
            )

    click.secho(_("Done!"), fg="green")
    click.secho(
        _(
            "Add following packages to your project "
            "using dependency manager like poetry or pdm:"
        ),
        fg="green",
    )
    click.secho(f"  {' '.join(context.packages)}", fg="green")
    click.secho(_("Run the following command to start your bot:"), fg="green")
    click.secho(f"  cd {project_dir}", fg="green")
    click.secho("  kirami run --reload", fg="green")


@click.command(
    cls=ClickAliasedCommand, aliases=["start"], help=_("Run the bot in current folder.")
)
@click.option(
    "-f",
    "--file",
    default="bot.py",
    show_default=True,
    help=_("Exist entry file of your bot."),
)
@click.option(
    "-r",
    "--reload",
    is_flag=True,
    default=False,
    help=_("Reload the bot when file changed."),
)
@click.option(
    "--reload-includes",
    multiple=True,
    default=None,
    help=_("Files to watch for changes."),
)
@click.option(
    "--reload-excludes",
    multiple=True,
    default=None,
    help=_("Files to ignore for changes."),
)
@click.option(
    "--reload-delay",
    type=float,
    default=0.5,
    show_default=True,
    help=_("Delay time for reloading in seconds."),
)
@run_async
async def run(
    file: str,
    reload: bool,
    reload_includes: list[str] | None,
    reload_excludes: list[str] | None,
    reload_delay: float,
):
    if reload:
        logger = Logger(__name__)
        logger.addHandler(ClickHandler())
        await Reloader(
            partial(run_project, exist_bot=Path(file)),
            terminate_process,
            file_filter=FileFilter(reload_includes, reload_excludes),
            reload_delay=reload_delay,
            cwd=get_project_root(),
            logger=logger,
        ).run()
    else:
        proc = await run_project(exist_bot=Path(file))
        await proc.wait()
