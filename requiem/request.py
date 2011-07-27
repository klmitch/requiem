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

from requiem import exceptions as exc
from requiem import headers as hdrs


__all__ = ['HTTPRequest']


class HTTPRequest(object):
    """Represent and perform HTTP requests.

    Implements the dictionary access protocol to modify headers
    (headers can also be accessed directly at the 'headers' attribute)
    and the stream protocol to build up the body.  Handles
    redirections under control of the class attribute 'max_redirects'.
    Understands schemes supported by the specified client, which must
    be compatible with the httplib2.Http object.
    """

    max_redirects = 10

    def __init__(self, method, url, client,
                 body=None, headers=None, debug=None):
        """Initialize a request.

        The method and url must be specified.  The body and headers
        are optional, and may be manipulated after instantiating the
        object.
        """

        # Save the relevant data
        self.method = method.upper()
        self.url = url
        self.client = client
        self.body = body or ''
        self.headers = hdrs.HeaderDict()
        self._debug = debug or (lambda *args, **kwargs: None)

        # Set up the headers...
        if headers:
            self.headers.update(headers)

        self._debug("Initialized %r request for %r", self.method, self.url)

    def write(self, data):
        """Write data to the body."""

        self._debug("Adding %r to request body", data)

        # Add the written data to our body
        self.body += data

    def flush(self):
        """Flush body stream--no-op for compatibility."""

        # Do-nothing to allow stream compatibility
        pass

    def send(self):
        """Issue the request.

        Uses httplib2.Http support for handling redirects.  Returns an
        httplib2.Response, which may be augmented by the
        proc_response() method.

        Note that the default implementation of proc_response() causes
        an appropriate exception to be raised if the response code is
        >= 400.
        """

        self._debug("Sending %r request to %r (body %r, headers %r)",
                    self.method, self.url, self.body, self.headers)

        # Issue the request
        (resp, content) = self.client(self.url, self.method, self.body,
                                      self.headers, self.max_redirects)

        # Save the body in the response
        resp.body = content

        # Do any processing on the response that's desired
        self.proc_response(resp)

        # Return the response
        return resp

    def proc_response(self, resp):
        """Process response hook.

        Process non-redirect responses received by the send() method.
        May augment the response.  The default implementation causes
        an exception to be raised if the response status code is >=
        400.
        """

        # Raise exceptions for error responses
        if resp.status >= 400:
            e = exc.exception_map.get(resp.status, exc.HTTPException)
            self._debug("  Response was a %d fault, raising %s",
                        resp.status, e.__name__)
            raise e(resp)

    def __getitem__(self, item):
        """Allow headers to be retrieved via dictionary access."""

        # Headers are done by item access
        return self.headers[item.title()]

    def __setitem__(self, item, value):
        """Allow headers to be set via dictionary access."""

        # Headers are done by item access
        self.headers[item.title()] = value

    def __delitem__(self, item):
        """Allow headers to be removed via dictionary access."""

        # Headers are done by item access
        del self.headers[item.title()]

    def __contains__(self, item):
        """Allow header presence to be discovered via dictionary access."""

        # Headers are done by item access
        return item.title() in self.headers

    def __len__(self):
        """Obtain the number of headers present on the request."""

        # Headers are done by item access
        return len(self.headers)
