# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-19 02:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('awards', '0026_auto_20180313_0418'),
    ]

    operations = [
        migrations.AddField(
            model_name='award',
            name='total_loan_value',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='The total of the face_value_loan_guarantee from associated transactions', max_digits=23, null=True),
        ),
        migrations.AddField(
            model_name='transactionnormalized',
            name='face_value_loan_guarantee',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='The face_value_loan_guarantee for loan type transactions', max_digits=23, null=True),
        ),
    ]