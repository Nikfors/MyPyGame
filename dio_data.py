import arcade

DIO_CHARACTER = {
    "display_name": "DIO",
    "file_prefix": "DIO",
    "health": 1000,
    "stand_name": "The World",
    "hitbox_size": (80, 200),
    "block_frames": (608, 609),
    "block_offset_x": 40,
    "block_offset_y": 0,
    "block_duration": 30,
    "block_cooldown": 40,

    # ПАРАМЕТРЫ ШКАЛЫ СТЕНДА
    "stand_meter_max": 100,
    "stand_summon_cost": 10,
    "stand_block_drain": 20,
    "stand_block_drain_no_stand": 10,
    "stand_gain_on_hit": 15,
    "stand_gain_on_block": 5,
    "stand_gain_on_attack": 2,
    "stand_passive_gain": 0.1,
    "stand_damage_drain": 15,  # Расход шкалы при получении урона
    "stand_damage_drain_no_stand": 5,  # Расход шкалы при получении урона без стенда

    # ОПТИМИЗИРОВАННЫЙ СЛОВАРЬ АНИМАЦИЙ
    "animations": {
        "idle": ((0, 37), 6),
        "move_right": ((54, 69), 5),
        "move_left": ((70, 85), 5),
        "jump": ((103, 115), 3),
        "crouch": ((42, 49), 4),
        "dash_forward": ((86, 93), 5),
        "dash_backward": ((94, 101), 5),
        "stand_summon": ((129, 137), 5),
        "attack1": ((371, 375), 3),
        "attack2": ((376, 386), 3),
        "attack3": ((387, 398), 3),
        "stand_attack1": ((608, 609), 3),
        "stand_attack2": ((608, 609), 3),
        "stand_attack3": ((608, 609), 4),
        "intro": ((623, 650), 6),
        "victory": ((610, 622), 5),
        "defeat": ((537, 567), 5),
        "hit": ((193, 201), 3),  # Анимация получения урона
    },

    "jump_loop": (111, 112),
    "dash_forward_loop": (88, 91),
    "dash_backward_loop": (96, 99),

    "attacks": {
        "attack1": {
            "damage": 10,
            "knockback": 5,
            "hitbox": (70, 40),
            "offset_x": 90,
            "offset_y": 45,
            "active_frames": (372, 372),
        },
        "attack2": {
            "damage": 12,
            "knockback": 8,
            "hitbox": (45, 75),
            "offset_x": 100,
            "offset_y": 90,
            "active_frames": (379, 380),
        },
        "attack3": {
            "damage": 25,
            "knockback": 50,
            "hitbox": (50, 80),
            "offset_x": 130,
            "offset_y": 30,
            "active_frames": (390, 391),
        },
        "stand_attack1": {
            "damage": 15,
            "knockback": 10,
            "hitbox": (55, 85),
            "offset_x": 150,
            "offset_y": 40,
            "active_frames": (140, 142),
        },
        "stand_attack2": {
            "damage": 18,
            "knockback": 12,
            "hitbox": (60, 90),
            "offset_x": 160,
            "offset_y": 40,
            "active_frames": (169, 170),
        },
        "stand_attack3": {
            "damage": 30,
            "knockback": 25,
            "hitbox": (140, 60),
            "offset_x": 170,
            "offset_y": 100,
            "active_frames": (180, 181),
        },
    },
    "combo_window": 30,
    "crouch_freeze_frame": 45,
    "movement_speed": 2,
    "jump_speed": 15,
    "dash_speed": 15,
    "dash_distance": 250,
    "dash_cooldown": 35,
    "sprite_scale": 2,
    "color": arcade.color.YELLOW
}

DIO_STAND = {
    "display_name": "The World",
    "folder_name": "TheWorld",
    "file_prefix": "TheWorld",
    "animations": {
        "idle": ((0, 4), 7),
        "block": ((47, 48), 6),
        "move_forward": ((23, 24), 4),
        "move_backward": ((17, 18), 4),
        "jump": ((38, 39), 3),
        "dash_forward": ((27, 31), 9),
        "dash_backward": ((33, 37), 7),
        "summon": ((40, 45), 6),
        "attack1": ((142, 149), 3),
        "attack2": ((165, 175), 3),
        "attack3": ((176, 184), 4),
    },
    "jump_loop": (38, 39),
    "dash_forward_loop": (28, 29),
    "dash_backward_loop": (34, 35),
    "sprite_scale": 2,
    "offset_x": 0,
    "offset_y": 0,
    "color": arcade.color.GOLD
}