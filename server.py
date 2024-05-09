import socket
import threading

class DisconnectError(Exception):
    pass

VERSION = 2

c = 0
addr = 1
username = 2

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
        self.accepter.start()
        print("Server up!")

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
            if int(self.get_packet(client[c])) != VERSION:
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

    def handle_game(self, p1, p2):
        p1 = list(p1)
        p2 = list(p2)
        self.send_packet(p1[c], "game_start")
        self.send_packet(p2[c], "game_start")
        p1.append(self.get_packet(p1[c]))
        p2.append(self.get_packet(p2[c]))
        self.send_packet(p1[c], p2[username])
        self.send_packet(p2[c], p1[username])

        def message(send, recieve):
            msg = ""
            while msg.lower() != "bye":
                msg = self.get_packet(send[c])
                self.send_packet(recieve[c], msg)
            raise DisconnectError(f"{send[username]} said bye to {recieve[username]}")

        t1 = threading.Thread(target=message, args=(p1, p2))
        t2 = threading.Thread(target=message, args=(p2, p1))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

server = Server(int(input("Port: ")))
server.accepter.join()
