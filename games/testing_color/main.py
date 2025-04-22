import pygame
import random
import sys
import colorsys
import subprocess
import sys
import asyncio

class GameWindow:
    def __init__(self):
        pygame.init()

        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Color Correct")

        self.GREY = (178, 190, 181)
        self.BLACK = (0, 0, 0)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)

        self.flash_size = 250
        self.choice_size = 147  # Fixed size for squares
        self.margin = 10       # Margin between squares
        self.font = pygame.font.SysFont(None, 48)

        self.clock = pygame.time.Clock()
        self.dt = 0

        self.round = 1
        self.score = 0  # Initialize score
        self.hue = random.uniform(0, 1)
        self.next_round()

    def generate_shades(self, hue, num_shades=28):
        colors = {}
        for i in range(num_shades):
            t = i / (num_shades - 1)
            value = 0.2 + (0.8 * t)
            saturation = 1.0 - (0.9 * t)
            rgb_float = colorsys.hsv_to_rgb(hue, saturation, value)
            rgb = tuple(int(c * 255) for c in rgb_float)
            colors[f"Shade-{i}"] = rgb
        return colors

    def calculate_difficulty(self):
        self.num_shades = min(3 + self.round * 2, 15)
        self.flash_duration = max(1000 - self.round * 100, 200)
        if self.flash_duration < 200:
            self.flash_duration = max(1000 - self.round * 20, 50)

    def reset(self):
        self.round = 1
        self.score = 0  # Reset score
        self.hue = random.uniform(0, 1)
        self.next_round()

    def next_round(self):
        self.calculate_difficulty()
        self.COLORS = self.generate_shades(self.hue, self.num_shades)
        self.flash_color_name = random.choice(list(self.COLORS.keys()))
        self.flash_color = self.COLORS[self.flash_color_name]
        self.flash_start_time = pygame.time.get_ticks()
        self.showing_flash = True
        self.user_selected = False
        self.result_text = ""
        self.choice_rects = []
        self.correct_rect = None
        self.selected_rect = None

    def draw_flash_square(self):
        square = pygame.Rect(
            (self.screen_width - self.flash_size) // 2,
            300,
            self.flash_size,
            self.flash_size
        )
        pygame.draw.rect(self.screen, self.flash_color, square)

    def draw_choice_squares(self):
        max_per_row = (self.screen_width + self.margin) // (self.choice_size + self.margin)
        start_y = 80

        self.choice_rects = []
        for idx, (name, color) in enumerate(self.COLORS.items()):
            row = idx // max_per_row
            col = idx % max_per_row

            x = self.margin + col * (self.choice_size + self.margin)
            y = start_y + row * (self.choice_size + self.margin)

            rect = pygame.Rect(x, y, self.choice_size, self.choice_size)
            pygame.draw.rect(self.screen, color, rect)
            self.choice_rects.append((rect, name))

            # Draw borders if needed
            if self.user_selected:
                if name == self.flash_color_name:
                    pygame.draw.rect(self.screen, self.GREEN, rect, 5)
                elif self.selected_rect and rect == self.selected_rect:
                    pygame.draw.rect(self.screen, self.RED, rect, 5)

    def launch_launcher(self):
        pygame.quit()
        subprocess.run([sys.executable, "_launcher.py"])

    async def main(self):
        running = True
        while running:
            self.screen.fill(self.GREY)
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.launch_launcher()
                    elif event.key == pygame.K_r:
                        self.reset()
                elif not self.showing_flash and event.type == pygame.MOUSEBUTTONDOWN and not self.user_selected:
                    mouse_pos = event.pos
                    for rect, name in self.choice_rects:
                        if rect.collidepoint(mouse_pos):
                            if name == self.flash_color_name:
                                self.result_text = "Correct!"
                                self.correct_rect = rect
                                self.score += 1  # Increment score on correct choice
                            else:
                                self.result_text = "Wrong!"
                                self.correct_rect = next(r for r, n in self.choice_rects if n == self.flash_color_name)
                                self.selected_rect = rect
                            self.user_selected = True
                            pygame.time.set_timer(pygame.USEREVENT, 1500)

                elif event.type == pygame.USEREVENT:
                    pygame.time.set_timer(pygame.USEREVENT, 0)
                    self.round += 1
                    self.next_round()

            if self.showing_flash:
                if current_time - self.flash_start_time < self.flash_duration:
                    self.draw_flash_square()
                else:
                    self.showing_flash = False
            else:
                self.draw_choice_squares()

            round_info = self.font.render(f"Round {self.round}", True, self.BLACK)
            self.screen.blit(round_info, (20, 30))

            score_info = self.font.render(f"Score {self.score}", True, self.BLACK) 
            self.screen.blit(score_info, (600, 30))

            if self.user_selected:
                text = self.font.render(f"{self.result_text}", True, self.BLACK)
                self.screen.blit(text, ((self.screen_width - text.get_width()) // 2, 30))

            pygame.display.flip()
            self.dt = self.clock.tick(60) / 1000
            await asyncio.sleep(0)

        pygame.quit()
        sys.exit()

game = GameWindow()
asyncio.run(game.main())
