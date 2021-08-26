# saferequests

**SafeRequests** and **SafeSession** are simple wrappers that make retrying a 
failed http request easier.

```python
>>> import saferequests
>>> sr = saferequests.SafeRequests(retry_delay=1, retry_limit=2, retry_codes=[429])
>>> r = sr.get('https://api.github.com/user', auth=('user', 'pass'))
>>> r.status_code
200
>>> r.headers['content-type']
'application/json; charset=utf8'
>>> r.encoding
'utf-8'
>>> r.text
'{"type":"User"...'
>>> r.json()
{'disk_usage': 368627, 'private_gists': 484, ...}
```

**SafeSession** wraps requests.sessions.Sessions but incorporates an easy to 
use recipie for retrying requests

```python
>>> import saferequests
>>> ss = saferequests.SafeSession(retry_delay=1, retry_limit=2, retry_codes=[429])
>>> r = ss.get('https://api.github.com/user', auth=('user', 'pass'))
>>> r.status_code
200
>>> r.headers['content-type']
'application/json; charset=utf8'
>>> r.encoding
'utf-8'
>>> r.text
'{"type":"User"...'
>>> r.json()
{'disk_usage': 368627, 'private_gists': 484, ...}
```
