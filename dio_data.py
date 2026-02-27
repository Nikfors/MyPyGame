import arcade

DIO_CHARACTER = {
    "display_name": "DIO",
    "file_prefix": "DIO",
    "health": 500,
    "stand_name": "The World",
    "hitbox_size": (80, 200),
    "block_frames": (608, 609),  # Кадры для анимации блока (для DIO это 608-609)
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
    "stand_passive_gain": 0.1,

    "frame_ranges": {
        "block": (608, 609),
        "idle": (0, 37),
        "move_right": (54, 69),
        "move_left": (70, 85),
        "jump": (103, 115),
        "crouch": (42, 49),
        "dash_forward": (86, 93),
        "dash_backward": (94, 101),
        "stand_summon": (129, 137),
        "attack1": (371, 375),
        "attack2": (376, 386),
        "attack3": (387, 398),
        "stand_attack1": (608, 609),
        "stand_attack2": (608, 609),
        "stand_attack3": (608, 609),
    },
    "jump_loop": (111, 112),
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
    "attacks": {
        "attack1": {
            "damage": 10,
            "knockback": 5,
            "hitbox": (70, 40),
            "offset_x": 150,
            "offset_y": 45,           # По центру
            "active_frames": (372, 372),
        },
        "attack2": {
            "damage": 12,
            "knockback": 8,
            "hitbox": (45, 75),
            "offset_x": 160,
            "offset_y": 90,            # Чуть выше (удар в голову)
            "active_frames": (379, 380),
        },
        "attack3": {
            "damage": 25,
            "knockback": 20,
            "hitbox": (50, 80),
            "offset_x": 45,
            "offset_y": 30,           # Чуть ниже (удар в ноги)
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
            "offset_y": 40,           # Стенд бьет сверху
            "active_frames": (169, 170),
        },
        "stand_attack3": {
            "damage": 30,
            "knockback": 25,
            "hitbox": (140, 60),
            "offset_x": 160,
            "offset_y": 100,          # Стенд бьет снизу
            "active_frames": (180, 181),
        },
    },
    "combo_window": 30,
    "crouch_freeze_frame": 45,
    "animation_speed": 5,
    "movement_speed": 2,
    "jump_speed": 15,
    "dash_speed": 15,
    "dash_distance": 220,
    "dash_cooldown": 40,
    "sprite_scale": 2,
    "color": arcade.color.YELLOW
}

DIO_STAND = {
    "display_name": "The World",
    "folder_name": "TheWorld",
    "file_prefix": "TheWorld",
    "frame_ranges": {
        "idle": (0, 4),
        "block": (40, 45),
        "move_forward": (23, 24),
        "move_backward": (17, 18),
        "jump": (38, 39),
        "dash_forward": (27, 31),
        "dash_backward": (33, 37),
        "summon": (40, 45),
        "attack1": (142, 149),
        "attack2": (165, 175),
        "attack3": (176, 184),
    },
    "jump_loop": (38, 39),
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
}