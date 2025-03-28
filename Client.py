import socket as sock
import multiprocessing as mp
import Server

import numpy as np
import os

import json

import msvcrt

import sys

import winsound

ROWS, COLS = 5, 20
CAR_SYMBOL, OBSTACLE_SYMBOL, EMPTY_SYMBOL = 1, 2, 0

game_ended = False

elements = [
    "  ",
    "🚗",
    "🧱",
]

grid = np.full((ROWS, COLS), EMPTY_SYMBOL, dtype=int)

import logging

logger = logging.getLogger("client")
logging.basicConfig(filename='client.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def CheckKeys(sock: sock.SocketType, kill_queue: mp.Queue):
    mp.Process(target=GameLoop, args=(sock,kill_queue)).start()
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
    clientsocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    clientsocket.connect((ip, port))

    intial_packet = f"INIT{name}"

    clientsocket.sendall(bytes(intial_packet, "utf-8"))

    return clientsocket


def GameLoop(sock: sock.SocketType, kill_queue: mp.Queue):
    global game_ended
    if kill_queue.empty() == False:
            kill = kill_queue.get_nowait()
            if kill == True:
                return
    winsound.PlaySound("assets/game.wav", winsound.SND_FILENAME + winsound.SND_ASYNC + winsound.SND_LOOP)
    for i in range(0, ROWS+6):
        print()

    while True:
        data = sock.recv(4096)
        if data:
            logger.info(f"[CLIENT] Received data: {data}")
            if b"LOSE" in data:
                print(f"You lost! Your score was {data.decode('utf-8')[5:]}")
                kill_queue.put_nowait(True)
                game_ended = True
                sock.close()
                winsound.PlaySound(None, winsound.SND_PURGE)
                break
            for line in data.decode('utf-8').splitlines():
                game_grid = (np.asarray(json.loads(line), dtype=int))
                for i in range(0, ROWS+6):
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

    



if __name__ == "__main__":
    def main():
        kill_queue = mp.Queue()
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
        "You lose when you crash into an obstacle.")
        
        name = input("What is your name? ")
        
        connection_selection = input("Would you like to connect to a server, or create a new one? (Connect/New Server): ").lower()

        if connection_selection == "connect":
            conn_det = input("Please specify the IP address and port, separated by a comma: ").split(",")

            winsound.PlaySound(None, winsound.SND_PURGE)
            socket: sock.SocketType = ConnectToServer(conn_det[0], int(conn_det[1]), name)
            CheckKeys(socket, kill_queue)

        elif connection_selection == "new server":
            server_process = mp.Process(target=Server.CreateNewServer, args=(6089,kill_queue))
            server_process.start()

            winsound.PlaySound(None, winsound.SND_PURGE)
            socket: sock.SocketType = ConnectToServer("localhost", 6089, name)
            CheckKeys(socket, kill_queue)

        else:
            print("Invalid input. Please try again.")
            main()

        return
    main()

    if game_ended:
        print()
        os.system("pause")