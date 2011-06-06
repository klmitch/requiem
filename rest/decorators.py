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

import functools
import inspect
import urllib
import urlparse

from rest import headers as hdrs


__all__ = ['restmethod']


# Custom version of inspect.getcallargs().  We need this because:
#
# 1. inspect.getcallargs() does not exist prior to Python 2.7.
#
# 2. We need to inject an argument for request objects, and make it
#    accessible to our caller.
#
# 3. We need to additionally return the object the method is acting
#    on.  (This function only works on methods.)
#
# Note that this implementation is largely copied straight from Python
# 2.7 inspect.py, with the addition of a few comments and the changes
# in behavior noted above.
def _getcallargs(func, positional, named):
    """Get the mapping of arguments to values.

    Generates a dict, with keys being the function argument names
    (including the names of the * and ** arguments, if any), and
    values the respective bound values from 'positional' and 'named'.
    A parameter for the request is injected.  Returns a tuple of the
    dict, the object the method is being called on, and the name of
    the injected request argument.
    """

    args, varargs, varkw, defaults = inspect.getargspec(func)
    f_name = func.__name__
    arg2value = {}

    # The following closures are basically because of tuple parameter
    # unpacking.
    assigned_tuple_params = []

    def assign(arg, value):
        if isinstance(arg, str):
            arg2value[arg] = value
        else:
            assigned_tuple_params.append(arg)
            value = iter(value)
            for i, subarg in enumerate(arg):
                try:
                    subvalue = next(value)
                except StopIteration:
                    raise ValueError('need more than %d %s to unpack' %
                                     (i, 'values' if i > 1 else 'value'))
                assign(subarg, subvalue)
            try:
                next(value)
            except StopIteration:
                pass
            else:
                raise ValueError('too many values to unpack')

    def is_assigned(arg):
        if isinstance(arg, str):
            return arg in arg2value
        return arg in assigned_tuple_params

    # Inject a place-holder for the request and get the self and the
    # req_name
    positional = positional[:1] + (None,) + positional[1:]
    theSelf = positional[0]
    req_name = args[1]

    num_pos = len(positional)
    num_total = num_pos + len(named)
    num_args = len(args)
    num_defaults = len(defaults) if defaults else 0

    # Start with our positional parameters...
    for arg, value in zip(args, positional):
        assign(arg, value)

    # Deal with the variable argument list...
    if varargs:
        if num_pos > num_args:
            assign(varargs, positional[-(num_pos-num_args):])
        else:
            assign(varargs, ())
    elif 0 < num_args < num_pos:
        raise TypeError('%s() takes %s %d %s (%d given)' % (
            f_name, 'at most' if defaults else 'exactly', num_args,
            'arguments' if num_args > 1 else 'argument', num_total))
    elif num_args == 0 and num_total:
        raise TypeError('%s() takes no arguments (%d given)' %
                        (f_name, num_total))

    # Exclusion rules on keyword arguments
    for arg in args:
        if isinstance(arg, str) and arg in named:
            if is_assigned(arg):
                raise TypeError("%s() got multiple values for keyword "
                                "argument '%s'" % (f_name, arg))
            else:
                assign(arg, named.pop(arg))

    # Fill in any missing values with the defaults
    if defaults:
        for arg, value in zip(args[-num_defaults:], defaults):
            if not is_assigned(arg):
                assign(arg, value)

    # Handle the **names
    if varkw:
        assign(varkw, named)
    elif named:
        unexpected = next(iter(named))
        if isinstance(unexpected, unicode):
            unexpected = unexpected.encode(sys.getdefaultencoding(), 'replace')
        raise TypeError("%s() got an unexpected keyword argument '%s'" %
                        (f_name, unexpected))

    # Anything left over?
    unassigned = num_args - len([arg for arg in args if is_assigned(arg)])
    if unassigned:
        num_required = num_args - num_defaults
        raise TypeError('%s() takes %s %d %s (%d given)' % (
            f_name, 'at least' if defaults else 'exactly', num_required,
            'arguments' if num_required > 1 else 'argument', num_total))

    # Return the mapping and the name of the request argument
    return arg2value, theSelf, req_name


def _urljoin(left, right):
    """Join two URLs.

    Takes URLs specified by left and right and joins them into a
    single URL.  If right is an absolute URL, it is returned directly.
    This differs from urlparse.urljoin() in that the latter always
    chops off the left-most component of left unless it is trailed by
    '/', which is not the behavior we want.
    """

    # Handle the tricky case of right being a full URL
    tmp = urlparse.urlparse(right)
    if tmp.scheme or tmp.netloc:
        # Go ahead and use urlparse.urljoin()
        return urlparse.urljoin(left, right)

    # Check for slashes
    joincond = (left[-1:], right[:1])
    if joincond == ('/', '/'):
        # Too many, preserve only one
        return left + right[1:]
    elif '/' in joincond:
        # Just one; great!
        return left + right
    else:
        # Not enough; add one
        return left + '/' + right


def restmethod(method, reluri, *qargs, **headers):
    """Decorate a method to inject an HTTPRequest.

    Generates an HTTPRequest using the given HTTP method and relative
    URI.  If additional positional arguments are present, they are
    expected to be strings that name function arguments that should be
    included as the query parameters of the URL.  If additional
    keyword arguments are present, the keywords are expected to name
    function arguments and the values are expected to name headers to
    set from those values.  The request is injected as the first
    function argument after the 'self' argument.

    Note that two attributes must exist on the object the method is
    called on: the '_baseurl' attribute specifies the URL that reluri
    is relative to; and the '_make_req' attribute specifies a method
    that instantiates an HTTPRequest from a method and full url (which
    will include query arguments).
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Process the arguments against the original function
            argmap, theSelf, req_name = _getcallargs(func, args, kwargs)

            # Build the URL
            url = _urljoin(theSelf._baseurl, reluri.format(**argmap))

            # Build the query string, as needed
            if qargs:
                query = dict([(k, argmap[k]) for k in qargs
                              if argmap[k] is not None])
                if query:
                    url += '?%s' % urllib.urlencode(query)

            # Build the headers, if needed
            hlist = None
            if headers:
                hlist = hdrs.HeaderDict()
                for aname, hname in headers.items():
                    if argmap[aname]:
                        hlist[hname] = argmap[aname]
                if not hlist:
                    # If there are no headers, don't send any
                    hlist = None

            # Now, build the request and pass it to the method
            argmap[req_name] = theSelf._make_req(method, url, hlist)

            # Call the method
            return func(**argmap)

        # Return the function wrapper
        return wrapper

    # Return the actual decorator
    return decorator
