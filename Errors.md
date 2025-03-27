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

# Error 2
This bug is a logic error, rather than a problem with the code. Upon both clients connecting, the server does not start the game, but rather, hangs. Client 2 in particular doesn't receive the first sent info array from the server. Something is wrong with the sleep function in the server gameloop.

According to the logging data, both clients are connecting, and have sucessfully sent their names through to the server.

I fixed this by making the server game loop asynchronous, however this caused a new problem by making it so that the server doesn't send messages every 500ms anymore. It doesn't send any more messages.

I fixed all these issues by implementing a queue system (much like the current_log in my pseudocode) that gives the server main loop a list of all the users connected, instead of the list being empty when the process forked.

I also moved the generation of the initial game frame to main game loop. Now the game runs smoothly.

# Error 3
```
json.decoder.JSONDecodeError: Extra data: line 1 column 161 (char 160)
```
This error was a runtime error. It happened due to how in the TCP protocol, a sending of a buffer of 4096 bytes is not equal to the receiving of a buffer of 4096 bytes. This means that one socket receive could include multiple socket message sends.

There are two main ways to solve such an error.
1. Including the message length as a prefix to the message
2. Separating each message with a delimiter.

I went with the second option, as it is a quick and dirty fix, that works fine for my purposes.

# Error 4
This was another logic error. It was found through running the game and observing output. In this error, the output of the road was not being drawn properly, instead, with overlapping emojis and lines cut off two characters in.

After fiddling with different methods of printing and ANSI escape codes, I realised that it was due to how my carriage return signals in the terminal were sending the cursor back to the start of the previous line, instead of the same y-position of the cursor on the previous line, when I was trying to get the borders of the road drawn in.

I fixed this by solidfying my lane markers as their own print statements before and after the lines are generated and drawn, and in the process, making the lane marker generation responsive to changes in the column and row variables.

# Error 5
This was another logic error. The game was freezing in the middle of playtime due to no reason, and in the server logs, the server was receiving key inputs, but wasn't sending new game frames to the clients.