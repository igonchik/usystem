# -*- coding: utf-8 -*-

from django.db import models
from datetime import datetime
from datetime import timezone
from django.utils.timezone import now
from django.db.models.deletion import CASCADE, SET_DEFAULT, SET_NULL


class ProgrammClass(models.Model):
    name = models.CharField(max_length=100, null=False)

    class Meta:
        db_table = 'usystem_programm_class'


class Group(models.Model):
    alias = models.CharField(max_length=100, null=False)
    uid = models.TextField(null=False)
    create_tstamp = models.DateTimeField(default=now)

    class Meta:
        db_table = '"pubview"."usystem_group_view"'


class User(models.Model):
    username = models.CharField(max_length=100, unique=True, null=False)
    alias = models.TextField()
    email = models.EmailField()
    register_tstamp = models.DateTimeField(default=now)
    lastactivity_tstamp = models.DateTimeField(default=now)
    email_confirmed = models.BooleanField(default='f')
    is_master = models.BooleanField(default='f')
    expirepwd_tstamp = models.DateTimeField()
    expirecert_tstamp = models.DateTimeField()
    home_path = models.TextField(null=False)
    version = models.CharField(max_length=100, null=False, default='0.0')
    current_ip = models.GenericIPAddressField()

    def isactive(self):
        delta = datetime.now().astimezone(timezone.utc) - self.lastactivity_tstamp.astimezone(timezone.utc)
        return (delta.days == -1 and delta.seconds > 86399-30) or (delta.days == 0 and delta.seconds < 30)

    class Meta:
        db_table = '"pubview"."usystem_user_view"'


class Programm(models.Model):
    name = models.CharField(max_length=100, null=False)
    username = models.ForeignKey(User, to_field='username', on_delete=CASCADE, db_column='username')
    classname = models.ForeignKey(ProgrammClass, on_delete=CASCADE)

    class Meta:
        db_table = '"pubview"."usystem_programm_view"'


class User2Group(models.Model):
    user = models.ForeignKey(User, on_delete=CASCADE)
    group = models.ForeignKey(Group, on_delete=CASCADE)

    class Meta:
        db_table = '"pubview"."usystem_user2group_view"'


class Work_Status(models.Model):
    name = models.TextField(unique=True, null=False)


class Worker(models.Model):
    author = models.CharField(max_length=100, null=False)
    username = models.CharField(max_length=100, null=False)
    create_tstamp = models.DateTimeField(default=now)
    get_tstamp = models.DateTimeField()
    status = models.ForeignKey(Work_Status, on_delete=CASCADE)
    work = models.TextField(null=False)

    class Meta:
        db_table = '"pubview"."usystem_worker_view"'


class Log_Action(models.Model):
    name = models.TextField(unique=True, null=False)


class Log(models.Model):
    author = models.CharField(max_length=100, unique=True, null=False)
    create_tstamp = models.DateTimeField(default=now)
    action = models.ForeignKey(Work_Status, on_delete=CASCADE)
    comment = models.TextField(null=False)

    class Meta:
        db_table = '"pubview"."usystem_log_view"'

