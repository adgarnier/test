import pygame
import random
import os
import asyncio

class GameWindow():
    def __init__(self):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Drinking Game")

        # Colors
        self.WHITE = (255, 255, 255)
        self.GREY = (178, 190, 181)
        self.BLACK = (0, 0, 0)
        self.RED = (210, 43, 43)
        self.GREEN = (49, 146, 54)
        self.BLUE = (76, 81, 247)
        self.PURPLE = (157, 77, 187)
        self.GOLD = (243, 175, 25)
        self.GREY2 = (100, 100, 100)
        self.BROWN = (137, 81, 41)

        self.font = pygame.font.SysFont(None, 55)
        self.dt = 0
        self.beer_images = self.load_beer_images('images/beers')
        self.selected_beer_images = []
        self.selected_hat = None
        self.speed_max = 1400
        self.mouse_held_down = False

        self.next_sequence_ready = False  # <-- NEW FLAG
        self.reset_game()

    def reset_game(self):
        self.player_total_points = 0
        self.speed_max = 1400
        self.gamestate = True
        self.selected_beer_images = self.select_unique_random_beer_images()
        hat_images = [f for f in os.listdir("images/fishhats") if f.endswith(".png")]
        if hat_images:
            random_hat = random.choice(hat_images)
            self.selected_hat = pygame.image.load(os.path.join("images/fishhats", random_hat))
            self.selected_hat = pygame.transform.scale(self.selected_hat, (150, 150))
        self.sequence = []
        self.user_sequence = []

    def load_beer_images(self, folder):
        beer_images = {}
        image_list = [
            'alexanderkeiths', 'becks', 'budweiser', 'budlight', 'busch', 'carlsberg', 'chambly', 'coorslight',
            'corona', 'heineken', 'hoegaarden', 'hofbrau', 'iceberg', 'labattblue', 'michelobultra', 'millerlite',
            'modelo', 'molsoncanadian', 'moosehead', 'sapporo', 'stellaartois', 'tsingtao'
        ]
        for image in image_list:
            image_path = os.path.join(folder, f'{image}.png')
            if os.path.exists(image_path):
                beer_images[image] = pygame.image.load(image_path)
            else:
                print(f'Warning: Image not found for {image}')
        return beer_images

    def load_bg(self):
        try:
            bg = pygame.image.load(os.path.join("images", "beers", "pub1.jpeg"))
            bg = pygame.transform.scale(bg, (self.screen_width, self.screen_height))
            man = pygame.image.load(os.path.join("images", "beers", "man.png"))
            man = pygame.transform.scale(man, (self.screen_width, self.screen_height))
            self.screen.blit(bg, (0, 0))
            self.screen.blit(man, (0, 0))
        except pygame.error as e:
            print(f"Error loading background image: {e}")

    def select_unique_random_beer_images(self):
        return random.sample(list(self.beer_images.keys()), 7)

    def background(self):
        self.screen.fill(self.GREY)
        self.load_bg()
        if self.selected_hat:
            hat_rect = self.selected_hat.get_rect(midtop=(self.screen_width // 2, 20))
            self.screen.blit(self.selected_hat, hat_rect)
        pygame.draw.rect(self.screen, self.BROWN, [0, self.screen_height // 1.25, self.screen_width, 300])
        self.draw_text(str(int(self.player_total_points)), self.screen_width - 200, self.screen_height // 10, self.WHITE)

    async def generate_sequence(self):
        self.sequence.append(random.randint(0, 6))
        await self.show_sequence()

    async def show_sequence(self):
        self.background()
        pygame.display.flip()
        for i in self.sequence:
            beer_key = self.selected_beer_images[i]
            beer_image = self.beer_images.get(beer_key)
            if beer_image:
                new_height = 300
                aspect = beer_image.get_width() / beer_image.get_height()
                new_width = int(new_height * aspect)
                beer_image = pygame.transform.scale(beer_image, (new_width, new_height))
                left_img = pygame.transform.rotate(beer_image, 245)
                right_img = pygame.transform.rotate(beer_image, 115)
                left_rect = left_img.get_rect(center=(250, 100))
                right_rect = right_img.get_rect(center=(550, 100))
                table_rect = beer_image.get_rect(center=(random.randint(100, self.screen_width - 100), random.randint(self.screen_height - 200, self.screen_height - 150)))
                chosen_img, chosen_rect = random.choice([(left_img, left_rect), (right_img, right_rect)])
                self.background()
                self.screen.blit(chosen_img, chosen_rect)
                pygame.display.flip()
                await asyncio.sleep(random.randint(500, self.speed_max) / 1000)
                self.background()
                self.screen.blit(beer_image, table_rect)
                pygame.display.flip()
                await asyncio.sleep(random.randint(100, 500) / 1000)

    def draw_text(self, text, x, y, color):
        surface = self.font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def button_clicked(self, index):
        self.user_sequence.append(index)
        self.player_total_points += 1
        if self.user_sequence == self.sequence[:len(self.user_sequence)]:
            if len(self.user_sequence) == len(self.sequence):
                if self.speed_max > 425:
                    self.speed_max = round(self.speed_max * 0.95)
                self.user_sequence = []
                self.next_sequence_ready = True  # <-- set flag to continue
        else:
            print("Incorrect sequence!")
            print("seq:", self.sequence)
            print("user:", self.user_sequence)
            self.player_total_points -= 1
            self.gamestate = False

    async def main(self):
        clock = pygame.time.Clock()
        first_time = True
        running = True

        while running:
            if first_time:
                await self.generate_sequence()
                first_time = False

            if self.next_sequence_ready:
                await self.generate_sequence()
                self.next_sequence_ready = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    elif event.key == pygame.K_r:
                        self.reset_game()
                        await self.generate_sequence()

            self.background()

            if self.gamestate:
                self.beer_click_width = self.screen_width // 10
                self.beer_click_height = self.screen_height // 3 + 100
                self.first_beer_position_x = self.screen_width // 10 - 20
                self.beer_position_y = self.screen_height // 2 - 20
                colors = [self.GREY2, self.RED, self.BLUE, self.GOLD, self.BLACK, self.WHITE, self.PURPLE]

                def draw_beer_button(x_offset, key, idx):
                    rect = pygame.Rect(
                        self.first_beer_position_x + x_offset,
                        self.beer_position_y,
                        self.beer_click_width,
                        self.beer_click_height
                    )
                    mouse = pygame.mouse.get_pos()
                    click = pygame.mouse.get_pressed()
                    if rect.collidepoint(mouse) and click[0] == 1 and not self.mouse_held_down:
                        self.mouse_held_down = True
                        self.button_clicked(idx)
                    elif click[0] == 0:
                        self.mouse_held_down = False

                    image = self.beer_images.get(key)
                    if image:
                        aspect = image.get_width() / image.get_height()
                        resized = pygame.transform.scale(image, (int(300 * aspect), 300))
                        rect = resized.get_rect(center=(self.first_beer_position_x + x_offset + 40, self.beer_position_y + 150))
                        self.screen.blit(resized, rect)

                for i, color in enumerate(colors):
                    draw_beer_button(600 - 100 * i, self.selected_beer_images[i], i)
            else:
                self.screen.fill(self.GREY)
                final_text = f'FINAL SCORE: {int(self.player_total_points)}'
                self.draw_text(final_text, self.screen_width // 5, self.screen_height // 2, self.BLACK)

            pygame.display.flip()
            self.dt = clock.tick(60) / 1000
            await asyncio.sleep(0)

        pygame.quit()

if __name__ == "__main__":
    game = GameWindow()
    asyncio.run(game.main())
