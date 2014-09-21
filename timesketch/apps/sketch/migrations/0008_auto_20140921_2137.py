# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sketch', '0007_auto_20140911_1434'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sketch',
            old_name='owner',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='timeline',
            old_name='owner',
            new_name='user',
        ),
    ]
