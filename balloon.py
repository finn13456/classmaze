import os
import sys
from random import randint
import pgzrun
import pygame

os.environ["SDL_VIDEO_WINDOW_POS"] = "50,50"

# --- CONSTANTS ---
WIDTH, HEIGHT = 800, 600
WIN_SCORE = 10
RESULT_FILE = "results.txt"
BIRD_Y_RANGE = (10, 200)

# --- ACTORS ---
balloon = Actor("balloon", pos=(WIDTH // 2, HEIGHT // 2))
bird = Actor("bird-up", pos=(randint(WIDTH, WIDTH * 2), randint(*BIRD_Y_RANGE)))
house = Actor("house", pos=(randint(WIDTH, WIDTH * 2), 460))
tree = Actor("tree", pos=(randint(WIDTH, WIDTH * 2), 450))

# --- STATE ---
game_over = False
game_won = False
score = 0
is_ascending = False
bird_flap_up = True
update_counter = 0

# Dev Mode Variables
dev_mode = False
noclip = False


def on_key_down(key):
    global noclip, score
    if dev_mode:
        # Toggle Noclip
        if key == keys.N:
            noclip = not noclip
        # Quick Score controls
        elif key == keys.RIGHT:
            score += 1
        elif key == keys.LEFT:
            score = max(0, score - 1)


def on_mouse_down():
    global is_ascending
    if not game_over:
        is_ascending = True
        balloon.y -= 50


def on_mouse_up():
    global is_ascending
    is_ascending = False


def draw():
    screen.blit("background", (0, 0))

    if not game_over:
        balloon.draw()
        bird.draw()
        house.draw()
        tree.draw()

        if dev_mode:
            draw_hitboxes()
            draw_dev_info()

        screen.draw.text(f"Score: {score}/{WIN_SCORE}", (650, 10), color="black")
    else:
        display_end_screen()


def draw_hitboxes():
    color = "magenta" if noclip else "cyan"
    for actor in [balloon, bird, house, tree]:
        hitbox = Rect(actor.topleft, (actor.width, actor.height))
        screen.draw.rect(hitbox, color)


def draw_dev_info():
    info = [
        f"Dev Mode: ON",
        f"Noclip: {noclip} (N)",
        f"Balloon Y: {int(balloon.y)}",
        f"Score Edit: Left/Right"
    ]
    for i, text in enumerate(info):
        screen.draw.text(text, (10, 10 + (i * 20)), fontsize=20, color="yellow")


def update():
    global game_over, score, update_counter, bird_flap_up, game_won

    if game_over:
        return

    # Check Win Condition
    if score >= WIN_SCORE:
        finish_game("WIN")

    # Balloon Physics
    if not is_ascending:
        balloon.y += 1

    # Movement Logic
    update_obstacles()

    # COLLISION LOGIC (Bypassed by Noclip)
    if not noclip:
        # Boundary check
        if balloon.top < 0 or balloon.bottom > 560:
            finish_game("LOSS")

        # Actor collision
        if (balloon.colliderect(bird) or
                balloon.colliderect(house) or
                balloon.colliderect(tree)):
            finish_game("LOSS")


def update_obstacles():
    global update_counter, bird_flap_up, score
    # Bird
    if bird.x > 0:
        bird.x -= 4
        update_counter = (update_counter + 1) % 10
        if update_counter == 0:
            bird.image = "bird-down" if bird_flap_up else "bird-up"
            bird_flap_up = not bird_flap_up
    else:
        bird.x = randint(WIDTH, WIDTH * 2)
        bird.y = randint(*BIRD_Y_RANGE)
        score += 1

    # Ground Obstacles
    for obj in [house, tree]:
        if obj.right > 0:
            obj.x -= 2
        else:
            obj.x = randint(WIDTH, WIDTH * 2)
            score += 1


def finish_game(status):
    global game_over, game_won
    game_over = True
    game_won = (status == "WIN")
    with open(RESULT_FILE, "w") as f:
        f.write(status)
    clock.schedule(sys.exit, 2.0)


def display_end_screen():
    msg = "YOU WIN!" if game_won else "GAME OVER"
    color = "green" if game_won else "red"
    screen.draw.text(msg, center=(WIDTH / 2, HEIGHT / 2), fontsize=70, color=color, owidth=1, ocolor="white")


pgzrun.go()