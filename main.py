import arcade
import random
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from harakteristici import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, GRAVITY, GROUND_LEVEL,
    get_available_characters,
    get_character_info,
    character_exists,
    get_character_data,
    get_crouch_freeze_frame,
    get_sprite_scale,
    get_stand_data,
    get_attack_data,
    get_combo_window
)

# Константы для меню
MENU_FONT_SIZE = 24
MENU_FONT_COLOR = arcade.color.WHITE
MENU_SELECTED_COLOR = arcade.color.YELLOW

# Константы для атак
ATTACK_COOLDOWN = 20
HIT_COOLDOWN = 30
KNOCKBACK_DURATION = 10

# Константы для комбо
COMBO_WINDOW = 30

# Константы для защиты
BLOCK_DURATION = 30

# Константы для анимаций
INTRO_ANIMATION_DURATION = 200
VICTORY_ANIMATION_DURATION = 200
INTRO_FIGHT_DURATION = 200

# Константы для шкалы стенда
STAND_METER_MAX = 100
STAND_METER_SUMMON_COST = 10
STAND_METER_BLOCK_DRAIN = 20
STAND_METER_BLOCK_DRAIN_NO_STAND = 10
STAND_METER_GAIN_ON_HIT = 15
STAND_METER_GAIN_ON_BLOCK = 5
STAND_METER_GAIN_ON_ATTACK = 2
STAND_METER_PASSIVE_GAIN = 0.1

# Константы для очков
POINTS_PER_KILL = 100
POINTS_PER_HIT = 10
POINTS_PER_COMBO = 25
POINTS_PER_BLOCK = 5
POINTS_PER_DASH = 2
POINTS_PER_JUMP = 1
POINTS_PER_STAND_SUMMON = 15
POINTS_WIN_BONUS = 50

# Константы для урона стенду
STAND_DAMAGE_DRAIN = 15
STAND_DAMAGE_DRAIN_NO_STAND = 5


class Database:
    """Класс для работы с базой данных SQLite"""

    def __init__(self, db_name="players.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Таблица игроков
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                total_points INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                kills INTEGER DEFAULT 0,
                hits_landed INTEGER DEFAULT 0,
                blocks_successful INTEGER DEFAULT 0,
                dashes_used INTEGER DEFAULT 0,
                jumps_used INTEGER DEFAULT 0,
                stands_summoned INTEGER DEFAULT 0,
                combos_completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_played TIMESTAMP
            )
        ''')

        # Таблица истории матчей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player1_name TEXT,
                player2_name TEXT,
                winner_name TEXT,
                player1_points INTEGER,
                player2_points INTEGER,
                match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player1_name) REFERENCES players(name),
                FOREIGN KEY (player2_name) REFERENCES players(name),
                FOREIGN KEY (winner_name) REFERENCES players(name)
            )
        ''')

        conn.commit()
        conn.close()

    def get_or_create_player(self, name):
        """Получить игрока или создать нового"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM players WHERE name = ?", (name,))
        player = cursor.fetchone()

        if not player:
            cursor.execute(
                "INSERT INTO players (name, total_points) VALUES (?, 0)",
                (name,)
            )
            conn.commit()
            cursor.execute("SELECT * FROM players WHERE name = ?", (name,))
            player = cursor.fetchone()

        conn.close()
        return player

    def update_player_stats(self, name, stats):
        """Обновить статистику игрока"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # Обновляем поля
        set_clause = ", ".join([f"{key} = {key} + ?" for key in stats.keys()])
        values = list(stats.values()) + [name]

        cursor.execute(
            f"UPDATE players SET {set_clause}, last_played = CURRENT_TIMESTAMP WHERE name = ?",
            values
        )

        conn.commit()
        conn.close()

    def save_match(self, player1_name, player2_name, winner_name, player1_points, player2_points):
        """Сохранить информацию о матче"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute(
            """INSERT INTO matches 
               (player1_name, player2_name, winner_name, player1_points, player2_points) 
               VALUES (?, ?, ?, ?, ?)""",
            (player1_name, player2_name, winner_name, player1_points, player2_points)
        )

        conn.commit()
        conn.close()

    def get_leaderboard(self, limit=10):
        """Получить таблицу лидеров"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT name, total_points, games_played, wins, losses, 
                   kills, hits_landed, combos_completed
            FROM players 
            ORDER BY total_points DESC 
            LIMIT ?
        ''', (limit,))

        leaders = cursor.fetchall()
        conn.close()
        return leaders

    def get_player_history(self, name, limit=5):
        """Получить историю матчей игрока"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT player1_name, player2_name, winner_name, 
                   player1_points, player2_points, match_date
            FROM matches 
            WHERE player1_name = ? OR player2_name = ?
            ORDER BY match_date DESC 
            LIMIT ?
        ''', (name, name, limit))

        history = cursor.fetchall()
        conn.close()
        return history


class PlayerStats:
    """Класс для сбора статистики игрока во время боя"""

    def __init__(self, player_name):
        self.player_name = player_name
        self.hits_landed = 0
        self.blocks_successful = 0
        self.dashes_used = 0
        self.jumps_used = 0
        self.stands_summoned = 0
        self.combos_completed = 0
        self.kills = 0
        self.points_earned = 0

    def add_hit(self):
        self.hits_landed += 1
        self.points_earned += POINTS_PER_HIT

    def add_block(self):
        self.blocks_successful += 1
        self.points_earned += POINTS_PER_BLOCK

    def add_dash(self):
        self.dashes_used += 1
        self.points_earned += POINTS_PER_DASH

    def add_jump(self):
        self.jumps_used += 1
        self.points_earned += POINTS_PER_JUMP

    def add_stand_summon(self):
        self.stands_summoned += 1
        self.points_earned += POINTS_PER_STAND_SUMMON

    def add_combo(self):
        self.combos_completed += 1
        self.points_earned += POINTS_PER_COMBO

    def add_kill(self):
        self.kills += 1
        self.points_earned += POINTS_PER_KILL

    def add_win_bonus(self):
        self.points_earned += POINTS_WIN_BONUS

    def get_stats_dict(self):
        """Получить словарь статистики для обновления в БД"""
        return {
            "total_points": self.points_earned,
            "games_played": 1,
            "wins": 1 if self.kills > 0 else 0,
            "losses": 1 if self.kills == 0 else 0,
            "kills": self.kills,
            "hits_landed": self.hits_landed,
            "blocks_successful": self.blocks_successful,
            "dashes_used": self.dashes_used,
            "jumps_used": self.jumps_used,
            "stands_summoned": self.stands_summoned,
            "combos_completed": self.combos_completed
        }


class StartView(arcade.View):
    def __init__(self):
        super().__init__()
        self.logo = None
        path = Path("Лого") / "jojo_logo.png"
        if path.exists():
            self.logo = arcade.load_texture(str(path))

        self.text_obj = arcade.Text("PUSH START BUTTON (ENTER)", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150,
                                    arcade.color.BLACK, 20, anchor_x="center", bold=True)
        self.show_text = True
        self.timer = 0

    def on_draw(self):
        self.clear()
        arcade.set_background_color(arcade.color.WHITE)
        if self.logo:
            arcade.draw_texture_rect(self.logo, arcade.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, 600, 300))
        if self.show_text:
            self.text_obj.draw()

    def on_update(self, delta_time):
        self.timer += delta_time
        if self.timer > 0.5:
            self.show_text = not self.show_text
            self.timer = 0

    def on_key_press(self, key, modifiers):
        self.window.on_key_press(key, modifiers)
        if key == arcade.key.ENTER:
            print("Переход в меню режимов")
            self.window.show_view(ModeMenuView())


class Stand(arcade.Sprite):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.stand_data = get_stand_data(owner.character_name)
        self.folder_name = self.stand_data["folder_name"]
        self.file_prefix = self.stand_data["file_prefix"]

        # Используем animations словарь
        self.animations = self.stand_data["animations"]
        self.frame_ranges = {}
        self.animation_speeds = {}
        for anim_name, (frames, speed) in self.animations.items():
            self.frame_ranges[anim_name] = frames
            self.animation_speeds[anim_name] = speed

        self.jump_loop = self.stand_data.get("jump_loop", None)

        self.scale = self.stand_data["sprite_scale"]

        self.all_textures = [{}, {}]
        self.load_all_textures()

        self.current_direction = owner.current_direction
        self.current_action = "summon"
        self.current_frame = self.frame_ranges["summon"][0]
        self.frame_counter = 0
        self.is_summoning = True

        self.is_attacking = False
        self.current_combo = 0
        self.attack_timer = 0
        self.has_hit_in_this_attack = False
        self.attack_duration = 0

        texture = self.get_current_texture(self.current_frame)
        if texture:
            self.texture = texture

    def load_all_textures(self):
        stand_path = Path("Спрайты") / self.folder_name
        max_frame = 0
        for start, end in self.frame_ranges.values():
            max_frame = max(max_frame, end)

        for i in range(max_frame + 1):
            filename = f"{self.file_prefix}_0-{i}.png"
            file_path = stand_path / filename

            if file_path.exists():
                try:
                    texture_normal = arcade.load_texture(str(file_path))
                    self.all_textures[0][i] = texture_normal
                    self.all_textures[1][i] = texture_normal.flip_left_right()
                except Exception as e:
                    print(f"Ошибка загрузки стенда {filename}: {e}")
                    self.all_textures[0][i] = None
                    self.all_textures[1][i] = None
            else:
                self.all_textures[0][i] = None
                self.all_textures[1][i] = None

    def get_current_texture(self, frame_number):
        if frame_number in self.all_textures[self.current_direction] and self.all_textures[self.current_direction][
            frame_number]:
            return self.all_textures[self.current_direction][frame_number]
        other_dir = 1 - self.current_direction
        if frame_number in self.all_textures[other_dir] and self.all_textures[other_dir][frame_number]:
            return self.all_textures[other_dir][frame_number]
        return None

    def set_action(self, new_action):
        if new_action == self.current_action or new_action not in self.frame_ranges:
            return
        self.current_action = new_action
        self.current_frame = self.frame_ranges[new_action][0]
        self.frame_counter = 0

    def start_attack(self, combo_number):
        """Запуск атаки стенда по номеру"""
        # Проверяем, что такая атака существует
        attack_name = f"attack{combo_number}"
        if attack_name not in self.frame_ranges:
            print(f"Атака стенда {attack_name} не найдена")
            return False

        self.current_combo = combo_number
        self.is_attacking = True
        self.has_hit_in_this_attack = False

        self.set_action(attack_name)
        start_frame, end_frame = self.frame_ranges[attack_name]
        frame_count = end_frame - start_frame + 1
        anim_speed = self.animation_speeds.get(attack_name, 5)
        self.attack_duration = frame_count * anim_speed
        self.attack_timer = self.attack_duration

        print(f"Стенд атакует! Атака {combo_number}, длительность: {self.attack_duration} кадров")
        return True

    def check_attack_hit(self, opponent):
        if not self.is_attacking or self.has_hit_in_this_attack or not opponent:
            return False

        stand_attack_name = f"stand_attack{self.current_combo}"
        attack_data = get_attack_data(self.owner.character_name, stand_attack_name)

        if not attack_data:
            return False

        active_frames = attack_data.get("active_frames", (0, 0))
        if self.current_frame < active_frames[0] or self.current_frame > active_frames[1]:
            return False

        if opponent.hit_cooldown > 0:
            return False

        hitbox_width, hitbox_height = attack_data.get("hitbox", (80, 100))
        offset_x = attack_data.get("offset_x", 80)
        offset_y = attack_data.get("offset_y", 0)

        if self.owner.facing_right:
            hitbox_left = self.owner.center_x + offset_x - hitbox_width // 2
        else:
            hitbox_left = self.owner.center_x - offset_x - hitbox_width // 2

        hitbox_right = hitbox_left + hitbox_width
        hitbox_center_y = self.owner.center_y + offset_y
        hitbox_bottom = hitbox_center_y - hitbox_height // 2
        hitbox_top = hitbox_center_y + hitbox_height // 2

        if hasattr(opponent, '_custom_hitbox') and opponent._custom_hitbox:
            opp_width, opp_height = opponent._custom_hitbox
            opponent_left = opponent.center_x - opp_width // 2
            opponent_right = opponent.center_x + opp_width // 2
            opponent_bottom = opponent.center_y - opp_height // 2
            opponent_top = opponent.center_y + opp_height // 2
        else:
            opponent_left = opponent.center_x - opponent.width // 2
            opponent_right = opponent.center_x + opponent.width // 2
            opponent_bottom = opponent.center_y - opponent.height // 2
            opponent_top = opponent.center_y + opponent.height // 2

        if (hitbox_right > opponent_left and hitbox_left < opponent_right and
                hitbox_top > opponent_bottom and hitbox_bottom < opponent_top):
            self.has_hit_in_this_attack = True

            damage = attack_data.get("damage", 15)
            knockback = attack_data.get("knockback", 10)
            knockback_dir = 1 if self.owner.facing_right else -1

            opponent.take_damage(damage, knockback * knockback_dir)
            self.owner.attack_hit = True

            if hasattr(self.owner, 'stats') and self.owner.stats is not None:
                self.owner.stats.add_hit()

            print(f"Стенд ПОПАЛ! Урон: {damage}")
            return True

        return False

    def update_animation(self):
        self.frame_counter += 1
        anim_speed = self.animation_speeds.get(self.current_action, 5)

        if self.frame_counter >= anim_speed:
            self.frame_counter = 0
            start_frame, end_frame = self.frame_ranges[self.current_action]

            if self.current_action == "jump" and self.jump_loop:
                loop_start, loop_end = self.jump_loop

                if self.current_frame < loop_start:
                    self.current_frame += 1
                elif self.owner.center_y > GROUND_LEVEL + 5:
                    if self.current_frame >= loop_end:
                        self.current_frame = loop_start
                    else:
                        self.current_frame += 1
                elif self.owner.center_y <= GROUND_LEVEL:
                    if self.current_frame < end_frame:
                        self.current_frame += 1
                    else:
                        self.set_action("idle")
            else:
                self.current_frame += 1
                if self.current_frame > end_frame:
                    if self.is_summoning and self.current_action == "summon":
                        self.is_summoning = False
                        self.set_action("idle")
                    elif "attack" in self.current_action:
                        self.is_attacking = False
                        self.set_action("idle")
                    else:
                        self.current_frame = start_frame

            texture = self.get_current_texture(self.current_frame)
            if texture:
                self.texture = texture

    def update(self):
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.is_attacking = False

        # Позиция стенда относительно персонажа
        dir_mult = 1 if self.owner.facing_right else -1
        self.center_x = self.owner.center_x - (self.stand_data["offset_x"] * dir_mult)
        self.center_y = self.owner.center_y + self.stand_data["offset_y"]
        self.current_direction = self.owner.current_direction

        if self.is_attacking and self.owner.opponent:
            self.check_attack_hit(self.owner.opponent)

        if self.owner.is_blocking and self.owner.is_crouching:
            if self.current_action != "block" and "block" in self.frame_ranges:
                self.set_action("block")
        elif not self.is_summoning and not self.is_attacking:
            owner_action = self.owner.current_action

            if owner_action in ["idle", "move_left", "move_right", "jump", "crouch", "dash_forward", "dash_backward"]:
                if owner_action == "move_left":
                    # При движении влево, стенд всегда двигается влево
                    stand_action = "move_backward"
                elif owner_action == "move_right":
                    # При движении вправо, стенд всегда двигается вправо
                    stand_action = "move_forward"
                elif owner_action == "jump":
                    stand_action = "jump"
                elif owner_action in ["dash_forward", "dash_backward"]:
                    stand_action = owner_action
                else:
                    stand_action = "idle"
                self.set_action(stand_action)

        self.update_animation()


class Character(arcade.Sprite):
    def __init__(self, character_name, start_pos_x, start_pos_y, player_number=1, opponent=None):

        if not character_exists(character_name):
            raise ValueError(f"Персонаж {character_name} не найден!")

        self.character_data = get_character_data(character_name)
        self.character_name = character_name
        self.file_prefix = self.character_data["file_prefix"]
        self.player_number = player_number
        self.opponent = opponent
        self.combo_cooldown = 0

        # Статистика для этого персонажа
        self.stats = None

        self.hitbox_size = self.character_data.get("hitbox_size", (60, 120))
        self.sprite_scale = self.character_data.get("sprite_scale", 0.5)

        # Используем animations словарь
        self.animations = self.character_data["animations"]
        self.frame_ranges = {}
        self.animation_speeds = {}
        for anim_name, (frames, speed) in self.animations.items():
            self.frame_ranges[anim_name] = frames
            self.animation_speeds[anim_name] = speed

        self._load_textures_only()

        first_texture = None
        if 0 in self.all_textures[0] and self.all_textures[0][0]:
            first_texture = self.all_textures[0][0]

        super().__init__(first_texture, scale=self.sprite_scale)

        self._custom_hitbox = self.hitbox_size

        self.max_health = self.character_data.get("health", 100)
        self.current_health = self.max_health

        self.movement_speed = self.character_data.get("movement_speed", 3)
        self.jump_speed = self.character_data.get("jump_speed", 15)
        self.base_animation_speed = self.character_data.get("animation_speed", 5)
        self.crouch_freeze_frame = self.character_data.get("crouch_freeze_frame", None)

        self.jump_loop = self.character_data.get("jump_loop", None)

        self.attacks_data = self.character_data.get("attacks", {})

        # Индивидуальные кулдауны для каждой атаки (в кадрах)
        self.attack1_cooldown_max = 15  # Очень маленький кулдаун
        self.attack2_cooldown_max = 30  # Средний кулдаун
        self.attack3_cooldown_max = 45  # Большой кулдаун

        self.attack1_cooldown = 0
        self.attack2_cooldown = 0
        self.attack3_cooldown = 0

        # Флаги для атак
        self.is_attacking = False
        self.current_attack = None  # Какая атака сейчас выполняется: "attack1", "attack2", "attack3" или "stand_attack1/2/3"
        self.attack_hit = False
        self.has_hit_in_this_attack = False

        self.hit_cooldown = 0
        self.is_hit = False
        self.knockback_velocity = 0
        self.knockback_timer = 0

        # Переменные для анимации получения урона
        self.is_hit_animating = False
        self.hit_timer = 0

        self.dash_speed = self.character_data.get("dash_speed", 8)
        self.dash_distance = self.character_data.get("dash_distance", 100)
        self.dash_cooldown_max = self.character_data.get("dash_cooldown", 45)
        self.dash_cooldown = 0
        self.is_dashing = False
        self.dash_direction = 0
        self.dash_target_x = None
        self.dash_start_x = None

        self.stand = None
        self.stand_active = False
        self.is_summoning = False
        self.double_jump_used = False
        self.stand_sprite_list = arcade.SpriteList()

        self.is_blocking = False
        self.block_timer = 0

        self.stand_meter = 0
        self.stand_meter_max = STAND_METER_MAX

        self.center_x = start_pos_x
        self.center_y = start_pos_y
        self.facing_right = True if player_number == 1 else False
        self.current_direction = 0

        self.current_frame = 0
        self.frame_counter = 0
        self.current_action = "idle"
        self.current_animation_speed = self.get_action_animation_speed("idle")
        self.is_jumping = False
        self.is_crouching = False
        self.crouch_freeze_frame_active = None
        self.crouch_resume_frame = None

        self.intro_frames = self.character_data.get("intro_frames", (0, 37))
        self.victory_frames = self.character_data.get("victory_frames", (0, 37))
        self.defeat_frames = self.character_data.get("defeat_frames", (0, 37))

        self.change_x = 0
        self.change_y = 0

        if first_texture:
            self.texture = first_texture

        print(f"ИГРОК {player_number}: {character_name} создан")
        print(f"  Здоровье: {self.current_health}/{self.max_health}")
        print(f"  Позиция: ({self.center_x}, {self.center_y})")
        print(f"  Хитбокс: {self.hitbox_size[0]}x{self.hitbox_size[1]}")

    @property
    def hit_box(self):
        if hasattr(self, '_custom_hitbox') and self._custom_hitbox:
            width, height = self._custom_hitbox
            return [
                (-width / 2, -height / 2),
                (width / 2, -height / 2),
                (width / 2, height / 2),
                (-width / 2, height / 2)
            ]
        return super().hit_box

    @hit_box.setter
    def hit_box(self, value):
        pass

    def _load_textures_only(self):
        character_path = Path("Спрайты") / self.character_name
        max_frame = 0
        for start, end in self.frame_ranges.values():
            max_frame = max(max_frame, end)

        self.all_textures = [{}, {}]
        for i in range(max_frame + 1):
            filename = f"{self.file_prefix}_0-{i}.png"
            file_path = character_path / filename

            if file_path.exists():
                try:
                    texture_normal = arcade.load_texture(str(file_path))
                    self.all_textures[0][i] = texture_normal
                    self.all_textures[1][i] = texture_normal.flip_left_right()
                except Exception as e:
                    print(f"Ошибка загрузки спрайта {filename}: {e}")
                    self.all_textures[0][i] = None
                    self.all_textures[1][i] = None
            else:
                self.all_textures[0][i] = None
                self.all_textures[1][i] = None

    def load_all_textures(self):
        self._load_textures_only()

    def get_character_bounds(self):
        left = self.center_x - self.width // 2
        right = self.center_x + self.width // 2
        bottom = self.center_y - self.height // 2
        top = self.center_y + self.height // 2
        return left, right, bottom, top

    def get_action_animation_speed(self, action):
        if action in self.animation_speeds:
            return self.animation_speeds[action]
        return self.base_animation_speed

    def set_opponent(self, opponent):
        self.opponent = opponent

    def update_facing_direction(self):
        if self.opponent and not self.is_attacking and not self.is_dashing and not self.is_blocking:
            if self.opponent.center_x > self.center_x:
                self.facing_right = True
                self.current_direction = 0
            else:
                self.facing_right = False
                self.current_direction = 1

    def get_current_texture(self, frame_number):
        if frame_number in self.all_textures[self.current_direction] and self.all_textures[self.current_direction][
            frame_number]:
            texture = self.all_textures[self.current_direction][frame_number]
            try:
                self.texture = texture
            except AttributeError:
                self._texture = texture
            return texture

        other_direction = 1 - self.current_direction
        if frame_number in self.all_textures[other_direction] and self.all_textures[other_direction][frame_number]:
            texture = self.all_textures[other_direction][frame_number]
            try:
                self.texture = texture
            except AttributeError:
                self._texture = texture
            return texture

        return None

    def get_action_for_movement(self, moving_left, moving_right):
        """
        Определяет анимацию движения в зависимости от направления движения и направления взгляда
        moving_left: True если игрок нажал кнопку движения влево
        moving_right: True если игрок нажал кнопку движения вправо
        """
        if moving_left and moving_right:
            return None

        if moving_left:
            return "move_right"
        elif moving_right:
            return "move_left"
        return None

    def jump(self):
        if self.is_summoning or self.is_attacking or self.is_blocking:
            return False

        if not self.is_jumping and not self.is_crouching and not self.is_dashing and self.center_y <= GROUND_LEVEL:
            self.change_y = self.jump_speed
            self.is_jumping = True
            self.double_jump_used = False
            self.set_action("jump")

            if hasattr(self, 'stats') and self.stats is not None:
                self.stats.add_jump()

            return True

        elif self.stand_active and self.is_jumping and not self.double_jump_used and not self.is_dashing:
            self.change_y = self.jump_speed
            self.double_jump_used = True
            if "jump" in self.frame_ranges:
                self.current_frame = self.frame_ranges["jump"][0]

            if hasattr(self, 'stats') and self.stats is not None:
                self.stats.add_jump()

            return True

        return False

    def crouch(self, start_crouch=True):
        if "crouch" not in self.frame_ranges or self.is_dashing or self.is_summoning or self.is_attacking:
            return

        start_frame, end_frame = self.frame_ranges["crouch"]

        if start_crouch:
            if not self.is_jumping and not self.is_crouching and not self.is_dashing:
                self.is_crouching = True
                self.is_blocking = True
                self.block_timer = BLOCK_DURATION
                self.set_action("crouch")

                if self.crouch_freeze_frame and start_frame <= self.crouch_freeze_frame <= end_frame:
                    self.crouch_freeze_frame_active = self.crouch_freeze_frame
                else:
                    self.crouch_freeze_frame_active = (start_frame + end_frame) // 2
        else:
            if self.is_crouching:
                self.crouch_resume_frame = self.current_frame
                self.is_crouching = False
                self.crouch_freeze_frame_active = None
                self.is_blocking = False

    def dash(self, move_direction=None):
        if self.is_dashing or self.is_jumping or self.is_crouching or self.dash_cooldown > 0 or self.is_summoning or self.is_attacking or self.is_blocking:
            return False

        if move_direction is not None:
            self.dash_direction = move_direction
        else:
            if self.facing_right:
                self.dash_direction = 1
            else:
                self.dash_direction = -1

        if self.facing_right:
            dash_action = "dash_forward" if self.dash_direction > 0 else "dash_backward"
        else:
            dash_action = "dash_forward" if self.dash_direction < 0 else "dash_backward"

        if dash_action not in self.frame_ranges:
            return False

        self.dash_start_x = self.center_x
        self.dash_target_x = self.center_x + (self.dash_distance * self.dash_direction)

        if self.dash_target_x < 0:
            self.dash_target_x = 0
        elif self.dash_target_x > SCREEN_WIDTH:
            self.dash_target_x = SCREEN_WIDTH

        self.is_dashing = True
        self.set_action(dash_action)
        self.dash_cooldown = self.dash_cooldown_max

        if hasattr(self, 'stats') and self.stats is not None:
            self.stats.add_dash()

        return True

    def toggle_stand(self):
        if self.is_jumping or self.is_dashing or self.is_blocking:
            return

        if self.is_attacking and "stand_attack" not in self.current_action:
            return

        if self.stand_active:
            self.stand_active = False
            self.stand = None
            self.stand_sprite_list.clear()
            print(f"Игрок {self.player_number} убрал стенд")
            return True
        else:
            if self.stand_meter >= STAND_METER_SUMMON_COST:
                self.stand_meter -= STAND_METER_SUMMON_COST
                self.stand_active = True
                self.is_summoning = True
                self.set_action("stand_summon")
                self.stand = Stand(self)
                self.stand_sprite_list.append(self.stand)

                if hasattr(self, 'stats') and self.stats is not None:
                    self.stats.add_stand_summon()

                print(
                    f"Игрок {self.player_number} призывает стенд, потрачено {STAND_METER_SUMMON_COST} шкалы, осталось {self.stand_meter:.1f}")
                return True
            else:
                print(f"Недостаточно шкалы стенда: {self.stand_meter:.1f}/100, нужно {STAND_METER_SUMMON_COST}")
                return False

    def attack1(self):
        """Первая атака (J) - если стенд активен, атакует стенд и проигрывает стойку"""
        if self.attack1_cooldown > 0 or self.is_summoning or self.is_dashing or self.is_jumping or self.is_blocking:
            return False

        if self.stand_active:
            # Если стенд активен - атакует стенд, персонаж проигрывает стойку
            if self.stand and not self.stand.is_attacking:
                # Запускаем атаку стенда
                self.stand.start_attack(1)
                # Персонаж проигрывает стойку
                self.start_attack("stand_attack1")
                print(f"Игрок {self.player_number} активирует атаку стенда 1 со стойкой")
                return True
        else:
            # Если стенд не активен - атакует персонаж
            if "attack1" not in self.frame_ranges:
                print("Атака 1 не найдена")
                return False

            self.start_attack("attack1")
            return True

        return False

    def attack2(self):
        """Вторая атака (I) - если стенд активен, атакует стенд и проигрывает стойку"""
        if self.attack2_cooldown > 0 or self.is_summoning or self.is_dashing or self.is_jumping or self.is_blocking:
            return False

        if self.stand_active:
            # Если стенд активен - атакует стенд, персонаж проигрывает стойку
            if self.stand and not self.stand.is_attacking:
                # Запускаем атаку стенда
                self.stand.start_attack(2)
                # Персонаж проигрывает стойку
                self.start_attack("stand_attack2")
                print(f"Игрок {self.player_number} активирует атаку стенда 2 со стойкой")
                return True
        else:
            # Если стенд не активен - атакует персонаж
            if "attack2" not in self.frame_ranges:
                print("Атака 2 не найдена")
                return False

            self.start_attack("attack2")
            return True

        return False

    def attack3(self):
        """Третья атака (L) - если стенд активен, атакует стенд и проигрывает стойку"""
        if self.attack3_cooldown > 0 or self.is_summoning or self.is_dashing or self.is_jumping or self.is_blocking:
            return False

        if self.stand_active:
            # Если стенд активен - атакует стенд, персонаж проигрывает стойку
            if self.stand and not self.stand.is_attacking:
                # Запускаем атаку стенда
                self.stand.start_attack(3)
                # Персонаж проигрывает стойку
                self.start_attack("stand_attack3")
                print(f"Игрок {self.player_number} активирует атаку стенда 3 со стойкой")
                return True
        else:
            # Если стенд не активен - атакует персонаж
            if "attack3" not in self.frame_ranges:
                print("Атака 3 не найдена")
                return False

            self.start_attack("attack3")
            return True

        return False

    def start_attack(self, attack_name):
        """Общий метод для запуска атаки персонажа"""
        self.current_attack = attack_name
        self.is_attacking = True
        self.attack_hit = False
        self.has_hit_in_this_attack = False
        self.change_x = 0

        # Устанавливаем соответствующий кулдаун
        if attack_name == "attack1" or attack_name == "stand_attack1":
            self.attack1_cooldown = self.attack1_cooldown_max
        elif attack_name == "attack2" or attack_name == "stand_attack2":
            self.attack2_cooldown = self.attack2_cooldown_max
        elif attack_name == "attack3" or attack_name == "stand_attack3":
            self.attack3_cooldown = self.attack3_cooldown_max

        self.set_action(attack_name)

        # Пополнение шкалы стенда за атаку (только если это атака персонажа, не стойка)
        if "stand_" not in attack_name:
            self.stand_meter = min(self.stand_meter_max, self.stand_meter + STAND_METER_GAIN_ON_ATTACK)

        print(f"Игрок {self.player_number} выполняет атаку {attack_name}")
        return True

    def check_attack_hit(self):
        """Проверка попадания текущей атаки"""
        if not self.is_attacking or self.has_hit_in_this_attack or not self.opponent:
            return False

        if "stand_" in self.current_action:
            return False

        attack_data = get_attack_data(self.character_name, self.current_action)
        if not attack_data:
            return False

        active_frames = attack_data.get("active_frames", (0, 0))
        if self.current_frame < active_frames[0] or self.current_frame > active_frames[1]:
            return False

        if self.opponent.hit_cooldown > 0:
            return False

        hitbox_width, hitbox_height = attack_data.get("hitbox", (50, 50))
        offset_x = attack_data.get("offset_x", 50)
        offset_y = attack_data.get("offset_y", 0)

        if self.facing_right:
            hitbox_left = self.center_x + offset_x - hitbox_width // 2
        else:
            hitbox_left = self.center_x - offset_x - hitbox_width // 2

        hitbox_right = hitbox_left + hitbox_width
        hitbox_center_y = self.center_y + offset_y
        hitbox_bottom = hitbox_center_y - hitbox_height // 2
        hitbox_top = hitbox_center_y + hitbox_height // 2

        if hasattr(self.opponent, '_custom_hitbox') and self.opponent._custom_hitbox:
            opp_width, opp_height = self.opponent._custom_hitbox
            opponent_left = self.opponent.center_x - opp_width // 2
            opponent_right = self.opponent.center_x + opp_width // 2
            opponent_bottom = self.opponent.center_y - opp_height // 2
            opponent_top = self.opponent.center_y + opp_height // 2
        else:
            opponent_left = self.opponent.center_x - self.opponent.width // 2
            opponent_right = self.opponent.center_x + self.opponent.width // 2
            opponent_bottom = self.opponent.center_y - self.opponent.height // 2
            opponent_top = self.opponent.center_y + self.opponent.height // 2

        if (hitbox_right > opponent_left and hitbox_left < opponent_right and
                hitbox_top > opponent_bottom and hitbox_bottom < opponent_top):
            self.attack_hit = True
            self.has_hit_in_this_attack = True

            damage = attack_data.get("damage", 10)
            knockback = attack_data.get("knockback", 5)
            knockback_dir = 1 if self.facing_right else -1

            self.opponent.take_damage(damage, knockback * knockback_dir)

            self.stand_meter = min(self.stand_meter_max, self.stand_meter + STAND_METER_GAIN_ON_ATTACK)

            if hasattr(self, 'stats') and self.stats is not None:
                self.stats.add_hit()

            return True

        return False

    def start_hit_animation(self):
        """Запуск анимации получения урона"""
        if "hit" in self.animations:
            self.is_hit_animating = True
            self.hit_timer = 15  # Длительность анимации
            self.set_action("hit")

    def take_damage(self, damage, knockback_force):
        if self.hit_cooldown > 0:
            return

        # Тратим шкалу стенда при получении урона
        if self.stand_active:
            drain_amount = self.character_data.get("stand_damage_drain", STAND_DAMAGE_DRAIN)
            self.stand_meter = max(0, self.stand_meter - drain_amount)

            # Если шкала закончилась - отключаем стенд
            if self.stand_meter <= 0:
                self.stand_meter = 0
                self.stand_active = False
                self.stand = None
                self.stand_sprite_list.clear()
                print(f"Стенд игрока {self.player_number} отключен из-за истощения шкалы")
        else:
            drain_amount = self.character_data.get("stand_damage_drain_no_stand", STAND_DAMAGE_DRAIN_NO_STAND)
            self.stand_meter = max(0, self.stand_meter - drain_amount)

        if not self.is_blocking:
            self.stand_meter = min(self.stand_meter_max, self.stand_meter + STAND_METER_GAIN_ON_HIT)

        # Запускаем анимацию получения урона
        self.start_hit_animation()

        if self.is_blocking:
            if self.stand_active:
                if self.stand_meter >= STAND_METER_BLOCK_DRAIN:
                    self.stand_meter -= STAND_METER_BLOCK_DRAIN
                    self.stand_meter = min(self.stand_meter_max, self.stand_meter + STAND_METER_GAIN_ON_BLOCK)

                    if hasattr(self, 'stats') and self.stats is not None:
                        self.stats.add_block()

                    if self.stand_meter <= 0:
                        self.stand_meter = 0
                        self.stand_active = False
                        self.stand = None
                        self.stand_sprite_list.clear()

                    knockback_dir = 1 if self.facing_right else -1
                    self.center_x += knockback_force * 0.3 * knockback_dir

                    return
                else:
                    self.is_blocking = False
            else:
                if self.stand_meter >= STAND_METER_BLOCK_DRAIN_NO_STAND:
                    self.stand_meter -= STAND_METER_BLOCK_DRAIN_NO_STAND

                    if hasattr(self, 'stats') and self.stats is not None:
                        self.stats.add_block()

                    reduced_damage = int(damage * 0.5)
                    reduced_knockback = int(knockback_force * 0.5)

                    self.current_health -= reduced_damage
                    if self.current_health < 0:
                        self.current_health = 0

                    self.stand_meter = min(self.stand_meter_max, self.stand_meter + STAND_METER_GAIN_ON_BLOCK)

                    self.hit_cooldown = HIT_COOLDOWN // 2
                    self.is_hit = True
                    self.knockback_velocity = reduced_knockback * (1 if self.facing_right else -1)
                    self.knockback_timer = KNOCKBACK_DURATION // 2

                    self.is_attacking = False
                    self.is_dashing = False

                    return
                else:
                    self.is_blocking = False

        self.current_health -= damage
        if self.current_health < 0:
            self.current_health = 0

        self.hit_cooldown = HIT_COOLDOWN
        self.is_hit = True
        self.knockback_velocity = knockback_force
        self.knockback_timer = KNOCKBACK_DURATION

        self.is_attacking = False
        self.is_dashing = False
        self.change_x = 0

    def draw_stand(self):
        if self.stand_active and self.stand:
            self.stand_sprite_list.draw()

    def draw_health_bar(self):
        if self.player_number == 1:
            x = SCREEN_WIDTH // 4
        else:
            x = 3 * SCREEN_WIDTH // 4

        y = SCREEN_HEIGHT - 50
        width = 300
        height = 30

        left = x - width // 2
        bottom = y - height // 2
        arcade.draw_lbwh_rectangle_filled(left, bottom, width, height, arcade.color.DARK_RED)

        if self.current_health > 0:
            health_width = (self.current_health / self.max_health) * (width - 4)
            left = x - width // 2 + 2
            bottom = y - height // 2 + 2
            arcade.draw_lbwh_rectangle_filled(left, bottom, health_width, height - 4, arcade.color.GREEN)

        arcade.draw_text(f"{int(self.current_health)}/{self.max_health}",
                         x, y - height - 5,
                         arcade.color.WHITE, 14, anchor_x="center")

        arcade.draw_text(f"{self.character_data['display_name']}",
                         x, y + height // 2 + 5,
                         arcade.color.WHITE, 16, anchor_x="center", bold=True)

    def draw_stand_meter(self):
        if self.player_number == 1:
            x = SCREEN_WIDTH // 4
        else:
            x = 3 * SCREEN_WIDTH // 4

        y = SCREEN_HEIGHT - 100
        width = 300
        height = 15

        left = x - width // 2
        bottom = y - height // 2
        arcade.draw_lbwh_rectangle_filled(left, bottom, width, height, arcade.color.DARK_GRAY)

        if self.stand_meter > 0:
            meter_width = (self.stand_meter / self.stand_meter_max) * (width - 4)
            left = x - width // 2 + 2
            bottom = y - height // 2 + 2

            if self.stand_active:
                color = arcade.color.GOLD
            else:
                color = arcade.color.LIGHT_BLUE

            arcade.draw_lbwh_rectangle_filled(left, bottom, meter_width, height - 4, color)

            if not self.stand_active:
                summon_cost_x = x - width // 2 + (STAND_METER_SUMMON_COST / STAND_METER_MAX) * width
                arcade.draw_line(summon_cost_x, y - height, summon_cost_x, y + height,
                                 arcade.color.WHITE, 2)

        stand_text = "STAND" if self.stand_active else "STAND METER"
        arcade.draw_text(stand_text, x, y - height - 10,
                         arcade.color.WHITE, 12, anchor_x="center")

        percent = int(self.stand_meter)
        arcade.draw_text(f"{percent}%", x, y,
                         arcade.color.WHITE, 10, anchor_x="center", anchor_y="center")

    def can_move(self):
        if self.is_attacking:
            return False
        if self.is_hit:
            return False
        if self.is_summoning:
            return False
        if self.is_dashing:
            return False
        if self.is_blocking:
            return False
        return True

    def set_action(self, new_action):
        if new_action == self.current_action:
            return

        print(f"Character {self.player_number} set_action: {self.current_action} -> {new_action}")

        if new_action in ["intro", "victory", "defeat"]:
            pass
        elif self.is_summoning and new_action not in ["stand_summon", "idle"]:
            if new_action != "stand_summon":
                return
        elif self.is_jumping and new_action not in ["jump", "idle"]:
            return
        elif self.is_dashing and new_action not in ["dash_forward", "dash_backward", "idle"]:
            return

        if new_action in self.frame_ranges:
            self.current_action = new_action
            self.current_frame = self.frame_ranges[new_action][0]
            self.frame_counter = 0
            self.current_animation_speed = self.get_action_animation_speed(new_action)

            texture = self.get_current_texture(self.current_frame)
            if texture:
                self.texture = texture

            if "attack" in new_action:
                self.change_x = 0

    def update_animation(self):
        self.frame_counter += 1
        start_frame, end_frame = self.frame_ranges[self.current_action]

        if self.frame_counter >= self.current_animation_speed:
            self.frame_counter = 0

            if self.current_action == "jump":
                if self.jump_loop:
                    loop_start, loop_end = self.jump_loop

                    if self.current_frame < loop_start:
                        self.current_frame += 1
                    elif self.center_y > GROUND_LEVEL + 5:
                        if self.current_frame >= loop_end:
                            self.current_frame = loop_start
                        else:
                            self.current_frame += 1
                    elif self.center_y <= GROUND_LEVEL:
                        if self.current_frame < end_frame:
                            self.current_frame += 1
                        else:
                            self.current_frame = end_frame
                            self.is_jumping = False
                            self.set_action("idle")
                else:
                    self.current_frame += 1
                    if self.current_frame > end_frame:
                        self.current_frame = end_frame
                        self.is_jumping = False
                        self.set_action("idle")

            elif self.current_action in ["intro", "victory", "defeat"]:
                self.current_frame += 1
                if self.current_frame > end_frame:
                    if self.current_action == "intro":
                        self.current_frame = start_frame
                    else:
                        self.current_frame = end_frame

            elif self.current_action == "stand_summon":
                self.current_frame += 1
                if self.current_frame > end_frame:
                    self.current_frame = end_frame
                    self.is_summoning = False
                    self.set_action("idle")

            elif self.current_action == "crouch":
                if self.is_crouching:
                    self.block_timer = BLOCK_DURATION

                    if self.crouch_freeze_frame_active is not None:
                        if self.current_frame < self.crouch_freeze_frame_active:
                            self.current_frame += 1
                            if self.current_frame > self.crouch_freeze_frame_active:
                                self.current_frame = self.crouch_freeze_frame_active
                    else:
                        self.current_frame += 1
                        if self.current_frame > end_frame:
                            self.current_frame = end_frame
                else:
                    if self.crouch_resume_frame is not None:
                        self.current_frame = self.crouch_resume_frame
                        self.crouch_resume_frame = None

                    self.current_frame += 1
                    if self.current_frame > end_frame:
                        self.current_frame = end_frame
                        self.set_action("idle")

            elif self.current_action in ["dash_forward", "dash_backward"]:
                self.current_frame += 1
                if self.current_frame >= end_frame:
                    if self.is_dashing:
                        self.is_dashing = False
                        self.dash_target_x = None
                        self.dash_start_x = None
                        self.dash_direction = 0
                    self.set_action("idle")

            elif "attack" in self.current_action and "stand" not in self.current_action:
                self.current_frame += 1
                if self.current_frame > end_frame:
                    self.is_attacking = False
                    self.set_action("idle")

            elif self.current_action == "hit":
                self.current_frame += 1
                if self.current_frame > end_frame:
                    if self.is_hit_animating:
                        self.is_hit_animating = False
                    if not self.is_attacking and not self.is_dashing and not self.is_jumping:
                        self.set_action("idle")

            else:
                self.current_frame += 1
                if self.current_frame > end_frame:
                    self.current_frame = start_frame

            texture = self.get_current_texture(self.current_frame)
            if texture:
                self.texture = texture

    def update(self):
        # Обновление кулдаунов атак
        if self.attack1_cooldown > 0:
            self.attack1_cooldown -= 1
        if self.attack2_cooldown > 0:
            self.attack2_cooldown -= 1
        if self.attack3_cooldown > 0:
            self.attack3_cooldown -= 1

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1
        else:
            self.is_hit = False

        # Обновление таймера анимации получения урона
        if self.hit_timer > 0:
            self.hit_timer -= 1
            if self.hit_timer <= 0:
                self.is_hit_animating = False

        if self.is_blocking:
            self.block_timer -= 1
            if self.block_timer <= 0:
                self.is_blocking = False

        if not self.stand_active:
            self.stand_meter = min(self.stand_meter_max, self.stand_meter + STAND_METER_PASSIVE_GAIN)

        if self.knockback_timer > 0:
            self.knockback_timer -= 1
            self.center_x += self.knockback_velocity
            self.knockback_velocity *= 0.8

        # Проверка попадания атаки персонажа
        if self.is_attacking and not self.stand_active and "attack" in self.current_action and "stand" not in self.current_action:
            self.check_attack_hit()

        # Проверка окончания атаки стенда
        if self.stand_active and self.stand:
            if not self.stand.is_attacking and self.is_attacking:
                if "stand_attack" in self.current_attack:
                    # Если атака стенда закончилась, персонаж возвращается в idle
                    self.is_attacking = False
                    self.current_attack = None
                    if not self.is_jumping and not self.is_dashing:
                        self.set_action("idle")

        if not self.is_attacking and not self.is_blocking and not self.is_hit_animating:
            self.update_facing_direction()

        if self.can_move() and not self.is_hit_animating:
            self.center_x += self.change_x
        else:
            self.change_x = 0

        if self.is_dashing and self.dash_target_x is not None:
            distance = self.dash_target_x - self.center_x
            if abs(distance) > self.dash_speed:
                self.center_x += self.dash_speed if distance > 0 else -self.dash_speed
            else:
                self.center_x = self.dash_target_x
                if not self.is_dashing:
                    self.dash_target_x = None
                    self.dash_start_x = None
                    self.dash_direction = 0
        else:
            if not self.is_crouching and not self.is_dashing and not self.is_hit:
                self.change_y -= GRAVITY

        self.center_y += self.change_y

        if self.center_y <= GROUND_LEVEL:
            self.center_y = GROUND_LEVEL
            self.change_y = 0
            self.double_jump_used = False

            if self.current_action == "jump" and not self.jump_loop:
                self.is_jumping = False
                self.set_action("idle")
            elif self.current_action != "jump":
                self.is_jumping = False

        if self.left < 0:
            self.left = 0
            if self.is_dashing:
                self.is_dashing = False
                self.dash_target_x = None
                self.set_action("idle")
        if self.right > SCREEN_WIDTH:
            self.right = SCREEN_WIDTH
            if self.is_dashing:
                self.is_dashing = False
                self.dash_target_x = None
                self.set_action("idle")
        if self.top > SCREEN_HEIGHT:
            self.top = SCREEN_HEIGHT
            self.change_y = 0

        self.update_animation()


class ModeMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        print("ModeMenuView инициализирован")
        self.bg_sprite_list = arcade.SpriteList()
        self.ui_sprite_list = arcade.SpriteList()
        self.side_rams_list = arcade.SpriteList()

        bg_path = Path("Лого") / "fon_menu.png"
        orig_w, orig_h = 128, 64
        self.bg_scale = SCREEN_WIDTH / (5 * orig_w)
        self.tile_w, self.tile_h = orig_w * self.bg_scale, orig_h * self.bg_scale
        if bg_path.exists():
            for r in range(8):
                for c in range(5):
                    s = arcade.Sprite(str(bg_path), scale=self.bg_scale)
                    s.center_x = c * self.tile_w + (self.tile_w / 2)
                    s.center_y = r * self.tile_h + (self.tile_h / 2)
                    self.bg_sprite_list.append(s)

        self.ramka = None
        ramka_path = Path("Лого") / "ramka.png"
        if ramka_path.exists():
            self.ramka = arcade.Sprite(str(ramka_path), scale=2.0)
            self.ramka.center_x = SCREEN_WIDTH // 2
            self.ramka.center_y = SCREEN_HEIGHT - 100
            self.ui_sprite_list.append(self.ramka)

        self.header_text = arcade.Text("Выбери режим", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                                       arcade.color.BLACK, 24, anchor_x="center", anchor_y="center", bold=True)

        self.darby_textures = []
        for i in range(14):
            p = Path("Лого") / f"DArby_{i}.png"
            if p.exists():
                self.darby_textures.append(arcade.load_texture(str(p)))

        self.darby_sprite = arcade.Sprite(scale=4.0)
        self.darby_sprite.center_x = SCREEN_WIDTH // 2
        self.darby_sprite.bottom = 10
        if self.darby_textures:
            self.darby_sprite.texture = self.darby_textures[0]
        self.ui_sprite_list.append(self.darby_sprite)

        self.ram_textures = []
        for i in range(5):
            p = Path("Лого") / f"ram_{i}.png"
            if p.exists():
                self.ram_textures.append(arcade.load_texture(str(p)))

        side_gap = 300
        bottom_gap = 80

        self.left_ram = arcade.Sprite(scale=4.0)
        self.left_ram.center_x = side_gap
        self.left_ram.bottom = bottom_gap

        self.right_ram = arcade.Sprite(scale=4.0)
        self.right_ram.center_x = SCREEN_WIDTH - side_gap
        self.right_ram.bottom = bottom_gap

        self.side_rams_list.append(self.left_ram)
        self.side_rams_list.append(self.right_ram)

        self.anim_state = "intro"
        self.selected_index = 0
        self.current_frame = 0
        self.ram_anim_frame = 0
        self.timer = 0.0
        self.ram_timer = 0.0

        self.modes = ["ТЕСТОВЫЙ РЕЖИМ", "БОЙ 1 НА 1", "ТАБЛИЦА ЛИДЕРОВ"]

    def on_update(self, delta_time):
        for s in self.bg_sprite_list:
            s.center_y -= 3.0
            if s.top < 0:
                s.center_y += 8 * self.tile_h

        if self.anim_state in ["intro", "outro"]:
            self.timer += delta_time
            if self.timer >= 0.1:
                self.timer = 0.0
                self.current_frame += 1
                if self.anim_state == "intro" and self.current_frame >= 4:
                    self.current_frame = 4
                    self.anim_state = "idle"
                elif self.anim_state == "outro" and self.current_frame >= 13:
                    self.current_frame = 13
                    if self.selected_index == 0:
                        self.window.show_view(TestCharacterSelectView())
                    elif self.selected_index == 1:
                        self.window.show_view(PlayerNameInputView(is_p1=True))
                    else:
                        self.window.show_view(LeaderboardView())

                if self.current_frame < len(self.darby_textures):
                    self.darby_sprite.texture = self.darby_textures[self.current_frame]

        self.ram_timer += delta_time
        if self.ram_timer >= 0.05:
            self.ram_timer = 0.0
            self.ram_anim_frame = (self.ram_anim_frame + 1) % 5

        if self.ram_textures:
            if self.selected_index == 0:
                self.left_ram.texture = self.ram_textures[self.ram_anim_frame]
                self.right_ram.texture = self.ram_textures[0]
            elif self.selected_index == 1:
                self.right_ram.texture = self.ram_textures[self.ram_anim_frame]
                self.left_ram.texture = self.ram_textures[0]
            else:
                # Для третьего пункта подсвечиваем центр
                self.left_ram.texture = self.ram_textures[0]
                self.right_ram.texture = self.ram_textures[0]

    def on_draw(self):
        self.clear()
        self.bg_sprite_list.draw()
        arcade.draw_rect_filled(arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT), (0, 0, 0, 160))

        self.ui_sprite_list.draw()
        self.side_rams_list.draw()
        self.header_text.draw()

        # Отрисовка трех пунктов меню
        colors = [arcade.color.WHITE] * 3
        colors[self.selected_index] = MENU_SELECTED_COLOR

        arcade.draw_text(self.modes[0], self.left_ram.center_x, self.left_ram.center_y,
                         colors[0], 18, anchor_x="center", anchor_y="center", bold=True)
        arcade.draw_text(self.modes[1], self.right_ram.center_x, self.right_ram.center_y,
                         colors[1], 18, anchor_x="center", anchor_y="center", bold=True)
        arcade.draw_text(self.modes[2], SCREEN_WIDTH // 2, 20,
                         colors[2], 18, anchor_x="center", anchor_y="center", bold=True)

    def on_key_press(self, key, modifiers):
        if self.anim_state != "idle":
            return

        if key in [arcade.key.LEFT, arcade.key.A]:
            self.selected_index = (self.selected_index - 1) % 3
        elif key in [arcade.key.RIGHT, arcade.key.D]:
            self.selected_index = (self.selected_index + 1) % 3
        elif key in [arcade.key.UP, arcade.key.W]:
            self.selected_index = (self.selected_index - 1) % 3
        elif key in [arcade.key.DOWN, arcade.key.S]:
            self.selected_index = (self.selected_index + 1) % 3
        elif key == arcade.key.ENTER:
            self.anim_state = "outro"
            self.current_frame = 4


class PlayerNameInputView(arcade.View):
    def __init__(self, is_p1=True, p1_name=""):
        super().__init__()
        self.is_p1 = is_p1
        self.p1_name = p1_name
        self.player_name = ""
        self.cursor_timer = 0
        self.show_cursor = True

        self.bg_sprite_list = arcade.SpriteList()
        bg_path = Path("Лого") / "fon_menu.png"

        orig_w, orig_h = 128, 64
        self.bg_scale = SCREEN_WIDTH / (5 * orig_w)
        self.tile_w, self.tile_h = orig_w * self.bg_scale, orig_h * self.bg_scale
        self.rows = 8

        if bg_path.exists():
            for r in range(self.rows):
                for c in range(5):
                    s = arcade.Sprite(str(bg_path), scale=self.bg_scale)
                    s.center_x = c * self.tile_w + (self.tile_w / 2)
                    s.center_y = r * self.tile_h + (self.tile_h / 2)
                    self.bg_sprite_list.append(s)

    def on_update(self, delta_time):
        for s in self.bg_sprite_list:
            s.center_y -= 3.0
            if s.top < 0:
                s.center_y += self.rows * self.tile_h

        self.cursor_timer += delta_time
        if self.cursor_timer >= 0.5:
            self.cursor_timer = 0
            self.show_cursor = not self.show_cursor

    def on_draw(self):
        self.clear()
        self.bg_sprite_list.draw()
        arcade.draw_rect_filled(
            arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
            (0, 0, 0, 200)
        )

        if self.is_p1:
            title = "ВВЕДИТЕ ИМЯ ИГРОКА 1"
        else:
            title = f"ВВЕДИТЕ ИМЯ ИГРОКА 2"

        arcade.draw_text(title, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150,
                         arcade.color.GOLD, 40, anchor_x="center", bold=True)

        # Поле ввода
        input_box_width = 400
        input_box_height = 60
        input_box_x = SCREEN_WIDTH // 2
        input_box_y = SCREEN_HEIGHT // 2

        arcade.draw_lrbt_rectangle_outline(
            input_box_x - input_box_width // 2,
            input_box_x + input_box_width // 2,
            input_box_y - input_box_height // 2,
            input_box_y + input_box_height // 2,
            arcade.color.WHITE, 3
        )

        display_text = self.player_name
        if self.show_cursor:
            display_text += "|"

        arcade.draw_text(display_text, input_box_x, input_box_y,
                         arcade.color.WHITE, 24, anchor_x="center", anchor_y="center")

        arcade.draw_text("Буквы и цифры", SCREEN_WIDTH // 2, input_box_y - 50,
                         arcade.color.GRAY, 16, anchor_x="center")
        arcade.draw_text("ENTER - продолжить | BACKSPACE - удалить | ESC - назад",
                         SCREEN_WIDTH // 2, input_box_y - 100,
                         arcade.color.GRAY, 16, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(ModeMenuView())
        elif key == arcade.key.ENTER:
            if self.player_name.strip():
                if self.is_p1:
                    # Переходим к вводу имени второго игрока
                    self.window.show_view(PlayerNameInputView(is_p1=False, p1_name=self.player_name))
                else:
                    # Оба имени введены, переходим к выбору персонажей
                    self.window.show_view(OneVsOneCharacterSelectView(self.p1_name, self.player_name))
        elif key == arcade.key.BACKSPACE:
            if self.player_name:
                self.player_name = self.player_name[:-1]
        else:
            # Добавляем символ (буквы и цифры)
            if key == arcade.key.SPACE:
                self.player_name += " "
            elif arcade.key.KEY_0 <= key <= arcade.key.KEY_9:
                self.player_name += str(key - arcade.key.KEY_0)
            elif arcade.key.A <= key <= arcade.key.Z:
                char = chr(key).upper()
                self.player_name += char


class OneVsOneCharacterSelectView(arcade.View):
    def __init__(self, p1_name, p2_name):
        super().__init__()
        print("OneVsOneCharacterSelectView инициализирован")

        self.p1_name = p1_name
        self.p2_name = p2_name

        self.bg_sprite_list = arcade.SpriteList()
        bg_path = Path("Лого") / "fon_menu.png"

        orig_w, orig_h = 128, 64
        self.bg_scale = SCREEN_WIDTH / (5 * orig_w)
        self.tile_w, self.tile_h = orig_w * self.bg_scale, orig_h * self.bg_scale
        self.rows = 8

        if bg_path.exists():
            for r in range(self.rows):
                for c in range(5):
                    s = arcade.Sprite(str(bg_path), scale=self.bg_scale)
                    s.center_x = c * self.tile_w + (self.tile_w / 2)
                    s.center_y = r * self.tile_h + (self.tile_h / 2)
                    self.bg_sprite_list.append(s)

        self.characters = get_available_characters()
        self.p1_selected = 0
        self.p2_selected = 0
        self.current_player = 1

        self.logos = {}
        self.load_logos()

        self.title_text = arcade.Text(
            "ВЫБОР ПЕРСОНАЖЕЙ",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
            arcade.color.WHITE, 36, anchor_x="center"
        )
        self.p1_text = arcade.Text(f"ИГРОК 1: {p1_name}", SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150, arcade.color.CYAN, 24,
                                   anchor_x="center")
        self.p2_text = arcade.Text(f"ИГРОК 2: {p2_name}", 3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150,
                                   arcade.color.ORANGE,
                                   24, anchor_x="center")
        self.instruction_text = arcade.Text("ENTER - выбрать | ПРОБЕЛ - переключить | ESC - назад", SCREEN_WIDTH // 2,
                                            80, arcade.color.GRAY, 16, anchor_x="center")
        self.start_text = arcade.Text("После выбора обоих нажмите S для старта", SCREEN_WIDTH // 2, 50,
                                      arcade.color.GREEN, 18, anchor_x="center")

    def load_logos(self):
        logos_path = Path("Лого")
        for character in self.characters:
            for file_path in logos_path.glob(f"{character}.*"):
                try:
                    self.logos[character] = arcade.load_texture(str(file_path))
                except:
                    pass

    def on_update(self, delta_time):
        for s in self.bg_sprite_list:
            s.center_y -= 3.0
            if s.top < 0:
                s.center_y += self.rows * self.tile_h

    def on_draw(self):
        self.clear()
        self.bg_sprite_list.draw()
        arcade.draw_rect_filled(
            arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
            (0, 0, 0, 180)
        )

        self.title_text.draw()
        self.p1_text.draw()
        self.p2_text.draw()

        for i, character in enumerate(self.characters):
            x1, y = SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 - i * 220
            self._draw_char_element(character, i, x1, y, 1)

            x2 = 3 * SCREEN_WIDTH // 4
            self._draw_char_element(character, i, x2, y, 2)

        if self.current_player == 1:
            arcade.draw_text("← ВЫБИРАЕТ", SCREEN_WIDTH // 4 - 150, SCREEN_HEIGHT - 180, arcade.color.GREEN, 16)
        else:
            arcade.draw_text("ВЫБИРАЕТ →", 3 * SCREEN_WIDTH // 4 + 150, SCREEN_HEIGHT - 180, arcade.color.GREEN, 16)

        self.instruction_text.draw()
        self.start_text.draw()

    def _draw_char_element(self, character, i, x, y, player_num):
        if character in self.logos:
            tex = self.logos[character]
            scale = min(150 / tex.width, 120 / tex.height)
            arcade.draw_texture_rect(tex, arcade.XYWH(x, y + 40, tex.width * scale, tex.height * scale))

        selected_idx = self.p1_selected if player_num == 1 else self.p2_selected
        player_color = arcade.color.CYAN if player_num == 1 else arcade.color.ORANGE

        if self.current_player == player_num and i == selected_idx:
            color = arcade.color.GREEN
        elif i == selected_idx:
            color = player_color
        else:
            color = arcade.color.GRAY

        arcade.draw_text(character if character == "DIO" else "Jotaro Kujo", x, y - 40, color, 20, anchor_x="center")

        if i == selected_idx:
            arcade.draw_lrbt_rectangle_outline(x - 120, x + 120, y - 70, y + 110, color, 3)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            if self.current_player == 1:
                self.p1_selected = (self.p1_selected - 1) % len(self.characters)
            else:
                self.p2_selected = (self.p2_selected - 1) % len(self.characters)
        elif key == arcade.key.DOWN:
            if self.current_player == 1:
                self.p1_selected = (self.p1_selected + 1) % len(self.characters)
            else:
                self.p2_selected = (self.p2_selected + 1) % len(self.characters)
        elif key == arcade.key.ENTER:
            self.current_player = 2 if self.current_player == 1 else 1
        elif key == arcade.key.SPACE:
            self.current_player = 3 - self.current_player
        elif key == arcade.key.S:
            p1_char = self.characters[self.p1_selected]
            p2_char = self.characters[self.p2_selected]
            print(f"Запуск боя 1 на 1: {self.p1_name}={p1_char}, {self.p2_name}={p2_char}")

            game_view = OneVsOneGameView(self.p1_name, self.p2_name, p1_char, p2_char)
            game_view.intro_mode = True
            game_view.intro_timer = 0
            self.window.show_view(game_view)
        elif key == arcade.key.ESCAPE:
            self.window.show_view(ModeMenuView())


class OneVsOneGameView(arcade.View):
    def __init__(self, p1_name, p2_name, p1_character, p2_character):
        super().__init__()

        self.p1_name = p1_name
        self.p2_name = p2_name
        self.p1_character_name = p1_character
        self.p2_character_name = p2_character

        # База данных
        self.db = Database()

        # Статистика игроков
        self.p1_stats = PlayerStats(p1_name)
        self.p2_stats = PlayerStats(p2_name)

        map_index = random.randint(0, 3)
        map_path = Path("Карта") / f"jojo_map_{map_index}.png"

        self.background = None
        if map_path.exists():
            self.background = arcade.load_texture(str(map_path))

        # Анимации
        self.intro_mode = False
        self.intro_timer = 0
        self.victory_mode = False
        self.victory_timer = 0
        self.winner = None
        self.loser = None
        self.show_stats = False
        self.stats_timer = 0

        # Флаги управления P1 (WASD + J/I/L)
        self.p1_left = False
        self.p1_right = False
        self.p1_up = False
        self.p1_down = False
        self.p1_w_was_pressed = False
        self.p1_s_was_pressed = False
        self.p1_shift_was_pressed = False
        self.p1_attack1_pressed = False  # J
        self.p1_attack2_pressed = False  # I
        self.p1_attack3_pressed = False  # L
        self.p1_stand_pressed = False

        # Флаги управления P2 (IJKL + U/M)
        self.p2_left = False
        self.p2_right = False
        self.p2_up = False
        self.p2_down = False
        self.p2_i_was_pressed = False
        self.p2_k_was_pressed = False
        self.p2_shift_was_pressed = False
        self.p2_attack_pressed = False
        self.p2_stand_pressed = False

        self.player1 = None
        self.player2 = None
        self.player1_list = None
        self.player2_list = None
        self.physics1 = None
        self.physics2 = None

        self.setup()

    def setup(self):
        self.player1 = Character(self.p1_character_name, SCREEN_WIDTH // 4, GROUND_LEVEL, player_number=1)
        self.player2 = Character(self.p2_character_name, 3 * SCREEN_WIDTH // 4, GROUND_LEVEL, player_number=2)

        # Привязываем статистику к персонажам
        self.player1.stats = self.p1_stats
        self.player2.stats = self.p2_stats

        self.player1.set_opponent(self.player2)
        self.player2.set_opponent(self.player1)

        self.player1_list = arcade.SpriteList()
        self.player1_list.append(self.player1)
        self.physics1 = arcade.PhysicsEngineSimple(self.player1, None)

        self.player2_list = arcade.SpriteList()
        self.player2_list.append(self.player2)
        self.physics2 = arcade.PhysicsEngineSimple(self.player2, None)

        # Запускаем анимацию приветствия
        if self.intro_mode:
            if "intro" in self.player1.frame_ranges:
                self.player1.set_action("intro")
            else:
                self.player1.set_action("idle")

            if "intro" in self.player2.frame_ranges:
                self.player2.set_action("intro")
            else:
                self.player2.set_action("idle")

            # Поворачиваем персонажей друг к другу
            self.player1.facing_right = True
            self.player2.facing_right = False

    def on_show(self):
        pass

    def on_draw(self):
        self.clear()

        if self.background:
            arcade.draw_texture_rect(
                self.background,
                arcade.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        else:
            arcade.set_background_color(arcade.color.BLACK)

        arcade.draw_line(0, GROUND_LEVEL, SCREEN_WIDTH, GROUND_LEVEL, arcade.color.GREEN, 3)

        if self.player1:
            self.player1.draw_stand()
        if self.player2:
            self.player2.draw_stand()

        if self.player1:
            self.player1_list.draw()
        if self.player2:
            self.player2_list.draw()

        if self.player1:
            self.player1.draw_health_bar()
            self.player1.draw_stand_meter()
        if self.player2:
            self.player2.draw_health_bar()
            self.player2.draw_stand_meter()

        # Отображаем имена игроков
        arcade.draw_text(self.p1_name, SCREEN_WIDTH // 4, SCREEN_HEIGHT - 20,
                         arcade.color.CYAN, 18, anchor_x="center", bold=True)
        arcade.draw_text(self.p2_name, 3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT - 20,
                         arcade.color.ORANGE, 18, anchor_x="center", bold=True)

        if self.intro_mode:
            arcade.draw_rect_filled(
                arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
                (0, 0, 0, 100)
            )

            arcade.draw_text(f"{self.player1.character_data['display_name']}",
                             SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 100,
                             arcade.color.CYAN, 36, anchor_x="center", bold=True)
            arcade.draw_text(f"{self.player2.character_data['display_name']}",
                             3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 100,
                             arcade.color.ORANGE, 36, anchor_x="center", bold=True)

            arcade.draw_text("VS", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50,
                             arcade.color.RED, 48, anchor_x="center", bold=True)

            if self.intro_timer >= INTRO_ANIMATION_DURATION - INTRO_FIGHT_DURATION:
                alpha = min(255, (self.intro_timer - (INTRO_ANIMATION_DURATION - INTRO_FIGHT_DURATION)) * 8)
                arcade.draw_text("FIGHT!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50,
                                 (255, 255, 255, alpha), 48, anchor_x="center", bold=True)

        elif self.victory_mode and self.winner and self.loser:
            arcade.draw_rect_filled(
                arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
                (0, 0, 0, 150)
            )

            if self.victory_timer < 30:
                alpha = min(255, self.victory_timer * 8)
                arcade.draw_text("K.O.!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                 (255, 0, 0, alpha), 64, anchor_x="center", bold=True)
            elif self.victory_timer > 60:
                winner_name = self.winner.character_data['display_name']
                player_name = self.p1_name if self.winner == self.player1 else self.p2_name
                arcade.draw_text(f"{player_name} WINS!",
                                 SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50,
                                 arcade.color.GOLD, 48, anchor_x="center", bold=True)

                # Показываем статистику
                if self.show_stats:
                    self.draw_match_stats()

        else:
            info_y = SCREEN_HEIGHT - 150
            if self.player1 and hasattr(self.player1, 'character_data'):
                arcade.draw_text("ИГРОК 1", SCREEN_WIDTH // 4, info_y, arcade.color.CYAN, 20, anchor_x="center")
                info_y -= 30
                arcade.draw_text(f"Действие: {self.player1.current_action}",
                                 SCREEN_WIDTH // 4, info_y, arcade.color.WHITE, 14, anchor_x="center")
                info_y -= 25
                if self.player1.is_attacking:
                    combo_info = f"Атака: {self.player1.current_attack}"
                    if self.player1.attack_hit:
                        combo_info += " (попадание)"
                    arcade.draw_text(combo_info, SCREEN_WIDTH // 4, info_y, arcade.color.YELLOW, 14, anchor_x="center")

            info_y = SCREEN_HEIGHT - 150
            if self.player2 and hasattr(self.player2, 'character_data'):
                arcade.draw_text("ИГРОК 2", 3 * SCREEN_WIDTH // 4, info_y, arcade.color.ORANGE, 20, anchor_x="center")
                info_y -= 30
                arcade.draw_text(f"Действие: {self.player2.current_action}",
                                 3 * SCREEN_WIDTH // 4, info_y, arcade.color.WHITE, 14, anchor_x="center")
                info_y -= 25
                if self.player2.is_attacking:
                    combo_info = f"Атака: {self.player2.current_attack}"
                    if self.player2.attack_hit:
                        combo_info += " (попадание)"
                    arcade.draw_text(combo_info, 3 * SCREEN_WIDTH // 4, info_y, arcade.color.YELLOW, 14,
                                     anchor_x="center")

            # Текст управления
            arcade.draw_text("WASD + Shift | J - Атака 1 | I - Атака 2 | L - Атака 3 | K - Стенд",
                             SCREEN_WIDTH // 4, 80, arcade.color.CYAN, 14, anchor_x="center")
            arcade.draw_text("IJKL - движение | U - Атака | M - Стенд | Shift - рывок",
                             3 * SCREEN_WIDTH // 4, 80, arcade.color.ORANGE, 14, anchor_x="center")

        arcade.draw_text("ESC - меню", SCREEN_WIDTH - 120, 30, arcade.color.GRAY, 14)

    def draw_match_stats(self):
        """Отрисовка статистики матча"""
        y_start = SCREEN_HEIGHT // 2 - 50

        arcade.draw_text("СТАТИСТИКА МАТЧА", SCREEN_WIDTH // 2, y_start + 100,
                         arcade.color.GOLD, 24, anchor_x="center", bold=True)

        # Статистика игрока 1
        arcade.draw_text(self.p1_name, SCREEN_WIDTH // 4, y_start + 50,
                         arcade.color.CYAN, 18, anchor_x="center", bold=True)
        arcade.draw_text(f"Попаданий: {self.p1_stats.hits_landed}", SCREEN_WIDTH // 4, y_start + 20,
                         arcade.color.WHITE, 16, anchor_x="center")
        arcade.draw_text(f"Блоков: {self.p1_stats.blocks_successful}", SCREEN_WIDTH // 4, y_start - 10,
                         arcade.color.WHITE, 16, anchor_x="center")
        arcade.draw_text(f"Рывков: {self.p1_stats.dashes_used}", SCREEN_WIDTH // 4, y_start - 40,
                         arcade.color.WHITE, 16, anchor_x="center")
        arcade.draw_text(f"Очки: {self.p1_stats.points_earned}", SCREEN_WIDTH // 4, y_start - 70,
                         arcade.color.GOLD, 18, anchor_x="center", bold=True)

        # Статистика игрока 2
        arcade.draw_text(self.p2_name, 3 * SCREEN_WIDTH // 4, y_start + 50,
                         arcade.color.ORANGE, 18, anchor_x="center", bold=True)
        arcade.draw_text(f"Попаданий: {self.p2_stats.hits_landed}", 3 * SCREEN_WIDTH // 4, y_start + 20,
                         arcade.color.WHITE, 16, anchor_x="center")
        arcade.draw_text(f"Блоков: {self.p2_stats.blocks_successful}", 3 * SCREEN_WIDTH // 4, y_start - 10,
                         arcade.color.WHITE, 16, anchor_x="center")
        arcade.draw_text(f"Рывков: {self.p2_stats.dashes_used}", 3 * SCREEN_WIDTH // 4, y_start - 40,
                         arcade.color.WHITE, 16, anchor_x="center")
        arcade.draw_text(f"Очки: {self.p2_stats.points_earned}", 3 * SCREEN_WIDTH // 4, y_start - 70,
                         arcade.color.GOLD, 18, anchor_x="center", bold=True)

        arcade.draw_text("Нажмите ENTER для продолжения", SCREEN_WIDTH // 2, y_start - 150,
                         arcade.color.GRAY, 16, anchor_x="center")

    def on_update(self, delta_time):
        if not self.player1 or not self.player2:
            return

        if self.intro_mode:
            self.intro_timer += 1
            self.player1.update()
            self.player2.update()

            if self.intro_timer >= INTRO_ANIMATION_DURATION:
                self.intro_mode = False
                self.intro_timer = 0
                self.player1.set_action("idle")
                self.player2.set_action("idle")
            return

        if self.victory_mode:
            self.victory_timer += 1

            if self.winner:
                self.winner.update()
            if self.loser:
                self.loser.update()

            if self.victory_timer >= VICTORY_ANIMATION_DURATION and not self.show_stats:
                self.show_stats = True
                self.victory_timer = VICTORY_ANIMATION_DURATION
            return

        if self.player1.current_health <= 0:
            self.show_game_over(self.player2, self.player1)
            return
        if self.player2.current_health <= 0:
            self.show_game_over(self.player1, self.player2)
            return

        # ИГРОК 1 (WASD + J/I/L)
        if not self.player1.is_summoning and not self.player1.is_hit:
            if not self.player1.is_dashing and not self.player1.is_attacking:
                self.player1.change_x = 0

                if not self.player1.is_crouching:
                    if self.p1_left:
                        self.player1.change_x = -self.player1.movement_speed
                        if not self.player1.is_jumping:
                            action = self.player1.get_action_for_movement(True, False)
                            if action:
                                self.player1.set_action(action)

                    if self.p1_right:
                        self.player1.change_x = self.player1.movement_speed
                        if not self.player1.is_jumping:
                            action = self.player1.get_action_for_movement(False, True)
                            if action:
                                self.player1.set_action(action)

                if (not self.p1_left and not self.p1_right and
                        not self.player1.is_jumping and
                        not self.player1.is_attacking and
                        self.player1.current_action not in ["crouch"]):
                    self.player1.set_action("idle")

            if self.p1_up and not self.p1_w_was_pressed:
                if not self.player1.is_crouching and not self.player1.is_dashing and not self.player1.is_attacking:
                    self.player1.jump()
                self.p1_w_was_pressed = True

            if self.p1_down and not self.p1_s_was_pressed:
                self.player1.crouch(True)
                self.p1_s_was_pressed = True

            if not self.p1_down and self.p1_s_was_pressed:
                self.player1.crouch(False)
                self.p1_s_was_pressed = False

            if self.p1_shift_was_pressed and not self.player1.is_dashing and self.player1.dash_cooldown == 0:
                if self.p1_left:
                    self.player1.dash(-1)
                elif self.p1_right:
                    self.player1.dash(1)
                else:
                    self.player1.dash()

            # Обработка трех разных атак
            if self.p1_attack1_pressed:
                self.player1.attack1()
            if self.p1_attack2_pressed:
                self.player1.attack2()
            if self.p1_attack3_pressed:
                self.player1.attack3()

            if self.p1_stand_pressed and not self.player1.is_summoning and not self.player1.is_attacking:
                self.player1.toggle_stand()
                self.p1_stand_pressed = False
        else:
            self.player1.change_x = 0

        # ИГРОК 2 (IJKL + U/M)
        if not self.player2.is_summoning and not self.player2.is_hit:
            if not self.player2.is_dashing and not self.player2.is_attacking:
                self.player2.change_x = 0

                if not self.player2.is_crouching:
                    if self.p2_left:
                        self.player2.change_x = -self.player2.movement_speed
                        if not self.player2.is_jumping:
                            action = self.player2.get_action_for_movement(True, False)
                            if action:
                                self.player2.set_action(action)

                    if self.p2_right:
                        self.player2.change_x = self.player2.movement_speed
                        if not self.player2.is_jumping:
                            action = self.player2.get_action_for_movement(False, True)
                            if action:
                                self.player2.set_action(action)

                if (not self.p2_left and not self.p2_right and
                        not self.player2.is_jumping and
                        not self.player2.is_attacking and
                        self.player2.current_action not in ["crouch"]):
                    self.player2.set_action("idle")

            if self.p2_up and not self.p2_i_was_pressed:
                if not self.player2.is_crouching and not self.player2.is_dashing and not self.player2.is_attacking:
                    self.player2.jump()
                self.p2_i_was_pressed = True

            if self.p2_down and not self.p2_k_was_pressed:
                self.player2.crouch(True)
                self.p2_k_was_pressed = True

            if not self.p2_down and self.p2_k_was_pressed:
                self.player2.crouch(False)
                self.p2_k_was_pressed = False

            if self.p2_shift_was_pressed and not self.player2.is_dashing and self.player2.dash_cooldown == 0:
                if self.p2_left:
                    self.player2.dash(-1)
                elif self.p2_right:
                    self.player2.dash(1)
                else:
                    self.player2.dash()

            if self.p2_attack_pressed and not self.player2.is_attacking:
                self.player2.attack()

            if self.p2_stand_pressed and not self.player2.is_summoning and not self.player2.is_attacking:
                self.player2.toggle_stand()
                self.p2_stand_pressed = False
        else:
            self.player2.change_x = 0

        if self.physics1 and self.physics2:
            self.physics1.update()
            self.physics2.update()

        if self.player1:
            self.player1.update()
            if self.player1.stand_active and self.player1.stand:
                self.player1.stand.update()

        if self.player2:
            self.player2.update()
            if self.player2.stand_active and self.player2.stand:
                self.player2.stand.update()

    def show_game_over(self, winner, loser):
        self.winner = winner
        self.loser = loser

        # Добавляем очки за убийство и победу
        winner.stats.add_kill()
        winner.stats.add_win_bonus()

        self.victory_mode = True
        self.victory_timer = 0

        # Запускаем анимации победы и поражения
        if "victory" in winner.frame_ranges:
            winner.set_action("victory")
        else:
            winner.set_action("idle")

        if "defeat" in loser.frame_ranges:
            loser.set_action("defeat")
        else:
            loser.set_action("crouch")

        # Убираем стенды для чистоты
        if winner.stand_active:
            winner.stand_active = False
            winner.stand = None
            winner.stand_sprite_list.clear()
        if loser.stand_active:
            loser.stand_active = False
            loser.stand = None
            loser.stand_sprite_list.clear()

        # Разворачиваем победителя к проигравшему
        if winner.center_x < loser.center_x:
            winner.facing_right = True
            loser.facing_right = False
        else:
            winner.facing_right = False
            loser.facing_right = True

        print(f"Анимация победы: {winner.character_name} - victory, {loser.character_name} - defeat")

    def save_stats_to_db(self):
        """Сохранение статистики в базу данных"""
        # Получаем или создаем игроков
        self.db.get_or_create_player(self.p1_name)
        self.db.get_or_create_player(self.p2_name)

        # Обновляем статистику
        self.db.update_player_stats(self.p1_name, self.p1_stats.get_stats_dict())
        self.db.update_player_stats(self.p2_name, self.p2_stats.get_stats_dict())

        # Сохраняем информацию о матче
        winner_name = self.p1_name if self.winner == self.player1 else self.p2_name
        self.db.save_match(
            self.p1_name, self.p2_name, winner_name,
            self.p1_stats.points_earned, self.p2_stats.points_earned
        )

    def on_key_press(self, key, modifiers):
        if self.intro_mode:
            return

        if self.victory_mode and self.show_stats:
            if key == arcade.key.ENTER:
                # Сохраняем статистику и выходим
                self.save_stats_to_db()
                self.window.show_view(ModeMenuView())
            return

        # Игрок 1 (WASD + J/I/L)
        if key == arcade.key.A:
            self.p1_left = True
        elif key == arcade.key.D:
            self.p1_right = True
        elif key == arcade.key.W:
            self.p1_up = True
        elif key == arcade.key.S:
            self.p1_down = True
        elif key == arcade.key.LSHIFT or key == arcade.key.RSHIFT:
            self.p1_shift_was_pressed = True
        elif key == arcade.key.J:  # Атака 1
            self.p1_attack1_pressed = True
        elif key == arcade.key.I:  # Атака 2
            self.p1_attack2_pressed = True
        elif key == arcade.key.L:  # Атака 3
            self.p1_attack3_pressed = True
        elif key == arcade.key.K:  # Стенд
            self.p1_stand_pressed = True

        # Игрок 2 (IJKL + U/M)
        elif key == arcade.key.J:
            self.p2_left = True
        elif key == arcade.key.L:
            self.p2_right = True
        elif key == arcade.key.I:
            self.p2_up = True
        elif key == arcade.key.K:
            self.p2_down = True
        elif key == arcade.key.RSHIFT:
            self.p2_shift_was_pressed = True
        elif key == arcade.key.U:
            if self.player2 and not self.p2_attack_pressed:
                self.player2.attack()
                self.p2_attack_pressed = True
        elif key == arcade.key.M:
            self.p2_stand_pressed = True

        elif key == arcade.key.ESCAPE:
            self.window.show_view(ModeMenuView())

    def on_key_release(self, key, modifiers):
        if self.intro_mode or self.victory_mode:
            return

        # Игрок 1
        if key == arcade.key.A:
            self.p1_left = False
        elif key == arcade.key.D:
            self.p1_right = False
        elif key == arcade.key.W:
            self.p1_up = False
            self.p1_w_was_pressed = False
        elif key == arcade.key.S:
            self.p1_down = False
            self.p1_s_was_pressed = False
        elif key == arcade.key.LSHIFT or key == arcade.key.RSHIFT:
            self.p1_shift_was_pressed = False
        elif key == arcade.key.J:
            self.p1_attack1_pressed = False
        elif key == arcade.key.I:
            self.p1_attack2_pressed = False
        elif key == arcade.key.L:
            self.p1_attack3_pressed = False

        # Игрок 2
        elif key == arcade.key.J:
            self.p2_left = False
        elif key == arcade.key.L:
            self.p2_right = False
        elif key == arcade.key.I:
            self.p2_up = False
            self.p2_i_was_pressed = False
        elif key == arcade.key.K:
            self.p2_down = False
            self.p2_k_was_pressed = False
        elif key == arcade.key.RSHIFT:
            self.p2_shift_was_pressed = False
        elif key == arcade.key.U:
            self.p2_attack_pressed = False


class LeaderboardView(arcade.View):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.leaders = self.db.get_leaderboard(15)

        self.bg_sprite_list = arcade.SpriteList()
        bg_path = Path("Лого") / "fon_menu.png"

        orig_w, orig_h = 128, 64
        self.bg_scale = SCREEN_WIDTH / (5 * orig_w)
        self.tile_w, self.tile_h = orig_w * self.bg_scale, orig_h * self.bg_scale
        self.rows = 8

        if bg_path.exists():
            for r in range(self.rows):
                for c in range(5):
                    s = arcade.Sprite(str(bg_path), scale=self.bg_scale)
                    s.center_x = c * self.tile_w + (self.tile_w / 2)
                    s.center_y = r * self.tile_h + (self.tile_h / 2)
                    self.bg_sprite_list.append(s)

    def on_update(self, delta_time):
        for s in self.bg_sprite_list:
            s.center_y -= 3.0
            if s.top < 0:
                s.center_y += self.rows * self.tile_h

    def on_draw(self):
        self.clear()
        self.bg_sprite_list.draw()
        arcade.draw_rect_filled(
            arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
            (0, 0, 0, 200)
        )

        arcade.draw_text("ТАБЛИЦА ЛИДЕРОВ", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                         arcade.color.GOLD, 40, anchor_x="center", bold=True)

        if not self.leaders:
            arcade.draw_text("Пока нет игроков", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                             arcade.color.GRAY, 24, anchor_x="center")
        else:
            # Заголовки
            arcade.draw_text("№", SCREEN_WIDTH // 2 - 350, SCREEN_HEIGHT - 180,
                             arcade.color.CYAN, 18, anchor_x="center")
            arcade.draw_text("ИМЯ", SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 180,
                             arcade.color.CYAN, 18, anchor_x="center")
            arcade.draw_text("ОЧКИ", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 180,
                             arcade.color.CYAN, 18, anchor_x="center")
            arcade.draw_text("ИГРЫ", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 180,
                             arcade.color.CYAN, 18, anchor_x="center")
            arcade.draw_text("ПОБЕДЫ", SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT - 180,
                             arcade.color.CYAN, 18, anchor_x="center")
            arcade.draw_text("УБИЙСТВА", SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT - 180,
                             arcade.color.CYAN, 18, anchor_x="center")
            arcade.draw_text("КОМБО", SCREEN_WIDTH // 2 + 300, SCREEN_HEIGHT - 180,
                             arcade.color.CYAN, 18, anchor_x="center")

            # Список игроков
            for i, leader in enumerate(self.leaders):
                y = SCREEN_HEIGHT - 220 - i * 35
                if i == 0:
                    color = arcade.color.GOLD
                elif i == 1:
                    color = arcade.color.SILVER
                elif i == 2:
                    color = arcade.color.BROWN
                else:
                    color = arcade.color.WHITE

                arcade.draw_text(f"{i + 1}", SCREEN_WIDTH // 2 - 350, y, color, 16, anchor_x="center")
                arcade.draw_text(leader[0], SCREEN_WIDTH // 2 - 250, y, color, 16, anchor_x="center")
                arcade.draw_text(str(leader[1]), SCREEN_WIDTH // 2 - 100, y, color, 16, anchor_x="center")
                arcade.draw_text(str(leader[2]), SCREEN_WIDTH // 2, y, color, 16, anchor_x="center")
                arcade.draw_text(str(leader[3]), SCREEN_WIDTH // 2 + 100, y, color, 16, anchor_x="center")
                arcade.draw_text(str(leader[5]), SCREEN_WIDTH // 2 + 200, y, color, 16, anchor_x="center")
                arcade.draw_text(str(leader[7]), SCREEN_WIDTH // 2 + 300, y, color, 16, anchor_x="center")

        arcade.draw_text("ESC - назад | R - обновить", SCREEN_WIDTH // 2, 100,
                         arcade.color.GRAY, 18, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(ModeMenuView())
        elif key == arcade.key.R:
            self.leaders = self.db.get_leaderboard(15)


class TestCharacterSelectView(arcade.View):
    def __init__(self):
        super().__init__()
        print("TestCharacterSelectView инициализирован")

        self.bg_sprite_list = arcade.SpriteList()
        bg_path = Path("Лого") / "fon_menu.png"

        orig_w, orig_h = 128, 64
        self.bg_scale = SCREEN_WIDTH / (5 * orig_w)
        self.tile_w, self.tile_h = orig_w * self.bg_scale, orig_h * self.bg_scale
        self.rows = 8

        if bg_path.exists():
            for r in range(self.rows):
                for c in range(5):
                    s = arcade.Sprite(str(bg_path), scale=self.bg_scale)
                    s.center_x = c * self.tile_w + (self.tile_w / 2)
                    s.center_y = r * self.tile_h + (self.tile_h / 2)
                    self.bg_sprite_list.append(s)

        self.characters = get_available_characters()
        self.p1_selected = 0
        self.p2_selected = 0
        self.current_player = 1

        self.logos = {}
        self.load_logos()

        self.title_text = arcade.Text(
            "ВЫБОР ПЕРСОНАЖЕЙ ДЛЯ ТЕСТОВОГО РЕЖИМА",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
            arcade.color.WHITE, 36, anchor_x="center"
        )
        self.p1_text = arcade.Text("ИГРОК 1 (WASD + J/I/L)", SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150, arcade.color.CYAN,
                                   28,
                                   anchor_x="center")
        self.p2_text = arcade.Text("ИГРОК 2 (ГЕЙМПАД + Стрелки)", 3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150,
                                   arcade.color.ORANGE,
                                   28, anchor_x="center")
        self.instruction_text = arcade.Text("ENTER - выбрать | ПРОБЕЛ - переключить | ESC - назад", SCREEN_WIDTH // 2,
                                            80, arcade.color.GRAY, 16, anchor_x="center")
        self.start_text = arcade.Text("После выбора обоих нажмите S для старта", SCREEN_WIDTH // 2, 50,
                                      arcade.color.GREEN, 18, anchor_x="center")

    def load_logos(self):
        logos_path = Path("Лого")
        for character in self.characters:
            for file_path in logos_path.glob(f"{character}.*"):
                try:
                    self.logos[character] = arcade.load_texture(str(file_path))
                except:
                    pass

    def on_update(self, delta_time):
        for s in self.bg_sprite_list:
            s.center_y -= 3.0
            if s.top < 0:
                s.center_y += self.rows * self.tile_h

    def on_draw(self):
        self.clear()
        self.bg_sprite_list.draw()
        arcade.draw_rect_filled(
            arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
            (0, 0, 0, 180)
        )

        self.title_text.draw()
        self.p1_text.draw()
        self.p2_text.draw()

        for i, character in enumerate(self.characters):
            x1, y = SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 - i * 220
            self._draw_char_element(character, i, x1, y, 1)

            x2 = 3 * SCREEN_WIDTH // 4
            self._draw_char_element(character, i, x2, y, 2)

        if self.current_player == 1:
            arcade.draw_text("← ВЫБИРАЕТ", SCREEN_WIDTH // 4 - 150, SCREEN_HEIGHT - 180, arcade.color.GREEN, 16)
        else:
            arcade.draw_text("ВЫБИРАЕТ →", 3 * SCREEN_WIDTH // 4 + 150, SCREEN_HEIGHT - 180, arcade.color.GREEN, 16)

        self.instruction_text.draw()
        self.start_text.draw()

    def _draw_char_element(self, character, i, x, y, player_num):
        if character in self.logos:
            tex = self.logos[character]
            scale = min(150 / tex.width, 120 / tex.height)
            arcade.draw_texture_rect(tex, arcade.XYWH(x, y + 40, tex.width * scale, tex.height * scale))

        selected_idx = self.p1_selected if player_num == 1 else self.p2_selected
        player_color = arcade.color.CYAN if player_num == 1 else arcade.color.ORANGE

        if self.current_player == player_num and i == selected_idx:
            color = arcade.color.GREEN
        elif i == selected_idx:
            color = player_color
        else:
            color = arcade.color.GRAY

        arcade.draw_text(character if character == "DIO" else "Jotaro Kujo", x, y - 40, color, 20, anchor_x="center")

        if i == selected_idx:
            arcade.draw_lrbt_rectangle_outline(x - 120, x + 120, y - 70, y + 110, color, 3)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            if self.current_player == 1:
                self.p1_selected = (self.p1_selected - 1) % len(self.characters)
            else:
                self.p2_selected = (self.p2_selected - 1) % len(self.characters)
        elif key == arcade.key.DOWN:
            if self.current_player == 1:
                self.p1_selected = (self.p1_selected + 1) % len(self.characters)
            else:
                self.p2_selected = (self.p2_selected + 1) % len(self.characters)
        elif key == arcade.key.ENTER:
            self.current_player = 2 if self.current_player == 1 else 1
        elif key == arcade.key.SPACE:
            self.current_player = 3 - self.current_player
        elif key == arcade.key.S:
            p1_char = self.characters[self.p1_selected]
            p2_char = self.characters[self.p2_selected]
            print(f"Запуск тестового режима: P1={p1_char}, P2={p2_char}")

            game_view = TestGameView(p1_char, p2_char)
            game_view.intro_mode = True
            game_view.intro_timer = 0
            self.window.show_view(game_view)
        elif key == arcade.key.ESCAPE:
            self.window.show_view(ModeMenuView())


class TestGameView(arcade.View):
    def __init__(self, p1_character, p2_character):
        super().__init__()

        self.p1_character_name = p1_character
        self.p2_character_name = p2_character
        map_index = random.randint(0, 3)
        map_path = Path("Карта") / f"jojo_map_{map_index}.png"

        self.background = None
        if map_path.exists():
            self.background = arcade.load_texture(str(map_path))

        # Анимации
        self.intro_mode = False
        self.intro_timer = 0
        self.victory_mode = False
        self.victory_timer = 0
        self.winner = None
        self.loser = None

        # Флаги управления P1 (WASD + J/I/L)
        self.p1_left = False
        self.p1_right = False
        self.p1_up = False
        self.p1_down = False
        self.p1_w_was_pressed = False
        self.p1_s_was_pressed = False
        self.p1_shift_was_pressed = False
        self.p1_attack1_pressed = False  # J
        self.p1_attack2_pressed = False  # I
        self.p1_attack3_pressed = False  # L
        self.p1_stand_pressed = False

        # Флаги управления P2 (клавиатура стрелки + ГЕЙМПАД)
        self.p2_left = False
        self.p2_right = False
        self.p2_up = False
        self.p2_down = False
        self.p2_up_was_pressed = False
        self.p2_down_was_pressed = False
        self.p2_shift_was_pressed = False
        self.p2_attack1_pressed = False  # X (атака 1)
        self.p2_attack2_pressed = False  # Y (атака 2)
        self.p2_attack3_pressed = False  # B (атака 3)
        self.p2_stand_pressed = False    # A (стенд)

        # === ГЕЙМПАД ===
        self.controller = None
        self.init_controller()

        # Флаги для предотвращения множественных вызовов
        self.stand_key_processed = False
        self.attack1_key_processed = False
        self.attack2_key_processed = False
        self.attack3_key_processed = False

        self.player1 = None
        self.player2 = None
        self.player1_list = None
        self.player2_list = None
        self.physics1 = None
        self.physics2 = None

        self.setup()

    def init_controller(self):
        """Инициализация геймпада"""
        controllers = arcade.get_controllers()
        if controllers:
            self.controller = controllers[0]
            self.controller.open()
            self.controller.push_handlers(self)
            print(f"Геймпад подключен: {self.controller.device.name}")
            print("Управление для ИГРОКА 2 через геймпад:")
            print("  Левый стик - движение")
            print("  A - Стенд")
            print("  X - Атака 1")
            print("  Y - Атака 2")
            print("  B - Атака 3")
            print("  LB/RB - Рывок")
            print("  D-pad - движение (альтернатива)")
        else:
            print("Геймпад не найден. Игрок 2 будет использовать клавиатуру (стрелки)")

    # === ОБРАБОТЧИКИ ГЕЙМПАДА ===

    def on_stick_motion(self, controller, stick_name, vector):
        """Обработка движения стиков с мертвой зоной"""
        if not self.player2 or self.intro_mode or self.victory_mode:
            return

        # Мертвая зона - значение 0.3 (30%)
        DEAD_ZONE = 0.3

        # Левый стик - движение для игрока 2
        if stick_name == "leftstick":
            # Движение по горизонтали с мертвой зоной
            if abs(vector.x) > DEAD_ZONE:
                if vector.x < 0:
                    self.p2_left = True
                    self.p2_right = False
                    print(f"Стик влево: {vector.x:.2f}")
                else:
                    self.p2_right = True
                    self.p2_left = False
                    print(f"Стик вправо: {vector.x:.2f}")
            else:
                self.p2_left = False
                self.p2_right = False

            # Движение по вертикали (прыжок/приседание) с мертвой зоной
            if abs(vector.y) > DEAD_ZONE:
                if vector.y > 0:  # Вверх
                    if not self.p2_up_was_pressed and not self.player2.is_jumping:
                        self.player2.jump()
                        self.p2_up_was_pressed = True
                        print(f"Прыжок: {vector.y:.2f}")
                    self.p2_up = True
                elif vector.y < 0:  # Вниз
                    if not self.p2_down_was_pressed and not self.player2.is_crouching:
                        self.player2.crouch(True)
                        self.p2_down_was_pressed = True
                        print(f"Приседание: {vector.y:.2f}")
                    self.p2_down = True
            else:
                self.p2_up = False
                self.p2_down = False
                if self.p2_up_was_pressed:
                    self.p2_up_was_pressed = False
                if self.p2_down_was_pressed:
                    self.player2.crouch(False)
                    self.p2_down_was_pressed = False

    def on_dpad_motion(self, controller, vector):
        """Обработка D-pad (крестовины) - альтернативное управление"""
        if not self.player2 or self.intro_mode or self.victory_mode:
            return

        # D-pad для движения
        if vector.x < 0:  # Влево
            self.p2_left = True
            self.p2_right = False
        elif vector.x > 0:  # Вправо
            self.p2_right = True
            self.p2_left = False
        else:
            # Если D-pad не двигается по X, не сбрасываем движение,
            # так как стик тоже может управлять
            if not (abs(self.controller.leftx) > 0.1 if self.controller else False):
                self.p2_left = False
                self.p2_right = False

        # D-pad для прыжка/приседания
        if vector.y > 0:  # Вверх
            if not self.p2_up_was_pressed and not self.player2.is_jumping:
                self.player2.jump()
                self.p2_up_was_pressed = True
        elif vector.y < 0:  # Вниз
            if not self.p2_down_was_pressed and not self.player2.is_crouching:
                self.player2.crouch(True)
                self.p2_down_was_pressed = True
        else:
            if self.p2_up_was_pressed:
                self.p2_up_was_pressed = False
            if self.p2_down_was_pressed:
                self.player2.crouch(False)
                self.p2_down_was_pressed = False

    def on_button_press(self, controller, button_name):
        """Обработка нажатия кнопок геймпада"""
        if not self.player2 or self.intro_mode or self.victory_mode:
            return

        print(f"Кнопка нажата: {button_name}")

        # Кнопки Xbox:
        # 'a' - A (стенд)
        # 'x' - X (атака 1)
        # 'y' - Y (атака 2)
        # 'b' - B (атака 3)
        # 'leftshoulder' - LB (рывок)
        # 'rightshoulder' - RB (рывок)
        # 'start' - Start (пауза/меню)

        if button_name == 'a' and not self.stand_key_processed:
            # A - призыв/убирание стенда
            self.player2.toggle_stand()
            self.stand_key_processed = True

        elif button_name == 'x' and not self.attack1_key_processed:
            # X - атака 1
            self.player2.attack1()
            self.attack1_key_processed = True

        elif button_name == 'y' and not self.attack2_key_processed:
            # Y - атака 2
            self.player2.attack2()
            self.attack2_key_processed = True

        elif button_name == 'b' and not self.attack3_key_processed:
            # B - атака 3
            self.player2.attack3()
            self.attack3_key_processed = True

        elif button_name in ['leftshoulder', 'rightshoulder'] and not self.p2_shift_was_pressed:
            # LB/RB - рывок
            self.p2_shift_was_pressed = True

        elif button_name == 'start':
            print("Пауза/Меню")

    def on_button_release(self, controller, button_name):
        """Обработка отпускания кнопок геймпада"""
        if not self.player2:
            return

        if button_name == 'a':
            # Сбрасываем флаг стенда
            self.stand_key_processed = False
        elif button_name == 'x':
            # Сбрасываем флаг атаки 1
            self.attack1_key_processed = False
        elif button_name == 'y':
            # Сбрасываем флаг атаки 2
            self.attack2_key_processed = False
        elif button_name == 'b':
            # Сбрасываем флаг атаки 3
            self.attack3_key_processed = False
        elif button_name in ['leftshoulder', 'rightshoulder']:
            self.p2_shift_was_pressed = False

    def on_trigger_motion(self, controller, trigger_name, value):
        """Обработка триггеров (можно использовать для рывка)"""
        if not self.player2 or self.intro_mode or self.victory_mode:
            return

        if value > 0.5:  # Триггер нажат достаточно сильно
            if not self.p2_shift_was_pressed:
                self.p2_shift_was_pressed = True
        else:
            self.p2_shift_was_pressed = False

    def setup(self):
        self.player1 = Character(self.p1_character_name, SCREEN_WIDTH // 4, GROUND_LEVEL, player_number=1)
        self.player2 = Character(self.p2_character_name, 3 * SCREEN_WIDTH // 4, GROUND_LEVEL, player_number=2)

        # В тестовом режиме НЕ создаем статистику (stats остается None)

        self.player1.set_opponent(self.player2)
        self.player2.set_opponent(self.player1)

        self.player1_list = arcade.SpriteList()
        self.player1_list.append(self.player1)
        self.physics1 = arcade.PhysicsEngineSimple(self.player1, None)

        self.player2_list = arcade.SpriteList()
        self.player2_list.append(self.player2)
        self.physics2 = arcade.PhysicsEngineSimple(self.player2, None)

        # Запускаем анимацию приветствия, если включен режим интро
        if hasattr(self, 'intro_mode') and self.intro_mode:
            if "intro" in self.player1.frame_ranges:
                self.player1.set_action("intro")
            else:
                self.player1.set_action("idle")

            if "intro" in self.player2.frame_ranges:
                self.player2.set_action("intro")
            else:
                self.player2.set_action("idle")

            # Поворачиваем персонажей друг к другу
            self.player1.facing_right = True
            self.player2.facing_right = False

    def on_show(self):
        pass

    def on_draw(self):
        self.clear()

        if self.background:
            arcade.draw_texture_rect(
                self.background,
                arcade.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        else:
            arcade.set_background_color(arcade.color.BLACK)

        arcade.draw_line(0, GROUND_LEVEL, SCREEN_WIDTH, GROUND_LEVEL, arcade.color.GREEN, 3)

        if self.player1:
            self.player1.draw_stand()
        if self.player2:
            self.player2.draw_stand()

        if self.player1:
            self.player1_list.draw()
        if self.player2:
            self.player2_list.draw()

        if self.player1:
            self.player1.draw_health_bar()
            self.player1.draw_stand_meter()
        if self.player2:
            self.player2.draw_health_bar()
            self.player2.draw_stand_meter()

        if self.intro_mode:
            arcade.draw_rect_filled(
                arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
                (0, 0, 0, 100)
            )

            arcade.draw_text(f"{self.player1.character_data['display_name']}",
                             SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 100,
                             arcade.color.CYAN, 36, anchor_x="center", bold=True)
            arcade.draw_text(f"{self.player2.character_data['display_name']}",
                             3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 + 100,
                             arcade.color.ORANGE, 36, anchor_x="center", bold=True)

            arcade.draw_text("VS", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50,
                             arcade.color.RED, 48, anchor_x="center", bold=True)

            if self.intro_timer >= INTRO_ANIMATION_DURATION - INTRO_FIGHT_DURATION:
                alpha = min(255, (self.intro_timer - (INTRO_ANIMATION_DURATION - INTRO_FIGHT_DURATION)) * 8)
                arcade.draw_text("FIGHT!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50,
                                 (255, 255, 255, alpha), 48, anchor_x="center", bold=True)

        elif self.victory_mode and self.winner and self.loser:
            arcade.draw_rect_filled(
                arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
                (0, 0, 0, 150)
            )

            if self.victory_timer < 30:
                alpha = min(255, self.victory_timer * 8)
                arcade.draw_text("K.O.!", SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                 (255, 0, 0, alpha), 64, anchor_x="center", bold=True)
            elif self.victory_timer > 60:
                winner_name = self.winner.character_data['display_name']
                arcade.draw_text(f"{winner_name} WINS!",
                                 SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                                 arcade.color.GOLD, 48, anchor_x="center", bold=True)

        else:
            info_y = SCREEN_HEIGHT - 150
            if self.player1 and hasattr(self.player1, 'character_data'):
                arcade.draw_text("ИГРОК 1", SCREEN_WIDTH // 4, info_y, arcade.color.CYAN, 20, anchor_x="center")
                info_y -= 30
                arcade.draw_text(f"Действие: {self.player1.current_action}",
                                 SCREEN_WIDTH // 4, info_y, arcade.color.WHITE, 14, anchor_x="center")
                info_y -= 25
                if self.player1.is_attacking:
                    combo_info = f"Атака: {self.player1.current_attack}"
                    if self.player1.attack_hit:
                        combo_info += " (попадание)"
                    arcade.draw_text(combo_info, SCREEN_WIDTH // 4, info_y, arcade.color.YELLOW, 14, anchor_x="center")

            info_y = SCREEN_HEIGHT - 150
            if self.player2 and hasattr(self.player2, 'character_data'):
                arcade.draw_text("ИГРОК 2", 3 * SCREEN_WIDTH // 4, info_y, arcade.color.ORANGE, 20, anchor_x="center")
                info_y -= 30
                arcade.draw_text(f"Действие: {self.player2.current_action}",
                                 3 * SCREEN_WIDTH // 4, info_y, arcade.color.WHITE, 14, anchor_x="center")
                info_y -= 25
                if self.player2.is_attacking:
                    combo_info = f"Атака: {self.player2.current_attack}"
                    if self.player2.attack_hit:
                        combo_info += " (попадание)"
                    arcade.draw_text(combo_info, 3 * SCREEN_WIDTH // 4, info_y, arcade.color.YELLOW, 14,
                                     anchor_x="center")

            # Обновленная информация об управлении
            arcade.draw_text("WASD + Shift | J - Атака 1 | I - Атака 2 | L - Атака 3 | K - Стенд",
                             SCREEN_WIDTH // 4, 80, arcade.color.CYAN, 14, anchor_x="center")

            if self.controller:
                arcade.draw_text("ГЕЙМПАД: Стик + LB/RB | A - Атака | X - Стенд",
                                 3 * SCREEN_WIDTH // 4, 80, arcade.color.ORANGE, 14, anchor_x="center")
            else:
                arcade.draw_text("Стрелки + Shift | Пробел - Атака | NUM 1 - Стенд",
                                 3 * SCREEN_WIDTH // 4, 80, arcade.color.ORANGE, 14, anchor_x="center")

            if self.player1:
                self.draw_attack_hitbox(self.player1, arcade.color.RED)
            if self.player2:
                self.draw_attack_hitbox(self.player2, arcade.color.BLUE)

        arcade.draw_text("ESC - меню", SCREEN_WIDTH - 120, 30, arcade.color.GRAY, 14)

    def draw_attack_hitbox(self, character, color):
        """Метод для отрисовки хитбоксов (только для тестового режима)"""
        if hasattr(character, '_custom_hitbox') and character._custom_hitbox:
            hit_width, hit_height = character._custom_hitbox
        elif hasattr(character, 'hitbox_size'):
            hit_width, hit_height = character.hitbox_size
        else:
            hit_width, hit_height = 60, 120

        char_left = character.center_x - hit_width // 2
        char_right = character.center_x + hit_width // 2
        char_bottom = character.center_y - hit_height // 2
        char_top = character.center_y + hit_height // 2

        arcade.draw_lrbt_rectangle_outline(
            char_left, char_right, char_bottom, char_top,
            arcade.color.GREEN, 3
        )
        arcade.draw_lrbt_rectangle_filled(
            char_left, char_right, char_bottom, char_top,
            (0, 255, 0, 30)
        )

        sprite_left = character.center_x - character.width // 2
        sprite_right = character.center_x + character.width // 2
        sprite_bottom = character.center_y - character.height // 2
        sprite_top = character.center_y + character.height // 2

        arcade.draw_lrbt_rectangle_outline(
            sprite_left, sprite_right, sprite_bottom, sprite_top,
            arcade.color.YELLOW, 1
        )

        arcade.draw_circle_filled(character.center_x, character.center_y, 5, arcade.color.WHITE)

        if character.stand_active and character.stand and character.stand.is_attacking:
            attack_data = get_attack_data(character.character_name, f"stand_attack{character.stand.current_combo}")
            if attack_data:
                hitbox_width, hitbox_height = attack_data.get("hitbox", (80, 100))
                offset_x = attack_data.get("offset_x", 80)
                offset_y = attack_data.get("offset_y", 0)

                if character.facing_right:
                    hitbox_left = character.center_x + offset_x - hitbox_width // 2
                else:
                    hitbox_left = character.center_x - offset_x - hitbox_width // 2

                hitbox_right = hitbox_left + hitbox_width
                hitbox_center_y = character.center_y + offset_y
                hitbox_bottom = hitbox_center_y - hitbox_height // 2
                hitbox_top = hitbox_center_y + hitbox_height // 2

                arcade.draw_lrbt_rectangle_outline(
                    hitbox_left, hitbox_right, hitbox_bottom, hitbox_top,
                    arcade.color.PURPLE, 3
                )
                arcade.draw_lrbt_rectangle_filled(
                    hitbox_left, hitbox_right, hitbox_bottom, hitbox_top,
                    (128, 0, 128, 30)
                )

        elif character.is_attacking and "stand" not in character.current_action:
            attack_data = get_attack_data(character.character_name, character.current_action)
            if attack_data:
                hitbox_width, hitbox_height = attack_data.get("hitbox", (50, 50))
                offset_x = attack_data.get("offset_x", 50)
                offset_y = attack_data.get("offset_y", 0)

                if character.facing_right:
                    hitbox_left = character.center_x + offset_x - hitbox_width // 2
                else:
                    hitbox_left = character.center_x - offset_x - hitbox_width // 2

                hitbox_right = hitbox_left + hitbox_width
                hitbox_center_y = character.center_y + offset_y
                hitbox_bottom = hitbox_center_y - hitbox_height // 2
                hitbox_top = hitbox_center_y + hitbox_height // 2

                arcade.draw_lrbt_rectangle_outline(
                    hitbox_left, hitbox_right, hitbox_bottom, hitbox_top,
                    color, 3
                )
                arcade.draw_lrbt_rectangle_filled(
                    hitbox_left, hitbox_right, hitbox_bottom, hitbox_top,
                    (color[0], color[1], color[2], 30)
                )

    def on_update(self, delta_time):
        if not self.player1 or not self.player2:
            return

        if self.intro_mode:
            self.intro_timer += 1
            self.player1.update()
            self.player2.update()

            if self.intro_timer >= INTRO_ANIMATION_DURATION:
                self.intro_mode = False
                self.intro_timer = 0
                self.player1.set_action("idle")
                self.player2.set_action("idle")
            return

        if self.victory_mode:
            self.victory_timer += 1

            if self.winner:
                self.winner.update()
            if self.loser:
                self.loser.update()

            if self.victory_timer >= VICTORY_ANIMATION_DURATION:
                winner_text = f"ИГРОК {1 if self.winner == self.player1 else 2} ПОБЕДИЛ!"
                game_over_view = GameOverView(winner_text)
                self.window.show_view(game_over_view)
            return

        if self.player1.current_health <= 0:
            self.show_game_over("ИГРОК 2 ПОБЕДИЛ!")
            return
        if self.player2.current_health <= 0:
            self.show_game_over("ИГРОК 1 ПОБЕДИЛ!")
            return

        # ИГРОК 1 (WASD + J/I/L)
        if not self.player1.is_summoning and not self.player1.is_hit:
            if not self.player1.is_dashing and not self.player1.is_attacking:
                self.player1.change_x = 0

                if not self.player1.is_crouching:
                    if self.p1_left:
                        self.player1.change_x = -self.player1.movement_speed
                        if not self.player1.is_jumping:
                            action = self.player1.get_action_for_movement(True, False)
                            if action:
                                self.player1.set_action(action)

                    if self.p1_right:
                        self.player1.change_x = self.player1.movement_speed
                        if not self.player1.is_jumping:
                            action = self.player1.get_action_for_movement(False, True)
                            if action:
                                self.player1.set_action(action)

                if (not self.p1_left and not self.p1_right and
                        not self.player1.is_jumping and
                        not self.player1.is_attacking and
                        self.player1.current_action not in ["crouch"]):
                    self.player1.set_action("idle")

            if self.p1_up and not self.p1_w_was_pressed:
                if not self.player1.is_crouching and not self.player1.is_dashing and not self.player1.is_attacking:
                    self.player1.jump()
                self.p1_w_was_pressed = True

            if self.p1_down and not self.p1_s_was_pressed:
                self.player1.crouch(True)
                self.p1_s_was_pressed = True

            if not self.p1_down and self.p1_s_was_pressed:
                self.player1.crouch(False)
                self.p1_s_was_pressed = False

            if self.p1_shift_was_pressed and not self.player1.is_dashing and self.player1.dash_cooldown == 0:
                if self.p1_left:
                    self.player1.dash(-1)
                elif self.p1_right:
                    self.player1.dash(1)
                else:
                    self.player1.dash()

            # Обработка трех разных атак для P1
            if self.p1_attack1_pressed:
                self.player1.attack1()
            if self.p1_attack2_pressed:
                self.player1.attack2()
            if self.p1_attack3_pressed:
                self.player1.attack3()

            if self.p1_stand_pressed and not self.player1.is_summoning and not self.player1.is_attacking:
                self.player1.toggle_stand()
                self.p1_stand_pressed = False
        else:
            self.player1.change_x = 0

        # ИГРОК 2 (клавиатура стрелки + геймпад)
        if not self.player2.is_summoning and not self.player2.is_hit:
            if not self.player2.is_dashing and not self.player2.is_attacking:
                self.player2.change_x = 0

                if not self.player2.is_crouching:
                    if self.p2_left:
                        self.player2.change_x = -self.player2.movement_speed
                        if not self.player2.is_jumping:
                            action = self.player2.get_action_for_movement(True, False)
                            if action:
                                self.player2.set_action(action)

                    if self.p2_right:
                        self.player2.change_x = self.player2.movement_speed
                        if not self.player2.is_jumping:
                            action = self.player2.get_action_for_movement(False, True)
                            if action:
                                self.player2.set_action(action)

                if (not self.p2_left and not self.p2_right and
                        not self.player2.is_jumping and
                        not self.player2.is_attacking and
                        self.player2.current_action not in ["crouch"]):
                    self.player2.set_action("idle")

            # Обработка прыжка (с учетом геймпада и клавиатуры)
            if (self.p2_up or self.p2_up_was_pressed) and not self.p2_up_was_pressed:
                if not self.player2.is_crouching and not self.player2.is_dashing and not self.player2.is_attacking:
                    self.player2.jump()
                self.p2_up_was_pressed = True

            # Обработка приседания (с учетом геймпада и клавиатуры)
            if (self.p2_down or self.p2_down_was_pressed) and not self.p2_down_was_pressed:
                self.player2.crouch(True)
                self.p2_down_was_pressed = True

            if not self.p2_down and self.p2_down_was_pressed and not (
                    self.controller and abs(self.controller.lefty) > 0.1):
                self.player2.crouch(False)
                self.p2_down_was_pressed = False

            # Рывок
            if self.p2_shift_was_pressed and not self.player2.is_dashing and self.player2.dash_cooldown == 0:
                if self.p2_left:
                    self.player2.dash(-1)
                elif self.p2_right:
                    self.player2.dash(1)
                else:
                    self.player2.dash()

            # Обработка трех разных атак для P2 (флаги устанавливаются геймпадом)
            if self.p2_attack1_pressed:
                self.player2.attack1()
            if self.p2_attack2_pressed:
                self.player2.attack2()
            if self.p2_attack3_pressed:
                self.player2.attack3()

            # Стенд для P2
            if self.p2_stand_pressed and not self.player2.is_summoning and not self.player2.is_attacking:
                self.player2.toggle_stand()
                self.p2_stand_pressed = False
        else:
            self.player2.change_x = 0

        if self.physics1 and self.physics2:
            self.physics1.update()
            self.physics2.update()

        if self.player1:
            self.player1.update()
            if self.player1.stand_active and self.player1.stand:
                self.player1.stand.update()

        if self.player2:
            self.player2.update()
            if self.player2.stand_active and self.player2.stand:
                self.player2.stand.update()

    def show_game_over(self, message):
        if "ИГРОК 1" in message:
            self.winner = self.player1
            self.loser = self.player2
        else:
            self.winner = self.player2
            self.loser = self.player1

        self.victory_mode = True
        self.victory_timer = 0

        # Запускаем анимации победы и поражения
        if "victory" in self.winner.frame_ranges:
            self.winner.set_action("victory")
        else:
            self.winner.set_action("idle")

        if "defeat" in self.loser.frame_ranges:
            self.loser.set_action("defeat")
        else:
            self.loser.set_action("crouch")

        # Убираем стенды для чистоты
        if self.winner.stand_active:
            self.winner.stand_active = False
            self.winner.stand = None
            self.winner.stand_sprite_list.clear()
        if self.loser.stand_active:
            self.loser.stand_active = False
            self.loser.stand = None
            self.loser.stand_sprite_list.clear()

        if self.winner.center_x < self.loser.center_x:
            self.winner.facing_right = True
            self.loser.facing_right = False
        else:
            self.winner.facing_right = False
            self.loser.facing_right = True

        print(f"Анимация победы: {self.winner.character_name} - victory, {self.loser.character_name} - defeat")

    def on_key_press(self, key, modifiers):
        if self.intro_mode or self.victory_mode:
            return

        # Игрок 1 (WASD + J/I/L)
        if key == arcade.key.A:
            self.p1_left = True
        elif key == arcade.key.D:
            self.p1_right = True
        elif key == arcade.key.W:
            self.p1_up = True
        elif key == arcade.key.S:
            self.p1_down = True
        elif key == arcade.key.J:  # Атака 1
            self.p1_attack1_pressed = True
        elif key == arcade.key.I:  # Атака 2
            self.p1_attack2_pressed = True
        elif key == arcade.key.L:  # Атака 3
            self.p1_attack3_pressed = True
        elif key == arcade.key.K:  # Стенд
            if self.player1:
                self.p1_stand_pressed = True
        elif key == arcade.key.LSHIFT or key == arcade.key.RSHIFT:
            self.p1_shift_was_pressed = True

        # Игрок 2 (стрелки + пробел/1)
        elif key == arcade.key.LEFT:
            self.p2_left = True
        elif key == arcade.key.RIGHT:
            self.p2_right = True
        elif key == arcade.key.UP:
            self.p2_up = True
        elif key == arcade.key.DOWN:
            self.p2_down = True
        elif key == arcade.key.SPACE:
            if self.player2 and not self.p2_attack_pressed:
                self.player2.attack()
                self.p2_attack_pressed = True
        elif key == arcade.key.NUM_1:
            if self.player2:
                self.p2_stand_pressed = True
        elif key == arcade.key.RCTRL:
            self.p2_shift_was_pressed = True

        elif key == arcade.key.ESCAPE:
            self.window.show_view(ModeMenuView())

    def on_key_release(self, key, modifiers):
        if self.intro_mode or self.victory_mode:
            return

        # Игрок 1
        if key == arcade.key.A:
            self.p1_left = False
        elif key == arcade.key.D:
            self.p1_right = False
        elif key == arcade.key.W:
            self.p1_up = False
            self.p1_w_was_pressed = False
        elif key == arcade.key.S:
            self.p1_down = False
        elif key == arcade.key.J:  # Атака 1
            self.p1_attack1_pressed = False
        elif key == arcade.key.I:  # Атака 2
            self.p1_attack2_pressed = False
        elif key == arcade.key.L:  # Атака 3
            self.p1_attack3_pressed = False
        elif key == arcade.key.K:  # Стенд
            self.p1_stand_pressed = False
        elif key == arcade.key.LSHIFT or key == arcade.key.RSHIFT:
            self.p1_shift_was_pressed = False

        # Игрок 2
        elif key == arcade.key.LEFT:
            self.p2_left = False
        elif key == arcade.key.RIGHT:
            self.p2_right = False
        elif key == arcade.key.UP:
            self.p2_up = False
            self.p2_up_was_pressed = False
        elif key == arcade.key.DOWN:
            self.p2_down = False
        elif key == arcade.key.SPACE:
            self.p2_attack_pressed = False
        elif key == arcade.key.NUM_1:
            self.p2_stand_pressed = False
        elif key == arcade.key.RCTRL:
            self.p2_shift_was_pressed = False


class GameOverView(arcade.View):
    def __init__(self, message):
        super().__init__()
        self.message = message
        print(f"GameOverView: {message}")

    def on_draw(self):
        self.clear()
        arcade.set_background_color(arcade.color.BLACK)

        arcade.draw_text(self.message,
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50,
                         arcade.color.WHITE, 48, anchor_x="center")
        arcade.draw_text("Нажмите ESC для выхода в меню",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50,
                         arcade.color.GRAY, 24, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            print("GameOver: ESC pressed")
            self.window.show_view(ModeMenuView())


def main():
    print("=" * 50)
    print("ЗАПУСК ИГРЫ")
    print("=" * 50)

    # Инициализируем базу данных
    db = Database()
    print("База данных инициализирована")

    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = StartView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()