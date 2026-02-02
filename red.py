import os
import sys
import random
os.environ["SDL_VIDEO_WINDOW_POS"] = "50,50"
import pgzrun
from pgzero.actor import Actor
from pgzero.clock import clock
from pygame import Rect, mouse

# --- WINDOW CONFIGURATION ---
WIDTH, HEIGHT = 800, 600
CENTER = (WIDTH / 2, HEIGHT / 2)

# --- GAME CONSTANTS ---
FINAL_LEVEL = 6
START_SPEED = 10
COLORS = ["green", "blue"]
RESULT_FILE = "results.txt"
FONT_MAIN = "white"

# --- GLOBAL VARIABLES ---
game_over = False
game_complete = False
current_level = 1
stars = []
animations = []

# --- DEVMODE VARIABLES ---
dev_mode = False
auto_play = False
freeze_mode = False
show_hitboxes = False
speed_modifier = 1.0
dev_action_timer = 0
current_fps = 0


def init_level():
    # Calculates colors and creates stars for the current level.
    global stars, animations

    stop_animations()
    stars.clear()
    animations.clear()

    # Determine colors: Always 1 red, plus random green/blue
    colors_to_create = ["red"] + [random.choice(COLORS) for _ in range(current_level)]

    # Create Actors
    stars = [Actor(f"{color}-star") for color in colors_to_create]

    # Layout (Grid spacing)
    gap_size = WIDTH / (len(stars) + 1)
    random.shuffle(stars)

    for i, star in enumerate(stars):
        # Start at edges
        star.x = (i + 1) * gap_size
        star.y = 0 if i % 2 == 0 else HEIGHT

        start_animation(star)


def start_animation(star):
    # Starts animation for a specific star based on its current position.
    target_y = HEIGHT if star.y < HEIGHT / 2 else 0

    # Calculate Base Duration
    base_duration = (START_SPEED - current_level) / speed_modifier
    if base_duration < 0.5: base_duration = 0.5

    # Adjust duration based on distance remaining
    distance_total = HEIGHT
    distance_remaining = abs(target_y - star.y)

    # If unfreezing near the target, prevent instant snap
    if distance_remaining < 10:
        distance_remaining = 10

    time_fraction = distance_remaining / distance_total
    final_duration = base_duration * time_fraction

    anim = animate(star, duration=final_duration, on_finished=handle_loss, y=target_y)
    animations.append(anim)


def toggle_freeze():
    # Stops or Resumes animations.
    global freeze_mode
    freeze_mode = not freeze_mode

    if freeze_mode:
        # Stop everything exactly where it is
        stop_animations()
    else:
        # Resume animations from current positions
        for star in stars:
            start_animation(star)


def stop_animations():
    for anim in animations:
        if anim.running:
            anim.stop()
    animations.clear()


def schedule_shuffle():
    if stars and not game_over and not game_complete and not freeze_mode:
        x_values = [s.x for s in stars]
        random.shuffle(x_values)
        for i, star in enumerate(stars):
            anim = animate(star, duration=0.5 / speed_modifier, x=x_values[i])
            animations.append(anim)


def update(dt):
    global dev_action_timer, current_fps

    if dt > 0:
        current_fps = 1 / dt

    # DEVMODE: Auto-Play Logic
    if dev_mode and auto_play and not (game_over or game_complete):
        dev_action_timer += 1
        if dev_action_timer > 30:
            red_star = next((s for s in stars if "red" in s.image), None)
            if red_star:
                on_mouse_down(red_star.pos)
            dev_action_timer = 0


def draw():
    screen.clear()
    screen.blit("space", (0, 0))

    if not (game_over or game_complete):
        for star in stars:
            star.draw()
            if dev_mode and show_hitboxes:
                bbox = Rect(star.left, star.top, star.width, star.height)

                # HITBOX COLOR LOGIC: Red stars = Green box, Others = Yellow box
                if "red" in star.image:
                    screen.draw.rect(bbox, "green")
                else:
                    screen.draw.rect(bbox, "yellow")

    if game_over:
        draw_center_text("GAME OVER!", f"Reached Level {current_level}")
    elif game_complete:
        draw_center_text("YOU WON!", f"Completed all {FINAL_LEVEL} levels")

    if dev_mode:
        draw_dev_dashboard()


def draw_center_text(main, sub):
    screen.draw.text(main, fontsize=60, center=CENTER, color=FONT_MAIN)
    screen.draw.text(sub, fontsize=30, center=(WIDTH / 2, HEIGHT / 2 + 40), color=FONT_MAIN)


def draw_dev_dashboard():
    mx, my = mouse.get_pos()

    red_star = next((s for s in stars if "red" in s.image), None)
    dist_to_red = "N/A"
    if red_star:
        dist_to_red = int(((mx - red_star.x) ** 2 + (my - red_star.y) ** 2) ** 0.5)

    info_lines = [
        f"DEVMODE ACTIVE | FPS: {int(current_fps)}",
        f"Level: {current_level}/{FINAL_LEVEL} | Total Stars: {len(stars)}",
        f"Speed Mod: x{round(speed_modifier, 1)} (UP/DOWN)",
        f"Auto-Play: {auto_play} (A) | Freeze: {freeze_mode} (F)",
        f"Hitboxes: {show_hitboxes} (1)",
        "---",
        f"Mouse: ({mx}, {my})",
        f"Dist to Target: {dist_to_red}",
        "Controls: (N)ext Lvl | (W)in | (L)oss"
    ]

    for i, line in enumerate(info_lines):
        screen.draw.text(line, (10, 10 + (i * 15)), fontsize=18, color="yellow", owidth=1, ocolor="black")


def on_mouse_down(pos):
    global current_level, game_over, game_complete, freeze_mode

    if game_over or game_complete:
        return

    for star in stars:
        if star.collidepoint(pos):
            if "red" in star.image:
                play_sound("ding")
                if current_level == FINAL_LEVEL:
                    handle_win()
                else:
                    current_level += 1
                    init_level()
            else:
                play_sound("plop")
                handle_loss()
            break
    if freeze_mode:
        freeze_mode = False


def on_key_down(key):
    global dev_mode, auto_play, freeze_mode, show_hitboxes, speed_modifier, current_level

    # DevMode is hardcoded, no toggle.

    if dev_mode:
        if key == keys.A:
            auto_play = not auto_play
        elif key == keys.F:
            toggle_freeze()  # Calls the new freeze logic
        elif key == keys.K_1:
            show_hitboxes = not show_hitboxes
        elif key == keys.UP:
            speed_modifier += 0.5
            init_level()
        elif key == keys.DOWN:
            if speed_modifier > 0.5:
                speed_modifier -= 0.5
                init_level()
        elif key == keys.N:
            if current_level < FINAL_LEVEL:
                current_level += 1
                init_level()
            else:
                handle_win()
        elif key == keys.W:
            handle_win()
        elif key == keys.L:
            handle_loss()


def handle_win():
    global game_complete
    game_complete = True
    stop_animations()
    save_result("WIN")


def handle_loss():
    global game_over
    game_over = True
    stop_animations()
    save_result("LOSS")


def save_result(result):
    with open(RESULT_FILE, "w") as f:
        f.write(result)
    clock.schedule_unique(sys.exit, 1.5)


def play_sound(name):
    try:
        getattr(sounds, name).play()
    except Exception:
        pass


# --- INITIALIZATION ---
try:
    music.play("redalert_music.mp3")
    music.set_volume(0.5)
except Exception:
    pass

clock.schedule_interval(schedule_shuffle, 1)
init_level()
pgzrun.go()