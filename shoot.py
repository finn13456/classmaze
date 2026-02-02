import os
import sys
from random import randint, choice

import pgzrun
import pygame
from pgzero.actor import Actor

os.environ["SDL_VIDEO_WINDOW_POS"] = "50,50"

# --- CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
WIN_TARGET = 25
RESULT_FILE = "results.txt"
MAX_SPEED = 15

BOX_LEFT, BOX_TOP = 50, 50
BOX_RIGHT, BOX_BOTTOM = 540, 540

# --- GAME STATE ---
score = 0
lives = 3
bounces = 0
game_over = False

# Movement
current_speed = 0
fruit_vx = 0
fruit_vy = 0

# Dev Mode
DevMode = False
auto_mode = False
lock_speed = False
lock_fruit = False
set_fruit = 1
speed_edit = 0


# --- INPUT ---
def on_key_down(key):
    global auto_mode, lives, score, set_fruit, lock_speed, current_speed, speed_edit

    if game_over or not DevMode:
        return

    if key == keys.SPACE:
        auto_mode = not auto_mode

    elif key == keys.UP:
        lives += 1

    elif key == keys.DOWN:
        lives -= 1
        if lives <= 0:
            handle_game_end("LOSS")

    elif key == keys.RIGHT:
        score += 1
        if score >= WIN_TARGET:
            handle_game_end("WIN")

    elif key == keys.LEFT:
        score = max(0, score - 1)

    elif key == keys.S:
        lock_speed = not lock_speed
        current_speed = abs(fruit_vx)

    elif key in (keys.D, keys.A):
        speed_edit += 1 if key == keys.D else -1
        current_speed = get_speed_from_bounces(bounces + speed_edit)

    elif key in (keys.K_1, keys.K_2, keys.K_3, keys.K_4):
        set_fruit = int(key.name[-1])
        place_fruit()


# --- DRAW ---
def draw():
    screen.clear()

    # Background
    box = Rect(
        BOX_LEFT,
        BOX_TOP,
        BOX_RIGHT - BOX_LEFT,
        BOX_BOTTOM - BOX_TOP
    )
    screen.draw.filled_rect(box, (135, 206, 235))

    fruit.draw()

    # UI
    screen.draw.text(f"Target: {WIN_TARGET}", (550, 50), color="white", fontsize=40)
    screen.draw.text(f"Score: {score}", (550, 100), color="white", fontsize=40)
    screen.draw.text(f"Lives: {lives}", (550, 150), color="red", fontsize=40)

    if DevMode:
        draw_dev_info()

    if game_over:
        text = "YOU WIN!" if score >= WIN_TARGET else "GAME OVER"
        color = "green" if score >= WIN_TARGET else "red"
        screen.draw.text(
            text,
            center=(WIDTH / 2, HEIGHT / 2),
            fontsize=80,
            color=color,
            owidth=1,
            ocolor="white"
        )


# --- DEV UI HELPERS ---
def draw_dev_lines(start_x, start_y, line_height, lines):
    y = start_y
    for line in lines:
        screen.draw.text(line, (start_x, y), color="yellow", fontsize=20)
        y += line_height


def draw_dev_info():
    mouse_x, mouse_y = pygame.mouse.get_pos()
    adjusted_bounces = max(0, bounces + speed_edit)
    speed_formula = round(get_speed_from_bounces(bounces + speed_edit), 5)

    lines = [
        "DevMode:",
        f"Bounces: {adjusted_bounces}",
        f"Formula: {speed_formula}",
        f"Speed: {int(abs(fruit_vx))}",
        f"fruit vx: {int(fruit_vx)}",
        f"fruit vy: {int(fruit_vy)}",
        f"fruit x: {int(fruit.x)}",
        f"fruit y: {int(fruit.y)}",
        f"cursor x: {mouse_x}",
        f"cursor y: {mouse_y}",
        f"fruit collide: {fruit.collidepoint((mouse_x, mouse_y))}",
        f"auto mode: {auto_mode} (SPACE)",
        f"edit lives ({lives}): UP / DOWN",
        f"edit score ({score}): RIGHT / LEFT",
        f"lock speed: {lock_speed} (S)",
        f"edit speed ({speed_edit}): D / A",
        f"set fruit: {set_fruit} (1–4)",
    ]

    draw_dev_lines(
        start_x=550,
        start_y=190,
        line_height=15,
        lines=lines
    )


# --- GAME LOGIC ---
def get_speed_from_bounces(x):
    x = max(0, x)
    return (-0.9 ** (x + 1) + 1) * MAX_SPEED


def update_velocity_magnitude():
    global current_speed, fruit_vx, fruit_vy

    if not lock_speed:
        base = bounces + speed_edit if DevMode else bounces
        current_speed = get_speed_from_bounces(base)

    if current_speed == 0 and (not DevMode or bounces > 0):
        current_speed = get_speed_from_bounces(1)

    fruit_vx = current_speed if fruit_vx >= 0 else -current_speed
    fruit_vy = current_speed if fruit_vy >= 0 else -current_speed


def place_fruit():
    global fruit, fruit_vx, fruit_vy, bounces

    bounces = 0

    fruit_types = {
        1: choice(["apple", "pineapple", "orange"]),
        2: "apple",
        3: "pineapple",
        4: "orange",
    }

    fruit = Actor(fruit_types[set_fruit])
    fruit.x = randint(100, 450)
    fruit.y = randint(100, 450)

    start_speed = get_speed_from_bounces(0)
    fruit_vx = start_speed if choice([True, False]) else -start_speed
    fruit_vy = start_speed if choice([True, False]) else -start_speed


def update():
    global fruit_vx, fruit_vy, bounces, score

    if auto_mode and fruit.collidepoint(pygame.mouse.get_pos()) and not game_over:
        score += 1
        place_fruit()
        if score >= WIN_TARGET:
            handle_game_end("WIN")

    if game_over:
        return

    fruit.x += fruit_vx
    fruit.y += fruit_vy

    wall_hit = False

    if fruit.left < BOX_LEFT:
        fruit.left = BOX_LEFT
        fruit_vx = abs(fruit_vx)
        wall_hit = True

    if fruit.right > BOX_RIGHT:
        fruit.right = BOX_RIGHT
        fruit_vx = -abs(fruit_vx)
        wall_hit = True

    if fruit.top < BOX_TOP:
        fruit.top = BOX_TOP
        fruit_vy = abs(fruit_vy)
        wall_hit = True

    if fruit.bottom > BOX_BOTTOM:
        fruit.bottom = BOX_BOTTOM
        fruit_vy = -abs(fruit_vy)
        wall_hit = True

    if wall_hit:
        if not lock_speed:
            bounces += 1
        update_velocity_magnitude()


def on_mouse_down(pos):
    global score, lives

    if game_over:
        return

    if fruit.collidepoint(pos):
        score += 1
        place_fruit()
        if score >= WIN_TARGET:
            handle_game_end("WIN")
    else:
        lives -= 1
        if lives <= 0:
            handle_game_end("LOSS")


def handle_game_end(result):
    global game_over

    if game_over:
        return

    game_over = True

    with open(RESULT_FILE, "w") as f:
        f.write(result)

    clock.schedule_unique(sys.exit, 1.5)


# --- MUSIC ---
try:
    music.play("shootthefruit_music.mp3")
    music.set_volume(0.5)
except Exception:
    pass


place_fruit()
pgzrun.go()
