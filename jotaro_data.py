import arcade

JOTARO_CHARACTER = {
    "display_name": "Jotaro Kujo",
    "file_prefix": "Jot",
    "health": 1000,
    "stand_name": "Star Platinum",
    "hitbox_size": (80, 200),
    "block_frames": (688, 694),  # Кадры для анимации блока (для Jotaro это 688-694)
    "block_offset_x": 40,  # Смещение спрайта блока по X
    "block_offset_y": 0,  # Смещение спрайта блока по Y
    "block_duration": 30,  # Длительность блока в кадрах
    "block_cooldown": 40,  # Перезарядка блока

    # ПАРАМЕТРЫ ШКАЛЫ СТЕНДА (индивидуальные для персонажа)
    "stand_meter_max": 100,
    "stand_summon_cost": 10,
    "stand_block_drain": 20,  # Расход при блоке со стендом
    "stand_block_drain_no_stand": 10,  # Расход при блоке без стенда
    "stand_gain_on_hit": 15,  # Пополнение при получении урона
    "stand_gain_on_block": 5,  # Пополнение при блоке
    "stand_gain_on_attack": 2,  # Пополнение при атаке
    "stand_passive_gain": 0.1,  # Пассивное пополнение

    "frame_ranges": {
        "block": (688, 694),
        "idle": (0, 23),
        "move_right": (37, 52),
        "move_left": (53, 68),
        "jump": (84, 99),
        "crouch": (26, 36),
        "dash_forward": (69, 75),
        "dash_backward": (76, 82),
        "stand_summon": (125, 136),
        "attack1": (452, 457),
        "attack2": (458, 466),
        "attack3": (467, 476),
        "stand_attack1": (688, 694),
        "stand_attack2": (688, 694),
        "stand_attack3": (153, 160),
        "intro": (0, 37),
        "victory": (526, 576),
        "defeat": (323, 341)
    },
    "jump_loop": (94, 95),
    "dash_forward_loop": (71, 73),
    "dash_backward_loop": (78, 80),
    "animation_speeds": {
        "idle": 8,
        "move_right": 5,
        "move_left": 5,
        "jump": 3,
        "crouch": 5,
        "dash_forward": 4,
        "dash_backward": 4,
        "stand_summon": 3,
        "attack1": 3,
        "attack2": 3,
        "attack3": 4,
        "stand_attack1": 3,
        "stand_attack2": 3,
        "stand_attack3": 4,
        "intro": 6,
        "victory": 5,
        "defeat": 5
    },
    "attacks": {
        "attack1": {
            "damage": 15,
            "knockback": 5,
            "hitbox": (50, 75),
            "offset_x": 85,
            "offset_y": 10,
            "active_frames": (453, 454),
        },
        "attack2": {
            "damage": 20,
            "knockback": 8,
            "hitbox": (50, 50),
            "offset_x": 130,
            "offset_y": -70,
            "active_frames": (461, 461),
        },
        "attack3": {
            "damage": 50,
            "knockback": 18,
            "hitbox": (65, 85),
            "offset_x": 110,
            "offset_y": 45,
            "active_frames": (470, 470),
        },
        "stand_attack1": {
            "damage": 12,
            "knockback": 10,
            "hitbox": (65, 95),
            "offset_x": 130,
            "offset_y": 45,
            "active_frames": (266, 266),
        },
        "stand_attack2": {
            "damage": 15,
            "knockback": 12,
            "hitbox": (75, 95),
            "offset_x": 80,
            "offset_y": 45,
            "active_frames": (287, 287),
        },
        "stand_attack3": {
            "damage": 25,
            "knockback": 22,
            "hitbox": (85, 105),
            "offset_x": 85,
            "offset_y": 45,
            "active_frames": (304, 305),
        },
    },
    "combo_window": 30,
    "crouch_freeze_frame": 31,
    "animation_speed": 5,
    "movement_speed": 3,
    "jump_speed": 15,
    "dash_speed": 15,
    "dash_distance": 250,
    "dash_cooldown": 35,
    "sprite_scale": 2,
    "color": arcade.color.BLUE
}

JOTARO_STAND = {
    "display_name": "Star Platinum",
    "folder_name": "StarPlatinum",
    "file_prefix": "SP",
    "frame_ranges": {
        "idle": (0, 19),
        "block": (114, 119),
        "move_forward": (41, 47),
        "move_backward": (49, 55),
        "jump": (69, 83),
        "dash_forward": (56, 62),
        "dash_backward": (63, 68),
        "summon": (99, 110),
        "attack1": (266, 270),
        "attack2": (282, 293),
        "attack3": (301, 313),
    },
    "jump_loop": (78, 79),
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
}