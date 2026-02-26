import arcade
import random
import requests
import socket
import threading
from pathlib import Path
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


LOBBY_SERVER_URL = "http://127.0.0.1:5000"


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

        self.frame_ranges = self.stand_data["frame_ranges"]
        self.animation_speeds = self.stand_data["animation_speeds"]
        self.jump_loop = self.stand_data.get("jump_loop", None)

        # Масштаб и позиция
        self.scale = self.stand_data["sprite_scale"]

        # Загрузка текстур
        self.all_textures = [{}, {}]
        self.load_all_textures()

        # Состояние анимации
        self.current_direction = owner.current_direction
        self.current_action = "summon"
        self.current_frame = self.frame_ranges["summon"][0]
        self.frame_counter = 0
        self.is_summoning = True

        # Для атак
        self.is_attacking = False
        self.current_combo = 0
        self.attack_timer = 0
        self.has_hit_in_this_attack = False
        self.attack_duration = 0  # Длительность атаки в кадрах

        # Устанавливаем первый кадр
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
        """Начать атаку стенда"""
        self.current_combo = combo_number
        self.is_attacking = True
        self.has_hit_in_this_attack = False
        attack_name = f"attack{combo_number}"

        if attack_name in self.frame_ranges:
            self.set_action(attack_name)
            # Вычисляем длительность атаки
            start_frame, end_frame = self.frame_ranges[attack_name]
            frame_count = end_frame - start_frame + 1
            anim_speed = self.animation_speeds.get(attack_name, 5)
            self.attack_duration = frame_count * anim_speed
            self.attack_timer = self.attack_duration

            print(f"Стенд атакует! Длительность: {self.attack_duration} кадров")

    def check_attack_hit(self, opponent):
        """Проверка попадания атаки стенда"""
        if not self.is_attacking or self.has_hit_in_this_attack or not opponent:
            return False

        # Формируем имя атаки для получения данных
        stand_attack_name = f"stand_attack{self.current_combo}"

        print(f"Проверка атаки стенда: {stand_attack_name}, кадр {self.current_frame}, комбо {self.current_combo}")

        # Получаем данные атаки из персонажа
        attack_data = get_attack_data(self.owner.character_name, stand_attack_name)
        if not attack_data:
            print(f"Нет данных для атаки стенда {stand_attack_name}")
            # Пробуем получить данные для обычной атаки как запасной вариант
            attack_data = get_attack_data(self.owner.character_name, f"attack{self.current_combo}")
            if not attack_data:
                return False

        # Проверяем активные кадры
        active_frames = attack_data.get("active_frames", (0, 0))
        print(f"Активные кадры: {active_frames}, текущий: {self.current_frame}")

        if self.current_frame < active_frames[0] or self.current_frame > active_frames[1]:
            return False

        # Проверяем неуязвимость противника
        if opponent.hit_cooldown > 0:
            print("Противник неуязвим")
            return False

        # Хитбокс стенда
        hitbox_width, hitbox_height = attack_data.get("hitbox", (80, 100))

        # Позиция хитбокса (впереди владельца)
        if self.owner.facing_right:
            hitbox_left = self.owner.center_x + 80 - hitbox_width // 2
        else:
            hitbox_left = self.owner.center_x - 80 - hitbox_width // 2

        hitbox_right = hitbox_left + hitbox_width
        hitbox_bottom = self.owner.center_y - hitbox_height // 2
        hitbox_top = hitbox_bottom + hitbox_height

        # Хитбокс противника
        opponent_left = opponent.center_x - opponent.width // 2
        opponent_right = opponent.center_x + opponent.width // 2
        opponent_bottom = opponent.center_y - opponent.height // 2
        opponent_top = opponent.center_y + opponent.height // 2

        print(f"Хитбокс стенда: L={hitbox_left:.0f}, R={hitbox_right:.0f}, B={hitbox_bottom:.0f}, T={hitbox_top:.0f}")
        print(
            f"Хитбокс противника: L={opponent_left:.0f}, R={opponent_right:.0f}, B={opponent_bottom:.0f}, T={opponent_top:.0f}")

        # Проверка пересечения
        if (hitbox_right > opponent_left and hitbox_left < opponent_right and
                hitbox_top > opponent_bottom and hitbox_bottom < opponent_top):
            self.has_hit_in_this_attack = True

            damage = attack_data.get("damage", 15)
            knockback = attack_data.get("knockback", 10)
            knockback_dir = 1 if self.owner.facing_right else -1

            opponent.take_damage(damage, knockback * knockback_dir)

            # Отмечаем попадание у владельца для комбо
            self.owner.attack_hit = True

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
                        # Атака закончена - возвращаемся в idle
                        self.is_attacking = False
                        self.set_action("idle")
                    else:
                        self.current_frame = start_frame

            texture = self.get_current_texture(self.current_frame)
            if texture:
                self.texture = texture

    def update(self):
        # Обновление таймера атаки
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer <= 0:
                self.is_attacking = False

        # Позиция относительно владельца
        dir_mult = 1 if self.owner.facing_right else -1
        self.center_x = self.owner.center_x - (self.stand_data["offset_x"] * dir_mult)
        self.center_y = self.owner.center_y + self.stand_data["offset_y"]
        self.current_direction = self.owner.current_direction

        # Проверка попадания атаки
        if self.is_attacking and self.owner.opponent:
            self.check_attack_hit(self.owner.opponent)

        # Если стенд не в процессе призыва и не атакует, синхронизируем базовые движения
        if not self.is_summoning and not self.is_attacking:
            owner_action = self.owner.current_action

            if owner_action in ["idle", "move_right", "move_left", "jump", "crouch", "dash_forward", "dash_backward"]:
                if owner_action == "move_right":
                    stand_action = "move_forward" if self.owner.facing_right else "move_backward"
                elif owner_action == "move_left":
                    stand_action = "move_forward" if not self.owner.facing_right else "move_backward"
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
        super().__init__()

        if not character_exists(character_name):
            raise ValueError(f"Персонаж {character_name} не найден!")

        self.character_data = get_character_data(character_name)
        self.character_name = character_name
        self.file_prefix = self.character_data["file_prefix"]
        self.player_number = player_number
        self.opponent = opponent

        # Характеристики
        self.max_health = self.character_data.get("health", 100)
        self.current_health = self.max_health

        self.movement_speed = self.character_data.get("movement_speed", 3)
        self.jump_speed = self.character_data.get("jump_speed", 15)
        self.base_animation_speed = self.character_data.get("animation_speed", 5)
        self.animation_speeds = self.character_data.get("animation_speeds", {})
        self.crouch_freeze_frame = self.character_data.get("crouch_freeze_frame", None)
        self.sprite_scale = self.character_data.get("sprite_scale", 0.5)

        # Получаем кадры для зацикливания прыжка
        self.jump_loop = self.character_data.get("jump_loop", None)

        # Данные атак
        self.attacks_data = self.character_data.get("attacks", {})
        self.combo_window = self.character_data.get("combo_window", 30)

        # Система комбо
        self.combo_counter = 0
        self.combo_timer = 0
        self.attack_hit = False
        self.can_attack = True
        self.attack_cooldown = 0
        self.is_attacking = False
        self.has_hit_in_this_attack = False

        # Система получения урона
        self.hit_cooldown = 0
        self.is_hit = False
        self.knockback_velocity = 0
        self.knockback_timer = 0

        # Рывок
        self.dash_speed = self.character_data.get("dash_speed", 8)
        self.dash_distance = self.character_data.get("dash_distance", 100)
        self.dash_cooldown_max = self.character_data.get("dash_cooldown", 45)
        self.dash_cooldown = 0
        self.is_dashing = False
        self.dash_direction = 0
        self.dash_target_x = None
        self.dash_start_x = None

        # Стенд
        self.stand = None
        self.stand_active = False
        self.is_summoning = False
        self.double_jump_used = False
        self.stand_sprite_list = arcade.SpriteList()

        # Анимация
        self.frame_ranges = self.character_data["frame_ranges"]
        self.all_textures = [{}, {}]
        self.load_all_textures()
        self.scale = self.sprite_scale

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

        self.change_x = 0
        self.change_y = 0

        print(f"ИГРОК {player_number}: {character_name} создан")
        print(f"  Здоровье: {self.current_health}/{self.max_health}")
        print(f"  Позиция: ({self.center_x}, {self.center_y})")

    def get_action_animation_speed(self, action):
        if action in self.animation_speeds:
            return self.animation_speeds[action]
        return self.base_animation_speed

    def set_opponent(self, opponent):
        self.opponent = opponent

    def update_facing_direction(self):
        if self.opponent and not self.is_attacking and not self.is_dashing:
            if self.opponent.center_x > self.center_x:
                self.facing_right = True
                self.current_direction = 0
            else:
                self.facing_right = False
                self.current_direction = 1

    def load_all_textures(self):
        character_path = Path("Спрайты") / self.character_name
        max_frame = 0
        for start, end in self.frame_ranges.values():
            max_frame = max(max_frame, end)

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

        if 0 in self.all_textures[0] and self.all_textures[0][0]:
            self.texture = self.all_textures[0][0]

    def get_current_texture(self, frame_number):
        if frame_number in self.all_textures[self.current_direction] and self.all_textures[self.current_direction][
            frame_number]:
            return self.all_textures[self.current_direction][frame_number]
        other_direction = 1 - self.current_direction
        if frame_number in self.all_textures[other_direction] and self.all_textures[other_direction][frame_number]:
            return self.all_textures[other_direction][frame_number]
        return None

    def get_action_for_movement(self, moving_left, moving_right):
        if self.facing_right:
            if moving_left:
                return "move_left"
            elif moving_right:
                return "move_right"
        else:
            if moving_left:
                return "move_right"
            elif moving_right:
                return "move_left"
        return None

    def jump(self):
        if self.is_summoning or self.is_attacking:
            return False

        if not self.is_jumping and not self.is_crouching and not self.is_dashing and self.center_y <= GROUND_LEVEL:
            self.change_y = self.jump_speed
            self.is_jumping = True
            self.double_jump_used = False
            self.set_action("jump")
            return True

        elif self.stand_active and self.is_jumping and not self.double_jump_used and not self.is_dashing:
            self.change_y = self.jump_speed
            self.double_jump_used = True
            if "jump" in self.frame_ranges:
                self.current_frame = self.frame_ranges["jump"][0]
            return True

        return False

    def crouch(self, start_crouch=True):
        if "crouch" not in self.frame_ranges or self.is_dashing or self.is_summoning or self.is_attacking:
            return

        start_frame, end_frame = self.frame_ranges["crouch"]

        if start_crouch:
            if not self.is_jumping and not self.is_crouching and not self.is_dashing:
                self.is_crouching = True
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

    def dash(self, move_direction=None):
        if self.is_dashing or self.is_jumping or self.is_crouching or self.dash_cooldown > 0 or self.is_summoning or self.is_attacking:
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
        return True

    def toggle_stand(self):
        """Переключение состояния стенда"""
        # Убираем лишние проверки, оставляем только самые необходимые
        if self.is_jumping or self.is_dashing:
            return

        # Если персонаж в атаке, но это стойка, можно призвать стенд
        if self.is_attacking and "stand_attack" not in self.current_action:
            return

        if self.stand_active:
            # Убираем стенд
            self.stand_active = False
            self.stand = None
            self.stand_sprite_list.clear()
            print(f"Игрок {self.player_number} убрал стенд")
        else:
            # Призываем стенд мгновенно
            self.stand_active = True
            self.is_summoning = True

            # НЕМЕДЛЕННО переключаем анимацию на призыв
            self.set_action("stand_summon")

            # Создаем стенд
            self.stand = Stand(self)
            self.stand_sprite_list.append(self.stand)

            print(f"Игрок {self.player_number} призывает стенд")

    def attack(self):
        """Основной метод атаки"""
        if not self.can_attack or self.is_summoning or self.is_dashing or self.is_jumping:
            return False

        # Определяем тип атаки
        if self.stand_active:
            attack_prefix = "stand_attack"  # Владелец встает в стойку
        else:
            attack_prefix = "attack"  # Владелец атакует сам

        # Логика комбо
        if self.combo_timer <= 0 or not self.is_attacking:
            self.combo_counter = 1
        else:
            if self.attack_hit and self.combo_counter < 3:
                self.combo_counter += 1

        attack_name = f"{attack_prefix}{self.combo_counter}"

        # Проверяем существование атаки
        if attack_name not in self.frame_ranges:
            return False

        # Сбрасываем флаги
        self.attack_hit = False
        self.is_attacking = True
        self.can_attack = False
        self.attack_cooldown = ATTACK_COOLDOWN
        self.has_hit_in_this_attack = False

        # Запускаем анимацию владельца
        self.set_action(attack_name)
        self.combo_timer = self.combo_window

        # Если стенд активен, говорим ему начать атаку
        if self.stand_active and self.stand:
            self.stand.start_attack(self.combo_counter)

        return True

    def check_attack_hit(self):
        """Проверка попадания атаки (для обычных атак без стенда)"""
        if not self.is_attacking or self.has_hit_in_this_attack or not self.opponent:
            return False

        # Проверяем, что это обычная атака (не стенд)
        if "stand_" in self.current_action:
            return False

        print(f"Проверка обычной атаки: {self.current_action}, кадр {self.current_frame}")

        # Получаем данные атаки
        attack_data = get_attack_data(self.character_name, self.current_action)
        if not attack_data:
            print(f"Нет данных для атаки {self.current_action}")
            return False

        # Проверяем активные кадры
        active_frames = attack_data.get("active_frames", (0, 0))
        print(f"Активные кадры: {active_frames}, текущий: {self.current_frame}")

        if self.current_frame < active_frames[0] or self.current_frame > active_frames[1]:
            return False

        # Проверяем неуязвимость противника
        if self.opponent.hit_cooldown > 0:
            return False

        # Хитбокс атаки
        hitbox_width, hitbox_height = attack_data.get("hitbox", (50, 50))
        offset_x = attack_data.get("offset_x", 50)

        if self.facing_right:
            hitbox_left = self.center_x + offset_x - hitbox_width // 2
        else:
            hitbox_left = self.center_x - offset_x - hitbox_width // 2

        hitbox_right = hitbox_left + hitbox_width
        hitbox_bottom = self.center_y - hitbox_height // 2
        hitbox_top = hitbox_bottom + hitbox_height

        # Хитбокс противника
        opponent_left = self.opponent.center_x - self.opponent.width // 2
        opponent_right = self.opponent.center_x + self.opponent.width // 2
        opponent_bottom = self.opponent.center_y - self.opponent.height // 2
        opponent_top = self.opponent.center_y + self.opponent.height // 2

        print(f"Хитбокс атаки: L={hitbox_left:.0f}, R={hitbox_right:.0f}, B={hitbox_bottom:.0f}, T={hitbox_top:.0f}")
        print(
            f"Хитбокс противника: L={opponent_left:.0f}, R={opponent_right:.0f}, B={opponent_bottom:.0f}, T={opponent_top:.0f}")

        # Проверка пересечения
        if (hitbox_right > opponent_left and hitbox_left < opponent_right and
                hitbox_top > opponent_bottom and hitbox_bottom < opponent_top):
            self.attack_hit = True
            self.has_hit_in_this_attack = True

            damage = attack_data.get("damage", 10)
            knockback = attack_data.get("knockback", 5)
            knockback_dir = 1 if self.facing_right else -1

            self.opponent.take_damage(damage, knockback * knockback_dir)
            print(f"Обычная атака ПОПАЛА! Урон: {damage}")
            return True

        return False

    def take_damage(self, damage, knockback_force):
        if self.hit_cooldown > 0:
            return

        self.current_health -= damage
        if self.current_health < 0:
            self.current_health = 0

        self.hit_cooldown = HIT_COOLDOWN
        self.is_hit = True
        self.knockback_velocity = knockback_force
        self.knockback_timer = KNOCKBACK_DURATION

        self.is_attacking = False
        self.is_dashing = False
        self.combo_timer = 0

    def draw_stand(self):
        if self.stand_active and self.stand:
            self.stand_sprite_list.draw()

    def draw_health_bar(self):
        """Отрисовка полоски здоровья в верхней части экрана"""
        if self.player_number == 1:
            x = SCREEN_WIDTH // 4
        else:
            x = 3 * SCREEN_WIDTH // 4

        y = SCREEN_HEIGHT - 50
        width = 300
        height = 30

        # Фон
        left = x - width // 2
        bottom = y - height // 2
        arcade.draw_lbwh_rectangle_filled(left, bottom, width, height, arcade.color.DARK_RED)

        # Здоровье
        if self.current_health > 0:
            health_width = (self.current_health / self.max_health) * (width - 4)
            left = x - width // 2 + 2
            bottom = y - height // 2 + 2
            arcade.draw_lbwh_rectangle_filled(left, bottom, health_width, height - 4, arcade.color.GREEN)

        # Текст
        arcade.draw_text(f"{int(self.current_health)}/{self.max_health}",
                         x, y - height - 5,
                         arcade.color.WHITE, 14, anchor_x="center")

        # Имя персонажа
        arcade.draw_text(f"{self.character_data['display_name']}",
                         x, y + height // 2 + 5,
                         arcade.color.WHITE, 16, anchor_x="center", bold=True)

        # Индикатор стенда
        if self.stand_active:
            arcade.draw_text("STAND", x, y - height - 25,
                             arcade.color.YELLOW, 12, anchor_x="center")

    def set_action(self, new_action):
        if new_action == self.current_action:
            return

        # Упрощаем проверки для более быстрого переключения
        if self.is_summoning and new_action not in ["stand_summon", "idle"]:
            # Если мы в процессе призыва, разрешаем только idle после окончания
            if new_action != "stand_summon":
                return

        if self.is_jumping and new_action not in ["jump", "idle"]:
            return

        if self.is_dashing and new_action not in ["dash_forward", "dash_backward", "idle"]:
            return

        if new_action in self.frame_ranges:
            # Немедленно меняем действие и сбрасываем кадр
            self.current_action = new_action
            self.current_frame = self.frame_ranges[new_action][0]
            self.frame_counter = 0
            self.current_animation_speed = self.get_action_animation_speed(new_action)

            # Обновляем текстуру сразу же
            texture = self.get_current_texture(self.current_frame)
            if texture:
                self.texture = texture

            # Для анимации стойки запоминаем диапазон кадров
            if "stand_attack" in new_action:
                self.stand_pose_start, self.stand_pose_end = self.frame_ranges[new_action]

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

            elif self.current_action == "stand_summon":
                self.current_frame += 1
                if self.current_frame > end_frame:
                    self.current_frame = end_frame
                    self.is_summoning = False
                    self.set_action("idle")

            elif self.current_action == "crouch":
                if self.is_crouching:
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

            elif "stand_attack" in self.current_action:
                # Анимация стойки - зацикливаем на двух кадрах
                self.current_frame += 1
                if self.current_frame > end_frame:
                    # Возвращаемся на первый кадр стойки
                    self.current_frame = start_frame

                # Если стенд больше не атакует, выходим из стойки
                if self.stand_active and self.stand and not self.stand.is_attacking:
                    self.is_attacking = False
                    self.set_action("idle")

            elif "attack" in self.current_action and "stand" not in self.current_action:
                # Обычная атака (без стенда)
                self.current_frame += 1
                if self.current_frame > end_frame:
                    self.is_attacking = False
                    self.set_action("idle")

            else:
                self.current_frame += 1
                if self.current_frame > end_frame:
                    self.current_frame = start_frame

            texture = self.get_current_texture(self.current_frame)
            if texture:
                self.texture = texture

    def update(self):
        # Обновление таймеров
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1
        else:
            self.is_hit = False

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        else:
            self.can_attack = True

        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo_counter = 0

        if self.knockback_timer > 0:
            self.knockback_timer -= 1
            self.center_x += self.knockback_velocity
            self.knockback_velocity *= 0.8

        # Проверка попадания атаки
        if self.is_attacking and not self.stand_active and "attack" in self.current_action and "stand" not in self.current_action:
            self.check_attack_hit()

        # Обновляем направление взгляда
        self.update_facing_direction()

        # Движение
        self.center_x += self.change_x

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

        # Границы
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

        # Настройка фона
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

        # D'Arby
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

        # Боковые рамки
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

        # Состояния
        self.anim_state = "intro"
        self.selected_index = 0
        self.current_frame = 0
        self.ram_anim_frame = 0
        self.timer = 0.0
        self.ram_timer = 0.0

        self.modes = ["ТЕСТОВЫЙ РЕЖИМ", "ОНЛАЙН"]

    def on_update(self, delta_time):
        # Движение фона
        for s in self.bg_sprite_list:
            s.center_y -= 3.0
            if s.top < 0:
                s.center_y += 8 * self.tile_h

        # Анимация D'Arby
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
                    print("Переход по выбору режима")
                    # Проверяем, какой режим был выбран
                    if self.selected_index == 0:
                        print("Переход к выбору персонажа для тестового режима")
                        self.window.show_view(TestCharacterSelectView())
                    else:  # selected_index == 1
                        print("Переход в онлайн меню")
                        self.window.show_view(OnlineMenuView())

                if self.current_frame < len(self.darby_textures):
                    self.darby_sprite.texture = self.darby_textures[self.current_frame]

        # Анимация боковых рамок
        self.ram_timer += delta_time
        if self.ram_timer >= 0.05:
            self.ram_timer = 0.0
            self.ram_anim_frame = (self.ram_anim_frame + 1) % 5

        if self.ram_textures:
            if self.selected_index == 0:
                self.left_ram.texture = self.ram_textures[self.ram_anim_frame]
                self.right_ram.texture = self.ram_textures[0]
            else:
                self.right_ram.texture = self.ram_textures[self.ram_anim_frame]
                self.left_ram.texture = self.ram_textures[0]

    def on_draw(self):
        self.clear()
        self.bg_sprite_list.draw()
        arcade.draw_rect_filled(arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT), (0, 0, 0, 160))

        self.ui_sprite_list.draw()
        self.side_rams_list.draw()
        self.header_text.draw()

        # Текст на иконках
        l_color = MENU_SELECTED_COLOR if self.selected_index == 0 else arcade.color.WHITE
        r_color = MENU_SELECTED_COLOR if self.selected_index == 1 else arcade.color.WHITE

        arcade.draw_text(self.modes[0], self.left_ram.center_x, self.left_ram.center_y,
                         l_color, 18, anchor_x="center", anchor_y="center", bold=True)
        arcade.draw_text(self.modes[1], self.right_ram.center_x, self.right_ram.center_y,
                         r_color, 18, anchor_x="center", anchor_y="center", bold=True)

    def on_key_press(self, key, modifiers):
        if self.anim_state != "idle":
            return

        if key in [arcade.key.LEFT, arcade.key.A]:
            self.selected_index = 0
            print("Выбран тестовый режим")
        elif key in [arcade.key.RIGHT, arcade.key.D]:
            self.selected_index = 1
            print("Выбран онлайн режим")
        elif key == arcade.key.ENTER:
            print(f"Запуск режима: {self.modes[self.selected_index]}")
            self.anim_state = "outro"
            self.current_frame = 4  # Начинаем с 4 кадра, где заканчивается intr


class OnlineMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.options = ["Создать комнату", "Подключиться к лобби", "Назад"]
        self.selected_index = 0
        self.status_message = ""

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
        # Отрисовка фона
        self.bg_sprite_list.draw()
        arcade.draw_rect_filled(
            arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
            (0, 0, 0, 180)
        )

        arcade.draw_text("ОНЛАЙН РЕЖИМ", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                         arcade.color.GOLD, 50, anchor_x="center", bold=True)

        for i, option in enumerate(self.options):
            color = MENU_SELECTED_COLOR if i == self.selected_index else MENU_FONT_COLOR
            text = f">> {option} <<" if i == self.selected_index else option
            arcade.draw_text(text, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - (i * 60),
                             color, 30, anchor_x="center")

        if self.status_message:
            arcade.draw_text(self.status_message, SCREEN_WIDTH // 2, 100,
                             arcade.color.WHITE, 18, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.selected_index = (self.selected_index - 1) % len(self.options)
        elif key == arcade.key.DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.options)
        elif key == arcade.key.ENTER:
            self.handle_selection()

    def handle_selection(self):
        if self.selected_index == 0:
            self.create_room_on_server()
        elif self.selected_index == 1:
            self.join_room_from_server()
        elif self.selected_index == 2:
            self.window.show_view(ModeMenuView())

    def create_room_on_server(self):
        """Регистрирует комнату во Flask и открывает сокет для игры"""
        try:
            # 1. Говорим Flask-серверу, что мы создаем комнату
            response = requests.post(f"{LOBBY_SERVER_URL}/create_room",
                                     json={"player_name": "Player 1"})

            if response.status_code == 200:
                self.status_message = "Комната создана во Flask! Ожидание игрока по сокету..."
                # 2. Запускаем ожидание по сокету (как в прошлом примере)
                threading.Thread(target=self._start_socket_server, daemon=True).start()
        except Exception as e:
            self.status_message = f"Ошибка связи с Flask: {e}"

    def join_room_from_server(self):
        """Получает список комнат из Flask и подключается к первой доступной"""
        try:
            self.status_message = "Поиск комнат..."
            response = requests.get(f"{LOBBY_SERVER_URL}/get_rooms")
            rooms = response.json()

            if rooms:
                host_ip = rooms[0]['host_ip']
                self.status_message = f"Подключение к {host_ip}..."
                threading.Thread(target=self._connect_to_socket, args=(host_ip,), daemon=True).start()
            else:
                self.status_message = "Свободных комнат не найдено."
        except Exception as e:
            self.status_message = f"Ошибка поиска: {e}"

    def _start_socket_server(self):
        # Логика сокет-сервера для самого боя
        pass

    def _connect_to_socket(self, ip):
        # Логика подключения сокет-клиента
        pass


class TestCharacterSelectView(arcade.View):
    def __init__(self):
        super().__init__()
        print("TestCharacterSelectView инициализирован")

        # Настройка фона
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
        self.p1_text = arcade.Text("ИГРОК 1 (WASD)", SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150, arcade.color.CYAN, 28,
                                   anchor_x="center")
        self.p2_text = arcade.Text("ИГРОК 2 (Стрелки)", 3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150, arcade.color.ORANGE,
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
                print(f"P1 выбирает: {self.characters[self.p1_selected]}")
            else:
                self.p2_selected = (self.p2_selected - 1) % len(self.characters)
                print(f"P2 выбирает: {self.characters[self.p2_selected]}")
        elif key == arcade.key.DOWN:
            if self.current_player == 1:
                self.p1_selected = (self.p1_selected + 1) % len(self.characters)
                print(f"P1 выбирает: {self.characters[self.p1_selected]}")
            else:
                self.p2_selected = (self.p2_selected + 1) % len(self.characters)
                print(f"P2 выбирает: {self.characters[self.p2_selected]}")
        elif key == arcade.key.ENTER:
            self.current_player = 2 if self.current_player == 1 else 1
            print(f"Текущий игрок: {self.current_player}")
        elif key == arcade.key.SPACE:
            self.current_player = 3 - self.current_player
            print(f"Текущий игрок: {self.current_player}")
        elif key == arcade.key.S:
            p1_char = self.characters[self.p1_selected]
            p2_char = self.characters[self.p2_selected]
            print(f"Запуск игры: P1={p1_char}, P2={p2_char}")
            game_view = TestGameView(p1_char, p2_char)
            self.window.show_view(game_view)
        elif key == arcade.key.ESCAPE:
            print("Возврат в меню режимов")
            self.window.show_view(ModeMenuView())


class TestGameView(arcade.View):
    def __init__(self, p1_character, p2_character):
        super().__init__()

        self.p1_character_name = p1_character
        self.p2_character_name = p2_character
        map_index = random.randint(0, 3)  # Выбираем число от 0 до 3
        map_path = Path("Карта") / f"jojo_map_{map_index}.png"

        self.background = None
        if map_path.exists():
            self.background = arcade.load_texture(str(map_path))
            print(f"Загружена карта: {map_path}")
        else:
            print(f"Ошибка: Файл {map_path} не найден!")

        # Флаги управления P1
        self.p1_left = False
        self.p1_right = False
        self.p1_up = False
        self.p1_down = False
        self.p1_w_was_pressed = False
        self.p1_s_was_pressed = False
        self.p1_shift_was_pressed = False
        self.p1_attack_pressed = False

        # Флаги управления P2
        self.p2_left = False
        self.p2_right = False
        self.p2_up = False
        self.p2_down = False
        self.p2_up_was_pressed = False
        self.p2_down_was_pressed = False
        self.p2_shift_was_pressed = False
        self.p2_attack_pressed = False

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

        self.player1.set_opponent(self.player2)
        self.player2.set_opponent(self.player1)

        self.player1_list = arcade.SpriteList()
        self.player1_list.append(self.player1)
        self.physics1 = arcade.PhysicsEngineSimple(self.player1, None)

        self.player2_list = arcade.SpriteList()
        self.player2_list.append(self.player2)
        self.physics2 = arcade.PhysicsEngineSimple(self.player2, None)

    def on_show(self):
        pass

    def on_draw(self):
        self.clear()

        if self.background:
            # Рисуем карту на весь экран
            arcade.draw_texture_rect(
                self.background,
                arcade.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        else:
            # Если карта не загрузилась, оставляем черный фон
            arcade.set_background_color(arcade.color.BLACK)

        # Рисуем землю
        arcade.draw_line(0, GROUND_LEVEL, SCREEN_WIDTH, GROUND_LEVEL, arcade.color.GREEN, 3)
        arcade.draw_text("Земля", 20, GROUND_LEVEL - 30, arcade.color.GREEN, 14)

        # Отрисовка стендов
        if self.player1:
            self.player1.draw_stand()
        if self.player2:
            self.player2.draw_stand()

        # Отрисовка персонажей
        if self.player1:
            self.player1_list.draw()
        if self.player2:
            self.player2_list.draw()

        # Отрисовка полосок здоровья в верхней части экрана
        if self.player1:
            self.player1.draw_health_bar()
        if self.player2:
            self.player2.draw_health_bar()

        # Информация об игроках (можно убрать или оставить как есть)
        info_y = SCREEN_HEIGHT - 150
        if self.player1 and hasattr(self.player1, 'character_data'):
            arcade.draw_text("ИГРОК 1", SCREEN_WIDTH // 4, info_y, arcade.color.CYAN, 20, anchor_x="center")
            info_y -= 30
            arcade.draw_text(f"Действие: {self.player1.current_action}",
                             SCREEN_WIDTH // 4, info_y, arcade.color.WHITE, 14, anchor_x="center")
            info_y -= 25
            if self.player1.is_attacking:
                combo_info = f"Комбо: {self.player1.combo_counter}/3"
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
                combo_info = f"Комбо: {self.player2.combo_counter}/3"
                if self.player2.attack_hit:
                    combo_info += " (попадание)"
                arcade.draw_text(combo_info, 3 * SCREEN_WIDTH // 4, info_y, arcade.color.YELLOW, 14, anchor_x="center")

        # Управление
        arcade.draw_text("WASD + Shift (рывок) | Q - Стенд | R - Атака",
                         SCREEN_WIDTH // 4, 80, arcade.color.CYAN, 14, anchor_x="center")
        arcade.draw_text("Стрелки + Shift (рывок) | NUM 1 - Стенд | Пробел - Атака",
                         3 * SCREEN_WIDTH // 4, 80, arcade.color.ORANGE, 14, anchor_x="center")

        arcade.draw_text("ESC - меню", SCREEN_WIDTH - 120, 30, arcade.color.GRAY, 14)

    def on_update(self, delta_time):
        if not self.player1 or not self.player2:
            return

        if self.player1.current_health <= 0:
            self.show_game_over("ИГРОК 2 ПОБЕДИЛ!")
            return
        if self.player2.current_health <= 0:
            self.show_game_over("ИГРОК 1 ПОБЕДИЛ!")
            return

        # ИГРОК 1
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
                if not self.player1.is_crouching and self.player1.current_action != "crouch" and not self.player1.is_dashing and not self.player1.is_attacking:
                    self.player1.jump()
                self.p1_w_was_pressed = True

            if self.p1_down and not self.p1_s_was_pressed:
                self.player1.crouch(True)
                self.p1_s_was_pressed = True

            if not self.p1_down and self.p1_s_was_pressed:
                self.player1.crouch(False)
                self.p1_s_was_pressed = False
        else:
            self.player1.change_x = 0

        # ИГРОК 2
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

            if self.p2_up and not self.p2_up_was_pressed:
                if not self.player2.is_crouching and self.player2.current_action != "crouch" and not self.player2.is_dashing and not self.player2.is_attacking:
                    self.player2.jump()
                self.p2_up_was_pressed = True

            if self.p2_down and not self.p2_down_was_pressed:
                self.player2.crouch(True)
                self.p2_down_was_pressed = True

            if not self.p2_down and self.p2_down_was_pressed:
                self.player2.crouch(False)
                self.p2_down_was_pressed = False
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
        game_over_view = GameOverView(message)
        self.window.show_view(game_over_view)

    def on_key_press(self, key, modifiers):
        # Игрок 1
        if key == arcade.key.A:
            self.p1_left = True
        elif key == arcade.key.D:
            self.p1_right = True
        elif key == arcade.key.W:
            self.p1_up = True
        elif key == arcade.key.S:
            self.p1_down = True
        elif key == arcade.key.Q:
            if self.player1:
                self.player1.toggle_stand()
        elif key == arcade.key.LSHIFT or key == arcade.key.RSHIFT:
            self.p1_shift_was_pressed = True
            if self.player1 and not self.player1.is_dashing and self.player1.dash_cooldown == 0 and not self.player1.is_summoning and not self.player1.is_attacking:
                if self.p1_left:
                    self.player1.dash(-1)
                elif self.p1_right:
                    self.player1.dash(1)
                else:
                    self.player1.dash()
        elif key == arcade.key.R:
            if self.player1 and not self.p1_attack_pressed:
                self.player1.attack()
                self.p1_attack_pressed = True

        # Игрок 2
        elif key == arcade.key.LEFT:
            self.p2_left = True
        elif key == arcade.key.RIGHT:
            self.p2_right = True
        elif key == arcade.key.UP:
            self.p2_up = True
        elif key == arcade.key.DOWN:
            self.p2_down = True
        elif key == arcade.key.NUM_1:
            if self.player2:
                self.player2.toggle_stand()
        elif key == arcade.key.RCTRL:
            self.p2_shift_was_pressed = True
            if self.player2 and not self.player2.is_dashing and self.player2.dash_cooldown == 0 and not self.player2.is_summoning and not self.player2.is_attacking:
                if self.p2_left:
                    self.player2.dash(-1)
                elif self.p2_right:
                    self.player2.dash(1)
                else:
                    self.player2.dash()
        elif key == arcade.key.SPACE:
            if self.player2 and not self.p2_attack_pressed:
                self.player2.attack()
                self.p2_attack_pressed = True

        elif key == arcade.key.ESCAPE:
            self.window.show_view(ModeMenuView())

    def on_key_release(self, key, modifiers):
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
        elif key == arcade.key.LSHIFT or key == arcade.key.RSHIFT:
            self.p1_shift_was_pressed = False
        elif key == arcade.key.R:
            self.p1_attack_pressed = False

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
        elif key == arcade.key.RCTRL:
            self.p2_shift_was_pressed = False
        elif key == arcade.key.SPACE:
            self.p2_attack_pressed = False


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

    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = StartView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()