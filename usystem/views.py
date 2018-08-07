# -*- coding: utf-8 -*-
from __future__ import division
from django.shortcuts import render, render_to_response, redirect
from usystem.models import models
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.db.models import Q
from operator import and_
from functools import wraps
from django.views.decorators.cache import patch_cache_control
from django.db import transaction
from usystem_master import config
from usystem.forms import *
import base64
from django.db.models import Max, F
import subprocess
from django.core.mail import send_mail
from copy import deepcopy
from django.db.models import Count
from django.db import connection
import os, getpass
import socket
from usystem.models import *
import time
from django.http import JsonResponse


__USERNAME = 'utest'

def get_open_port(count=1):
    ports = list()
    socks = list()
    for i in range(0, count):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.listen(1)
        ports.append(s.getsockname()[1])
        socks.append(s)
    for s in socks:
        s.close()
    return ports


def start_stunnel(remote_ip, remote_port):
    from usystem.pystunnel import Stunnel
    if not os.path.isdir("/tmp/usystem/{0}/".format(getpass.getuser())):
        os.mkdir("/tmp/usystem/{0}/".format(getpass.getuser()))
    if not os.path.isdir("/var/log/usystem/{0}/".format(getpass.getuser())):
        os.mkdir("/var/log/usystem/{0}/".format(getpass.getuser()))
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    local_port = s.getsockname()[1]
    data = 'output = /var/log/usystem/{0}/stunnel1.log\n\
    [vnc]\n\
    verify = 2\n\
    sslVersion = TLSv1\n\
    accept  = 127.0.0.1:{1}\n\
    connect = {2}:{3}\n\
    cert = /var/{0}/p12/web.pem\n\
    key = /var/{0}/p12/web.pem\n\
    CAfile = /var/{0}/cacert.pem'.format(getpass.getuser(), local_port, remote_ip, remote_port)
    stunnel = Stunnel("/tmp/usystem/{0}/stunnel.conf".format(getpass.getuser()), data)
    s.close()
    rc = stunnel.start()
    if rc.pid:
        print("stunnel is running with pid", rc.pid)
    else:
        raise RuntimeError("Stunnel is not running")
    time.sleep(1)
    os.remove("/tmp/usystem/{0}/stunnel.conf".format(getpass.getuser()))
    return local_port


def connectvnc(request, uid):
    def start_web():
        class RecordWeb(object):
            __slots__ = "record", "timeout", "cert", "ssl_only", "verify_client", "cafile", "ssl_version",\
            "unix_target", "web", "auth_plugin", "auth_source", "ssl_options", "listen_port", "remote", \
            "log_file", "syslog", "verbose", "token_source", "token_plugin", "host_token", "web_auth", \
            "target_cfg", "wrap_cmd", "inetd", "listen_host", "listen_port", "wrap_cmd", "target_host",\
                        "target_port", "local", "libserver"
        local_port = start_stunnel(remote_ip, remote_port)
        local_ip = socket.gethostbyname(socket.gethostname())
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        opts = RecordWeb()
        opts.inetd = None
        opts.libserver = None
        opts.unix_target = None
        opts.listen_host = None
        opts.listen_port = None
        opts.wrap_cmd = None
        opts.target_host = None
        opts.target_port = None
        opts.log_file = None
        opts.syslog = None
        opts.verbose = None
        opts.token_source = None
        opts.token_plugin = None
        opts.host_token = None
        opts.web_auth = None
        opts.target_cfg = None
        opts.wrap_cmd = None
        opts.web = os.path.join(base_dir, 'templates', 'websockify')
        opts.local = '{0}:{1}'.format(local_ip, local_port)
        opts.ssl_version ='tlsv1_2'
        opts.verify_client = True
        opts.ssl_options = None
        opts.cert = '/var/{0}/p12/web.pem'.format(getpass.getuser())
        opts.timeout = 10
        opts.ssl_only = True
        opts.cafile ='/var/{0}/cacert.pem'.format(getpass.getuser())
        opts.auth_plugin = 'ClientCertCNAuth'
        opts.auth_source = 'test1'
        opts.remote = '{0}:{1}'.format(remote_ip, remote_port)
        import websockify
        s.close()
        websockify.websocketproxy.websockify_init(opts)

    minion = User.objects.get(uid=uid)
    remote_ip = minion.current_ip
    new_work = Worker(work='vncconnect {0}'.format(uid), status_id=1)
    new_work.save()
    time_index = 0
    remote_start = False
    while time_index < 6 and not remote_start:
        time.sleep(1)
        time_index += 1
        if Worker.objects.get(id=new_work.id).status_id > 1:
            remote_start = True

    if remote_start or 1==1:
        remote_port = 5900
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        s.listen(1)
        port_num = s.getsockname()[1]
        from multiprocessing import Process
        pool = Process(target=start_web)
        pool.start()
        time.sleep(1)
        return redirect('https://connect.{0}:{1}'.format(config.DOMAIN_NAME, port_num))
    return render(request, 'errors/vnc_error.html', {'minion': minion})


@transaction.atomic
def _control(user, num=0):
    if num == 0:
        groups = Group.objects.filter(user2group__user_id=user.id).values_list('id', flat=True)
    else:
        groups = Group.objects.filter(id=num).values_list('id', flat=True)
    groups_id = list(groups)
    uusers = User.objects.filter(user2group__group__id__in=groups_id)\
        .prefetch_related('user2group_set__group').prefetch_related('programm_set__classname')
    response = {'minion': [], 'master': []}
    for rec in uusers:
        if rec.is_master:
            response['master'].append(rec)
        else:
            response['minion'].append(rec)
    return response


@transaction.atomic
def control(request, cur_group=0):
    user = get_user(__USERNAME)
    groups = Group.objects.filter(user2group__user_id=user.id)
    response = _control(user, cur_group)
    filtered = False
    search = ''
    group = 0
    if 'filtered' in request.GET:
        filtered = True
    if 'search' in request.GET:
        search = request.GET['search']
    if 'group' in request.GET:
        group = int(request.GET['group'])
    response.update({'user': user, 'groups': groups, 'current_group_id': cur_group, 'filtered': filtered,
                     'search': search, 'group': group})
    return render(request, 'ajax_miniontable.html', response)


def get_user(username):
    return User.objects.get(username=username)


@transaction.atomic
def index(request, cur_group=0):
    user = get_user(__USERNAME)
    groups = Group.objects.filter(user2group__user_id=user.id)
    response = _control(user, cur_group)
    response.update({'user': user, 'groups': groups, 'current_group_id': cur_group})
    return render(request, 'main.html', response)