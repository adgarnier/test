import pygame
import random
import json
import os
import asyncio

class GameWindow:
    def __init__(self):
        random.seed()
        # pygame setup
        pygame.init()

        # Set up the game window dimensions
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

        # Set the title of the window
        pygame.display.set_caption("Match the Meaning")

        # Define colors
        self.WHITE = (255, 255, 255)
        self.GREY = (178, 190, 181)
        self.BLACK = (0, 0, 0)
        self.RED = (210, 43, 43)
        self.GREEN = (49, 146, 54)
        self.BLUE = (76, 81, 247)
        self.PURPLE = (157, 77, 187)
        self.GOLD = (243, 175, 25)
        self.GREY2 = (100, 100, 100)
        self.GREY3 = (200, 200, 200)

        # Initialize font
        self.font = pygame.font.SysFont(None, 50)
        self.small_font = pygame.font.SysFont(None, 40)

        # Load dictionary
        self.load_dictionary()
        self.option_rects = [] 
        self.player_total_points = 0

        # Reset game state
        self.next_round()

    def load_dictionary(self):
        # Load the dictionary from the file
        with open(os.path.join("jsons", "dictionary.json"), "r") as file:
            self.dictionary = json.load(file)

    def reset_game(self):
        # Reset the game state
        self.player_total_points = 0
        self.next_round()

    def next_round(self):
        # Keep picking a word until we find one with meanings
        while True:
            self.word = random.choice(list(self.dictionary.keys()))  # Random word from the dictionary
            if self.dictionary[self.word]["MEANINGS"] and len(self.word) < 16:  # Check if there are meanings available
                break

        self.length = len(self.dictionary[self.word])
        self.type = self.dictionary[self.word]["MEANINGS"][0][0]  # Get the first meaning only
        self.definition = self.dictionary[self.word]["MEANINGS"][0][1]  # Get the first meaning only
        self.synonyms = self.dictionary[self.word]["SYNONYMS"][:]
        word = str(self.word).capitalize()
        self.synonyms = str(self.synonyms).replace("[", "").replace("]", "").replace("\'", "").replace(word, "")
        self.game_over = False
        self.feedback = ""
        self.feedback_timer = 0

        # Generate options
        self.options = [self.word]
        while len(self.options) < 6:
            random_word = random.choice(list(self.dictionary.keys()))
            if random_word not in self.options and len(random_word) < 16:
                self.options.append(random_word)
        random.shuffle(self.options)

        # Create a dictionary to store whether each option was selected correctly
        self.selected_status = {option: None for option in self.options}

    def draw_text(self, text, x, y, font, color):
        # Break the text into lines if it exceeds the screen width
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            # If the word doesn't fit on the current line, move it to the next line
            if font.size(current_line + word)[0] <= self.screen_width - 140:  # 40px padding from the edge
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = word + " "
        
        lines.append(current_line)  # Add the last line

        # Draw each line of text
        line_height = font.get_height() + 5  # Add some space between lines
        for i, line in enumerate(lines):
            text_surface = font.render(line, True, color)
            self.screen.blit(text_surface, (x, y + i * line_height))

    def check_click(self, pos):
        for i, (rect, option) in enumerate(self.option_rects):
            if rect.collidepoint(pos):
                if self.selected_status[option] is None:  # Only proceed if the option hasn't been selected yet
                    if option == self.word:
                        self.selected_status[option] = "correct"
                        self.player_total_points += 1
                        self.feedback = f"Correct! {self.word}"
                    else:
                        self.selected_status[option] = "incorrect"
                        self.feedback = f"Wrong! {self.word}"
                    self.feedback_timer = pygame.time.get_ticks()

    async def main(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pass
                    elif event.key == pygame.K_r:
                        self.feedback = f"The word was: {self.word}"
                        self.next_round()
                        self.feedback = ""
                    elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]:
                        index = event.key - pygame.K_1
                        if index < len(self.options):
                            selected_option = self.options[index]
                            if self.selected_status[selected_option] is None:  # Only proceed if not already selected
                                if selected_option == self.word:
                                    self.selected_status[selected_option] = "correct"
                                    self.player_total_points += 1
                                    self.feedback = f"Correct! {self.word}"
                                    print(self.player_total_points)
                                else:
                                    self.selected_status[selected_option] = "incorrect"
                                    self.feedback = f"Wrong! {self.word}"
                                self.feedback_timer = pygame.time.get_ticks()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.check_click(event.pos)

            self.screen.fill(self.GREY)

            if not self.game_over:
                
                square = pygame.Rect(70, 100, 680, 230)
                pygame.draw.rect(self.screen, self.GREY3, square)
                self.draw_text(f"{self.definition}", 80, 110, self.font, self.BLACK)

                self.option_rects = [] 
                f = 0
                for i, option in enumerate(self.options):
                    if i < 3:
                        square = pygame.Rect(70, 392 + i * 60, 330, 40)
                    else:
                        square = pygame.Rect(420, 392 + f * 60, 330, 40)
                        f += 1

                    # Color the option based on whether it was selected correctly
                    if self.selected_status[option] == "correct":
                        color = self.GREEN
                    elif self.selected_status[option] == "incorrect":
                        color = self.RED
                    else:
                        color = self.GREY3

                    pygame.draw.rect(self.screen, color, square)
                    self.draw_text(f"{i+1}. {option}", square.x + 10, square.y + 5, self.small_font, self.BLACK)
                    self.option_rects.append((square, option))

                total_points = str(self.player_total_points)
                self.draw_text(total_points, self.screen_width - 200, self.screen_height // 10, self.font, self.BLACK)

                if self.feedback:
                    self.draw_text(self.feedback, self.screen_width // 10, 340, self.font, self.GREEN if "Correct" in self.feedback else self.RED)
                    if pygame.time.get_ticks() - self.feedback_timer > 2000:
                        self.next_round()
                        self.feedback = ""
            else:
                self.draw_text(f"Final Score: {self.player_total_points}", self.screen_width // 4, self.screen_height // 2, self.font, self.RED)

            pygame.display.flip()
            clock.tick(60)
            await asyncio.sleep(0)

        pygame.quit()

if __name__ == "__main__":
    game = GameWindow()
    asyncio.run(game.main())