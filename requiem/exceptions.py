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
import re


__all__ = ['RESTException', 'HTTPException', 'exception_map']


class RESTException(Exception):
    """Superclass for exceptions from this package."""

    pass


class HTTPException(RESTException):
    """Superclass of exceptions raised if an error status is returned."""

    def __init__(self, response):
        """Initializes exception, attaching response."""

        # Formulate a message from the response
        msg = response.reason

        # Initialize superclass
        super(RESTException, self).__init__(msg)

        # Also attach status code and the response
        self.status = response.status
        self.response = response


# Set up more specific exceptions
exception_map = {}
for _status, _name in httplib.responses.items():
    # Skip non-error codes
    if _status < 400:
        continue

    # Make a valid exception name
    _exname = re.sub(r'\W+', '', _name) + 'Exception'

    # Make a class
    _cls = type(_exname, (HTTPException,),
                {'__doc__': _name, '__module__': __name__})

    # Put it in the right places
    vars()[_exname] = _cls
    exception_map[_status] = _cls

    # Also export it
    __all__.append(_exname)
