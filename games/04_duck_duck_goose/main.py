import math
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
        pygame.display.set_caption("Duck Duck Goose")
        self.colors = {"WHITE": (255, 255, 255), "GREY": (178, 190, 181), "BLACK": (0, 0, 0), 
                       "RED": (210, 43, 43), "GREEN": (49, 146, 54), "BLUE": (76, 81, 247),
                       "PURPLE": (157, 77, 187), "GOLD": (243, 175, 25), "GREY2": (100, 100, 100)}
        self.font = pygame.font.SysFont(None, 55)
        self.dt = 0
        self.bird_amount = 3
        self.bird_images = self.load_bird_images()
        self.reset_game()
        self.shots = []
        self.hitbox = False
        self.score_popups = []
        self.kill_points = 0

    def load_bird_images(self):
        all_birds = [
            'Albatross', 'Crow', 'Duck', 'Eagle', 'Falcon', 'Flamingo', 
            'Goose', 'Heron', 'Hummingbird', 'Owl', 'Pidgeon'
        ]
        selected_birds = random.sample(all_birds, self.bird_amount)  # Randomly select 5 birds
        images = {}
        for bird in selected_birds:
            path = os.path.join("images", "birds", f"{bird}.png")
            try:
                image = pygame.image.load(path)
                images[bird] = image 
            except pygame.error as e:
                print(f"Error loading {bird}.png: {e}")
                images[bird] = None  # Placeholder for missing images
        return images

    def load_bg_images(self, mouse_x, mouse_y):
        try:
            gun = pygame.image.load(os.path.join("images", "background", "gun.png"))
            new_height = 200
            aspect_ratio = gun.get_width() / gun.get_height()
            new_width = int(new_height * aspect_ratio)
            gun = pygame.transform.scale(gun, (new_width, new_height))
            # Adjust the gun's position relative to the mouse
            image_rect = gun.get_rect(midbottom=(mouse_x, self.screen_height + mouse_y * 0.1))
            self.screen.blit(gun, image_rect)
        except pygame.error as e:
            print(f"Error loading gun image: {e}")
            
    def load_bg(self):
        try:
            bg = pygame.image.load(os.path.join("images", "background", "skywithtrees.jpg"))
            bg = pygame.transform.scale(bg, (self.screen_width, self.screen_height))  # Ensure full-screen fit
            self.screen.blit(bg, (0, 0))  # Draw background at the top-left corner
        except pygame.error as e:
            print(f"Error loading background image: {e}")
            
    def draw_hitbox(self, bird):
        if bird["image"]:
            # Define top or bottom birds
            upper_birds = ['Albatross', 'Flamingo', 'Heron', 'Hummingbird', 'Owl']
            if bird["bird_type"] in upper_birds:
                top_or_bottom = bird["size"] // 2
            elif bird["bird_type"] == 'Falcon':
                top_or_bottom = bird["size"] // 3
            else:
                top_or_bottom = 0
            bird_rect = pygame.Rect(
                int(bird["pos"].x) - bird["size"] // 2, 
                int(bird["pos"].y) - top_or_bottom, 
                bird["size"], 
                bird["size"] // 2
            )
            pygame.draw.rect(self.screen, self.colors["RED"], bird_rect, 2)  # Red rectangle around birds

    def next_round(self):
        if self.wave_height < 300:
            self.wave_height = self.wave_height + 30
        if self.speed < 10:
            self.speed = self.speed * 1.10
        self.interval = self.interval * 1.1
        # Generate a new sequence of three target birds (can repeat)
        self.target_sequence = [random.choice(list(self.bird_images.keys())) for _ in range(3)]
        self.current_target_index = 0  # Track progress through the sequence

    def reset_game(self):
        self.birds = []
        self.explosions = []
        self.kill_points = 0
        self.player_total_points = 0
        self.gamestate = True
        self.wave_height = 10
        self.speed = 1
        self.interval = 0.005
        self.point_multiplier = 1 * self.bird_amount
        if self.bird_amount >= 5:
            self.speed = 1
            self.interval = 0.025
        
        # Generate a new sequence of three target birds (can repeat)
        self.target_sequence = [random.choice(list(self.bird_images.keys())) for _ in range(3)]
        self.current_target_index = 0  # Track progress through the sequence

    def spawn_bird(self, direction):
        bird_type = random.choice(list(self.bird_images.keys()))
        x_pos = 0 if direction == "left" else self.screen_width
        y_pos = random.randint(50, self.screen_height - 200)
        speed_x = random.randint(100, 300) * (1 if direction == "left" else -1) * self.speed
        wave_amplitude = random.randint(5, self.wave_height) 
        wave_frequency = 2
        size = random.randint(50, 150)  # Random size per bird spawn
        
        if self.bird_images[bird_type]:
            original_image = self.bird_images[bird_type]
            aspect_ratio = original_image.get_height() / original_image.get_width()
            new_width = size
            new_height = int(new_width * aspect_ratio)
            resized_image = pygame.transform.scale(original_image, (new_width, new_height))
        else:
            resized_image = None
        
        self.birds.append({
            "pos": pygame.Vector2(x_pos, y_pos),
            "speed_x": speed_x,
            "wave_amplitude": wave_amplitude,
            "wave_frequency": wave_frequency,
            "start_y": y_pos,
            "time_offset": random.uniform(0, math.pi * 2),
            "direction": direction,
            "bird_type": bird_type,
            "image": resized_image,
            "size": size
        })

    def explode_bird(self, bird, x, y):
        if bird["bird_type"] == self.target_sequence[self.current_target_index]:
            self.kill_points += (10 * self.point_multiplier)
            self.interval = self.interval * 1.1
            self.player_total_points += self.kill_points
            score_text = '+ ' + str(self.kill_points)
            self.score_popups.append({"pos": pygame.Vector2(x, y), "text": score_text, "timer": 30})
            self.explosions.append({"pos": bird["pos"].copy(), "radius": 5, "max_radius": 50})
            self.birds.remove(bird)
            self.current_target_index += 1  # Move to the next target in the sequence

            if self.current_target_index == len(self.target_sequence):
                self.next_round()  # Generate a new sequence of 3 birds after winning
        else:
            self.gamestate = False  # Lose if you click the wrong bird 
            
    def gun_shots(self):
        x, y = pygame.mouse.get_pos()
        self.shots.append({"pos": pygame.Vector2(x, y), "radius": 5, "max_radius": 20})
        if self.player_total_points > 0:
            self.player_total_points -= 1  # Reward points for correct click

    def draw_text(self, text, x, y, color):
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def draw_sequence(self):
        """Display the target sequence at the top of the screen."""
        x_offset = 20
        # y_offset = self.screen_height - 400
        for i, bird in enumerate(self.target_sequence):
            color = self.colors["GREEN"] if i < self.current_target_index else self.colors["WHITE"]
            self.draw_text(bird, x_offset, self.screen_height - 50, color)
            # self.draw_text(bird, 200, y_offset, color)
            x_offset += self.screen_width // 3
            # y_offset += 40

    def draw_crosshair(self, mouse_x, mouse_y):
        # Draw horizontal line
        pygame.draw.line(self.screen, self.colors["RED"], (mouse_x - 15, mouse_y), (mouse_x + 15, mouse_y), 2)
        # Draw vertical line
        pygame.draw.line(self.screen, self.colors["RED"], (mouse_x, mouse_y - 15), (mouse_x, mouse_y + 15), 2)

    def hitbox_toggle(self):
        self.hitbox = not self.hitbox

    def mode(self, n):
        self.bird_amount = n
        self.bird_images = self.load_bird_images()
        self.reset_game()

    async def main(self):
        running = True
        clock = pygame.time.Clock()
        time_elapsed = 0
        
        pygame.mouse.set_visible(False)

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    if event.key == pygame.K_ESCAPE:
                        pass
                elif event.type == pygame.MOUSEBUTTONDOWN and self.gamestate:
                    x, y = pygame.mouse.get_pos()
                    self.gun_shots()
                    for bird in self.birds[:]:
                        # Create the hitbox using the same logic as `draw_hitbox`
                        upper_birds = ['Albatross', 'Flamingo', 'Heron', 'Hummingbird', 'Owl']
                        if bird["bird_type"] in upper_birds:
                            top_or_bottom = bird["size"] // 2
                        elif bird["bird_type"] == 'Falcon':
                            top_or_bottom = bird["size"] // 3
                        else:
                            top_or_bottom = 0

                        bird_rect = pygame.Rect(
                            int(bird["pos"].x) - bird["size"] // 2, 
                            int(bird["pos"].y) - top_or_bottom, 
                            bird["size"], 
                            bird["size"] // 2
                        )

                        # Check if mouse click is inside the hitbox
                        if bird_rect.collidepoint(x, y):
                            self.explode_bird(bird, x, y)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_h:  # Fix event check
                    self.hitbox_toggle()
                if event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_9:
                    self.mode(event.key - pygame.K_1 + 1)                   

            if self.gamestate:
                self.load_bg()
                if len(self.birds) == 0:
                    self.spawn_bird(random.choice(["left", "right"]))
                if random.random() < self.interval:
                    self.spawn_bird("left")
                if random.random() < self.interval:
                    self.spawn_bird("right")

                time_elapsed += self.dt
                for bird in self.birds:
                    bird["pos"].x += bird["speed_x"] * self.dt
                    bird["pos"].y = bird["start_y"] + bird["wave_amplitude"] * math.sin(pygame.time.get_ticks() * 0.002 * bird["wave_frequency"] + bird["time_offset"])
                    
                    if bird["image"]:
                        image = pygame.transform.flip(bird["image"], bird["direction"] == "right", False)
                        self.screen.blit(image, (int(bird["pos"].x) - bird["size"] // 2, int(bird["pos"].y) - bird["size"] // 2))
                        if self.hitbox == True:
                            self.draw_hitbox(bird)
                
                self.birds = [b for b in self.birds if -50 <= b["pos"].x <= self.screen_width + 50]
            
                self.draw_text(f'{int(self.player_total_points)}', self.screen_width - 200, self.screen_height // 10, self.colors["WHITE"])
                self.draw_sequence()  # Draw the sequence at the top

                # Get mouse position
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Draw crosshair at the mouse position
                self.draw_crosshair(mouse_x, mouse_y)

                for shot in self.shots[:]:
                    shot["radius"] += 3
                    if shot["radius"] >= shot["max_radius"]:
                        self.shots.remove(shot)
                    else:
                        pygame.draw.circle(self.screen, self.colors["GREY2"], (int(shot["pos"].x), int(shot["pos"].y)), shot["radius"], 3)

                for explosion in self.explosions[:]:
                    explosion["radius"] += 5
                    if explosion["radius"] >= explosion["max_radius"]:
                        self.explosions.remove(explosion)
                    else:
                        pygame.draw.circle(self.screen, self.colors["RED"], (int(explosion["pos"].x), int(explosion["pos"].y)), explosion["radius"], 3)

                for popup in self.score_popups[:]:
                    self.draw_text(popup["text"], int(popup["pos"].x), int(popup["pos"].y), self.colors["GOLD"])
                    popup["timer"] -= 1
                    popup["pos"].y -= 1  # Move the text upwards
                    if popup["timer"] <= 0:
                        self.score_popups.remove(popup)

                # Load gun
                self.load_bg_images(mouse_x, mouse_y)

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