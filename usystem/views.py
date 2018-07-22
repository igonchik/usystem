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
import os
import socket
from usystem.models import *
import time

USERNAME = 'ds-goncharov'


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port


def start_stunnel(admin, remote_ip, remote_port):
    try:
        pid = subprocess.check_output(["pgrep", "-u", "ds-goncharov", "stunnel"]).strip()
    except:
        pid = None
    if not pid:
        from usystem.pystunnel import Stunnel
        port = get_open_port()
        data = ''
        stunnel = Stunnel("/tmp/usystem/{0}/stunnel.conf".format(USERNAME), data)
        rc = stunnel.start()
        if stunnel.check() == 0:
            print("stunnel is running with pid", stunnel.getpid())
        else:
            raise RuntimeError("Stunnel is not running")
        os.remove("/tmp/usystem/{0}/stunnel.conf".format(USERNAME))
        rc = stunnel.stop()
        print("stunnel stopped with rc", rc)


def connectvnc(request, uid):
    def start_web():
        current_ip = socket.gethostbyname(socket.gethostname())
        port_num = get_open_port()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        opts = ['run', '--web', os.path.join(base_dir, 'templates', 'websockify'),
                current_ip, port_num, remote_ip, remote_port, '--ssl', '-version',
                'tlsv1_2', '--cert', '/home/{0}/p12/web.p12'.format(USERNAME),
                '--ssl', '-only', '--cafile', '/home/{0}/cacert.pem'.format(USERNAME)]
        import websockify
        websockify.websocketproxy.websockify_init(opts)

    minion = User.objects.get(uid=uid)
    remote_ip = minion.current_ip
    new_work = Worker('vncconnect {0}'.format(uid), status_id=1)
    new_work.save()
    time_index = 0
    remote_start = False
    while time_index < 6 or not remote_start:
        time.sleep(1)
        time_index += 1
        if Worker.objects.get(id=new_work.id).status_id > 1:
            remote_start = True

    if remote_start:
        remote_port = 5900
        from multiprocessing import Process
        pool = Process(target=start_web)
        pool.start()
        time.sleep(1)
        return redirect('https://connect.{0}:{1}'.format(config.DOMAIN_NAME, remote_port))
    return render(request, 'errors/vnc_error.html', {'minion': minion})

@transaction.atomic
def material(request, num=0):
    pass

@transaction.atomic
def zakaz(request, num=0):
    pass

@transaction.atomic
def print_saw(request, num=0):
    pass

@transaction.atomic
def update_saw(request):
    pass

@transaction.atomic
def index(request):

    return render(request, 'main.html', {})