import json
import logging
from functools import cached_property
from itertools import product
from pathlib import Path
from typing import Any, ClassVar

import tomlkit
from ruamel.yaml import YAML
from tomlkit.toml_document import TOMLDocument

from kirami_cli import _
from kirami_cli.consts import WINDOWS
from kirami_cli.exceptions import ProjectNotFoundError
from kirami_cli.log import SUCCESS

from .model import KiramiBotConfig, NoneBotConfig

CONFIG_NAME = ("kirami", "kirami.config")
CONFIG_TYPE = ("toml", "yaml", "yml", "json")

DEFAULT_CONFIG_FILE = "kirami.config.toml"
PROJECT_FILE = "pyproject.toml"
FILE_ENCODING = "utf-8"

CONFIG_LOADS = {
    "toml": tomlkit.parse,
    "yaml": YAML().load,
    "json": json.loads,
}
CONFIG_DUMPS = {
    "toml": tomlkit.dumps,
    "yaml": YAML().dump,
    "json": json.dumps,
}
CONFIG_LOADS["yml"] = CONFIG_LOADS["yaml"]
CONFIG_DUMPS["yml"] = CONFIG_DUMPS["yaml"]


class ConfigManager:
    _global_working_dir: ClassVar[Path | None] = None
    _global_python_path: ClassVar[str | None] = None
    _global_use_venv: ClassVar[bool] = True
    _path_venv_cache: ClassVar[dict[Path, str | None]] = {}

    def __init__(
        self,
        *,
        working_dir: Path | None = None,
        python_path: str | None = None,
        use_venv: bool | None = None,
        logger: logging.Logger | None = None,
    ):
        self._working_dir = working_dir
        self._python_path = python_path
        self._use_venv = use_venv
        self._logger = logger

    @property
    def working_dir(self) -> Path:
        return (self._working_dir or self._global_working_dir or Path.cwd()).resolve()

    @staticmethod
    def _locate_project_root(cwd: Path | None = None) -> Path:
        cwd = (cwd or Path.cwd()).resolve()
        for dir in (cwd,) + tuple(cwd.parents):
            if dir.joinpath(PROJECT_FILE).is_file():
                return dir
        raise ProjectNotFoundError(
            _(
                "Cannot find project root directory! {config_file} file not exists."
            ).format(config_file=PROJECT_FILE)
        )

    @cached_property
    def project_root(self) -> Path:
        return self._locate_project_root(self.working_dir)

    @cached_property
    def project_file(self) -> Path:
        return self.project_root.joinpath(PROJECT_FILE)

    @cached_property
    def config_file(self) -> Path:
        for name, type in product(CONFIG_NAME, CONFIG_TYPE):
            file = self.project_root.joinpath(f"{name}.{type}")
            if file.is_file():
                return file
        return self.project_root.joinpath(DEFAULT_CONFIG_FILE)

    @cached_property
    def config_type(self) -> str:
        return self.config_file.suffix.removeprefix(".")

    @staticmethod
    def _detact_virtual_env(cwd: Path | None = None) -> str | None:
        cwd = (cwd or Path.cwd()).resolve()
        for venv_dir in cwd.iterdir():
            if venv_dir.is_dir() and (venv_dir / "pyvenv.cfg").is_file():
                return str(
                    venv_dir
                    / ("Scripts" if WINDOWS else "bin")
                    / ("python.exe" if WINDOWS else "python")
                )

    @cached_property
    def python_path(self) -> str | None:
        if python := (self._python_path or self._global_python_path):
            return python
        elif self.use_venv:
            try:
                cwd = self.project_root.resolve()
            except ProjectNotFoundError:
                cwd = Path.cwd().resolve()

            if cwd in self._path_venv_cache:
                return self._path_venv_cache[cwd]

            if venv_python := self._detact_virtual_env(cwd):
                self._path_venv_cache[cwd] = venv_python
                if self._logger:
                    self._logger.log(
                        SUCCESS,
                        _("Using python: {python_path}").format(
                            python_path=venv_python
                        ),
                    )
                return venv_python

    @property
    def use_venv(self) -> bool:
        return self._use_venv if self._use_venv is not None else self._global_use_venv

    def _get_data(self) -> TOMLDocument | dict[str, Any]:
        self.config_file.touch()
        text = self.config_file.read_text(encoding=FILE_ENCODING)
        return CONFIG_LOADS[self.config_type](text)

    def _write_data(self, data: TOMLDocument | dict[str, Any]) -> None:
        self.config_file.touch()
        text = CONFIG_DUMPS[self.config_type](data)
        self.config_file.write_text(text, encoding=FILE_ENCODING)

    def get_kiramibot_config(self) -> KiramiBotConfig:
        data = self._get_data()
        bot = data.get("bot", {})
        plugin = data.get("plugin", {})
        return KiramiBotConfig(**bot, **plugin)

    def get_nonebot_config(self) -> NoneBotConfig:
        data = tomlkit.parse(self.project_file.read_text(encoding=FILE_ENCODING))
        return NoneBotConfig(**data.get("tool", {}).get("nonebot", {}))

    def migrate(self) -> None:
        data = self._get_data()
        nonebot_config = self.get_nonebot_config()
        bot: dict[str, Any] = data.setdefault("bot", {})
        adapters: list[str] = bot.setdefault("adapters", [])
        adapters += [
            a.module_name.replace("nonebot.adapters.", "~")
            for a in nonebot_config.adapters
        ]
        plugin: dict[str, Any] = data.setdefault("plugin", {})
        plugins = plugin.setdefault("plugins", [])
        plugins += nonebot_config.plugins
        plugin_dirs = plugin.setdefault("plugin_dirs", [])
        plugin_dirs += nonebot_config.plugin_dirs
        self._write_data(data)

    def add_driver(self, driver: str) -> None:
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("bot", {})
        drivers: list[str] = table.setdefault("driver", "").split("+")
        driver_names = [
            driver,
            driver.replace("nonebot.drivers.", "~"),
        ]
        if all(d not in driver_names for d in drivers):
            drivers.append(driver_names[1])
        table["driver"] = "+".join(drivers)
        self._write_data(data)

    def remove_driver(self, driver: str) -> None:
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("bot", {})
        drivers: list[str] = table.setdefault("driver", "").split("+")
        driver_names = [
            driver,
            driver.replace("nonebot.drivers.", "~"),
        ]
        for driver_name in driver_names:
            if driver_name in drivers:
                drivers.remove(driver_name)
        table["driver"] = "+".join(drivers)
        self._write_data(data)

    def add_adapter(self, adapter: str) -> None:
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("bot", {})
        adapters: list[str] = table.setdefault("adapters", [])
        adapter_names = [
            adapter,
            adapter.replace("nonebot.adapters.", "~"),
        ]
        if all(a not in adapter_names for a in adapters):
            adapters.append(adapter_names[1])
        self._write_data(data)

    def remove_adapter(self, adapter: str) -> None:
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("bot", {})
        adapters: list[str] = table.setdefault("adapters", [])
        adapter_names = [
            adapter,
            adapter.replace("nonebot.adapters.", "~"),
        ]
        for adapter_name in adapter_names:
            if adapter_name in adapters:
                adapters.remove(adapter_name)
        self._write_data(data)

    def add_plugin(self, plugin: str) -> None:
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("plugin", {})
        plugins: list[str] = table.setdefault("plugins", [])
        if plugin not in plugins:
            plugins.append(plugin)
        self._write_data(data)

    def remove_plugin(self, plugin: str) -> None:
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("plugin", {})
        plugins: list[str] = table.setdefault("plugins", [])
        if plugin in plugins:
            plugins.remove(plugin)
        self._write_data(data)

    def add_plugin_dir(self, plugin_dir: str) -> None:
        data = self._get_data()
        table: dict[str, Any] = data.setdefault("plugin", {})
        plugin_dirs: list[str] = table.setdefault("plugin_dirs", [])
        if plugin_dir not in plugin_dirs:
            plugin_dirs.append(plugin_dir)
        self._write_data(data)
