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
            print(f"Say hi to {self.their_name}")
            print("You can say 'bye' to disconnect")
            
            self.root = tk.Tk()
            self.root.geometry("300x300")
            self.root.title(f"{self.my_name}'s client")

            self.chat_history_string = tk.StringVar(self.root)
            self.chat_history_list = ['']*18
            self.chat_history_string.set('\n'.join(self.chat_history_list))
            self.chat_history_label = tk.Label(self.root, font=("Courier", 9),
                textvariable=self.chat_history_string, justify=tk.LEFT)
            self.chat_history_label.grid(row=0, column=0)

            self.chat_entry_string = tk.StringVar(self.root)
            self.chat_entry = tk.Entry(self.root, font=("Courier", 9),
                                       textvariable=self.chat_entry_string)
            self.chat_entry.grid(row=1, column=0)

            self.chat_entry.bind("<Return>", self.send)

            t1 = threading.Thread(target=self.recieve)
            t1.start()
            self.root.mainloop()

    def update_chat(self, msg, name):
        line_length = (__class__.max_line_length-2)-len(name)
        self.chat_history_list.append(f"{name}: {msg[0:line_length]}")

        msg = msg[line_length:]
        while msg:
            self.chat_history_list.append(msg[0:__class__.max_line_length])
            msg = msg[__class__.max_line_length:]
        while len(self.chat_history_list) > __class__.max_lines:
            del self.chat_history_list[0]
        self.chat_history_string.set('\n'.join(self.chat_history_list))

    def send(self, event):
        msg = self.chat_entry_string.get()
        if msg == "":
            return
        self.chat_entry_string.set("")
        self.update_chat(msg, self.my_name)
        self.send_packet(msg)
        if msg == "bye":
            raise DisconnectError("I said bye")

    def recieve(self):
        while True:
            msg = self.get_packet()
            self.update_chat(msg, self.their_name)
            if msg == "bye":
                raise DisconnectError(f"{self.their_name} said bye")

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