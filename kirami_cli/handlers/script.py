import asyncio
import json
from pathlib import Path
from typing import IO, Any

from . import templates
from .meta import (
    get_default_python,
    get_project_root,
    requires_kiramibot,
    requires_project_root,
    requires_python,
)
from .process import create_process


@requires_project_root
@requires_python
async def list_scripts(
    *, python_path: str | None = None, cwd: Path | None = None
) -> list[str]:
    if python_path is None:
        python_path = await get_default_python(cwd)

    t = templates.get_template("script/list_scripts.py.jinja")
    proc = await create_process(
        python_path,
        "-W",
        "ignore",
        "-c",
        await t.render_async(),
        stdout=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return json.loads(stdout.strip())


@requires_project_root
@requires_kiramibot
async def run_script(
    script_name: str,
    script_args: list[str] | None = None,
    *,
    python_path: str | None = None,
    cwd: Path | None = None,
    stdin: IO[Any] | int | None = None,
    stdout: IO[Any] | int | None = None,
    stderr: IO[Any] | int | None = None,
) -> asyncio.subprocess.Process:
    if script_args is None:
        script_args = []

    if python_path is None:
        python_path = await get_default_python()
    if cwd is None:
        cwd = get_project_root()

    t = templates.get_template("script/run_script.py.jinja")

    return await create_process(
        python_path,
        "-c",
        await t.render_async(
            script_name=script_name,
        ),
        *script_args,
        cwd=cwd,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )
