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

import sys

from requiem import exceptions as exc


__all__ = ['Processor']


class Processor(object):
    """
    Class for pre-processing requests and post-processing responses
    and exceptions.  It is not necessary for processors to inherit
    from this class.
    """

    def proc_request(self, req):
        """
        Pre-processes requests.  The req object may be modified--in
        place--in any way.  May return a response object to
        short-circuit other request processing, including submission.
        """

        pass

    def proc_response(self, resp):
        """
        Post-processes responses.  The resp object may be modified--in
        place--in any way.  Return values are ignored.
        """

        pass

    def proc_exception(self, exc_type, exc_value, traceback):
        """
        Post-processes exceptions.  May return a response to halt
        exception processing.
        """

        pass


def _safe_call(obj, methname, *args, **kwargs):
    """
    Safely calls the method with the given methname on the given
    object.  Remaining positional and keyword arguments are passed to
    the method.  The return value is None, if the method is not
    available, or the return value of the method.
    """

    meth = getattr(obj, methname, None)
    if meth is None or not callable(meth):
        return

    return meth(*args, **kwargs)


class ProcessorStack(list):
    """
    A list subclass for processor stacks, defining three
    domain-specific methods: proc_request(), proc_response(), and
    proc_exception().
    """

    def proc_request(self, req):
        """
        Pre-process a request through all processors in the stack, in
        order.  If any processor's proc_request() method returns a
        value other than None, that value is treated as a response and
        post-processed through the proc_response() methods of the
        processors preceding that processor in the stack.  (Note that
        the response returned this way is not passed to the
        processor's proc_response() method.)  Such a response will
        then be attached to a ShortCircuit exception.

        For convenience, returns the request passed to the method.
        """

        for idx in range(len(self)):
            resp = _safe_call(self[idx], 'proc_request', req)

            # Do we have a response?
            if resp is not None:
                # Short-circuit
                raise exc.ShortCircuit(self.proc_response(resp, idx - 1))

        # Return the request we were passed
        return req

    def proc_response(self, resp, startidx=None):
        """
        Post-process a response through all processors in the stack,
        in reverse order.  For convenience, returns the response
        passed to the method.

        The startidx argument is an internal interface only used by
        the proc_request() and proc_exception() methods to process a
        response through a subset of response processors.
        """

        # If we're empty, bail out early
        if not self:
            return resp

        # Select appropriate starting index
        if startidx is None:
            startidx = len(self)

        for idx in range(startidx, -1, -1):
            _safe_call(self[idx], 'proc_response', resp)

        # Return the response we were passed
        return resp

    def proc_exception(self, exc_type, exc_value, traceback):
        """
        Post-process an exception through all processors in the stack,
        in reverse order.  The exception so post-processed is any
        exception raised by the Request object's proc_response()
        method; if the httplib2.Http raises an exception, that
        exception will not be processed by this mechanism.

        Exception processors may return a response object to preempt
        exception processing.  The response object will be
        post-processed with the proc_response() method on the
        remaining processors in the stack.

        Note that, if the exception has a 'response' attribute, each
        processor's proc_response() method will be called on it prior
        to calling proc_exception().

        The return value will be None if the exception was not
        handled, or a response object returned by one of the
        processors.
        """

        # If we're empty, bail out early
        if not self:
            return

        for idx in range(len(self), -1, -1):
            # First, process the response...
            if hasattr(exc_value, 'response'):
                _safe_call(self[idx], 'proc_response', exc_value.response)

            resp = _safe_call(self[idx], 'proc_exception',
                              exc_type, exc_value, traceback)

            # If we have a response, finish processing and return it
            if resp:
                return self.proc_response(resp, idx - 1)
