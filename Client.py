import socket as sock
import multiprocessing as mp
import Server

import numpy as np
import os

import json

import msvcrt

ROWS, COLS = 3, 10
CAR_SYMBOL, OBSTACLE_SYMBOL, EMPTY_SYMBOL = 1, 2, 0

grid = np.full((ROWS, COLS), EMPTY_SYMBOL, dtype=int)

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='client.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def CheckKeys(sock: sock.SocketType):
    mp.Process(target=GameLoop, args=(sock,)).start()
    while True:
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


def GameLoop(sock: sock.SocketType):
    while True:
        data = sock.recv(4096)
        if data:
            if b"LOSE" in data:
                print("You lost!")
                sock.close()
                os._exit(0)
                break
            for line in data.decode('utf-8').splitlines():
                print(np.asarray(json.loads(line), dtype=int))
        else:
            break

    



if __name__ == "__main__":
    def main():
        print("Welcome to Alphons's Car Racing Game!")
        print("The aim of the game is to work with another player to control a car in order to dodge obstacles.\n You must use your arrow keys to change the lane in which your car is in, and have the same input as the other player.\n You lose when you crash into an obstacle.")
        
        name = input("What is your name? ")
        
        connection_selection = input("Would you like to connect to a server, or create a new one? (Connect/New Server): ").lower()

        if connection_selection == "connect":
            conn_det = input("Please specify the IP address and port, separated by a comma: ").split(",")

            socket: sock.SocketType = ConnectToServer(conn_det[0], int(conn_det[1]), name)
            CheckKeys(socket)

        elif connection_selection == "new server":
            server_process = mp.Process(target=Server.CreateNewServer, args=(6089,))
            server_process.start()

            socket: sock.SocketType = ConnectToServer("localhost", 6089, name)
            CheckKeys(socket)

        else:
            print("Invalid input. Please try again.")
            main()
    main()