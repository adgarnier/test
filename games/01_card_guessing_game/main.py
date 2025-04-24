import pygame
import sys
import random
import os
import asyncio

class Deck:
    def __init__(self):
        self.cards = self.create_deck()
        self.removed_cards = []

    def create_deck(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
        return [{'rank': rank, 'suit': suit} for suit in suits for rank in ranks]

    def shuffle(self):
        random.shuffle(self.cards)

    def draw_card(self):
        if not self.cards:
            print('Deck is empty')
            return None
        card = self.cards.pop()
        self.removed_cards.append(card)
        return card

class GameWindow:
    def __init__(self):
        pygame.init()

        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Card Guessing Game")

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

        self.deck = Deck()
        self.deck.shuffle()

        self.font = pygame.font.SysFont(None, 55)
        self.drawn_card = None
        self.suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']

        self.card_images = self.load_card_images('images/playing-cards-master')   
        self.other_images = self.load_other_images('images/playing-cards-master')

        self.starting_points = 1000000     
        self.new_points_calc = self.starting_points
        self.player_total_points = 0
        self.guessed_card_counts = {}

        self.selected_suit_index = 0
        self.selected_rank_index = 0
        self.is_guess_correct = False

        pygame.key.set_repeat(200, 50)
        self.points_added = False
        self.gamestate = False
        self.viewing_removed_cards = False

    def draw_text(self, text, x, y, color):
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def load_card_images(self, folder):
        card_images = {}
        for suit in self.suits:
            for rank in self.ranks:
                card_name = f'{suit}_{rank}'
                image_path = os.path.join(folder, f'{card_name}.png')
                if os.path.exists(image_path):
                    card_images[card_name] = pygame.image.load(image_path)
        return card_images

    def load_other_images(self, folder):
        other_images = {}
        image_list = ['win_outline', 'trash_icon_small', 'back_dark', 'back_light', 'back_light_temp']
        for image in image_list:
            image_path = os.path.join(folder, f'{image}.png')
            if os.path.exists(image_path):
                other_images[image] = pygame.image.load(image_path)
        return other_images

    def handle_keydown(self, key):
        if key == pygame.K_SPACE:
            self.gamestate = True
            self.drawn_card = self.deck.draw_card()
            if self.drawn_card:
                self.points_added = False
                card_name = f'{self.drawn_card["suit"]}_{self.drawn_card["rank"]}'
                guess = f'{self.suits[self.selected_suit_index]}_{self.ranks[self.selected_rank_index]}'

                self.guessed_card_counts.setdefault(guess, 0)

                if self.guessed_card_counts[guess] < 3:
                    if guess.lower() == card_name.lower():
                        self.is_guess_correct = True
                        self.player_total_points += self.new_points_calc
                        self.new_points_calc = self.starting_points
                        self.deck = Deck()
                        self.deck.shuffle()
                        self.guessed_card_counts = {}
                    else:
                        self.guessed_card_counts[guess] += 1
                        self.is_guess_correct = False
                        self.new_points_calc *= 0.85
        elif key in [pygame.K_DOWN, pygame.K_s]:
            self.points_added = True
            self.selected_suit_index = (self.selected_suit_index + 1) % len(self.suits)
        elif key in [pygame.K_UP, pygame.K_w]:
            self.points_added = True
            self.selected_suit_index = (self.selected_suit_index - 1) % len(self.suits)
        elif key in [pygame.K_RIGHT, pygame.K_d]:
            self.points_added = True
            self.selected_rank_index = (self.selected_rank_index + 1) % len(self.ranks)
        elif key in [pygame.K_LEFT, pygame.K_a]:
            self.points_added = True
            self.selected_rank_index = (self.selected_rank_index - 1) % len(self.ranks)

    def draw_button(self, text, x, y, width, height, color, action=None):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, color, rect)
        self.draw_text(text, x + 10, y + 10, self.BLACK)
        if rect.collidepoint(mouse) and click[0] == 1 and action:
            action()

    def open_removed_cards_view(self):
        self.viewing_removed_cards = not self.viewing_removed_cards

    def draw_removed_cards(self):
        card_width, card_height = 63, 99
        max_cards_per_column = 5
        x_offset, y_offset = 40, 50
        column_count, card_counter = 0, 0

        sorted_cards = sorted(
            self.deck.removed_cards,
            key=lambda c: self.ranks.index(c['rank'])
        )

        for card in sorted_cards[-52:]:
            card_name = f"{card['suit']}_{card['rank']}"
            if card_name in self.card_images:
                img = pygame.transform.scale(self.card_images[card_name], (card_width, card_height))
                rect = img.get_rect(center=(x_offset, y_offset))
                self.screen.blit(img, rect)
                y_offset += 100
                card_counter += 1
                if card_counter == max_cards_per_column:
                    column_count += 1
                    y_offset = 50
                    x_offset += 72
                    card_counter = 0

        self.draw_button("Back to Game", self.screen_width // 3, self.screen_height - 70, 275, 50, self.BLUE, self.open_removed_cards_view)

    async def main(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        print('Restarting...')
                        self.deck = Deck()
                        self.deck.shuffle()
                        self.player_total_points = 0  # Reset player points if necessary
                        self.new_points_calc = self.starting_points  # Reset round points if necessary
                        self.guessed_card_counts = {}
                        self.gamestate = False
                    else:
                        self.handle_keydown(event.key)

            self.screen.fill(self.GREY)

            if self.viewing_removed_cards:
                self.draw_removed_cards()
                pygame.display.flip()
                await asyncio.sleep(0)
                continue

            if not self.deck.cards:
                self.draw_text(f'FINAL SCORE: {int(self.player_total_points)}', self.screen_width // 5, self.screen_height // 2, self.BLACK)
            else:
                other_img = self.other_images.get("back_light_temp")
                if other_img:
                    rect = other_img.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                    self.screen.blit(other_img, rect)

                self.draw_button("", self.screen_width - 150, self.screen_height - 150, 100, 100, self.GREY, self.open_removed_cards_view)
                trash_img = self.other_images.get("trash_icon_small")
                if trash_img:
                    rect = trash_img.get_rect(center=(self.screen_width - 100, self.screen_height - 100))
                    self.screen.blit(trash_img, rect)

                self.draw_text(str(int(self.player_total_points)), self.screen_width - 200, self.screen_height // 10, self.BLACK)
                self.draw_text("POINTS:", self.screen_width // 10, self.screen_height // 10, self.BLACK)

                if self.new_points_calc == self.starting_points:
                    color = self.GOLD
                elif self.new_points_calc > self.starting_points * 0.6:
                    color = self.PURPLE
                elif self.new_points_calc > self.starting_points * 0.12:
                    color = self.BLUE
                elif self.new_points_calc > self.starting_points * 0.01:
                    color = self.GREEN
                else:
                    color = self.GREY2
                self.draw_text(str(int(self.new_points_calc)), self.screen_width // 3, self.screen_height // 10, color)

                guess_color = self.RED if self.selected_suit_index < 2 else self.BLACK
                self.draw_text("GUESS:", self.screen_width // 10, self.screen_height - 100, self.BLACK)
                self.draw_text(f'{self.ranks[self.selected_rank_index]} of {self.suits[self.selected_suit_index]}',
                               self.screen_width // 3, self.screen_height - 100, guess_color)

                if self.drawn_card and self.gamestate:
                    name = f"{self.drawn_card['suit']}_{self.drawn_card['rank']}"
                    if name in self.card_images:
                        card_img = self.card_images[name]
                        rect = card_img.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                        self.screen.blit(card_img, rect)

                if self.drawn_card:
                    if self.suits[self.selected_suit_index] == self.drawn_card["suit"] and not self.points_added:
                        self.player_total_points += 100
                        self.points_added = True
                    if self.ranks[self.selected_rank_index] == self.drawn_card["rank"] and not self.points_added:
                        self.player_total_points += 500
                        self.points_added = True
                    if self.is_guess_correct:
                        win_img = self.other_images.get("win_outline")
                        if win_img:
                            rect = win_img.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                            self.screen.blit(win_img, rect)
                    self.draw_text("Correct!" if self.is_guess_correct else '', self.screen_width // 5, self.screen_height - 50, self.BLACK)

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = GameWindow()
    asyncio.run(game.main())
