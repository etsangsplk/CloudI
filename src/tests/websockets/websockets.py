#!/usr/bin/env python
#-*-Mode:python;coding:utf-8;tab-width:4;c-basic-offset:4;indent-tabs-mode:()-*-
# ex: set ft=python fenc=utf-8 sts=4 ts=4 sw=4 et nomod:
#
# MIT License
#
# Copyright (c) 2013-2017 Michael Truog <mjtruog at gmail dot com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

import sys, threading, time, traceback
from cloudi_c import API, terminate_exception

class Task(threading.Thread):
    def __init__(self, api):
        threading.Thread.__init__(self)
        self.__api = api

    def run(self):
        try:
            self.__api.subscribe('bounce/get', self.__request)
            self.__api.subscribe('bounce/delay', self.__delay)
            self.__api.subscribe('bounce/websocket/connect',
                                 self.__connect)
            self.__api.subscribe('bounce/websocket/disconnect',
                                 self.__disconnect)

            result = self.__api.poll()
            assert result == False
        except terminate_exception:
            pass
        except:
            traceback.print_exc(file=sys.stderr)
        print('terminate websockets python_c')

    def __connect(self, request_type, name, pattern, request_info, request,
                  timeout, priority, trans_id, pid):
        assert request == 'CONNECT'
        print('connect: %s' %
              str(self.__api.info_key_value_parse(request_info)))
        return 'got connect! yay!'

    def __disconnect(self, request_type, name, pattern, request_info, request,
                     timeout, priority, trans_id, pid):
        assert request == 'DISCONNECT'
        print('disconnect: %s' %
              str(self.__api.info_key_value_parse(request_info)))
        return ''

    def __request(self, request_type, name, pattern, request_info, request,
                  timeout, priority, trans_id, pid):
        # send the request to self
        self.__api.send_async(self.__api.prefix() + 'bounce/delay',
                              request)
        return request

    def __delay(self, request_type, name, pattern, request_info, request,
                timeout, priority, trans_id, pid):
        time.sleep(1.0)
        assert name[-6:] == '/delay'
        trans_ids = self.__api.mcast_async(name[:-6] + '/websocket',
                                           'notification: got "' +
                                           request + '" 1 second ago')
        if len(trans_ids) == 0:
            print('websockets: (no websockets connected?)')
        else:
            for check in trans_ids:
                (tmp, response, tmp) = self.__api.recv_async(trans_id=check)
                print('websockets: %s' % str(response))

if __name__ == '__main__':
    thread_count = API.thread_count()
    assert thread_count >= 1
    
    threads = [Task(API(i)) for i in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

