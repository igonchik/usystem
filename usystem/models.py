# -*- coding: utf-8 -*-

from django.db import models
from datetime import datetime
from django.utils.timezone import now


class Group(models.Model):
    alias = models.CharField(max_length=100, unique=True, null=False)
    uid = models.TextField(unique=True, null=False)
    num_stars = models.IntegerField()
    create_tstamp = models.DateTimeField(default=now)

    class Meta:
        db_table = '"pubview"."usystem_group_view"'


class User(models.Model):
    username = models.CharField(max_length=100, unique=True, null=False)
    email = models.EmailField(unique=True)
    uid = models.TextField(unique=True, null=False)
    register_tstamp = models.DateTimeField(default=now)
    lastactivity_tstamp = models.DateTimeField(default=now)
    email_confirmed = models.BooleanField(default='f')
    is_master = models.BooleanField(default='f')
    expirepwd_tstamp = models.DateTimeField()
    expirecert_tstamp = models.DateTimeField()
    home_path = models.TextField(unique=True, null=False)
    public_key = models.TextField(unique=True, null=False)
    installation_tstamp = models.DateTimeField()
    current_ip = models.GenericIPAddressField()

    class Meta:
        db_table = '"pubview"."usystem_user_view"'


class User2Group(models.Model):
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)

    class Meta:
        db_table = '"pubview"."usystem_user2group"'


class Work_Status(models.Model):
    name = models.TextField(unique=True, null=False)


class Worker(models.Model):
    author = models.CharField(max_length=100, unique=True, null=False)
    create_tstamp = models.DateTimeField(default=now)
    status = models.ForeignKey(Work_Status)
    comment = models.TextField(null=False)

    class Meta:
        db_table = '"pubview"."usystem_worker_view"'


class Log_Action(models.Model):
    name = models.TextField(unique=True, null=False)


class Log(models.Model):
    author = models.CharField(max_length=100, unique=True, null=False)
    create_tstamp = models.DateTimeField(default=now)
    action = models.ForeignKey(Work_Status)
    comment = models.TextField(null=False)

    class Meta:
        db_table = '"pubview"."usystem_log_view"'

