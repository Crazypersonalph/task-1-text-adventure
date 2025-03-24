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

executed = False

users = []

current_user_input = [0, 0]


logger = logging.getLogger(__name__)
logging.basicConfig(filename='server.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

sel = selectors.DefaultSelector()

def start_game(queue: mp.Queue, keyQueue: mp.Queue):
    grid = np.full((ROWS, COLS), EMPTY_SYMBOL, dtype=int)
    grid[1, 0] = CAR_SYMBOL
    
    users = queue.get()

    while True:

        grid[:, :-1] = grid[:, 1:]
        grid[random.randint(0,ROWS-1), -1] = random.choice([0,0,0,2])

        
        if keyQueue.qsize() > 0:
            print(keyQueue.get_nowait())

        """
        if current_user_input[0] == 1 and current_user_input[1] == 1:
            print("up")
        elif current_user_input[0] == 2 and current_user_input[1] == 2:
            print("down")"
        """

        user: dict
        for user in users:
            user[1].setblocking(False)
            user[1].sendall(json.dumps(grid, cls=NumpyEncoder.NumpyEncoder).encode("utf-8"))

        time.sleep(1)


def accept(sock: sock.SocketType, mask, queue: mp.Queue, keyQueue: mp.Queue):
    conn, addr = sock.accept()  # Should be ready

    logger.info('[SERVER] Accepted %s from %s', conn, addr)

    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn: sock.SocketType, mask, queue: mp.Queue, keyQueue: mp.Queue):
    current_user_input = [0, 0]
    data = conn.recv(1024)
    if data:
        logger.info('[SERVER] Received %s from %s', repr(data), conn)

        if data.decode("utf-8").startswith("INIT"):
            users.append([data.decode("utf-8")[4:], conn])


        logger.info(data.decode("utf-8"))

        try:
            while True:
                keyQueue.get_nowait()
        except:
            pass

        if data.decode("utf-8") == "UP":
            if conn == users[0][1]:
                current_user_input[0] = 1
            elif conn == users[1][1]:
                current_user_input[1] = 1
            keyQueue.put_nowait(current_user_input)
        elif data.decode("utf-8") == "DOWN":
            if conn == users[0][1]:
                current_user_input[0] = 2
            elif conn == users[1][1]:
                current_user_input[1] = 2
            keyQueue.put_nowait(current_user_input)
        else:
            current_user_input = [0, 0]
            keyQueue.put_nowait(current_user_input)

    else:
        logger.warning('[SERVER] closing %s', conn)

        sel.unregister(conn)
        conn.close()


def Server(sock: sock.SocketType):
    sel.register(sock, selectors.EVENT_READ, accept)
    q = mp.Queue()

    keyQueue = mp.Queue()

    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask, q, keyQueue)

        global executed
        if users.__len__() == 2 and executed == False:
            q.put_nowait(users)
            executed = True
            mp.Process(target=start_game, args=(q, keyQueue, )).start()


def CreateNewServer(port):
    serversocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    serversocket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
    serversocket.setblocking(False)
    serversocket.bind(('', port))
    serversocket.listen(5)

    logger.info("Server created on port %s.", str(port))

    server_process = mp.Process(target=Server, args=(serversocket,))
    server_process.start()