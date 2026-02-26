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
        "health": 500,
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
            # Атаки без стенда
            "attack1": (371, 375),
            "attack2": (376, 386),
            "attack3": (387, 398),
            # Атаки со стендом
            "stand_attack1": (608, 609),
            "stand_attack2": (608, 609),
            "stand_attack3": (608, 609),
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
            "attack1": 3,
            "attack2": 3,
            "attack3": 4,
            "stand_attack1": 3,
            "stand_attack2": 3,
            "stand_attack3": 4,
        },
        # Данные атак
        "attacks": {
            "attack1": {
                "damage": 10,
                "knockback": 5,
                "hitbox": (50, 80),  # ширина, высота
                "offset_x": 60,  # смещение хитбокса от центра
                "active_frames": (372, 372),  # кадры, на которых активен удар
            },
            "attack2": {
                "damage": 12,
                "knockback": 8,
                "hitbox": (60, 80),
                "offset_x": 65,
                "active_frames": (379, 380),
            },
            "attack3": {
                "damage": 25,
                "knockback": 20,
                "hitbox": (70, 90),
                "offset_x": 70,
                "active_frames": (390, 391),
            },
            "stand_attack1": {
                "damage": 15,
                "knockback": 10,
                "hitbox": (70, 100),
                "offset_x": 10,
                "active_frames": (140, 142),
            },
            "stand_attack2": {
                "damage": 18,
                "knockback": 12,
                "hitbox": (80, 100),
                "offset_x": 85,
                "active_frames": (169, 170),
            },
            "stand_attack3": {
                "damage": 30,
                "knockback": 25,
                "hitbox": (90, 110),
                "offset_x": 90,
                "active_frames": (180, 181),
            },
        },
        "combo_window": 30,  # кадров для продолжения комбо
        "crouch_freeze_frame": 45,
        "animation_speed": 5,
        "movement_speed": 2,
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
            # Атаки без стенда
            "attack1": (452, 457),
            "attack2": (458, 466),
            "attack3": (467, 476),
            # Атаки со стендом
            "stand_attack1": (688, 694),
            "stand_attack2": (688, 694),
            "stand_attack3": (153, 160),
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
            "attack1": 3,
            "attack2": 3,
            "attack3": 4,
            "stand_attack1": 3,
            "stand_attack2": 3,
            "stand_attack3": 4,
        },
        # Данные атак
        "attacks": {
            "attack1": {
                "damage": 8,
                "knockback": 5,
                "hitbox": (45, 75),
                "offset_x": 55,
                "active_frames": (102, 104),
            },
            "attack2": {
                "damage": 10,
                "knockback": 8,
                "hitbox": (55, 75),
                "offset_x": 60,
                "active_frames": (108, 110),
            },
            "attack3": {
                "damage": 20,
                "knockback": 18,
                "hitbox": (65, 85),
                "offset_x": 65,
                "active_frames": (115, 117),
            },
            "stand_attack1": {
                "damage": 12,
                "knockback": 10,
                "hitbox": (65, 95),
                "offset_x": 75,
                "active_frames": (266, 266),
            },
            "stand_attack2": {
                "damage": 15,
                "knockback": 12,
                "hitbox": (75, 95),
                "offset_x": 80,
                "active_frames": (169, 170),
            },
            "stand_attack3": {
                "damage": 25,
                "knockback": 22,
                "hitbox": (85, 105),
                "offset_x": 85,
                "active_frames": (155, 158),
            },
        },
        "combo_window": 30,  # кадров для продолжения комбо
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

# База данных стендов (без изменений)
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
            # Атаки стенда
            "attack1": (142, 149),
            "attack2": (165, 175),
            "attack3": (176, 184),
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
            "attack1": 4,
            "attack2": 4,
            "attack3": 5,
        },
        "sprite_scale": 2,
        "offset_x": 0,
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
            # Атаки стенда
            "attack1": (266, 270),
            "attack2": (282, 293),
            "attack3": (301, 313),
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
            "attack1": 4,
            "attack2": 4,
            "attack3": 5,
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

def get_attack_data(character_name, attack_name):
    """Получить данные конкретной атаки персонажа"""
    if character_name in CHARACTERS_DB:
        attacks = CHARACTERS_DB[character_name].get("attacks", {})
        return attacks.get(attack_name, None)
    return None

def get_combo_window(character_name):
    """Получить окно комбо для персонажа"""
    if character_name in CHARACTERS_DB:
        return CHARACTERS_DB[character_name].get("combo_window", 30)
    return 30