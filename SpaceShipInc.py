import pygame
import sys
import random
import os
import threading
import socket
import json
import time

pygame.init()

# =============================
# Window & Clock
# =============================
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SpaceShip Inc.")
clock = pygame.time.Clock()

# =============================
# Asset Folders
# =============================
ASSETS = os.path.join(os.path.dirname(__file__), "assets")
SOUNDS = os.path.join(ASSETS, "Sounds")
TEXTURES = os.path.join(ASSETS, "Textures")

# =============================
# Sounds
# =============================
def load_sound(file_name):
    path = os.path.join(SOUNDS, file_name)
    return pygame.mixer.Sound(path) if os.path.exists(path) else None

bg1_sound = load_sound("bg1.wav")
bg2_sound = load_sound("bg2.wav")
bullet_sound = load_sound("bullet.wav")
enemy_die_sound = load_sound("enemy_die.wav")
laser_sound = load_sound("laser.wav")

# =============================
# Images
# =============================
def load_image(file_name, size=None):
    path = os.path.join(TEXTURES, file_name)
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    return None

player_size = (200, 200)
player_img = load_image("PLAYER.png", player_size)

bullet_size = (50, 100)
bullet_img = load_image("boost.png", bullet_size)

enemy_size = (100, 100)
enemy_img = load_image("enemy.png", enemy_size)
enemy2_img = load_image("enemy2.png", (120, 120))
boss_img = load_image("enemyboss.png", (250, 250))

explosion_img = load_image("explosion.png", (150,150))

background1 = load_image("background.png", (WIDTH, HEIGHT))
background2 = load_image("background2.png", (WIDTH, HEIGHT))

# Health bars
player_health_img = load_image("player_health.png", (300,30))
boss_health_img = load_image("boss_health.png", (400,40))

# =============================
# Game Constants
# =============================
PLAYER_SPEED = 5
BULLET_SPEED = 6
MAX_BULLETS = 4

ENEMY_SPEED = 1
ENEMY2_SPEED = 1
BOSS_SPEED = 1

SPAWN_TIMER = 40

# =============================
# Multiplayer Settings
# =============================
PORT_BASE = 50000  # Base port for matchmaking
HOST_CODE = None
IS_HOST = False
MULTI_CONNECTED = False
conn = None
addr = None

# =============================
# Game State
# =============================
class Player:
    def __init__(self, x, y, img, hp=100):
        self.x = x
        self.y = y
        self.img = img
        self.rect = pygame.Rect(x, y, img.get_width(), img.get_height())
        self.hp = hp

class Bullet:
    def __init__(self, x, y, owner_id):
        self.x = x
        self.y = y
        self.owner = owner_id
        self.rect = pygame.Rect(x, y, bullet_size[0], bullet_size[1])

class Enemy:
    def __init__(self, x, y, img, type_="enemy"):
        self.x = x
        self.y = y
        self.img = img
        self.type = type_
        self.rect = pygame.Rect(x, y, img.get_width(), img.get_height())
        self.hp = 500 if type_=="boss" else 1
        self.shoot_timer = 0

# =============================
# Multiplayer Helper Functions
# =============================
def generate_code():
    global HOST_CODE
    HOST_CODE = str(random.randint(100000,999999))
    return HOST_CODE

def host_game():
    global conn, addr, IS_HOST, MULTI_CONNECTED
    IS_HOST = True
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("", PORT_BASE + int(HOST_CODE[-2:])))
    server.listen(1)
    print("Waiting for client to join...")
    conn, addr = server.accept()
    MULTI_CONNECTED = True
    print(f"Client connected from {addr}")

def join_game(code):
    global conn, addr, MULTI_CONNECTED
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("127.0.0.1", PORT_BASE + int(code[-2:])))
    conn = client
    MULTI_CONNECTED = True
    print("Connected to host!")

# =============================
# Start Screen
# =============================
def start_screen():
    font = pygame.font.Font(None, 60)
    small_font = pygame.font.Font(None, 40)
    input_box = pygame.Rect(WIDTH//2-100, HEIGHT//2+60, 200,50)
    code_input = ""
    active_input = False
    code_generated = False
    run = True
    while run:
        screen.fill((10,10,50))
        title_text = font.render("SpaceShip Inc.", True, (255,255,0))
        screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//4))
        mx, my = pygame.mouse.get_pos()

        play_button = pygame.Rect(WIDTH//2-100, HEIGHT//2-60, 200,50)
        code_button = pygame.Rect(WIDTH//2-100, HEIGHT//2, 200,50)
        exit_button = pygame.Rect(WIDTH//2-100, HEIGHT//2+120, 200,50)

        pygame.draw.rect(screen,(0,200,0) if play_button.collidepoint((mx,my)) else (0,150,0), play_button)
        pygame.draw.rect(screen,(0,0,200) if code_button.collidepoint((mx,my)) else (0,0,150), code_button)
        pygame.draw.rect(screen,(200,0,0) if exit_button.collidepoint((mx,my)) else (150,0,0), exit_button)

        screen.blit(small_font.render("Play",True,(255,255,255)),(play_button.x+60,play_button.y+10))
        screen.blit(small_font.render("Code",True,(255,255,255)),(code_button.x+60,code_button.y+10))
        screen.blit(small_font.render("Exit",True,(255,255,255)),(exit_button.x+60,exit_button.y+10))

        if code_generated:
            code_text = small_font.render(f"Your Code: {HOST_CODE}", True, (255,255,255))
            screen.blit(code_text, (WIDTH//2 - code_text.get_width()//2, HEIGHT//2+180))

        if active_input:
            pygame.draw.rect(screen,(255,255,255),input_box,2)
            text_surface = small_font.render(code_input, True, (255,255,255))
            screen.blit(text_surface,(input_box.x+5,input_box.y+10))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    return "play"
                if code_button.collidepoint(event.pos):
                    active_input = True
                if exit_button.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:
                    generate_code()
                    threading.Thread(target=host_game,daemon=True).start()
                    code_generated = True
                elif active_input:
                    if event.key == pygame.K_RETURN and code_input:
                        threading.Thread(target=join_game,args=(code_input,),daemon=True).start()
                        return "multiplayer"
                    elif event.key == pygame.K_BACKSPACE:
                        code_input = code_input[:-1]
                    else:
                        if len(code_input)<6 and event.unicode.isdigit():
                            code_input += event.unicode
        pygame.display.flip()
        clock.tick(60)

# =============================
# Call Start Screen
# =============================
mode = start_screen()

# =============================
# Player Setup
# =============================
player = Player(WIDTH//2-100, HEIGHT-120, player_img)
player2 = Player(WIDTH//2-100, HEIGHT-120, player_img) if MULTI_CONNECTED else None

# =============================
# Game State Lists
# =============================
bullets = []
enemies = []
enemy2s = []
bosses = []
score = 0
spawn_timer = 0

# =============================
# Main Game Loop
# =============================
running = True
while running:
    clock.tick(60)

    # Background
    current_bg = background1 if score<40 else background2
    if current_bg:
        screen.blit(current_bg,(0,0))
    else:
        screen.fill((0,0,0))

    # Event Handling
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_SPACE and len(bullets)<MAX_BULLETS:
                bullets.append(Bullet(player.x+player_size[0]//2 - bullet_size[0]//2, player.y - bullet_size[1],1))
                if bullet_sound:
                    bullet_sound.play()

    # Player Movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_a] and player.x>0: player.x -= PLAYER_SPEED
    if keys[pygame.K_d] and player.x<WIDTH - player_size[0]: player.x += PLAYER_SPEED
    if keys[pygame.K_w] and player.y>0: player.y -= PLAYER_SPEED
    if keys[pygame.K_s] and player.y<HEIGHT - player_size[1]: player.y += PLAYER_SPEED

    player.rect.topleft = (player.x, player.y)

    # Bullets Update
    for b in bullets[:]:
        b.y -= BULLET_SPEED
        b.rect.topleft = (b.x,b.y)
        if b.y<-bullet_size[1]:
            bullets.remove(b)

    # Enemy Spawning
    spawn_timer += 1
    if spawn_timer>=SPAWN_TIMER:
        if score<40:
            enemies.append(Enemy(random.randint(0,WIDTH-enemy_size[0]),-enemy_size[1],enemy_img))
        else:
            enemy2s.append(Enemy(random.randint(0,WIDTH-enemy2_img.get_width()),-enemy2_img.get_height(),enemy2_img,"enemy2"))
        spawn_timer = 0

    # Enemy Movement & Collision
    for en in enemies[:]+enemy2s[:]+bosses[:]:
        en.y += ENEMY_SPEED if en.type=="enemy" else ENEMY2_SPEED if en.type=="enemy2" else 0
        en.rect.topleft = (en.x,en.y)
        # Collision with player
        if en.rect.colliderect(player.rect):
            player.hp -= 1 if en.type=="enemy" else 5 if en.type=="enemy2" else 15
            # Reset position for simple dodge mechanic
            en.y = -100

    # Bullet Collision with enemies
    for en in enemies[:]+enemy2s[:]+bosses[:]:
        for b in bullets[:]:
            if en.rect.colliderect(b.rect):
                bullets.remove(b)
                en.hp -= 1 if en.type!="boss" else 10
                if en.hp<=0:
                    if enemy_die_sound:
                        enemy_die_sound.play()
                    if en.type=="boss" and explosion_img:
                        screen.blit(explosion_img,(en.x,en.y))
                    if en.type=="enemy": enemies.remove(en)
                    if en.type=="enemy2": enemy2s.remove(en)
                    if en.type=="boss": bosses.remove(en)
                    score += 1

    # Draw Player
    screen.blit(player.img,(player.x,player.y))
    # Draw bullets
    for b in bullets: screen.blit(bullet_img,(b.x,b.y))
    # Draw enemies
    for en in enemies: screen.blit(en.img,(en.x,en.y))
    for en in enemy2s: screen.blit(en.img,(en.x,en.y))
    for en in bosses: screen.blit(en.img,(en.x,en.y))
    # Draw player health
    if player_health_img:
        pygame.draw.rect(screen,(50,50,50),(10,10,300,30))
        pygame.draw.rect(screen,(255,0,0),(10,10,3*player.hp,30))
        screen.blit(player_health_img,(10,10))
    # Draw score
    font = pygame.font.Font(None,40)
    score_text = font.render(f"Score: {score}",True,(255,255,255))
    screen.blit(score_text,(WIDTH-150,10))

    pygame.display.flip()
