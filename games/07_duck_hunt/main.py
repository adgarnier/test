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
        pygame.display.set_caption("Duck Hunt")
        self.colors = {
            "WHITE": (255, 255, 255), "GREY": (178, 190, 181), "BLACK": (0, 0, 0), 
            "RED": (210, 43, 43), "GREEN": (49, 146, 54), "BLUE": (76, 81, 247),
            "PURPLE": (157, 77, 187), "GOLD": (243, 175, 25), "GREY2": (100, 100, 100)
        }
        self.font = pygame.font.SysFont(None, 55)
        self.dt = 0
        self.bird_amount = 10  # ← FIXED: define how many birds you want
        self.gamestate = True  # ← FIXED: initialize game state
        self.hitbox = False  # ← FIXED: default hitbox toggle
        self.player_total_points = 0
        self.bird_height = 500
        self.bird_images = self.load_bird_images()
        self.bg_image = self.load_large_bg()
        
        self.bird_pos = self.random_bird_position()
        self.bird_type, self.bird_image = random.choice(list(self.bird_images.items()))
        
        self.bird_rect_on_screen = pygame.Rect(0, 0, 0, 0)
        
        self.show_bird_info = False

    def random_bird_position(self):
        if not self.bg_image:
            return pygame.Vector2(0, 0)
        bg_width, bg_height = self.bg_image.get_size()
        margin = self.bird_height
        x = random.randint(margin, bg_width - margin - 1)
        y = random.randint(margin, bg_height - margin - 1)
        return pygame.Vector2(x, y)

    def load_bird_images(self):
        all_birds = [
            'Albatross', 'Crow', 'Duck', 'Eagle', 'Falcon', 
            'Goose', 'Heron', 'Hummingbird', 'Owl', 'Pidgeon'
        ]
        selected_birds = random.sample(all_birds, self.bird_amount)
        images = {}
        for bird in selected_birds:
            path = os.path.join("images", "birds", f"{bird}.png")
            try:
                image = pygame.image.load(path)
                images[bird] = image 
            except pygame.error as e:
                print(f"Error loading {bird}.png: {e}")
                images[bird] = None
        return images
            
    def load_bg(self, mouse_x, mouse_y):
        if not self.bg_image:
            return
        
        bg_width, bg_height = self.bg_image.get_size()

        # How far can we scroll?
        max_x_offset = bg_width - self.screen_width
        max_y_offset = bg_height - self.screen_height

        # Calculate offset based on mouse position (center is no movement)
        offset_x = int((mouse_x / self.screen_width - 0.5) * 2 * max_x_offset * 0.5)
        offset_y = int((mouse_y / self.screen_height - 0.5) * 2 * max_y_offset * 0.5)

        # Clamp to image bounds
        offset_x = max(0, min(max_x_offset, offset_x + max_x_offset // 2))
        offset_y = max(0, min(max_y_offset, offset_y + max_y_offset // 2))

        # Blit cropped portion of background
        crop_rect = pygame.Rect(offset_x, offset_y, self.screen_width, self.screen_height)
        self.screen.blit(self.bg_image, (0, 0), crop_rect)
        
        if self.bird_image:
            screen_bird_x = self.bird_pos.x - offset_x
            screen_bird_y = self.bird_pos.y - offset_y

            original_image = self.bird_image
            new_height = self.bird_height
            aspect_ratio = original_image.get_width() / original_image.get_height()
            new_width = int(new_height * aspect_ratio)
            self.small_bird = pygame.transform.scale(original_image, (new_width, new_height))

            self.bird_rect_on_screen = pygame.Rect(screen_bird_x, screen_bird_y, new_width, new_height)
            self.screen.blit(self.small_bird, self.bird_rect_on_screen.topleft)

            if self.hitbox:
                pygame.draw.rect(self.screen, self.colors["RED"], self.bird_rect_on_screen, 2)
            
    def load_large_bg(self):
        try:
            bg_name = random.choice([
                "city.jpg", "city2.jpg", "city3.jpg", "city4.jpg", "city5.jpg", "city6.jpg",
                "city7.jpg", "city8.jpg", "city9.jpg", "city10.jpg", "city11.jpg"])
            bg_path = os.path.join("images", "background", bg_name)
            bg = pygame.image.load(bg_path).convert()
            print(f"Loaded background: {bg_name}")
            return bg
        except pygame.error as e:
            print(f"Error loading background image: {e}")
            return pygame.Surface((self.screen_width, self.screen_height))  # Fallback

    def next_round(self):
        if self.player_total_points % 3 == 0 and self.bird_height > 10:
            self.bird_height = int(self.bird_height * 0.5)
        print(self.bird_height)
        self.bg_image = self.load_large_bg()
        self.bird_pos = self.random_bird_position()
        self.bird_type, self.bird_image = random.choice(list(self.bird_images.items()))

    def reset_game(self):
        self.player_total_points = 0
        self.gamestate = True
        self.next_round()

    def draw_text(self, text, x, y, color):
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def hitbox_toggle(self):
        self.hitbox = not self.hitbox

    def display_all_bird_images(self):
        self.screen.fill(self.colors["GREY2"])
        padding = 20
        x, y = padding, padding
        max_height_in_row = 0

        for bird_name, image in self.bird_images.items():
            if image is None:
                continue

            scaled_height = 130
            aspect_ratio = image.get_width() / image.get_height()
            scaled_width = int(scaled_height * aspect_ratio)
            scaled_img = pygame.transform.scale(image, (scaled_width, scaled_height))

            if x + scaled_width > self.screen_width - padding:
                x = padding
                y += max_height_in_row + padding
                max_height_in_row = 0

            self.screen.blit(scaled_img, (x, y))
            # label = self.font.render(bird_name, True, self.colors["WHITE"])
            # self.screen.blit(label, (x, y + scaled_height + 5))

            x += scaled_width + padding
            max_height_in_row = max(max_height_in_row, scaled_height + 5)

    async def main(self):
        running = True
        clock = pygame.time.Clock()
        time_elapsed = 0

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.launch_launcher()
                    elif event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_h:
                        self.hitbox_toggle()
                    elif event.key == pygame.K_i:
                        self.show_bird_info = not self.show_bird_info
                elif event.type == pygame.MOUSEBUTTONDOWN and self.gamestate:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if self.bird_rect_on_screen.collidepoint(mouse_x, mouse_y):
                        print("Bird hit!")
                        self.player_total_points += 1
                        self.next_round()
                    else:
                        print("Missed!")

            if self.show_bird_info:
                self.display_all_bird_images()
            elif self.gamestate:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.load_bg(mouse_x, mouse_y)
                time_elapsed += self.dt
                self.draw_text(f'{int(self.player_total_points)}', self.screen_width - 200, self.screen_height // 10, self.colors["WHITE"])
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