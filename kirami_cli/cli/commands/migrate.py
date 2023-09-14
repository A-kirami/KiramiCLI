from pathlib import Path

import click
from noneprompt import CancelledError, ConfirmPrompt

from kirami_cli import _
from kirami_cli.cli import CLI_DEFAULT_STYLE, ClickAliasedCommand, run_async
from kirami_cli.config import ConfigManager
from kirami_cli.handlers import call_pip_install


@click.command(
    cls=ClickAliasedCommand,
    context_settings={"ignore_unknown_options": True},
    help=_("Migrate from nonebot2."),
)
@click.option(
    "-s",
    "--source_dir",
    default=None,
    type=click.Path(exists=True, file_okay=False, writable=True),
)
@click.argument("pip_args", nargs=-1, default=None)
@click.pass_context
@run_async
async def migrate(
    ctx: click.Context, source_dir: str | None, pip_args: list[str] | None
):
    config_manager = ConfigManager(working_dir=Path(source_dir or "."))

    if config_manager.config_file.is_file():
        click.secho(
            _(
                "The KiramiBot configuration already exists. "
                "Please run `kirami run` to start your bot."
            ),
            fg="red",
        )
        ctx.exit(1)

    nonebot_config = config_manager.get_nonebot_config()
    if not nonebot_config.model_dump(exclude_defaults=True):
        click.secho(
            _(
                "The NoneBot2 configuration does not exist. "
                "Please run `kirami init` to create a new KiramiBot project."
            ),
            fg="red",
        )
        ctx.exit(1)

    click.echo(
        _("Detected NoneBot2 project: {project_root}").format(
            project_root=config_manager.project_root
        )
    )

    click.echo(_("Migrating project..."))
    config_manager.migrate()

    try:
        install_dependencies = await ConfirmPrompt(
            _("Install dependencies now?"), default_choice=True
        ).prompt_async(style=CLI_DEFAULT_STYLE)
    except CancelledError:
        ctx.exit()

    if install_dependencies:
        proc = await call_pip_install("kiramibot", pip_args)
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
    click.secho("  kiramibot", fg="green")
    click.secho(_("Run the following command to start your bot:"), fg="green")
    click.secho("  kirami run --reload", fg="green")
