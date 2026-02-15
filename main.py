import arcade
from pathlib import Path
from harakteristici import (
    get_available_characters,
    get_character_info,
    character_exists,
    get_character_data,
    get_crouch_freeze_frame
)

# Константы
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Arcade Game"
GRAVITY = 0.5

# Константы для меню
MENU_FONT_SIZE = 24
MENU_FONT_COLOR = arcade.color.WHITE
MENU_SELECTED_COLOR = arcade.color.YELLOW


class Character(arcade.Sprite):
    def __init__(self, character_name, start_pos_x, start_pos_y):
        """Инициализация персонажа"""
        if not character_exists(character_name):
            raise ValueError(f"Персонаж {character_name} не найден!")

        # Получаем данные персонажа
        self.character_data = get_character_data(character_name)
        self.character_name = character_name
        self.file_prefix = self.character_data["file_prefix"]

        # Характеристики
        self.movement_speed = self.character_data.get("movement_speed", 5)
        self.jump_speed = self.character_data.get("jump_speed", 15)
        self.animation_speed = self.character_data.get("animation_speed", 5)
        self.crouch_freeze_frame = self.character_data.get("crouch_freeze_frame", None)

        # Диапазоны кадров
        self.frame_ranges = self.character_data["frame_ranges"]

        # Загружаем текстуры
        self.all_textures = []
        self.load_all_textures()

        # Инициализируем спрайт
        super().__init__()
        if self.all_textures:
            self.texture = self.all_textures[0]

        # Позиция
        self.center_x = start_pos_x
        self.center_y = start_pos_y

        # Анимация
        self.current_frame = 0
        self.frame_counter = 0
        self.current_action = "idle"
        self.is_jumping = False
        self.is_crouching = False
        self.crouch_freeze_frame_active = None  # Кадр на котором замираем при приседании
        self.crouch_resume_frame = None  # Кадр с которого продолжаем после отпускания

        # Физика
        self.change_y = 0

        # Направление
        self.facing_right = True

        print(f"Загружен персонаж: {self.character_data['display_name']}")
        print(f"Кадров загружено: {len(self.all_textures)}")
        print(f"Диапазоны: {self.frame_ranges}")
        print(f"Кадр заморозки приседания: {self.crouch_freeze_frame}")

    def load_all_textures(self):
        """Загрузка всех текстур"""
        character_path = Path("Спрайты") / self.character_name

        # Определяем максимальный номер кадра
        max_frame = 0
        for start, end in self.frame_ranges.values():
            max_frame = max(max_frame, end)

        # Загружаем кадры
        for i in range(max_frame + 1):
            filename = f"{self.file_prefix}_0-{i}.png"
            file_path = character_path / filename

            if file_path.exists():
                try:
                    texture = arcade.load_texture(str(file_path))
                    self.all_textures.append(texture)
                except:
                    self.all_textures.append(None)
            else:
                self.all_textures.append(None)

    def jump(self):
        """Прыжок"""
        if not self.is_jumping and not self.is_crouching and self.center_y <= 100:
            self.change_y = self.jump_speed
            self.is_jumping = True
            self.current_action = "jump"
            self.current_frame = self.frame_ranges["jump"][0]
            self.frame_counter = 0
            return True
        return False

    def crouch(self, start_crouch=True):
        """Приседание / Вставание

        Args:
            start_crouch: True - начать приседание, False - закончить
        """
        if "crouch" not in self.frame_ranges:
            return

        start_frame, end_frame = self.frame_ranges["crouch"]

        if start_crouch:
            # Начинаем приседание
            if not self.is_jumping and not self.is_crouching:
                self.is_crouching = True
                self.current_action = "crouch"
                self.current_frame = start_frame
                self.frame_counter = 0

                # Устанавливаем кадр заморозки из характеристик
                if self.crouch_freeze_frame and start_frame <= self.crouch_freeze_frame <= end_frame:
                    self.crouch_freeze_frame_active = self.crouch_freeze_frame
                else:
                    # Если не указан или вне диапазона, замираем на середине
                    self.crouch_freeze_frame_active = (start_frame + end_frame) // 2
        else:
            # Заканчиваем приседание
            if self.is_crouching:
                # Запоминаем текущий кадр как точку возобновления
                self.crouch_resume_frame = self.current_frame
                self.is_crouching = False
                # Сбрасываем флаг заморозки
                self.crouch_freeze_frame_active = None

    def set_action(self, new_action):
        """Смена действия"""
        if new_action == self.current_action:
            return

        # Не меняем действие во время прыжка
        if self.is_jumping and new_action not in ["jump", "idle"]:
            return

        if new_action in self.frame_ranges:
            self.current_action = new_action
            self.current_frame = self.frame_ranges[new_action][0]
            self.frame_counter = 0

    def update_animation(self):
        """Обновление анимации"""
        self.frame_counter += 1

        # Получаем текущий диапазон
        start_frame, end_frame = self.frame_ranges[self.current_action]

        # Меняем кадр
        if self.frame_counter >= self.animation_speed:
            self.frame_counter = 0

            # Для прыжка - один раз
            if self.current_action == "jump":
                self.current_frame += 1
                if self.current_frame > end_frame:
                    self.current_frame = end_frame
                    self.is_jumping = False
                    self.current_action = "idle"

            # Для приседания - особая логика
            elif self.current_action == "crouch":
                if self.is_crouching:
                    # Если приседаем и есть кадр заморозки
                    if self.crouch_freeze_frame_active is not None:
                        if self.current_frame < self.crouch_freeze_frame_active:
                            # Идем до кадра заморозки
                            self.current_frame += 1
                            if self.current_frame > self.crouch_freeze_frame_active:
                                self.current_frame = self.crouch_freeze_frame_active
                        # Замираем на кадре заморозки
                    else:
                        # Обычное приседание без заморозки
                        self.current_frame += 1
                        if self.current_frame > end_frame:
                            self.current_frame = end_frame
                else:
                    # Если встаем - допроигрываем с текущего кадра до конца
                    if self.crouch_resume_frame is not None:
                        self.current_frame = self.crouch_resume_frame
                        self.crouch_resume_frame = None

                    self.current_frame += 1
                    if self.current_frame > end_frame:
                        self.current_frame = end_frame
                        # После завершения анимации вставания переходим в idle
                        self.current_action = "idle"

            else:
                # Для остальных действий - зацикливаем
                self.current_frame += 1
                if self.current_frame > end_frame:
                    self.current_frame = start_frame

            # Устанавливаем текстуру
            if self.current_frame < len(self.all_textures) and self.all_textures[self.current_frame]:
                self.texture = self.all_textures[self.current_frame]

    def update(self):
        """Обновление"""
        # Гравитация
        if not self.is_crouching:
            self.change_y -= GRAVITY
        self.center_y += self.change_y

        # Земля
        if self.center_y < 100:
            self.center_y = 100
            self.change_y = 0
            self.is_jumping = False
            if self.current_action == "jump":
                self.current_action = "idle"

        # Границы экрана
        if self.left < 0:
            self.left = 0
        if self.right > SCREEN_WIDTH:
            self.right = SCREEN_WIDTH
        if self.top > SCREEN_HEIGHT:
            self.top = SCREEN_HEIGHT
            self.change_y = 0

        # Анимация
        self.update_animation()


class MenuView(arcade.View):
    """Меню выбора персонажа"""

    def __init__(self):
        super().__init__()

        self.characters = get_available_characters()
        self.selected_index = 0

        # Загружаем логотипы
        self.logos = {}
        self.load_logos()

        # Текст
        self.title_text = arcade.Text(
            "ВЫБЕРИТЕ ПЕРСОНАЖА",
            SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100,
            arcade.color.WHITE, 36,
            anchor_x="center"
        )

    def load_logos(self):
        """Загрузка логотипов"""
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

        for i, character in enumerate(self.characters):
            x = SCREEN_WIDTH // 2
            y = SCREEN_HEIGHT // 2 - i * 200

            # Логотип
            if character in self.logos:
                tex = self.logos[character]
                scale = min(200 / tex.width, 150 / tex.height)
                arcade.draw_texture_rect(
                    tex,
                    arcade.XYWH(
                        x - (tex.width * scale) // 2,
                        y + 50 - (tex.height * scale) // 2,
                        tex.width * scale,
                        tex.height * scale
                    )
                )

            # Имя
            color = MENU_SELECTED_COLOR if i == self.selected_index else MENU_FONT_COLOR
            arcade.draw_text(
                character if character == "DIO" else "Jotaro Kujo",
                x, y - 50,
                color, MENU_FONT_SIZE,
                anchor_x="center"
            )

            # Рамка
            if i == self.selected_index:
                arcade.draw_lrbt_rectangle_outline(
                    x - 150, x + 150,
                    y - 100, y + 125,
                    arcade.color.YELLOW, 3
                )


    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.selected_index = (self.selected_index - 1) % len(self.characters)
        elif key == arcade.key.DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.characters)
        elif key == arcade.key.ENTER:
            game_view = GameView(self.characters[self.selected_index])
            self.window.show_view(game_view)
            game_view.setup()


class GameView(arcade.View):
    """Игровой процесс"""

    def __init__(self, character_name):
        super().__init__()

        self.character_name = character_name
        arcade.set_background_color(arcade.color.BLACK)

        # Управление
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.w_was_pressed = False
        self.s_was_pressed = False

        # Персонаж
        self.character = None
        self.character_list = None
        self.physics = None

    def setup(self):
        """Настройка игры"""
        self.character_list = arcade.SpriteList()
        self.character = Character(self.character_name, SCREEN_WIDTH // 2, 100)
        self.character_list.append(self.character)
        self.physics = arcade.PhysicsEngineSimple(self.character, None)
        print("Игра запущена")

    def on_show(self):
        self.setup()

    def on_draw(self):
        self.clear()

        # Земля
        arcade.draw_line(0, 100, SCREEN_WIDTH, 100, arcade.color.GREEN)
        arcade.draw_text("Земля", 10, 80, arcade.color.GREEN, 12)

        # Персонаж
        if self.character:
            self.character_list.draw()

            # Информация
            y = SCREEN_HEIGHT - 30
            arcade.draw_text(f"Персонаж: {self.character.character_data['display_name']}", 10, y, arcade.color.WHITE,
                             16)
            y -= 25
            arcade.draw_text(f"Действие: {self.character.current_action}", 10, y, arcade.color.WHITE, 16)
            y -= 25
            arcade.draw_text(f"Кадр: {self.character.current_frame}", 10, y, arcade.color.WHITE, 16)
            y -= 25
            arcade.draw_text(f"Флаги: прыжок={self.character.is_jumping}, присед={self.character.is_crouching}", 10, y,
                             arcade.color.WHITE, 16)
            y -= 25
            if self.character.crouch_freeze_frame_active:
                arcade.draw_text(f"Заморозка на кадре: {self.character.crouch_freeze_frame_active}", 10, y,
                                 arcade.color.YELLOW, 16)
                y -= 25
            arcade.draw_text(f"ESC - меню", 10, y, arcade.color.WHITE, 16)

            # Подсказки по управлению
            arcade.draw_text("W - прыжок, S - присесть (замереть на кадре), A/D - движение",
                             SCREEN_WIDTH // 2, 50, arcade.color.GRAY, 14, anchor_x="center")

    def on_update(self, delta_time):
        if not self.character:
            return

        # Движение
        self.character.change_x = 0

        # Не можем двигаться во время приседания или вставания
        if not self.character.is_crouching and self.character.current_action != "crouch":
            if self.left_pressed:
                self.character.change_x = -self.character.movement_speed
                self.character.facing_right = False
                if not self.character.is_jumping:
                    self.character.set_action("move_left")

            if self.right_pressed:
                self.character.change_x = self.character.movement_speed
                self.character.facing_right = True
                if not self.character.is_jumping:
                    self.character.set_action("move_right")

        # Если не двигаемся и не прыгаем и не в специальных состояниях
        if (not self.left_pressed and not self.right_pressed and
                not self.character.is_jumping and
                self.character.current_action not in ["crouch"]):
            self.character.set_action("idle")

        # Прыжок (нельзя прыгать во время приседания или вставания)
        if self.up_pressed and not self.w_was_pressed:
            if not self.character.is_crouching and self.character.current_action != "crouch":
                self.character.jump()
            self.w_was_pressed = True

        # Приседание - кадр заморозки берется из характеристик персонажа
        if self.down_pressed and not self.s_was_pressed:
            self.character.crouch(True)
            self.s_was_pressed = True

        # Отпускание S - допроигрываем оставшиеся кадры
        if not self.down_pressed and self.s_was_pressed:
            self.character.crouch(False)
            self.s_was_pressed = False

        # Физика
        self.physics.update()
        self.character.update()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.ESCAPE:
            self.window.show_view(MenuView())

    def on_key_release(self, key, modifiers):
        if key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.D:
            self.right_pressed = False
        elif key == arcade.key.W:
            self.up_pressed = False
            self.w_was_pressed = False
        elif key == arcade.key.S:
            self.down_pressed = False
            # Не сбрасываем s_was_pressed здесь, это делается в on_update


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.show_view(MenuView())
    arcade.run()


if __name__ == "__main__":
    main()