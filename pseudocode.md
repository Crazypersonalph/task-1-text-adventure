```
IMPORT sockets FROM Python

GLOBAL current_log = []

FUNCTION MainGame(sock: PySocket)
    WHILE TRUE
        IF down_arrow_pressed == TRUE
            sock.send(down_arrow_pressed)
        ELSE IF up_arrow == TRUE
            sock.send(up_arrow_pressed)
        END IF
        OUTPUT[current_log.search("grid_display")]
    END WHILE
END FUNCTION

FUNCTION CarSelectionCollision(car_type: str, sock: PySocket)
    coll = sock.send(car_type)
    return coll
END FUNCTION

FUNCTION SelectCar(sock: PySocket)
    OUTPUT["What car design would you like? They all run the same! (race car/buggy/van)"]
    car_type = INPUT[str]
    collision = CarSelectionCollision(car_type, sock)

    IF collision == FALSE
        MainGame(sock)
    ELSE
        OUTPUT["Please select the same car as your partner! ;)"]
        SelectCar(sock)
END FUNCTION

ASYNC FUNCTION Listener(socket_instance)
    WHILE True:
        data_buffer = socket_instance.receive_data()
        current_log.append(data_buffer)
        IF data_buffer == "collision"
            OUTPUT["Game Over!"]
            CONST score = socket_instance.send("score")
            OUTPUT["Your score was {score}"]
            END ALL
        END IF
    END WHILE
END FUNCTION

ASYNC Function Server(socket_instance)
    WHILE sock.player_count < 2
        SLEEP(1)
    END WHILE
    ASYNC sock.listen()
    movement_dict = ["user1": "", "user2": ""]
    WHILE TRUE:
        IF sock.receive(move_key, username)
            movement_dict[username] = move_key
        END IF
        IF movement_dict["user1"] == movement_dict["user2"]
            sock.send(grid_display)
        ELSE
            sock.send(existing_grid_display)
        END IF
        IF car_pos == obstacle_pos
            sock.send(obstacle_collision)
        END IF
        
    END WHILE
END FUNCTION

FUNCTION ConnectToServer(ConnectionDetails: arr)
    sock = PySocket_EXTERNAL(ConnectionDetails)
    Listener(sock)
    SelectCar(sock)
END FUNCTION

FUNCTION CreateNewServer()
    CONST port = 6089
    CONST sock = SOCKET_CREATE_EXTERNAL(port)
    Server(sock)
END FUNCTION


MAIN MODULE
    OUTPUT["Welcome to my car racing game!"]
    OUTPUT["The aim of the game is to work with another player to control a car in order to dodge obstacles.\n You must use your arrow keys to change the lane in which your car is in, and have the same input as the other player.\n You lose when you crash into an obstacle."]
    
    OUTPUT["Would you like to connect to a server, or create a new one? (Connect/New Server)"]

    CONST IsServer = INPUT[str]

    IF IsServer == "New Server":
        CreateNewServer()
        ConnectToServer([LOCAL_IP, 6089])
    ELSE IF IsServer == "Connect":
        OUTPUT["Please specify the IP address and port, separated by a comma."]
        CONST CONNECT_DETAILS = INPUT[arr]
        ConnectToServer(CONNECT_DETAILS)
    ELSE:
        OUTPUT["Invalid input. Try again"]
        GOTO IsServer
    END IF
END MAIN MODULE

```