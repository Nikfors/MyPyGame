import arcade

# Константы для окна
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Arcade Game"

# Константы для игры
GRAVITY = 0.5
GROUND_LEVEL = 150

# База данных персонажей
CHARACTERS_DB = {
    "DIO": {
        "display_name": "DIO",
        "file_prefix": "DIO",
        "health": 100,
        "stand_name": "The World",
        "frame_ranges": {
            "idle": (0, 37),
            "move_right": (54, 69),
            "move_left": (70, 85),
            "jump": (103, 115),
            "crouch": (42, 49),  # Диапазон для приседания
        },
        "crouch_freeze_frame": 45,  # Кадр на котором замираем при приседании
        "animation_speed": 5,
        "movement_speed": 3,
        "jump_speed": 15,
        "sprite_scale": 2,
        "color": arcade.color.YELLOW
    },

    "JotaroKujo": {
        "display_name": "Jotaro Kujo",
        "file_prefix": "Jot",
        "health": 120,
        "stand_name": "Star Platinum",
        "frame_ranges": {
            "idle": (0, 23),
            "move_right": (37, 52),
            "move_left": (53, 68),
            "jump": (84, 99),
            "crouch": (26, 36),  # Диапазон для приседания
        },
        "crouch_freeze_frame": 31,  # Кадр на котором замираем при приседании
        "animation_speed": 5,
        "movement_speed": 3,
        "jump_speed": 15,
        "sprite_scale": 2,
        "color": arcade.color.BLUE
    },
}

# Функция для получения списка доступных персонажей
def get_available_characters():
    return list(CHARACTERS_DB.keys())

# Функция для получения информации о персонаже
def get_character_info(character_name):
    if character_name in CHARACTERS_DB:
        data = CHARACTERS_DB[character_name]
        return {
            "display_name": data["display_name"],
            "color": data["color"],
            "health": data["health"],
            "stand": data["stand_name"],
            "crouch_freeze_frame": data.get("crouch_freeze_frame", None),
            "sprite_scale": data.get("sprite_scale", 0.5)
        }
    return None

# Функция для проверки существования персонажа
def character_exists(character_name):
    return character_name in CHARACTERS_DB

# Функция для получения данных персонажа
def get_character_data(character_name):
    return CHARACTERS_DB.get(character_name, None)

# Функция для получения кадра заморозки приседания
def get_crouch_freeze_frame(character_name):
    if character_name in CHARACTERS_DB:
        return CHARACTERS_DB[character_name].get("crouch_freeze_frame", None)
    return None

# Функция для получения масштаба спрайта
def get_sprite_scale(character_name):
    if character_name in CHARACTERS_DB:
        return CHARACTERS_DB[character_name].get("sprite_scale", 0.5)
    return 0.5