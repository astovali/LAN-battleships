import socket
import threading
import tkinter as tk

VERSION = 2

class DisconnectError(Exception):
    pass

class Client:
    max_lines = 18
    max_line_length = 20

    def __init__(self, host, port):
        HOST = host
        PORT = port

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((HOST, PORT))
        self.send_packet(VERSION)

        data = self.get_packet()
        if data == "wrong":
            print("Old version")
            print(f"Update to version {self.get_packet()} to connect")
            print("https://github.com/astovali/LAN-battleships")
            input('')
        if data == "waiting":
            print("Waiting for another client, please do not disconnect")
            if self.get_packet() == "found":
                self.send_packet("good")
                print("Server found another client")
                data = self.get_packet()
        if data == "game_start":
            self.my_name = input("Tell them your name: ")
            self.send_packet(self.my_name)
            self.their_name = self.get_packet()
            print("You can say 'bye' to disconnect")

            self.their_board = [["+" for j in range(10)] for i in range(10)]

            print("Enter positions in format: yx")
            print("The board is 10x10, and 00 is the top left")
            print("Valid directions are up, down, right, left")
            my_encoded = self.get_board()
            self.send_packet(my_encoded)
            valid = self.get_packet()
            while valid != "valid":
                print("Pluh you input an invalid board try again")
                my_encoded = self.get_board()
                self.send_packet(my_encoded)
                valid = self.get_packet()
            
            self.root = tk.Tk()
            self.root.title(f"{self.my_name}'s client")

            self.chat_history_string = tk.StringVar(self.root)
            self.chat_history_list = ['']*18
            self.chat_history_string.set('\n'.join(self.chat_history_list))
            self.chat_history_label = tk.Label(self.root, font=("Courier", 9),
                textvariable=self.chat_history_string, justify=tk.LEFT, anchor=tk.NW)
            self.chat_history_label.grid(row=0, column=0)

            self.board_string = tk.StringVar(self.root)
            self.board_string.set("\n".join(["".join(row) for row in self.their_board]))
            self.board_label = tk.Label(self.root, font=("Courier", 16),
                textvariable=self.board_string)
            self.board_label.grid(row=0, column=1)

            self.chat_entry_string = tk.StringVar(self.root)
            self.chat_entry = tk.Entry(self.root, font=("Courier", 9),
                                       textvariable=self.chat_entry_string)
            self.chat_entry.grid(row=1, column=0)

            self.move_entry_string = tk.StringVar(self.root)
            self.move_entry = tk.Entry(self.root, font=("Courier", 9),
                                       textvariable=self.move_entry_string)
            self.move_entry.grid(row=1, column=1)


            self.chat_entry.bind("<Return>", self.send_msg)

            self.move_entry.bind("<Return>", self.send_move)

            t1 = threading.Thread(target=self.recieve)
            t1.start()
            self.root.mainloop()
    
    def get_board(self):
            if input("Use previous setup? Y/N ").lower() == "y":
                my_encoded = input("Code: ")
                if len(my_encoded) == 15:
                    return my_encoded
                else:
                    print("Pluh that is not a code, just use the normal setup bro")
            lengths = [2, 3, 3, 4, 5]
            directions = {"up": "1", "down": "0", "right": "3", "left": "2"}
            my_encoded = ""
            for i in range(5):
                pos = input(f"{lengths[i]} long boat starting pos: ")
                my_encoded += pos
                dir = input("Direction: ")
                my_encoded += directions[dir]
            print("Code for future reference:")
            print(my_encoded)
            return my_encoded

    def update_chat(self, msg, name):
        line_length = (__class__.max_line_length-1)-len(name)
        self.chat_history_list.append(f"{name} {msg[0:line_length]}")

        msg = msg[line_length:]
        while msg:
            self.chat_history_list.append(msg[0:__class__.max_line_length])
            msg = msg[__class__.max_line_length:]
        while len(self.chat_history_list) > __class__.max_lines:
            del self.chat_history_list[0]
        self.chat_history_string.set('\n'.join(self.chat_history_list))

    def send_msg(self, event):
        msg = self.chat_entry_string.get()
        if msg == "":
            return
        self.chat_entry_string.set("")
        self.update_chat(msg, self.my_name+":")
        self.send_packet(f"msg{msg}")
        if msg == "bye":
            raise DisconnectError("I said bye")
    
    def send_move(self, event):
        move = self.move_entry_string.get()
        if move == "":
            return
        self.move_entry_string.set("")
        self.send_packet(f"mve{move}")

    def recieve(self):
        while True:
            msg = self.get_packet()
            if msg[0:3] == "msg":
                msg = msg[3:]
                self.update_chat(msg, self.their_name+":")
                if msg == "bye":
                    raise DisconnectError(f"{self.their_name} said bye")
            elif msg[0:3] == "sys":
                msg = msg[3:]
                self.update_chat(msg, "<SERVER>")
                if msg == "bye":
                    raise DisconnectError(f"SERVER said bye")
            elif msg[0:3] == "hit":
                msg = msg[3:]
                self.their_board[int(msg[0])][int(msg[1])] = "X"
                self.board_string.set("\n".join(["".join(row) for row in self.their_board]))
                self.update_chat(f"at {msg}", "<HIT>")
            elif msg[0:3] == "mis":
                msg = msg[3:]
                self.their_board[int(msg[0])][int(msg[1])] = "O"
                self.board_string.set("\n".join(["".join(row) for row in self.their_board]))
                self.update_chat(f"at {msg}", "<MISS>")

    def send_packet(self, packet):
        packet = str(packet)
        data = bytes(packet, "utf8")
        self.s.sendall(bytes(hex(len(data))[2:10].zfill(8), "utf8") + data)

    def get_packet(self):
        data_size = self.s.recv(8, socket.MSG_WAITALL)
        if not data_size:
            raise DisconnectError("Server disconnected")
        data_size = int(data_size.decode("utf8"), base=16)
        data = self.s.recv(data_size, socket.MSG_WAITALL)
        return data.decode("utf8")

client = Client(input("Server IP: "), int(input("Port: ")))