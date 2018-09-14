# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-08-22 18:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('references', '0019_update_program_activity_allow_null_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='legalentity',
            name='parent_recipient_name',
            field=models.TextField(blank=True, null=True, verbose_name='Parent Recipient Name'),
        ),
    ]