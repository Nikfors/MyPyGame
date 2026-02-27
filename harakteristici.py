import arcade

# Импортируем данные из отдельных файлов персонажей
from dio_data import DIO_CHARACTER, DIO_STAND
from jotaro_data import JOTARO_CHARACTER, JOTARO_STAND

# Константы для окна
SCREEN_WIDTH = 1536
SCREEN_HEIGHT = 896
SCREEN_TITLE = "Arcade Game"

# Константы для игры
GRAVITY = 1
GROUND_LEVEL = 150

# Формируем базу данных персонажей
CHARACTERS_DB = {
    "DIO": DIO_CHARACTER,
    "JotaroKujo": JOTARO_CHARACTER,
}

# Формируем базу данных стендов
STANDS_DB = {
    "DIO": DIO_STAND,
    "JotaroKujo": JOTARO_STAND,
}

# Функции получения данных
def get_available_characters():
    return list(CHARACTERS_DB.keys())

def get_character_info(character_name):
    if character_name in CHARACTERS_DB:
        data = CHARACTERS_DB[character_name]
        return data
    return None

def character_exists(character_name):
    return character_name in CHARACTERS_DB

def get_character_data(character_name):
    """Получение данных персонажа"""
    if character_name in CHARACTERS_DB:
        data = CHARACTERS_DB[character_name].copy()
        # Убедимся, что hitbox_size есть
        if "hitbox_size" not in data:
            data["hitbox_size"] = (60, 120)  # Значение по умолчанию
        return data
    return None

def get_stand_data(character_name):
    return STANDS_DB.get(character_name, None)

def stand_exists(character_name):
    return character_name in STANDS_DB

def get_action_animation_speed(character_name, action):
    if character_name in CHARACTERS_DB:
        character_data = CHARACTERS_DB[character_name]
        if "animation_speeds" in character_data and action in character_data["animation_speeds"]:
            return character_data["animation_speeds"][action]
        return character_data.get("animation_speed", 5)
    return 5

def get_crouch_freeze_frame(character_name):
    if character_name in CHARACTERS_DB:
        return CHARACTERS_DB[character_name].get("crouch_freeze_frame", None)
    return None

def get_sprite_scale(character_name):
    if character_name in CHARACTERS_DB:
        return CHARACTERS_DB[character_name].get("sprite_scale", 0.5)
    return 0.5

def get_attack_data(character_name, attack_name):
    if character_name in CHARACTERS_DB:
        attacks = CHARACTERS_DB[character_name].get("attacks", {})
        return attacks.get(attack_name, None)
    return None

def get_combo_window(character_name):
    if character_name in CHARACTERS_DB:
        return CHARACTERS_DB[character_name].get("combo_window", 30)
    return 30