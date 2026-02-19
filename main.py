import arcade
from pathlib import Path
from harakteristici import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, GRAVITY, GROUND_LEVEL,
    get_available_characters,
    get_character_info,
    character_exists,
    get_character_data,
    get_crouch_freeze_frame,
    get_sprite_scale
)

# Константы для меню
MENU_FONT_SIZE = 24
MENU_FONT_COLOR = arcade.color.WHITE
MENU_SELECTED_COLOR = arcade.color.YELLOW


class Character(arcade.Sprite):
    def __init__(self, character_name, start_pos_x, start_pos_y, player_number=1, opponent=None):
        super().__init__()

        # Проверяем существование персонажа
        if not character_exists(character_name):
            raise ValueError(f"Персонаж {character_name} не найден!")

        # Получаем данные персонажа
        self.character_data = get_character_data(character_name)
        self.character_name = character_name
        self.file_prefix = self.character_data["file_prefix"]
        self.player_number = player_number
        self.opponent = opponent

        # Характеристики
        self.movement_speed = self.character_data.get("movement_speed", 3)
        self.jump_speed = self.character_data.get("jump_speed", 15)
        self.animation_speed = self.character_data.get("animation_speed", 5)
        self.crouch_freeze_frame = self.character_data.get("crouch_freeze_frame", None)
        self.sprite_scale = self.character_data.get("sprite_scale", 0.5)

        # Диапазоны кадров
        self.frame_ranges = self.character_data["frame_ranges"]

        # Загружаем текстуры для обоих направлений
        self.all_textures = [{}, {}]
        self.load_all_textures()

        # Устанавливаем масштаб
        self.scale = self.sprite_scale

        # Позиция
        self.center_x = start_pos_x
        self.center_y = start_pos_y

        self.facing_right = True  # Временное значение
        self.current_direction = 0  # 0 - обычные спрайты, 1 - зеркальные

        # Анимация
        self.current_frame = 0
        self.frame_counter = 0
        self.current_action = "idle"
        self.is_jumping = False
        self.is_crouching = False
        self.crouch_freeze_frame_active = None
        self.crouch_resume_frame = None

        # Физика
        self.change_y = 0

        print(f"Загружен персонаж {self.player_number}: {self.character_data['display_name']}")

    def set_opponent(self, opponent):
        self.opponent = opponent
        print(f"Персонаж {self.player_number} получил ссылку на противника")

    def update_facing_direction(self):
        if self.opponent:
            # Если противник справа - смотрим направо (используем обычные спрайты)
            # Если противник слева - смотрим налево (используем зеркальные спрайты)
            if self.opponent.center_x > self.center_x:
                # Противник справа - смотрим направо (обычные спрайты)
                self.facing_right = True
                self.current_direction = 0
            else:
                # Противник слева - смотрим налево (зеркальные спрайты)
                self.facing_right = False
                self.current_direction = 1

    def load_all_textures(self):
        character_path = Path("Спрайты") / self.character_name

        # Определяем максимальный номер кадра
        max_frame = 0
        for start, end in self.frame_ranges.values():
            max_frame = max(max_frame, end)

        # Загружаем обычные спрайты (смотрят вправо) - суффикс _0
        print(f"Загрузка обычных спрайтов для {self.character_name}:")
        for i in range(max_frame + 1):
            filename = f"{self.file_prefix}_0-{i}.png"
            file_path = character_path / filename

            if file_path.exists():
                try:
                    texture = arcade.load_texture(str(file_path))
                    self.all_textures[0][i] = texture
                    print(f"  Загружен {filename}")
                except Exception as e:
                    print(f"  Ошибка загрузки {filename}: {e}")
                    self.all_textures[0][i] = None
            else:
                self.all_textures[0][i] = None

        # Загружаем зеркальные спрайты (смотрят влево) - суффикс _1
        print(f"Загрузка зеркальных спрайтов для {self.character_name}:")
        for i in range(max_frame + 1):
            filename = f"{self.file_prefix}_1-{i}.png"
            file_path = character_path / filename

            if file_path.exists():
                try:
                    texture = arcade.load_texture(str(file_path))
                    self.all_textures[1][i] = texture
                    print(f"  Загружен {filename}")
                except Exception as e:
                    print(f"  Ошибка загрузки {filename}: {e}")
                    self.all_textures[1][i] = None
            else:
                self.all_textures[1][i] = None

        # Подсчет загруженных текстур
        count_right = len([t for t in self.all_textures[0].values() if t])
        count_left = len([t for t in self.all_textures[1].values() if t])
        print(f"Загружено: обычных - {count_right}, зеркальных - {count_left}")

        # Устанавливаем начальную текстуру
        if 0 in self.all_textures[0] and self.all_textures[0][0]:
            self.texture = self.all_textures[0][0]

    def get_current_texture(self, frame_number):
        if frame_number in self.all_textures[self.current_direction] and self.all_textures[self.current_direction][
            frame_number]:
            return self.all_textures[self.current_direction][frame_number]

        # Если текстура для этого направления не найдена, пробуем другое
        other_direction = 1 - self.current_direction
        if frame_number in self.all_textures[other_direction] and self.all_textures[other_direction][frame_number]:
            return self.all_textures[other_direction][frame_number]

        # Если ничего не найдено, возвращаем любую доступную текстуру
        for direction in [0, 1]:
            if frame_number in self.all_textures[direction] and self.all_textures[direction][frame_number]:
                return self.all_textures[direction][frame_number]

        return None

    def get_action_for_movement(self, moving_left, moving_right):
        if self.current_direction == 0:
            # Обычные спрайты (смотрят вправо)
            if moving_left:
                return "move_left"
            elif moving_right:
                return "move_right"
        else:
            # Зеркальные спрайты (смотрят влево) - меняем местами
            if moving_left:
                # Движение влево на поле, но персонаж смотрит влево - используем анимацию "move_right"
                return "move_right"
            elif moving_right:
                # Движение вправо на поле, но персонаж смотрит влево - используем анимацию "move_left"
                return "move_left"

        return None

    def jump(self):
        """Прыжок"""
        if not self.is_jumping and not self.is_crouching and self.center_y <= GROUND_LEVEL:
            self.change_y = self.jump_speed
            self.is_jumping = True
            self.current_action = "jump"
            self.current_frame = self.frame_ranges["jump"][0]
            self.frame_counter = 0
            return True
        return False

    def crouch(self, start_crouch=True):
        """Приседание"""
        if "crouch" not in self.frame_ranges:
            return

        start_frame, end_frame = self.frame_ranges["crouch"]

        if start_crouch:
            if not self.is_jumping and not self.is_crouching:
                self.is_crouching = True
                self.current_action = "crouch"
                self.current_frame = start_frame
                self.frame_counter = 0

                if self.crouch_freeze_frame and start_frame <= self.crouch_freeze_frame <= end_frame:
                    self.crouch_freeze_frame_active = self.crouch_freeze_frame
                else:
                    self.crouch_freeze_frame_active = (start_frame + end_frame) // 2
        else:
            if self.is_crouching:
                self.crouch_resume_frame = self.current_frame
                self.is_crouching = False
                self.crouch_freeze_frame_active = None

    def set_action(self, new_action):
        if new_action == self.current_action:
            return

        if self.is_jumping and new_action not in ["jump", "idle"]:
            return

        if new_action in self.frame_ranges:
            self.current_action = new_action
            self.current_frame = self.frame_ranges[new_action][0]
            self.frame_counter = 0

    def update_animation(self):
        self.frame_counter += 1
        start_frame, end_frame = self.frame_ranges[self.current_action]
        if self.frame_counter >= self.animation_speed:
            self.frame_counter = 0

            if self.current_action == "jump":
                self.current_frame += 1
                if self.current_frame > end_frame:
                    self.current_frame = end_frame
                    self.is_jumping = False
                    self.current_action = "idle"

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
                        self.current_action = "idle"

            else:
                self.current_frame += 1
                if self.current_frame > end_frame:
                    self.current_frame = start_frame

            # Устанавливаем текстуру с учетом направления взгляда
            texture = self.get_current_texture(self.current_frame)
            if texture:
                self.texture = texture

    def update(self):
        # Сначала обновляем направление взгляда относительно противника
        self.update_facing_direction()

        # Гравитация
        if not self.is_crouching:
            self.change_y -= GRAVITY
        self.center_y += self.change_y

        if self.center_y < GROUND_LEVEL:
            self.center_y = GROUND_LEVEL
            self.change_y = 0
            self.is_jumping = False
            if self.current_action == "jump":
                self.current_action = "idle"

        if self.left < 0:
            self.left = 0
        if self.right > SCREEN_WIDTH:
            self.right = SCREEN_WIDTH
        if self.top > SCREEN_HEIGHT:
            self.top = SCREEN_HEIGHT
            self.change_y = 0

        self.update_animation()


class ModeMenuView(arcade.View):
    def __init__(self):
        super().__init__()

        self.modes = ["ТЕСТОВЫЙ РЕЖИМ (2 игрока)", "ОНЛАЙН (в разработке)"]
        self.selected_index = 0

        # Текст
        self.title_text = arcade.Text(
            "ВЫБЕРИТЕ РЕЖИМ ИГРЫ",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200,
            arcade.color.WHITE, 48,
            anchor_x="center"
        )

        self.instruction_text = arcade.Text(
            "Используйте стрелки ВВЕРХ/ВНИЗ для выбора, ENTER для подтверждения",
            SCREEN_WIDTH // 2, 150,
            arcade.color.GRAY, 18,
            anchor_x="center"
        )

        # Описание режимов
        self.descriptions = [
            "Два игрока: WASD (Игрок 1) и Стрелки (Игрок 2). Можно выбрать разных персонажей",
            "Режим онлайн будет доступен в будущих обновлениях"
        ]

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        self.title_text.draw()

        for i, mode in enumerate(self.modes):
            x = SCREEN_WIDTH // 2
            y = SCREEN_HEIGHT // 2 - i * 120

            # Название режима
            color = MENU_SELECTED_COLOR if i == self.selected_index else MENU_FONT_COLOR
            arcade.draw_text(
                mode,
                x, y,
                color, MENU_FONT_SIZE + 4,
                anchor_x="center"
            )

            # Описание режима
            arcade.draw_text(
                self.descriptions[i],
                x, y - 40,
                arcade.color.GRAY, 16,
                anchor_x="center"
            )

            # Рамка для выбранного режима
            if i == self.selected_index:
                arcade.draw_lrbt_rectangle_outline(
                    x - 300, x + 300,
                    y - 70, y + 30,
                    arcade.color.YELLOW, 4
                )

        self.instruction_text.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.selected_index = (self.selected_index - 1) % len(self.modes)
        elif key == arcade.key.DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.modes)
        elif key == arcade.key.ENTER:
            if self.selected_index == 0:  # Тестовый режим
                character_select_view = TestCharacterSelectView()
                self.window.show_view(character_select_view)
            elif self.selected_index == 1:  # Онлайн режим
                print("Онлайн режим в разработке")


class TestCharacterSelectView(arcade.View):
    def __init__(self):
        super().__init__()

        self.characters = get_available_characters()
        self.p1_selected = 0  # Индекс для игрока 1
        self.p2_selected = 0  # Индекс для игрока 2
        self.current_player = 1  # Какого игрока сейчас выбираем (1 или 2)

        # Загружаем логотипы
        self.logos = {}
        self.load_logos()

        # Текст
        self.title_text = arcade.Text(
            "ВЫБОР ПЕРСОНАЖЕЙ ДЛЯ ТЕСТОВОГО РЕЖИМА",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
            arcade.color.WHITE, 36,
            anchor_x="center"
        )

        self.p1_text = arcade.Text(
            "ИГРОК 1 (WASD)",
            SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150,
            arcade.color.CYAN, 28,
            anchor_x="center"
        )

        self.p2_text = arcade.Text(
            "ИГРОК 2 (Стрелки)",
            3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150,
            arcade.color.ORANGE, 28,
            anchor_x="center"
        )

        self.instruction_text = arcade.Text(
            "ENTER - выбрать текущего игрока | ПРОБЕЛ - переключить выбор между игроками | ESC - назад",
            SCREEN_WIDTH // 2, 80,
            arcade.color.GRAY, 16,
            anchor_x="center"
        )

        self.start_text = arcade.Text(
            "После выбора обоих игроков нажмите S для старта",
            SCREEN_WIDTH // 2, 50,
            arcade.color.GREEN, 18,
            anchor_x="center"
        )

    def load_logos(self):
        logos_path = Path("Лого")
        for character in self.characters:
            for file_path in logos_path.glob(f"{character}.*"):
                try:
                    self.logos[character] = arcade.load_texture(str(file_path))
                    print(f"Загружен логотип для {character}")
                except:
                    pass

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        self.title_text.draw()
        self.p1_text.draw()
        self.p2_text.draw()

        # Отображаем персонажей для игрока 1
        for i, character in enumerate(self.characters):
            x = SCREEN_WIDTH // 4
            y = SCREEN_HEIGHT // 2 - i * 220

            # Логотип
            if character in self.logos:
                tex = self.logos[character]
                scale = min(150 / tex.width, 120 / tex.height)
                arcade.draw_texture_rect(
                    tex,
                    arcade.XYWH(
                        x - (tex.width * scale) // 2,
                        y + 40 - (tex.height * scale) // 2,
                        tex.width * scale,
                        tex.height * scale
                    )
                )

            # Определяем цвет для имени
            if self.current_player == 1 and i == self.p1_selected:
                color = arcade.color.GREEN  # Выбранный текущим игроком
            elif i == self.p1_selected:
                color = arcade.color.CYAN  # Выбранный но не текущий
            else:
                color = arcade.color.GRAY

            # Имя
            arcade.draw_text(
                character if character == "DIO" else "Jotaro Kujo",
                x, y - 40,
                color, 20,
                anchor_x="center"
            )

            # Рамка для выбранного
            if i == self.p1_selected:
                arcade.draw_lrbt_rectangle_outline(
                    x - 120, x + 120,
                    y - 70, y + 80,
                    arcade.color.CYAN if self.current_player != 1 else arcade.color.GREEN,
                    3
                )

        # Отображаем персонажей для игрока 2
        for i, character in enumerate(self.characters):
            x = 3 * SCREEN_WIDTH // 4
            y = SCREEN_HEIGHT // 2 - i * 220

            # Логотип
            if character in self.logos:
                tex = self.logos[character]
                scale = min(150 / tex.width, 120 / tex.height)
                arcade.draw_texture_rect(
                    tex,
                    arcade.XYWH(
                        x - (tex.width * scale) // 2,
                        y + 40 - (tex.height * scale) // 2,
                        tex.width * scale,
                        tex.height * scale
                    )
                )

            # Определяем цвет для имени
            if self.current_player == 2 and i == self.p2_selected:
                color = arcade.color.GREEN  # Выбранный текущим игроком
            elif i == self.p2_selected:
                color = arcade.color.ORANGE  # Выбранный но не текущий
            else:
                color = arcade.color.GRAY

            # Имя
            arcade.draw_text(
                character if character == "DIO" else "Jotaro Kujo",
                x, y - 40,
                color, 20,
                anchor_x="center"
            )

            # Рамка для выбранного
            if i == self.p2_selected:
                arcade.draw_lrbt_rectangle_outline(
                    x - 120, x + 120,
                    y - 70, y + 80,
                    arcade.color.ORANGE if self.current_player != 2 else arcade.color.GREEN,
                    3
                )

        # Указатель текущего игрока
        if self.current_player == 1:
            arcade.draw_text("← ВЫБИРАЕТ", SCREEN_WIDTH // 4 - 150, SCREEN_HEIGHT - 180, arcade.color.GREEN, 16)
        else:
            arcade.draw_text("ВЫБИРАЕТ →", 3 * SCREEN_WIDTH // 4 + 150, SCREEN_HEIGHT - 180, arcade.color.GREEN, 16)

        self.instruction_text.draw()
        self.start_text.draw()

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
            # Подтверждаем выбор текущего игрока
            if self.current_player == 1:
                self.current_player = 2
            else:
                self.current_player = 1

        elif key == arcade.key.SPACE:
            # Переключаем выбор между игроками
            self.current_player = 3 - self.current_player  # 1 -> 2, 2 -> 1

        elif key == arcade.key.S:
            # Старт игры с выбранными персонажами
            p1_character = self.characters[self.p1_selected]
            p2_character = self.characters[self.p2_selected]
            game_view = TestGameView(p1_character, p2_character)
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

        # Управление для первого игрока (WASD)
        self.p1_left = False
        self.p1_right = False
        self.p1_up = False
        self.p1_down = False
        self.p1_w_was_pressed = False
        self.p1_s_was_pressed = False

        # Управление для второго игрока (Стрелки)
        self.p2_left = False
        self.p2_right = False
        self.p2_up = False
        self.p2_down = False
        self.p2_up_was_pressed = False
        self.p2_down_was_pressed = False

        # Персонажи
        self.player1 = None
        self.player2 = None
        self.player1_list = None
        self.player2_list = None
        self.physics1 = None
        self.physics2 = None

    def setup(self):
        # Создаем персонажей без ссылок друг на друга
        self.player1 = Character(self.p1_character_name, SCREEN_WIDTH // 4, GROUND_LEVEL, player_number=1)
        self.player2 = Character(self.p2_character_name, 3 * SCREEN_WIDTH // 4, GROUND_LEVEL, player_number=2)

        # Устанавливаем ссылки друг на друга
        self.player1.set_opponent(self.player2)
        self.player2.set_opponent(self.player1)

        # Создаем спрайт-листы
        self.player1_list = arcade.SpriteList()
        self.player1_list.append(self.player1)
        self.physics1 = arcade.PhysicsEngineSimple(self.player1, None)

        self.player2_list = arcade.SpriteList()
        self.player2_list.append(self.player2)
        self.physics2 = arcade.PhysicsEngineSimple(self.player2, None)

        print(f"Тестовый режим запущен")
        print(f"Игрок 1: {self.p1_character_name} (WASD) - позиция X: {self.player1.center_x}")
        print(f"Игрок 2: {self.p2_character_name} (Стрелки) - позиция X: {self.player2.center_x}")

    def on_show(self):
        self.setup()

    def on_draw(self):
        self.clear()

        # Земля для обоих игроков
        arcade.draw_line(0, GROUND_LEVEL, SCREEN_WIDTH, GROUND_LEVEL, arcade.color.GREEN, 3)
        arcade.draw_text("Земля", 20, GROUND_LEVEL - 30, arcade.color.GREEN, 14)

        # Персонажи
        if self.player1:
            self.player1_list.draw()
        if self.player2:
            self.player2_list.draw()

        # Информация об игроках
        # Игрок 1 (слева)
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
            # Показываем, какой тип спрайтов используется
            sprite_type = "Обычные (смотрит вправо)" if self.player1.current_direction == 0 else "Зеркальные (смотрит влево)"
            arcade.draw_text(f"Спрайты: {sprite_type}",
                             SCREEN_WIDTH // 4, info_y, arcade.color.YELLOW, 14, anchor_x="center")

        # Игрок 2 (справа)
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
            # Показываем, какой тип спрайтов используется
            sprite_type = "Обычные (смотрит вправо)" if self.player2.current_direction == 0 else "Зеркальные (смотрит влево)"
            arcade.draw_text(f"Спрайты: {sprite_type}",
                             3 * SCREEN_WIDTH // 4, info_y, arcade.color.YELLOW, 14, anchor_x="center")

        # Управление
        arcade.draw_text("WASD", SCREEN_WIDTH // 4, 80, arcade.color.CYAN, 18, anchor_x="center")
        arcade.draw_text("Стрелки", 3 * SCREEN_WIDTH // 4, 80, arcade.color.ORANGE, 18, anchor_x="center")

        # Выход
        arcade.draw_text("ESC - меню", SCREEN_WIDTH - 120, 30, arcade.color.GRAY, 14)

    def on_update(self, delta_time):
        if not self.player1 or not self.player2:
            return

        # === ИГРОК 1 (WASD) ===
        self.player1.change_x = 0

        if not self.player1.is_crouching and self.player1.current_action != "crouch":
            if self.p1_left:
                self.player1.change_x = -self.player1.movement_speed
                if not self.player1.is_jumping:
                    # Используем новый метод для определения действия
                    action = self.player1.get_action_for_movement(True, False)
                    if action:
                        self.player1.set_action(action)

            if self.p1_right:
                self.player1.change_x = self.player1.movement_speed
                if not self.player1.is_jumping:
                    # Используем новый метод для определения действия
                    action = self.player1.get_action_for_movement(False, True)
                    if action:
                        self.player1.set_action(action)

        if (not self.p1_left and not self.p1_right and
                not self.player1.is_jumping and
                self.player1.current_action not in ["crouch"]):
            self.player1.set_action("idle")

        # Прыжок игрока 1 (W)
        if self.p1_up and not self.p1_w_was_pressed:
            if not self.player1.is_crouching and self.player1.current_action != "crouch":
                self.player1.jump()
            self.p1_w_was_pressed = True

        # Приседание игрока 1 (S)
        if self.p1_down and not self.p1_s_was_pressed:
            self.player1.crouch(True)
            self.p1_s_was_pressed = True

        if not self.p1_down and self.p1_s_was_pressed:
            self.player1.crouch(False)
            self.p1_s_was_pressed = False

        # === ИГРОК 2 (Стрелки) ===
        self.player2.change_x = 0

        if not self.player2.is_crouching and self.player2.current_action != "crouch":
            if self.p2_left:
                self.player2.change_x = -self.player2.movement_speed
                if not self.player2.is_jumping:
                    # Используем новый метод для определения действия
                    action = self.player2.get_action_for_movement(True, False)
                    if action:
                        self.player2.set_action(action)

            if self.p2_right:
                self.player2.change_x = self.player2.movement_speed
                if not self.player2.is_jumping:
                    # Используем новый метод для определения действия
                    action = self.player2.get_action_for_movement(False, True)
                    if action:
                        self.player2.set_action(action)

        if (not self.p2_left and not self.p2_right and
                not self.player2.is_jumping and
                self.player2.current_action not in ["crouch"]):
            self.player2.set_action("idle")

        # Прыжок игрока 2 (Стрелка вверх)
        if self.p2_up and not self.p2_up_was_pressed:
            if not self.player2.is_crouching and self.player2.current_action != "crouch":
                self.player2.jump()
            self.p2_up_was_pressed = True

        # Приседание игрока 2 (Стрелка вниз)
        if self.p2_down and not self.p2_down_was_pressed:
            self.player2.crouch(True)
            self.p2_down_was_pressed = True

        if not self.p2_down and self.p2_down_was_pressed:
            self.player2.crouch(False)
            self.p2_down_was_pressed = False

        # Физика
        if self.physics1 and self.physics2:
            self.physics1.update()
            self.physics2.update()

        # Обновление персонажей
        if self.player1:
            self.player1.update()
        if self.player2:
            self.player2.update()

    def on_key_press(self, key, modifiers):
        # Игрок 1 - WASD
        if key == arcade.key.A:
            self.p1_left = True
        elif key == arcade.key.D:
            self.p1_right = True
        elif key == arcade.key.W:
            self.p1_up = True
        elif key == arcade.key.S:
            self.p1_down = True

        # Игрок 2 - Стрелки
        elif key == arcade.key.LEFT:
            self.p2_left = True
        elif key == arcade.key.RIGHT:
            self.p2_right = True
        elif key == arcade.key.UP:
            self.p2_up = True
        elif key == arcade.key.DOWN:
            self.p2_down = True

        # Выход в меню
        elif key == arcade.key.ESCAPE:
            self.window.show_view(ModeMenuView())

    def on_key_release(self, key, modifiers):
        # Игрок 1 - WASD
        if key == arcade.key.A:
            self.p1_left = False
        elif key == arcade.key.D:
            self.p1_right = False
        elif key == arcade.key.W:
            self.p1_up = False
            self.p1_w_was_pressed = False
        elif key == arcade.key.S:
            self.p1_down = False

        # Игрок 2 - Стрелки
        elif key == arcade.key.LEFT:
            self.p2_left = False
        elif key == arcade.key.RIGHT:
            self.p2_right = False
        elif key == arcade.key.UP:
            self.p2_up = False
            self.p2_up_was_pressed = False
        elif key == arcade.key.DOWN:
            self.p2_down = False


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.show_view(ModeMenuView())
    arcade.run()


if __name__ == "__main__":
    main()