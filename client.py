import socket
import threading

VERSION = 2

class DisconnectError(Exception):
    pass

class Client:
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
            my_name = input("Tell them your name: ")
            self.send_packet(my_name)
            their_name = self.get_packet()
            print(f"Say hi to {their_name}")
            print("You can say 'bye' to disconnect")
        
            def send():
                while True:
                    msg = input()
                    self.send_packet(msg)
                    if msg == "bye":
                        raise DisconnectError("I said bye")

            def recieve():
                while True:
                    msg = self.get_packet()
                    print(f"{their_name}: {msg}")
                    if msg == "bye":
                        raise DisconnectError(f"{their_name} said bye")
            
            t1 = threading.Thread(target=send)
            t2 = threading.Thread(target=recieve)
            t1.start()
            t2.start()

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