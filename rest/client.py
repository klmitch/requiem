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

    def __init__(self, baseurl, headers=None, debug=False):
        """Initialize a REST client API.

        The baseurl specifies the base URL for the REST service.  If
        provided, headers specifies a dictionary of additional HTTP
        headers to set on every request.  Beware of name clashes in
        the keys of headers; header names are considered in a
        case-insensitive manner.
        """

        # Initialize an API client
        self._baseurl = baseurl
        self._headers = hdrs.HeaderDict(headers)
        self._debug_mode = debug

    def _debug(self, msg, *args, **kwargs):
        """Emit debugging messages."""

        # Do nothing if debugging is disabled
        if not self._debug_mode:
            return

        # What are we passing to the format?
        if kwargs:
            fmtargs = kwargs
        else:
            fmtargs = args

        # Emit the message
        print >>sys.stderr, msg % fmtargs

    def _make_req(self, method, url, headers=None):
        """Create a request object for the specified method and url."""

        # Were headers specified?
        if headers is not None:
            # Create a copy of our global headers...
            hdrs = self._headers.copy()

            # Update from specified headers
            hdrs.update(headers)
        else:
            # Use our global headers...
            hdrs = self._headers

        # Hook method to instantiate requests
        self._debug("Creating request %s.%s(%r, %r, headers=%r)",
                    self._req_class.__module__, self._req_class.__name__,
                    method, url, hdrs)
        return self._req_class(method, url, headers=hdrs, debug=self._debug)
