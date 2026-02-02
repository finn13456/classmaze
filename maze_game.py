import os
import sys
import subprocess

os.environ["SDL_VIDEO_WINDOW_POS"] = f"50,50"
import pgzrun
import random

# --- CONFIGURATION ---
WIDTH = 600
HEIGHT = 600
SQUARE_SIZE = 10
RESULT_FILE = "results.txt"

# List of available mini-games
MINI_GAMES = [
    {'file': 'garden.py', 'name': 'Happy Garden'},
    {'file': 'balloon.py', 'name': 'Balloon Flight'},
    {'file': 'dragons.py', 'name': 'Sleeping Dragons'},
    {'file': 'shoot.py', 'name': 'Shoot the Fruit'},
    {'file': 'red.py', 'name': 'Red Alert'}
]

# --- VARIABLES ---
global maze_map, maze, new_game, star_count, new_map
Actor: Actor  # type: ignore
keys: keys  # type: ignore

new_game = True
game_over = False
new_map = True
percent_star = 5
minimum_star = 5
star_count = 0
lives = 3

# States: "play", "prompt", "win", "gameover"
game_state = "play"
current_game = None
game_locations = {}

player = Actor('player')

if percent_star < 1:
    percent_star = 1


def get_maze():
    global maze, maze_map, game_locations
    stars = 0
    game_locations = {}

    while stars < minimum_star:
        stars = 0
        maze = []
        maze_map = []

        try:
            file = open("maze.txt", 'r')
        except FileNotFoundError:
            print("Error: maze.txt not found.")
            return

        r = 0
        for row in file.readlines():
            c = 0
            maze.append([])
            maze_map.append([])
            for column in row:
                if column in "xwsfo":
                    maze[r].append(column)

                    if column == 'w':
                        maze_map[r].append(Actor('wall'))

                    elif column == 'o':
                        # Randomly place a Red Star (Mini-game)
                        if new_game and random.randint(1, 100) in range(1, percent_star + 1):
                            maze_map[r].append(Actor('red-star-path'))
                            maze[r][c] = 'r'  # Mark as 'r' for logic

                            # Assign a random game to this spot
                            game_locations[(r, c)] = random.choice(MINI_GAMES)
                            stars += 1
                        else:
                            maze_map[r].append(Actor('path'))

                    elif column == 's':
                        maze_map[r].append(Actor('start'))
                        if new_game:
                            # Calculate Player Start Position
                            start_pos = (SQUARE_SIZE / 2 + c * SQUARE_SIZE, SQUARE_SIZE / 2 + r * SQUARE_SIZE)
                            player.x, player.y = start_pos
                            player.r = int((player.y - SQUARE_SIZE / 2) / SQUARE_SIZE)
                            player.c = int((player.x - SQUARE_SIZE / 2) / SQUARE_SIZE)

                    elif column == 'f':
                        maze_map[r].append(Actor('finish'))

                    # Set position for the actor we just added
                    maze_map[r][c].pos = (SQUARE_SIZE / 2 + c * SQUARE_SIZE, SQUARE_SIZE / 2 + r * SQUARE_SIZE)
                    c += 1
                elif column == '\n':
                    r += 1

    file.close()


def check_win():
    global game_over, maze, game_state
    # Update logic coordinates
    player.r = int((player.y - SQUARE_SIZE / 2) / SQUARE_SIZE)
    player.c = int((player.x - SQUARE_SIZE / 2) / SQUARE_SIZE)

    if maze[player.r][player.c] == 'f' and not game_over:
        game_over = True
        game_state = "win"
        print('You win!')


def draw():
    global new_game, maze_map, maze
    screen.clear()

    # Draw the map actors
    for r in range(len(maze_map)):
        for c in range(len(maze_map[r])):
            maze_map[r][c].draw()

    new_game = False
    player.draw()

    # --- UI: Lives and Score ---
    screen.draw.text(
        f"Lives: {lives}",
        topright=(WIDTH - 80, 10),
        fontsize=30,
        color="red",
        shadow=(1, 1),
        scolor="black"
    )

    # Score directly under lives (y=40)
    screen.draw.text(
        f"Score: {star_count}",
        topright=(WIDTH - 80, 40),
        fontsize=30,
        color="white",
        shadow=(1, 1),
        scolor="black"
    )

    # --- Overlays ---
    if game_state == "win":
        screen.draw.text("YOU WIN!", center=(WIDTH / 2, HEIGHT / 2), fontsize=60, color="green", shadow=(1, 1),
                         scolor="black")

    elif game_state == "gameover":
        screen.draw.text("GAME OVER", center=(WIDTH / 2, HEIGHT / 2), fontsize=60, color="red", shadow=(1, 1),
                         scolor="black")

    elif game_state == "prompt":
        draw_prompt()


def draw_prompt():
    # Helper to draw the popup box
    box = Rect((100, 200), (400, 200))
    screen.draw.filled_rect(box, (50, 50, 50))
    screen.draw.rect(box, "white")

    game_name = current_game['name']
    screen.draw.text(f"Game: {game_name}", center=(300, 240), fontsize=35, color="cyan")
    screen.draw.text("Play for +1 Score?", center=(300, 290), fontsize=30, color="white")
    screen.draw.text("[Y] Yes    [N] No", center=(300, 350), fontsize=40, color="yellow")


def collect_star():
    global star_count, maze_map, maze
    star_count += 1
    print(f"Stars collected: {star_count}")

    # Remove star logically and visually
    maze[player.r][player.c] = 'o'
    maze_map[player.r][player.c].image = "path"


def run_minigame():
    global lives, game_state

    script_file = current_game['file']

    # Run the external python file
    subprocess.call([sys.executable, script_file])

    # Check the result file that the minigame should have written
    result = "UNKNOWN"
    if os.path.exists(RESULT_FILE):
        with open(RESULT_FILE, "r") as f:
            result = f.read().strip()
        os.remove(RESULT_FILE)  # Clean up

    if result == "WIN":
        collect_star()
    else:
        # Loss or window closed without winning
        lives -= 1
        # We remove the star anyway so they don't get stuck in a loop
        maze[player.r][player.c] = 'o'
        maze_map[player.r][player.c].image = "path"

    if lives <= 0:
        game_state = "gameover"
    else:
        game_state = "play"


def on_key_down(key):
    global maze, game_state, current_game

    if game_state == "play":
        # Check intended move direction
        if (key == keys.UP or key == keys.W) and maze[player.r - 1][player.c] != 'w':
            player.y -= SQUARE_SIZE
        elif (key == keys.LEFT or key == keys.A) and maze[player.r][player.c - 1] != 'w':
            player.x -= SQUARE_SIZE
        elif (key == keys.DOWN or key == keys.S) and maze[player.r + 1][player.c] != 'w':
            player.y += SQUARE_SIZE
        elif (key == keys.RIGHT or key == keys.D) and maze[player.r][player.c + 1] != 'w':
            player.x += SQUARE_SIZE

        # Update Grid Coordinates
        player.r = int((player.y - SQUARE_SIZE / 2) / SQUARE_SIZE)
        player.c = int((player.x - SQUARE_SIZE / 2) / SQUARE_SIZE)

        # Check for star at new location
        if maze[player.r][player.c] == 'r':
            current_game = game_locations.get((player.r, player.c))
            game_state = "prompt"

        check_win()

    elif game_state == "prompt":
        if key == keys.Y:
            run_minigame()
        elif key == keys.N:
            # Skip game, remove star
            maze[player.r][player.c] = 'o'
            maze_map[player.r][player.c].image = "path"
            game_state = "play"


get_maze()
pgzrun.go()