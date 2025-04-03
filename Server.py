import socket as sock
import multiprocessing as mp
import selectors

import logging
import json
import numpy as np
import os
import time
import random

# Import required libraries

import classes.NumpyEncoder as NumpyEncoder

ROWS, COLS = 6, 20
CAR_SYMBOL, OBSTACLE_SYMBOL, EMPTY_SYMBOL = 1, 2, 0

# constant variables for grid size and integer representations of grid

executed = False

users = []

current_user_input = [0, 0]

# Start logging
logger = logging.getLogger("server")
logging.basicConfig(filename='server.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Setup the socket selector for managing multiple clients
sel = selectors.DefaultSelector()

# Function called when starting the actual game
def start_game(queue: mp.Queue, keyQueue: mp.Queue, kill_queue: mp.Queue): # Takes arguments for the users, key inputs, and whether the game has been terminated
    grid = np.full((ROWS, COLS), EMPTY_SYMBOL, dtype=int) # Define a new NumPy array for the game filled with 0s
    car_x_pos = 0 # The car starts at (0,1)
    car_y_pos = 1

    grid[car_y_pos, car_x_pos] = CAR_SYMBOL # Set this position on the grid
    
    users = queue.get() # Get all the users currently connected

    score = 0 # Set the score initially to zero

    while True:

        if kill_queue.empty() == False: # If the game has been terminated, exit the function and loop
            kill = kill_queue.get_nowait()
            if kill == True:
                return

        grid[random.randint(0,ROWS-1), -1] = random.choice([0,0,0,0,0,0,0,0,2]) # Put an obstacle on the last column of a random row
        grid[:, :-1] = grid[:, 1:] # Shift all obstacles one unit to the left

        grid[car_y_pos, car_x_pos] += CAR_SYMBOL # Re-set the car position after left shift

        Kqueue = [0, 0] # Define a local variable for key inputs
        
        if keyQueue.qsize() > 0: # If there is a key input
            Kqueue = keyQueue.get_nowait() # Get all keys (avoid errors)

        if Kqueue[0] == 1 and Kqueue[1] == 1: # If both users click up arrows
            if car_y_pos > 0: # Make sure we don't go too far up
                grid[car_y_pos, car_x_pos] = EMPTY_SYMBOL # Set the old car position to empty
                car_y_pos -= 1 # Move the car up
                grid[car_y_pos, car_x_pos] += CAR_SYMBOL # Add the value of the car to the value of that position
                # If the value is 3 or greater, than an obstacle exists in that position
        elif Kqueue[0] == 2 and Kqueue[1] == 2: # If both users click down arrows
            if car_y_pos < ROWS - 1: # Make sure we don't go too far down
                grid[car_y_pos, car_x_pos] = EMPTY_SYMBOL
                car_y_pos += 1 # Likewise
                grid[car_y_pos, car_x_pos] += CAR_SYMBOL

        if grid[car_y_pos, car_x_pos] >= 3: # If the car is colliding with an obstacle
            for user in users: # Tell all users that they have lost
                user[1].setblocking(False)
                user[1].sendall(b"LOSE " + bytes(str(score), "utf-8"))
                kill_queue.put_nowait(True) # Turn the kill queue True, and communicate to all processes
            os._exit(0) # Exit this thread

        score += 1

        user: dict
        for user in users: # Send the new grid to users
            user[1].sendall((json.dumps(grid, cls=NumpyEncoder.NumpyEncoder) + "\n").encode("utf-8"))
        

        time.sleep(0.3) # Constant time change


def accept(sock: sock.SocketType, mask, queue: mp.Queue, keyQueue: mp.Queue): # Accept connections from client, send to read function
    conn, addr = sock.accept()  # Should be ready

    logger.info('[SERVER] Accepted %s from %s', conn, addr)

    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

def read(conn: sock.SocketType, mask, queue: mp.Queue, keyQueue: mp.Queue): # Read messages from clients
    global current_user_input
    data = conn.recv(4096)
    if data:
        logger.info('[SERVER] Received %s from %s', repr(data), conn)

        if data.decode("utf-8").startswith("INIT"): # If users first connecting, set their username and socket info in users list
            users.append([data.decode("utf-8")[4:], conn])


        logger.info(data.decode("utf-8")) # Log everything into file

        try:
            while True: # Empty the key queue to set new inputs
                keyQueue.get_nowait()
        except:
            pass

        if data.decode("utf-8") == "UP": # If somebody sent a message indicating they want to go up
            if conn == users[0][1]: # Check who it is
                current_user_input[0] = 1
            elif conn == users[1][1]:
                current_user_input[1] = 1
            keyQueue.put_nowait(current_user_input) # Throw it into the queue for the next game loop
        elif data.decode("utf-8") == "DOWN": # vice versa
            if conn == users[0][1]:
                current_user_input[0] = 2
            elif conn == users[1][1]:
                current_user_input[1] = 2
            keyQueue.put_nowait(current_user_input)
        else:
            current_user_input = [0, 0] # Else reset the queue. Nobody wants to do anything
            keyQueue.put_nowait(current_user_input)

    else:
        logger.warning('[SERVER] closing %s', conn)

        sel.unregister(conn)
        conn.close()


def Server(sock: sock.SocketType, kill_queue: mp.Queue):
    sel.register(sock, selectors.EVENT_READ, accept) # Start the selectors

    # Establish different multiprocessing queues
    q = mp.Queue()
    keyQueue = mp.Queue()
    
    

    while True:
        events = sel.select() # When an event happens with the sockets
        for key, mask in events:
            callback = key.data # Get the function for the respective event (e.g. accept or read)
            callback(key.fileobj, mask, q, keyQueue) # Call the function with the correct parameters

        global executed
        if users.__len__() == 2 and executed == False: # Start the game
            q.put_nowait(users)
            executed = True
            mp.Process(target=start_game, args=(q, keyQueue, kill_queue)).start()

        if kill_queue.empty() == False: # If there is something in the kill queue, it's time to terminate.
            kill = kill_queue.get_nowait()
            if kill == True:
                return


def CreateNewServer(port, kill_queue: mp.Queue): # Client-available function for starting the server
    serversocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    serversocket.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, 1) # Reuse the port after crash or something goes wrong (e.g. restarting the game)
    serversocket.setblocking(False) # Non-blocking socket for concurrency
    serversocket.bind(('', port)) # Listen on all IPs
    serversocket.listen(5)

    logger.info("Server created on port %s.", str(port))

    server_process = mp.Process(target=Server, args=(serversocket, kill_queue)) # Start the multiprocessing
    server_process.start()