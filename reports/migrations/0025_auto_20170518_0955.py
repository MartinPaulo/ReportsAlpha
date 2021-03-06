# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-17 23:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0024_auto_20170503_1440'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cloudprojectfaculty',
            old_name='faculty_abbreviation',
            new_name='allocated_faculty',
        ),
        migrations.RemoveField(
            model_name='cloudprojectfaculty',
            name='faculties',
        ),
        migrations.AddField(
            model_name='cloudprojectfaculty',
            name='chief_investigator',
            field=models.CharField(blank=True, max_length=75, null=True),
        ),
        migrations.AddField(
            model_name='cloudprojectfaculty',
            name='for_code',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
    ]
