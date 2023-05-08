VERSION = "5.15.1"
PROJECT_NAME = "aksara"
LOGICA_VERSION = None
current_path = None
updated_path = None
LOG_BUFFER = []


def set_logica_version(aksara_path="."):
    from .utils.app import get_current_logica_version

    global LOGICA_VERSION
    if not LOGICA_VERSION:
        LOGICA_VERSION = get_current_logica_version(aksara_path=aksara_path)
