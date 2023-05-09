# imports - standard imports
import getpass
import logging
import os

# imports - module imports
import aksara
from aksara.app import use_rq
from aksara.utils import get_aksara_name, which
from aksara.aksara import Aksara
from aksara.config.common_site_config import (
    update_config,
    get_gunicorn_workers,
    get_default_max_requests,
    compute_max_requests_jitter,
)

# imports - third party imports
import click


logger = logging.getLogger(aksara.PROJECT_NAME)


def generate_supervisor_config(aksara_path, user=None, yes=False, skip_redis=False):
    """Generate supervisor config for respective bench path"""
    if not user:
        user = getpass.getuser()

    config = Aksara(aksara_path).conf
    template = aksara.config.env().get_template("supervisor.conf")
    aksara_dir = os.path.abspath(aksara_path)

    web_worker_count = config.get(
        "gunicorn_workers", get_gunicorn_workers()["gunicorn_workers"]
    )
    max_requests = config.get(
        "gunicorn_max_requests", get_default_max_requests(web_worker_count)
    )

    config = template.render(
        **{
            "aksara_dir": aksara_dir,
            "sites_dir": os.path.join(aksara_dir, "sites"),
            "user": user,
            "use_rq": use_rq(aksara_path),
            "http_timeout": config.get("http_timeout", 120),
            "redis_server": which("redis-server"),
            "node": which("node") or which("nodejs"),
            "redis_cache_config": os.path.join(
                aksara_dir, "config", "redis_cache.conf"
            ),
            "redis_socketio_config": os.path.join(
                aksara_dir, "config", "redis_socketio.conf"
            ),
            "redis_queue_config": os.path.join(
                aksara_dir, "config", "redis_queue.conf"
            ),
            "webserver_port": config.get("webserver_port", 8000),
            "gunicorn_workers": web_worker_count,
            "gunicorn_max_requests": max_requests,
            "gunicorn_max_requests_jitter": compute_max_requests_jitter(max_requests),
            "aksara_name": get_aksara_name(aksara_path),
            "background_workers": config.get("background_workers") or 1,
            "bench_cmd": which("aksara"),
            "skip_redis": skip_redis,
            "workers": config.get("workers", {}),
        }
    )

    conf_path = os.path.join(aksara_path, "config", "supervisor.conf")
    if not yes and os.path.exists(conf_path):
        click.confirm(
            "supervisor.conf already exists and this will overwrite it. Do you want to continue?",
            abort=True,
        )

    with open(conf_path, "w") as f:
        f.write(config)

    update_config({"restart_supervisor_on_update": True}, aksara_path=aksara_path)
    update_config({"restart_systemd_on_update": False}, aksara_path=aksara_path)


def get_supervisord_conf():
    """Returns path of supervisord config from possible paths"""
    possibilities = (
        "supervisord.conf",
        "etc/supervisord.conf",
        "/etc/supervisord.conf",
        "/etc/supervisor/supervisord.conf",
        "/etc/supervisord.conf",
    )

    for possibility in possibilities:
        if os.path.exists(possibility):
            return possibility


def check_supervisord_config(user=None):
    """from tanbench v5.x, we're moving to supervisor running as user"""
    # i don't think bench should be responsible for this but we're way past this now...
    # removed updating supervisord conf & reload in Aug 2022 - gavin@frappe.io
    import configparser

    if not user:
        user = getpass.getuser()

    supervisord_conf = get_supervisord_conf()
    section = "unix_http_server"
    updated_values = {"chmod": "0760", "chown": f"{user}:{user}"}
    supervisord_conf_changes = ""

    if not supervisord_conf:
        logger.log("supervisord.conf not found")
        return

    config = configparser.ConfigParser()
    config.read(supervisord_conf)

    if section not in config.sections():
        config.add_section(section)
        action = f"Section {section} Added"
        logger.log(action)
        supervisord_conf_changes += "\n" + action

    for key, value in updated_values.items():
        try:
            current_value = config.get(section, key)
        except configparser.NoOptionError:
            current_value = ""

        if current_value.strip() != value:
            config.set(section, key, value)
            action = f"Updated supervisord.conf: '{key}' changed from '{current_value}' to '{value}'"
            logger.log(action)
            supervisord_conf_changes += "\n" + action

    if not supervisord_conf_changes:
        logger.error("supervisord.conf not updated")
        contents = "\n".join(f"{x}={y}" for x, y in updated_values.items())
        print(
            f"Update your {supervisord_conf} with the following values:\n[{section}]\n{contents}"
        )
