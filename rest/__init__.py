"""Straight-forward REST client construction package.

This package defines a set of interfaces which makes it
straightforward to create classes that implement a REST API.  The
primary interface is the RESTClient class; in conjunction with the
@restmethod() decorator, methods defined on RESTClient subclasses can
issue simple HTTP requests, process the responses, and return desired
values.  As an example, let's assume we have a REST server bound to
the resource "http://example.com/hello" that returns "world" in
response to a GET.  A full client for this server may be:

    import rest

    class HelloClient(rest.RESTClient):
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
from rest import client
from rest import decorators
from rest import exceptions
from rest import headers
from rest import request


# Build up our __all__ and import all the symbols
__all__ = []
for _mod in (client, decorators, exceptions, headers, request):
    for _sym in _mod.__all__:
        vars()[_sym] = getattr(_mod, _sym)
    __all__ += _mod.__all__
