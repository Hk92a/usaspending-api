# Generated by Django 2.2.23 on 2021-08-05 17:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('awards', '0083_auto_20210722_1348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactionfabs',
            name='cfda_number',
            field=models.TextField(blank=True, db_index=True, null=True),
        ),
    ]
