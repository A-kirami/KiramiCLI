from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from kirami_cli.consts import SCRIPTS_GROUP

templates = Environment(
    trim_blocks=True,
    lstrip_blocks=True,
    autoescape=False,
    loader=FileSystemLoader(Path(__file__).parent.parent / "template" / "scripts"),
    enable_async=True,
)
templates.globals["ENTRYPOINT_GROUP"] = SCRIPTS_GROUP
templates.filters["repr"] = repr

# meta
from .meta import draw_logo as draw_logo
from .meta import get_default_python as get_default_python
from .meta import get_kiramibot_config as get_kiramibot_config
from .meta import get_kiramibot_version as get_kiramibot_version
from .meta import get_pip_version as get_pip_version
from .meta import get_project_root as get_project_root
from .meta import get_python_version as get_python_version
from .meta import requires_kiramibot as requires_kiramibot
from .meta import requires_pip as requires_pip
from .meta import requires_project_root as requires_project_root
from .meta import requires_python as requires_python

# isort: split

# data
from .data import CACHE_DIR as CACHE_DIR
from .data import CONFIG_DIR as CONFIG_DIR
from .data import DATA_DIR as DATA_DIR

# isort: split

# package
from .store import format_package_results as format_package_results
from .store import load_module_data as load_module_data

# isort: split

# process
from .process import create_process as create_process
from .process import create_process_shell as create_process_shell
from .process import ensure_process_terminated as ensure_process_terminated
from .process import terminate_process as terminate_process

# isort: split

# pip
from .pip import call_pip as call_pip
from .pip import call_pip_install as call_pip_install
from .pip import call_pip_list as call_pip_list
from .pip import call_pip_uninstall as call_pip_uninstall
from .pip import call_pip_update as call_pip_update

# isort: split

# virtualenv
from .venv import create_virtualenv as create_virtualenv
from .venv import detect_virtualenv as detect_virtualenv

# isort: split

# signal
from .signal import install_signal_handler as install_signal_handler
from .signal import register_signal_handler as register_signal_handler
from .signal import remove_signal_handler as remove_signal_handler
from .signal import shield_signals as shield_signals

# isort: split

# plugin
from .plugin import create_plugin as create_plugin
from .plugin import list_plugins as list_plugins

# isort: split

# adapter
from .adapter import create_adapter as create_adapter
from .adapter import list_adapters as list_adapters

# isort: split

# driver
from .driver import list_drivers as list_drivers

# isort: split

# script
from .script import list_scripts as list_scripts
from .script import run_script as run_script

# isort: split

# project
from .project import create_project as create_project
from .project import generate_run_script as generate_run_script
from .project import run_project as run_project
from .reloader import FileFilter as FileFilter
from .reloader import Reloader as Reloader
