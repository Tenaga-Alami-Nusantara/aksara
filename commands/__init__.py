# imports - third party imports
import click

# imports - module imports
from aksara.utils.cli import (
    MultiCommandGroup,
    print_bench_version,
    use_experimental_feature,
    setup_verbosity,
)


@click.group(cls=MultiCommandGroup)
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    callback=print_bench_version,
    expose_value=False,
)
@click.option(
    "--use-feature",
    is_eager=True,
    callback=use_experimental_feature,
    expose_value=False,
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    callback=setup_verbosity,
    expose_value=False,
)
def aksara_command(aksara_path="."):
    import aksara

    aksara.set_logica_version(aksara_path=aksara_path)


from aksara.commands.make import (
    drop,
    exclude_app_for_update,
    get_app,
    include_app_for_update,
    init,
    new_app,
    pip,
    remove_app,
)

aksara_command.add_command(init)
aksara_command.add_command(drop)
aksara_command.add_command(get_app)
aksara_command.add_command(new_app)
aksara_command.add_command(remove_app)
aksara_command.add_command(exclude_app_for_update)
aksara_command.add_command(include_app_for_update)
aksara_command.add_command(pip)


from aksara.commands.update import (
    retry_upgrade,
    switch_to_branch,
    switch_to_develop,
    update,
)

aksara_command.add_command(update)
aksara_command.add_command(retry_upgrade)
aksara_command.add_command(switch_to_branch)
aksara_command.add_command(switch_to_develop)


from aksara.commands.utils import (
    backup_all_sites,
    bench_src,
    disable_production,
    download_translations,
    find_benches,
    migrate_env,
    renew_lets_encrypt,
    restart,
    set_mariadb_host,
    set_nginx_port,
    set_redis_cache_host,
    set_redis_queue_host,
    set_redis_socketio_host,
    set_ssl_certificate,
    set_ssl_certificate_key,
    set_url_root,
    start,
)

aksara_command.add_command(start)
aksara_command.add_command(restart)
aksara_command.add_command(set_nginx_port)
aksara_command.add_command(set_ssl_certificate)
aksara_command.add_command(set_ssl_certificate_key)
aksara_command.add_command(set_url_root)
aksara_command.add_command(set_mariadb_host)
aksara_command.add_command(set_redis_cache_host)
aksara_command.add_command(set_redis_queue_host)
aksara_command.add_command(set_redis_socketio_host)
aksara_command.add_command(download_translations)
aksara_command.add_command(backup_all_sites)
aksara_command.add_command(renew_lets_encrypt)
aksara_command.add_command(disable_production)
aksara_command.add_command(bench_src)
aksara_command.add_command(find_benches)
aksara_command.add_command(migrate_env)

from aksara.commands.setup import setup

aksara_command.add_command(setup)


from aksara.commands.config import config

aksara_command.add_command(config)

from aksara.commands.git import remote_reset_url, remote_set_url, remote_urls

aksara_command.add_command(remote_set_url)
aksara_command.add_command(remote_reset_url)
aksara_command.add_command(remote_urls)

from aksara.commands.install import install

aksara_command.add_command(install)
