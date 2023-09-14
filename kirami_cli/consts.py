import os
import sys

# consts
PLUGINS_GROUP = "kirami"
SCRIPTS_GROUP = "kirami_scripts"
REQUIRES_PYTHON = (3, 10)
DEFAULT_DRIVER = ("FastAPI",)
DEFAULT_ADAPTER = ("OneBot V11",)
# SHELL = os.getenv("SHELL", "")
WINDOWS = sys.platform.startswith("win") or (sys.platform == "cli" and os.name == "nt")
# MINGW = sysconfig.get_platform().startswith("mingw")
# MACOS = sys.platform == "darwin"
