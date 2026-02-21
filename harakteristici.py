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
            "crouch": (42, 49),
            "dash_forward": (86, 93),
            "dash_backward": (94, 101),
        },
        # Индивидуальная скорость анимации для каждого действия
        "animation_speeds": {
            "idle": 5,           # Медленная анимация бездействия
            "move_right": 4,      # Средняя скорость движения
            "move_left": 4,       # Средняя скорость движения
            "jump": 4,            # Быстрая анимация прыжка
            "crouch": 5,          # Средняя скорость приседания
            "dash_forward": 4,    # Очень быстрая анимация рывка (чтобы все кадры успели проиграться)
            "dash_backward": 4,   # Очень быстрая анимация рывка
        },
        "crouch_freeze_frame": 45,
        "animation_speed": 5,      # Базовая скорость (будет использоваться если нет индивидуальной)
        "movement_speed": 4,
        "jump_speed": 10,
        "dash_speed": 11,          # Увеличил скорость рывка
        "dash_distance": SCREEN_WIDTH // 3,
        "dash_cooldown": 50,
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
            "crouch": (26, 36),
            "dash_forward": (69, 75),
            "dash_backward": (76, 82),
        },
        # Индивидуальная скорость анимации для каждого действия
        "animation_speeds": {
            "idle": 7,
            "move_right": 5,
            "move_left": 5,
            "jump": 3,
            "crouch": 5,
            "dash_forward": 2,     # Быстрая анимация рывка
            "dash_backward": 2,     # Быстрая анимация рывка
        },
        "crouch_freeze_frame": 31,
        "animation_speed": 5,
        "movement_speed": 3,
        "jump_speed": 10,
        "dash_speed": 12,
        "dash_distance": 150,
        "dash_cooldown": 35,
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
            "sprite_scale": data.get("sprite_scale", 0.5),
            "dash_speed": data.get("dash_speed", 8),
            "dash_distance": data.get("dash_distance", 100),
            "dash_cooldown": data.get("dash_cooldown", 45),
            "animation_speeds": data.get("animation_speeds", {})
        }
    return None

# Функция для проверки существования персонажа
def character_exists(character_name):
    return character_name in CHARACTERS_DB

# Функция для получения данных персонажа
def get_character_data(character_name):
    return CHARACTERS_DB.get(character_name, None)

# Функция для получения скорости анимации для конкретного действия
def get_action_animation_speed(character_name, action):
    if character_name in CHARACTERS_DB:
        character_data = CHARACTERS_DB[character_name]
        # Сначала проверяем индивидуальные скорости
        if "animation_speeds" in character_data and action in character_data["animation_speeds"]:
            return character_data["animation_speeds"][action]
        # Если нет индивидуальной, возвращаем базовую скорость
        return character_data.get("animation_speed", 5)
    return 5

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