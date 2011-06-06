import sys

from rest import headers as hdrs
from rest import request


__all__ = ['RESTClient']


class RESTClient(object):
    """Represent a REST client API.

    Methods are expected to perform REST calls to a server specified
    by a base URL.  The @restmethod() decorator helps this process by
    passing an additional HTTPRequest object into the method.  The
    request class to use can be overridden by changing the
    '_req_class' class attribute or by overriding the _make_req()
    method.
    """

    _req_class = request.HTTPRequest

    def __init__(self, baseurl, headers=None, debug=None):
        """Initialize a REST client API.

        The baseurl specifies the base URL for the REST service.  If
        provided, headers specifies a dictionary of additional HTTP
        headers to set on every request.  Beware of name clashes in
        the keys of headers; header names are considered in a
        case-insensitive manner.

        Debugging output can be enabled by passing a stream as the
        debug parameter.  If True is passed instead, sys.stderr will
        be used.
        """

        # Initialize an API client
        self._baseurl = baseurl
        self._headers = hdrs.HeaderDict(headers)
        self._debug_stream = sys.stderr if debug is True else debug

    def _debug(self, msg, *args, **kwargs):
        """Emit debugging messages."""

        # Do nothing if debugging is disabled
        if self._debug_stream is None or self._debug_stream is False:
            return

        # What are we passing to the format?
        if kwargs:
            fmtargs = kwargs
        else:
            fmtargs = args

        # Emit the message
        print >>self._debug_stream, msg % fmtargs

    def _make_req(self, method, url, headers=None):
        """Create a request object for the specified method and url."""

        # Build up headers
        hset = hdrs.HeaderDict()

        # Walk through our global headers
        for hdr, value in self._headers.items():
            # If it's a callable, call it
            if callable(value):
                hset[hdr] = value()
            else:
                # OK, just stringify it
                hset[hdr] = str(value)

        # Were headers passed in?
        if headers is not None:
            # Update from specified headers
            hset.update(headers)

        # Hook method to instantiate requests
        self._debug("Creating request %s.%s(%r, %r, headers=%r)",
                    self._req_class.__module__, self._req_class.__name__,
                    method, url, hset)
        return self._req_class(method, url, headers=hdrs, debug=self._debug)
