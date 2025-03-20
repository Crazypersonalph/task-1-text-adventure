import socket as sock
import multiprocessing as mp
import Server

current_log = []

def ConnectToServer(ip, port):
    clientsocket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
    clientsocket.connect((ip, port))
    print("Connected to server at " + ip + ":" + str(port) + ".")
    clientsocket.send("Hello, server!".encode())
    clientsocket.close()  



if __name__ == "__main__":
    def main():
        print("Welcome to Alphons's Car Racing Game!")
        print("The aim of the game is to work with another player to control a car in order to dodge obstacles.\n You must use your arrow keys to change the lane in which your car is in, and have the same input as the other player.\n You lose when you crash into an obstacle.")
        connection_selection = input("Would you like to connect to a server, or create a new one? (Connect/New Server)")

        if connection_selection == "Connect":
            conn_det = input("Please specify the IP address and port, separated by a comma.").split(",")
            ConnectToServer(conn_det)
        elif connection_selection == "New Server":
            Server.CreateNewServer(6089)
            ConnectToServer("localhost", 6089)
        else:
            print("Invalid input. Please try again.")
            main()
    main()