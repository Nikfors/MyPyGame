import socket
import pickle
import threading
import time
from enum import Enum


class GameMessageType(Enum):
    PLAYER_STATE = 1
    GAME_START = 2
    GAME_END = 3
    PING = 4
    PONG = 5


class GameServer:
    def __init__(self, host='0.0.0.0', port=65432):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.running = False
        self.connected = False

    def start(self):
        """Запуск сервера и ожидание подключения"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.running = True

            print(f"Сервер запущен на {self.host}:{self.port}, ожидание подключения...")

            # Устанавливаем таймаут для возможности проверки running
            self.server_socket.settimeout(1.0)

            while self.running and not self.connected:
                try:
                    self.client_socket, self.client_address = self.server_socket.accept()
                    # Устанавливаем таймаут для сокета клиента
                    self.client_socket.settimeout(5.0)
                    self.connected = True
                    print(f"Клиент подключился: {self.client_address}")
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        print(f"Ошибка при подключении: {e}")
                    break

            return self.connected
        except Exception as e:
            print(f"Ошибка запуска сервера: {e}")
            return False

    def stop(self):
        """Остановка сервера"""
        self.running = False
        self.connected = False
        try:
            if self.client_socket:
                self.client_socket.close()
            if self.server_socket:
                self.server_socket.close()
        except:
            pass
        print("Сервер остановлен")

    def send_state(self, player_state):
        """Отправка состояния игрока"""
        if not self.connected or not self.client_socket:
            return False

        try:
            data = pickle.dumps({
                'type': GameMessageType.PLAYER_STATE,
                'data': player_state
            })
            self.client_socket.sendall(len(data).to_bytes(4, 'big') + data)
            return True
        except socket.timeout:
            print("Таймаут отправки")
            self.connected = False
            return False
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            self.connected = False
            return False

    def receive_state(self):
        """Получение состояния противника"""
        if not self.connected or not self.client_socket:
            return None

        try:
            # Получаем размер сообщения
            size_data = self.client_socket.recv(4)
            if not size_data:
                self.connected = False
                return None

            msg_size = int.from_bytes(size_data, 'big')

            # Получаем само сообщение
            data = b''
            while len(data) < msg_size:
                try:
                    chunk = self.client_socket.recv(min(msg_size - len(data), 4096))
                    if not chunk:
                        self.connected = False
                        return None
                    data += chunk
                except socket.timeout:
                    continue

            msg = pickle.loads(data)
            return msg['data']
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Ошибка получения: {e}")
            self.connected = False
            return None


class GameClient:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.server_address = None

    def connect(self, host, port=65432):
        """Подключение к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Устанавливаем таймаут на подключение
            self.socket.settimeout(5.0)
            self.socket.connect((host, port))
            # Устанавливаем таймаут на операции
            self.socket.settimeout(1.0)
            self.connected = True
            self.server_address = (host, port)
            print(f"Подключено к серверу {host}:{port}")
            return True
        except socket.timeout:
            print(f"Таймаут подключения к {host}:{port}")
            return False
        except ConnectionRefusedError:
            print(f"Соединение отклонено {host}:{port} - сервер не запущен")
            return False
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def disconnect(self):
        """Отключение от сервера"""
        self.connected = False
        try:
            if self.socket:
                self.socket.close()
        except:
            pass
        print("Отключено от сервера")

    def send_state(self, player_state):
        """Отправка состояния игрока"""
        if not self.connected or not self.socket:
            return False

        try:
            data = pickle.dumps({
                'type': GameMessageType.PLAYER_STATE,
                'data': player_state
            })
            self.socket.sendall(len(data).to_bytes(4, 'big') + data)
            return True
        except socket.timeout:
            print("Таймаут отправки")
            self.connected = False
            return False
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            self.connected = False
            return False

    def receive_state(self):
        """Получение состояния противника"""
        if not self.connected or not self.socket:
            return None

        try:
            size_data = self.socket.recv(4)
            if not size_data:
                self.connected = False
                return None

            msg_size = int.from_bytes(size_data, 'big')

            data = b''
            while len(data) < msg_size:
                try:
                    chunk = self.socket.recv(min(msg_size - len(data), 4096))
                    if not chunk:
                        self.connected = False
                        return None
                    data += chunk
                except socket.timeout:
                    continue

            msg = pickle.loads(data)
            return msg['data']
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Ошибка получения: {e}")
            self.connected = False
            return None