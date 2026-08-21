import platform
import sys 
def check_environment():
    return {"python_version": platform.python_version(),
            "platform": platform.system(),
            "venv_active": sys.prefix != sys.base_prefix}