# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-11-17 03:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0008_auto_20161117_1419'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='related',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='reports.Report'),
        ),
    ]