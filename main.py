import arcade
from pathlib import Path

# Константы
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Arcade Game - DIO"
MOVEMENT_SPEED = 5
JUMP_SPEED = 10
GRAVITY = 0.5
UPDATES_PER_FRAME = 5  # Скорость анимации


class Hero(arcade.Sprite):
    def __init__(self):
        """Инициализация героя"""
        # Загружаем все анимации
        self.load_animations()

        # Инициализируем спрайт с первой текстурой анимации бездействия
        super().__init__()
        self.texture = self.idle_textures[0]

        # Устанавливаем начальную позицию
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = 100  # Стартовая позиция выше для прыжков

        # Переменные для анимации
        self.current_texture = 0
        self.frame_counter = 0
        self.is_moving = False
        self.was_moving = False
        self.direction = "idle"  # idle, right, left, jump
        self.last_direction = "idle"

        # Переменные для прыжка
        self.change_y = 0  # Скорость по вертикали
        self.is_jumping = False
        self.jump_animation_playing = False

    def load_animations(self):
        """Загрузка всех анимаций"""
        # Анимация бездействия
        self.idle_textures = self.load_animation_frames("DIO-стоит", 0, 37)
        print(f"Загружено {len(self.idle_textures)} кадров анимации бездействия")

        # Анимация движения вправо (вперед)
        self.right_textures = self.load_animation_frames("DIO-двигается вперед", 54, 69)
        print(f"Загружено {len(self.right_textures)} кадров анимации движения вправо")

        # Анимация движения влево (назад)
        self.left_textures = self.load_animation_frames("DIO-двигается назад", 70, 85)
        print(f"Загружено {len(self.left_textures)} кадров анимации движения влево")

        # Анимация прыжка
        self.jump_textures = self.load_animation_frames("DIO-прыжок", 103, 115)
        print(f"Загружено {len(self.jump_textures)} кадров анимации прыжка")

    def load_animation_frames(self, folder_name, start_frame, end_frame):
        """Загрузка кадров анимации из указанной папки"""
        folder_path = Path(folder_name)
        textures = []

        # Загружаем кадры от start_frame до end_frame включительно
        for i in range(start_frame, end_frame + 1):
            filename = f"DIO_0-{i}.png"
            file_path = folder_path / filename

            # Загружаем текстуру
            texture = arcade.load_texture(str(file_path))
            textures.append(texture)

        return textures

    def jump(self):
        """Выполнение прыжка"""
        if not self.is_jumping:
            self.change_y = JUMP_SPEED
            self.is_jumping = True
            self.jump_animation_playing = True
            self.current_texture = 0  # Сбрасываем анимацию прыжка
            self.frame_counter = 0
            return True
        return False

    def update_animation(self):
        # Увеличиваем счетчик кадров
        self.frame_counter += 1

        # Определяем, какую анимацию проигрывать
        if self.is_jumping or self.jump_animation_playing:
            # Проигрываем анимацию прыжка
            textures = self.jump_textures
            direction = "jump"
        elif self.direction == "idle":
            textures = self.idle_textures
            direction = "idle"
        elif self.direction == "right":
            textures = self.right_textures
            direction = "right"
        elif self.direction == "left":
            textures = self.left_textures
            direction = "left"
        else:
            textures = self.idle_textures
            direction = "idle"

        # Меняем текстуру каждые UPDATES_PER_FRAME обновлений
        if self.frame_counter >= UPDATES_PER_FRAME:
            self.frame_counter = 0

            # Для прыжка проигрываем анимацию один раз, затем возвращаемся к обычной
            if direction == "jump":
                self.current_texture += 1
                if self.current_texture >= len(textures):
                    self.current_texture = len(textures) - 1
                    self.jump_animation_playing = False
            else:
                self.current_texture += 1
                # Циклически перебираем текстуры текущей анимации
                if self.current_texture >= len(textures):
                    self.current_texture = 0

            # Устанавливаем текущую текстуру
            self.texture = textures[self.current_texture]

        # Сохраняем текущее направление для следующего кадра
        self.last_direction = self.direction

        # Сбрасываем флаг движения для следующего кадра
        self.was_moving = self.is_moving
        self.is_moving = False
        self.direction = "idle"  # Сбрасываем направление, если не двигаемся

    def update(self):
        # Применяем гравитацию
        self.change_y -= GRAVITY

        # Обновляем позицию
        self.center_y += self.change_y

        # Проверка земли (нижней границы)
        if self.center_y < 100:  # "Земля" на высоте 100 пикселей
            self.center_y = 100
            self.change_y = 0
            self.is_jumping = False
            if self.last_direction == "jump":
                self.jump_animation_playing = False

        # Ограничение по левой границе
        if self.left < 0:
            self.left = 0

        # Ограничение по правой границе
        if self.right > SCREEN_WIDTH:
            self.right = SCREEN_WIDTH

        # Ограничение по верхней границе
        if self.top > SCREEN_HEIGHT:
            self.top = SCREEN_HEIGHT
            self.change_y = min(self.change_y, 0)  # Останавливаем движение вверх

        # Обновляем анимацию
        self.update_animation()


class MyGame(arcade.Window):

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Черный фон
        arcade.set_background_color(arcade.color.BLACK)

        # Спрайт-листы
        self.hero_sprite = None
        self.hero_list = None
        self.physics_engine = None

        # Переменные для управления
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.w_was_pressed = False  # Для отслеживания нажатия W

    def setup(self):
        # Создаем спрайт-лист для героя
        self.hero_list = arcade.SpriteList()

        # Создаем героя
        self.hero_sprite = Hero()
        self.hero_list.append(self.hero_sprite)

        # Создаем физический движок
        self.physics_engine = arcade.PhysicsEngineSimple(self.hero_sprite, None)

    def on_draw(self):
        # Очищаем экран
        self.clear()

        # Рисуем "землю"
        arcade.draw_line(0, 100, SCREEN_WIDTH, 100, arcade.color.GREEN)
        arcade.draw_text("Земля", 10, 80, arcade.color.GREEN, 12)

        # Рисуем героя
        self.hero_list.draw()

        # Отображаем инструкции
        arcade.draw_text(
            "Управление: WASD",
            10, SCREEN_HEIGHT - 30,
            arcade.color.WHITE, 16
        )
        arcade.draw_text(
            "A - назад, D - вперед, W - прыжок",
            10, SCREEN_HEIGHT - 60,
            arcade.color.WHITE, 16
        )
        arcade.draw_text(
            "ESC - выход",
            10, SCREEN_HEIGHT - 90,
            arcade.color.WHITE, 16
        )
        arcade.draw_text(
            f"Позиция: ({int(self.hero_sprite.center_x)}, {int(self.hero_sprite.center_y)})",
            10, SCREEN_HEIGHT - 120,
            arcade.color.WHITE, 16
        )
        arcade.draw_text(
            f"Скорость Y: {self.hero_sprite.change_y:.1f}",
            10, SCREEN_HEIGHT - 150,
            arcade.color.WHITE, 16
        )

        # Определяем текст и цвет для направления
        if self.hero_sprite.last_direction == "idle":
            direction_color = arcade.color.YELLOW
            direction_text = "Стоит"
        elif self.hero_sprite.last_direction == "right":
            direction_color = arcade.color.GREEN
            direction_text = "Двигается вправо (D)"
        elif self.hero_sprite.last_direction == "left":
            direction_color = arcade.color.BLUE
            direction_text = "Двигается влево (A)"
        else:  # jump
            direction_color = arcade.color.MAGENTA
            direction_text = "Прыжок (W)"

        arcade.draw_text(
            f"Состояние: {direction_text}",
            10, SCREEN_HEIGHT - 180,
            direction_color, 16
        )

        arcade.draw_text(
            f"Кадр анимации: {self.hero_sprite.current_texture + 1}",
            10, SCREEN_HEIGHT - 210,
            arcade.color.WHITE, 16
        )

        if not self.hero_sprite.is_jumping:
            arcade.draw_text(
                "Нажмите W для прыжка!",
                SCREEN_WIDTH // 2 - 100, 150,
                arcade.color.CYAN, 16
            )

    def on_update(self, delta_time):
        # Сбрасываем горизонтальную скорость
        self.hero_sprite.change_x = 0

        # Определяем, двигается ли персонаж и в каком направлении
        is_moving = False
        direction = "idle"

        # Обработка движения ВЛЕВО (A) - назад
        if self.left_pressed and not self.right_pressed:
            self.hero_sprite.change_x = -MOVEMENT_SPEED
            is_moving = True
            direction = "left"

        # Обработка движения ВПРАВО (D) - вперед
        if self.right_pressed and not self.left_pressed:
            self.hero_sprite.change_x = MOVEMENT_SPEED
            is_moving = True
            direction = "right"

        # Обработка прыжка (W)
        if self.up_pressed and not self.w_was_pressed:
            # Прыжок только при нажатии, а не удержании
            self.hero_sprite.jump()
            self.w_was_pressed = True

        # Устанавливаем флаги
        self.hero_sprite.is_moving = is_moving
        self.hero_sprite.direction = direction

        # Обновляем физику
        self.physics_engine.update()
        self.hero_sprite.update()

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
            arcade.close_window()

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


def main():
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()