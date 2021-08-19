import pygame
from pygame.locals import *
import os
import random
import sys

START, PLAY, GAMEOVER, STAGECLEAR = (0, 1, 2, 3)  # Состояние игры
SCR_RECT = Rect(0, 0, 640, 480)


class Invader:
    def __init__(self):
        self.lives = 5  # Кол-во жизней
        self.wave = 1  # Номер волны
        self.counter = 0  # Это - счетчик времени, который помогает отсчитывать время
        # с его помощью создана задержка между стрельбой, появлением мобов и тд
        # 60 отсчетов - 1 секунда
        self.score = 0  # Счет игрока
        pygame.init()
        screen = pygame.display.set_mode(SCR_RECT.size)
        pygame.display.set_caption("Invader Game")
        # Загрузка спрайтов и звука
        self.load_images()
        self.load_sounds()
        # Инициализируем игру
        self.init_game()
        clock = pygame.time.Clock()
        # Начинаем цикл
        while True:
            clock.tick(60)
            self.update()
            self.draw(screen)
            pygame.display.update()
            self.key_handler()

    def init_game(self):
        # начинаем игру
        # создаем переменную для отслеживания состаояния игры
        self.game_state = START
        # создаем группы спрайтов
        self.all = pygame.sprite.RenderUpdates()
        self.invisible = pygame.sprite.RenderUpdates()
        self.aliens = pygame.sprite.Group()  # Спрайты пришельцев
        self.shots = pygame.sprite.Group()  # Спрайты с выстрелами
        self.beams = pygame.sprite.Group()  # спрайт лучей
        self.walls = pygame.sprite.Group()  # Спрайты со стенами
        self.ufos = pygame.sprite.Group()  # Спрайты с НЛО
        # регистрируем группы спрайтов, для того чтобы потом быстро к ним обратиться
        Player.containers = self.all
        Shot.containers = self.all, self.shots, self.invisible
        Alien.containers = self.all, self.aliens, self.invisible
        Beam.containers = self.all, self.beams, self.invisible
        Wall.containers = self.all, self.walls, self.invisible
        UFO.containers = self.all, self.ufos, self.invisible
        Explosion.containers = self.all, self.invisible
        ExplosionWall.containers = self.all, self.invisible
        # Создаем игрока
        self.player = Player()
        # создаем инопланетян с помощью цикла
        for i in range(0, 50):
            x = 20 + (i % 10) * 40  # их координаты по x
            y = 50 + (i // 10) * 40  # их координаты по y
            Alien((x, y), self.wave)  # создаем
        # создаем четыре стены за которыми
        # может укрыться игрок
        for i in range(4):
            x = 95 + i * 150  # координаты по x
            y = 400  # координаты по y
            Wall((x, y), self.wave)

    def update(self):
        # обновляем статус игры
        if self.game_state == PLAY:
            # задаем появление НЛО(каждые 15 секунд)
            self.counter += 1
            if self.counter == 900:
                UFO((20, 30), self.wave)

            self.all.update()
            # тут создано движение пришельцев по экран3
            # они плавно переходят слева направо, а после того как достигли конца экрана
            # начинают свое движение в противоположную сторону
            turn_flag = False
            for alien in self.aliens:
                if (alien.rect.center[0] < 15 and alien.speed < 0) or \
                        (alien.rect.center[0] > SCR_RECT.width - 15 and alien.speed > 0):
                    turn_flag = True
                    break
            if turn_flag:
                for alien in self.aliens:
                    alien.speed *= -1
            # エイリアンの追加ビーム判定（プレイヤーが近くにいると反応する）
            for alien in self.aliens:
                alien.shoot_extra_beam(self.player.rect.center[0], 32, 2)
            # проверка на попадание моба в стену
            self.collision_detection()
            # после уничтожения всех пришельцев переходим дальше
            if len(self.aliens.sprites()) == 0:  # проверяем длину спрайта. Если нулевая(мы всех убили)
                # меняем game_state и переходим дальше
                self.game_state = STAGECLEAR

    def draw(self, screen):  # функция рисования(рендеринга)
        screen.fill((0, 0, 0))
        if self.game_state == START:  # задаем стартовый экран перед началом игры:
            # название игры
            title_font = pygame.font.SysFont(None, 80)
            title = title_font.render("INVADER GAME", False, (255, 0, 0))
            screen.blit(title, ((SCR_RECT.width - title.get_width()) // 2, 100))
            # рисуем картинку инопланетянина на вступительном экране
            alien_image = Alien.images[0]
            screen.blit(alien_image, ((SCR_RECT.width - alien_image.get_width()) // 2, 200))
            # создаем очередную надпись на экране и размещаем...
            push_font = pygame.font.SysFont(None, 40)
            push_space = push_font.render("Press any key to continue", False, (255, 255, 255))
            screen.blit(push_space, ((SCR_RECT.width - push_space.get_width()) // 2, 300))  # координаты текста
            anotherFont = pygame.font.SysFont(None, 20)
            Font = anotherFont.render("Arrows - Movement, SPACE - Shooting", False, (255, 255, 255))
            screen.blit(Font, ((SCR_RECT.width - Font.get_width()) // 2, 380))  # координаты текста
        elif self.game_state == PLAY:  # переключаем game_state в значение PLAY
            # если в вас попали, то заставляем спрайт игрока мерцать
            # и даем ему неуязвимость на некоторое время
            # после отрисовываем все это на экране
            if self.player.invisible % 10 > 4:
                self.invisible.draw(screen)
            else:
                self.all.draw(screen)
            # Надпись с номером волны, количеством жизней и счетом
            stat_font = pygame.font.SysFont(None, 20)
            stat = stat_font.render("Wave:{:2d}  Lives:{:2d}  Score:{:05d}".format(
                self.wave, self.lives, self.score), False, (255, 255, 255))
            screen.blit(stat, ((SCR_RECT.width - stat.get_width()) // 2, 10))  # отражаем на экране
            # отображаем количество оставшихся жизней у стен
            # отрисовываем прямо на спрайте стены
            shield_font = pygame.font.SysFont(None, 30)
            for wall in self.walls:
                shield = shield_font.render(str(wall.shield), False, (0, 0, 0))
                text_size = shield_font.size(str(wall.shield))
                screen.blit(shield, (wall.rect.center[0] - text_size[0] // 2,
                                     wall.rect.center[1] - text_size[1] // 2))
        elif self.game_state == GAMEOVER:  # Экран окончания игры
            # Надпись GAME OVER
            gameover_font = pygame.font.SysFont(None, 80)
            gameover = gameover_font.render("GAME OVER", False, (255, 0, 0))
            screen.blit(gameover, ((SCR_RECT.width - gameover.get_width()) // 2, 100))
            # Снова рисуем спрайт инопланетянина
            alien_image = Alien.images[0]
            screen.blit(alien_image, ((SCR_RECT.width - alien_image.get_width()) // 2, 200))
            # Нажмите кнопку для продолжения...
            push_font = pygame.font.SysFont(None, 40)
            push_space = push_font.render("PUSH SPACE KEY", False, (255, 255, 255))
            screen.blit(push_space, ((SCR_RECT.width - push_space.get_width()) // 2, 300))

        elif self.game_state == STAGECLEAR:
            # Экран STAGE CLEAR, который появляется после зачистки уровня
            stat_font = pygame.font.SysFont(None, 20)
            stat = stat_font.render("Wave:{:2d}  Lives:{:2d}  Score:{:05d}".format(
                self.wave, self.lives, self.score), False, (255, 255, 255))
            screen.blit(stat, ((SCR_RECT.width - stat.get_width()) // 2, 10))
            # надпись STAGE CLEAR
            gameover_font = pygame.font.SysFont(None, 80)
            gameover = gameover_font.render("STAGE CLEAR", False, (255, 0, 0))
            screen.blit(gameover, ((SCR_RECT.width - gameover.get_width()) // 2, 100))
            alien_image = Alien.images[0]
            screen.blit(alien_image, ((SCR_RECT.width - alien_image.get_width()) // 2, 200))
            push_font = pygame.font.SysFont(None, 40)
            push_space = push_font.render("PUSH SPACE KEY", False, (255, 255, 255))
            screen.blit(push_space, ((SCR_RECT.width - push_space.get_width()) // 2, 300))

    def key_handler(self):  # Тут я создаю функцию обрабатывания ключей(событий) pygame
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN and event.key == K_SPACE:
                if self.game_state == START:  # Нажатие кнопки или пробела на стартавом экране переводит
                    # game_state в состояние старт и начинается игра
                    self.game_state = PLAY
                elif self.game_state == GAMEOVER:  # конец игры
                    self.score = 0  # инициализация счета
                    self.wave = 1  # волна(начинается с первой)
                    self.lives = 5  # кол-во жизней игрока
                    self.counter = 0
                    self.init_game()  # перезапустаем игру
                    self.game_state = PLAY
                elif self.game_state == STAGECLEAR:  # Если волна отбита, то увеличиваем номер волны
                    # кол-во жизней игрока и снова переводим game_stage в состояние PLAY
                    self.wave += 1
                    self.lives += 1
                    self.counter = 0
                    self.init_game()
                    self.game_state = PLAY

    def collision_detection(self):  # Функция, фиксирующая столкновение(попадание) пули пришельца(моба) в игрока
        # или наоборот
        alien_collided = pygame.sprite.groupcollide(self.aliens, self.shots, True, True)  # проверяем это
        # с помощью функции pygame groupcollide
        for alien in alien_collided.keys():
            Alien.kill_sound.play()  # звук попадания
            self.score += 10 * self.wave  # прибавка к счету
            Explosion(alien.rect.center)  # Создаем взрыв из последовательности анимированных спрайтов
            # создаем его в центре пришельца
        #  Звук попадания в НЛО
        ufo_collided = pygame.sprite.groupcollide(self.ufos, self.shots, True, True)
        for ufo in ufo_collided.keys():
            Alien.kill_sound.play()  # звук попадания
            self.score += 50 * self.wave  # прибавка к счету
            Explosion(ufo.rect.center)
            self.lives += 1  # если попали в НЛО, то прибавляем еще и кол-во жизней игрока
            # это как бы своеобразный бонус игроку
        #         # проверяем, прошло ли нужное количество времени с момента прошлого попадания в игрока
        #         # если это так, то не засчитываем попадание(тк игрока был в режиме невесомости или невидимости для
        # выстрелов врага
        if self.player.invisible > 0:
            beam_collided = False
            self.player.invisible -= 1
        else:
            beam_collided = pygame.sprite.spritecollide(self.player, self.beams, True)
        if beam_collided:  # Если все верно и пуля все таки попала в игрока в правильный момент времени:
            Player.bomb_sound.play()  # Активируем звук взрыва(звук попадания в игрока)
            Explosion(self.player.rect.center)
            self.lives -= 1  # отнимаем одну жизнь
            self.player.invisible = 180  # Время невесомости игрока - 180, то есть 3 секунды
            if self.lives < 0:
                self.game_state = GAMEOVER  # Если жизней не остается, то переводим игру в состояние GAMEOVER
        # Определяем, попала ли пуля в стену
        hit_dict = pygame.sprite.groupcollide(self.walls, self.shots, False, True)
        hit_dict.update(pygame.sprite.groupcollide(self.walls, self.beams, False, True))
        for hit_wall in hit_dict:
            hit_wall.shield -= len(hit_dict[hit_wall])
            for hit_beam in hit_dict[hit_wall]:
                Alien.kill_sound.play()
                Explosion(hit_beam.rect.center)  # Если попадание есть(как со стороны игрока, так и со стороны
                # противника), то превращаем спрайт пули в взрыв для эффектности
            if hit_wall.shield <= 0:  # Если здоровья у стены совсем не остается, то просто уничтожаем её
                # теперь там появится пустое пространство , что может стать опасным для игрока
                hit_wall.kill()
                Alien.kill_sound.play()
                ExplosionWall(hit_wall.rect.center)  # Взрыв отрисовываем в самом центре стены

    def load_images(self):
        # Загружаем все нужные нам изображения
        # И создаем группы со спрайтами
        Player.image = load_image("Data/player.png")
        Shot.image = load_image("Data/shot.png")
        Alien.images = split_image(load_image("Data/alien.png"), 2)
        UFO.images = split_image(load_image("Data/ufo.png"), 2)
        Beam.image = load_image("Data/beam.png")
        Wall.image = load_image("Data/wall.png")
        Explosion.images = split_image(load_image("Data/explosion.png"), 16)
        ExplosionWall.images = split_image(load_image("Data/explosion2.png"), 16)

    def load_sounds(self):
        # Загружаем звуки
        Alien.kill_sound = load_sound("kill.wav")
        Player.shot_sound = load_sound("shot.wav")
        Player.bomb_sound = load_sound("bomb.wav")

class Player(pygame.sprite.Sprite):
    # Класс игрока
    speed = 5  # его скорость
    reload_time = 15  # время между выстрелами(не в секундах)
    invisible = 0  # и начальное значение невесомости, то есть False(0)

    def __init__(self):
        # устанавливаем спрайт игрока
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.rect = self.image.get_rect()
        self.rect.bottom = SCR_RECT.bottom
        self.reload_timer = 0

    def update(self):
        # проверяем нажатые клавиши
        pressed_keys = pygame.key.get_pressed()
        # проверяем нажатие клавиши
        # перемещаем игрока при нажатии
        if pressed_keys[K_LEFT]:
            self.rect.move_ip(-self.speed, 0)
        elif pressed_keys[K_RIGHT]:
            self.rect.move_ip(self.speed, 0)  # двигает объект в какую-либо область
        self.rect.clamp_ip(SCR_RECT)  # перемещает объект внутрь другого
        # проверяем нажат ли пробел
        # если да - то стреляем
        if pressed_keys[K_SPACE]:
            # провеяем время, прошедшее с момента прошлого выстрела
            if self.reload_timer > 0:
                # если оно есть, перезагружаем и даем снова выстрельнуть
                self.reload_timer -= 1
            else:
                # стрельба
                Player.shot_sound.play()
                Shot(self.rect.center)  # добавляем вылет пули к спрайту игрока и таким образом стреляем
                self.reload_timer = self.reload_time


class Alien(pygame.sprite.Sprite):
    # класс пришельца

    def __init__(self, pos, wave):
        self.speed = 1 + wave  # скорость движения. Постепенно увеличивается с увеличением волны
        self.animcycle = 18  # скорость анимации
        self.frame = 0
        self.prob_beam = (1.5 + wave) * 0.002  # вероятность выстреливания лучом. Луч - не обычная пуля,
        # это снаряд который намного сильнее него, но шанс на появление довольно мал
        # Подгружаем спрайт пришельца
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos

    def update(self):
        # движение
        self.rect.move_ip(self.speed, 0)
        if random.random() < self.prob_beam:  # Стрельба
            Beam(self.rect.center)
        # анимация пришельца
        self.frame += 1
        self.image = self.images[self.frame // self.animcycle % 2]

    def shoot_extra_beam(self, target_x_pos, border_dist, rate):  # Стрельба
        if random.random() < self.prob_beam * rate and \
                abs(self.rect.center[0] - target_x_pos) < border_dist:
            Beam(self.rect.center)


class UFO(pygame.sprite.Sprite):
    # Класс НЛО - другого противника в игре, встречающегося в виде бонуса

    def __init__(self, pos, wave):
        self.speed = 1 + wave // 2  # скорость
        # if side => 0:
        #     left, 1: right
        side = 0 if random.random() < 0.5 else 1
        if side:
            self.speed *= -1  # появление на экране - случайно, поэтому если она появляется справа, то скорость нужно
            # изменить на противоположную, чтобы тарелка двигалась в противоположную сторону
        self.animcycle = 18  # скорость анимации
        self.frame = 0
        # загружаем спрайт НЛО
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = (SCR_RECT.width - pos[0] if side else pos[0], pos[1])  # начальная позиция по x
        self.pos_kill = pos[0] if side else SCR_RECT.width - pos[0]  # позиция исчезновения

    def update(self):
        # боковое движение
        self.rect.move_ip(self.speed, 0)
        # при достижении края экрана исчезает
        if (self.rect.center[0] > self.pos_kill and self.speed > 0) or \
                (self.rect.center[0] < self.pos_kill and self.speed < 0):
            self.kill()  # проверяем это и убираем спрайт, без бонуса игроку
        # анимация картинки
        self.frame += 1
        self.image = self.images[int(self.frame // self.animcycle % 2)]


class Shot(pygame.sprite.Sprite):
    # Класс выстрелов ИГРОКА !!!
    speed = 12  # скорость полета пули

    def __init__(self, pos):
        # загружаем изображение пули
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.rect = self.image.get_rect()
        self.rect.center = pos  # координаты пули - координаты центра игрока

    def update(self):
        self.rect.move_ip(0, -self.speed)  # при выстреле перемещаем пулю вверх
        if self.rect.top < 0:  # удаляем при достижении вершины экрана
            self.kill()


class Beam(pygame.sprite.Sprite):
    # Класс луча
    speed = 5  # скорость

    def __init__(self, pos):
        # загружаем спрайт
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.rect = self.image.get_rect()
        self.rect.center = pos

    def update(self):
        self.rect.move_ip(0, self.speed)  # луч должен двигаться вниз. Задаем его движение
        if self.rect.bottom > SCR_RECT.height:  # при достижении дна экрана, луч удаляется
            self.kill()


class Explosion(pygame.sprite.Sprite):
    # Класс эффекта взрыва
    animcycle = 2  # скорость анимации
    frame = 0

    def __init__(self, pos):
        # загружаем спрайт взрыва
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.max_frame = len(self.images) * self.animcycle  # устанавливаем исчезающую рамку

    def update(self):
        # анимация взрыва. Постепенная замена спрайтов последовательно
        self.image = self.images[self.frame // self.animcycle]
        self.frame += 1
        if self.frame == self.max_frame:
            self.kill()  # Когда анимация завершится, удаляем спрайт


class ExplosionWall(Explosion):
    pass


class Wall(pygame.sprite.Sprite):
    # Класс стены

    def  __init__(self, pos, wave):
        self.shield = 80 + 20 * wave  # Задаем прочность
        # Загружаем спрайт
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.rect = self.image.get_rect()
        self.rect.center = pos

    def update(self):
        pass



def load_image(filename, colorkey=None):
    # Функиця загрузки изображения
    filenmae = os.path.join("data", filename)
    try:
        image = pygame.image.load(filename)
    except pygame.error as message:
        print("Не удалось загрузить картинку:", filename)
        raise SystemExit(message)
    image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image


def split_image(image, n):
    # разделяем изображения по горизонтали на n изображений,
    # возвращаем список разделенных изображкний
    image_list = []
    w = image.get_width()
    h = image.get_height()
    w1 = w // n
    for i in range(0, w, w1):
        surface = pygame.Surface((w1, h))
        surface.blit(image, (0, 0), (i, 0, w1, h))
        surface.set_colorkey(surface.get_at((0, 0)), RLEACCEL)
        surface.convert()
        image_list.append(surface)
    return image_list



def load_sound(filename):
    # Загружаем звук
    filename = os.path.join("Data", filename)
    return pygame.mixer.Sound(filename)


if __name__ == "__main__":
    Invader()  # И, наконец, запускаем главный класс всей программы. Игра началась!
