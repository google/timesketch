# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sketch', '0002_auto_20140903_2301'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collaborator',
            name='user',
        ),
        migrations.RemoveField(
            model_name='sketch',
            name='collaborators',
        ),
        migrations.RemoveField(
            model_name='timeline',
            name='collaborators',
        ),
        migrations.DeleteModel(
            name='Collaborator',
        ),
    ]
