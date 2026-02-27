from flask import Flask, jsonify, request
import threading
import time
import socket

app = Flask(__name__)

# Хранилище активных комнат
active_rooms = []
room_counter = 0


# Функция для получения реального IP-адреса
def get_real_ip():
    try:
        # Пытаемся получить реальный IP в локальной сети
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        # Проверяем, что это не localhost
        if local_ip.startswith('127.'):
            # Если получили localhost, пробуем другой способ
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Это не создает реального соединения
                s.connect(('8.8.8.8', 80))
                local_ip = s.getsockname()[0]
            finally:
                s.close()
        return local_ip
    except:
        return request.remote_addr


# Удаляем комнаты, которые висят больше 30 секунд без второго игрока
def cleanup_old_rooms():
    while True:
        time.sleep(10)
        current_time = time.time()
        global active_rooms
        active_rooms = [room for room in active_rooms if current_time - room['created_at'] < 30]


# Запускаем поток для очистки
threading.Thread(target=cleanup_old_rooms, daemon=True).start()


@app.route('/create_room', methods=['POST'])
def create_room():
    global room_counter
    data = request.json
    room_counter += 1

    # Получаем реальный IP для подключения
    host_ip = get_real_ip()

    room_info = {
        "room_id": room_counter,
        "host_ip": host_ip,
        "host_name": data.get("player_name", "Player 1"),
        "port": 65432,
        "created_at": time.time(),
        "status": "waiting"
    }

    # Удаляем старые комнаты от этого же хоста
    global active_rooms
    active_rooms = [room for room in active_rooms if room['host_ip'] != host_ip]
    active_rooms.append(room_info)

    print(f"Комната создана: ID={room_counter}, IP={host_ip}")

    return jsonify({
        "status": "Room created",
        "room": room_info,
        "room_id": room_counter,
        "host_ip": host_ip
    })


@app.route('/get_rooms', methods=['GET'])
def get_rooms():
    # Возвращаем только комнаты в статусе waiting
    available_rooms = [room for room in active_rooms if room['status'] == 'waiting']
    return jsonify(available_rooms)


@app.route('/join_room/<int:room_id>', methods=['POST'])
def join_room(room_id):
    data = request.json

    for room in active_rooms:
        if room['room_id'] == room_id and room['status'] == 'waiting':
            room['status'] = 'active'
            room['guest_ip'] = request.remote_addr
            room['guest_name'] = data.get("player_name", "Player 2")

            print(f"Игрок подключился к комнате {room_id}")

            return jsonify({
                "status": "Joined",
                "room": room,
                "host_ip": room['host_ip']
            })

    return jsonify({"status": "Room not found"}), 404


@app.route('/room_status/<int:room_id>', methods=['GET'])
def room_status(room_id):
    for room in active_rooms:
        if room['room_id'] == room_id:
            return jsonify(room)

    return jsonify({"status": "not_found"}), 404


if __name__ == '__main__':
    print("=" * 50)
    print("LOBBY SERVER STARTED ON PORT 5000")
    print("=" * 50)
    # Показываем реальный IP сервера
    try:
        real_ip = get_real_ip()
        print(f"Server IP address: {real_ip}")
        print("Make sure clients can access this IP")
    except:
        pass
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)