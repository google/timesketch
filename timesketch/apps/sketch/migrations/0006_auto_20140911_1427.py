# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sketch', '0005_auto_20140909_1004'),
    ]

    operations = [
        migrations.RenameField(
            model_name='accesscontrolentry',
            old_name='delete',
            new_name='permission_delete',
        ),
        migrations.RenameField(
            model_name='accesscontrolentry',
            old_name='read',
            new_name='permission_read',
        ),
        migrations.RenameField(
            model_name='accesscontrolentry',
            old_name='write',
            new_name='permission_write',
        ),
    ]
