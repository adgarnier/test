import pygame
import random
import os
import asyncio

class GameWindow():
    def __init__(self):
        random.seed()
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Maze")
        self.colors = {"WHITE": (255, 255, 255), "GREY": (178, 190, 181), "BLACK": (0, 0, 0), 
                       "RED": (210, 43, 43), "GREEN": (49, 146, 54), "BLUE": (76, 81, 247),
                       "PURPLE": (157, 77, 187), "GOLD": (243, 175, 25), "GREY2": (100, 100, 100),
                       "GREY3": (195, 195, 195)}
        self.font = pygame.font.SysFont(None, 55)
        self.dt = 0
        self.player_total_points = 0
        self.gamestate = True
        self.maze_size = 3
        self.maze_setup()

        self.total_position = 0
        self.maze_orientations = ["straight", "right", "backwards", "left"]
        self.current_maze_index = 0
        
        self.stats_reset()

        self.images = self.load_images()
        self.minimap = False
        self.note_start_time = 0
        self.note = False
        self.falses()
        
        self.fading = False
        self.fade_alpha = 0
        self.fade_color = (0, 0, 0)
        self.fade_speed = 5
                
    def stats_reset(self):
        # reset stats 
        self.last_skeleton = -1
        self.last_spider = -1
        self.last_painting = -1
        self.last_note = -1
        self.last_grimreaper = -1
        self.skeleton_count = 0
        self.spider_count = 0
        self.painting_count = 0
        self.note_count = 0
        self.grimreaper_count = 0

    def falses(self):
        # reset position
        self.start = False
        self.end = False
        # reset walls
        self.top_wall = False
        self.bottom_wall = False
        self.right_wall = False
        self.left_wall = False
        # reset images
        self.skeleton = False
        self.painting = False
        # self.note = False
        self.grimreaper = False
        self.spider = False
        self.ladder = False
        self.showing_note = False
        
    def generate_orientations(self, x, y, width, height):
        return [
            (x, y),  # Original
            (height - 1 - y, x),  # 270 degrees clockwise
            (width - 1 - x, height - 1 - y),  # 180 degrees
            (y, width - 1 - x)  # 90 degrees clockwise
        ]

    def random_position(self, width, height):
        return random.randint(0, width - 1), random.randint(0, height - 1)
        
    def maze_setup(self):
        # Maze setup
        self.width, self.height = self.maze_size, self.maze_size  # Maze size (6x6)
        self.cell_size = 60  # Each cell (room) will be 60x60 pixels
        self.base_maze = self.create_maze(self.width, self.height)
        self.mazes = [
            self.base_maze,
            self.rotate_maze(self.base_maze),
            self.rotate_maze(self.rotate_maze(self.base_maze)),
            self.rotate_maze(self.rotate_maze(self.rotate_maze(self.base_maze)))
        ]

        # Define a single start position
        start_x, start_y = random.randint(0, self.width - 1), self.height - 1
        self.start_positions = self.generate_orientations(start_x, start_y, self.width, self.height)

        # Define a single end position
        end_x, end_y = random.choice([0, self.width - 1]), 0
        self.end_s = self.generate_orientations(end_x, end_y, self.width, self.height)
        
        # Generate all positions with transformations
        skeleton_x, skeleton_y = self.random_position(self.width, self.height)
        self.skeleton_s = self.generate_orientations(skeleton_x, skeleton_y, self.width, self.height)

        painting_x, painting_y = self.random_position(self.width, self.height)
        self.painting_s = self.generate_orientations(painting_x, painting_y, self.width, self.height)

        note_x, note_y = self.random_position(self.width, self.height)
        self.note_s = self.generate_orientations(note_x, note_y, self.width, self.height)
        self.maze_for_note = random.randint(0, 3)
        self.note_position_x = random.randint(200, 540)
        self.note_position_y = random.randint(450, 520)
        self.note_rotation = random.randint(0, 360)

        grimreaper_x, grimreaper_y = self.random_position(self.width, self.height)
        self.grimreaper_s = self.generate_orientations(grimreaper_x, grimreaper_y, self.width, self.height)

        spider_x, spider_y = self.random_position(self.width, self.height)
        self.spider_s = self.generate_orientations(spider_x, spider_y, self.width, self.height)

        ladder_x, ladder_y = random.choice([0, self.width - 1]), 0
        self.ladder_s = self.generate_orientations(ladder_x, ladder_y, self.width, self.height)

        # Initialize positions
        self.end_positions = list(self.end_s)
        self.skeleton_positions = list(self.skeleton_s)
        self.painting_positions = list(self.painting_s)
        self.note_positions = list(self.note_s)
        self.grimreaper_positions = list(self.grimreaper_s)
        self.spider_positions = list(self.spider_s)
        self.ladder_positions = list(self.ladder_s)
        self.player_positions = list(self.start_positions)

    def rotate_maze(self, maze):
        """Rotate the maze 90 degrees clockwise."""
        width, height = len(maze[0]), len(maze)
        rotated_maze = [[None for _ in range(width)] for _ in range(height)]
        
        for y in range(height):
            for x in range(width):
                room = maze[y][x]
                rotated_maze[x][height - 1 - y] = {
                    'top': room['left'],
                    'bottom': room['right'],
                    'left': room['bottom'],
                    'right': room['top'],
                    'visited': room['visited']
                }
        
        return rotated_maze

    def create_maze(self, width, height):
        # Maze grid initialized with all walls present
        maze = [[{'top': True, 'bottom': True, 'left': True, 'right': True, 'visited': False}
                 for _ in range(width)] for _ in range(height)]

        def get_neighbors(x, y):
            """Returns a list of unvisited neighbors with their directions."""
            neighbors = []
            directions = [(0, -1, 'top', 'bottom'), (0, 1, 'bottom', 'top'),
                          (-1, 0, 'left', 'right'), (1, 0, 'right', 'left')]

            for dx, dy, wall, opposite in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and not maze[ny][nx]['visited']:
                    neighbors.append((nx, ny, wall, opposite))

            return neighbors

        def carve_maze(x, y):
            """Recursive function to generate the maze."""
            maze[y][x]['visited'] = True
            neighbors = get_neighbors(x, y)
            random.shuffle(neighbors)

            for nx, ny, wall, opposite in neighbors:
                if not maze[ny][nx]['visited']:
                    maze[y][x][wall] = False  # Remove wall from current room
                    maze[ny][nx][opposite] = False  # Remove opposite wall from next room
                    carve_maze(nx, ny)

        # Start maze generation from a random position
        start_x, start_y = random.randint(0, width - 1), random.randint(0, height - 1)
        carve_maze(start_x, start_y)

        return maze

    def draw_maze(self, maze):
        """Render the maze on the Pygame screen."""
        for y in range(self.height):
            for x in range(self.width):
                room = maze[y][x]
                room_x = x * self.cell_size
                room_y = y * self.cell_size

                # Draw walls
                if room['top']:
                    pygame.draw.line(self.screen, self.colors['BLACK'], (room_x, room_y), 
                                     (room_x + self.cell_size, room_y), 2)
                if room['bottom']:
                    pygame.draw.line(self.screen, self.colors['BLACK'], (room_x, room_y + self.cell_size), 
                                     (room_x + self.cell_size, room_y + self.cell_size), 2)
                if room['left']:
                    pygame.draw.line(self.screen, self.colors['BLACK'], (room_x, room_y), 
                                     (room_x, room_y + self.cell_size), 2)
                if room['right']:
                    pygame.draw.line(self.screen, self.colors['BLACK'], (room_x + self.cell_size, room_y), 
                                     (room_x + self.cell_size, room_y + self.cell_size), 2)

    def draw_player(self, player_pos):
        """Draw the player as a red circle."""
        player_x_pos = player_pos[0] * self.cell_size + self.cell_size // 2
        player_y_pos = player_pos[1] * self.cell_size + self.cell_size // 2
        pygame.draw.circle(self.screen, self.colors["RED"], (player_x_pos, player_y_pos), 10)

    def next_game(self):
        self.load_images()
        if self.player_total_points != 0:
            self.start_fade_out()
            self.maze_setup()
        self.total_position = 0
        self.current_maze_index = 0
        self.maze_size += 1
        self.gamestate = True
        self.note = False
        self.falses()

    def start_fade_out(self, speed=5):
        self.fading = True
        self.fade_alpha = 0
        self.fade_speed = speed

        if self.grimreaper:
            self.fade_color = (80, 0, 0)
        elif self.ladder:
            self.fade_color = (255, 255, 255)
        else:
            self.fade_color = (0, 0, 0)

    def reset_game(self):
        print('resetting...')
        self.player_total_points = 0
        self.maze_size = 2
        self.skeleton_count = 0
        self.spider_count = 0
        self.painting_count = 0
        self.note_count = 0
        self.stats_reset()
        self.note = False
        self.next_game()
        self.maze_setup()
    
    def draw_text(self, text, x, y, color):
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))
    
    def tint_surface(self, surface, tint_color):
        # Apply a red tint to a surface
        tinted = surface.copy()
        tint = pygame.Surface(surface.get_size()).convert_alpha()
        tint.fill(tint_color)
        tinted.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        return tinted
    
    def load_images(self):
        all_images = [
            'new_start', 'new_left', 'new_left_right', 'new_left_straight', 'new_left_straight_right', 
            'new_none_dark', 'new_right', 'new_straight_close', 'new_straight_long', 'new_straight_long_2', 
            'new_straight_right', 'new_end', 'ladder', 'skeleton_front', 'skeleton_back', 'skeleton_side_1',
            'skeleton_side_2', 'painting1', 'painting1_side1', 'painting1_side2', 'note', 'grimreaper', 'spider',
            'spider2', 'spider3'
        ]
        
        # Special sizes per image name
        custom_sizes = {
            'new_start': (150, 80),
            'new_end': (150, 80),
            'ladder': (300, 600),
            'skeleton_front': (500, 1000),
            'skeleton_back': (110, 300),
            'skeleton_side_1': (140, 390),
            'skeleton_side_2': (110, 300),
            'painting1': (200, 150),
            'painting1_side1': (400, 225),
            'painting1_side2': (400, 225),
            'note': (60, 60),
            'grimreaper': (250, 500),
            'spider': (100, 110),
            'spider2': (300, 330),
            'spider3': (100, 110),
        }
        
        default_size = (800, 600)
        images = {}

        for wall in all_images:
            path = os.path.join("images", "doors", f"{wall}.png")
            try:
                image = pygame.image.load(path)
                size = custom_sizes.get(wall, default_size)
                image = pygame.transform.scale(image, size)
                images[wall] = image
            except pygame.error as e:
                print(f"Error loading {wall}.png: {e}")
                images[wall] = None

        return images
    
    def draw_wall_images(self):
        wall_position = (0, 0)
        # Determine the image key based on the wall conditions
        if self.top_wall and self.right_wall and self.left_wall:
            image_key = "new_none_dark"
        elif self.top_wall and self.left_wall:
            image_key = "new_left"
        elif self.top_wall and self.right_wall:
            image_key = "new_right"
        elif self.top_wall:
            image_key = "new_left_right"
        elif self.left_wall and self.right_wall:
            if self.player_positions[self.current_maze_index] == self.start_positions[self.current_maze_index]:
                image_key = "new_straight_close"
            elif self.current_maze_index in [0, 1]:
                image_key = "new_straight_long"
            else:
                image_key = "new_straight_long_2"
        elif self.left_wall:
            image_key = "new_left_straight"
        elif self.right_wall:
            image_key = "new_straight_right"
        else:
            image_key = "new_left_straight_right"

        # Check if the image exists in the images dictionary and blit it to the screen
        if image_key in self.images and self.images[image_key]:
            image = self.images[image_key]
            # if self.player_total_points == 5:
            #     image = self.tint_surface(self.images[image_key], (80, 0, 0, 50))  # Reddish overlay
            self.screen.blit(image, wall_position)

        if self.start:
            start_key = "new_start"
            start_position = (320, 480)

            if start_key in self.images and self.images[start_key]:
                start_image = self.images[start_key]

                # Rotate the image based on maze index
                if self.current_maze_index == 2:
                    start_image = pygame.transform.rotate(start_image, 180)
                if self.current_maze_index == 1:
                    start_image = pygame.transform.scale(start_image, (100, 80))
                    start_image = pygame.transform.rotate(start_image, 270)
                    start_position = (350, 480) 
                if self.current_maze_index == 3:
                    start_image = pygame.transform.scale(start_image, (100, 80))
                    start_image = pygame.transform.rotate(start_image, 90)
                    start_position = (350, 480) 
                self.screen.blit(start_image, start_position)

        if self.end:
            end_position = (320, 480)
            end_key = "new_end"
            if end_key in self.images and self.images[end_key]:
                self.screen.blit(self.images[end_key], end_position)  

        if self.painting:
            painting_key = 'painting1'
            painting_position = (800, 800)
            if painting_key in self.images and self.images[painting_key]:
                if self.current_maze_index == 0 and self.top_wall:
                    painting_key = "painting1"
                    painting_position = (300, 200)
                if self.current_maze_index == 2:
                    painting_position = (800, 800)  
                    painting_key = "painting1"
                if self.current_maze_index == 1 and self.left_wall:
                    painting_position = (500, 200)
                    painting_key = "painting1_side2"
                if self.current_maze_index == 3 and self.right_wall:
                    painting_position = (-100, 200) 
                    painting_key = "painting1_side1"
                self.screen.blit(self.images[painting_key], painting_position) 
                
        if self.note:
            note_key = "note"
            note_position = (self.note_position_x, self.note_position_y)
            if note_key in self.images and self.images[note_key]:
                note = self.images[note_key]
                note = pygame.transform.rotate(note, self.note_rotation)
                self.screen.blit(note, note_position) 
                
        if self.skeleton:
            skeleton_key = "skeleton_front"
            skeleton_position = (240, 170)
            if skeleton_key in self.images and self.images[skeleton_key]:
                if self.current_maze_index == 2 or (self.current_maze_index == 1 and self.left_wall and self.right_wall):
                    skeleton_position = (300, 170)  
                    skeleton_key = "skeleton_back"
                if self.current_maze_index == 1 and not (self.left_wall and self.right_wall):
                    skeleton_position = (170, 170)  
                    skeleton_key = "skeleton_side_1"
                if self.current_maze_index == 3 and not (self.left_wall and self.right_wall):
                    skeleton_position = (500, 190) 
                    skeleton_key = "skeleton_side_2"
                self.screen.blit(self.images[skeleton_key], skeleton_position)                  
        
        if self.grimreaper:
            grimreaper_key = "grimreaper"
            grimreaper_position = (280, 130)
            if grimreaper_key in self.images and self.images[grimreaper_key]:
                self.screen.blit(self.images[grimreaper_key], grimreaper_position)
    
        if self.spider:
            spider_key = "spider"
            spider_position = (self.screen_width, self.screen_height)
            if spider_key in self.images and self.images[spider_key]:
                if self.current_maze_index == 0 and not (self.left_wall and self.right_wall):
                    spider_position = (230, 100)
                    spider_key = "spider"
                if self.current_maze_index == 2:
                    spider_position = (self.screen_width, self.screen_height)  # You can set this to any position you want
                    spider_key = "spider"
                if self.current_maze_index == 1 and not (self.left_wall and self.right_wall):
                    spider_position = (550, 110)  # You can set this to any position you want
                    spider_key = "spider3"
                if self.current_maze_index == 3 and not (self.left_wall and self.right_wall):
                    spider_position = (-150, -150)  # You can set this to any position you want
                    spider_key = "spider2"
                self.screen.blit(self.images[spider_key], spider_position)

        # ladder
        if self.ladder:
            ladder_key = "ladder"
            ladder_position = (260, -30)
            self.screen.blit(self.images[ladder_key], ladder_position)
    
    def toggle_minimap(self):
        self.minimap = not self.minimap

    def handle_click(self, mouse_pos):      
        # Define areas for left, straight, and right doors based on the screen position
        left_area = (0, self.screen_width // 3)  # Left door
        straight_area = (self.screen_width // 3, 2 * self.screen_width // 3, 0, 500)
        right_area = (2 * self.screen_width // 3, self.screen_width)  # Right door
        backwards_area = (self.screen_height - 100, self.screen_height)
        next_area = (self.screen_height - 150, self.screen_height)
        note_area = (self.note_position_x + 60, self.note_position_y + 60)

        if next_area[0] <= mouse_pos[1] < next_area[1] \
        and self.player_positions[self.current_maze_index] == self.end_positions[self.current_maze_index]:
            self.player_total_points += 1
            self.next_game()
            
        self.falses()
        
        if note_area[0] <= mouse_pos[1] < note_area[1] and self.note:
            self.pick_note()
            print("you found a note")
        elif straight_area[0] <= mouse_pos[0] < straight_area[1] \
        and straight_area[2] <= mouse_pos[1] < straight_area[3] \
        and not self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['top']:
            self.total_position += 0  
            # Move straight
            if self.current_maze_index == 0:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] - 1),(self.player_positions[1][0] + 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] + 1),(self.player_positions[3][0] - 1, self.player_positions[3][1])]
            # backwards
            if self.current_maze_index == 2:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] + 1),(self.player_positions[1][0] - 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] - 1),(self.player_positions[3][0] + 1, self.player_positions[3][1])]
            # left
            if self.current_maze_index == 3:
                self.player_positions = [
                    (self.player_positions[0][0] + 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] + 1),
                    (self.player_positions[2][0] - 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] - 1)]
            # right
            if self.current_maze_index == 1:
                self.player_positions = [
                    (self.player_positions[0][0] - 1, self.player_positions[0][1]), (self.player_positions[1][0], self.player_positions[1][1] - 1), 
                    (self.player_positions[2][0] + 1, self.player_positions[2][1]), (self.player_positions[3][0], self.player_positions[3][1] + 1)]

        elif backwards_area[0] <= mouse_pos[1] < backwards_area[1] and not self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['bottom']:
            self.total_position += 2  # Move backwards
            if self.current_maze_index == 0:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] + 1),(self.player_positions[1][0] - 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] - 1),(self.player_positions[3][0] + 1, self.player_positions[3][1])
                ]
            if self.current_maze_index == 2:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] - 1),(self.player_positions[1][0] + 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] + 1),(self.player_positions[3][0] - 1, self.player_positions[3][1])
                ]
            if self.current_maze_index == 1:
                self.player_positions = [
                    (self.player_positions[0][0] + 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] + 1),
                    (self.player_positions[2][0] - 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] - 1)
                    ]
            if self.current_maze_index == 3:
                self.player_positions = [
                    (self.player_positions[0][0] - 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] - 1),
                    (self.player_positions[2][0] + 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] + 1)
                    ]

        elif left_area[0] <= mouse_pos[0] < left_area[1] and not self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['left']:
            self.total_position -= 1  # Move right
            # straight
            if self.current_maze_index == 0:
                self.player_positions = [
                    (self.player_positions[0][0] - 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] - 1),
                    (self.player_positions[2][0] + 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] + 1)
                ]
            # backwards
            if self.current_maze_index == 2:
                self.player_positions = [
                    (self.player_positions[0][0] + 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] + 1),
                    (self.player_positions[2][0] - 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] - 1)
                ]   
            # left
            if self.current_maze_index == 3:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] - 1),(self.player_positions[1][0] + 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] + 1),(self.player_positions[3][0] - 1, self.player_positions[3][1])
                    ]
            # right
            if self.current_maze_index == 1:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] + 1),(self.player_positions[1][0] - 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] - 1),(self.player_positions[3][0] + 1, self.player_positions[3][1])
                    ]
            
        elif right_area[0] <= mouse_pos[0] < right_area[1] and not self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['right']:
            self.total_position += 1  # Move left
            # straight
            if self.current_maze_index == 0:
                self.player_positions = [
                    (self.player_positions[0][0] + 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] + 1),
                    (self.player_positions[2][0] - 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] - 1)
                ]
            # backwards
            if self.current_maze_index == 2:
                self.player_positions = [
                    (self.player_positions[0][0] - 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] - 1),
                    (self.player_positions[2][0] + 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] + 1)
                ]
            # left
            if self.current_maze_index == 3:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] + 1),(self.player_positions[1][0] - 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] - 1),(self.player_positions[3][0] + 1, self.player_positions[3][1])
                    ]
            # right
            if self.current_maze_index == 1:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] - 1),(self.player_positions[1][0] + 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] + 1),(self.player_positions[3][0] - 1, self.player_positions[3][1])
                    ]
        self.note = False

    def handle_key_movement(self, event_key):
        self.note = False
        self.falses()
        if event_key == pygame.K_UP and not self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['top']:
            self.total_position += 0
            if self.current_maze_index == 0:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] - 1),(self.player_positions[1][0] + 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] + 1),(self.player_positions[3][0] - 1, self.player_positions[3][1])
                    ]
            if self.current_maze_index == 2:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] + 1),(self.player_positions[1][0] - 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] - 1),(self.player_positions[3][0] + 1, self.player_positions[3][1])
                    ]
            # left
            if self.current_maze_index == 3:
                self.player_positions = [
                    (self.player_positions[0][0] + 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] + 1),
                    (self.player_positions[2][0] - 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] - 1)
                    ]
            # right
            if self.current_maze_index == 1:
                self.player_positions = [
                    (self.player_positions[0][0] - 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] - 1),
                    (self.player_positions[2][0] + 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] + 1)
                    ]
                                        
        elif event_key == pygame.K_DOWN and not self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['bottom']:
            self.total_position += 2
            if self.current_maze_index == 0:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] + 1),(self.player_positions[1][0] - 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] - 1),(self.player_positions[3][0] + 1, self.player_positions[3][1])
                ]
            if self.current_maze_index == 2:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] - 1),(self.player_positions[1][0] + 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] + 1),(self.player_positions[3][0] - 1, self.player_positions[3][1])
                ]
            if self.current_maze_index == 1:
                self.player_positions = [
                    (self.player_positions[0][0] + 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] + 1),
                    (self.player_positions[2][0] - 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] - 1)
                    ]
            if self.current_maze_index == 3:
                self.player_positions = [
                    (self.player_positions[0][0] - 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] - 1),
                    (self.player_positions[2][0] + 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] + 1)
                    ]
                                        
        elif event_key == pygame.K_LEFT and not self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['left']:
            self.total_position -= 1
            # straight
            if self.current_maze_index == 0:
                self.player_positions = [
                    (self.player_positions[0][0] - 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] - 1),
                    (self.player_positions[2][0] + 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] + 1)
                ]
            # backwards
            if self.current_maze_index == 2:
                self.player_positions = [
                    (self.player_positions[0][0] + 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] + 1),
                    (self.player_positions[2][0] - 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] - 1)
                ]   
            # left
            if self.current_maze_index == 3:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] - 1),(self.player_positions[1][0] + 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] + 1),(self.player_positions[3][0] - 1, self.player_positions[3][1])
                    ]
            # right
            if self.current_maze_index == 1:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] + 1),(self.player_positions[1][0] - 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] - 1),(self.player_positions[3][0] + 1, self.player_positions[3][1])
                    ]
            
        elif event_key == pygame.K_RIGHT and not self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['right']:
            self.total_position += 1
            # straight
            if self.current_maze_index == 0:
                self.player_positions = [
                    (self.player_positions[0][0] + 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] + 1),
                    (self.player_positions[2][0] - 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] - 1)
                ]
            # backwards
            if self.current_maze_index == 2:
                self.player_positions = [
                    (self.player_positions[0][0] - 1, self.player_positions[0][1]),(self.player_positions[1][0], self.player_positions[1][1] - 1),
                    (self.player_positions[2][0] + 1, self.player_positions[2][1]),(self.player_positions[3][0], self.player_positions[3][1] + 1)
                ]
            # left
            if self.current_maze_index == 3:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] + 1),(self.player_positions[1][0] - 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] - 1),(self.player_positions[3][0] + 1, self.player_positions[3][1])
                    ]
            # right
            if self.current_maze_index == 1:
                self.player_positions = [
                    (self.player_positions[0][0], self.player_positions[0][1] - 1),(self.player_positions[1][0] + 1, self.player_positions[1][1]),
                    (self.player_positions[2][0], self.player_positions[2][1] + 1),(self.player_positions[3][0] - 1, self.player_positions[3][1])
                    ]

    def pick_note(self):
        if not hasattr(self, 'last_points'):
            self.last_points = -1  # or whatever makes sense for starting value

        if self.player_total_points != self.last_points:
            self.last_points = self.player_total_points
            note_notes = (
                "don't lose the light", "the walls turn", "you shouldn't be here", "there's only one way out",
                "i saw myself, but it wasn't me", "the notes write back", "they moved the exit again",
                "hello?", "which maze am i in?", "it keeps expanding", "wrong turn. very wrong.",
                "skeleton keeps you safe", "be scared of the dark", " go down to go up"
            )
            self.current_note = random.choice(note_notes)
        else:
            self.current_note = ""
        self.showing_note = True
                
    async def main(self):
        running = True
        clock = pygame.time.Clock()
        time_elapsed = 0

        while running:
            self.screen.fill(self.colors["GREY"])
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.launch_launcher()
                    elif event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_m:
                        self.toggle_minimap()
                    elif event.key == pygame.K_SPACE and self.player_positions[self.current_maze_index] == self.end_positions[self.current_maze_index]:
                        self.player_total_points += 1
                        self.next_game()
                    else:
                        event_key = event.key
                        self.handle_key_movement(event_key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse_pos = event.pos
                        self.handle_click(mouse_pos)

            if self.gamestate:
                time_elapsed += self.dt

                # Determine current maze index
                if self.total_position % 4 == 0 or self.total_position == 0:
                    self.current_maze_index = 0
                elif self.total_position % 2 == 0:
                    self.current_maze_index = 2
                elif self.total_position % 4 == 3 or self.total_position == -1:
                    self.current_maze_index = 1
                elif self.total_position % 4 == 1 or self.total_position == 1:
                    self.current_maze_index = 3

                # Determine walls
                if self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['top']:
                    self.top_wall = True
                if self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['bottom']:
                    self.bottom_wall = True
                if self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['right']:
                    self.left_wall = True
                if self.mazes[self.current_maze_index][self.player_positions[self.current_maze_index][1]][self.player_positions[self.current_maze_index][0]]['left']:
                    self.right_wall = True

                # Check if the player is at the start
                if self.player_positions[self.current_maze_index] == self.start_positions[self.current_maze_index]:
                    self.start = True

                # Check if the player reached the end
                if self.player_positions[self.current_maze_index] == self.end_positions[self.current_maze_index]:
                    self.end = True

                # Check for other events in the maze
                if self.player_positions[self.current_maze_index] == self.skeleton_positions[self.current_maze_index] \
                and not self.start and not self.end:
                    self.skeleton = True
                    if self.player_total_points != self.last_skeleton:
                        self.last_skeleton = self.player_total_points
                        self.skeleton_count += 1

                if self.player_positions[self.current_maze_index] == self.painting_positions[self.current_maze_index] \
                and not self.start and not self.end and not (self.left_wall and self.right_wall):
                    self.painting = True
                    if self.player_total_points != self.last_painting:
                        self.last_painting = self.player_total_points
                        self.painting_count += 1

                if self.player_positions[self.current_maze_index] == self.note_positions[self.current_maze_index] \
                and self.current_maze_index == self.maze_for_note and not self.start and not self.end:
                    self.note = True
                    if self.player_total_points != self.last_note:
                        self.last_note = self.player_total_points
                        self.note_count += 1

                if self.player_positions[self.current_maze_index] == self.grimreaper_positions[self.current_maze_index]\
                and not self.start and not self.end and not self.skeleton and not self.note and not self.painting \
                and self.top_wall and self.right_wall and self.left_wall and self.player_total_points > 0:
                    self.grimreaper = True
                    self.start_fade_out()
                    self.gamestate = False

                # grimreapers avoided
                # if self.player_positions[self.current_maze_index] == self.grimreaper_positions[self.current_maze_index]\
                # and not self.start and not self.end and (self.skeleton or self.note or self.painting) \
                # and self.top_wall and self.right_wall and self.left_wall and self.player_total_points > 0:
                #     self.grimreaper = True
                #     self.fade_out()
                #     self.gamestate = False
                #     if self.player_total_points != self.last_grimreaper:
                #         self.last_grimreaper = self.player_total_points
                #         self.grimreaper_count += 1
                #     print('saved from grimreaper')

                # grimreapers avoided
                if self.player_positions[self.current_maze_index] == self.grimreaper_positions[self.current_maze_index]\
                    and (self.skeleton or self.spider or self.note or self.painting):
                    if self.player_total_points != self.last_grimreaper:
                        self.last_grimreaper = self.player_total_points
                        self.grimreaper_count += 1
                    print('avoided from grimreaper')

                elif self.player_positions[self.current_maze_index] == self.grimreaper_positions[self.current_maze_index]:
                    if self.player_total_points != self.last_grimreaper:
                        self.last_grimreaper = self.player_total_points
                        self.grimreaper_count += 1
                    print(' grimreaper qwas her')

                if self.player_positions[self.current_maze_index] == self.spider_positions[self.current_maze_index]:
                    self.spider = True
                    if self.player_total_points != self.last_spider:
                        self.last_spider = self.player_total_points
                        self.spider_count += 1

                if self.player_positions[self.current_maze_index] == self.ladder_positions[self.current_maze_index]\
                and not self.skeleton and not self.note and not self.painting and not self.grimreaper and not self.spider\
                and not self.end and self.player_total_points > 5 and self.player_total_points % 2 != 0:
                    self.ladder = True
                    self.start_fade_out()
                    self.gamestate = False

                self.draw_wall_images()
                
                if self.showing_note:
                    pygame.draw.rect(self.screen, self.colors["GREY3"], (30, 100, 750, 450))
                    self.draw_text(self.current_note, 80, 300, self.colors["BLACK"])
                    if pygame.time.get_ticks() - self.note_start_time > 5000:
                        self.showing_note = False

                if self.fading:
                    fade_surface = pygame.Surface(self.screen.get_size())
                    fade_surface.fill(self.fade_color)
                    fade_surface.set_alpha(self.fade_alpha)
                    self.screen.blit(fade_surface, (0, 0))

                    self.fade_alpha += self.fade_speed
                    if self.fade_alpha >= 255:
                        self.fade_alpha = 255
                        self.fading = False  # Fade complete

                if self.end and self.player_total_points == 0:
                    self.draw_text('press SPACE to continue...', self.screen_width - 650, self.screen_height - 50, self.colors["GREY2"])

                if self.minimap == True:
                    self.draw_maze(self.mazes[self.current_maze_index])
                    self.draw_player(self.player_positions[self.current_maze_index])
                
                # self.player_points = f'{int(self.player_total_points)}'
                # self.draw_text(self.player_points, self.screen_width - 200, self.screen_height // 10, self.colors["BLACK"])
                
            else:
                self.screen.fill(self.colors["GREY"])
                self.draw_text(f"FINAL SCORE: {self.player_total_points}", self.screen_width // 5, self.screen_height // 2, self.colors["BLACK"])

            pygame.display.flip()
            self.dt = clock.tick(60) / 1000
            await asyncio.sleep(0)
        
        pygame.quit()

if __name__ == "__main__":
    game = GameWindow()
    asyncio.run(game.main())