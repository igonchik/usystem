# -*- coding: utf-8 -*-
from __future__ import division
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError
from django.db import transaction
import subprocess
import os
import socket
from usystem.models import *
import time
from django.http import JsonResponse
from usystem.common_funcs import safe_query
from filemanager import FileManager
import platform
from django.forms.models import model_to_dict
from django.shortcuts import redirect


def file_view(request, path):
    user = get_user(request.META['HTTP_X_FORWARDED_USER'])
    #fm = FileManager(os.path.join(user.home_path, 'share'))
    fm = FileManager('C:\\Users\\d.goncharov.ACC\\servershare')
    return fm.render(request, path)


def audit_json(request, uid):
    def getwmi(agent_id):
        _res = {}
        try:
            wmiinfo = WMIInfo.objects.get(agent_id=agent_id)
            wmidrive = WMIDrive.objects.select_related('drivetype').filter(wmi_id=wmiinfo.id)
            wmiipinfo = WMIIPInfo.objects.select_related('netdrive').filter(netdrive__wmi_id=wmiinfo.id)
            wmigpu = WMIGpuInfo.objects.filter(wmi_id=wmiinfo.id)
            _res.update({'osname': wmiinfo.osname, 'osversion': wmiinfo.osversion, 'proc_info': wmiinfo.proc_info,
                         'freeram': wmiinfo.free_ram, 'sysram': wmiinfo.system_ram, 'domain': wmiinfo.domain,
                         'computername': wmiinfo.name, 'username': wmiinfo.username, 'cpu_load': wmiinfo.cpu_load,
                         })
            _res_d = []
            for rec in wmidrive:
                _res_d.append({'caption': rec.caption, 'free': rec.free, 'size': rec.size,
                               'drivetype': rec.drivetype.caption})

            _res_gpu = []
            for rec in wmigpu:
                _res_gpu.append({'caption': rec.caption})

            _res_net = []
            for rec in wmiipinfo:
                _res_net.append({'caption': rec.netdrive.caption, 'ipaddr': rec.ipaddr, 'macaddr': rec.macaddr})

            _res.update({'drivers': _res_d, 'gpu': _res_gpu, 'netdrive': _res_net})
        except:
            pass
        return JsonResponse(_res)

    minion = User.objects.get(id=uid)
    new_work = Worker(status_id=1, username=minion.username, work='MAINAUDIT')
    new_work.save()
    time_index = 0
    while time_index < 10 and minion.isactive() > 0:
        time.sleep(1)
        time_index += 1
        if Worker.objects.get(id=new_work.id).status_id == 4:
            return getwmi(int(uid))
    new_work.status_id = 5
    new_work.save()
    return getwmi(int(uid))


def set_soft_audit(request, uid):
    minion = User.objects.get(id=uid)
    new_work = Worker(status_id=1, username=minion.username, work='SOFTAUDIT')
    new_work.save()
    return HttpResponse('ok')


def soft_audit(request, uid):
    soft = WMISoft.objects.filter(agent_id=uid)
    _res = list()
    for rec in soft:
        _res.append(model_to_dict(rec))
    return JsonResponse({'softdata': _res})


def main_audit(request, uid):
    def getwmi(agent_id):
        _res = {}
        try:
            wmiinfo = WMIInfo.objects.get(agent_id=agent_id)
            _res.update({'wmiinfo': wmiinfo})
            wmidrive = WMIDrive.objects.select_related('drivetype').filter(wmi_id=wmiinfo.id)
            _res.update({'wmidrive': wmidrive})
            wmiipinfo = WMIIPInfo.objects.select_related('netdrive').filter(netdrive__wmi_id=wmiinfo.id)
            _res.update({'wmiipinfo': wmiipinfo})
            wmigpu = WMIGpuInfo.objects.filter(wmi_id=wmiinfo.id)
            _res.update({'wmigpu': wmigpu})
        except:
            pass
        return _res

    minion = User.objects.get(id=uid)
    new_work = Worker(status_id=1, username=minion.username, work='MAINAUDIT')
    new_work.save()
    time_index = 0
    while time_index < 10 and minion.isactive() > 0:
        time.sleep(1)
        time_index += 1
        if Worker.objects.get(id=new_work.id).status_id == 4:
            return render(request, 'WMIInfo.html', getwmi(uid))
    new_work.status_id = 5
    new_work.save()
    return render(request, 'WMIInfo.html', getwmi(uid))


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


def checktable(request):
    user = get_user(request.META['HTTP_X_FORWARDED_USER'])
    groups = Group.objects.all().order_by('id')
    response = {'user': user, 'groups': groups}
    return render(request, 'CheckTable.html', response)


def sendfile(request):
    import urllib.parse
    def file_transfer_client(filename, host, port):
        i_size = 0
        m_size = os.path.getsize(filename)
        s = socket.socket()  # Create a socket object
        s.connect((host, port))
        f = open(filename, 'rb')
        print('Sending...')
        line = f.read(1024)
        while line:
            print('Sending... {0} from {1}'.format(i_size*1024, m_size))
            s.send(line)
            line = f.read(1024)
            i_size += 1
        f.close()
        print("Done Sending")
        s.shutdown(socket.SHUT_WR)  # Close the socket when done
        s.close()
        return 0

    if request.method == 'GET' and 'path' in request.GET and 'filename' in request.GET:
        query = safe_query(request.GET)
        uids = query['path'].split(',')
        filename = urllib.parse.unquote(query['filename'])
    else:
        return HttpResponse('Error1', status=500)

    if platform.system() != 'Windows':
        import pwd
    uid = int(uids[0])
    user = get_user(request.META['HTTP_X_FORWARDED_USER'])
    minion = User.objects.prefetch_related('user2group_set').get(id=uid)
    new_work = Worker(status_id=1, username=minion.username)
    new_work.save()
    port = get_open_port(new_work.id, 3)

    # For Debug
    if platform.system() == 'Windows':
        hpath = 'C:\\Users\\d.goncharov.ACC\\'
    else:
        hpath = user.home_path

    if platform.system() == 'Windows':
        filename = filename.replace('/', '\\')

    filename = os.path.normpath(hpath + 'share' + filename)

    new_work.work = 'FILEIN{0}:{1}'.format(port[0], filename)
    new_work.save()
    time_index = 0
    while time_index < 30:
        time.sleep(1)
        time_index += 1
        if Worker.objects.get(id=new_work.id).status_id == 4:
            if platform.system() != 'Windows':
                coonfpw_uid = pwd.getpwnam(user.username).pw_uid
            else:
                coonfpw_uid = 'debug'

            conf_path = '{1}stunnel{0}_filein.conf'.format(coonfpw_uid, hpath)
            stunnel_conf = "setuid={0}\nclient = yes\n" \
                           "pid={1}stunnel4{0}_transfer.pid\n" \
                           "[file]\n" \
                           "verify = 2\n" \
                           "sslVersion = TLSv1\n" \
                           "accept  = 127.0.0.1:{2}\n" \
                           "connect = 127.0.0.1:{3}\n" \
                           "cert = {1}p12/web.pem\n" \
                           "key = {1}p12/web.pem\n" \
                           "CAfile = {1}cacert.pem\n".format(coonfpw_uid, hpath, port[1], port[0])
            with open(conf_path, 'w') as the_file:
                the_file.write(stunnel_conf)
            stun = subprocess.Popen(['stunnel', conf_path])
            if not stun.pid:
                new_work.status_id = 5
                new_work.save()
                PortMap.objects.filter(work_id=new_work.id).delete()
                return HttpResponse('Error', status=500)
            try:
                time.sleep(1)
                res = file_transfer_client(filename, '127.0.0.1', port[1])
                # TODO: kill proc
                #kill_proc = ["kill", "`netstat -luntp | grep 'sshd: stun' | grep '127.0.0.1:1091' | awk '{print $7}'"
                #                     "| cut -d '/' -f1`"]
                #subprocess.call(kill_proc)
                if res == 0:
                    return HttpResponse('OK')
                else:
                    return HttpResponse('Error', status=500)
            except:
                new_work.status_id = 5
                new_work.save()
                PortMap.objects.filter(work_id=new_work.id).delete()
                return HttpResponse('Error transfering the file', status=500)
    new_work.status_id = 5
    new_work.save()
    PortMap.objects.filter(work_id=new_work.id).delete()
    return HttpResponse('Error', status=500)


def connectvnc(request, uid):
    if platform.system() != 'Windows':
        import pwd
    user = get_user(request.META['HTTP_X_FORWARDED_USER'])
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
                                                             user.home_path, port[1], port[0])
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
                                        # '--timeout', '60',
                                        '--cafile', cafile,
                                        '--auth-plugin', 'ClientCertCNAuth',
                                        '--auth-source', ' '.join(rec for rec in users)
                                        ], close_fds=True)
            if not websock.pid or not stun.pid:
                new_work.status_id = 5
                new_work.save()
                PortMap.objects.filter(work_id=new_work.id).delete()
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


def removereq(request, num):
    minion = User.objects.get(id=num)
    wrks = Worker.objects.filter(status_id=1).filter(work='CONNECT_{0}'.format(minion.username)) \
        .filter(author='uminion_')
    for rec in wrks:
        rec.status_id = 5
        rec.save()
    return HttpResponse('OK')


def minion_json(request, num=0):
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
    user = get_user(request.META['HTTP_X_FORWARDED_USER'])
    num = int(num)
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
    if num == 1:
        h.append({'name': 'name', 'title': '', 'sortable': False})

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
            if num == 1:
                data.append([
                    '1',
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
            else:
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
    user = get_user(request.META['HTTP_X_FORWARDED_USER'])
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
    user = get_user(request.META['HTTP_X_FORWARDED_USER'])
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
        return render(request, 'ModifyGroup.html',
                      {'parent': parent} if num == 0 else {'rec': Group.objects.get(id=num)})


def about(request, num=0):
    minion = User.objects.get(id=num)
    groups = Group.objects.all().order_by('id')
    u2g = User2Group.objects.filter(user_id=minion.id)
    u2g_list = list(u2g.values_list('id', flat=True))
    if len(u2g_list) == 0:
        return updatecert(request, num)

    # Cert info
    certpath = '{0}p12/{1}.pem'.format(minion.home_path, minion.username)
    capath = os.path.join(os.path.dirname(minion.home_path), 'cacert.pem')
    crlpath = os.path.join(os.path.dirname(minion.home_path), 'cacrl.pem')

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
        st_ca = open(capath, 'rt').read()
        st_crl = open(crlpath, 'rt').read()
        try:
            crl = crypto.load_crl(crypto.FILETYPE_PEM, st_crl)
            x509 = crypto.load_certificate(crypto.FILETYPE_PEM, st_cert)
            cax509 = crypto.load_certificate(crypto.FILETYPE_PEM, st_ca)
            store = crypto.X509Store()
            store.add_cert(cax509)
            store.add_crl(crl)
            validator = crypto.X509StoreContext(store, x509)
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
def removeagent(request, num):
    minion = User.objects.get(id=num)
    user = get_user(request.META['HTTP_X_FORWARDED_USER'])
    if request.method == 'POST':
        post = safe_query(request.POST)
        if 'pin' in post and post['pin'] != '':
            crlexists = ['openssl', 'ca', '-config', '{0}/openssl.cnf'.format(user.home_path),
                         '-revoke', '/{1}/certs/{0}.pem'.format(minion.username, user.home_path),
                         '-batch', '-passin', 'pass:{0}'.format(post['pin'])]
            gencrl = ['openssl', 'ca', '-config', '{0}/openssl.cnf'.format(user.home_path),
                      '-gencrl', '-passin', 'pass:{0}'.format(post['pin']),
                      '-out', '/{0}/cacrl.pem'.format(user.home_path), '-crldays', '1825']
            if os.path.isfile('{1}/certs/{0}.pem'.format(minion.username, user.home_path)):
                try:
                    subprocess.check_output(crlexists)
                except:
                    pass
                subprocess.check_output(gencrl)
            wrk = Worker(username=minion.username, status_id=1, work='CACERTUPDATE/home/usystem/cacert.pem')
            wrk.save()
            wrk = Worker(username=minion.username, status_id=1, work='RCERTUPDATE')
            wrk.save()
            User2Group.objects.filter(user_id=minion.id).delete()
            return HttpResponse('ok')
        return HttpResponseServerError('PASS Phrase is incorrect')
    return HttpResponseServerError('request method is not POST')


@transaction.atomic
def updatecert(request, num):
    minion = User.objects.get(id=num)
    groupset = Group.objects.filter(id__in=User2Group.objects.filter(user_id=
                                                                     minion.id).values_list('group_id', flat=True))
    groups = Group.objects.all().order_by('id')
    user = get_user(request.META['HTTP_X_FORWARDED_USER'])
    if request.method == 'POST':
        post = safe_query(request.POST)
        if 'path' in post and post['path'] != '' and 'pin' in post and post['pin'] != '':
            try:
                path = int(post['path'])
                group = Group.objects.get(id=path)
            except:
                group = None
            if group:
                crlexists = ['openssl', 'ca', '-config', '{0}/openssl.cnf'.format(user.home_path),
                             '-revoke', '/{1}/certs/{0}.pem'.format(minion.username, user.home_path),
                             '-batch', '-passin', 'pass:{0}'.format(post['pin'])]
                gencrl = ['openssl', 'ca', '-config', '{0}/openssl.cnf'.format(user.home_path),
                          '-gencrl', '-passin', 'pass:{0}'.format(post['pin']),
                          '-out', '/{0}/cacrl.pem'.format(user.home_path), '-crldays', '1825']
                genrsa = ['openssl', 'genrsa', '-out', '{1}/private/{0}.key'.format(minion.username,
                                                                                    user.home_path),
                          '2048']
                genreq = ['openssl', 'req', '-new', '-batch',
                          '-config', '/{0}/openssl.cnf'.format(user.home_path),
                          '-key', '{1}/private/{0}.key'.format(minion.username, user.home_path),
                          '-out', '{1}/reqs/{0}.req'.format(minion.username, user.home_path),
                          '-subj', '/C=RU/O={1}/CN={0}'.format(minion.username, user.username)]
                gencert = ['openssl', 'ca', '-config', '{0}/openssl.cnf'.format(user.home_path), '-batch',
                           '-days', '300', '-notext', '-md', 'sha256', '-in',
                           '{1}/reqs/{0}.req'.format(minion.username, user.home_path), '-out',
                           '{1}/certs/{0}.pem'.format(minion.username, user.home_path), '-passin',
                           'pass:{0}'.format(post['pin'])]
                if os.path.isfile('{1}/certs/{0}.pem'.format(minion.username, user.home_path)):
                    try:
                        subprocess.check_output(crlexists)
                    except:
                        pass
                    subprocess.check_output(gencrl)

                subprocess.check_output(genrsa)
                subprocess.check_output(genreq)
                subprocess.check_output(gencert)
                data1 = open('{1}/certs/{0}.pem'.format(minion.username, user.home_path), 'rt').read()
                data2 = open('{1}/private/{0}.key'.format(minion.username, user.home_path), 'rt').read()
                with open('{1}/p12/{0}.pem'.format(minion.username, user.home_path), 'w') as file:
                    file.write(data1)
                    file.write(data2)
                wrk = Worker(username=minion.username, status_id=1, work='CERTUPDATE{1}/p12/{0}.pem'
                             .format(minion.username, user.home_path))
                wrk.save()
                if len(groupset) == 0 or groupset[0] != group.id:
                    User2Group.objects.filter(user_id=minion.id).delete()
                    u2g = User2Group(group_id=group.id, user_id=minion.id)
                    u2g.save()
                    wrk = Worker(username=minion.username, status_id=1, work='CACERTUPDATE{0}/cacert.pem'
                                 .format(user.home_path))
                    wrk.save()
                tsave = Worker.objects.filter(status_id=1, work='CONNECT_{0}'.format(minion.username))
                for rec in tsave:
                    rec.status_id = 6
                    rec.save()
                minion.home_path = user.home_path
                minion.save()
                return HttpResponse('ok')
    return render(request, 'GenX509.html', {'groups': groups, 'minion': minion, 'about': True, 'grset': groupset})


@transaction.atomic
def genadminpin(request):
    from datetime import timedelta
    user = get_user(request.META['HTTP_X_FORWARDED_USER'])
    from random import randint
    inbase = list(Worker.objects.filter(username='*', status_id=4, work__startswith='ADMPIN',
                                        create_tstamp__gte=datetime.now() - timedelta(hours=1))
                  .values_list('work', flat=True))
    pin = '{0}{1}{2}{3}{4}{5}'.format(randint(0, 9), randint(0, 9), randint(0, 9), randint(0, 9),
                                      randint(0, 9), randint(0, 9))
    while 'ADMPIN{0}'.format(pin) in inbase:
        pin = '{0}{1}{2}{3}{4}{5}'.format(randint(0, 9), randint(0, 9), randint(0, 9), randint(0, 9),
                                          randint(0, 9), randint(0, 9))
    oldpin = Worker.objects.filter(username='*', status_id=4, work__startswith='ADMPIN', author=user.username)
    for rec in oldpin:
        rec.status_id = 6
        rec.save()
    wrk = Worker(username='*', status_id=4, work='ADMPIN{0}'.format(pin))
    wrk.save()
    return render(request, 'AdminPin.html', {'PIN': pin})


def get_user(username):
    return User.objects.get(username=username)


@transaction.atomic
def index(request, cur_group=0):
    user = get_user(request.META['HTTP_X_FORWARDED_USER'])
    groups = Group.objects.all().order_by('id')
    response = {'user': user, 'groups': groups, 'current_group_id': cur_group}
    return render(request, 'main.html', response)
