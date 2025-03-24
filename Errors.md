# Error 1
`ConnectionAbortedError: [WinError 10053] An established connection was aborted by the software in your host machine`
This error means that the connection between the client and the server was prematurely closed by the client.
The error was caused in the server, and per the traceback, and can be linked to the function in which data is read.

According the logging data, the server has successfully received and logged information. This indicates that the error perhaps might be occurring due to the socket being closed incorrectly. However, in the logs, nothing indicates the socket being closed by any code I have written.

Excerpt of logging:
```
2025-03-23 19:34:31 INFO Server created on port 6089.
2025-03-23 19:34:31 INFO [SERVER] Accepted <socket.socket fd=508, family=2, type=1, proto=0, laddr=('127.0.0.1', 6089), raddr=('127.0.0.1', 61652)> from ('127.0.0.1', 61652)
2025-03-23 19:34:31 INFO [SERVER] Received b'Alphons' from <socket.socket fd=508, family=2, type=1, proto=0, laddr=('127.0.0.1', 6089), raddr=('127.0.0.1', 61652)>
```

### Fix
After a bit of thinking and reading the Python sockets documentation, I realised that for the connection to be maintained, the client must run a `while True:` loop to keep listening for data. If it stops listening for data, then the connection is prematurely closed.