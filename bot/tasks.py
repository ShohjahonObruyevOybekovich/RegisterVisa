import logging
from datetime import datetime, date

from celery import shared_task

from account.models import CustomUser

logging.basicConfig(level=logging.INFO)

@shared_task
def check_daily_tasks():

    check_user =


@shared_task
def check_today_tasks():
    today = date.today()
    tasks = Task.objects.filter(status="SOON", date_of_expired__date=today)

    for task in tasks:
        task.status = "ONGOING"
        task.save()
        logging.info(f"Task {task.id} status changed to ONGOING for today.")