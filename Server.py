import socket as sock
import multiprocessing as mp
import selectors

sel = selectors.DefaultSelector()

def accept(sock, mask):
    conn, addr = sock.accept()  # Should be ready
    print('accepted', conn, 'from', addr)
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn: sock.SocketType, mask):
    data = conn.recv(1000)  # Should be ready
    if data:
        print('echoing', repr(data), 'to', conn)
        conn.send(data)  # Hope it won't block
    else:
        print('closing', conn)
        sel.unregister(conn)
        conn.close()

def Server(sock: sock.SocketType):
    sel.register(sock, selectors.EVENT_READ, accept)
    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)

def CreateNewServer(port):
    serversocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    serversocket.setblocking(False)
    serversocket.bind(('', port))
    serversocket.listen(5)
    print("Server created on port " + str(port) + ".")

    server_process = mp.Process(target=Server, args=(serversocket,))
    server_process.start()