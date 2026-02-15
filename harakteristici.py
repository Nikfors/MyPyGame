import arcade

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
        },
        "animation_speed": 5,
        "movement_speed": 4,
        "jump_speed": 14,
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
        },
        "animation_speed": 4,
        "movement_speed": 4,
        "jump_speed": 13,
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
            "stand": data["stand_name"]
        }
    return None


# Функция для проверки существования персонажа
def character_exists(character_name):
    return character_name in CHARACTERS_DB


# Функция для получения данных персонажа
def get_character_data(character_name):
    return CHARACTERS_DB.get(character_name, None)