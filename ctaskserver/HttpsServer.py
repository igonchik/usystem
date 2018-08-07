#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
pip install aiojobs
pip install  aiopg
pip  install aioredis
patch aiopg.connection.py #109 self._conn = psycopg2.connect(dsn, async_=True, **kwargs)
patch aiopg.utils.py #18     ensure_future = asyncio.async_
pip install sqlalchemy
pip install psycopg2-binary

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
import aioredis
from aiopg.sa import create_engine
from aiopg.sa.exc import *
import ssl
from aiohttp.web import middleware
from celery import Celery
import sqlalchemy as sa
from datetime import datetime


celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

metadata = sa.MetaData()
pubuser = sa.Table('usystem_pubuser', metadata,
                   sa.Column('username', sa.String(100), nullable=False),
                   sa.Column('email', sa.Text))

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
                     sa.Column('is_master', sa.Boolean),
                     sa.Column('email_confirmed', sa.Boolean),
                     schema='pubview'
                     )

work_view = sa.Table('usystem_worker_view', metadata,
                     sa.Column('author', sa.String(255), nullable=False),
                     sa.Column('username', sa.String(255), nullable=False),
                     sa.Column('create_tstamp', sa.DateTime),
                     sa.Column('get_tstamp', sa.DateTime),
                     sa.Column('work', sa.DateTime),
                     sa.Column('status_id', sa.Integer),
                     sa.Column('id', sa.Integer, nullable=False),
                     schema='pubview'
                     )


class USystemServer:
    def __init__(self, psql_server, ssl_ciphers=None, debug=False):
        self.ssl_ciphers = ssl_ciphers
        self.psql_server = psql_server
        self.debug = debug

        @middleware
        async def cert_middleware(request, handler):
            response = web.Response(status=403)
            username = None
            email = None
            try:
                peercert = request.transport._ssl_protocol._extra['peercert']['subject']
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
                    print("Minion has no peer cert")
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
                sub = await aioredis.create_redis(('localhost', 6379), loop=app.loop)
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
                                                'testcerts', 'usystem.com.pem'))
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

    async def _write_to_postgres_hello(self, request, data):
        async with self.app['pg_engine'].acquire() as connection:
            query = (sa.select([pubuser.c.username]).select_from(pubuser)
                     .where(pubuser.c.username == request['remote_user']))
            res = await connection.execute(query)
            return_ = {}
            if res.rowcount == 0:
                #create new user
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

            #update user status
            query = sa.update(user_view).where(user_view.c.username == request['remote_user']). \
                values(version=data['version'])
            await connection.execute(query)

            # update works status
            if 'task' in data.keys() and len(data['task']) > 1:
                for rec in data['task']:
                    query = sa.update(work_view).where(work_view.c.id == int(rec[0])). \
                        where(work_view.c.username == request['remote_user']).values(status_id=int(rec[1]))
                    await connection.execute(query)

            # find and send new works to minion
            query = (sa.select([work_view.c.id, work_view.c.work]).select_from(work_view)
                     .where(work_view.c.username == request['remote_user']).where(work_view.c.status_id == 1))
            res = await connection.execute(query)
            if res.returns_rows:
                tasks = await res.fetchall()
                for rec in tasks:
                    if 'VNCCONNECT' in rec[1]:
                        query = sa.update(work_view).where(work_view.c.id == int(rec[0])).values(status_id=4)
                        await connection.execute(query)
                        return_.update({'vnc': [int(rec[0]), int(rec[1][10:])]})
                    elif 'CERTUPDATE' in rec[1]:
                        query = sa.update(work_view).where(work_view.c.id == int(rec[0])).values(status_id=2)
                        await connection.execute(query)
                        try:
                            st_cert = open(rec[1][10:], 'rt').read()
                            return_.update({'certfile': [int(rec[0]), st_cert]})
                        except:
                            print("Can not open cert file in path".format(rec[1][10:]))
                    elif 'CACERTUPDATE' in rec[1]:
                        query = sa.update(work_view).where(work_view.c.id == int(rec[0])).values(status_id=2)
                        await connection.execute(query)
                        try:
                            st_cert = open(rec[1][12:], 'rt').read()
                            return_.update({'cacertfile': [int(rec[0]), st_cert]})
                        except:
                            print("Can not open cacert file in path".format(rec[1][12:]))
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
    USystemServer('db.usystem.com', debug=True)
