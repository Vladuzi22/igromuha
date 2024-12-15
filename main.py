import pygame
import sys

from pygame.locals import *
import math
import os
import ctypes
import time

pygame.init()
font = pygame.font.Font(None, 36)
pygame.mixer.init()

font = pygame.font.Font(None, 50)

pygame.mixer.music.load('joc.mp3')
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

click_sound = pygame.mixer.Sound('patron.mp3')
click_sound.set_volume(0.5)  # Setează volumul

WIDTH, HEIGHT = 800, 600
MAP_WIDTH, MAP_HEIGHT = 2200, 2200

background_image = pygame.image.load('background_image.png')
background_image = pygame.transform.smoothscale(background_image, (WIDTH, HEIGHT))

FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (50, 50, 50)
LIGHT_BLUE = (0, 150, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (150, 0, 150)
DARK_BLUE = (0, 100, 200)
DARK_GRAY = (30, 30, 30)
DARK_RED = (139, 0, 0)
DARK_BROWN = (101, 67, 33)
BLUE = (0, 0, 255)

user32 = ctypes.windll.user32
screen_width, screen_height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
os.environ['SDL_VIDEO_WINDOW_POS'] = f'{(screen_width - WIDTH) // 2},{(screen_height - HEIGHT) // 2}'

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("IgroMuha")
clock = pygame.time.Clock()

square_width, square_height = 100, 50
square_padding = 10
square_1_pos = ((WIDTH // 2) - square_width - square_padding, HEIGHT - square_height - 20)
square_2_pos = ((WIDTH // 2) + square_padding, HEIGHT - square_height - 20)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Încarcă imaginea PNG a jucătorului
        self.original_image = pygame.image.load("player.png").convert_alpha()

        # Redimensionează imaginea la o dimensiune mai mică (ex. 30x30 pixeli)
        self.original_image = pygame.transform.scale(self.original_image, (60, 60))

        self.image = self.original_image
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 3
        self.health = 100
        self.ammo_9mm = 70  # Initializează muniția de 9mm
        self.ammo_55mm = 30  # Initializează muniția de 5.5mm
        self.selected_ammo = '9mm'  # Începe cu muniția de 9mm

    def update(self, keys, mouse_pos, walls):
        dx, dy = 0, 0
        if keys[K_w]:
            dy = -self.speed
        if keys[K_s]:
            dy = self.speed
        if keys[K_a]:
            dx = -self.speed
        if keys[K_d]:
            dx = self.speed

        self.rect.x += dx
        if pygame.sprite.spritecollide(self, walls, False) or pygame.sprite.spritecollide(self, barriers, False):
            self.rect.x -= dx

        self.rect.y += dy
        if pygame.sprite.spritecollide(self, walls, False) or pygame.sprite.spritecollide(self, barriers, False):
            self.rect.y -= dy

        self.rotate_towards(mouse_pos)

        # Menține jucătorul în interiorul granițelor hărții
        self.rect.x = max(0, min(MAP_WIDTH - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(MAP_HEIGHT - self.rect.height, self.rect.y))

    def rotate_towards(self, mouse_pos):
        # Ajustăm mouse_pos pentru a ține cont de poziția camerei
        mouse_x, mouse_y = mouse_pos
        world_mouse_x = mouse_x - camera.camera.x
        world_mouse_y = mouse_y - camera.camera.y

        # Calculăm direcția relativă către mouse în coordonate globale
        rel_x, rel_y = world_mouse_x - self.rect.centerx, world_mouse_y - self.rect.centery
        angle = math.degrees(math.atan2(-rel_y, rel_x)) - 360

        # Rotim imaginea PNG
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, camera, ammo_type='9mm'):
        super().__init__()

        # Design pentru dimensiuni și culori gloanțe
        if ammo_type == '9mm':
            self.image = pygame.Surface((2, 5), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (255, 255, 0), (0, 0, 2, 3))  # Rect galben
            pygame.draw.polygon(self.image, (255, 0, 0), [(0, 3), (2, 3), (1, 5)])  # Triunghi roșu
            speed = 8
        elif ammo_type == '55mm':
            self.image = pygame.Surface((3, 9), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (0, 0, 255), (0, 0, 3, 6))  # Rect albastru
            pygame.draw.polygon(self.image, (0, 255, 0), [(0, 6), (3, 6), (1.5, 9)])  # Triunghi verde
            speed = 10

        # Ajustează coordonate mouse țintă conform camerei
        world_target_x = target_x - camera.camera.x  # Elimină offset-ul camerei
        world_target_y = target_y - camera.camera.y

        # Direcția spre mouse
        dx = world_target_x - x
        dy = world_target_y - y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        bullet_dir_x = dx / distance
        bullet_dir_y = dy / distance

        # Offset pentru mâna stângă (glonț tras din mâna stângă)
        hand_offset_x = -20 * bullet_dir_y
        hand_offset_y = 20 * bullet_dir_x
        bullet_start_x = x + hand_offset_x
        bullet_start_y = y + hand_offset_y

        # Poziția inițială și viteza glonțului
        self.rect = self.image.get_rect(center=(bullet_start_x, bullet_start_y))
        self.dx = bullet_dir_x * speed
        self.dy = bullet_dir_y * speed

    def update(self, walls):
        # Actualizează poziția glonțului
        self.rect.x += self.dx
        self.rect.y += self.dy

        # Elimină glonțul dacă iese din hartă
        if self.rect.right < 0 or self.rect.left > MAP_WIDTH or self.rect.top < 0 or self.rect.bottom > MAP_HEIGHT:
            self.kill()

        # Distruge glonțul la coliziune cu zidurile
        if pygame.sprite.spritecollide(self, walls, False):
            self.kill()


# Clasă pentru pereți
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect(topleft=(x, y))


class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + WIDTH // 2
        y = -target.rect.centery + HEIGHT // 2

        # Limite camera la granițele hărții
        x = max(-(self.width - WIDTH), min(0, x))
        y = max(-(self.height - HEIGHT), min(0, y))

        self.camera = pygame.Rect(x, y, self.width, self.height)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=2):
        super().__init__()
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.health = 50
        self.speed = speed

        self.color_main = RED
        self.color_shadow = DARK_RED

        pygame.draw.circle(self.image, self.color_shadow, (20, 24), 20)
        pygame.draw.circle(self.image, self.color_main, (20, 20), 20)

    def update(self, player, walls, barriers):
        dx, dy = self.get_direction_to_player(player)

        if dx != 0 or dy != 0:
            self.rect.x += dx * self.speed
            if pygame.sprite.spritecollide(self, walls, False) or pygame.sprite.spritecollide(self, barriers, False):
                self.rect.x -= dx * self.speed
                if pygame.sprite.spritecollide(self, walls, False) or pygame.sprite.spritecollide(self, barriers, False):
                    self.rect.y += dy * self.speed
                    if pygame.sprite.spritecollide(self, walls, False) or pygame.sprite.spritecollide(self, barriers, False):
                        self.rect.y -= dy * self.speed

            else:
                self.rect.y += dy * self.speed
                if pygame.sprite.spritecollide(self, walls, False):
                    self.rect.y -= dy * self.speed

        self.rotate_towards(player.rect.center)

    def get_direction_to_player(self, player):
        dx = 0
        dy = 0
        if self.rect.x < player.rect.x:
            dx = 1
        elif self.rect.x > player.rect.x:
            dx = -1

        if self.rect.y < player.rect.y:
            dy = 1
        elif self.rect.y > player.rect.y:
            dy = -1

        return dx, dy

    def rotate_towards(self, target_pos):
        target_x, target_y = target_pos
        rel_x, rel_y = target_x - self.rect.centerx, target_y - self.rect.centery
        angle = math.degrees(math.atan2(-rel_y, rel_x)) - 90

        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color_shadow, (20, 24), 20)
        pygame.draw.circle(self.image, self.color_main, (20, 20), 20)

        pygame.draw.rect(self.image, GRAY, (10, 6, 8, 20))
        pygame.draw.rect(self.image, WHITE, (6, -10, 4, 20))

        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)


class HealthPack(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((34, 34), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.color = GREEN
        self.bg_color = WHITE
        self.border_color = RED

        pygame.draw.rect(self.image, self.border_color, self.image.get_rect(), 4)
        inner_rect = pygame.Rect(4, 4, 26, 26)
        pygame.draw.rect(self.image, self.bg_color, inner_rect)
        plus_thickness = 5
        pygame.draw.rect(self.image, self.color, (15, 8, plus_thickness, 18))
        pygame.draw.rect(self.image, self.color, (8, 15, 18, plus_thickness))


class AmmoPack(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 35), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.color = (255, 223, 0)  # Galben

        # Desenează cutia galbenă
        pygame.draw.rect(self.image, self.color, (0, 0, 30, 30))

        bullet_color = (255, 0, 0)  # Negru
        bullet_width = 5
        bullet_height = 15

        bullets = [(5, 12), (12, 12), (19, 12)]

        for bullet_x, bullet_y in bullets:
            pygame.draw.rect(self.image, bullet_color, (bullet_x, bullet_y, bullet_width, bullet_height))

            pygame.draw.polygon(
                self.image,
                bullet_color,
                [
                    (bullet_x, bullet_y),  # Stânga sus
                    (bullet_x + bullet_width, bullet_y),  # Dreapta sus
                    (bullet_x + bullet_width // 2, bullet_y - 5)  # Vârf ascuțit
                ]
            )


class Trap(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.color = PURPLE

        points = [(0, 15), (5, 10), (10, 15), (15, 10), (20, 15), (25, 10), (30, 15), (25, 20), (20, 15), (15, 20),
                  (10, 15), (5, 20)]
        pygame.draw.polygon(self.image, self.color, points)


class SpeedBoost(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 34), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.color = YELLOW

        pygame.draw.rect(self.image, self.color, (5, 0, 10, 30))
        pygame.draw.rect(self.image, RED, (7, 5, 6, 20))
        pygame.draw.rect(self.image, BLACK, (8, 5, 4, 2))
        pygame.draw.rect(self.image, BLACK, (8, 10, 4, 2))
        pygame.draw.rect(self.image, BLACK, (8, 15, 4, 2))


class Barricade(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, durability=3):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((0, 0, 0))  # Culoare neagră
        self.rect = self.image.get_rect(topleft=(x, y))
        self.durability = durability  # Numărul de vieți ale baricadei

    def take_damage(self):
        """Reduce durabilitatea baricadei când este lovită de un glonț."""
        self.durability -= 1
        if self.durability <= 0:
            self.kill()  # Distruge baricada


class Effect(pygame.sprite.Sprite):
    POSITIONS = [
        (0, -40),  # Above the player
        (-30, -20),  # Top-left of the player
        (30, -20)  # Top-right of the player
    ]

    def __init__(self, x, y, text, color, index):
        super().__init__()
        self.image = pygame.Surface((60, 20), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x + self.POSITIONS[index][0], y + self.POSITIONS[index][1]))
        font = pygame.font.Font(None, 36)
        render = font.render(text, True, color)
        self.image.blit(render, (0, 0))
        self.creation_time = pygame.time.get_ticks()

    def update(self):
        # Remove the effect after 1 second
        if pygame.time.get_ticks() - self.creation_time > 1000:
            self.kill()


def create_radial_gradient_optimized(buffer_size, screen_width, screen_height, color_center, color_edge):
    buffer_surface = pygame.Surface((buffer_size, buffer_size), pygame.SRCALPHA)
    center_x, center_y = buffer_size // 2, buffer_size // 2
    max_radius = math.hypot(center_x, center_y)

    for y in range(buffer_size):
        for x in range(buffer_size):
            distance = math.hypot(center_x - x, center_y - y)
            ratio = min(distance / max_radius, 1)
            r = (1 - ratio) * color_center[0] + ratio * color_edge[0]
            g = (1 - ratio) * color_center[1] + ratio * color_edge[1]
            b = (1 - ratio) * color_center[2] + ratio * color_edge[2]
            a = (1 - ratio) * color_center[3] + ratio * color_edge[3]
            buffer_surface.set_at((x, y), (int(r), int(g), int(b), int(a)))

    return pygame.transform.smoothscale(buffer_surface, (screen_width, screen_height))


def load_level(level_data):
    walls = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    health_packs = pygame.sprite.Group()
    traps = pygame.sprite.Group()
    speed_boosts = pygame.sprite.Group()
    ammo_packs = pygame.sprite.Group()
    barriers = pygame.sprite.Group()

    for item in level_data['walls']:
        wall = Wall(*item)
        walls.add(wall)
        all_sprites.add(wall)

    for item in level_data['enemies']:
        if len(item) == 3:
            enemy = Enemy(*item)
        else:
            enemy = Enemy(item[0], item[1])
        enemies.add(enemy)
        all_sprites.add(enemy)

    for item in level_data['health_packs']:
        health_pack = HealthPack(*item)
        health_packs.add(health_pack)
        all_sprites.add(health_pack)

    for item in level_data['traps']:
        trap = Trap(*item)
        traps.add(trap)
        all_sprites.add(trap)

    for item in level_data['speed_boosts']:
        boost = SpeedBoost(*item)
        speed_boosts.add(boost)
        all_sprites.add(boost)

    for item in level_data['ammo_packs']:
        ammo_pack = AmmoPack(*item)
        ammo_packs.add(ammo_pack)  # Add to ammo pack group
        all_sprites.add(ammo_pack)  # Add to all sprites for rendering

    for item in level_data['barriers']:
        barricade = Barricade(*item)
        barriers.add(barricade)
        all_sprites.add(barricade)

    return walls, enemies, health_packs, traps, speed_boosts, ammo_packs, barriers
def draw_button(text, position, font, color, text_color, hover_color, hover=False):
    """Funcția ta pentru a desena butoane cu suport hover"""
    x, y = position
    button_width, button_height = 200, 50

    button_color = hover_color if hover else color
    pygame.draw.rect(screen, button_color, (x, y, button_width, button_height), border_radius=10)

    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x + button_width // 2, y + button_height // 2))
    screen.blit(text_surface, text_rect)

    return pygame.Rect(x, y, button_width, button_height)

def draw_text(surface, text, font, color, rect, align="center"):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if align == "center":
        text_rect.center = rect.center
    elif align == "topleft":
        text_rect.topleft = rect.topleft
    surface.blit(text_surface, text_rect)


def show_next_level_menu(level_number):
    pygame.mouse.set_visible(True)
    global is_in_menu
    is_in_menu = True  # Suntem într-un meniu

    # Titlul meniu în galben
    title_font = pygame.font.Font(None, 100)
    title_surface = title_font.render(f"Уровень {level_number} пройден!", True, (255, 215, 0))
    title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70))

    instruction_font = pygame.font.Font(None, 50)
    instruction_surface = instruction_font.render("Нажмите Enter, чтобы продолжить", True, (245, 245, 245))
    instruction_rect = instruction_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))

    screen.fill((0, 0, 0))
    pygame.draw.rect(screen, (30, 30, 30), title_rect.inflate(20, 20))
    pygame.draw.rect(screen, (30, 30, 30), instruction_rect.inflate(20, 20))

    screen.blit(title_surface, title_rect)
    screen.blit(instruction_surface, instruction_rect)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                waiting = False
                is_in_menu = False  # Ieșim din meniu, se continuă jocul

# Variabilă globală pentru culoarea de fundal
CURRENT_BG_COLOR_INDEX = 0  # Index-ul culorii curente


def draw_slider(label, position, value, font, color, bg_color):
    """Funcție pentru slider"""
    slider_rect = pygame.Rect(position[0], position[1], 200, 20)
    knob_rect = pygame.Rect(position[0] + int(value * 200) - 10, position[1] - 5, 20, 30)

    pygame.draw.rect(screen, bg_color, slider_rect)
    pygame.draw.rect(screen, color, knob_rect)

    label_surface = font.render(f"{label}: {int(value * 100)}%", True, (255, 255, 255))
    screen.blit(label_surface, (position[0], position[1] - 30))

    return slider_rect, knob_rect


def draw_color_picker(label, position, options, selected_index, font):
    """Funcție pentru selectorul de culoare"""
    label_surface = font.render(label, True, (255, 255, 255))
    screen.blit(label_surface, (position[0], position[1] - 30))

    color_boxes = []
    for i, color in enumerate(options):
        box_position = (position[0] + i * 50, position[1])
        box_rect = pygame.Rect(box_position[0], box_position[1], 40, 40)

        pygame.draw.rect(screen, color, box_rect)
        if i == selected_index:  # Evidențiere dacă este selectat
            pygame.draw.rect(screen, (255, 255, 255), box_rect, 3)
        color_boxes.append((color, box_rect))

    return color_boxes


def draw_button1(text, position, font, color, text_color, hover_color=None, hover=False):
    """Funcție pentru desenarea butoanelor."""
    button_rect = pygame.Rect(position[0], position[1], 200, 50)
    if hover and hover_color:
        pygame.draw.rect(screen, hover_color, button_rect)
    else:
        pygame.draw.rect(screen, color, button_rect)

    text_surface = font.render(text, True, text_color)
    text_x = position[0] + (button_rect.width - text_surface.get_width()) // 2
    text_y = position[1] + (button_rect.height - text_surface.get_height()) // 2
    screen.blit(text_surface, (text_x, text_y))

    return button_rect


def show_settings():
    global WIDTH, HEIGHT, screen, CURRENT_BG_COLOR_INDEX

    # Oprește muzica de fundal înainte de a intra în meniul de setări
    if pygame.mixer.music.get_busy():  # Verifică dacă muzica e redată
        pygame.mixer.music.pause()

    font_buttons = pygame.font.Font(None, 50)
    font_small = pygame.font.Font(None, 30)

    dropdown_button_position = (WIDTH // 2 - 100, 100)
    dropdown_open = False

    # Butoane pentru rezoluție
    resolutions = [
        ("Auto", None),  # Dimensiune automată (rezoluția ecranului curent)
        ("Fullscreen", "fullscreen"),
        ("800x600", (800, 600)),
        ("1024x768", (1024, 768)),
        ("1280x720", (1280, 720)),
        ("1920x1080", (1920, 1080)),
    ]

    slider_volume_value = pygame.mixer.music.get_volume()  # Preluăm volumul curent al muzicii
    bg_colors = [(0, 0, 0), (255, 255, 0), (100, 100, 100), (255, 0, 0), (0, 255, 0), (0, 0, 255)]
    current_color_index = CURRENT_BG_COLOR_INDEX  # Utilizăm valoarea salvată

    dropdown_rects = []  # Pentru dropdown
    slider_dragging = False  # Indică dacă sliderul este în proces de drag
    waiting = True
    while waiting:
        mouse_position = pygame.mouse.get_pos()
        dropdown_offset = len(
            resolutions) * 60 if dropdown_open else 0  # Calculăm un offset dacă dropdown-ul este deschis
        dropdown_button_height = dropdown_offset + 100  # Înălțimea ajustată pentru dropdown

        # Actualizează interfața
        screen.fill(bg_colors[current_color_index])  # Fundalul folosește culoarea curentă
        dropdown_text = "< Resolution" if dropdown_open else "> Resolution"
        dropdown_hover = dropdown_button_position[0] <= mouse_position[0] <= dropdown_button_position[0] + 200 and \
                         dropdown_button_position[1] <= mouse_position[1] <= dropdown_button_position[1] + 50

        dropdown_rect = draw_button1(
            dropdown_text, dropdown_button_position, font_buttons, (0, 255, 0), (255, 255, 255), (0, 100, 0),
            hover=dropdown_hover
        )

        # Dropdown pentru selecția rezoluției
        if dropdown_open:
            dropdown_rects = []  # Resetăm dropdown-ul
            for i, (label, _) in enumerate(resolutions):
                option_position = (dropdown_button_position[0], dropdown_button_position[1] + (i + 1) * 60)
                option_hover = option_position[0] <= mouse_position[0] <= option_position[0] + 200 and \
                               option_position[1] <= mouse_position[1] <= option_position[1] + 50
                option_rect = draw_button1(
                    label, option_position, font_buttons, (50, 50, 50), (255, 255, 255), (100, 100, 100),
                    hover=option_hover
                )
                dropdown_rects.append((label, option_rect))

        # Slider pentru volum
        slider_position = (
        WIDTH // 2 - 100, dropdown_button_position[1] + dropdown_offset + 80)  # Calculator de poziție dinamică
        slider_rect, knob_rect = draw_slider("Volume", slider_position, slider_volume_value, font_small, (0, 255, 0),
                                             (255, 255, 255))

        # Selector de culoare
        color_picker_position = (WIDTH // 2 - 150, slider_position[1] + 100)
        color_boxes = draw_color_picker("BG Color", color_picker_position, bg_colors, current_color_index, font_small)

        # Buton "Back" mutat dinamic
        back_button_position = (WIDTH // 2 - 100, color_picker_position[1] + 100)
        back_hover = back_button_position[0] <= mouse_position[0] <= back_button_position[0] + 200 and \
                     back_button_position[1] <= mouse_position[1] <= back_button_position[1] + 50
        draw_button1("Back", back_button_position, font_buttons, (255, 0, 0), (255, 255, 255), (100, 0, 0),
                     hover=back_hover)

        pygame.display.flip()

        # Gestionăm evenimentele
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Marcare slider ca fiind "dragging"
                if knob_rect.collidepoint(event.pos):
                    slider_dragging = True

                if dropdown_rect.collidepoint(event.pos):
                    dropdown_open = not dropdown_open

                # Selectare opțiune dropdown
                if dropdown_open:
                    for label, rect in dropdown_rects:
                        if rect.collidepoint(event.pos):
                            if label == "Auto":
                                info = pygame.display.Info()
                                WIDTH, HEIGHT = info.current_w, info.current_h
                                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                            elif label == "Fullscreen":
                                screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                            else:  # Rezoluție selectată
                                dims = next((res for res in resolutions if res[0] == label), None)
                                if dims and dims[1]:
                                    WIDTH, HEIGHT = dims[1]
                                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                            dropdown_open = False

                # Schimbare culoare fundal
                for index, (_, rect) in enumerate(color_boxes):
                    if rect.collidepoint(event.pos):
                        current_color_index = index

                # Click pe "Back"
                if back_hover:
                    CURRENT_BG_COLOR_INDEX = current_color_index
                    waiting = False

            if event.type == pygame.MOUSEBUTTONUP:
                slider_dragging = False

            if event.type == pygame.MOUSEMOTION and slider_dragging:
                # Mutăm slider-ul odată cu mouse-ul
                slider_volume_value = (mouse_position[0] - slider_position[0]) / 200.0
                slider_volume_value = max(0, min(1, slider_volume_value))
                pygame.mixer.music.set_volume(slider_volume_value)

    # Reluăm muzica când ieșim din setări
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.unpause()


            # Mutarea sliderului (mouse motion)
        if event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                if knob_rect.collidepoint(event.pos):
                    slider_volume_value = (event.pos[0] - slider_position[0]) / 200.0
                    slider_volume_value = max(0, min(1, slider_volume_value))
                    pygame.mixer.music.set_volume(slider_volume_value)

    # Reluăm muzica de fundal la ieșirea din meniul de setări
    if not pygame.mixer.music.get_busy():  # Verificăm dacă muzica a fost întreruptă
        pygame.mixer.music.unpause()


def show_menu(text, is_game_over=False):
    global is_in_menu
    is_in_menu = True  # Suntem într-un meniu

    font = pygame.font.Font(None, 74)
    screen.fill(BLACK)

    font_title = pygame.font.Font(None, 74)
    font_decor = pygame.font.Font(None, 150)
    font_buttons = pygame.font.Font(None, 50)

    title_text = font_title.render(text, True, DARK_RED)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))

    left_decor = font_decor.render("&", True, WHITE)
    right_decor = font_decor.render("&", True, WHITE)

    left_decor_rect = left_decor.get_rect(center=(title_rect.left - 50, HEIGHT // 4))
    right_decor_rect = right_decor.get_rect(center=(title_rect.right + 50, HEIGHT // 4))

    start_button = (WIDTH // 2 - 100, HEIGHT // 2 - 20)
    settings_button = (WIDTH // 2 - 100, HEIGHT // 2 + 60)
    exit_button = (WIDTH // 2 - 100, HEIGHT // 2 + 140)

    waiting = True
    while waiting:
        mouse_position = pygame.mouse.get_pos()

        screen.fill(BLACK)

        screen.blit(left_decor, left_decor_rect)
        screen.blit(title_text, title_rect)
        screen.blit(right_decor, right_decor_rect)

        # Draw buttons
        start_hover = start_button[0] <= mouse_position[0] <= start_button[0] + 200 and \
                      start_button[1] <= mouse_position[1] <= start_button[1] + 50
        draw_button("Start", start_button, font_buttons, GREEN, WHITE, (0, 100, 0), hover=start_hover)

        settings_hover = settings_button[0] <= mouse_position[0] <= settings_button[0] + 200 and \
                         settings_button[1] <= mouse_position[1] <= settings_button[1] + 50
        draw_button("Settings", settings_button, font_buttons, (0, 0, 255), WHITE, (0, 0, 150), hover=settings_hover)

        exit_hover = exit_button[0] <= mouse_position[0] <= exit_button[0] + 200 and \
                     exit_button[1] <= mouse_position[1] <= exit_button[1] + 50
        draw_button("Exit", exit_button, font_buttons, (200, 0, 0), WHITE, (100, 0, 0), hover=exit_hover)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_hover:
                    waiting = False
                    is_in_menu = False  # Ieșim din meniu, se continuă jocul
                elif settings_hover:
                    show_settings()
                    return
                elif exit_hover:
                    pygame.quit()
                    sys.exit()

def pause_menu():
    font = pygame.font.Font(None, 35)  # Font pentru text
    title_font = pygame.font.Font(None, 70)  # Font mai mare pentru titlu

    resume_button = (WIDTH // 2 - 100, HEIGHT // 2 - 50)
    main_menu_button = (WIDTH // 2 - 100, HEIGHT // 2 + 50)

    paused = True
    while paused:
        # Fundal semitransparent
        screen.fill((0, 0, 50))  # Fundal albastru
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # Semitransparent (RGBA)
        screen.blit(overlay, (0, 0))

        # Titlu
        title_surface = title_font.render("ПАУЗА", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
        screen.blit(title_surface, title_rect)

        # Cursor hover checks
        mouse_pos = pygame.mouse.get_pos()
        resume_hover = (resume_button[0] < mouse_pos[0] < resume_button[0] + 200 and
                        resume_button[1] < mouse_pos[1] < resume_button[1] + 50)
        menu_hover = (main_menu_button[0] < mouse_pos[0] < main_menu_button[0] + 200 and
                      main_menu_button[1] < mouse_pos[1] < main_menu_button[1] + 50)

        # Butoane
        draw_button("Продолжить", resume_button, font, (0, 200, 0), (255, 255, 255), (0, 250, 0), hover=resume_hover)
        draw_button("Главное меню", main_menu_button, font, (200, 0, 0), (255, 255, 255), (250, 0, 0), hover=menu_hover)

        pygame.display.flip()

        # Evenimente
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if resume_hover:
                    paused = False  # Revenim la joc
                elif menu_hover:
                    show_menu("IgroMuha!")
                    return  # Revine la meniul principal

levels = [
#level 1
    {
        'walls': [
            # Casa pentru spawn-ul jucătorului - UȘĂ PE SUD
            (100, 100, 300, 20),  # Zid nord
            (100, 100, 20, 200),  # Zid vest
            (100, 300, 50, 20), (250, 300, 150, 20),  # Zid sud cu DESCHIDERE mare pentru ușă
            (400, 100, 20, 200),  # Zid est

            # Hambar 1 - UȘI PE NORD ȘI VEST
            (600, 500, 150, 20), (950, 500, 150, 20),  # Zid nord cu DESCHIDERE mare pentru ușă
            (600, 500, 20, 200), (600, 750, 20, 150),  # Zid vest cu DESCHIDERE mare
            (600, 900, 500, 20),  # Zid sud
            (1100, 500, 20, 400),  # Zid est

            # Hambar 2 - UȘI PE VEST ȘI EST
            (1300, 300, 500, 20),  # Zid nord
            (1300, 300, 20, 100), (1300, 540, 20, 100),  # Zid vest cu DESCHIDERE mare
            (1300, 700, 150, 20), (1650, 700, 150, 20),  # Zid sud cu DESCHIDERE mare
            (1800, 300, 20, 100), (1800, 540, 20, 100),  # Zid est cu DESCHIDERE mare

            # Casa 1 - UȘI PE EST ȘI SUD
            (1000, 800, 200, 20), (1220, 800, 80, 20),  # Zid nord
            (1000, 800, 20, 150),  # Zid vest
            (1000, 970, 100, 20), (1200, 970, 100, 20),  # Zid sud cu DESCHIDERE mare pentru ușă
            (1300, 800, 20, 100),  # Zid est cu DESCHIDERE

            # Casa 2 - UȘI PE SUD ȘI EST
            (1500, 1100, 250, 20), (1750, 1100, 50, 20),  # Zid nord
            (1500, 1100, 20, 100), (1500, 1240, 20, 60),  # Zid vest
            (1500, 1300, 100, 20), (1650, 1300, 100, 20),  # Zid sud cu DESCHIDERE mare
            (1800, 1100, 20, 100), (1800, 1240, 20, 60),  # Zid est cu DESCHIDERE mare

            # Casa 3 - UȘĂ PE NORD
            (400, 1500, 120, 20), (680, 1500, 20, 20),  # Zid nord cu DESCHIDERE mare
            (400, 1500, 20, 100), (400, 1620, 20, 160),  # Zid vest
            (400, 1800, 300, 20),  # Zid sud
            (700, 1500, 20, 300),  # Zid est

            # Casa 4 - UȘI PE EST ȘI VEST
            (1000, 1400, 200, 20), (1220, 1400, 200, 20),  # Zid nord
            (1000, 1400, 20, 120), (1000, 1620, 20, 120),  # Zid vest cu DESCHIDERE mare
            (1000, 1700, 200, 20), (1220, 1700, 200, 20),  # Zid sud
            (1400, 1400, 20, 120), (1400, 1620, 20, 120),  # Zid est cu DESCHIDERE mare

            # Casa 5 - UȘĂ PE NORD ȘI SUD
            (1800, 2000, 120, 20), (2000, 2000, 120, 20),  # Zid nord cu DESCHIDERE mare
            (1800, 2000, 20, 150), (1800, 2150, 20, 150),  # Zid vest
            (1800, 2300, 120, 20), (2000, 2300, 120, 20),  # Zid sud cu DESCHIDERE mare
            (2100, 2000, 20, 300),  # Zid est
        ],
        'enemies': [
            # Inamicii din hambar 1
            (700, 600), (750, 700), (850, 800),
            # Inamicii din hambar 2
            (1350, 400), (1450, 500), (1550, 600),

            # Inamicii din Casa 1
            (1100, 850), (1250, 900),

            # Inamicii din Casa 2
            (1550, 1200), (1650, 1250), (1750, 1200),

            # Inamicii din Casa 3
            (450, 1550), (550, 1650), (650, 1700),

            # Inamicii din Casa 4
            (1050, 1450), (1200, 1600), (1350, 1500),

            # Inamicii din Casa 5
            (1850, 2100), (1950, 2200),

            # Inamici pe afară
            (500, 400), (1400, 1000), (1800, 700),
            (1000, 400), (1700, 1500), (950, 950),
        ],
        'health_packs': [
            (700, 1200), (1800, 1800), (400, 1350), (1400, 800), (1300, 1500)
        ],
        'ammo_packs': [
            (1000, 700), (800, 850), (1300, 600), (500, 950), (1500, 1300), (1800, 1600)
        ],
        'traps': [
            (1150, 850), (1550, 1450), (400, 750), (1500, 1100), (850, 1750)
        ],
        'speed_boosts': [
            (950, 1200), (1600, 800), (700, 1700), (1200, 1150), (1400, 1400), (2100, 1800)
        ],
        'barriers': [
            (300, 250, 40, 40),  # Baricadă lângă casa spawn
            (650, 700, 40, 40), (750, 750, 40, 40),  # Baricade lângă hambar 1
            (1250, 550, 40, 40), (1350, 600, 40, 40),  # Baricade în hambar 2
            (1150, 850, 40, 40),  # Baricadă în casa 1
            (1700, 1250, 40, 40),  # Baricadă lângă casa 2
            (600, 1650, 40, 40),  # Baricadă lângă casa 3
            (1200, 1550, 40, 40),  # Baricadă lângă casa 4
            (1900, 2200, 40, 40)  # Baricadă lângă casa 5
        ],
    },
    #level 2
    {
        'walls': [
            # Casa pentru spawn-ul jucătorului - UȘĂ PE EST (gaură mai mare pentru ușă)
            (100, 100, 300, 20),  # Zid nord
            (100, 100, 20, 200),  # Zid vest
            (100, 300, 300, 20),  # Zid sud
            (400, 100, 20, 60), (400, 260, 20, 60),  # Zid est cu DESCHIDERE pentru ușă mai mare

            # Hambar 1 - UȘĂ PE EST (gaură mai mare pentru ușă)
            (500, 200, 500, 20),  # Zid nord
            (500, 200, 20, 400),  # Zid vest
            (500, 600, 500, 20),  # Zid sud
            (1000, 200, 20, 140), (1000, 440, 20, 140),  # Zid est cu DESCHIDERE pentru ușă mai mare

            # Hambar 2 - UȘI PE VEST ȘI SUD (găuri mai mari pentru uși)
            (1300, 300, 500, 20),  # Zid nord
            (1300, 300, 20, 150), (1300, 550, 20, 150),  # Zid vest cu DESCHIDERE pentru ușă mai mare
            (1300, 700, 200, 20), (1600, 700, 200, 20),  # Zid sud cu DESCHIDERE pentru ușă mai mare
            (1800, 300, 20, 400),  # Zid est

            # Casa 1 - UȘĂ PE NORD (gaură mai mare pentru ușă)
            (400, 800, 100, 20), (520, 800, 140, 20),  # Zid nord cu DESCHIDERE pentru ușă mai mare
            (400, 800, 20, 250),  # Zid vest
            (400, 1050, 300, 20),  # Zid sud
            (700, 800, 20, 250),  # Zid est

            # Casa 2 - UȘĂ PE SUD (gaură mai mare pentru ușă)
            (800, 1000, 400, 20),  # Zid nord
            (800, 1000, 20, 200),  # Zid vest
            (800, 1200, 250, 20), (1050, 1200, 150, 20),  # Zid sud cu DESCHIDERE pentru ușă mai mare

            # Casa 3 - UȘI PE SUD ȘI VEST (găuri mai mari pentru uși)
            (1600, 1400, 400, 20),  # Zid nord
            (1600, 1400, 20, 100), (1600, 1600, 20, 200),  # Zid vest cu DESCHIDERE pentru ușă mai mare
            (1600, 1700, 200, 20), (1850, 1700, 150, 20),  # Zid sud cu DESCHIDERE pentru ușă mai mare
            (2000, 1400, 20, 300),  # Zid est

            # Casa 4 - UȘĂ PE EST (gaură mai mare pentru ușă)
            (1000, 1400, 400, 20),  # Zid nord
            (1000, 1400, 20, 300),  # Zid vest
            (1000, 1700, 400, 20),  # Zid sud
            (1400, 1400, 20, 100), (1400, 1600, 20, 200),  # Zid est cu DESCHIDERE pentru ușă mai mare

            # Casa 5 - UȘĂ PE NORD (gaură mai mare pentru ușă)
            (1600, 2000, 180, 20),  # Zid nord cu DESCHIDERE pentru ușă mai mare
            (1600, 2000, 20, 300),  # Zid vest
            (1600, 2300, 300, 20),  # Zid sud
            (1900, 2000, 20, 300),  # Zid est
        ],
        'enemies': [
            # Inamicii din hambar 1
            (550, 300), (600, 400), (800, 500),
            # Inamicii din hambar 2
            (1350, 350), (1400, 450), (1550, 550),

            # Inamicii din Casa 1
            (450, 850), (550, 950),

            # Inamicii din Casa 2
            (850, 1050), (950, 1150), (1000, 1100),

            # Inamicii din Casa 3
            (1650, 1450), (1750, 1500), (1850, 1650),

            # Inamicii din Casa 4
            (1050, 1450), (1150, 1500), (1300, 1600),

            # Inamicii din Casa 5
            (1650, 2100), (1750, 2200),

            # Inamici pe afară
            (400, 400), (1200, 800), (1800, 600),
            (800, 400), (1600, 1000), (900, 900),
        ],
        'health_packs': [
            (600, 1100), (1700, 1700), (300, 1300), (1300, 300), (800, 1200)
        ],
        'ammo_packs': [
            (900, 600), (700, 700), (1000, 600), (400, 800), (1200, 1200), (1600, 1600)
        ],
        'traps': [
            (1050, 700), (1250, 1450), (300, 500), (1500, 1400), (800, 1600)
        ],
        'speed_boosts': [
            (850, 1200), (1550, 800), (700, 1500), (1100, 1100), (1300, 1300), (1800, 1800)
        ],
        'barriers': [
            (300, 200, 40, 40),  # Baricadă lângă casa spawn
            (650, 500, 40, 40),  # Baricade lângă hambar 1
            (1350, 650, 40, 40),  # Baricadă în hambar 2 sud
            (450, 950, 40, 40),  # Baricadă în casa 1
            (1000, 1150, 40, 40), (1050, 1100, 40, 40),  # Baricade lângă casa 2
            (1650, 1550, 40, 40), (1750, 1600, 40, 40),  # Baricade lângă casa 3
            (1100, 1250, 40, 40),  # Baricadă în casa 4
            (1700, 2100, 40, 40)  # Baricadă în casa 5
        ],
    },
    #level 3
{
        'walls': [
            # Casa pentru spawn-ul jucătorului - UȘĂ PE SUD
            (100, 100, 300, 20),  # Zid nord
            (100, 100, 20, 200),  # Zid vest
            (100, 300, 50, 20), (250, 300, 150, 20),  # Zid sud cu DESCHIDERE mare pentru ușă
            (400, 100, 20, 200),  # Zid est

            # Hambar 1 - UȘI PE NORD ȘI VEST
            (600, 500, 150, 20), (950, 500, 150, 20),  # Zid nord cu DESCHIDERE mare pentru ușă
            (600, 500, 20, 200), (600, 750, 20, 150),  # Zid vest cu DESCHIDERE mare
            (600, 900, 500, 20),  # Zid sud
            (1100, 500, 20, 400),  # Zid est

            # Hambar 2 - UȘI PE VEST ȘI EST
            (1400, 400, 500, 20),  # Zid nord (mutat mai sus)
            (1400, 400, 20, 150), (1400, 600, 20, 150),  # Zid vest cu DESCHIDERE mare
            (1400, 900, 250, 20), (1670, 900, 230, 20),  # Zid sud cu DESCHIDERE mare pentru ușă
            (1900, 400, 20, 150), (1900, 600, 20, 150),  # Zid est cu DESCHIDERE mare

            # Casa 1 - UȘI PE EST ȘI SUD
            (300, 800, 300, 20),  # Zid nord (mutat poziția casei total)
            (300, 800, 20, 160),  # Zid vest
            (300, 980, 100, 20), (500, 980, 100, 20),  # Zid sud cu DESCHIDERE mare
            (600, 800, 20, 200),  # Zid est

            # Casa 2 - UȘI PE NORD ȘI EST
            (1000, 1100, 300, 20),  # Zid nord (mutat mai sus)
            (1000, 1100, 20, 180),  # Zid vest
            (1000, 1300, 250, 20),  # Zid sud
            (1300, 1100, 20, 150), (1300, 1270, 20, 30),  # Zid est cu DESCHIDERE mare

            # Casa 3 - UȘĂ PE SUD
            (500, 1500, 200, 20),  # Zid nord
            (500, 1500, 20, 250),  # Zid vest
            (500, 1750, 80, 20), (620, 1750, 80, 20),  # Zid sud cu DESCHIDERE mare
            (700, 1500, 20, 250),  # Zid est

            # Casa 4 - UȘI PE NORD ȘI VEST
            (1500, 1400, 300, 20),  # Zid nord (mutat poziția să nu fie suprapus)
            (1500, 1400, 20, 120), (1500, 1620, 20, 120),  # Zid vest cu DESCHIDERE mare
            (1500, 1700, 200, 20), (1720, 1700, 40, 20),  # Zid sud cu DESCHIDERE mai mică
            (1800, 1400, 20, 300),  # Zid est

            # Casa 5 - UȘĂ PE VEST
            (800, 2000, 20, 150), (800, 2150, 20, 150),  # Zid vest cu DESCHIDERE mare
            (800, 2300, 300, 20),  # Zid sud
            (1100, 2000, 20, 300),  # Zid est
        ],
        'enemies': [
            # Inamicii din hambar 1
            (700, 600), (750, 700), (850, 800),
            # Inamicii din hambar 2
            (1450, 500), (1550, 600), (1650, 450),

            # Inamicii din Casa 1
            (400, 850), (500, 950),

            # Inamicii din Casa 2
            (1100, 1150), (1150, 1200),

            # Inamicii din Casa 3
            (550, 1550), (650, 1600),

            # Inamicii din Casa 4
            (1550, 1450), (1650, 1600),

            # Inamicii din Casa 5
            (850, 2050), (950, 2200),

            # Inamici pe afară
            (1000, 500), (1500, 800), (1800, 1000),
            (1800, 1300), (900, 900), (700, 1300),
        ],
        'health_packs': [
            (300, 900), (1400, 450), (1800, 850), (500, 1400), (1500, 1600)
        ],
        'ammo_packs': [
            (600, 700), (1300, 1700), (1650, 1450), (1800, 1450), (850, 1900), (1400, 900)
        ],
        'traps': [
            (1500, 1200), (1600, 800), (700, 780), (1900, 1300), (600, 1780)
        ],
        'speed_boosts': [
            (450, 750), (1200, 1250), (1400, 2000), (1600, 1000), (1700, 1550)
        ],
        'barriers': [
            (250, 200, 40, 40),  # Baricadă lângă casa spawn
            (750, 650, 40, 40),  # Baricade lângă hambar 1
            (1550, 750, 40, 40),  # Baricadă în hambar 2 sud
            (400, 900, 40, 40),  # Baricadă lângă casa 1
            (1200, 1200, 40, 40), (1250, 1150, 40, 40),  # Baricade lângă casa 2
            (500, 1650, 40, 40), (650, 1700, 40, 40),  # Baricade în apropiere de casa 3
            (1600, 1550, 40, 40),  # Baricadă în casa 4
            (1000, 2200, 40, 40)  # Baricadă în apropiere de casa 5
        ],
    },
]

running = True
while running:
    show_menu("IgroMuha!")

    hearts = 3
    current_level = 0
    normal_speed = 3  # Viteza normală a jucătorului
    speed_boost_active = False  # Starea boost-ului
    player = Player(150, 150)
    camera = Camera(MAP_WIDTH, MAP_HEIGHT)
    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    effects = pygame.sprite.Group()
    all_sprites.add(player)
    walls, enemies, health_packs, traps, speed_boosts, ammo_packs, barriers = load_level(levels[current_level])

    playing = True
    last_shot_time = 0  # Track the last shot time
    cooldown = 0.3  # Cooldown of 1 second

    while playing:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
                playing = False

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:  # Apăsarea tastei Esc deschide meniul de pauză
                    pause_menu()

            if is_in_menu:
                is_in_menu = False  # Setare implicită

            if not is_in_menu:  # Permit interacțiuni doar dacă nu este deschis un meniu
                if event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        pause_menu()

            if event.type == USEREVENT + 1:
                if speed_boost_active:  # Verifică dacă boost-ul este activ
                    player.speed = normal_speed  # Revino la viteza normală
                    speed_boost_active = False  # Dezactivează starea boost
                    pygame.time.set_timer(USEREVENT + 1, 0)  # Dezactivează temporizatorul

            if event.type == KEYDOWN:
                if event.key == K_1:
                    player.selected_ammo = '9mm'
                elif event.key == K_2:
                    player.selected_ammo = '55mm'

            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                current_time = time.time()  # Get the current time
                if current_time - last_shot_time >= cooldown:  # Check if 1 second has passed
                    if ((player.selected_ammo == '9mm' and player.ammo_9mm > 0) or
                            (player.selected_ammo == '55mm' and player.ammo_55mm > 0)):
                        target_x, target_y = event.pos
                        bullet = Bullet(player.rect.centerx, player.rect.centery, target_x, target_y, camera)
                        click_sound.play()

                        if player.selected_ammo == '9mm':
                            player.ammo_9mm -= 1
                        else:
                            player.ammo_55mm -= 1
                            bullet.dx *= 1.5  # Increase speed for 5.5mm bullet
                            bullet.dy *= 1.5
                            bullet.damage = 40  # Custom damage for 5.5mm

                        bullets.add(bullet)
                        all_sprites.add(bullet)

                        last_shot_time = current_time  # Update the last shot time

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        player.update(keys, mouse_pos, walls)
        camera.update(player)
        bullets.update(walls)
        enemies.update(player, walls, barriers)
        effects.update()

        if player.health <= 0:
            show_menu("Ты проиграл!!!! ", is_game_over=True)
            playing = False
            break  # Ieşim din bucla de joc pentru a reîncepe jocul

        for bullet in bullets:
            hit_enemies = pygame.sprite.spritecollide(bullet, enemies, False)
            for enemy in hit_enemies:
                enemy.health -= 10
                bullet.kill()
                if enemy.health <= 0:
                    enemy.kill()

            hit_barriers = pygame.sprite.spritecollide(bullet, barriers, False)
            for barricade in hit_barriers:
                barricade.take_damage()  # Aplicăm daune baricadei
                bullet.kill()

        if pygame.sprite.spritecollide(player, enemies, False):
            player.health -= 1
            for index in range(min(1, len(Effect.POSITIONS))):
                effect = Effect(player.rect.centerx, player.rect.centery, "-", RED, index)
                effects.add(effect)
                all_sprites.add(effect)
            if player.health <= 0:
                show_menu("Ты проиграл!!!! ", is_game_over=True)
                playing = False
                break  # Ieşim din bucla de joc pentru a reîncepe jocul

        collected_health = pygame.sprite.spritecollide(player, health_packs, True)
        for pack in collected_health:
            player.health = min(player.health + 30, 120)  # Vindecare maximă la 120
            for index in range(min(3, len(Effect.POSITIONS))):
                effect = Effect(player.rect.centerx, player.rect.centery, "+", GREEN, index)
                effects.add(effect)
                all_sprites.add(effect)

        collected_ammo = pygame.sprite.spritecollide(player, ammo_packs, True)
        for ammo in collected_ammo:
            player.ammo_9mm += 15
            player.ammo_55mm += 5

        if pygame.sprite.spritecollide(player, traps, True):
            player.health -= 20  # Jucătorul pierde sănătate
            for index in range(min(3, len(Effect.POSITIONS))):
                effect = Effect(player.rect.centerx, player.rect.centery, "-", PURPLE, index)
                effects.add(effect)
                all_sprites.add(effect)

        if pygame.sprite.spritecollide(player, speed_boosts, True):
            player.speed = 8  # Crește viteza jucătorului
            speed_boost_active = True  # Activează starea boost
            pygame.time.set_timer(USEREVENT + 1, 2500)  # După 5 secunde, dezactivează boost-ul
            for index in range(min(3, len(Effect.POSITIONS))):
                effect = Effect(player.rect.centerx, player.rect.centery, "+", YELLOW, index)
                effects.add(effect)
                all_sprites.add(effect)

        if len(enemies) == 0:
            current_level += 1
            if current_level >= len(levels):
                show_menu("Ты выиграл!! Красавчик!", is_game_over=True)
                playing = False
            else:
                show_next_level_menu(current_level)
                all_sprites.empty()
                all_sprites.add(player)
                walls, enemies, health_packs, traps, speed_boosts, ammo_packs, barriers = load_level(levels[current_level])
                player.rect.topleft = (150, 150)  # Respawn sigur

        buffer_size = 100

        # Redesenare
        screen.blit(background_image, (0, 0))

        # Desenează obiectele, aplicând camera
        for entity in all_sprites:
            screen.blit(entity.image, camera.apply(entity))

        for sprite in all_sprites:
            screen.blit(sprite.image, camera.apply(sprite))

        health_text = font.render(f"ХП: {player.health}", True, GREEN)
        ammo_9mm_text = font.render(f"9mm Патроны: {player.ammo_9mm}", True, YELLOW)
        ammo_55mm_text = font.render(f"5.5mm Патроны: {player.ammo_55mm}", True, YELLOW)
        screen.blit(health_text, (40, 40))
        screen.blit(ammo_9mm_text, (40, 80))
        screen.blit(ammo_55mm_text, (40, 120))  # Position below 9mm ammo text

        square_border_color_1 = BLUE if player.selected_ammo == '9mm' else WHITE
        square_border_color_2 = BLUE if player.selected_ammo == '55mm' else WHITE

        pygame.draw.rect(screen, square_border_color_1, (*square_1_pos, square_width, square_height), 3)
        text_1 = font.render("9mm", True, WHITE)
        text_1_rect = text_1.get_rect(
            center=(square_1_pos[0] + square_width // 2, square_1_pos[1] + square_height // 2))
        screen.blit(text_1, text_1_rect)

        pygame.draw.rect(screen, square_border_color_2, (*square_2_pos, square_width, square_height), 3)
        text_2 = font.render("5.5mm", True, WHITE)
        text_2_rect = text_2.get_rect(
            center=(square_2_pos[0] + square_width // 2, square_2_pos[1] + square_height // 2))
        screen.blit(text_2, text_2_rect)

        if player.health < 70:
            color_center = (0, 0, 0, 0)  # Transparent at center
            if player.health < 50:
                color_edge = (100, 0, 0, 200) if player.health < 20 else (100, 0, 0, 100)  # Dark red to black at edges
            else:
                color_edge = (100, 0, 0, 50)  # Even more transparent dark red
            gradient_overlay = create_radial_gradient_optimized(buffer_size, WIDTH, HEIGHT, color_center, color_edge)
            screen.blit(gradient_overlay, (0, 0))

        pygame.display.flip()
        clock.tick(FPS)

pygame.quit()
sys.exit()
