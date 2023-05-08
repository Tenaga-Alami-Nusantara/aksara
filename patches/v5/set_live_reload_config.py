from aksara.config.common_site_config import update_config


def execute(aksara_path):
    update_config({"live_reload": True}, aksara_path)
