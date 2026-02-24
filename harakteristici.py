import arcade

# Константы для окна
SCREEN_WIDTH = 1536
SCREEN_HEIGHT = 896
SCREEN_TITLE = "Arcade Game"

# Константы для игры
GRAVITY = 1
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
            "stand_summon": (129, 137),
        },
        "jump_loop": (111, 112),
        # Циклы для рывков персонажа
        "dash_forward_loop": (88, 91),
        "dash_backward_loop": (96, 99),
        "animation_speeds": {
            "idle": 6,
            "move_right": 5,
            "move_left": 5,
            "jump": 3,
            "crouch": 5,
            "dash_forward": 4,
            "dash_backward": 4,
            "stand_summon": 5,
        },
        "crouch_freeze_frame": 45,
        "animation_speed": 5,
        "movement_speed": 4,
        "jump_speed": 15,
        "dash_speed": 15,
        "dash_distance": 220,
        "dash_cooldown": 40,
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
            "stand_summon": (125, 136),
        },
        "jump_loop": (94, 95),
        # Циклы для рывков персонажа
        "dash_forward_loop": (71, 73),
        "dash_backward_loop": (78, 80),
        "animation_speeds": {
            "idle": 8,
            "move_right": 5,
            "move_left": 5,
            "jump": 3,
            "crouch": 5,
            "dash_forward": 4,
            "dash_backward": 2,
            "stand_summon": 3,
        },
        "crouch_freeze_frame": 31,
        "animation_speed": 5,
        "movement_speed": 3,
        "jump_speed": 15,
        "dash_speed": 12,
        "dash_distance": 220,
        "dash_cooldown": 35,
        "sprite_scale": 2,
        "color": arcade.color.BLUE
    },
}

# База данных стендов
STANDS_DB = {
    "DIO": {
        "display_name": "The World",
        "folder_name": "TheWorld",
        "file_prefix": "TheWorld",
        "frame_ranges": {
            "idle": (0, 4),
            "move_forward": (23, 24),
            "move_backward": (17, 18),
            "jump": (38, 39),
            "dash_forward": (27, 31),
            "dash_backward": (33, 37),
            "summon": (40, 45),
        },
        "jump_loop": (38, 39),
        # Циклы для рывков стенда
        "dash_forward_loop": (28, 29),
        "dash_backward_loop": (34, 35),
        "animation_speeds": {
            "idle": 7,
            "move_forward": 4,
            "move_backward": 4,
            "jump": 3,
            "dash_forward": 9,
            "dash_backward": 7,
            "summon": 6,
        },
        "sprite_scale": 2,
        "offset_x": 30,
        "offset_y": 0,
        "color": arcade.color.GOLD
    },

    "JotaroKujo": {
        "display_name": "Star Platinum",
        "folder_name": "StarPlatinum",
        "file_prefix": "SP",
        "frame_ranges": {
            "idle": (0, 19),
            "move_forward": (41, 47),
            "move_backward": (49, 55),
            "jump": (69, 83),
            "dash_forward": (56, 62),
            "dash_backward": (63, 68),
            "summon": (99, 110),
        },
        "jump_loop": (78, 79),
        # Циклы для рывков стенда
        "dash_forward_loop": (57, 58),
        "dash_backward_loop": (64, 65),
        "animation_speeds": {
            "idle": 7,
            "move_forward": 5,
            "move_backward": 5,
            "jump": 3,
            "dash_forward": 6,
            "dash_backward": 6,
            "summon": 3,
        },
        "sprite_scale": 2,
        "offset_x": -40,
        "offset_y": 0,
        "color": arcade.color.PURPLE
    },
}

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
    return CHARACTERS_DB.get(character_name, None)

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