import arcade
from pathlib import Path
from harakteristici import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, GRAVITY, GROUND_LEVEL,
    get_available_characters,
    get_character_info,
    character_exists,
    get_character_data,
    get_crouch_freeze_frame,
    get_sprite_scale,
    get_stand_data
)

# Константы для меню
MENU_FONT_SIZE = 24
MENU_FONT_COLOR = arcade.color.WHITE
MENU_SELECTED_COLOR = arcade.color.YELLOW



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
        self.all_textures = [{}, {}]  # 0 - обычные, 1 - зеркальные
        self.load_all_textures()

        # Состояние анимации
        self.current_direction = owner.current_direction
        self.current_action = "summon"
        self.current_frame = self.frame_ranges["summon"][0]
        self.frame_counter = 0
        self.is_summoning = True

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
                    # Загружаем обычную
                    texture_normal = arcade.load_texture(str(file_path))
                    self.all_textures[0][i] = texture_normal

                    # Делаем зеркальную
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

    def update_animation(self):
        self.frame_counter += 1
        anim_speed = self.animation_speeds.get(self.current_action, 5)

        if self.frame_counter >= anim_speed:
            self.frame_counter = 0
            start_frame, end_frame = self.frame_ranges[self.current_action]

            # Логика анимации прыжка стенда
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
                    else:
                        self.current_frame = start_frame

            texture = self.get_current_texture(self.current_frame)
            if texture:
                self.texture = texture

    def update(self):
        dir_mult = 1 if self.owner.facing_right else -1
        self.center_x = self.owner.center_x - (self.stand_data["offset_x"] * dir_mult)
        self.center_y = self.owner.center_y + self.stand_data["offset_y"]
        self.current_direction = self.owner.current_direction

        if not self.is_summoning:
            mapped_action = "idle"
            owner_action = self.owner.current_action

            if owner_action == "move_right":
                mapped_action = "move_forward" if self.owner.facing_right else "move_backward"
            elif owner_action == "move_left":
                mapped_action = "move_forward" if not self.owner.facing_right else "move_backward"
            elif owner_action in ["jump", "dash_forward", "dash_backward"]:
                mapped_action = owner_action

            self.set_action(mapped_action)

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

        self.movement_speed = self.character_data.get("movement_speed", 3)
        self.jump_speed = self.character_data.get("jump_speed", 15)
        self.base_animation_speed = self.character_data.get("animation_speed", 5)
        self.animation_speeds = self.character_data.get("animation_speeds", {})
        self.crouch_freeze_frame = self.character_data.get("crouch_freeze_frame", None)
        self.sprite_scale = self.character_data.get("sprite_scale", 0.5)

        # Получаем кадры для зацикливания прыжка
        self.jump_loop = self.character_data.get("jump_loop", None)

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
        self.stand_sprite_list = arcade.SpriteList()  # Для безопасной отрисовки стенда

        self.frame_ranges = self.character_data["frame_ranges"]
        self.all_textures = [{}, {}]
        self.load_all_textures()
        self.scale = self.sprite_scale

        self.center_x = start_pos_x
        self.center_y = start_pos_y
        self.facing_right = True
        self.current_direction = 0

        self.current_frame = 0
        self.frame_counter = 0
        self.current_action = "idle"
        self.current_animation_speed = self.get_action_animation_speed("idle")
        self.is_jumping = False
        self.is_crouching = False
        self.crouch_freeze_frame_active = None
        self.crouch_resume_frame = None

        self.change_y = 0

    def get_action_animation_speed(self, action):
        if action in self.animation_speeds:
            return self.animation_speeds[action]
        return self.base_animation_speed

    def set_opponent(self, opponent):
        self.opponent = opponent

    def update_facing_direction(self):
        if self.opponent:
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
                    # 1. Загружаем обычную текстуру
                    texture_normal = arcade.load_texture(str(file_path))
                    self.all_textures[0][i] = texture_normal

                    # 2. Создаем зеркальную копию программно
                    # Этот метод работает во всех версиях Arcade
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
        if self.current_direction == 0:
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
        if self.is_summoning:
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
        if "crouch" not in self.frame_ranges or self.is_dashing or self.is_summoning:
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
        if self.is_dashing or self.is_jumping or self.is_crouching or self.dash_cooldown > 0 or self.is_summoning:
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
        if self.is_jumping or self.is_dashing or self.is_crouching:
            return

        if self.stand_active:
            self.stand_active = False
            self.stand = None
            self.stand_sprite_list.clear()
        else:
            self.stand_active = True
            self.is_summoning = True
            self.set_action("stand_summon")

            self.stand = Stand(self)
            self.stand_sprite_list.append(self.stand)

    def draw_stand(self):
        """Безопасная отрисовка стенда через SpriteList"""
        if self.stand_active and self.stand:
            self.stand_sprite_list.draw()

    def set_action(self, new_action):
        if new_action == self.current_action:
            return

        if self.is_summoning and new_action not in ["stand_summon", "idle"]:
            return

        if self.is_jumping and new_action not in ["jump", "idle"]:
            return

        if self.is_dashing and new_action not in ["dash_forward", "dash_backward", "idle"]:
            return

        if new_action in self.frame_ranges:
            self.current_action = new_action
            self.current_frame = self.frame_ranges[new_action][0]
            self.frame_counter = 0
            self.current_animation_speed = self.get_action_animation_speed(new_action)

    def update_animation(self):
        self.frame_counter += 1
        start_frame, end_frame = self.frame_ranges[self.current_action]

        if self.frame_counter >= self.current_animation_speed:
            self.frame_counter = 0

            # Логика анимации прыжка персонажа
            if self.current_action == "jump":
                if self.jump_loop:
                    loop_start, loop_end = self.jump_loop

                    if self.current_frame < loop_start:
                        self.current_frame += 1
                    elif self.center_y > GROUND_LEVEL + 5:  # Полет в воздухе
                        if self.current_frame >= loop_end:
                            self.current_frame = loop_start
                        else:
                            self.current_frame += 1
                    elif self.center_y <= GROUND_LEVEL:  # Приземление
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

            else:
                self.current_frame += 1
                if self.current_frame > end_frame:
                    self.current_frame = start_frame

            texture = self.get_current_texture(self.current_frame)
            if texture:
                self.texture = texture

    def update(self):
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        self.update_facing_direction()

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
            if not self.is_crouching and not self.is_dashing:
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
            self.ramka.center_y = SCREEN_HEIGHT - 100  # Опустили чуть-чуть от самого верха
            self.ui_sprite_list.append(self.ramka)

        self.header_text = arcade.Text("Выбери режим", SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
                                       arcade.color.BLACK, 24, anchor_x="center", anchor_y="center", bold=True)

        # 2. D'Arby (Масштаб 4x, в самом низу)
        self.darby_textures = []
        for i in range(14):
            p = Path("Лого") / f"DArby_{i}.png"
            if p.exists(): self.darby_textures.append(arcade.load_texture(str(p)))

        self.darby_sprite = arcade.Sprite(scale=4.0)
        self.darby_sprite.center_x = SCREEN_WIDTH // 2
        self.darby_sprite.bottom = 10
        if self.darby_textures: self.darby_sprite.texture = self.darby_textures[0]
        self.ui_sprite_list.append(self.darby_sprite)

        # 3. Боковые рамки (Масштаб 4x, зазоры со всех сторон)
        self.ram_textures = []
        for i in range(5):
            p = Path("Лого") / f"ram_{i}.png"
            if p.exists(): self.ram_textures.append(arcade.load_texture(str(p)))

        side_gap = 300  # Зазор от левого/правого края
        bottom_gap = 80  # Зазор от нижнего края

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
            if s.top < 0: s.center_y += 8 * self.tile_h

        # Анимация D'Arby (Intro/Outro)
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
                    # Импортируй тут свой вид выбора персонажа
                    from main import TestCharacterSelectView
                    self.window.show_view(TestCharacterSelectView())

                if self.current_frame < len(self.darby_textures):
                    self.darby_sprite.texture = self.darby_textures[self.current_frame]

        # Анимация активной боковой рамки
        self.ram_timer += delta_time
        if self.ram_timer >= 0.05:
            self.ram_timer = 0.0
            self.ram_anim_frame = (self.ram_anim_frame + 1) % 5

        # Логика текстур: активная крутится, пассивная стоит на 0
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
        if self.anim_state != "idle": return

        if key in [arcade.key.LEFT, arcade.key.A]:
            self.selected_index = 0
        elif key in [arcade.key.RIGHT, arcade.key.D]:
            self.selected_index = 1
        elif key == arcade.key.ENTER:
            if self.selected_index == 0:
                self.anim_state = "outro"
            else:
                print("Онлайн пока недоступен")


class TestCharacterSelectView(arcade.View):
    def __init__(self):
        super().__init__()

        # --- НАСТРОЙКА ДВИЖУЩЕГОСЯ ФОНА ---
        self.bg_sprite_list = arcade.SpriteList()
        bg_path = Path("Лого") / "fon_menu.png"

        orig_w, orig_h = 128, 64
        self.bg_scale = SCREEN_WIDTH / (5 * orig_w)
        self.tile_w, self.tile_h = orig_w * self.bg_scale, orig_h * self.bg_scale
        self.rows = 8  # Количество рядов, чтобы перекрыть экран с запасом

        if bg_path.exists():
            for r in range(self.rows):
                for c in range(5):
                    s = arcade.Sprite(str(bg_path), scale=self.bg_scale)
                    s.center_x = c * self.tile_w + (self.tile_w / 2)
                    s.center_y = r * self.tile_h + (self.tile_h / 2)
                    self.bg_sprite_list.append(s)
        # ----------------------------------

        self.characters = get_available_characters()
        self.p1_selected = 0
        self.p2_selected = 0
        self.current_player = 1

        self.logos = {}
        self.load_logos()

        # Твои существующие текстовые объекты
        self.title_text = arcade.Text(
            "ВЫБОР ПЕРСОНАЖЕЙ ДЛЯ ТЕСТОВОГО РЕЖИМА",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
            arcade.color.WHITE, 36, anchor_x="center"
        )
        # ... (остальные текстовые объекты оставляем без изменений)
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
        # Движение фона вниз
        for s in self.bg_sprite_list:
            s.center_y -= 3.0
            # Если плитка ушла за нижний край, перекидываем её наверх
            if s.top < 0:
                s.center_y += self.rows * self.tile_h

    def on_draw(self):
        self.clear()

        # 1. Рисуем движущийся фон
        self.bg_sprite_list.draw()

        # 2. Затемняем его, чтобы интерфейс и логотипы были читаемы
        arcade.draw_rect_filled(
            arcade.LRBT(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT),
            (0, 0, 0, 180)  # Чуть темнее (180 вместо 160), чтобы логотипы выделялись
        )

        # --- ДАЛЬШЕ ТВОЙ ОРИГИНАЛЬНЫЙ КОД ОТРИСОВКИ БЕЗ ИЗМЕНЕНИЙ ---
        self.title_text.draw()
        self.p1_text.draw()
        self.p2_text.draw()

        # Отрисовка колонок персонажей (P1 и P2)
        for i, character in enumerate(self.characters):
            # Левая колонка (P1)
            x1, y = SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2 - i * 220
            self._draw_char_element(character, i, x1, y, 1)

            # Правая колонка (P2)
            x2 = 3 * SCREEN_WIDTH // 4
            self._draw_char_element(character, i, x2, y, 2)

        # Текст текущего выбора
        if self.current_player == 1:
            arcade.draw_text("← ВЫБИРАЕТ", SCREEN_WIDTH // 4 - 150, SCREEN_HEIGHT - 180, arcade.color.GREEN, 16)
        else:
            arcade.draw_text("ВЫБИРАЕТ →", 3 * SCREEN_WIDTH // 4 + 150, SCREEN_HEIGHT - 180, arcade.color.GREEN, 16)

        self.instruction_text.draw()
        self.start_text.draw()

    def _draw_char_element(self, character, i, x, y, player_num):
        """Вспомогательная функция, чтобы не дублировать код отрисовки логотипа"""
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
        # Твой оригинальный код управления без изменений
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
            # Важно: убедись, что TestGameView определен в main.py
            if "TestGameView" in globals():
                game_view = globals()["TestGameView"](p1_char, p2_char)
                self.window.show_view(game_view)
                game_view.setup()
        elif key == arcade.key.ESCAPE:
            self.window.show_view(ModeMenuView())


class TestGameView(arcade.View):
    def __init__(self, p1_character, p2_character):
        super().__init__()

        self.p1_character_name = p1_character
        self.p2_character_name = p2_character
        arcade.set_background_color(arcade.color.BLACK)

        self.p1_left = False
        self.p1_right = False
        self.p1_up = False
        self.p1_down = False
        self.p1_w_was_pressed = False
        self.p1_s_was_pressed = False
        self.p1_shift_was_pressed = False

        self.p2_left = False
        self.p2_right = False
        self.p2_up = False
        self.p2_down = False
        self.p2_up_was_pressed = False
        self.p2_down_was_pressed = False
        self.p2_shift_was_pressed = False

        self.player1 = None
        self.player2 = None
        self.player1_list = None
        self.player2_list = None
        self.physics1 = None
        self.physics2 = None

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
        self.setup()

    def on_draw(self):
        self.clear()

        arcade.draw_line(0, GROUND_LEVEL, SCREEN_WIDTH, GROUND_LEVEL, arcade.color.GREEN, 3)
        arcade.draw_text("Земля", 20, GROUND_LEVEL - 30, arcade.color.GREEN, 14)

        # Безопасная отрисовка стендов через встроенные в класс методы
        if self.player1:
            self.player1.draw_stand()
        if self.player2:
            self.player2.draw_stand()

        if self.player1:
            self.player1_list.draw()
        if self.player2:
            self.player2_list.draw()

        info_y = SCREEN_HEIGHT - 50
        if self.player1 and hasattr(self.player1, 'character_data'):
            arcade.draw_text("ИГРОК 1", SCREEN_WIDTH // 4, info_y, arcade.color.CYAN, 20, anchor_x="center")
            info_y -= 30
            arcade.draw_text(f"Персонаж: {self.player1.character_data['display_name']}",
                             SCREEN_WIDTH // 4, info_y, arcade.color.WHITE, 14, anchor_x="center")
            info_y -= 25
            arcade.draw_text(f"Действие: {self.player1.current_action}",
                             SCREEN_WIDTH // 4, info_y, arcade.color.WHITE, 14, anchor_x="center")
            info_y -= 25
            arcade.draw_text(f"Кадр: {self.player1.current_frame}",
                             SCREEN_WIDTH // 4, info_y, arcade.color.WHITE, 14, anchor_x="center")
            info_y -= 25
            sprite_type = "Обычные (вправо)" if self.player1.current_direction == 0 else "Зеркальные (влево)"
            arcade.draw_text(f"Спрайты: {sprite_type}",
                             SCREEN_WIDTH // 4, info_y, arcade.color.YELLOW, 14, anchor_x="center")
            info_y -= 25

            stand_status = "Активирован" if self.player1.stand_active else "Скрыт"
            arcade.draw_text(f"Стенд: {stand_status}",
                             SCREEN_WIDTH // 4, info_y, arcade.color.LIGHT_GREEN, 14, anchor_x="center")

        info_y = SCREEN_HEIGHT - 50
        if self.player2 and hasattr(self.player2, 'character_data'):
            arcade.draw_text("ИГРОК 2", 3 * SCREEN_WIDTH // 4, info_y, arcade.color.ORANGE, 20, anchor_x="center")
            info_y -= 30
            arcade.draw_text(f"Персонаж: {self.player2.character_data['display_name']}",
                             3 * SCREEN_WIDTH // 4, info_y, arcade.color.WHITE, 14, anchor_x="center")
            info_y -= 25
            arcade.draw_text(f"Действие: {self.player2.current_action}",
                             3 * SCREEN_WIDTH // 4, info_y, arcade.color.WHITE, 14, anchor_x="center")
            info_y -= 25
            arcade.draw_text(f"Кадр: {self.player2.current_frame}",
                             3 * SCREEN_WIDTH // 4, info_y, arcade.color.WHITE, 14, anchor_x="center")
            info_y -= 25
            sprite_type = "Обычные (вправо)" if self.player2.current_direction == 0 else "Зеркальные (влево)"
            arcade.draw_text(f"Спрайты: {sprite_type}",
                             3 * SCREEN_WIDTH // 4, info_y, arcade.color.YELLOW, 14, anchor_x="center")
            info_y -= 25

            stand_status = "Активирован" if self.player2.stand_active else "Скрыт"
            arcade.draw_text(f"Стенд: {stand_status}",
                             3 * SCREEN_WIDTH // 4, info_y, arcade.color.LIGHT_GREEN, 14, anchor_x="center")

        arcade.draw_text("WASD + Shift (рывок) | Q - Стенд",
                         SCREEN_WIDTH // 4, 80, arcade.color.CYAN, 14, anchor_x="center")
        arcade.draw_text("Стрелки + Shift (рывок) | NUM 1 - Стенд",
                         3 * SCREEN_WIDTH // 4, 80, arcade.color.ORANGE, 14, anchor_x="center")

        arcade.draw_text("ESC - меню", SCREEN_WIDTH - 120, 30, arcade.color.GRAY, 14)

    def on_update(self, delta_time):
        if not self.player1 or not self.player2:
            return

        # === ИГРОК 1 (WASD) ===
        if not self.player1.is_summoning:
            if not self.player1.is_dashing:
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
                        self.player1.current_action not in ["crouch"]):
                    self.player1.set_action("idle")

            if self.p1_up and not self.p1_w_was_pressed:
                if not self.player1.is_crouching and self.player1.current_action != "crouch" and not self.player1.is_dashing:
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

        # === ИГРОК 2 (Стрелки) ===
        if not self.player2.is_summoning:
            if not self.player2.is_dashing:
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
                        self.player2.current_action not in ["crouch"]):
                    self.player2.set_action("idle")

            if self.p2_up and not self.p2_up_was_pressed:
                if not self.player2.is_crouching and self.player2.current_action != "crouch" and not self.player2.is_dashing:
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

    def on_key_press(self, key, modifiers):
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
            if self.player1 and not self.player1.is_dashing and self.player1.dash_cooldown == 0 and not self.player1.is_summoning:
                if self.p1_left:
                    self.player1.dash(-1)
                elif self.p1_right:
                    self.player1.dash(1)
                else:
                    self.player1.dash()

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
            if self.player2 and not self.player2.is_dashing and self.player2.dash_cooldown == 0 and not self.player2.is_summoning:
                if self.p2_left:
                    self.player2.dash(-1)
                elif self.p2_right:
                    self.player2.dash(1)
                else:
                    self.player2.dash()

        elif key == arcade.key.ESCAPE:
            self.window.show_view(ModeMenuView())

    def on_key_release(self, key, modifiers):
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


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = StartView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()