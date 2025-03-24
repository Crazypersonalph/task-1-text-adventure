import socket as sock
import multiprocessing as mp
import Server

import numpy as np
import os

import json

ROWS, COLS = 3, 10
CAR_SYMBOL, OBSTACLE_SYMBOL, EMPTY_SYMBOL = 1, 2, 0

grid = np.full((ROWS, COLS), EMPTY_SYMBOL, dtype=int)

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename='client.log', encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


current_log = []


def ConnectToServer(ip, port, name):
    clientsocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    clientsocket.connect((ip, port))

    intial_packet = f"INIT{name}"

    clientsocket.sendall(bytes(intial_packet, "utf-8"))


    GameLoop(clientsocket)


def GameLoop(sock: sock.SocketType):
    try:
        while True:
            data = sock.recv(1024)
            if data:
                print(np.asarray(json.loads(data.decode("utf-8")), dtype=int))
            else:
                raise
    except:
        sock.close()
        os._exit(0)
        return
    



if __name__ == "__main__":
    def main():
        print("Welcome to Alphons's Car Racing Game!")
        print("The aim of the game is to work with another player to control a car in order to dodge obstacles.\n You must use your arrow keys to change the lane in which your car is in, and have the same input as the other player.\n You lose when you crash into an obstacle.")
        
        name = input("What is your name? ")
        
        connection_selection = input("Would you like to connect to a server, or create a new one? (Connect/New Server)")

        if connection_selection == "Connect":
            conn_det = input("Please specify the IP address and port, separated by a comma: ").split(",")

            client_process = mp.Process(target=ConnectToServer, args=(conn_det[0], int(conn_det[1]), name))
            client_process.start()

        elif connection_selection == "New Server":
            server_process = mp.Process(target=Server.CreateNewServer, args=(6089,))
            server_process.start()

            client_process = mp.Process(target=ConnectToServer, args=("localhost", 6089, name))
            client_process.start()
        else:
            print("Invalid input. Please try again.")
            main()
    main()