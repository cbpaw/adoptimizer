# Generated migration for optimization periodic task

from django.db import migrations


def create_optimization_task(apps, schema_editor):
    """Create periodic task for running campaign optimization checks"""
    from django_celery_beat.models import MINUTES

    IntervalSchedule = apps.get_model("django_celery_beat", "IntervalSchedule")
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")

    # Create schedule: every 20 minutes
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=20,
        period=MINUTES,
    )

    # Create periodic task
    PeriodicTask.objects.get_or_create(
        name="run-campaign-optimization-checks",
        defaults={
            "task": "apps.facebook_ads.tasks.run_campaign_optimization_check",
            "interval": schedule,
            "expire_seconds": 1200,  # 20 minutes - cancel if it hasn't started
            "enabled": True,
        }
    )


def delete_optimization_task(apps, schema_editor):
    """Remove the optimization periodic task"""
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(name="run-campaign-optimization-checks").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("facebook_ads", "0006_dailyperiod_optimizationstrategy_and_more"),
        ("django_celery_beat", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_optimization_task, reverse_code=delete_optimization_task)
    ]
