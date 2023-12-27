import pygame
import random
import math
import asyncio
import os

# Initialize Pygame
pygame.init()

# Constants
GRID_WIDTH = 4
GRID_HEIGHT = 4
CELL_SIZE = 80
EXTRA_HEIGHT = 100
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE + EXTRA_HEIGHT  # Additional space for score and submit area
WINDOW_SIZE = (GRID_WIDTH * CELL_SIZE, WINDOW_HEIGHT)
WHITE = (255, 255, 255)
GREY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
FONT = pygame.font.Font(None, 28)
WIN_CONDITION = 10000
MAX_LEVEL = 7
CLICK_DELAY = 200  # delay before recognizing as drag

# Constants for submission box
SUBMIT_BOX = pygame.Rect(WINDOW_SIZE[0] - 150, WINDOW_SIZE[1] - 90, 140, 80)
SUBMIT_TEXT = FONT.render("Submit", True, "black")

# Create the window
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption('Merge Game')

def main():
    # Grid representation
    grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    grid[0][0] = ('G', 1)

    # Game loop flag and dragging state
    running = True
    dragging = False
    dragged_item = None
    dragged_pos = None
    hide_dragged_item = False
    mouse_down_time = None

    total_score = 0

    point_goal = 500  # Initial point goal
    gen_level_to_reward = 1
    click_count = 0

    def load_images():
        dir_path = os.path.dirname(os.path.realpath(__file__))
        images = {}
        min_scale_factor = 1
        for item_type in ['A', 'B', 'C']:
            for level in range(1, 8):  # Levels 1 through 7
                path = dir_path + f"/resources/slime_{item_type.lower()}_{level}.png"
                if os.path.exists(path):
                    image = pygame.image.load(path)
                    img_width, img_height = image.get_size()

                    # Find the scale factor necessary for the biggest image
                    scale_factor = 0.9 * min(CELL_SIZE / img_width, CELL_SIZE / img_height)
                    min_scale_factor = min(min_scale_factor, scale_factor)

                    images[(item_type, level)] = image
                else:
                    pass #print(f"Warning: Image not found at {path}")

        for item_type in ['A', 'B', 'C']:
            for level in range(1, 8):  # Levels 1 through 7
                if os.path.exists(path):
                    # Apply same factor to all images
                    if min_scale_factor < 1:
                        image = images[(item_type, level)]
                        img_width, img_height = image.get_size()
                        new_size = (int(img_width * min_scale_factor), int(img_height * min_scale_factor))
                        images[(item_type, level)] = pygame.transform.smoothscale(image, new_size)
        return images

    item_images = load_images()

    class Generator:
        @staticmethod
        def spawn_item(level):
            multi = (level - 1)**1.1
            type_probability = {
                'A': max(0.7 - 0.1 * multi, 0.1),
                'B': 0.3 + 0.05 * multi,
                'C': 0.05 * multi,
            }
            level_probability = {
                1: max(0.8 - 0.1 * multi, 0.1),  # Decrease chance for level 1 items
                2: 0.2 + 0.06 * multi,  # Increase chance for level 2+ items
                3: 0.035 * multi,
                4: 0.005 * multi,
            }
            item_type = random.choices(list(type_probability.keys()), list(type_probability.values()))[0]
            item_level = random.choices(list(level_probability.keys()), list(level_probability.values()))[0]
            return (item_type, item_level)

    def in_bounds(w, h, x, y):
        return x >= 0 and y >= 0 and x < w and y < h

    def on_point_goal_reached():
        nonlocal point_goal, gen_level_to_reward
        empty_cells = [(r, c) for r in range(GRID_HEIGHT) for c in range(GRID_WIDTH) if grid[r][c] is None]
        if empty_cells:
            random_cell = random.choice(empty_cells)
            grid[random_cell[0]][random_cell[1]] = ("G", gen_level_to_reward)

        point_goal = min(point_goal * 2, WIN_CONDITION)  # Double the point goal for the next cycle
        gen_level_to_reward += 1

    # Item scoring system
    def calculate_score(item):
        base_scores = {
            "A": 10,
            "B": 15,
            "C": 20,
            "G": 0,
        }
        return math.ceil(base_scores[item[0]] * 2.4 ** (item[1] - 1))  # Exponential scoring for levels

    def spawn_item_if_space(level):
        # Find a random empty cell
        empty_cells = [(r, c) for r in range(GRID_HEIGHT) for c in range(GRID_WIDTH) if grid[r][c] is None]
        if empty_cells:
            random_cell = random.choice(empty_cells)
            grid[random_cell[0]][random_cell[1]] = Generator.spawn_item(level)

    def handle_event(event):
        nonlocal dragging, dragged_item, dragged_pos, mouse_down_time, hide_dragged_item
        nonlocal running, total_score, click_count

        if event.type == pygame.QUIT:
            running = False# Inside the game loop

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            col, row = mouse_pos[0] // CELL_SIZE, mouse_pos[1] // CELL_SIZE

            if in_bounds(GRID_WIDTH, GRID_HEIGHT, col, row) and grid[row][col] is not None:
                dragged_item = grid[row][col]
                dragged_pos = (row, col)
                mouse_down_time = pygame.time.get_ticks()  # Record the time when mouse is pressed down

            click_count += 1

        elif event.type == pygame.MOUSEMOTION:
            if dragged_item and pygame.mouse.get_pressed()[0]:  # Check if the mouse button is still pressed
                if dragged_item[0] != 'G' or (pygame.time.get_ticks() - mouse_down_time) > CLICK_DELAY:
                    dragging = True
                    hide_dragged_item = True

        elif event.type == pygame.MOUSEBUTTONUP:
            try:
                mouse_up_time = pygame.time.get_ticks()
                if dragged_item and dragged_item[0] == "G" and (mouse_up_time - mouse_down_time) < CLICK_DELAY:
                    spawn_item_if_space(dragged_item[1])
                elif dragging:
                    drop_pos_x, drop_pos_y = event.pos
                    drop_col, drop_row = drop_pos_x // CELL_SIZE, drop_pos_y // CELL_SIZE

                    if dragged_item:
                        # Check for item submission
                        if SUBMIT_BOX.collidepoint(drop_pos_x, drop_pos_y):
                            if dragged_item[0] != "G":
                                grid[dragged_pos[0]][dragged_pos[1]] = None
                                total_score += calculate_score(dragged_item)
                                dragged_item = None
                        elif in_bounds(GRID_WIDTH, GRID_HEIGHT, drop_col, drop_row) and (drop_row, drop_col) != dragged_pos:
                            if grid[drop_row][drop_col] is None:
                                # Move item
                                grid[dragged_pos[0]][dragged_pos[1]] = None
                                grid[drop_row][drop_col] = dragged_item
                            elif grid[drop_row][drop_col] == dragged_item and dragged_item[1] < MAX_LEVEL:
                                # Merge items
                                grid[dragged_pos[0]][dragged_pos[1]] = None
                                grid[drop_row][drop_col] = (dragged_item[0], dragged_item[1] + 1)
            finally:
                dragging = False
                dragged_item = None
                dragged_pos = None
                mouse_down_time = None
                hide_dragged_item = False

    def get_hovered_cell(mouse_pos):
        col, row = mouse_pos[0] // CELL_SIZE, mouse_pos[1] // CELL_SIZE
        if 0 <= col < GRID_WIDTH and 0 <= row < GRID_HEIGHT:
            return row, col
        return None, None
    
    def mergeable(item):
        is_match = [(grid[row][col] == item) for col in range(GRID_WIDTH) for row in range(GRID_HEIGHT)]
        return sum(is_match) >= 2

    # Game loop
    async def game_loop():
        nonlocal running
        nonlocal dragging, hide_dragged_item
        while running:
            # Inside the game loop
            # Update dragging
            if dragged_item and pygame.mouse.get_pressed()[0]:  # Check if the mouse button is still pressed
                if (pygame.time.get_ticks() - mouse_down_time) > CLICK_DELAY:
                    dragging = True
                    hide_dragged_item = True

            # Handle events
            for event in pygame.event.get():
                handle_event(event)
                            
            # Inside the game loop, drawing section
            screen.fill("black")

            mouse_x, mouse_y = pygame.mouse.get_pos()
            hovered_row, hovered_col = get_hovered_cell((mouse_x, mouse_y))
            for row in range(GRID_HEIGHT):
                for col in range(GRID_WIDTH):
                    # Define the cell rectangle
                    cell_rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    
                    # Clear the cell by drawing a filled rectangle
                    pygame.draw.rect(screen, WHITE, cell_rect)

                    # Draw the cell border
                    pygame.draw.rect(screen, GREY, cell_rect, 1)
                    # Draw items with their point values
                    if grid[row][col] and not (hide_dragged_item and (row, col) == dragged_pos):
                        item = grid[row][col]
                        if item[0] == 'G':
                            gen_text = FONT.render(f"Gen {item[1]}", True, "black")
                            text_rect = gen_text.get_rect(center=(col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2))
                            screen.blit(gen_text, text_rect)
                            if mergeable(item):
                                help_text = FONT.render(f"Merge!", True, "blue")
                                screen.blit(help_text, (col * CELL_SIZE + 10, row * CELL_SIZE + 10))
                        else:
                            image = item_images.get(item)  # Get the corresponding image
                            if image:
                                # Position the image at the center of the grid cell
                                image_rect = image.get_rect(center=(col * CELL_SIZE + CELL_SIZE // 2, row * CELL_SIZE + CELL_SIZE // 2))
                                screen.blit(image, image_rect)
                    
                        # Check for hover
                        if (row, col) == (hovered_row, hovered_col):
                            item = grid[row][col]
                            points = calculate_score(item)
                            if points:
                                points_text = FONT.render(f"{points} pts", True, "black")
                                screen.blit(points_text, (col * CELL_SIZE + 10, row * CELL_SIZE + 10))
                            if item[1] is MAX_LEVEL:
                                max_text = FONT.render(f"Maxed", True, "black")
                                screen.blit(max_text, (col * CELL_SIZE + 10, row * CELL_SIZE + 50))
                    
                pygame.draw.rect(screen, GREY, SUBMIT_BOX)  # Draw the submission box
                screen.blit(SUBMIT_TEXT, (SUBMIT_BOX.x + SUBMIT_BOX.width // 2 - SUBMIT_TEXT.get_width() // 2, SUBMIT_BOX.y + SUBMIT_BOX.height // 2 - SUBMIT_TEXT.get_height() // 2))
            
                if click_count < 2:
                    # Show first time text
                    help_text = FONT.render(f"Click!", True, "blue")
                    screen.blit(help_text, (10, 10))

                # Inside the game loop, after drawing the grid and items
                goal_text = FONT.render(f"Goal: {WIN_CONDITION}", True, "white")
                screen.blit(goal_text, (5, WINDOW_SIZE[1] - 90))

                goal_text = FONT.render(f"Reward at: {point_goal}", True, "white")
                screen.blit(goal_text, (5, WINDOW_SIZE[1] - 60))

                score_text = FONT.render(f"Score: {total_score}", True, "white")
                screen.blit(score_text, (5, WINDOW_SIZE[1] - 30))  # Display at the bottom of the window

            if total_score >= WIN_CONDITION:
                win_text = FONT.render("YOU WIN!", True, (0, 128, 0))
                win_rect = win_text.get_rect(center=(CELL_SIZE * GRID_WIDTH // 2, CELL_SIZE * GRID_HEIGHT // 2))
                screen.blit(win_text, win_rect)
                    
            if dragging and hide_dragged_item:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if dragged_item[0] == 'G':
                    gen_text = FONT.render(f"Gen {dragged_item[1]}", True, "black")
                    screen.blit(gen_text, (mouse_x, mouse_y))
                else:
                    dragged_image = item_images.get(dragged_item)
                    if dragged_image:
                        screen.blit(dragged_image, (mouse_x - dragged_image.get_width() // 2, mouse_y - dragged_image.get_height() // 2))
                    
            if total_score >= point_goal:
                on_point_goal_reached()

            # Update the screen
            pygame.display.flip()
            await asyncio.sleep(0)  # very important, and keep it 0 for pygame

    return game_loop()

if __name__ == "__main__":
    asyncio.run(main())