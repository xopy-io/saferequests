import requests
import time
from typing import List, Union, Tuple
import logging
from datetime import datetime, timedelta
from collections.abc import Mapping
from requests.structures import CaseInsensitiveDict
from urllib.parse import parse_qs, urlparse

DEFAULT_EXCEPTIONS = (requests.exceptions.ConnectionError,
                      requests.exceptions.Timeout)
DEFAULT_DELAY = 1
DEFAULT_LIMIT = 10
DEFAULT_CODES = [429] + list(range(500,512))
DEFAULT_EXP_BACKOFF = False
DEFAULT_MAX_EXP_BACKOFF = 60


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
           ]

def paramstodict(params):
    if isinstance(params,dict):
        return dict(params)
    elif isinstance(params,list):
        return {v[0]:v[1] for v in params}
    elif isinstance(params,(str,bytes)):
        if isinstance(params,bytes):
            decoded = params.decode('utf8')
        else:
            decoded = params

        new_params = dict()
        for k,v in parse_qs(decoded).items():
            if isinstance(v,list) and len(v)==1:
                new_params[k] = v[0]
            else:
                new_params[k] = v
        return new_params
        
def mergesettings(request_setting,persistant_setting,setting_type):
    if not persistant_setting:
        return request_setting
    if not request_setting:
        return persistant_setting
    if setting_type == 'auth':
        return request_setting
    elif setting_type == 'headers':
        merged_settings = CaseInsensitiveDict(persistant_setting)
        merged_settings.update(request_setting)
    elif setting_type == 'params':
        merged_settings = paramstodict(persistant_setting)
        merged_settings.update(paramstodict(request_setting))

    _merged_settings = {k:v for (k, v) in merged_settings.items() if v is not None}
    del merged_settings
    return _merged_settings
                               
            
        
    
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
        parameters
        ----------
            method :: str
                method for the new :class:`Request` object: ``GET``, ``OPTIONS``, ``HEAD``, ``POST``, ``PUT``, ``PATCH``, or ``DELETE``.
            url :: str
                URL for the new :class:`Request` object.
            kwargs
                kwargs accepted by requests.sessions.Session.request
            kwargs accpeted
            ---------------
                params :: (optional)
                    Dictionary, list of tuples or bytes to send
                    in the query string for the :class:`Request`.
                data :: (optional)
                    Dictionary, list of tuples, bytes, or file-like
                    object to send in the body of the :class:`Request`.
                json :: (optional)
                    A JSON serializable Python object to send in the body of the :class:`Request`.
                headers :: (optional)
                    Dictionary of HTTP Headers to send with the :class:`Request`.
                cookies :: (optional)
                    Dict or CookieJar object to send with the :class:`Request`.
                files :: (optional)
                    Dictionary of ``'name': file-like-objects`` (or ``{'name': file-tuple}``) for multipart encoding upload.
                    ``file-tuple`` can be a 2-tuple ``('filename', fileobj)``, 3-tuple ``('filename', fileobj, 'content_type')``
                    or a 4-tuple ``('filename', fileobj, 'content_type', custom_headers)``, where ``'content-type'`` is a string
                    defining the content type of the given file and ``custom_headers`` a dict-like object containing additional headers
                    to add for the file.
                auth :: (optional)
                    Auth tuple to enable Basic/Digest/Custom HTTP Auth.
                timeout :: (optional)
                    How many seconds to wait for the server to send data
                    before giving up, as a float, or a :ref:`(connect timeout, read
                    timeout) <timeouts>` tuple.
                allow_redirects :: (optional)
                    Enable/disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection.
                    Defaults to ``True``.
                proxies :: (optional)
                    Dictionary mapping protocol to the URL of the proxy.
                verify :: (optional)
                    Either a boolean, in which case it controls whether we verify
                    the server's TLS certificate, or a string, in which case it must be a path
                    to a CA bundle to use. Defaults to ``True``.
                stream :: (optional)
                    If ``False``, the response content will be immediately downloaded.
                cert :: (optional)
                    string path to ssl client cert file (.pem) or Tuple ('cert', 'key') pair.
        return
        ------
            class:`Response <Response>` object
        usage
        -----    
            >>> import saferequests
            >>> sf = saferequests.SafeSession(retry_delay=5,retry_limit=5)
            >>> req = sf.get('https://google.com')
            >>> req
            <Response [200]>
        """

        
        count = self.retry_limit
        retry_delay = self.retry_delay
        url_str += '&' if '?' in url_str else '?'
        joiner = []
        for k,v in kwargs['params'].items():
            if isinstance(v,(list,tuple)):
                for vv in v:
                    joiner.append(f'{k}={vv}')
            else:
                joiner.append(f'{k}={v}')
        url_str += '&'.join(joiner)
        del joiner
        
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
                logging.debug(f'{response.request.url} - response recieved '
                              f'{response.status_code}. Retrying')
                count = count -1
                time.sleep(retry_delay)
                if self.exp_backoff:
                    retry_delay = min(retry_delay * 2,self.max_exp_backoff)
            
            else:
                response.elapsed = end - start
                logging.info(f'{response.request.url} - '
                             f'response_status  {response.status_code}. In '
                             f'{response.elapsed.total_seconds():.2f} seconds')
                return response


    def get(self, url, params=None, **kwargs):
        """
        Sends a GET request with retry parameters defined when object of
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            params :: (optional)
                Dictionary, list of tuples or bytes to send
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("get", url, params=params, **kwargs)

    def options(self, url, **kwargs):
        """
        Sends an OPTIONS request with retry parameters defined when object of
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("options", url, **kwargs)

    def head(self, url, **kwargs):
        """
        Sends a HEAD request with retry parameters defined when object of
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """    
        return self.request("options", url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        """
        Sends a POST request with retry parameters defined when object of
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            data :: (optional)
                Dictionary, list of tuples, bytes, or file-like
            json :: (optional)
                json data to send in the body of the :class:`Request`.
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("post", url, data=data, json=json, **kwargs)
    
    def put(self, url, data=None, **kwargs):
        """
        Sends a PUT request with retry parameters defined when object of
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            data :: (optional)
                Dictionary, list of tuples, bytes, or file-like
            json :: (optional)
                json data to send in the body of the :class:`Request`.
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("put", url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        """
        Sends a PATCH request with retry parameters defined when object of
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            data :: (optional)
                Dictionary, list of tuples, bytes, or file-like
            json :: (optional)
                json data to send in the body of the :class:`Request`.
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("patch", url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        """
        Sends a PATCH request with retry parameters defined when object of
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
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
                  persistant_params : Union[
                      dict,List[Tuple],str,bytes] = dict(),
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
        self.__persistant_params__ = persistant_params or dict()
        self.__persistant_headers__ = persistant_headers or dict()
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
        
        parameters
        ----------
            method :: str
                method for the new :class:`Request` object: ``GET``, ``OPTIONS``, ``HEAD``, ``POST``, ``PUT``, ``PATCH``, or ``DELETE``.
            url :: str
                URL for the new :class:`Request` object.
            kwargs
                kwargs accepted by requests.sessions.Session.request
            kwargs accpeted
            ---------------
                params :: dict (optional)
                    Dictionary, list of tuples or bytes to send
                    in the query string for the :class:`Request`.
                data :: (optional)
                    Dictionary, list of tuples, bytes, or file-like
                    object to send in the body of the :class:`Request`.
                json ::  dict (optional)
                    A JSON serializable Python object to send in the body of the :class:`Request`.
                headers :: (optional)
                    Dictionary of HTTP Headers to send with the :class:`Request`.
                cookies :: (optional)
                    Dict or CookieJar object to send with the :class:`Request`.
                files :: (optional)
                    Dictionary of ``'name': file-like-objects`` (or ``{'name': file-tuple}``) for multipart encoding upload.
                    ``file-tuple`` can be a 2-tuple ``('filename', fileobj)``, 3-tuple ``('filename', fileobj, 'content_type')``
                    or a 4-tuple ``('filename', fileobj, 'content_type', custom_headers)``, where ``'content-type'`` is a string
                    defining the content type of the given file and ``custom_headers`` a dict-like object containing additional headers
                    to add for the file.
                auth :: (optional)
                    Auth tuple to enable Basic/Digest/Custom HTTP Auth.
                timeout :: Union[float,tuple] (optional)
                    How many seconds to wait for the server to send data
                    before giving up, as a float, or a :ref:`(connect timeout, read
                    timeout) <timeouts>` tuple.
                allow_redirects :: bool (optional)
                    Enable/disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection.
                    Defaults to ``True``.
                proxies :: dict (optional)
                    Dictionary mapping protocol to the URL of the proxy.
                verify :: Union[bool,str] (optional)
                    Either a boolean, in which case it controls whether we verify
                    the server's TLS certificate, or a string, in which case it must be a path
                    to a CA bundle to use. Defaults to ``True``.
                stream :: bool (optional)
                    If ``False``, the response content will be immediately downloaded.
                cert :: Union[str,tuple] (optional)
                    string path to ssl client cert file (.pem) or Tuple ('cert', 'key') pair.
        return
        ------
            class:`Response <Response>` object

        usage
        -----
            >>> import saferequests
            >>> sf = saferequests.SafeRequests(retry_delay=5,retry_limit=5)
            >>> req = sf.get('https://google.com')
            >>> req
            <Response [200]>
        """
        count = self.retry_limit
        retry_delay = self.retry_delay
        url_str = url
        
        kwargs['params'] = mergesettings(kwargs.get('params',dict()),
                                          self.persistant_params,
                                          'params')
        kwargs['headers'] = mergesettings(kwargs.get('headers',dict()),
                                          self.persistant_headers,
                                          'headers')
        kwargs.setdefault('auth',self.persistant_auth)
        start = datetime.now()
        url_str += '&' if '?' in url_str else '?'
        joiner = []
        for k,v in kwargs['params'].items():
            if isinstance(v,(list,tuple)):
                for vv in v:
                    joiner.append(f'{k}={vv}')
            else:
                joiner.append(f'{k}={v}')
        url_str += '&'.join(joiner)
        del joiner        
        while count>=0:
            timed_out = False
            timeout_error = None
            
            try:
                response = requests.request(method = method,
                                    url = url,
                                    **kwargs
                                    )
                url_str = response.request.url
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
                logging.debug(f'{response.request.url} - response recieved '
                              f'{response.status_code}. Retrying')
                count = count -1
                time.sleep(retry_delay)
                if self.exp_backoff:
                    retry_delay = min(retry_delay * 2,self.max_exp_backoff)
            
            else:
                response.elapsed = end - start
                logging.info(f'{response.request.url} - '
                             f'response_status  {response.status_code}. In '
                             f'{response.elapsed.total_seconds():.2f} seconds')
                return response
    
    def get(self, url, params=None, **kwargs):
        """
        Sends a GET request using retry parameters defined as object of
        :class:`SafeRequests <SafeRequests>` is created
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            params :: (optional)
                Dictionary, list of tuples or bytes to send
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("get", url, params=params, **kwargs)

    def options(self, url, **kwargs):
        """
        Sends an OPTIONS request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("options", url, **kwargs)

    def head(self, url, **kwargs):
        """
        Sends a HEAD request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            params :: (optional)
                Dictionary, list of tuples or bytes to send
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("options", url, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        """
        Sends a POST request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            data :: (optional)
                Dictionary, list of tuples, bytes, or file-like
            json :: (optional)
                json data to send in the body of the :class:`Request`.
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("post", url, data=data, json=json, **kwargs)
    
    def put(self, url, data=None, **kwargs):
        """
        Sends a PUT request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            data :: (optional)
                Dictionary, list of tuples, bytes, or file-like
            json :: (optional)
                json data to send in the body of the :class:`Request`.
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("put", url, data=data, **kwargs)

    def patch(self, url, data=None, **kwargs):
        """
        Sends a PATCH request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            data :: (optional)
                Dictionary, list of tuples, bytes, or file-like
            json :: (optional)
                json data to send in the body of the :class:`Request`.
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("patch", url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        """
        Sends a PATCH request with retry parameters defined when object of
            :class:`SafeRequests <SafeRequests>` is created
        parameters
        ----------
            url :: str
                URL for the new :class:`Request` object.
            \*\*kwargs :: (optional)
                Optional arguments that ``request`` takes.
        return
        ------
            `Response <Response>` object
        """
        return self.request("delete", url, **kwargs)
    

SafeRequests.root = SafeRequests()

def request(method, url, **kwargs):
    """
    Wrapper around the requests.request function which
    Constructs and sends a :class:`Request <Request>`
    but will use default retry options using root object
    SafeRequests.root
    
    parameters
    ----------
        method :: str
            method for the new :class:`Request` object: ``GET``, ``OPTIONS``, ``HEAD``, ``POST``, ``PUT``, ``PATCH``, or ``DELETE``.
        url :: str
            URL for the new :class:`Request` object.
        kwargs
            kwargs accepted by requests.sessions.Session.request
        kwargs accpeted
        ---------------
            params :: dict (optional)
                Dictionary, list of tuples or bytes to send
                in the query string for the :class:`Request`.
            data :: (optional)
                Dictionary, list of tuples, bytes, or file-like
                object to send in the body of the :class:`Request`.
            json ::  dict (optional)
                A JSON serializable Python object to send in the body of the :class:`Request`.
            headers :: (optional)
                Dictionary of HTTP Headers to send with the :class:`Request`.
            cookies :: (optional)
                Dict or CookieJar object to send with the :class:`Request`.
            files :: (optional)
                Dictionary of ``'name': file-like-objects`` (or ``{'name': file-tuple}``) for multipart encoding upload.
                ``file-tuple`` can be a 2-tuple ``('filename', fileobj)``, 3-tuple ``('filename', fileobj, 'content_type')``
                or a 4-tuple ``('filename', fileobj, 'content_type', custom_headers)``, where ``'content-type'`` is a string
                defining the content type of the given file and ``custom_headers`` a dict-like object containing additional headers
                to add for the file.
            auth :: (optional)
                Auth tuple to enable Basic/Digest/Custom HTTP Auth.
            timeout :: Union[float,tuple] (optional)
                How many seconds to wait for the server to send data
                before giving up, as a float, or a :ref:`(connect timeout, read
                timeout) <timeouts>` tuple.
            allow_redirects :: bool (optional)
                Enable/disable GET/OPTIONS/POST/PUT/PATCH/DELETE/HEAD redirection.
                Defaults to ``True``.
            proxies :: dict (optional)
                Dictionary mapping protocol to the URL of the proxy.
            verify :: Union[bool,str] (optional)
                Either a boolean, in which case it controls whether we verify
                the server's TLS certificate, or a string, in which case it must be a path
                to a CA bundle to use. Defaults to ``True``.
            stream :: bool (optional)
                If ``False``, the response content will be immediately downloaded.
            cert :: Union[str,tuple] (optional)
                string path to ssl client cert file (.pem) or Tuple ('cert', 'key') pair.
    return
    ------
        class:`Response <Response>` object
    usage
    -----
        >>> import saferequests
        >>> req = saferequests.request('GET', 'https://httpbin.org/get')
        >>> req
       <Response [200]>
    """
    return root.request(method=method, url=url, **kwargs)

def get(url, params=None, **kwargs):
    """
    Sends a GET request with default retry params using root object
    SafeRequests.root.
    parameters
    ----------
        url :: str
            URL for the new :class:`Request` object.
        params :: (optional)
            Dictionary, list of tuples or bytes to send
        \*\*kwargs :: (optional)
            Optional arguments that ``request`` takes.
    return
    ------
        `Response <Response>` object
    """

    return request('get', url, params=params, **kwargs)


def options(url, **kwargs):
    """
    Sends an OPTIONS request with default retry params using root object
    SafeRequests.root.
    parameters
    ----------
        url :: str
            URL for the new :class:`Request` object.
        \*\*kwargs :: (optional)
            Optional arguments that ``request`` takes.
    return
    ------
        `Response <Response>` object
    """
    return request('options', url, **kwargs)

def head(url, **kwargs):
    """
    Sends a HEAD request with default retry params using root object
    SafeRequests.root.
    parameters
    ----------
        url :: str
            URL for the new :class:`Request` object.
        \*\*kwargs :: (optional)
            Optional arguments that ``request`` takes.
    return
    ------
        `Response <Response>` object
    """    
    return request('head', url, **kwargs)


def post(url, data=None, json=None, **kwargs):
    """
    Sends a POST request with default retry params using root object
    SafeRequests.root.
    parameters
    ----------
        url :: str
            URL for the new :class:`Request` object.
        data :: (optional)
            Dictionary, list of tuples, bytes, or file-like
        json :: (optional)
            json data to send in the body of the :class:`Request`.
        \*\*kwargs :: (optional)
            Optional arguments that ``request`` takes.
    return
    ------
        `Response <Response>` object
    """
    return request('post', url, data=data, json=json, **kwargs)


def put(url, data=None, **kwargs):
    """
    Sends a PUT request with default retry params using root object
    SafeRequests.root.
    parameters
    ----------
        url :: str
            URL for the new :class:`Request` object.
        data :: (optional)
            Dictionary, list of tuples, bytes, or file-like
        json :: (optional)
            json data to send in the body of the :class:`Request`.
        \*\*kwargs :: (optional)
            Optional arguments that ``request`` takes.
    return
    ------
        `Response <Response>` object
    """
    return request('put', url, data=data, **kwargs)

def patch(url, data=None, **kwargs):
    """
    Sends a PATCH request with default retry params using root object
    SafeRequests.root.
    parameters
    ----------
        url :: str
            URL for the new :class:`Request` object.
        data :: (optional)
            Dictionary, list of tuples, bytes, or file-like
        json :: (optional)
            json data to send in the body of the :class:`Request`.
        \*\*kwargs :: (optional)
            Optional arguments that ``request`` takes.
    return
    ------
        `Response <Response>` object
    """
    return request('patch', url, data=data, **kwargs)


def delete(url, **kwargs):
    """
    Sends a PATCH request with default retry params using root object
    SafeRequests.root.
    parameters
    ----------
        url :: str
            URL for the new :class:`Request` object.
        \*\*kwargs :: (optional)
            Optional arguments that ``request`` takes.
    return
    ------
        `Response <Response>` object
    """
    return request('delete', url, **kwargs)
