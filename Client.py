import socket as sock
import multiprocessing as mp
import Server

import numpy as np
import os

import json

import msvcrt

import sys

import winsound

ROWS, COLS = 6, 20
CAR_SYMBOL, OBSTACLE_SYMBOL, EMPTY_SYMBOL = 1, 2, 0

game_ended = False

conn_det = []

car_select_array = ['🚃','🚋','🚓', '🚔', '🚗', '🚘', '🚙', '🏎️', '🚡', '🚞', '🚲', '🏍️', '🛵', '⛴️', '🚢']


elements = [
    "  ",
    car_select_array[1],
    "🧱",
]

grid = np.full((ROWS, COLS), EMPTY_SYMBOL, dtype=int)

import logging

logger = logging.getLogger("client")
logging.basicConfig(filename='client.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def CheckKeys(sock: sock.SocketType, kill_queue: mp.Queue, name: str):
    mp.Process(target=GameLoop, args=(sock,kill_queue, name, elements)).start()
    global game_ended
    while True:
        if kill_queue.empty() == False:
            kill = kill_queue.get_nowait()
            if kill == True:
                game_ended = True
                return

        if msvcrt.kbhit():
                    character = msvcrt.getch()
                    if character == b"\xe0" or character == b"\x00":
                        character = msvcrt.getch()

                        if character == b"H":
                            sock.sendall(b"UP")
                        elif character == b"P":
                            sock.sendall(b"DOWN")


def ConnectToServer(ip: str, port: int, name: str):
    while True:
         try:
            clientsocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            clientsocket.connect((ip, port))

            intial_packet = f"INIT{name}"

            clientsocket.sendall(bytes(intial_packet, "utf-8"))

            return clientsocket
         except:
              pass


def GameLoop(sock: sock.SocketType, kill_queue: mp.Queue, name: str, elements: list):
    global game_ended
    if kill_queue.empty() == False:
            kill = kill_queue.get_nowait()
            if kill == True:
                return
    winsound.PlaySound("assets/game.wav", winsound.SND_FILENAME + winsound.SND_ASYNC + winsound.SND_LOOP)
    for i in range(0, ROWS*2+1):
        print()

    while True:
        data = sock.recv(4096)
        if data:
            logger.info(f"[CLIENT] Received data: {data}")
            if b"LOSE" in data:
                print(f"You lost, {name}! Your score was {data.decode('utf-8')[5:]}")
                kill_queue.put_nowait(True)
                game_ended = True
                sock.close()
                winsound.PlaySound(None, winsound.SND_PURGE)
                break
            for line in data.decode('utf-8').splitlines():
                game_grid = (np.asarray(json.loads(line), dtype=int))
                for i in range(0, ROWS*2+1):
                    sys.stdout.write("\x1b[F")
                for row in game_grid:
                    for i in range(0, COLS):
                        print("--", end="")
                    print()

                    for i in row:
                        print(elements[i], end="")
                    print()

                for i in range(0, COLS):
                    print("--", end="")
                print()
        else:
            break

    
def connection_selection_func(kill_queue: mp.Queue, name: str, connection_selection, restart=False):
    global conn_det
    if connection_selection == "connect":
            if not restart:
                conn_det = input("Please specify the IP address and port, separated by a comma: ").split(",")

            winsound.PlaySound(None, winsound.SND_PURGE)
            print(f"Good luck, {name}!")

            socket: sock.SocketType = ConnectToServer(conn_det[0], int(conn_det[1]), name)
            CheckKeys(socket, kill_queue, name)

    elif connection_selection == "new server":
            print(f"Good luck, {name}!")
            server_process = mp.Process(target=Server.CreateNewServer, args=(6089,kill_queue))
            server_process.start()

            winsound.PlaySound(None, winsound.SND_PURGE)
            socket: sock.SocketType = ConnectToServer("localhost", 6089, name)
            CheckKeys(socket, kill_queue, name)

    else:
            print("Invalid input. Please try again.")
            main()


if __name__ == "__main__":
    def main(kill_q: mp.Queue = None, name_par: str = None, connect_selec = None, res = False):
        global elements
        kill_queue = kill_q or mp.Queue()
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
        
        name = name_par or input("What is your name? ")

        current_car_selection = 0

        print('\033[?25l', end="")

        if not res:
            print("What car would you like?")
            print(f'<< {car_select_array[current_car_selection]} >>', end='\r')
            while True:
                if msvcrt.kbhit():
                    character = msvcrt.getch()
                    if character == b"\xe0" or character == b"\x00":
                        character = msvcrt.getch()

                        if character == b"M":
                            try:
                                current_car_selection = min(current_car_selection+1, car_select_array.__len__()-1)
                            except:
                                pass
                        elif character == b"K":
                            try:
                                current_car_selection = max(current_car_selection-1, 0)
                            except:
                                pass

                        print(f"<< {car_select_array[current_car_selection]} >>", end='\r')
                    elif character == b'\r':
                        break
        print(f"<< {car_select_array[current_car_selection]} >>", end='\n')

        elements[1] = car_select_array[current_car_selection]
        print('\033[?25h', end="")
        
        connection_selection = connect_selec or input("Would you like to connect to a server, or create a new one? (Connect/New Server): ").lower()

        connection_selection_func(kill_queue, name, connection_selection, restart=res)

        restart = input("Would you like to play another game with the same settings? (Y/N) ")

        if restart.lower() == 'y':
            main(kill_queue, name, connection_selection, res=True)
        else:
            pass

        return
    main()

    if game_ended:
        print()
        os.system("pause")