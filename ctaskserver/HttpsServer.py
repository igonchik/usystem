#!/usr/local/bin/python3.7
# -*- coding: utf-8 -*-
"""
pip3 install aiojobs
pip3 install  aiopg
pip3  install aioredis
patch aiopg.connection.py #109 self._conn = psycopg2.connect(dsn, async_=True, **kwargs)
patch aiopg.utils.py #18     ensure_future = asyncio.async_
pip3 install sqlalchemy;pip3 install psycopg2-binary

for redis:
amqp==2.2.1
billiard==3.5.0.3
pip install celery
redis==2.10.6
pytz
"""

import asyncio
import os
from aiohttp import web
#import aioredis
from aiopg.sa import create_engine
from aiopg.sa.exc import *
import ssl
from aiohttp.web import middleware
from celery import Celery
import sqlalchemy as sa
from datetime import datetime
from datetime import timedelta
from sqlalchemy.orm import scoped_session, sessionmaker


celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

metadata = sa.MetaData()
pubuser = sa.Table('usystem_pubuser', metadata,
                   sa.Column('username', sa.String(100), nullable=False),
                   sa.Column('email', sa.Text))

portmap = sa.Table('usystem_portmap_view', metadata,
                   sa.Column('work_id', sa.Integer, nullable=False),
                   sa.Column('port_num', sa.Integer, nullable=False),
                   schema='pubview')

programs = sa.Table('usystem_programm_view', metadata,
                    sa.Column('username', sa.String(100), nullable=False),
                    sa.Column('name', sa.String(100), nullable=False),
                    sa.Column('classname_id', sa.Integer, nullable=False),
                    schema='pubview')

user_view = sa.Table('usystem_user_view', metadata,
                     sa.Column('current_ip', sa.String(255)),
                     sa.Column('installation_tstamp', sa.DateTime),
                     sa.Column('lastactivity_tstamp', sa.DateTime),
                     sa.Column('expirepwd_tstamp', sa.DateTime),
                     sa.Column('expirecert_tstamp', sa.DateTime),
                     sa.Column('email', sa.Text),
                     sa.Column('home_path', sa.Text),
                     sa.Column('alias', sa.Text),
                     sa.Column('username', sa.String(100), nullable=False),
                     sa.Column('version', sa.String(100)),
                     sa.Column('policy', sa.Integer),
                     sa.Column('id', sa.Integer),
                     sa.Column('is_master', sa.Boolean),
                     sa.Column('email_confirmed', sa.Boolean),
                     schema='pubview'
                     )

work_view = sa.Table('usystem_worker_view', metadata,
                     sa.Column('author', sa.String(255), nullable=False),
                     sa.Column('username', sa.String(255), nullable=False),
                     sa.Column('create_tstamp', sa.DateTime),
                     sa.Column('get_tstamp', sa.DateTime),
                     sa.Column('work', sa.String(255)),
                     sa.Column('status_id', sa.Integer),
                     sa.Column('id', sa.Integer, nullable=False),
                     schema='pubview'
                     )

u2g_view = sa.Table('usystem_user2group_view', metadata,
                    sa.Column('user_id', sa.Integer, nullable=False),
                    sa.Column('group_id', sa.Integer, nullable=False),
                    sa.Column('id', sa.Integer, nullable=False),
                    schema='pubview'
                    )

wmiinfo_view = sa.Table('usystem_wmiinfo_view', metadata,
                        sa.Column('agent_id', sa.Integer),
                        sa.Column('osname', sa.String(255), nullable=False),
                        sa.Column('osversion', sa.String(255), nullable=False),
                        sa.Column('proc_info', sa.String(255), nullable=False),
                        sa.Column('free_ram', sa.Integer),
                        sa.Column('system_ram', sa.Integer),
                        sa.Column('domain', sa.String(255), nullable=False),
                        sa.Column('name', sa.String(255), nullable=False),
                        sa.Column('username', sa.String(255), nullable=False),
                        sa.Column('cpu_load', sa.Integer),
                        sa.Column('id', sa.Integer, nullable=False),
                        schema='pubview'
                        )

wmisoft_view = sa.Table('usystem_wmisoft_view', metadata,
                        sa.Column('agent_id', sa.Integer),
                        sa.Column('display_name', sa.String(255), nullable=False),
                        sa.Column('display_version', sa.String(255), nullable=False),
                        sa.Column('install_location', sa.String(255), nullable=False),
                        sa.Column('install_date', sa.DateTime, nullable=False),
                        sa.Column('id', sa.Integer, nullable=False),
                        schema='pubview'
                        )

wmidrive_view = sa.Table('usystem_wmidrive_view', metadata,
                         sa.Column('caption', sa.String(255), nullable=False),
                         sa.Column('wmi_id', sa.Integer),
                         sa.Column('drivetype_id', sa.Integer),
                         sa.Column('free', sa.Integer),
                         sa.Column('size', sa.Integer),
                         sa.Column('id', sa.Integer, nullable=False),
                         schema='pubview'
                         )

wminetdrive_view = sa.Table('usystem_wminetdrive_view', metadata,
                            sa.Column('caption', sa.String(255), nullable=False),
                            sa.Column('wmi_id', sa.Integer),
                            sa.Column('macaddr', sa.String(255), nullable=False),
                            sa.Column('id', sa.Integer, nullable=False),
                            schema='pubview'
                            )

wmiipinfo_view = sa.Table('usystem_wmiipinfo_view', metadata,
                          sa.Column('macaddr', sa.String(255), nullable=False),
                          sa.Column('netdrive_id', sa.Integer),
                          sa.Column('ipaddr', sa.String(255), nullable=False),
                          sa.Column('id', sa.Integer, nullable=False),
                          schema='pubview'
                          )

wmigpuinfo_view = sa.Table('usystem_wmigpuinfo_view', metadata,
                           sa.Column('caption', sa.String(255), nullable=False),
                           sa.Column('wmi_id', sa.Integer),
                           sa.Column('id', sa.Integer, nullable=False),
                           schema='pubview'
                           )


class USystemServer:
    def __init__(self, psql_server, ssl_ciphers=None, debug=False):
        self.ssl_ciphers = ssl_ciphers
        self.psql_server = psql_server
        self.debug = debug
        self.tasks_srv = list()

        @middleware
        async def cert_middleware(request, handler):
            response = web.Response(status=403)
            username = None
            email = None
            try:
                peercert = request.transport._ssl_protocol._extra['peercert']['subject']
                from datetime import datetime
                request['notAfter'] = datetime.strptime(request.transport._ssl_protocol._extra['peercert']['notAfter'],
                                                        '%b %d %H:%M:%S %Y %Z')
                for rec in peercert:
                    if rec[0][0] == 'commonName':
                        username = rec[0][1]
                    elif rec[0][0] == 'emailAddress':
                        email = rec[0][1]
                if username:
                    request['remote_user'] = username
                    request['remote_email'] = email
            except:
                if self.debug:
                    print('Client does not send cert')

            if username:
                response = await handler(request)
            return response

        async def pg_engine(app):
            app['pg_engine'] = await create_engine(
                user='uminion_',
                database='usystem',
                host=psql_server,
                port=5432,
                password=''
            )
            yield
            app['pg_engine'].close()
            await app['pg_engine'].wait_closed()

        async def listen_to_redis(app):
            sub = None
            try:
                pass
                # TODO: add if
                # sub = await aioredis.create_redis(('localhost', 6379), loop=app.loop)
            except asyncio.CancelledError:
                pass
            finally:
                await sub.quit()

        async def start_background_tasks(app):
            app['redis_listener'] = app.loop.create_task(listen_to_redis(app))

        async def cleanup_background_tasks(app):
            app['redis_listener'].cancel()
            await app['redis_listener']

        sslcontext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                                cafile=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                    'capath', 'cacert.pem'))
        if self.ssl_ciphers is not None:
            sslcontext.set_ciphers(self.ssl_ciphers)
        sslcontext.load_cert_chain(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'capath', 'web.pem'))
        sslcontext.verify_flags = ssl.VERIFY_CRL_CHECK_LEAF
        sslcontext.verify_mode = ssl.CERT_REQUIRED
        self.app = web.Application(middlewares=[cert_middleware])
        self.app.cleanup_ctx.append(pg_engine)
        self.app.on_startup.append(start_background_tasks)
        self.app.on_cleanup.append(cleanup_background_tasks)
        self.app.add_routes([web.get('/', self.hello),
                             web.post('/', self.hello)])
        web.run_app(self.app, host='0.0.0.0', port=8080, ssl_context=sslcontext)

    @celery_app.task
    def _debug_task(self):
        if self.debug:
            print('Request: {0!r}'.format(11))

    @celery_app.task
    async def _write_to_redis(self, request):
        return 0

    @staticmethod
    def path_leaf(path):
        import ntpath
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    async def _write_to_postgres_hello(self, request, data):
        async with self.app['pg_engine'].acquire() as connection:
            query = (sa.select([pubuser.c.username]).select_from(pubuser)
                     .where(pubuser.c.username == request['remote_user']))
            res = await connection.execute(query)
            return_ = {}
            if res.rowcount == 0:
                # create new user
                try:
                    await connection.scalar(pubuser.insert().values(username=request['remote_user']))
                except ResourceClosedError:
                    if self.debug:
                        print("Append new minion {0}...".format(request['remote_user']))
                if 'platform' in data.keys():
                    try:
                        await connection.scalar(programs.insert().values(username=request['remote_user'],
                                                                         classname_id=1, name=data['platform']))
                    except ResourceClosedError:
                        if self.debug:
                            print("Append new program {0}...".format(request['remote_user']))

            # update user status
            if 'policy' in data and 'version' in data:
                query = sa.update(user_view).where(user_view.c.username == request['remote_user']). \
                    values(version=data['version'], current_ip=request.remote, policy=int(data['policy']))
            else:
                query = sa.update(user_view).where(user_view.c.username == request['remote_user']). \
                    values(current_ip=request.remote)
            await connection.execute(query)

            if 'new_remote_user' in request:
                try:
                    st_cert = open('/home/usystem/p12/{0}.pem'.format(request['new_remote_user']), 'rt').read()
                    return_.update({'certfile': [0, st_cert]})
                except:
                    print("Can not open cert file in path")

            if 'datasoft' in data:
                softaudit = data['datasoft']
                query = sa.select([user_view.c.id]).select_from(user_view) \
                    .where(user_view.c.username == request['remote_user'])
                res = await connection.execute(query)
                users = await res.fetchall()
                user_id = users[0][0]
                query_del = sa.delete(wmisoft_view).where(wmisoft_view.c.agent_id == int(user_id))
                await connection.execute(query_del)
                query_ins_all = ''
                for rec in softaudit:
                    rec_install = datetime.strftime(datetime.strptime(rec['install_date'], '%Y%m%d'), '%Y-%m-%d')\
                        if rec['install_date'] != '' else None
                    if rec_install:
                        query_ins = "insert into \"pubview\".usystem_wmisoft_view (display_version, display_name, " \
                                    "install_location, install_date, agent_id) values ('" \
                                    "" + rec['display_version']\
                                    + "', '" + rec['display_name']\
                                    + "', '" + rec['install_location']\
                                    + "', '" + rec_install + "', " + str(user_id) + ");"
                    else:
                        query_ins = "insert into \"pubview\".usystem_wmisoft_view (display_version, display_name, " \
                                    "install_location, install_date, agent_id) values ('" \
                                    "" + rec['display_version'] \
                                    + "', '" + rec['display_name'] \
                                    + "', '" + rec['install_location'] \
                                    + "', null, " + str(user_id) + ");"
                    query_ins_all = '{0}\n{1}'.format(query_ins_all, query_ins)
                await connection.execute(query_ins_all)

            if 'mainaudit' in data:
                drive = data['drive'] if 'drive' in data else list()
                netdev = data['netdev'] if 'netdev' in data else list()
                os_name = data['OS Name'] if 'OS Name' in data else ''
                os_version = data['OS Version'] if 'OS Version' in data else ''
                proc_info = data['CPU'] if 'CPU' in data else ''
                free_ram = int(data['Free RAM']) if 'Free RAM' in data else 0
                system_ram = int(data['SYS RAM']) if 'SYS RAM' in data else 0
                gpu_info = data['Graphics Card'] if 'Graphics Card' in data else list()
                domain = data['Domain'] if 'Domain' in data else ''
                name = data['Name'] if 'Name' in data else ''
                username = data['Username'] if 'Username' in data else ''
                cpu_load = float(data['CPU Load']) if 'CPU Load' in data else 0
                query = sa.select([user_view.c.id]).select_from(user_view) \
                    .where(user_view.c.username == request['remote_user'])
                res = await connection.execute(query)
                users = await res.fetchall()
                user_id = users[0][0]
                query_del = sa.delete(wmiinfo_view).where(wmiinfo_view.c.agent_id == int(user_id))
                await connection.execute(query_del)
                wmi = await connection.scalar(wmiinfo_view.insert()
                                              .values(agent_id=user_id,
                                                      osname=os_name,
                                                      osversion=os_version,
                                                      proc_info=proc_info,
                                                      free_ram=free_ram,
                                                      system_ram=system_ram,
                                                      domain=domain,
                                                      name=name,
                                                      username=username,
                                                      cpu_load=cpu_load,
                                                      ).returning(wmiinfo_view.c.id))
                for recx in drive:
                    await connection.scalar(wmidrive_view.insert()
                                            .values(caption=recx[0],
                                                    wmi_id=wmi,
                                                    drivetype_id=int(recx[3]),
                                                    free=int(recx[1]),
                                                    size=int(recx[2]),
                                                    ).returning(wmidrive_view.c.id))
                for recx in gpu_info:
                    await connection.scalar(wmigpuinfo_view.insert()
                                            .values(caption=recx,
                                                    wmi_id=wmi,
                                                    ).returning(wmigpuinfo_view.c.id))
                for recx in netdev:
                    netwmi = await connection.scalar(wminetdrive_view.insert()
                                                     .values(caption=recx[0],
                                                             wmi_id=wmi,
                                                             macaddr=recx[1],
                                                             ).returning(wminetdrive_view.c.id))
                    await connection.scalar(wmiipinfo_view.insert()
                                            .values(ipaddr=recx[2][0],
                                                    netdrive_id=netwmi,
                                                    macaddr=recx[2][1],
                                                    ).returning(wmiipinfo_view.c.id))

            if 'goout' in data:
                query = sa.select([user_view.c.id]).select_from(user_view) \
                    .where(user_view.c.username == request['remote_user'])
                res = await connection.execute(query)
                users = await res.fetchall()
                user_id = users[0][0]
                query_del = sa.delete(u2g_view).where(u2g_view.c.user_id == int(user_id))
                await connection.execute(query_del)

            if 'adminpin' in data:
                query = sa.select([work_view.c.author]).select_from(work_view)\
                    .where(work_view.c.username == '*').where(work_view.c.status_id == 4)\
                    .where(work_view.c.create_tstamp >= datetime.now()-timedelta(hours=1))\
                    .where(work_view.c.work == 'ADMPIN{0}'.format(data['adminpin']))
                res = await connection.execute(query)
                if res.returns_rows:
                    tasks = await res.fetchall()
                    for rec in tasks:
                        try:
                            await connection.scalar(work_view.insert()
                                                    .values(username=rec[0],
                                                            work='CONNECT_{0}'.format(request['remote_user']),
                                                            status_id=1))
                        except ResourceClosedError:
                            if self.debug:
                                print("Try to connect {0} to {1}...".format(request['remote_user'], rec))

            # update works status
            if 'task' in data.keys() and len(data['task']) > 0:
                for rec in data['task']:
                    query = sa.update(work_view).where(work_view.c.id == int(rec[0])).\
                        where(work_view.c.status_id <= 4). \
                        where(work_view.c.username == request['remote_user']).values(status_id=int(rec[1]))
                    # delete buinding ports
                    if int(rec[1]) > 4:
                        query_del = sa.delete(portmap).where(portmap.c.work_id == int(rec[0]))
                        await connection.execute(query_del)
                    await connection.execute(query)

            # find and send new works to minion
            query = (sa.select([work_view.c.id, work_view.c.work]).select_from(work_view)
                     .where(work_view.c.username == request['remote_user']).where(work_view.c.status_id == 1))
            res = await connection.execute(query)
            if res.returns_rows:
                tasks = await res.fetchall()
                for rec in tasks:
                    if rec[1].startswith('FILEOUT'):
                        query = sa.update(work_view).where(work_view.c.id == int(rec[0])).values(status_id=2)
                        await connection.execute(query)
                        return_.update({'fileouttransfer': [int(rec[0]), int(rec[1][7:].split(':', 1)[0]),
                                                            rec[1][7:].split(':', 1)[1]]})
                    if rec[1].startswith('FILEIN'):
                        query = sa.update(work_view).where(work_view.c.id == int(rec[0])).values(status_id=2)
                        await connection.execute(query)
                        return_.update({'fileintransfer': [int(rec[0]), int(rec[1][6:].split(':', 1)[0]),
                                                           self.path_leaf(rec[1][6:].split(':', 1)[1])]})
                    if rec[1].startswith('VNCCONNECT'):
                        query = sa.update(work_view).where(work_view.c.id == int(rec[0])).values(status_id=2)
                        await connection.execute(query)
                        return_.update({'vnc': [int(rec[0]), int(rec[1][10:])]})
                    if rec[1].startswith('MAINAUDIT'):
                        query = sa.update(work_view).where(work_view.c.id == int(rec[0])).values(status_id=2)
                        await connection.execute(query)
                        return_.update({'mainaudit': [int(rec[0])]})
                    if rec[1].startswith('SOFTAUDIT'):
                        query = sa.update(work_view).where(work_view.c.id == int(rec[0])).values(status_id=2)
                        await connection.execute(query)
                        return_.update({'softaudit': [int(rec[0])]})
                    if rec[1].startswith('CERTUPDATE'):
                        query = sa.update(work_view).where(work_view.c.id == int(rec[0])).values(status_id=2)
                        await connection.execute(query)
                        try:
                            st_cert = open(rec[1][10:], 'rt').read()
                            return_.update({'certfile': [int(rec[0]), st_cert]})
                        except:
                            print("Can not open cert file in path {0}".format(rec[1][10:]))
                    if rec[1].startswith('RCERTUPDATE'):
                        query = sa.update(work_view).where(work_view.c.id == int(rec[0])).values(status_id=2)
                        await connection.execute(query)
                        return_.update({'rcertfile': [int(rec[0]), '']})
                    if rec[1].startswith('CACERTUPDATE'):
                        query = sa.update(work_view).where(work_view.c.id == int(rec[0])).values(status_id=2)
                        await connection.execute(query)
                        try:
                            st_cert0 = open('/home/usystem/cacert.pem', 'rt').read()
                            st_cert = open(rec[1][12:], 'rt').read()
                            return_.update({'cacertfile': [int(rec[0]), '{0}{1}'.format(st_cert0, st_cert)]})
                        except:
                            print("Can not open cacert file in path {0}".format(rec[1][12:]))
            return return_

    async def hello(self, request):
        data = await request.json()
        res = await asyncio.shield(self._write_to_postgres_hello(request, data))
        if 'redis' in data.keys() and data['redis'] != '':
            await asyncio.shield(self._write_to_redis(request))
        data = {'username': request['remote_user']}
        data.update(res)
        return web.json_response(data)


if __name__ == '__main__':
    USystemServer('cp.u-system.tech', debug=True)
