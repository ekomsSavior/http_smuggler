import re
from urllib.parse import urlparse

STATUS_RE = re.compile(rb'^HTTP/\d\.\d (\d{3})')
HDR_RE = re.compile(rb'^(.*?):\s*(.*)$', re.I | re.M)

def parse_status_and_headers(raw_bytes):
    head, _, _ = raw_bytes.partition(b"\r\n\r\n")
    m = STATUS_RE.match(head.split(b"\r\n", 1)[0])
    status = int(m.group(1)) if m else None
    headers = {}
    for line in head.split(b"\r\n")[1:]:
        mh = HDR_RE.match(line)
        if mh:
            k = mh.group(1).decode('latin-1', 'ignore').lower()
            v = mh.group(2).decode('latin-1', 'ignore')
            headers.setdefault(k, []).append(v)
    return status, headers

def get_header(headers, name):
    return headers.get(name.lower(), [])

def extract_set_cookies(headers):
    return get_header(headers, 'set-cookie')

def normalize_target(target):
    p = urlparse(target)
    if p.scheme not in ('http', ''):
        raise ValueError("HTTP only")
    host = p.hostname or target.replace('http://','').split('/')[0]
    port = p.port or 80
    return host, port

def ensure_crlf(s):
    # normalize any stray \n to CRLF blocks
    s = s.replace("\r\n","\n").replace("\r","\n")
    return s.replace("\n","\r\n")
