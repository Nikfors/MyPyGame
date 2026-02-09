import arcade
from pathlib import Path

# Константы
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Arcade Game - DIO"
MOVEMENT_SPEED = 5
UPDATES_PER_FRAME = 5  # Скорость анимации


class Hero(arcade.Sprite):
    def __init__(self):
        """Инициализация героя"""
        # Сначала загружаем текстуры
        idle_folder = Path("DIO-стоит")
        self.idle_textures = []

        # Загружаем все кадры анимации DIO_0-0.png до DIO_0-37.png
        for i in range(38):  # от 0 до 37 включительно
            filename = f"DIO_0-{i}.png"
            file_path = idle_folder / filename

            # Загружаем текстуру
            texture = arcade.load_texture(str(file_path))
            self.idle_textures.append(texture)

        print(f"Загружено {len(self.idle_textures)} кадров анимации")

        # Инициализируем спрайт с первой текстурой
        super().__init__()
        self.texture = self.idle_textures[0]

        # Устанавливаем начальную позицию
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2

        # Переменные для анимации
        self.current_texture = 0
        self.frame_counter = 0
        self.is_moving = False
        self.was_moving = False

    def update_animation(self):
        """Обновление анимации"""
        # Увеличиваем счетчик кадров
        self.frame_counter += 1

        # Если персонаж не двигается, проигрываем анимацию бездействия
        if not self.is_moving:
            # Меняем текстуру каждые UPDATES_PER_FRAME обновлений
            if self.frame_counter >= UPDATES_PER_FRAME:
                self.frame_counter = 0
                self.current_texture += 1

                # Циклически перебираем текстуры
                if self.current_texture >= len(self.idle_textures):
                    self.current_texture = 0

                # Устанавливаем текущую текстуру
                self.texture = self.idle_textures[self.current_texture]

        # Сбрасываем флаг движения для следующего кадра
        self.was_moving = self.is_moving
        self.is_moving = False

    def update(self):
        """Обновление положения с учетом границ экрана"""
        # Ограничение по левой границе
        if self.left < 0:
            self.left = 0

        # Ограничение по правой границе
        if self.right > SCREEN_WIDTH:
            self.right = SCREEN_WIDTH

        # Ограничение по нижней границе
        if self.bottom < 0:
            self.bottom = 0

        # Ограничение по верхней границе
        if self.top > SCREEN_HEIGHT:
            self.top = SCREEN_HEIGHT

        # Обновляем анимацию
        self.update_animation()


class MyGame(arcade.Window):
    """Основной класс игры"""

    def __init__(self):
        """Инициализация игры"""
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Черный фон
        arcade.set_background_color(arcade.color.BLACK)

        # Спрайт-листы
        self.hero_sprite = None
        self.hero_list = None

        # Переменные для управления
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

    def setup(self):
        """Настройка игры"""
        # Создаем спрайт-лист для героя
        self.hero_list = arcade.SpriteList()

        # Создаем героя
        self.hero_sprite = Hero()
        self.hero_list.append(self.hero_sprite)

    def on_draw(self):
        """Отрисовка игры"""
        # Очищаем экран
        self.clear()

        # Рисуем героя
        self.hero_list.draw()

        # Отображаем инструкции
        arcade.draw_text(
            "Управление: WASD",
            10, SCREEN_HEIGHT - 30,
            arcade.color.WHITE, 16
        )
        arcade.draw_text(
            "ESC - выход",
            10, SCREEN_HEIGHT - 60,
            arcade.color.WHITE, 16
        )
        arcade.draw_text(
            f"Позиция: ({int(self.hero_sprite.center_x)}, {int(self.hero_sprite.center_y)})",
            10, SCREEN_HEIGHT - 90,
            arcade.color.WHITE, 16
        )
        arcade.draw_text(
            f"Кадр анимации: {self.hero_sprite.current_texture + 1}/{len(self.hero_sprite.idle_textures)}",
            10, SCREEN_HEIGHT - 120,
            arcade.color.WHITE, 16
        )
        arcade.draw_text(
            f"Состояние: {'Двигается' if self.hero_sprite.was_moving else 'Стоит'}",
            10, SCREEN_HEIGHT - 150,
            arcade.color.GREEN if self.hero_sprite.was_moving else arcade.color.YELLOW,
            16
        )

    def on_update(self, delta_time):
        """Обновление логики игры"""
        # Сбрасываем скорость
        self.hero_sprite.change_x = 0
        self.hero_sprite.change_y = 0

        # Определяем, двигается ли персонаж
        is_moving = False

        # Устанавливаем скорость в зависимости от нажатых клавиш
        if self.up_pressed and not self.down_pressed:
            self.hero_sprite.change_y = MOVEMENT_SPEED
            is_moving = True
        elif self.down_pressed and not self.up_pressed:
            self.hero_sprite.change_y = -MOVEMENT_SPEED
            is_moving = True

        if self.left_pressed and not self.right_pressed:
            self.hero_sprite.change_x = -MOVEMENT_SPEED
            is_moving = True
        elif self.right_pressed and not self.left_pressed:
            self.hero_sprite.change_x = MOVEMENT_SPEED
            is_moving = True

        # Устанавливаем флаг движения
        self.hero_sprite.is_moving = is_moving

        # Обновляем положение героя
        self.hero_sprite.center_x += self.hero_sprite.change_x
        self.hero_sprite.center_y += self.hero_sprite.change_y

        # Проверяем границы и обновляем анимацию
        self.hero_sprite.update()

    def on_key_press(self, key, modifiers):
        """Обработка нажатия клавиш"""
        if key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.ESCAPE:
            arcade.close_window()

    def on_key_release(self, key, modifiers):
        """Обработка отпускания клавиш"""
        if key == arcade.key.W:
            self.up_pressed = False
        elif key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.D:
            self.right_pressed = False


def main():
    """Главная функция"""
    window = MyGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()