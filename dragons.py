import os
import sys
import time
from random import randint
import pgzrun
from pgzero.actor import Actor

os.environ["SDL_VIDEO_WINDOW_POS"] = "50,50"

# --- CONFIGURATION ---
WIDTH = 800
HEIGHT = 600
RESULT_FILE = "results.txt"
EGG_TARGET = 20
MOVE_DISTANCE = 5

# --- VARIABLES ---
lives = 3
eggs_collected = 0
game_over = False
game_complete = False

hero = Actor("hero", pos=(200, 300))
lairs = []


def draw():
    screen.clear()
    screen.blit("dungeon", (0, 0))

    hero.draw()
    for lair in lairs:
        lair["dragon"].draw()
        if not lair["egg_hidden"]:
            lair["eggs"].draw()

    # HUD
    screen.draw.text(f"Lives: {lives}", topleft=(10, 10), fontsize=40, color="black")
    screen.draw.text(f"Eggs: {eggs_collected}/{EGG_TARGET}", topright=(WIDTH - 10, 10), fontsize=40, color="black")

    if game_over:
        screen.draw.text("GAME OVER", center=(WIDTH / 2, HEIGHT / 2), fontsize=80, color="red")
    if game_complete:
        screen.draw.text("YOU WIN!", center=(WIDTH / 2, HEIGHT / 2), fontsize=80, color="green")


def update():
    global game_over, game_complete

    if game_over:
        handle_game_end("LOSS")
        return
    if game_complete:
        handle_game_end("WIN")
        return

    # --- Movement Input ---
    if (keyboard.left or keyboard.a) and hero.left > 0:
        hero.x -= MOVE_DISTANCE
    if (keyboard.right or keyboard.d) and hero.right < WIDTH:
        hero.x += MOVE_DISTANCE
    if (keyboard.up or keyboard.w) and hero.top > 0:
        hero.y -= MOVE_DISTANCE
    if (keyboard.down or keyboard.s) and hero.bottom < HEIGHT:
        hero.y += MOVE_DISTANCE

    # --- Hard Boundary Clamp (Safety Net) ---
    if hero.left < 0:
        hero.left = 0
    if hero.right > WIDTH:
        hero.right = WIDTH
    if hero.top < 0:
        hero.top = 0
    if hero.bottom > HEIGHT:
        hero.bottom = HEIGHT

    check_lairs()


def make_lairs():
    global lairs
    lairs = []

    # 3 Lairs (Easy, Medium, Hard)
    positions = [(600, 100), (600, 300), (600, 500)]
    egg_positions = [(400, 100), (400, 300), (400, 500)]

    for i in range(3):
        lair = {
            "dragon": Actor("dragon-asleep", pos=positions[i]),
            "eggs": Actor(f"{i + 1}-eggs", pos=egg_positions[i]),
            "egg_count": i + 1,
            "egg_hidden": False,
            "wake_counter": 0,
            "sleep_length": randint(100, 200)
        }

        lairs.append(lair)


def check_lairs():
    global eggs_collected, game_complete, lives, game_over

    for lair in lairs:
        dragon = lair["dragon"]

        # If hero close, dragon wakes up
        distance = hero.distance_to(dragon)

        if distance < 150:
            dragon.image = "dragon-awake"
            # If colliding while awake -> hurt
            if hero.colliderect(dragon):
                lives -= 1
                hero.pos = (200, 300)  # Reset pos
                if lives == 0: game_over = True
        else:
            dragon.image = "dragon-asleep"
            # If close to eggs and dragon asleep -> collect
            if not lair["egg_hidden"] and hero.distance_to(lair["eggs"]) < 50:
                eggs_collected += lair["egg_count"]
                lair["egg_hidden"] = True

    # Respawn eggs periodically
    if randint(0, 100) < 2:
        for lair in lairs:
            lair["egg_hidden"] = False

    if eggs_collected >= EGG_TARGET:
        game_complete = True


def handle_game_end(result):
    draw()
    with open(RESULT_FILE, "w") as f:
        f.write(result)
    time.sleep(1.5)
    sys.exit()


# --- MUSIC ---
try:
    music.play("sleepingdragons_music.mp3")
    music.set_volume(0.5)
except Exception:
    pass

make_lairs()
pgzrun.go()