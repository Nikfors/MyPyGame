from flask import Flask, jsonify, request
import threading
import time

app = Flask(__name__)

# Хранилище активных комнат
active_rooms = []
room_counter = 0


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

    room_info = {
        "room_id": room_counter,
        "host_ip": request.remote_addr,
        "host_name": data.get("player_name", "Player 1"),
        "port": 65432,
        "created_at": time.time(),
        "status": "waiting"
    }

    # Удаляем старые комнаты от этого же хоста
    global active_rooms
    active_rooms = [room for room in active_rooms if room['host_ip'] != request.remote_addr]
    active_rooms.append(room_info)

    return jsonify({
        "status": "Room created",
        "room": room_info,
        "room_id": room_counter
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
    app.run(host='0.0.0.0', port=5000, debug=False)