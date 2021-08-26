import requests
import time
from typing import List, Union, Tuple
import logging
from datetime import datetime, timedelta

DEFAULT_EXCEPTIONS = (requests.exceptions.ConnectionError,
                      requests.exceptions.Timeout)
DEFAULT_DELAY = 1
DEFAULT_LIMIT = 10
DEFAULT_CODES = [429] + list(range(500,512))
DEFAULT_EXP_BACKOFF = False
DEFAULT_MAX_EXP_BACKOFF = 60
DEFAULT_LOG_LEVEL = logging.INFO

__all__ = ['SafeRequests',
           'SafeSession',
           'request',
           'get',
           'options',
           'head',
           'post',
           'put',
           'patch',
           'delete',
           'DEFAULT_DELAY',
           'DEFAULT_LIMIT',
           'DEFAULT_CODES',
           'DEFAULT_EXP_BACKOFF',
           'DEFAULT_MAX_EXP_BACKOFF'
           ]

class SafeSession(requests.sessions.Session):
    """
    Create a SafeSession object which wraps requests.sessions.Session.
    The wrapper automatically retries all requests in case of
    failuers according to parameters set.

    Parameters
    ----------
    retry_delay :: float
        delay in seconds between retries
        default - 1

    retry_limit :: int
        maximum number of times a request is retried
        default - 10

    retry_codes :: List[int]
        http response retry_codes on which to force a retry
        default - [429, 501, 502, 503, 504, 505,
                  506, 507, 508, 509, 510, 511]

    exp_backoff :: bool
        boolean indicating if the retry_delay is exponentially increasing
        or constant. If true retry delay doubles with each try to a
        maximum value specified by max_exp_backoff 
        default - False

    max_exp_backoff :: float
        maximum retry_delay in case exp_backoff is set to True
        default - 60

    retry_exception :: bool
        boolean indicating if the request should be retried on certain
        requests.exceptions like requests.exceptions.ConnectionError or
        requests.exceptions.Timeout.

    retry_exception_codes :: Tuple[Exception] or Exception
        A tuple of Exceptions or an Excpetion on which to retry
        Default - (requests.exceptions.ConnectionError,
                   requests.exceptions.Timeout)

    Returns
    -------
    saferequests.SafeSession
        A saferequests.SafeSession which is a simple wrapper of
        requests.sessions.Session.

    Example
    s = SafeSession(retry_delay = 1,retry_limit = 10)
    s.get("https://example.com")
    """
    def __init__(self,
                 retry_delay : float = DEFAULT_DELAY,
                 retry_limit : int =  DEFAULT_LIMIT,
                 retry_codes : List[int] = DEFAULT_CODES,
                 exp_backoff : bool = DEFAULT_EXP_BACKOFF,
                 max_exp_backoff : int = DEFAULT_MAX_EXP_BACKOFF,
                 retry_exception : bool = False,
                 retry_exception_codes : Union[
                     Tuple[Exception], Exception]  = DEFAULT_EXCEPTIONS
                 ):

        self.__retry_delay__ = retry_delay
        self.__retry_limit__ = retry_limit
        self.__retry_codes__ = retry_codes
        self.__exp_backoff__ = exp_backoff
        self.__max_exp_backoff__ = max_exp_backoff
        self.__retry_exception__ = retry_exception
        self.__retry_exception_codes__ = retry_exception_codes
        super().__init__()

    def __repr__(self):
        return (f'\nSafeSession(\n'
                f'retry_delay={self.retry_delay},\n'
                f'retry_limit={self.retry_limit},\n'
                f'retry_codes={self.retry_codes},\n'
                f'exp_backoff={self.exp_backoff},\n'
                f'max_exp_backoff={self.max_exp_backoff},\n'
                f'retry_exception={self.retry_exception},\n'
                f'retry_exception_codes={self.retry_exception_codes})\n')
                
    @property
    def retry_delay(self):
        return self.__retry_delay__

    @property
    def retry_limit(self):
        return self.__retry_limit__

    @property
    def retry_codes(self):
        return self.__retry_codes__

    @property
    def exp_backoff(self):
        return self.__exp_backoff__

    @property
    def max_exp_backoff(self):
        return self.__max_exp_backoff__

    @property
    def retry_exception(self):
        return self.__retry_exception__

    @property
    def retry_exception_codes(self):
        return self.__retry_exception_codes__
    
    
    def __reduce__(self):
        return (self.__class__,(
            self.__retry_delay__,
            self.__retry_limit__,
            self.__codes__,
            self.__exp_backoff__,
            self.__max_exp_backoff__,
            self.__retry_exception__,
            self.__retry_exception_codes__
            ))
    
    def request(self, method, url, **kwargs):
        """
        Constructs and sends a :class:`Request <Request>`
        but will use parameters defined when object of
        :class:`SafeSession <SafeSession>` is created
        
            :param method: method for the new :class:`Request` object: ``GET``, ``OPTIONS``, ``HEAD``, ``POST``, ``PUT``, ``PATCH``, or ``DELETE``.
            :param url: URL for the new :class:`Request` object.
            :param params: (optional) Dictionary, list of tuples or bytes to send
                in the query string for the :class:`Request`.
            :param data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            :param json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
            :param headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
            :param cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
            :param files: (optional) Dictionary of ``'name': file-like-objects`` (or ``{'name': file-tuple}``) for multipart encoding upload.
                ``file-tuple`` can be a 2-tuple ``('filename', fileobj)``, 3-tuple ``('filename', fileobj, 'content_type')``
                or a 4-tuple ``('filename', fileobj, 'content_type', custom_headers)``, where ``'content-type'`` is a string
                defining the content type of the given file and ``custom_headers`` a dict-like object containing additional headers
                to add for the file.
            :param auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
            :param timeout: (optional) How many seconds to wait for the server to send data
                before giving up, as a float, or a :ref:`(connect timeout, read
                timeout) <timeouts>` tuple.
            :type timeout: float or tuple
            :param allow_redirects: (optional) Boolean. Enable/disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``True``.
            :type allow_redirects: bool
            :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
            :param verify: (optional) Either a boolean, in which case it controls whether we verify
                    the server's TLS certificate, or a string, in which case it must be a path
                    to a CA bundle to use. Defaults to ``True``.
            :param stream: (optional) if ``False``, the response content will be immediately downloaded.
            :param cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
            Usage::
        
              >>> import saferequests
              >>> sf = saferequests.SafeSession(retry_delay=5,retry_limit=5)
              >>> req = sf.get('https://google.com')
              >>> req
              <Response [200]>
        """
        count = self.retry_limit
        retry_delay = self.retry_delay
        url_str = url
        start = datetime.now()
        while count>=0:
            timed_out = False
            timeout_error = None
            try:
                response = super().request(method = method,
                                    url = url,
                                    **kwargs
                                    )
                end = datetime.now()
            except retry_exception_codes as e:
                if self.retry_exception:
                    timed_out = True
                    timeout_error = e
                else:
                    raise e

            if timed_out and count:
                logging.debug(f'{url_str} - '
                              f'connection timedout Retrying')
            elif timed_out and not count:
                logging.debug(f'{url_str} - '
                              f'connection timedout max reties reached')
                raise timeout_error
            elif response.status_code in self.retry_codes and count:
                logging.debug(f'{url_str} - response recieved '
                              f'{response.status_code}. Retrying')
                count = count -1
                time.sleep(retry_delay)
                if self.exp_backoff:
                    retry_delay = min(retry_delay * 2,self.max_exp_backoff)
            
            else:
                logging.log(DEFAULT_LOG_LEVEL,f'{url_str} - response recieved '
                            f'{response.status_code}. '
                            'returning response')
                response.elapsed = end - start
                return response


    def get(self, url, params=None, **kwargs):
        """
        Sends a GET request with retry parameters defined when object of
            :class:`SafeSession <SafeSession>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param params: (optional) Dictionary, list of tuples or bytes to send
                in the query string for the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("get", url, params=params, **kwargs)

    def options(self, url, **kwargs):
        """
        Sends an OPTIONS request with retry parameters defined when object of
            :class:`SafeSession <SafeSession>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("options", url, **kwargs)

    def head(self, url, **kwargs):
        """
        Sends a HEAD request with retry parameters defined when object of
            :class:`SafeSession <SafeSession>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param \*\*kwargs: Optional arguments that ``request`` takes. If
                `allow_redirects` is not provided, it will be set to `False` (as
                opposed to the default :meth:`request` behavior).
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """    
        return self.request("options", url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        """
        Sends a POST request with retry parameters defined when object of
            :class:`SafeSession <SafeSession>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            :param json: (optional) json data to send in the body of the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("post", url, data=data, json=json, **kwargs)
    
    def put(self, url, data=None, **kwargs):
        """
        Sends a PUT request with retry parameters defined when object of
            :class:`SafeSession <SafeSession>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            :param json: (optional) json data to send in the body of the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("put", url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        """
        Sends a PATCH request with retry parameters defined when object of
            :class:`SafeSession <SafeSession>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            :param json: (optional) json data to send in the body of the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("patch", url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        """
        Sends a PATCH request with retry parameters defined when object of
            :class:`SafeSession <SafeSession>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("delete", url, **kwargs)
                 
class SafeRequests:
    """
    Create a SafeRequests object which allows you to make http requests
    with automotic retries based on parameters setup

    Parameters
    ----------
    retry_delay :: float
        delay in seconds between retries
        default - 1

    retry_limit :: int
        maximum number of times a request is retried
        default - 10

    retry_codes :: List[int]
        http response retry_codes on which to force a retry
        default - [429, 501, 502, 503, 504, 505,
                  506, 507, 508, 509, 510, 511]

    exp_backoff :: bool
        boolean indicating if the retry_delay is exponentially increasing
        or constant. If true retry delay doubles with each try to a
        maximum value specified by max_exp_backoff 
        default - False

    max_exp_backoff :: float
        maximum retry_delay in case exp_backoff is set to True
        default - 60

    persistant_params :: dict
        a dictionary represneting parameters which will be persisted in
        all requests made from this object. In case a new param with the
        an existing key is specified during the request, the new param
        will take precedence

    persistant_headers :: dict
        a dictionary represneting headers which will be persisted in
        all requests made from this object. In case a new header with the
        an existing key is specified during the request, the new param
        will take precedence

    persistant_auth
        an auth object which will be passed to all requests made from
        this object. In case a new auth object is passed while make a
        request, the passed object will take precedence

    retry_exception :: bool
        boolean indicating if the request should be retried on certain
        requests.exceptions like requests.exceptions.ConnectionError or
        requests.exceptions.Timeout.

    retry_exception_codes :: Tuple[Exception] or Exception
        A tuple of Exceptions or an Excpetion on which to retry
        Default - (requests.exceptions.ConnectionError,
                   requests.exceptions.Timeout)
    

    Returns
    -------
    saferequests.SafeRequests

    Example
    s = SafeRequests(retry_delay = 1,retry_limit = 10)
    s.get("https://example.com")
    """
    def __init__ (self,
                  retry_delay : int = DEFAULT_DELAY,
                  retry_limit : int =  DEFAULT_LIMIT,
                  retry_codes : List[int] = DEFAULT_CODES,
                  exp_backoff : bool = DEFAULT_EXP_BACKOFF,
                  max_exp_backoff : int = DEFAULT_MAX_EXP_BACKOFF,
                  persistant_params : dict = dict(),
                  persistant_headers : dict = dict(),
                  persistant_auth = None,
                  retry_exception : bool = False,
                  retry_exception_codes : Union[
                     Tuple[Exception], Exception]  = DEFAULT_EXCEPTIONS
                  ):
        self.__retry_delay__ = retry_delay 
        self.__retry_limit__ = retry_limit 
        self.__retry_codes__ = retry_codes or list()
        self.__exp_backoff__ = exp_backoff
        self.__max_exp_backoff__ = max_exp_backoff
        self.__persistant_params__ = persistant_params
        self.__persistant_headers__ = persistant_headers
        self.__persistant_auth__ = persistant_auth
        self.__retry_exception__ = retry_exception
        self.__retry_exception_codes__ = retry_exception_codes

    @property
    def retry_delay(self):
        return self.__retry_delay__

    @property
    def retry_limit(self):
        return self.__retry_limit__

    @property
    def retry_codes(self):
        return self.__retry_codes__

    @property
    def exp_backoff(self):
        return self.__exp_backoff__

    @property
    def max_exp_backoff(self):
        return self.__max_exp_backoff__

    @property
    def persistant_params(self):
        return self.__persistant_params__

    @property
    def persistant_headers(self):
        return self.__persistant_headers__

    @property
    def persistant_auth(self):
        return self.__persistant_auth__

    @property
    def retry_exception(self):
        return self.__retry_exception__

    @property
    def retry_exception_codes(self):
        return self.__retry_exception_codes__
    
    def __repr__(self):
        return (f'\nSafeRequest(\n'
                f'retry_delay={self.retry_delay},\n'
                f'retry_limit={self.retry_limit},\n'
                f'retry_codes={self.retry_codes},\n'
                f'exp_backoff={self.exp_backoff},\n'
                f'persistant_params={self.persistant_params},\n'
                f'persistant_headers={self.persistant_headers},\n'
                f'persistant_auth={self.persistant_auth},\n'
                f'max_exp_backoff={self.max_exp_backoff},\n'
                f'retry_exception={self.retry_exception},\n'
                f'retry_exception_codes={self.retry_exception_codes})\n')

    def __reduce__(self):
        return (self.__class__,(
            self.retry_delay,
            self.retry_limit,
            self.retry_codes,
            self.exp_backoff,
            self.max_exp_backoff,
            self.persistant_params,
            self.persistant_headers,
            self.persistant_auth,
            self.retry_exception,
            self.retry_exception_codes
            ))

    def request(self, method, url, **kwargs):
        """
        Wrapper around the requests.request function which
        Constructs and sends a :class:`Request <Request>`
        but will use parameters defined when object of
        :class:`SafeRequests <SafeRequests>` is created
        
            :param method: method for the new :class:`Request` object: ``GET``, ``OPTIONS``, ``HEAD``, ``POST``, ``PUT``, ``PATCH``, or ``DELETE``.
            :param url: URL for the new :class:`Request` object.
            :param params: (optional) Dictionary, list of tuples or bytes to send
                in the query string for the :class:`Request`.
            :param data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            :param json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
            :param headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
            :param cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
            :param files: (optional) Dictionary of ``'name': file-like-objects`` (or ``{'name': file-tuple}``) for multipart encoding upload.
                ``file-tuple`` can be a 2-tuple ``('filename', fileobj)``, 3-tuple ``('filename', fileobj, 'content_type')``
                or a 4-tuple ``('filename', fileobj, 'content_type', custom_headers)``, where ``'content-type'`` is a string
                defining the content type of the given file and ``custom_headers`` a dict-like object containing additional headers
                to add for the file.
            :param auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
            :param timeout: (optional) How many seconds to wait for the server to send data
                before giving up, as a float, or a :ref:`(connect timeout, read
                timeout) <timeouts>` tuple.
            :type timeout: float or tuple
            :param allow_redirects: (optional) Boolean. Enable/disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``True``.
            :type allow_redirects: bool
            :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
            :param verify: (optional) Either a boolean, in which case it controls whether we verify
                    the server's TLS certificate, or a string, in which case it must be a path
                    to a CA bundle to use. Defaults to ``True``.
            :param stream: (optional) if ``False``, the response content will be immediately downloaded.
            :param cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
            Usage::
        
              >>> import saferequests
              >>> sf = saferequests.SafeRequests(retry_delay=5,retry_limit=5)
              >>> req = sf.get('https://google.com')
              >>> req
              <Response [200]>
        """
        count = self.retry_limit
        retry_delay = self.retry_delay
        url_str = url
        kwargs['params'] = {**self.persistant_params,
                            **kwargs.get('params',dict())}
        kwargs['headers'] = {**self.persistant_headers,
                             **kwargs.get('headers',dict())}
        kwargs.setdefault('auth',self.persistant_auth)
        start = datetime.now()
        while count>=0:
            timed_out = False
            timeout_error = None
            
            try:
                response = requests.request(method = method,
                                    url = url,
                                    **kwargs
                                    )
                end = datetime.now()
            except retry_exception_codes as e:
                if self.retry_exception:
                    timed_out = True
                    timeout_error = e
                else:
                    raise e

            if timed_out and count:
                logging.debug(f'{url_str} - '
                              f'connection timedout Retrying')
            elif timed_out and not count:
                logging.debug(f'{url_str} - '
                              f'connection timedout max reties reached')
                raise timeout_error
            elif response.status_code in self.retry_codes and count:
                logging.debug(f'{url_str} - response recieved '
                              f'{response.status_code}. Retrying')
                count = count -1
                time.sleep(retry_delay)
                if self.exp_backoff:
                    retry_delay = min(retry_delay * 2,self.max_exp_backoff)
            
            else:
                logging.log(DEFAULT_LOG_LEVEL,f'{url_str} - response recieved '
                            f'{response.status_code}. '
                            'returning response')
                r.elapsed = end - start
                return response
    
    def get(self, url, params=None, **kwargs):
        """
        Sends a GET request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param params: (optional) Dictionary, list of tuples or bytes to send
                in the query string for the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("get", url, params=params, **kwargs)

    def options(self, url, **kwargs):
        """
        Sends an OPTIONS request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("options", url, **kwargs)

    def head(self, url, **kwargs):
        """
        Sends a HEAD request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param \*\*kwargs: Optional arguments that ``request`` takes. If
                `allow_redirects` is not provided, it will be set to `False` (as
                opposed to the default :meth:`request` behavior).
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """    
        return self.request("options", url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        """
        Sends a POST request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            :param json: (optional) json data to send in the body of the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("post", url, data=data, json=json, **kwargs)
    
    def put(self, url, data=None, **kwargs):
        """
        Sends a PUT request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            :param json: (optional) json data to send in the body of the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("put", url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        """
        Sends a PATCH request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param data: (optional) Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            :param json: (optional) json data to send in the body of the :class:`Request`.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("patch", url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        """
        Sends a PATCH request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        
            :param url: URL for the new :class:`Request` object.
            :param \*\*kwargs: Optional arguments that ``request`` takes.
            :return: :class:`Response <Response>` object
            :rtype: requests.Response
        """
        return self.request("delete", url, **kwargs)
    

root = SafeRequests()

def request(method, url, **kwargs):
    """
    Wrapper around the requests.request function which
    Constructs and sends a :class:`Request <Request>`
    but will use default retry options
    
        :param method: method for the new :class:`Request` object: ``GET``, ``OPTIONS``, ``HEAD``, ``POST``, ``PUT``, ``PATCH``, or ``DELETE``.
        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) A JSON serializable Python object to send in the body of the :class:`Request`.
        :param headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
        :param cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
        :param files: (optional) Dictionary of ``'name': file-like-objects`` (or ``{'name': file-tuple}``) for multipart encoding upload.
            ``file-tuple`` can be a 2-tuple ``('filename', fileobj)``, 3-tuple ``('filename', fileobj, 'content_type')``
            or a 4-tuple ``('filename', fileobj, 'content_type', custom_headers)``, where ``'content-type'`` is a string
            defining the content type of the given file and ``custom_headers`` a dict-like object containing additional headers
            to add for the file.
        :param auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
        :param timeout: (optional) How many seconds to wait for the server to send data
            before giving up, as a float, or a :ref:`(connect timeout, read
            timeout) <timeouts>` tuple.
        :type timeout: float or tuple
        :param allow_redirects: (optional) Boolean. Enable/disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection. Defaults to ``True``.
        :type allow_redirects: bool
        :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
        :param verify: (optional) Either a boolean, in which case it controls whether we verify
                the server's TLS certificate, or a string, in which case it must be a path
                to a CA bundle to use. Defaults to ``True``.
        :param stream: (optional) if ``False``, the response content will be immediately downloaded.
        :param cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        Usage::
    
          >>> import saferequests
          >>> req = saferequests.request('GET', 'https://httpbin.org/get')
          >>> req
          <Response [200]>
    """
    return root.request(method=method, url=url, **kwargs)

def get(url, params=None, **kwargs):
    """
    Sends a GET request with default retry params.
    
        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary, list of tuples or bytes to send
            in the query string for the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
    """

    return request('get', url, params=params, **kwargs)


def options(url, **kwargs):
    """
    Sends an OPTIONS request with default retry params.
    
        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
    """
    return request('options', url, **kwargs)

def head(url, **kwargs):
    """
    Sends a HEAD request with default retry params.
    
        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes. If
            `allow_redirects` is not provided, it will be set to `False` (as
            opposed to the default :meth:`request` behavior).
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
    """    
    return request('head', url, **kwargs)


def post(url, data=None, json=None, **kwargs):
    """
    Sends a POST request with default retry params.
    
        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param json: (optional) json data to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
    """
    return request('post', url, data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    """
    Sends a PUT request with default retry params.
    
        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
    """
    return request('put', url, data=data, **kwargs)

def patch(url, data=None, **kwargs):
    """
    Sends a PATCH request with default retry params.
    
        :param url: URL for the new :class:`Request` object.
        :param data: (optional) Dictionary, list of tuples, bytes, or file-like
            object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
    """
    return request('patch', url, data=data, **kwargs)


def delete(url, **kwargs):
    """
    Sends a PATCH request with default retry params.
    
        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
    """
    return request('delete', url, **kwargs)