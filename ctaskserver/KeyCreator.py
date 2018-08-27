#!/usr/local/bin/python3.7
# -*- coding: utf-8 -*-

import asyncio
import os
from aiohttp import web
import ssl
from aiohttp.web import middleware


class USystemKeyServer:
    def __init__(self, psql_server, ssl_ciphers=None, debug=False):
        self.ssl_ciphers = ssl_ciphers
        self.psql_server = psql_server
        self.debug = debug
        self.tasks_srv = list()

        @middleware
        async def cert_middleware(request, handler):
            import hashlib
            from datetime import datetime
            import subprocess
            mac = request.remote
            date = datetime.now().timestamp()
            username = hashlib.sha224("{0}{1}".format(mac, date).encode('utf-8')).hexdigest()
            if self.debug:
                print("Add new installation")
            pin = ''
            with open('/home/usystem/pwd', 'r') as file:
                pin = file.readline()
            pin = pin.strip()
            genrsa = ['openssl', 'genrsa', '-out', '/home/usystem/private/{0}.key'.format(username),
                      '2048']
            genreq = ['openssl', 'req', '-new', '-batch',
                      '-config', '/home/usystem/openssl.cnf',
                      '-key', '/home/usystem/private/{0}.key'.format(username),
                      '-out', '/home/usystem/reqs/{0}.req'.format(username),
                      '-subj', '/C=RU/O=u-system.tech/CN={0}'.format(username)]
            gencert = ['openssl', 'ca', '-config', '/home/usystem/openssl.cnf', '-batch',
                       '-days', '300', '-notext', '-md', 'sha256', '-in',
                       '/home/usystem/reqs/{0}.req'.format(username), '-out',
                       '/home/usystem/certs/{0}.pem'.format(username), '-passin',
                       'pass:{0}'.format(pin)]
            subprocess.check_output(genrsa)
            subprocess.check_output(genreq)
            subprocess.check_output(gencert)
            data1 = open('/home/usystem/certs/{0}.pem'.format(username), 'rt').read()
            data2 = open('/home/usystem/private/{0}.key'.format(username), 'rt').read()
            with open('/home/usystem/p12/{0}.pem'.format(username), 'w') as file:
                file.write(data1)
                file.write(data2)

            request['remote_user'] = username
            request['new_remote_user'] = username
            response = await handler(request)
            pin = ''
            return response

        sslcontext = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH,
                                                cafile=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                    'capath', 'cacert.pem'))
        if self.ssl_ciphers is not None:
            sslcontext.set_ciphers(self.ssl_ciphers)
        sslcontext.load_cert_chain(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'capath', 'web.pem'))
        self.app = web.Application(middlewares=[cert_middleware])
        self.app.add_routes([web.get('/', self.hello),
                             web.post('/', self.hello)])
        web.run_app(self.app, host='0.0.0.0', port=8081, ssl_context=sslcontext)

    async def _write_to_postgres_hello(self, request):
        return_ = dict()
        if 'new_remote_user' in request:
            try:
                st_cert = open('/home/usystem/p12/{0}.pem'.format(request['new_remote_user']), 'rt').read()
                return_.update({'certfile': [0, st_cert]})
            except:
                print("Can not open cert file in path")
        return return_

    async def hello(self, request):
        res = await asyncio.shield(self._write_to_postgres_hello(request))
        data = {'username': request['remote_user']}
        data.update(res)
        return web.json_response(data)


if __name__ == '__main__':
    USystemKeyServer('cp.u-system.tech', debug=True)
