import asyncio
from functools import cache
from pathlib import Path
from textwrap import dedent
from typing import IO, Any

from cookiecutter.main import cookiecutter

from .meta import (
    get_default_python,
    get_project_root,
    requires_kiramibot,
    requires_project_root,
)
from .process import create_process

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "project"


def create_project(
    template: str | None = None,
    context: dict[str, Any] | None = None,
    output_dir: str | None = None,
    no_input: bool = True,
) -> None:
    cookiecutter(
        str(TEMPLATE_ROOT.resolve()) if template is None else template,
        no_input=no_input,
        extra_context=context,
        output_dir=output_dir or ".",
    )


@cache
def generate_run_script() -> str:
    return dedent(
        """\
        from kirami import KiramiBot

        bot = KiramiBot()

        if __name__ == "__main__":
            bot.run()
        """
    )


@requires_project_root
@requires_kiramibot
async def run_project(
    exist_bot: Path = Path("bot.py"),
    *,
    python_path: str | None = None,
    cwd: Path | None = None,
    stdin: IO[Any] | int | None = None,
    stdout: IO[Any] | int | None = None,
    stderr: IO[Any] | int | None = None,
) -> asyncio.subprocess.Process:
    if python_path is None:
        python_path = await get_default_python()
    if cwd is None:
        cwd = get_project_root()

    if cwd.joinpath(exist_bot).exists():
        return await create_process(
            python_path,
            exist_bot,
            cwd=cwd,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
        )

    return await create_process(
        python_path,
        "-c",
        generate_run_script(),
        cwd=cwd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )
