# Copyright 2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Straight-forward REST client construction package.

This package defines a set of interfaces which makes it
straightforward to create classes that implement a REST API.  The
primary interface is the RESTClient class; in conjunction with the
@restmethod() decorator, methods defined on RESTClient subclasses can
issue simple HTTP requests, process the responses, and return desired
values.  As an example, let's assume we have a REST server bound to
the resource "http://example.com/hello" that returns "world" in
response to a GET.  A full client for this server may be:

    import requiem

    class HelloClient(requiem.RESTClient):
        @restmethod('GET', '/hello')
        def hello(self, req):
            resp = req.send()

            return resp.read()

To use this client:

    >>> hc = HelloClient('http://example.com')
    >>> hc.hello()
    'world'

For information about the request that is passed to @restmethod()
decorated methods, see the documentation for HTTPRequest, as well as
the documentation for @restmethod() itself.
"""


# Import everything
from requiem import client
from requiem import decorators
from requiem import exceptions
from requiem import headers
from requiem import processor
from requiem import request


# Build up our __all__ and import all the symbols
__all__ = []
for _mod in (client, decorators, exceptions, headers, processor, request):
    for _sym in _mod.__all__:
        vars()[_sym] = getattr(_mod, _sym)
    __all__ += _mod.__all__
