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
import getpass
import socket
from usystem.models import *
import time
from django.http import JsonResponse
from usystem.common_funcs import safe_query


__USERNAME = 'utest'


def get_open_port(worker, count=1):
    ports = list()
    socks = list()
    i = 0
    while i < count:
        allports = list(PortMap.objects.all().values_list('port_num', flat=True))
        for port_num in range(1025, 65534):
            if port_num not in allports:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.bind(("", int(port_num)))
                    s.listen(1)
                    ports.append(s.getsockname()[1])
                    socks.append(s)
                    portmap = PortMap(work_id=worker, port_num=s.getsockname()[1])
                    portmap.save()
                    i += 1
                    break
                except:
                    print('Port {0} all ready in use!'.format(port_num))

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
    import pwd
    user = get_user(__USERNAME)
    minion = User.objects.prefetch_related('user2group_set').get(id=uid)
    new_work = Worker(status_id=1, username=minion.username)
    new_work.save()
    port = get_open_port(new_work.id, 3)
    new_work.work = 'VNCCONNECT{0}'.format(port[0])
    new_work.save()
    time_index = 0
    while time_index < 30:
        time.sleep(1)
        time_index += 1
        if Worker.objects.get(id=new_work.id).status_id == 4:
            group_list = list(minion.user2group_set.all().values_list('group_id', flat=True))
            user_list = list(user.user2group_set.all().filter(group_id__in=group_list).values_list('user_id',
                                                                                                   flat=True))
            users = list(User.objects.filter(id__in=user_list).filter(is_master=True).values_list('username',
                                                                                                  flat=True))
            websockify_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            certpath = os.path.join(user.home_path, 'p12', 'web.pem')
            cafile = os.path.join(user.home_path, 'cacert.pem')
            certpath = os.path.join(websockify_dir, 'ctaskserver', 'testcerts', 'usystem.com.pem')
            cafile = os.path.join(websockify_dir, 'ctaskserver', 'capath', 'cacert.pem')
            conf_path = '{1}stunnel{0}_vnc.conf'.format(pwd.getpwnam(user.username).pw_uid,
                                                                          user.home_path)
            stunnel_conf = "setuid={0}\nclient = yes\n" \
                           "pid={1}stunnel4{0}_vnc.pid\n" \
                           "[vnc]\n" \
                           "verify = 2\n" \
                           "sslVersion = TLSv1\n" \
                           "accept  = 127.0.0.1:{2}\n" \
                           "connect = 127.0.0.1:{3}\n" \
                           "cert = {1}p12/web.pem\n" \
                           "key = {1}p12/web.pem\n" \
                           "CAfile = {1}cacert.pem\n".format(pwd.getpwnam(user.username).pw_uid,
                                                                    user.home_path,
                                                                    port[1], port[0])
            with open(conf_path, 'w') as the_file:
                the_file.write(stunnel_conf)
            stun = subprocess.Popen(['stunnel', conf_path], close_fds=True)
            websock = subprocess.Popen(['python3', os.path.join(websockify_dir, 'websockify', 'run'),
                                        '--web', os.path.join(websockify_dir, 'templates', 'websockify'),
                                        '0.0.0.0:{0}'.format(port[2]), '127.0.0.1:{0}'.format(port[1]),
                                        '--verify-client',
                                        '--ssl-version', 'tlsv1_2',
                                        '--cert', certpath,
                                        '--ssl-only',
                                        '--timeout', '60',
                                        '--cafile', cafile,
                                        '--auth-plugin', 'ClientCertCNAuth',
                                        '--auth-source', ' '.join(rec for rec in users)
                                        ], close_fds=True)
            if not websock.pid or not stun.pid:
                return HttpResponse('Error', status=500)
            host = request.META['HTTP_HOST']
            if ':' in request.META['HTTP_HOST']:
                host = request.META['HTTP_HOST'].split(':')[0]
            return HttpResponse('https://{0}:{1}'.format(host, port[2]))

    new_work.status_id = 5
    new_work.save()
    PortMap.objects.filter(work_id=new_work.id).delete()
    return HttpResponse('Error', status=500)


def minion_json(request):
    """
    header format:
    {
      "name": ..., // string
      "title": ..., // string
      "sortable": ..., // true or false
      "sortDir": ..., // string - "asc" or "desc"
      "size": ..., // int, column width
      "cls": ..., // additional class for header cell
      "clsColumn": ...,  // additional class for related cells in table body
      "format": ... // string define column format for right sorting
    }
    footer format:
    "footer": [
    {
      "name": ..., // string
      "title": ..., // string
      "cls": ..., // additional class for header cell
    },
    """
    user = get_user(__USERNAME)
    groups = Group.objects.filter(user2group__user_id=user.id).values_list('id', flat=True)
    groups_id = list(groups)
    uusers = User.objects.filter(user2group__group__id__in=groups_id) \
        .prefetch_related('user2group_set__group').prefetch_related('programm_set__classname')
    response = dict()
    h = list()
    h.append({'name': 'name', 'title': 'Name', 'sortable': True, 'sortDir': 'asc', 'format': 'string'})
    h.append({'name': 'group', 'title': 'Group', 'sortable': True, 'format': 'string'})
    h.append({'name': 'version', 'title': 'USYS version', 'sortable': True, 'format': 'string'})
    h.append({'name': 'os', 'title': 'OS', 'sortable': True, 'format': 'string', 'clsColumn': 'cls_os'})
    h.append({'name': 'creation', 'title': 'Creation date', 'sortable': True, 'format': 'date',
              'formatMask': 'mm.dd.yyyy'})
    h.append({'name': 'update', 'title': 'Last update', 'sortable': True, 'format': 'date',
              'formatMask': 'mm.dd.yyyy HH:MM'})
    h.append({'name': 'state', 'title': 'State', 'sortable': True, 'clsColumn': 'cls_state'})
    h.append({'name': 'id', 'title': 'ID', 'clsColumn': 'notshow id_col'})
    h.append({'name': 'group_id', 'title': 'GROUP_ID', 'clsColumn': 'notshow groupid_col'})
    f = list()
    for rec in h:
        f.append({'name': rec['name'], 'title': rec['title']})
    response.update({'header': h})
    response.update({'footer': f})
    data = list()
    for rec in uusers:
        if not rec.is_master:
            data.append([
                rec.username if not rec.alias else rec.alias,
                ', '.join(group.group.alias for group in rec.user2group_set.all()),
                rec.version,
                rec.programm_set.filter(classname_id=1)[0].name if rec.programm_set.filter(classname_id=1).exists()
                else '',
                rec.register_tstamp.strftime("%d.%m.%Y"),
                rec.lastactivity_tstamp.strftime("%d.%m.%Y %H:%M"),
                rec.isactive(),
                rec.id,
                rec.user2group_set.all()[0].group.id
            ])
    response.update({'data': data})
    return JsonResponse(response)


@transaction.atomic
def delete_group(request, num):
    user = get_user(__USERNAME)
    gr = Group.objects.get(id=int(num))
    exists = User2Group.objects.filter(group=gr, user__is_master=False).exists()
    if exists or gr.author != user.username or gr.alias == 'Ожидают авторизации':
        return HttpResponse('exists')
    User2Group.objects.filter(group=gr).delete()
    gr.delete()
    return HttpResponse('OK')


@transaction.atomic
def add_group(request, num=0):
    user = get_user(__USERNAME)
    if request.method == 'POST':
        post = safe_query(request.POST)
        groups = Group.objects.all().order_by('id')
        if 'grname' in post and post['grname'] != '' and post['grname'] != 'Ожидают авторизации':
            if 'grid' in post and post['grid'] != '':
                gr = Group.objects.get(id=int(post['grid']))
            else:
                gr = Group()
            gr.alias = post['grname']
            gr.save()
            if not ('grid' in post and post['grid'] != ''):
                u2g = User2Group(user_id=user.id, group=gr)
                u2g.save()
            return render(request, 'groupselector.html', {'groups': groups, 'cur_gr': gr.id})
        else:
            return HttpResponse('Error', status=404)
    else:
        return render(request, 'ModifyGroup.html', dict() if num == 0 else {'rec': Group.objects.get(id=num)})


def about(request, num=0):
    minion = User.objects.get(id=num)
    groups = Group.objects.all().order_by('id')
    u2g = User2Group.objects.filter(user_id=minion.id)

    # VNC ACTIVE CONNECTION
    port_vnc = False
    author_vnc = False
    vncconnection = Worker.objects.filter(username=minion.username).filter(status_id=4).\
        filter(work__startswith='VNCCONNECT').order_by('id')
    if vncconnection.exists():
        vncconnection = vncconnection.last()
        author_vnc = User.objects.get(username=vncconnection.author)
        try:
            port_vnc = PortMap.objects.filter(work_id=vncconnection.id).order_by('id').last().port_num
            host = request.META['HTTP_HOST']
            if ':' in request.META['HTTP_HOST']:
                host = request.META['HTTP_HOST'].split(':')[0]
            port_vnc = 'https://{0}:{1}'.format(host, port_vnc)
        except:
            pass
    if request.method == 'POST':
        post = safe_query(request.POST)
        if 'grname' in post and post['grname'] != '':
            minion.alias = post['grname']
            minion.save()
    return render(request, 'AboutUser.html', {'rec': minion, 'groups': groups, 'u2g': u2g, 'port_vnc': port_vnc,
                                              'author_vnc': author_vnc})


def get_user(username):
    return User.objects.get(username=username)


@transaction.atomic
def index(request, cur_group=0):
    user = get_user(__USERNAME)
    groups = Group.objects.all().order_by('id')
    response = {'user': user, 'groups': groups, 'current_group_id': cur_group}
    return render(request, 'main.html', response)
