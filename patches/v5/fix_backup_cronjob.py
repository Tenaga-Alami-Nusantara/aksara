from aksara.config.common_site_config import get_config
from crontab import CronTab


def execute(aksara_path):
    """
    This patch fixes a cron job that would backup sites every minute per 6 hours
    """

    user = get_config(aksara_path=aksara_path).get("logica_user")
    user_crontab = CronTab(user=user)

    for job in user_crontab.find_comment("bench auto backups set for every 6 hours"):
        job.every(6).hours()
        user_crontab.write()
