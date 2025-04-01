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

ROWS, COLS = 6, 20
CAR_SYMBOL, OBSTACLE_SYMBOL, EMPTY_SYMBOL = 1, 2, 0

executed = False

users = []

current_user_input = [0, 0]


logger = logging.getLogger("server")
logging.basicConfig(filename='server.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

sel = selectors.DefaultSelector()

def start_game(queue: mp.Queue, keyQueue: mp.Queue, kill_queue: mp.Queue):
    grid = np.full((ROWS, COLS), EMPTY_SYMBOL, dtype=int)
    car_x_pos = 0
    car_y_pos = 1

    grid[car_y_pos, car_x_pos] = CAR_SYMBOL
    
    users = queue.get()

    score = 0

    while True:

        if kill_queue.empty() == False:
            kill = kill_queue.get_nowait()
            if kill == True:
                return

        grid[:, :-1] = grid[:, 1:]
        grid[random.randint(0,ROWS-1), -1] = random.choice([0,0,0,2])

        grid[car_y_pos, car_x_pos] += CAR_SYMBOL

        Kqueue = [0, 0]
        
        if keyQueue.qsize() > 0:
            Kqueue = keyQueue.get_nowait()

        if Kqueue[0] == 1 and Kqueue[1] == 1:
            if car_y_pos > 0:
                grid[car_y_pos, car_x_pos] = EMPTY_SYMBOL
                car_y_pos -= 1
                grid[car_y_pos, car_x_pos] += CAR_SYMBOL
        elif Kqueue[0] == 2 and Kqueue[1] == 2:
            if car_y_pos < ROWS - 1:
                grid[car_y_pos, car_x_pos] = EMPTY_SYMBOL
                car_y_pos += 1
                grid[car_y_pos, car_x_pos] += CAR_SYMBOL

        if grid[car_y_pos, car_x_pos] >= 3:
            for user in users:
                user[1].setblocking(False)
                user[1].sendall(b"LOSE " + bytes(str(score), "utf-8"))
                kill_queue.put_nowait(True)
            os._exit(0)

        score += 1

        user: dict
        for user in users:
            user[1].sendall((json.dumps(grid, cls=NumpyEncoder.NumpyEncoder) + "\n").encode("utf-8"))
        
        logger.info("Loop of start_game completed")

        time.sleep(0.3)


def accept(sock: sock.SocketType, mask, queue: mp.Queue, keyQueue: mp.Queue):
    conn, addr = sock.accept()  # Should be ready

    logger.info('[SERVER] Accepted %s from %s', conn, addr)

    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn: sock.SocketType, mask, queue: mp.Queue, keyQueue: mp.Queue):
    global current_user_input
    data = conn.recv(4096)
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


def Server(sock: sock.SocketType, kill_queue: mp.Queue):
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
            mp.Process(target=start_game, args=(q, keyQueue, kill_queue)).start()

        if kill_queue.empty() == False:
            kill = kill_queue.get_nowait()
            if kill == True:
                return


def CreateNewServer(port, kill_queue: mp.Queue):
    serversocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    serversocket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1)
    serversocket.setblocking(False)
    serversocket.bind(('', port))
    serversocket.listen(5)

    logger.info("Server created on port %s.", str(port))

    server_process = mp.Process(target=Server, args=(serversocket, kill_queue))
    server_process.start()