import time
from random import randint
import os
import sys

os.environ["SDL_VIDEO_WINDOW_POS"] = "50,50"
import pgzrun
from pgzero.actor import Actor

# --- CONFIGURATION ---
WIDTH = 800
HEIGHT = 600
CENTER_X = WIDTH / 2
CENTER_Y = HEIGHT / 2
RESULT_FILE = "results.txt"
WIN_TIME = 30  # Seconds to survive to win
RAIN_CHANCE = 2
# --- VARIABLES ---
game_over = False
game_won = False
result_written = False
garden_happy = True
raining = False
time_elapsed = 0
start_time = time.time()

# Character Setup
rand_char = randint(1, 2)
if rand_char == 1:
    char = Actor("cow")
else:
    char = Actor("pig")
char.pos = 100, 500

# Lists
flower_list = []
wilted_list = []
fangflower_list = []
fangflower_vy_list = []
fangflower_vx_list = []


def draw():
    global game_over, time_elapsed, game_won, raining

    screen.clear()

    if raining:
        screen.blit("garden-raining", (0, 0))
    else:
        screen.blit("garden", (0, 0))

    # Draw game elements
    char.draw()
    for flower in flower_list:
        flower.draw()
    for fangflower in fangflower_list:
        fangflower.draw()

    # Calculate time
    if not game_over:
        current_time = int(time.time() - start_time)
        time_elapsed = current_time

    # UI Text
    screen.draw.text(
        f"Garden happy for: {time_elapsed} seconds",
        topleft=(10, 10), color="black", fontsize=30
    )

    if game_over:
        if game_won:
            screen.draw.text(
                "GARDEN SAFE - YOU WIN!",
                center=(CENTER_X, CENTER_Y),
                fontsize=60, color="green", owidth=1.5, ocolor="black"
            )
        elif not garden_happy:
            screen.draw.text(
                "GARDEN UNHAPPY!",
                center=(CENTER_X, CENTER_Y),
                fontsize=60, color="red", owidth=1.5, ocolor="black"
            )
        else:
            screen.draw.text(
                "FANGFLOWER ATTACK!",
                center=(CENTER_X, CENTER_Y),
                fontsize=60, color="red", owidth=1.5, ocolor="black"
            )


def update():
    global game_over, time_elapsed, game_won, raining

    if game_over:
        return

    # Check Win Condition
    current_time = int(time.time() - start_time)
    if current_time >= WIN_TIME:
        game_over = True
        game_won = True
        handle_game_end("WIN")
        return

    check_fangflower_collision()
    check_wilt_times()

    if not game_over:
        if keyboard.space:
            if rand_char == 1:
                char.image = "cow-water"
            else:
                char.image = "pig-water"
            clock.schedule(reset_char, 0.5)
            check_flower_collision()

        if (keyboard.left or keyboard.a) and char.x > 0:
            char.x -= 5
        elif (keyboard.right or keyboard.d) and char.x < WIDTH:
            char.x += 5
        elif (keyboard.up or keyboard.w) and char.y > 150:
            char.y -= 5
        elif (keyboard.down or keyboard.s) and char.y < HEIGHT:
            char.y += 5

        if current_time > 10 and not fangflower_list:
            mutate()

        update_fangflowers()


def handle_game_end(result):
    global result_written
    if result_written:
        return
    result_written = True

    with open(RESULT_FILE, "w") as f:
        f.write(result)
    clock.schedule_unique(sys.exit, 2.0)


def check_rain():
    if not game_over and not raining:
        if randint(1, 100) <= round(RAIN_CHANCE):
            start_rain()

    clock.schedule(check_rain, 1.0)


def start_rain():
    global raining, flower_list, wilted_list
    raining = True

    for i in range(len(flower_list)):
        flower_list[i].image = "flower"
        wilted_list[i] = "happy"

    clock.schedule(stop_rain, 1.0)


def stop_rain():
    global raining
    raining = False


def new_flower():
    flower_new = Actor("flower")
    flower_new.pos = randint(50, WIDTH - 50), randint(150, HEIGHT - 100)
    flower_list.append(flower_new)
    wilted_list.append("happy")


def add_flowers():
    if not game_over:
        new_flower()
        clock.schedule(add_flowers, 4)


def check_wilt_times():
    global garden_happy, game_over
    if wilted_list and not game_over:
        for wilted_since in wilted_list:
            if not wilted_since == "happy":
                time_wilted = int(time.time() - wilted_since)
                if time_wilted > 10.0:
                    garden_happy = False
                    game_over = True
                    handle_game_end("LOSS")
                    break


def wilt_flower():
    global flower_list, wilted_list
    if not game_over:
        if flower_list:
            rand_flower = randint(0, len(flower_list) - 1)
            # Only wilt if it is not currently raining
            if flower_list[rand_flower].image == "flower" and not raining:
                flower_list[rand_flower].image = "flower-wilt"
                wilted_list[rand_flower] = time.time()
        clock.schedule(wilt_flower, 3)


def check_flower_collision():
    index = 0
    for flower in flower_list:
        if flower.colliderect(char) and flower.image == "flower-wilt":
            flower.image = "flower"
            wilted_list[index] = "happy"
            break
        index = index + 1


def check_fangflower_collision():
    global game_over
    for fangflower in fangflower_list:
        if fangflower.colliderect(char):
            char.image = "zap"
            game_over = True
            handle_game_end("LOSS")
            break


def velocity():
    random_dir = randint(0, 1)
    random_velocity = randint(2, 3)
    if random_dir == 0:
        return -random_velocity
    else:
        return random_velocity


def mutate():
    if not game_over and flower_list:
        rand_flower = randint(0, len(flower_list) - 1)
        fangflower_pos_x = flower_list[rand_flower].x
        fangflower_pos_y = flower_list[rand_flower].y
        del flower_list[rand_flower]
        fangflower = Actor("fangflower")
        fangflower.pos = fangflower_pos_x, fangflower_pos_y
        fangflower_vx = velocity()
        fangflower_vy = velocity()
        fangflower_list.append(fangflower)
        fangflower_vx_list.append(fangflower_vx)
        fangflower_vy_list.append(fangflower_vy)
        clock.schedule(mutate, 20)


def update_fangflowers():
    global raining
    if not game_over and not raining:
        index = 0
        for fangflower in fangflower_list:
            fangflower_vx = fangflower_vx_list[index]
            fangflower_vy = fangflower_vy_list[index]
            fangflower.x = fangflower.x + fangflower_vx
            fangflower.y = fangflower.y + fangflower_vy
            if fangflower.left < 0:
                fangflower_vx_list[index] = -fangflower_vx
            if fangflower.right > WIDTH:
                fangflower_vx_list[index] = -fangflower_vx
            if fangflower.top < 150:
                fangflower_vy_list[index] = -fangflower_vy
            if fangflower.bottom > HEIGHT:
                fangflower_vy_list[index] = -fangflower_vy
            index = index + 1


def reset_char():
    if not game_over:
        if rand_char == 1:
            char.image = "cow"
        else:
            char.image = "pig"


# Start the loops
add_flowers()
wilt_flower()
check_rain()  # Start the rain checker

pgzrun.go()
