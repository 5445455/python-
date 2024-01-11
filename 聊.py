import tkinter as tk
import socket
import threading
import sqlite3

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
    def __init__(self, host, port, username):
        self.host = host
        self.port = port
        self.username = username
        self.client_socket = None

    def connect(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        print("Connected to {}:{}".format(self.host, self.port))

        receive_thread = threading.Thread(target=self.receive)
        receive_thread.start()

    def receive(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                if message:
                    print("[Received] {}".format(message))
                    chat_window.add_message(message)
                else:
                    break
            except:
                break

    def send(self, message):
        message = "{}: {}".format(self.username, message)
        try:
            self.client_socket.send(message.encode())
            chat_window.add_message(message)
        except:
            print("Failed to send message")

# 创建用户管理类
class UserManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.connection = None
        self.cursor = None
        self.create_table()

    def create_table(self):
        self.connection = sqlite3.connect(self.db_file)
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)")
        self.connection.commit()

    def register_user(self, username, password):
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            self.connection.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username, password):
        self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        result = self.cursor.fetchone()
        if result:
            return True
        else:
            return False

# 创建聊天窗口类
class ChatWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Chatroom")
        self.chat_frame = tk.Frame(self.root)
        self.chat_frame.pack(padx=10, pady=10)
        self.message_listbox = tk.Listbox(self.chat_frame, width=130, height=20)
        self.message_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar = tk.Scrollbar(self.chat_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.message_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.message_listbox.yview)
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(padx=10, pady=10)
        self.username_label = tk.Label(self.input_frame, text="Username:")
        self.username_label.pack(side=tk.LEFT)
        self.username_entry = tk.Entry(self.input_frame)
        self.username_entry.pack(side=tk.LEFT)
        self.password_label = tk.Label(self.input_frame, text="Password:")
        self.password_label.pack(side=tk.LEFT)
        self.password_entry = tk.Entry(self.input_frame, show="*")
        self.password_entry.pack(side=tk.LEFT)
        self.register_button = tk.Button(self.input_frame, text="Register", command=self.register_user)
        self.register_button.pack(side=tk.LEFT)
        self.connect_button = tk.Button(self.input_frame, text="Connect", command=self.connect)
        self.connect_button.pack(side=tk.LEFT, padx=10)
        self.message_entry = tk.Entry(self.input_frame, width=50)
        self.message_entry.pack(side=tk.LEFT, padx=10)
        self.send_button = tk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.LEFT)
        self.client = None
        self.user_manager = UserManager("users.db")

    def register_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if username == "" or password == "":
            return

        if self.user_manager.register_user(username, password):
            print("User registered successfully")
        else:
            print("Username already exists")

    def connect(self):
        if self.client is None:
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()

            if username == "" or password == "":
                return

            if not self.user_manager.verify_user(username, password):
                print("Invalid username or password")
                return

            self.client = ChatClient('127.0.0.1', 5000, username)
            self.client.connect()
            self.connect_button.config(text="Disconnect")
        else:
            self.client.client_socket.close()
            self.client = None
            self.connect_button.config(text="Connect")

    def send_message(self):
        if self.client is not None:
            message = self.message_entry.get().strip()
            if message != "":
                self.client.send(message)
                self.message_entry.delete(0, tk.END)

    def add_message(self, message):
        self.message_listbox.insert(tk.END, message)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    # 启动聊天服务器
    server_thread = threading.Thread(target=ChatServer('127.0.0.1', 5000).start)
    server_thread.start()

    # 创建聊天窗口并运行应用程序
    chat_window = ChatWindow()
    chat_window.run()
