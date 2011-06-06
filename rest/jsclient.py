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

"""Straight-forward JSON REST client construction.

This module extends the base REST infrastructure of the rest package
by providing a JSONClient class, to support REST-based protocols that
use JSON-serialized data.  As an example, let's assume we have a REST
server bound to the resource "http://example.com/echo" that returns
any object that is POSTed to it.  A full client for this server may
be:

    import rest
    from rest import jsclient

    class EchoClient(jsclient.JSONClient):
        @restmethod('POST', '/echo')
        def echo(self, req, obj):
            self._attach_obj(req, obj)
            return req.send().obj

To use this client:

    >>> ec = EchoClient('http://example.com')
    >>> ec.echo({'foo': bar})
    {'foo': bar}

See the documentation for JSONClient for more information.
"""


import json

from rest import client
from rest import request


__all__ = ['JSONRequest', 'JSONClient']


class JSONRequest(request.HTTPRequest):
    """Variant of HTTPRequest to process JSON data in responses."""

    def proc_response(self, resp):
        """Process JSON data found in the response."""

        # Try to interpret any JSON
        try:
            resp.obj = json.loads(resp.body)
            self._debug("  Received entity: %r", resp.obj)
        except ValueError:
            resp.obj = None
            self._debug("  No received entity; body %r", resp.body)

        # Now, call superclass method for error handling
        super(JSONRequest, self).proc_response(resp)


class JSONClient(client.RESTClient):
    """Process JSON data in requests and responses.

    Augments RESTClient to include the _attach_obj() helper method,
    for attaching JSON objects to requests.  Also uses JSONRequest in
    preference to HTTPRequest, so that JSON data in responses is
    processed.
    """

    _req_class = JSONRequest
    _content_type = 'application/json'

    def __init__(self, baseurl, headers=None, debug=False):
        """Override RESTClient.__init__() to set an Accept header."""

        # Initialize superclass
        super(JSONClient, self).__init__(baseurl, headers, debug)

        # Set the accept header
        self._headers.setdefault('accept', self._content_type)

    def _attach_obj(self, req, obj):
        """Helper method to attach obj to req as JSON data."""

        # Attach the object to the request
        json.dump(obj, req)

        # Also set the content-type header
        req['content-type'] = self._content_type
