import socket
import threading

class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = None
        self.connections = []

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print("Chat server started on {}:{}".format(self.host, self.port))

        while True:
            client_socket, address = self.server_socket.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    def handle_client(self, client_socket):
        self.connections.append(client_socket)
        while True:
            try:
                message = client_socket.recv(1024).decode()
                if message:
                    print("[Received] {}".format(message))
                    self.broadcast(message, client_socket)
                else:
                    self.remove_client(client_socket)
                    break
            except:
                self.remove_client(client_socket)
                break

    def broadcast(self, message, sender_socket):
        for client_socket in self.connections:
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode())
                except:
                    self.remove_client(client_socket)

    def remove_client(self, client_socket):
        if client_socket in self.connections:
            self.connections.remove(client_socket)
        client_socket.close()

    def stop(self):
        for client_socket in self.connections:
            client_socket.close()
        self.server_socket.close()

class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        print("Connected to {}:{}".format(self.host, self.port))

        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

        while True:
            message = input()
            if message.lower() == "exit":
                break
            self.send(message)

        self.client_socket.close()

    def receive(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    print("[Received] {}".format(message))
                else:
                    break
            except:
                break

    def send(self, message):
        self.client_socket.send(message.encode())

# 在服务器端运行聊天软件
def run_server():
    server = ChatServer('127.0.0.1', 5000)
    server.start()

# 在客户端运行聊天软件
def run_client():
    client = ChatClient('127.0.0.1', 5000)
    client.connect()

if __name__ == "__main__":
    # 启动聊天服务器
    server_thread = threading.Thread(target=run_server)
    server_thread.start()

    # 启动聊天客户端
    client_thread = threading.Thread(target=run_client)
    client_thread.start()
