"""
The main entrypoint for the game. Handles client-side code.
"""

import socket as sock
import multiprocessing as mp

import os
import json
import logging

import msvcrt
import sys
import winsound

import numpy as np

import server

# Import required libraries

ROWS, COLS = 6, 20
CAR_SYMBOL, OBSTACLE_SYMBOL, EMPTY_SYMBOL = 1, 2, 0

# constant variables for grid size and integer representations of grid

game_ended: bool = False # Boolean value for whether the game has ended

conn_det = [] # The current connection details (globally accessible)

# The cars from which we can choose
car_select_array = ['🚃','🚋','🚓', '🚔', '🚗', '🚘', '🚙', '🏎️', '🚡', '🚞', '🚲', '🏍️', '🛵', '⛴️', '🚢']

# The elements which form the drawn grid
elements = [
    "  ",
    car_select_array[1],
    "🧱",
]

# Create a new empty grid
grid = np.full((ROWS, COLS), EMPTY_SYMBOL, dtype=int)

# Do all our logging stuff
logger = logging.getLogger("client")
logging.basicConfig(filename='client.log',
                    encoding='utf-8',
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def check_keys(keys_sock: sock.SocketType, kill_queue: mp.Queue, name: str):
    """
    Check the key inputs, and if detected, send them to the server.
    """

    # Start the game loop checking for messages from the server
    mp.Process(target=game_loop, args=(keys_sock,kill_queue, name, elements)).start()

    global game_ended # pylint: disable=global-statement
    while True:
        if not kill_queue.empty(): # Check if it is time to terminate
            kill = kill_queue.get_nowait()
            if kill is True:
                game_ended = True
                return

        if msvcrt.kbhit(): # Check for key inputs
            character = msvcrt.getch()
            if character == b"\xe0" or character == b"\x00":
                character = msvcrt.getch()

                if character == b"H": # If up, send up to the server
                    keys_sock.sendall(b"UP")
                elif character == b"P": # Vice versa
                    keys_sock.sendall(b"DOWN")


def connect_to_server(ip: str, port: int, name: str):
    """
    Function to connect to the server and send initial packets
    """
    while True: # Always try to make first contact to the server quietly
        try:
            clientsocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            clientsocket.connect((ip, port))

            intial_packet = f"INIT{name}"

            clientsocket.sendall(bytes(intial_packet, "utf-8"))

            return clientsocket
        except: # pylint: disable=bare-except
            pass

# Actually start the game
def game_loop(game_sock: sock.SocketType, kill_queue: mp.Queue, name: str, game_elements: list):
    """
    Function that constantly polls the server for changes and draws the game.
    """
    global game_ended # pylint: disable=global-statement
    if not kill_queue.empty(): # Check for termination
        kill = kill_queue.get_nowait()
        if kill is True:
            return
    # Cool music
    winsound.PlaySound("assets/game.wav",
                       winsound.SND_FILENAME + winsound.SND_ASYNC + winsound.SND_LOOP)

    # Create enough space for the grid to be drawn without overwriting console text
    for i in range(0, ROWS*2+1):
        print()

    while True:
        data = game_sock.recv(4096) # Upon data being recieved
        if data:
            logger.info("[CLIENT] Received data: %s", data)
            if b"LOSE" in data: # Stop the game if we lose
                # Stop music, close sockets, put True into kill_queue
                if int(data.decode('utf-8')[5:]) >= 1000:
                    print(f"You won, {name}! Your score was {data.decode('utf-8')[5:]}")
                else:
                    print(f"You lost, {name}! Your score was {data.decode('utf-8')[5:]}")
                kill_queue.put_nowait(True)
                game_ended = True
                game_sock.close()
                winsound.PlaySound(None, winsound.SND_PURGE)
                break
            # Print each individual line of the server data
            for line in data.decode('utf-8').splitlines():
                # Load the lines from the json data
                game_grid = (np.asarray(json.loads(line), dtype=int))
                for i in range(0, ROWS*2+1):
                    sys.stdout.write("\x1b[F") # Move the cursor up to the top of the grid
                for row in game_grid:
                    for i in range(0, COLS): # Print road markers
                        print("--", end="")
                    print()

                    for i in row:
                        # Print the elements of the game (obstacle, car, air)
                        print(game_elements[i], end="")
                    print()

                for i in range(0, COLS):
                    print("--", end="") # Print final road markers
                print()
        else:
            break

# Function for selecting the wanted connection
def connection_selection_func(kill_queue: mp.Queue, name: str, connection_selection, restart=False):
    """
    Function to gather input to connect to the server
    """
    global conn_det # pylint: disable=global-statement
    if connection_selection == "connect": # If we want to connect to an existing server
        if not restart: # If we are joining a new game
            conn_det = input("Please specify the IP address and port, separated by a comma: ").split(",") # pylint: disable=line-too-long

        winsound.PlaySound(None, winsound.SND_PURGE)
        print(f"Good luck, {name}!")

        # Start the game
        socket: sock.SocketType = connect_to_server(conn_det[0], int(conn_det[1]), name)
        check_keys(socket, kill_queue, name)

    elif connection_selection == "new server": # Otherwise if we want to start a new server
        print(f"Good luck, {name}!")
        server_process = mp.Process(target=server.create_new_server,
                                    args=(6089,kill_queue)) # Start a new server on another thread
        server_process.start()

        winsound.PlaySound(None, winsound.SND_PURGE)

        # Create a client to connect to our new server
        socket: sock.SocketType = connect_to_server("localhost",
                                                    6089,
                                                    name)
        check_keys(socket, kill_queue, name)

    else: # Try again if garbage input
        print("Invalid input. Please try again.")
        main()


if __name__ == "__main__": # Main function that starts
    def main(kill_q: mp.Queue = None, name_par: str = None, connect_selec = None, res = False):
        """
        Main entrypoint function of the game client.
        """
        global elements # pylint: disable=global-variable-not-assigned
        kill_queue = kill_q or mp.Queue()
        # Initial music
        winsound.PlaySound("assets/intro.wav",
                           winsound.SND_FILENAME + winsound.SND_ASYNC + winsound.SND_LOOP)
        print("Welcome to",
              "\033[36m" "A" # pylint: disable=implicit-str-concat
              "\033[30m" "l"
              "\033[31m" "p"
              "\033[32m" "h"
              "\033[33m" "o"
              "\033[34m" "n"
              "\033[35m" "s"
              "\033[36m" "'s",
              "\033[31m" "Car Racing Game!" "\033[0m") # pylint: disable=implicit-str-concat
        print("\033[31m"
r'''
                      ___..............._
             __.. ' _'.""""""\\""""""""- .`-._
 ______.-'         (_) |      \\           ` \\`-. _
/_       --------------'-------\\---....______\\__`.`  -..___
| T      _.----._           Xxx|x...           |          _.._`--. _
| |    .' ..--.. `.         XXX|XXXXXXXXXxx==  |       .'.---..`.     -._
\_j   /  /  __  \  \        XXX|XXXXXXXXXXX==  |      / /  __  \ \        `-.
 _|  |  |  /  \  |  |       XXX|""'            |     / |  /  \  | |          |
|__\_j  |  \__/  |  L__________|_______________|_____j |  \__/  | L__________J
     `'\ \      / ./__________________________________\ \      / /___________\\
        `.`----'.'                                     `.`----'.'
          `""""'                                         `""""'
'''
"\033[0m")

        print("The aim of the game is to work with another player to control a car in order to"
        "dodge obstacles.\n"
        "Your objective is to reach 1000 points or higher, and nominally, "
        "to reach as high as possible\n"
        "You must use your arrow keys to change the lane in which your car is in, "
        "and have the same input as the other player.\n"
        "You lose when you crash into an obstacle.\n"
        "Remember, if you press the Up arrow key, "
        "and the other player presses something else, the car will not move.\n"
        "However, if you two press the same button at the same time, then the car will move.")

        # Check if the name already exists (if restarting)
        name = name_par or input("What is your name? ")

        current_car_selection = 0

        print('\033[?25l', end="")

        if not res: # If we aren't restarting
            print("What car would you like? Select it with your right or left arrow keys, "
                  "and then press enter!")
            print(f'<< {car_select_array[current_car_selection]} >>', end='\r')
            while True:
                if msvcrt.kbhit():
                    character = msvcrt.getch()
                    if character == b"\xe0" or character == b"\x00":
                        character = msvcrt.getch() # Collect key inputs

                        if character == b"M": # Right arrow key
                            try:
                                # Choose whichever is lower to not go too far
                                current_car_selection = min(current_car_selection+1,
                                                            len(car_select_array)-1)
                            except: # pylint: disable=bare-except
                                pass
                        elif character == b"K": # Left arrow key
                            try:
                                 # Choose whatever is higher to not go too far
                                current_car_selection = max(current_car_selection-1, 0)
                            except: # pylint: disable=bare-except
                                pass

                        print(f"<< {car_select_array[current_car_selection]} >>", end='\r')
                    elif character == b'\r':
                        break
        print(f"<< {car_select_array[current_car_selection]} >>", end='\n')

        # Set the car element to the emoji we want
        elements[1] = car_select_array[current_car_selection]
        print('\033[?25h', end="")

        connection_selection = connect_selec or input("Would you like to connect to a server, "
                                            "or create a new one? (Connect/New Server): ").lower()

        connection_selection_func(kill_queue, name, connection_selection, restart=res)

        restart = input("Would you like to play another game with the same settings? (Y/N) ")

        if restart.lower() == 'y': # Check if we want to restart
            main(kill_queue, name, connection_selection, res=True)
        else:
            pass

        return
    main()

    if game_ended: # Press key to exit to avoid closing window immediately
        print()
        os.system("pause")
