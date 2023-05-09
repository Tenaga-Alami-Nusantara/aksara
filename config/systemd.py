# imports - standard imports
import getpass
import os

# imports - third partyimports
import click

# imports - module imports
import aksara
from aksara.app import use_rq
from aksara.aksara import Aksara
from aksara.config.common_site_config import (
    get_gunicorn_workers,
    update_config,
    get_default_max_requests,
    compute_max_requests_jitter,
)
from aksara.utils import exec_cmd, which, get_aksara_name


def generate_systemd_config(
    aksara_path,
    user=None,
    yes=False,
    stop=False,
    create_symlinks=False,
    delete_symlinks=False,
):
    if not user:
        user = getpass.getuser()

    config = Aksara(aksara_path).conf

    aksara_dir = os.path.abspath(aksara_path)
    aksara_name = get_aksara_name(aksara_path)

    if stop:
        exec_cmd(
            f"sudo systemctl stop -- $(systemctl show -p Requires {aksara_name}.target | cut -d= -f2)"
        )
        return

    if create_symlinks:
        _create_symlinks(aksara_path)
        return

    if delete_symlinks:
        _delete_symlinks(aksara_path)
        return

    number_of_workers = config.get("background_workers") or 1
    background_workers = []
    for i in range(number_of_workers):
        background_workers.append(
            get_aksara_name(aksara_path)
            + "-logica-default-worker@"
            + str(i + 1)
            + ".service"
        )

    for i in range(number_of_workers):
        background_workers.append(
            get_aksara_name(aksara_path)
            + "-logica-short-worker@"
            + str(i + 1)
            + ".service"
        )

    for i in range(number_of_workers):
        background_workers.append(
            get_aksara_name(aksara_path)
            + "-logica-long-worker@"
            + str(i + 1)
            + ".service"
        )

    web_worker_count = config.get(
        "gunicorn_workers", get_gunicorn_workers()["gunicorn_workers"]
    )
    max_requests = config.get(
        "gunicorn_max_requests", get_default_max_requests(web_worker_count)
    )

    bench_info = {
        "aksara_dir": aksara_dir,
        "sites_dir": os.path.join(aksara_dir, "sites"),
        "user": user,
        "use_rq": use_rq(aksara_path),
        "http_timeout": config.get("http_timeout", 120),
        "redis_server": which("redis-server"),
        "node": which("node") or which("nodejs"),
        "redis_cache_config": os.path.join(aksara_dir, "config", "redis_cache.conf"),
        "redis_socketio_config": os.path.join(
            aksara_dir, "config", "redis_socketio.conf"
        ),
        "redis_queue_config": os.path.join(aksara_dir, "config", "redis_queue.conf"),
        "webserver_port": config.get("webserver_port", 8000),
        "gunicorn_workers": web_worker_count,
        "gunicorn_max_requests": max_requests,
        "gunicorn_max_requests_jitter": compute_max_requests_jitter(max_requests),
        "aksara_name": get_aksara_name(aksara_path),
        "worker_target_wants": " ".join(background_workers),
        "bench_cmd": which("aksara"),
    }

    if not yes:
        click.confirm(
            "current systemd configuration will be overwritten. Do you want to continue?",
            abort=True,
        )

    setup_systemd_directory(aksara_path)
    setup_main_config(bench_info, aksara_path)
    setup_workers_config(bench_info, aksara_path)
    setup_web_config(bench_info, aksara_path)
    setup_redis_config(bench_info, aksara_path)

    update_config({"restart_systemd_on_update": False}, aksara_path=aksara_path)
    update_config({"restart_supervisor_on_update": False}, aksara_path=aksara_path)


def setup_systemd_directory(aksara_path):
    if not os.path.exists(os.path.join(aksara_path, "config", "systemd")):
        os.makedirs(os.path.join(aksara_path, "config", "systemd"))


def setup_main_config(bench_info, aksara_path):
    # Main config
    bench_template = aksara.config.env().get_template("systemd/logica-aksara.target")
    bench_config = bench_template.render(**bench_info)
    bench_config_path = os.path.join(
        aksara_path, "config", "systemd", bench_info.get("aksara_name") + ".target"
    )

    with open(bench_config_path, "w") as f:
        f.write(bench_config)


def setup_workers_config(bench_info, aksara_path):
    # Worker Group
    bench_workers_target_template = aksara.config.env().get_template(
        "systemd/logica-bench-workers.target"
    )
    bench_default_worker_template = aksara.config.env().get_template(
        "systemd/logica-bench-logica-default-worker.service"
    )
    bench_short_worker_template = aksara.config.env().get_template(
        "systemd/logica-bench-logica-short-worker.service"
    )
    bench_long_worker_template = aksara.config.env().get_template(
        "systemd/logica-bench-logica-long-worker.service"
    )
    bench_schedule_worker_template = aksara.config.env().get_template(
        "systemd/logica-bench-logica-schedule.service"
    )

    bench_workers_target_config = bench_workers_target_template.render(**bench_info)
    bench_default_worker_config = bench_default_worker_template.render(**bench_info)
    bench_short_worker_config = bench_short_worker_template.render(**bench_info)
    bench_long_worker_config = bench_long_worker_template.render(**bench_info)
    bench_schedule_worker_config = bench_schedule_worker_template.render(**bench_info)

    bench_workers_target_config_path = os.path.join(
        aksara_path,
        "config",
        "systemd",
        bench_info.get("aksara_name") + "-workers.target",
    )
    bench_default_worker_config_path = os.path.join(
        aksara_path,
        "config",
        "systemd",
        bench_info.get("aksara_name") + "-logica-default-worker@.service",
    )
    bench_short_worker_config_path = os.path.join(
        aksara_path,
        "config",
        "systemd",
        bench_info.get("aksara_name") + "-logica-short-worker@.service",
    )
    bench_long_worker_config_path = os.path.join(
        aksara_path,
        "config",
        "systemd",
        bench_info.get("aksara_name") + "-logica-long-worker@.service",
    )
    bench_schedule_worker_config_path = os.path.join(
        aksara_path,
        "config",
        "systemd",
        bench_info.get("aksara_name") + "-logica-schedule.service",
    )

    with open(bench_workers_target_config_path, "w") as f:
        f.write(bench_workers_target_config)

    with open(bench_default_worker_config_path, "w") as f:
        f.write(bench_default_worker_config)

    with open(bench_short_worker_config_path, "w") as f:
        f.write(bench_short_worker_config)

    with open(bench_long_worker_config_path, "w") as f:
        f.write(bench_long_worker_config)

    with open(bench_schedule_worker_config_path, "w") as f:
        f.write(bench_schedule_worker_config)


def setup_web_config(bench_info, aksara_path):
    # Web Group
    bench_web_target_template = aksara.config.env().get_template(
        "systemd/logica-bench-web.target"
    )
    bench_web_service_template = aksara.config.env().get_template(
        "systemd/logica-bench-logica-web.service"
    )
    bench_node_socketio_template = aksara.config.env().get_template(
        "systemd/logica-bench-node-socketio.service"
    )

    bench_web_target_config = bench_web_target_template.render(**bench_info)
    bench_web_service_config = bench_web_service_template.render(**bench_info)
    bench_node_socketio_config = bench_node_socketio_template.render(**bench_info)

    bench_web_target_config_path = os.path.join(
        aksara_path, "config", "systemd", bench_info.get("aksara_name") + "-web.target"
    )
    bench_web_service_config_path = os.path.join(
        aksara_path,
        "config",
        "systemd",
        bench_info.get("aksara_name") + "-logica-web.service",
    )
    bench_node_socketio_config_path = os.path.join(
        aksara_path,
        "config",
        "systemd",
        bench_info.get("aksara_name") + "-node-socketio.service",
    )

    with open(bench_web_target_config_path, "w") as f:
        f.write(bench_web_target_config)

    with open(bench_web_service_config_path, "w") as f:
        f.write(bench_web_service_config)

    with open(bench_node_socketio_config_path, "w") as f:
        f.write(bench_node_socketio_config)


def setup_redis_config(bench_info, aksara_path):
    # Redis Group
    bench_redis_target_template = aksara.config.env().get_template(
        "systemd/logica-bench-redis.target"
    )
    bench_redis_cache_template = aksara.config.env().get_template(
        "systemd/logica-bench-redis-cache.service"
    )
    bench_redis_queue_template = aksara.config.env().get_template(
        "systemd/logica-bench-redis-queue.service"
    )
    bench_redis_socketio_template = aksara.config.env().get_template(
        "systemd/logica-bench-redis-socketio.service"
    )

    bench_redis_target_config = bench_redis_target_template.render(**bench_info)
    bench_redis_cache_config = bench_redis_cache_template.render(**bench_info)
    bench_redis_queue_config = bench_redis_queue_template.render(**bench_info)
    bench_redis_socketio_config = bench_redis_socketio_template.render(**bench_info)

    bench_redis_target_config_path = os.path.join(
        aksara_path,
        "config",
        "systemd",
        bench_info.get("aksara_name") + "-redis.target",
    )
    bench_redis_cache_config_path = os.path.join(
        aksara_path,
        "config",
        "systemd",
        bench_info.get("aksara_name") + "-redis-cache.service",
    )
    bench_redis_queue_config_path = os.path.join(
        aksara_path,
        "config",
        "systemd",
        bench_info.get("aksara_name") + "-redis-queue.service",
    )
    bench_redis_socketio_config_path = os.path.join(
        aksara_path,
        "config",
        "systemd",
        bench_info.get("aksara_name") + "-redis-socketio.service",
    )

    with open(bench_redis_target_config_path, "w") as f:
        f.write(bench_redis_target_config)

    with open(bench_redis_cache_config_path, "w") as f:
        f.write(bench_redis_cache_config)

    with open(bench_redis_queue_config_path, "w") as f:
        f.write(bench_redis_queue_config)

    with open(bench_redis_socketio_config_path, "w") as f:
        f.write(bench_redis_socketio_config)


def _create_symlinks(aksara_path):
    aksara_dir = os.path.abspath(aksara_path)
    etc_systemd_system = os.path.join("/", "etc", "systemd", "system")
    config_path = os.path.join(aksara_dir, "config", "systemd")
    unit_files = get_unit_files(aksara_dir)
    for unit_file in unit_files:
        filename = "".join(unit_file)
        exec_cmd(
            f'sudo ln -s {config_path}/{filename} {etc_systemd_system}/{"".join(unit_file)}'
        )
    exec_cmd("sudo systemctl daemon-reload")


def _delete_symlinks(aksara_path):
    aksara_dir = os.path.abspath(aksara_path)
    etc_systemd_system = os.path.join("/", "etc", "systemd", "system")
    unit_files = get_unit_files(aksara_dir)
    for unit_file in unit_files:
        exec_cmd(f'sudo rm {etc_systemd_system}/{"".join(unit_file)}')
    exec_cmd("sudo systemctl daemon-reload")


def get_unit_files(aksara_path):
    aksara_name = get_aksara_name(aksara_path)
    unit_files = [
        [aksara_name, ".target"],
        [aksara_name + "-workers", ".target"],
        [aksara_name + "-web", ".target"],
        [aksara_name + "-redis", ".target"],
        [aksara_name + "-logica-default-worker@", ".service"],
        [aksara_name + "-logica-short-worker@", ".service"],
        [aksara_name + "-logica-long-worker@", ".service"],
        [aksara_name + "-logica-schedule", ".service"],
        [aksara_name + "-logica-web", ".service"],
        [aksara_name + "-node-socketio", ".service"],
        [aksara_name + "-redis-cache", ".service"],
        [aksara_name + "-redis-queue", ".service"],
        [aksara_name + "-redis-socketio", ".service"],
    ]
    return unit_files
