# -*- coding: utf-8 -*-
# comment

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
    author = models.CharField(max_length=100, null=False)
    create_tstamp = models.DateTimeField(default=now)
    parent_id = models.IntegerField(null=True)
    path = models.TextField(null=False)

    class Meta:
        db_table = '"pubview"."usystem_group_view"'

    def __unicode__(self):
        return self.alias


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
    policy = models.IntegerField(default=0)

    def isactive(self):
        try:
            delta = datetime.now().astimezone(timezone.utc) - self.lastactivity_tstamp.astimezone(timezone.utc)
        except:
            delta = datetime.now() - self.lastactivity_tstamp
        if (delta.days == -1 and delta.seconds > 86399-30) or (delta.days == 0 and delta.seconds < 30):
            return self.policy + 1
        else:
            return 0

    def uname(self):
        if self.alias:
            return self.alias
        return self.username

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


class PortMap(models.Model):
    work = models.ForeignKey(Worker, on_delete=CASCADE)
    port_num = models.IntegerField(null=False)

    class Meta:
        db_table = '"pubview"."usystem_portmap_view"'


class Log_Action(models.Model):
    name = models.TextField(unique=True, null=False)


class Log(models.Model):
    author = models.CharField(max_length=100, unique=True, null=False)
    create_tstamp = models.DateTimeField(default=now)
    action = models.ForeignKey(Work_Status, on_delete=CASCADE)
    comment = models.TextField(null=False)

    class Meta:
        db_table = '"pubview"."usystem_log_view"'


class WMIDriveType(models.Model):
    """
            DRIVE_TYPES = {
            0: "Unknown",
            1: "No Root Directory",
            2: "Removable Disk",
            3: "Local Disk",
            4: "Network Drive",
            5: "Compact Disc",
            6: "RAM Disk"
        }
    """
    caption = models.TextField(null=False)

    class Meta:
        db_table = 'usystem_wmidrivetype'


class WMIInfo(models.Model):
    agent = models.ForeignKey(User, on_delete=CASCADE)
    osname = models.TextField(null=False)
    osversion = models.CharField(null=False, max_length=128)
    proc_info = models.CharField(null=False, max_length=256)
    free_ram = models.IntegerField(null=False, default=0)
    system_ram = models.IntegerField(null=False, default=0)
    domain = models.CharField(null=False, max_length=256)
    name = models.CharField(null=False, max_length=256)
    username = models.CharField(null=False, max_length=256)
    cpu_load = models.FloatField(null=False)

    class Meta:
        db_table = '"pubview"."usystem_wmiinfo_view"'


class WMIDrive(models.Model):
    wmi = models.ForeignKey(WMIInfo, on_delete=CASCADE)
    caption = models.TextField(null=False)
    drivetype = models.ForeignKey(WMIDriveType, on_delete=CASCADE)
    free = models.TextField(null=False)
    size = models.TextField(null=False)

    class Meta:
        db_table = '"pubview"."usystem_wmidrive_view"'


class WMINetDrive(models.Model):
    wmi = models.ForeignKey(WMIInfo, on_delete=CASCADE)
    caption = models.TextField(null=False)
    macaddr = models.CharField(null=False, max_length=128)

    class Meta:
        db_table = '"pubview"."usystem_wminetdrive_view"'


class WMIIPInfo(models.Model):
    netdrive = models.ForeignKey(WMINetDrive, on_delete=CASCADE)
    ipaddr = models.GenericIPAddressField()
    macaddr = models.CharField(null=False, max_length=128)

    class Meta:
        db_table = '"pubview"."usystem_wmiipinfo_view"'


class WMIGpuInfo(models.Model):
    wmi = models.ForeignKey(WMIInfo, on_delete=CASCADE)
    caption = models.TextField(null=False)

    class Meta:
        db_table = '"pubview"."usystem_wmigpuinfo_view"'

