from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json
from loguru import logger
from notes.tasks import send_reminder_email


def schedule_reminder(note):

    """
    Description:
        Schedules a periodic task using Django Celery Beat to send a reminder email for a specific note.
        The function converts the note's reminder time into a cron schedule and uses `CrontabSchedule` 
        and `PeriodicTask` models to create or update the task. The task is set to send a reminder email
        to the note's associated user at the specified time.
    Parameters:
        note (Note): The note object containing reminder details, including reminder time and user information.
    Process:
        1. The reminder time is extracted from the note and converted into cron schedule format (minute, hour, day, month).
        2. A `CrontabSchedule` is created or reused if it matches the calculated cron schedule.
        3. A `PeriodicTask` is created or updated with the schedule and task details, which includes 
           the task `send_reminder_email` and the note's title and user email as arguments.
    Tasks:
        - The task `notes.tasks.send_reminder_email` will be triggered at the scheduled time.
    Logging:
        - Logs the scheduling process, including creation or reuse of `CrontabSchedule` and `PeriodicTask`.
        - Logs errors if the scheduling fails.
    Exception Handling:
        - If any error occurs during the scheduling process, the exception is logged, 
          and no task is scheduled.
    Example Usage:
        schedule_reminder(note)  # Pass a note instance with valid reminder and user data.
    Returns:
        None
    """
    try:
        # Convert datetime to cron format
        reminder_time = note.reminder
        cron_minute = reminder_time.minute
        cron_hour = reminder_time.hour
        cron_day = reminder_time.day
        cron_month = reminder_time.month
        cron_day_of_week = reminder_time.weekday()

        logger.info(f'Scheduling reminder for note ID {note.id} at {reminder_time}.')

        # Create a schedule
        schedule, created = CrontabSchedule.objects.get_or_create(
            minute=cron_minute,
            hour=cron_hour,
            day_of_month=cron_day,
            month_of_year=cron_month,
            day_of_week="*",
        )
        if created:
            logger.info(f'Created new CrontabSchedule: {schedule}.')
        else:
            logger.info(f'Using existing CrontabSchedule: {schedule}.')

        # Create or update the periodic task
        periodic_task, created = PeriodicTask.objects.update_or_create(
            name=f"send_reminder_email_{note.id}",
            defaults={
                'crontab': schedule,
                'task': 'notes.tasks.send_reminder_email',
                'args': json.dumps([note.title,note.user.email]),
            }
        )
        if created:
            logger.info(f'Created new PeriodicTask: {periodic_task}.')
        else:
            logger.info(f'Updated existing PeriodicTask: {periodic_task}.')

    except Exception as e:
        logger.error(f'Error scheduling reminder for note ID {note.id}: {e}')