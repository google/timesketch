# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sketch', '0006_auto_20140911_1427'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sketch',
            name='acl_public',
        ),
        migrations.RemoveField(
            model_name='timeline',
            name='acl_public',
        ),
    ]
