from pathlib import Path

from cookiecutter.main import cookiecutter

from kirami_cli.config import Plugin

from .store import load_module_data

TEMPLATE_ROOT = Path(__file__).parent.parent / "template" / "plugin"


def create_plugin(
    plugin_name: str,
    output_dir: str = ".",
    sub_plugin: bool = False,
    template: str | None = None,
):
    cookiecutter(
        str(TEMPLATE_ROOT.resolve()) if template is None else template,
        no_input=True,
        output_dir=output_dir,
        extra_context={"plugin_name": plugin_name, "sub_plugin": sub_plugin},
    )


async def list_plugins(query: str | None = None) -> list[Plugin]:
    plugins = await load_module_data("plugin")
    if query is None:
        return plugins

    return [
        plugin
        for plugin in plugins
        if any(query in value for value in plugin.model_dump().values())
    ]
