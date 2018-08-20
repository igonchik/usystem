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
            # TODO: FOR DEBUG
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
            websock = subprocess.Popen(['python3.5', os.path.join(websockify_dir, 'websockify', 'run'),
                                        '--web', os.path.join(websockify_dir, 'templates', 'websockify'),
                                        '0.0.0.0:{0}'.format(port[2]), '127.0.0.1:{0}'.format(port[1]),
                                        '--verify-client',
                                        '--ssl-version', 'tlsv1_2',
                                        '--cert', certpath,
                                        '--ssl-only',
                                        #'--timeout', '60',
                                        '--cafile', cafile,
                                        '--auth-plugin', 'ClientCertCNAuth',
                                        '--auth-source', ' '.join(rec for rec in users)
                                        ], close_fds=True)
            if not websock.pid or not stun.pid:
                return HttpResponse('Error', status=500)
            host = request.META['HTTP_HOST']
            if ':' in request.META['HTTP_HOST']:
                host = request.META['HTTP_HOST'].split(':')[0]
            time.sleep(2)
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
    groups = Group.objects.filter(user2group__user_id=user.id).values_list('id', flat=True).order_by('id')
    groups_id = list(groups)
    uusers = User.objects.filter(user2group__group__id__in=groups_id) \
        .prefetch_related('user2group_set__group').prefetch_related('programm_set__classname')

    find_connect = Worker.objects.filter(status_id=1).filter(work__startswith='CONNECT_').filter(author='uminion_')
    trying_connect = list()
    if find_connect.exists():
        find_connect = list(find_connect.values_list('work', flat=True))
        user_toconnect = list()
        for rec in find_connect:
            user_toconnect.append(rec[8:])
        trying_connect = list(User.objects.filter(username__in=user_toconnect)
                              .prefetch_related('programm_set__classname'))

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
                rec.user2group_set.all()[0].group.path
            ])
    for rec in trying_connect:
        if not rec.is_master:
            data.append([
                rec.username if not rec.alias else rec.alias,
                '-',
                rec.version,
                rec.programm_set.filter(classname_id=1)[0].name if rec.programm_set.filter(classname_id=1).exists()
                else '',
                rec.register_tstamp.strftime("%d.%m.%Y"),
                rec.lastactivity_tstamp.strftime("%d.%m.%Y %H:%M"),
                rec.isactive(),
                rec.id,
                '.' + str(groups_id[0]) + '.'
            ])
    response.update({'data': data})
    return JsonResponse(response)


@transaction.atomic
def delete_group(request, num):
    user = get_user(__USERNAME)
    gr = Group.objects.get(id=int(num))
    gr_path = Group.objects.filter(path__startswith=gr.path).values_list('id', flat=True)
    exists = User2Group.objects.filter(group_id__in=gr_path, user__is_master=False).exists()
    if exists or gr.author != user.username or gr.alias == 'Ожидают авторизации':
        return HttpResponse('exists')
    User2Group.objects.filter(group_id__in=gr_path).delete()
    Group.objects.filter(path__startswith=gr.path).delete()
    groups = Group.objects.all().order_by('id')
    return render(request, 'GroupSelectorTree.html', {'groups': groups})


@transaction.atomic
def add_group(request, num=0):
    user = get_user(__USERNAME)
    parent = 0
    if 'parent' in request.GET:
        parent = request.GET['parent']
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
            if 'parent_id' in post and post['parent_id'] != '' and \
                    Group.objects.filter(id=int(post['parent_id'])).exists():
                parent = Group.objects.get(id=int(post['parent_id']))
                if parent.alias != 'Ожидают авторизации':
                    gr.path = parent.path + str(gr.id) + '.'
                    gr.parent_id = parent.id
                else:
                    gr.path = '.' + str(gr.id) + '.'
            else:
                gr.path = '.' + str(gr.id) + '.'
            gr.save()
            return render(request, 'GroupSelectorTree.html', {'groups': groups, 'cur_gr': gr.id})
        else:
            return HttpResponse('Error', status=404)
    else:
        return render(request, 'ModifyGroup.html', {'parent': parent}
                                                        if num == 0 else {'rec': Group.objects.get(id=num)})


def about(request, num=0):
    minion = User.objects.get(id=num)
    groups = Group.objects.all().order_by('id')
    u2g = User2Group.objects.filter(user_id=minion.id)
    u2g_list = list(u2g.values_list('id', flat=True))
    if len(u2g_list) == 0:
        return updatecert(request, num)

    # Cert info
    certpath = minion.home_path
    capath = os.path.join(os.path.dirname(os.path.dirname(minion.home_path)), 'cacert.pem')
    crlpath = os.path.join(os.path.dirname(os.path.dirname(minion.home_path)), 'cacrl.pem')

    # TODO: FOR DEBUG
    certpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'client', 'testcerts', 'myvirtwin7.p12')
    capath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'ctaskserver', 'capath', 'cacert.pem')
    crlpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          'client', 'testcerts', 'cacrl.pem')
    x509 = None
    x509valid = False
    if os.path.isfile(certpath) and os.path.isfile(capath) and os.path.isfile(crlpath):
        import OpenSSL.crypto as crypto
        st_cert = open(certpath, 'rt').read()
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, st_cert)
        st_ca = open(capath, 'rt').read()
        st_crl = open(crlpath, 'rt').read()
        crl = crypto.load_crl(crypto.FILETYPE_PEM, st_crl)
        cax509 = crypto.load_certificate(crypto.FILETYPE_PEM, st_ca)
        store = crypto.X509Store()
        store.add_cert(cax509)
        store.add_crl(crl)
        validator = crypto.X509StoreContext(store, x509)
        try:
            validator.verify_certificate()
            x509valid = True
        except:
            x509valid = False

    # VNC ACTIVE CONNECTION
    port_vnc = False
    author_vnc = False

    vncconnection = Worker.objects.filter(username=minion.username).filter(status_id=4). \
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
            if 'group_id' in post and post['group_id'] != '' and \
                    Group.objects.filter(id=int(post['group_id'])).exists():
                uu = User2Group(user_id=minion.id, group_id=int(post['group_id']))
                uu.save()
                User2Group.objects.filter(id__in=u2g_list).delete()

    return render(request, 'AboutUser.html', {'rec': minion, 'groups': groups, 'u2g': u2g, 'port_vnc': port_vnc,
                                              'author_vnc': author_vnc, 'about': True, 'x509': x509,
                                              'x509valid': x509valid})


@transaction.atomic
def updatecert(request, num):
    import OpenSSL.crypto as crypto
    import random
    user = get_user(__USERNAME)
    minion = User.objects.get(id=int(num))
    if request.method == 'POST' and 'cakey' in request.POST:
        key = safe_query(request.POST)
        cakey = key['cakey']
        # Cert info
        capath = os.path.join(os.path.dirname(os.path.dirname(user.home_path)), 'cacert.pem')
        crlpath = os.path.join(os.path.dirname(os.path.dirname(user.home_path)), 'cacrl.pem')
        # TODO: FOR DEBUG
        capath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'ctaskserver', 'capath', 'cacert.pem')
        crlpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               'client', 'testcerts', 'cacrl.pem')
        st_ca = open(capath, 'rt').read()
        ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, st_ca)
        ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, st_ca, passphrase=cakey)
        ca_subj = ca_cert.get_subject()

        ###############
        # Client Cert #
        ###############
        client_key = crypto.PKey()
        client_key.generate_key(crypto.TYPE_RSA, 2048)
        client_cert = crypto.X509()
        client_cert.set_version(2)
        client_cert.set_serial_number(random.randint(50000000, 100000000))
        client_subj = client_cert.get_subject()
        client_subj.commonName = minion.username
        client_subj.O = ca_subj.O

        client_cert.add_extensions([
            crypto.X509Extension("basicConstraints", False, "CA:FALSE"),
            crypto.X509Extension("subjectKeyIdentifier", False, "hash", subject=client_cert),
        ])

        client_cert.add_extensions([
            crypto.X509Extension("authorityKeyIdentifier", False, "keyid:always", issuer=ca_cert),
            crypto.X509Extension("extendedKeyUsage", False, "clientAuth"),
            crypto.X509Extension("keyUsage", False, "digitalSignature"),
        ])

        client_cert.set_issuer(ca_subj)
        client_cert.set_pubkey(client_key)
        client_cert.gmtime_adj_notBefore(0)
        client_cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        client_cert.sign(ca_key, 'sha256')

        # Save certificate
        with open(os.path.join(os.path.dirname(os.path.dirname(user.home_path)), 'p12', minion.username + '.p12'),
                  "wt") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, client_cert))

        # Save private key
        with open(os.path.join(os.path.dirname(os.path.dirname(user.home_path)), 'p12', minion.username + '.p12'),
                  "at") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, client_key))
    return render(request, 'GenX509.html', {})


@transaction.atomic
def genadminpin(request):
    user = get_user(__USERNAME)
    from random import randint
    inbase = list(Worker.objects.filter(username='*', status_id=4, work__startswith='ADMPIN')
                  .values_list('work', flat=True))
    PIN = '{0}{1}{2}{3}{4}{5}'.format(randint(0, 9), randint(0, 9), randint(0, 9), randint(0, 9),
                                      randint(0, 9), randint(0, 9))
    while 'ADMPIN{0}'.format(PIN) in inbase:
        PIN = '{0}{1}{2}{3}{4}{5}'.format(randint(0, 9), randint(0, 9), randint(0, 9), randint(0, 9),
                                          randint(0, 9), randint(0, 9))
    oldpin = Worker.objects.filter(username='*', status_id=4, work__startswith='ADMPIN', author=user.username)
    for rec in oldpin:
        rec.status_id = 6
        rec.save()
    wrk = Worker(username='*', status_id=4, work='ADMPIN{0}'.format(PIN))
    wrk.save()
    return render(request, 'AdminPin.html', {'PIN': PIN})


def get_user(username):
    return User.objects.get(username=username)


@transaction.atomic
def index(request, cur_group=0):
    user = get_user(__USERNAME)
    groups = Group.objects.all().order_by('id')
    response = {'user': user, 'groups': groups, 'current_group_id': cur_group}
    return render(request, 'main.html', response)
