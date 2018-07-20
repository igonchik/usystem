# -*- coding: utf-8 -*-

import traceback
import sys
import datetime

@staticmethod
class ProcessExceptionMiddleware(object):
    def process_exception(self, request, exception):
        sys.stderr.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S\n'))
        sys.stderr.write('\n'.join(traceback.format_exception(*sys.exc_info())))
        pass