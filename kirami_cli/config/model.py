from pydantic import BaseModel, Extra


class SimpleInfo(BaseModel):
    name: str
    module_name: str


class Adapter(SimpleInfo):
    project_link: str
    desc: str


class Plugin(SimpleInfo):
    project_link: str
    desc: str


class Driver(SimpleInfo):
    project_link: str
    desc: str


class KiramiBotConfig(BaseModel, extra=Extra.allow):
    driver: str = ""
    adapters: list[str] = []
    plugins: list[str] = []
    plugin_dirs: list[str] = []


class NoneBotConfig(BaseModel, extra=Extra.allow):
    adapters: list[SimpleInfo] = []
    plugins: list[str] = []
    plugin_dirs: list[str] = []
    builtin_plugins: list[str] = []
