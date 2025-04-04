import socket as sock
import multiprocessing as mp
import Server

import numpy as np
import os

import json

import msvcrt
import sys
import winsound

# Import required libraries

ROWS, COLS = 6, 20
CAR_SYMBOL, OBSTACLE_SYMBOL, EMPTY_SYMBOL = 1, 2, 0

# constant variables for grid size and integer representations of grid

game_ended = False # Boolean value for whether the game has ended

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
import logging

logger = logging.getLogger("client")
logging.basicConfig(filename='client.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def CheckKeys(sock: sock.SocketType, kill_queue: mp.Queue, name: str):
    mp.Process(target=GameLoop, args=(sock,kill_queue, name, elements)).start() # Start the game loop checking for messages from the server
    global game_ended
    while True:
        if kill_queue.empty() == False: # Check if it is time to terminate
            kill = kill_queue.get_nowait()
            if kill == True:
                game_ended = True
                return

        if msvcrt.kbhit(): # Check for key inputs
                    character = msvcrt.getch()
                    if character == b"\xe0" or character == b"\x00":
                        character = msvcrt.getch()

                        if character == b"H": # If up, send up to the server
                            sock.sendall(b"UP")
                        elif character == b"P": # Vice versa
                            sock.sendall(b"DOWN")


def ConnectToServer(ip: str, port: int, name: str):
    while True: # Always try to make first contact to the server quietly
         try:
            clientsocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            clientsocket.connect((ip, port))

            intial_packet = f"INIT{name}"

            clientsocket.sendall(bytes(intial_packet, "utf-8"))

            return clientsocket
         except:
              pass

# Actually start the game
def GameLoop(sock: sock.SocketType, kill_queue: mp.Queue, name: str, elements: list):
    global game_ended
    if kill_queue.empty() == False: # Check for termination
            kill = kill_queue.get_nowait()
            if kill == True:
                return
    # Cool music
    winsound.PlaySound("assets/game.wav", winsound.SND_FILENAME + winsound.SND_ASYNC + winsound.SND_LOOP)
    
    # Create enough space for the grid to be drawn without overwriting console text
    for i in range(0, ROWS*2+1):
        print()

    while True:
        data = sock.recv(4096) # Upon data being recieved
        if data:
            logger.info(f"[CLIENT] Received data: {data}")
            if b"LOSE" in data: # Stop the game if we lose
                print(f"You lost, {name}! Your score was {data.decode('utf-8')[5:]}")
                kill_queue.put_nowait(True)
                game_ended = True
                sock.close()
                winsound.PlaySound(None, winsound.SND_PURGE) # Stop music, close sockets, put True into kill_queue
                break
            for line in data.decode('utf-8').splitlines(): # Print each individual line of the server data
                game_grid = (np.asarray(json.loads(line), dtype=int)) # Load the lines from the json data
                for i in range(0, ROWS*2+1):
                    sys.stdout.write("\x1b[F") # Move the cursor up to the top of the grid
                for row in game_grid:
                    for i in range(0, COLS): # Print road markers
                        print("--", end="")
                    print()

                    for i in row:
                        print(elements[i], end="") # Print the elements of the game (obstacle, car, air)
                    print()

                for i in range(0, COLS):
                    print("--", end="") # Print final road markers
                print()
        else:
            break

# Function for selecting the wanted connection    
def connection_selection_func(kill_queue: mp.Queue, name: str, connection_selection, restart=False):
    global conn_det
    if connection_selection == "connect": # If we want to connect to an existing server
            if not restart: # If we are joining a new game
                conn_det = input("Please specify the IP address and port, separated by a comma: ").split(",")

            winsound.PlaySound(None, winsound.SND_PURGE)
            print(f"Good luck, {name}!")

            # Start the game
            socket: sock.SocketType = ConnectToServer(conn_det[0], int(conn_det[1]), name)
            CheckKeys(socket, kill_queue, name)

    elif connection_selection == "new server": # Otherwise if we want to start a new server
            print(f"Good luck, {name}!")
            server_process = mp.Process(target=Server.CreateNewServer, args=(6089,kill_queue)) # Start a new server on another thread
            server_process.start()

            winsound.PlaySound(None, winsound.SND_PURGE)
            socket: sock.SocketType = ConnectToServer("localhost", 6089, name) # Create a client to connect to our new server
            CheckKeys(socket, kill_queue, name)

    else: # Try again if garbage input
            print("Invalid input. Please try again.")
            main()


if __name__ == "__main__": # Main function that starts
    def main(kill_q: mp.Queue = None, name_par: str = None, connect_selec = None, res = False):
        global elements
        kill_queue = kill_q or mp.Queue()
        # Initial music
        winsound.PlaySound("assets/intro.wav", winsound.SND_FILENAME + winsound.SND_ASYNC + winsound.SND_LOOP)
        print("Welcome to",
              "\033[36m" "A"
              "\033[30m" "l"
              "\033[31m" "p"
              "\033[32m" "h"
              "\033[33m" "o"
              "\033[34m" "n"
              "\033[35m" "s"
              "\033[36m" "'s",
              "\033[31m" "Car Racing Game!" "\033[0m")
        
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
        
        print("The aim of the game is to work with another player to control a car in order to dodge obstacles.\n"
        "You must use your arrow keys to change the lane in which your car is in, and have the same input as the other player.\n"
        "You lose when you crash into an obstacle.\n"
        "Remember, if you press the Up arrow key, and the other player presses something else, the car will not move.\n"
        "However, if you two press the same button at the same time, then the car will move.")
        
        name = name_par or input("What is your name? ") # Check if the name already exists (if restarting)

        current_car_selection = 0

        print('\033[?25l', end="")

        if not res: # If we aren't restarting
            print("What car would you like? Select it with your right or left arrow keys, and then press enter!")
            print(f'<< {car_select_array[current_car_selection]} >>', end='\r')
            while True:
                if msvcrt.kbhit():
                    character = msvcrt.getch()
                    if character == b"\xe0" or character == b"\x00":
                        character = msvcrt.getch() # Collect key inputs

                        if character == b"M": # Right arrow key
                            try:
                                current_car_selection = min(current_car_selection+1, car_select_array.__len__()-1) # choose whichever is lower to not go too far
                            except:
                                pass
                        elif character == b"K": # Left arrow key
                            try:
                                current_car_selection = max(current_car_selection-1, 0) # choose whatever is higher to not go too far
                            except:
                                pass

                        print(f"<< {car_select_array[current_car_selection]} >>", end='\r')
                    elif character == b'\r':
                        break
        print(f"<< {car_select_array[current_car_selection]} >>", end='\n')

        elements[1] = car_select_array[current_car_selection] # Set the car element to the emoji we want
        print('\033[?25h', end="")
        
        connection_selection = connect_selec or input("Would you like to connect to a server, or create a new one? (Connect/New Server): ").lower()

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