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

import httplib
import urlparse

from requiem import exceptions as exc
from requiem import headers as hdrs


__all__ = ['HTTPRequest']


class HTTPRequest(object):
    """Represent and perform HTTP requests.

    Implements the dictionary access protocol to modify headers
    (headers can also be accessed directly at the 'headers' attribute)
    and the stream protocol to build up the body.  Handles
    redirections under control of the class attribute 'max_redirects'.
    Understands the 'http' and 'https' schemes; additional schemes can
    be supported by adding them to the 'schemes' dictionary--values
    should be callables that take a network location ("host:port") and
    return an object compatible with httplib.HTTPConnection.
    """

    _connect_cache = {}

    max_redirects = 10
    schemes = {
        'http': httplib.HTTPConnection,
        'https': httplib.HTTPSConnection,
        }

    @classmethod
    def _open(cls, scheme, netloc):
        """Open a connection using specified scheme and netloc."""

        # See if this connection is already present
        if (scheme, netloc) in cls._connect_cache:
            return cls._connect_cache[(scheme, netloc)]

        # Open a connection for the given scheme and netloc
        connect = cls.schemes[scheme](netloc)

        # Cache the connection and return it
        cls._connect_cache[(scheme, netloc)] = connect
        return connect

    def __init__(self, method, url, body=None, headers=None, debug=None):
        """Initialize a request.

        The method and url must be specified.  The body and headers
        are optional, and may be manipulated after instantiating the
        object.
        """

        # Save the relevant data
        self.method = method.upper()
        self.url = url
        self.body = body or ''
        self.headers = hdrs.HeaderDict()
        self._debug = debug or (lambda *args, **kwargs: None)

        # Set up the headers...
        if headers:
            self.headers.update(headers)

        # Split up the URL for later use
        tmp = urlparse.urlparse(url)

        # Save scheme and netloc
        self.scheme = tmp.scheme
        self.netloc = tmp.netloc

        # Now determine just the path
        self.path = urlparse.urlunparse((None, None) + tmp[2:])

        self._debug("Initialized %r request for %r (%r)",
                    self.scheme, self.netloc, self.path)

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

        Handles redirects 301, 302, 303, and 307, if encountered.
        Returns an httplib.HTTPResponse, which may be augmented by the
        proc_response() method.  If a redirect loop is encountered, a
        RESTException is raised.

        Note that the default implementation of proc_response() causes
        an appropriate exception to be raised if the response code is
        >= 400.
        """

        self._debug("Sending %r request to %r (body %r, headers %r)",
                    self.method, self.url, self.body, self.headers)

        # Get the basic initial information we need
        connect = self._open(self.scheme, self.netloc)
        path = self.path
        url = self.url

        # Watch out for looping redirects
        seen = set([url])

        # Now, loop for redirection handling
        for i in range(self.max_redirects):
            self._debug("  Trying %r...", url)

            # Make the request
            connect.request(self.method, path, self.body, self.headers)

            # Get the response
            resp = connect.getresponse()

            # Is the response a redirection?
            newurl = None
            if resp.status in (301, 302, 303, 307):
                # Find the forwarding header...
                if 'location' in resp.msg:
                    newurl = resp.getheader('location')
                elif 'uri' in resp.msg:
                    newurl = resp.getheader('uri')

            # Process the redirection
            if newurl is not None:
                # Canonicalize the URL
                url = urlparse.urljoin(url, newurl)

                self._debug("  Redirected to %s", url)

                # Have we seen it before?
                if url in seen:
                    self._debug("    Redirection already seen!")
                    break

                # Well, now we have...
                seen.add(url)

                # Get the path part of the URL
                tmp = urlparse.urlparse(url)
                path = urlparse.urlunparse((None, None) + tmp[2:])

                # Get the connection
                connect = self._open(tmp.scheme, tmp.netloc)

                # Try the request again
                continue

            self._debug("  Received %d response (%r)", resp.status,
                        resp.reason)

            # Suck in the body, so we'll be able to re-use this
            # connection
            resp.body = resp.read()

            # Do any processing on the response that's desired
            self.proc_response(resp)

            # Return the response
            return resp

        # Exceeded the maximum number of redirects
        self._debug("  Redirect loop detected")
        raise exc.RESTException("Redirect loop detected")

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
