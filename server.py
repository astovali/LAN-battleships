import socket
import threading

class DisconnectError(Exception):
    pass

VERSION = 2

c = 0
addr = 1
username = 2
brd = 3
buffer = 4

class Server:
    def __init__(self, port):
        HOST = ""
        PORT = port #non-privileged ports are > 1023

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((HOST, PORT))
        self.s.listen()

        self.game_threads = []
        self.waiting_client = ()
        self.accepter = threading.Thread(target=self.accept_clients)

    def send_packet(self, client, packet):
        packet = str(packet)
        data = bytes(packet, "utf8")
        client.sendall(bytes(hex(len(data))[2:10].zfill(8), "utf8") + data)

    def get_packet(self, client):
        data_size = client.recv(8, socket.MSG_WAITALL)
        if not data_size:
            raise DisconnectError("Client disconnected")
        data_size = int(data_size.decode("utf8"), base=16)
        data = client.recv(data_size, socket.MSG_WAITALL)
        return data.decode("utf8")

    def accept_clients(self):
        while True:
            client = self.s.accept()
            print(f"{client[addr]} connected")
            if int(self.get_packet(client[c])) != VERSION:
                print("...with wrong version")
                self.send_packet(client[c], "wrong")
                self.send_packet(client[c], VERSION)
                client[c].close()
                continue
            if self.waiting_client:
                self.send_packet(self.waiting_client[c], "found")
                data = self.get_packet(self.waiting_client[c])
                if data:
                    t1 = threading.Thread(target=self.handle_game,
                        args=(client, self.waiting_client))
                    t1.start()
                    self.waiting_client = ()
                    self.game_threads.append(t1)
                else:
                    self.waiting_client = client
                    self.send_packet(self.waiting_client[c], "waiting")
            else:
                self.waiting_client = client
                self.send_packet(self.waiting_client[c], "waiting")
    
    def decode_board(self, encoded):
        if not encoded.isdigit():
            return False
        if len(encoded) != 15:
            return False
        board = [[" " for j in range(10)] for i in range(10)]
        lengths = [2, 3, 3, 4, 5]
        for i in range(0, 15, 3):
            if encoded[i+2]=="0":
                for j in range(lengths[i//3]):
                    if int(encoded[i])+j > 9:
                        return False
                    if board[int(encoded[i])+j][int(encoded[i+1])] == "O":
                        return False
                    board[int(encoded[i])+j][int(encoded[i+1])] = "O"
            if encoded[i+2]=="1":
                for j in range(lengths[i//3]):
                    if int(encoded[i])-j < 0:
                        return False
                    if board[int(encoded[i])-j][int(encoded[i+1])] == "O":
                        return False
                    board[int(encoded[i])-j][int(encoded[i+1])] = "O"
            if encoded[i+2]=="2":
                for j in range(lengths[i//3]):
                    if int(encoded[i+1])+j > 9:
                        return False
                    if board[int(encoded[i])][int(encoded[i+1])+j] == "O":
                        return False
                    board[int(encoded[i])][int(encoded[i+1])+j] = "O"
            if encoded[i+2]=="3":
                for j in range(lengths[i//3]):
                    if int(encoded[i+1])-j < 0:
                        return False
                    if board[int(encoded[i])][int(encoded[i+1])-j] == "O":
                        return False
                    board[int(encoded[i])][int(encoded[i+1])-j] = "O"
        return board
    
    def board_alive(self, board):
        for row in board:
            for tile in row:
                if tile == "O":
                    return True
        return False

    def handle_game(self, p1, p2):
        p1 = list(p1)
        p2 = list(p2)
        self.send_packet(p1[c], "game_start")
        self.send_packet(p2[c], "game_start")
        p1.append(self.get_packet(p1[c]))
        p2.append(self.get_packet(p2[c]))
        self.send_packet(p1[c], p2[username])
        self.send_packet(p2[c], p1[username])

        p1.append(self.decode_board(self.get_packet(p1[c])))
        p2.append(self.decode_board(self.get_packet(p2[c])))
        while not p1[brd]:
            self.send_packet(p1[c], "invalid")
            p1[brd] = self.decode_board(self.get_packet(p1[c]))
        self.send_packet(p1[c], "valid")
        while not p2[brd]:
            self.send_packet(p2[c], "invalid")
            p2[brd] = self.decode_board(self.get_packet(p2[c]))
        self.send_packet(p2[c], "valid")

        p1.append({"msg": [], "mve": ""})
        p2.append({"msg": [], "mve": ""})
        
        print(f"Game between '{p1[username]}' {p1[addr]} and '{p2[username]}' {p2[addr]} began")

        def add_buffer_from(client):
            msg = ""
            while msg.lower() != "msgbye":
                msg = self.get_packet(client[c])
                if msg[0:3] == "msg":
                    client[buffer]["msg"].append(msg)
                elif msg[0:3] == "mve":
                    if msg[3:].isdigit() and len(msg[3:]) == 2:
                        client[buffer]["mve"] = msg[3:]
            raise DisconnectError(f"{client[username]}")
        
        def messages(fro, to):
            msg = ""
            while msg.lower() != "msgbye":
                if len(fro[buffer]["msg"]) > 0:
                    msg = fro[buffer]["msg"].pop(0)
                    self.send_packet(to[c], msg)
        
        def moves(p1, p2):
            while self.board_alive(p1[brd]):
                while p1[buffer]["mve"] == "":
                    pass
                move = p1[buffer]["mve"]
                p1[buffer]["mve"] = ""
                if p2[brd][int(move[0])][int(move[1])] == "O":
                    p2[brd][int(move[0])][int(move[1])] = "X"
                    self.send_packet(p1[c], f"hit{move}")
                if p2[brd][int(move[0])][int(move[1])] == " ":
                    p2[brd][int(move[0])][int(move[1])] = "O"
                    self.send_packet(p1[c], f"mis{move}")

                if not self.board_alive(p2[brd]):
                    break

                while p2[buffer]["mve"] == "":
                    pass
                move = p2[buffer]["mve"]
                p2[buffer]["mve"] = ""
                if p1[brd][int(move[0])][int(move[1])] == "O":
                    p1[brd][int(move[0])][int(move[1])] = "X"
                    self.send_packet(p2[c], f"hit{move}")
                if p1[brd][int(move[0])][int(move[1])] == " ":
                    p1[brd][int(move[0])][int(move[1])] = "O"
                    self.send_packet(p2[c], f"mis{move}")
            if self.board_alive(p1[brd]):
                self.send_packet(p1[c], "sysYou won!")
                self.send_packet(p2[c], "sysYou lost!")
                print(f"{p1[username]}' {p1[addr]} won")
            else:
                self.send_packet(p2[c], "sysYou won!")
                self.send_packet(p1[c], "sysYou lost!")
                print(f"{p2[username]}' {p2[addr]} won")
            p1[buffer]["msg"].insert(0, "msgbye")
            p2[buffer]["msg"].insert(0, "msgbye")

        threads = []
        threads.append(threading.Thread(target=add_buffer_from, args=(p1,)))
        threads.append(threading.Thread(target=add_buffer_from, args=(p2,)))
        threads.append(threading.Thread(target=messages, args=(p1, p2)))
        threads.append(threading.Thread(target=messages, args=(p2, p1)))
        threads.append(threading.Thread(target=moves, args=(p2, p1)))
        for i in range(len(threads)):
            threads[i].start()
        for i in range(len(threads)):
            threads[i].join()
        print(f"Game between '{p1[username]}' {p1[addr]} and '{p2[username]}' {p2[addr]} ended")

server = Server(int(input("Port: ")))
server.accepter.start()
print("Server up!")
server.accepter.join()
while True:
    server.accepter = threading.Thread(target=server.accept_clients)
    server.accepter.start()
    print("Server reboot")
    server.accepter.join()