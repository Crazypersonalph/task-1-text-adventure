import socket as sock
import multiprocessing as mp
import selectors

import logging
import json
import numpy as np
import os
import time
import random

import classes.NumpyEncoder as NumpyEncoder

ROWS, COLS = 5, 10
CAR_SYMBOL, OBSTACLE_SYMBOL, EMPTY_SYMBOL = 1, 2, 0
grid = np.full((ROWS, COLS), EMPTY_SYMBOL, dtype=int)
grid[1, 0] = CAR_SYMBOL

executed = False

users = []


logger = logging.getLogger(__name__)
logging.basicConfig(filename='server.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

sel = selectors.DefaultSelector()

def start_game():
    while True:
        start_time = time.time()

        grid[:, :-1] = grid[:, 1:]
        grid[random.randint(0,ROWS-1), -1] = random.choice([0,0,0,2])

        user: dict
        for user in users:
            user[1].sendall(json.dumps(grid, cls=NumpyEncoder.NumpyEncoder).encode("utf-8"))
        execution_time = time.time() - start_time
        time.sleep(1 - execution_time)

def accept(sock: sock.SocketType, mask):
    conn, addr = sock.accept()  # Should be ready

    logger.info('[SERVER] Accepted %s from %s', conn, addr)

    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn: sock.SocketType, mask):
    data = conn.recv(1024)
    if data:
        logger.info('[SERVER] Received %s from %s', repr(data), conn)
        if data.decode("utf-8").startswith("INIT"):
            users.append([data.decode("utf-8")[4:], conn])

        conn.sendall(json.dumps(grid, cls=NumpyEncoder.NumpyEncoder).encode("utf-8"))
    else:
        logger.warning('[SERVER] closing %s', conn)

        sel.unregister(conn)
        conn.close()


def Server(sock: sock.SocketType):
    sel.register(sock, selectors.EVENT_READ, accept)
    while True:
        global executed
        if users.__len__() == 2 and executed == False:
            executed = True
            start_game()
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)


def CreateNewServer(port):
    serversocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    serversocket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
    serversocket.setblocking(False)
    serversocket.bind(('', port))
    serversocket.listen(5)

    logger.info("Server created on port %s.", str(port))

    server_process = mp.Process(target=Server, args=(serversocket,))
    server_process.start()