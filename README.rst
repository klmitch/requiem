=========================================
Straight-forward REST client construction
=========================================

This package provides a simple mechanism for constructing clients for
REST-based services.  Every client extends the RESTClient class, and
every method which hits the REST service is decorated with the
@restmethod() decorator.  The @restmethod() decorator causes the
decorated method to be passed an additional argument (after the "self"
argument): an HTTPRequest object.  The method may then manipulate
request headers and the body of the request, then use the send()
method on the HTTPRequest object to issue the request.  The return
value of the send() method will be an httplib.HTTPResponse object,
which can then be interpreted.  If the response is a redirection, the
redirection will be followed; if the response is an error (status code
400 or greater), an exception is raised.

JSON-based Clients
==================

The rest package also includes the rest.jsclient module, which
provides a JSONClient class geared toward those REST services which
use JSON-encoded data.  An additional _attach_obj() method is provided
for JSONClient, and responses have any available valid JSON decoded
and placed in the ``obj`` attribute of the response.  (The ``body``
attribute of the response is additionally set to the content of the
response, whether or not it is valid JSON.)
