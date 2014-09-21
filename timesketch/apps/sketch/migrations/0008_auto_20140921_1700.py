# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sketch', '0007_auto_20140911_1434'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accesscontrolentry',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='accesscontrolentry',
            name='user',
        ),
        migrations.DeleteModel(
            name='AccessControlEntry',
        ),
    ]
