# Generated manually to fix duplicate key constraint issue

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('facebook_ads', '0002_alter_facebookadaccount_options_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='facebookcampaign',
            unique_together=set(),
        ),
    ] 