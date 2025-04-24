import pygame
import random
import json
import os
import subprocess
import sys

class CEOSimulator:
    def __init__(self):
        pygame.init()

        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("CEO Simulator")

        self.WHITE = (255, 255, 255)
        self.GREY = (178, 190, 181)
        self.BLACK = (0, 0, 0)
        self.RED = (210, 43, 43)
        self.GREEN = (50, 160, 50)
        self.BLUE = (76, 81, 247)
        self.GOLD = (200, 180, 50)

        self.font = pygame.font.SysFont(None, 40)
        self.small_font = pygame.font.SysFont(None, 30)
        self.smaller_font = pygame.font.SysFont(None, 25)

        self.money_high = 1000
        self.reputation_high = 1000
        self.morale_high = 1000

        self.reset()

    def startup_screen(self):
        selecting = True
        while selecting:
            self.screen.fill(self.GREY)
            self.draw_text("Choose Your CEO Type", 200, 100, self.font, self.BLACK)

            types = ["Capitalist", "Narcissist", "Socialist", "Idealist"]
            buttons = []

            mouse_pos = pygame.mouse.get_pos()

            for i, ceo_type in enumerate(types):
                rect = pygame.Rect(250, 180 + i * 80, 300, 50)

                is_hovered = rect.collidepoint(mouse_pos)
                button_color = (140, 140, 255) if is_hovered else self.BLUE

                pygame.draw.rect(self.screen, button_color, rect)
                pygame.draw.rect(self.screen, self.BLACK, rect, 2)  # Optional border
                self.draw_text(ceo_type, rect.x + 20, rect.y + 10, self.small_font, self.WHITE)
                buttons.append((rect, ceo_type))

            if any(rect.collidepoint(mouse_pos) for rect, _ in buttons):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for rect, ceo_type in buttons:
                        if rect.collidepoint(event.pos):
                            self.reset()
                            self.game_type(ceo_type)
                            selecting = False

            pygame.display.flip()

    def load_scenarios(self):
        with open(os.path.join("jsons", "ceo_scenarios.json"), "r") as file:
            self.scenarios = json.load(file)

    def reset(self):
        self.scenarios_played = 0
        self.click = True
        self.type = ""
        self.penalty_message = ""
        self.load_scenarios()
        self.money = 50
        self.reputation = 50
        self.morale = 50
        self.feedback = ""
        self.feedback_timer = 0
        self.option_rects = []
        self.scenarios_seen = set()
        self.next_scenario()

    def draw_stat_bar(self, x, y, value, max_value, label, color):
        bar_width = 200
        bar_height = 20
        fill_width = int((value / max_value) * bar_width)
        
        # Draw border
        pygame.draw.rect(self.screen, self.BLACK, (x, y, bar_width, bar_height), 2)
        
        # Draw filled portion
        pygame.draw.rect(self.screen, color, (x, y, fill_width, bar_height))
        
        # Label
        self.draw_text(f"{label}", x + bar_width + 10, y + 2, self.smaller_font, self.BLACK)

    def next_scenario(self):
        self.scenarios_played += 1
        if len(self.scenarios_seen) == len(self.scenarios):
            self.scenarios_seen.clear()  # Reset when all have been shown

        available_indexes = [i for i in range(len(self.scenarios)) if i not in self.scenarios_seen]
        chosen_index = random.choice(available_indexes)

        self.scenarios_seen.add(chosen_index)
        self.current = self.scenarios[chosen_index]

        self.feedback = ""
        self.penalty_message = ""
        self.feedback_timer = 0
        self.option_rects = []
        self.click = True

    def draw_text(self, text, x, y, font, color):
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            if font.size(current_line + word)[0] <= self.screen_width - 100:
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)

        line_height = font.get_height() + 5
        for i, line in enumerate(lines):
            text_surface = font.render(line, True, color)
            self.screen.blit(text_surface, (x, y + i * line_height))

    def load_bg(self):
        try:
            # Load and scale monitor image once
            monitor = pygame.image.load(os.path.join("images", "ceo", "monitor_desk.png"))
            monitor = pygame.transform.scale(monitor, (self.screen_width, self.screen_height))

            # Dictionary mapping CEO types to their background and ornament images
            ceo_assets = {
                "Capitalist": ("bg_cap_2.png", "ornaments_capitalist.png"),
                "Narcissist": ("bg_nar.jpg", "ornaments_narcissist.png"),
                "Socialist": ("bg_soc.jpg", "ornaments_socialist.png"),
                "Idealist": ("bg_ideal.jpg", "ornaments_idealist.png"),
            }

            if self.type in ceo_assets:
                bg_file, ornament_file = ceo_assets[self.type]
                bg = pygame.image.load(os.path.join("images", "ceo", bg_file))
                bg = pygame.transform.scale(bg, (self.screen_width, self.screen_height))
                self.screen.blit(bg, (0, 0))

                ornament = pygame.image.load(os.path.join("images", "ceo", ornament_file))
                ornament = pygame.transform.scale(ornament, (self.screen_width, self.screen_height))

                pygame.draw.rect(self.screen, self.GREY, (28, 38, 743, 400))
                self.screen.blit(monitor, (0, 0))
                self.screen.blit(ornament, (0, 0))
        except Exception as e:
            print(f"Error loading background: {e}")

    def apply_effects(self, effects):
        self.money += effects.get("money", 0)
        self.reputation += effects.get("reputation", 0)
        self.morale += effects.get("morale", 0)

        # Set limits
        if self.type == "Capitalist":
            if self.reputation > self.reputation_high and self.morale > self.morale_high:
                self.money -= 10
                self.penalty_message = "The goal is money (-10 Money)"
            elif self.reputation > self.reputation_high:
                self.money -= 5
                self.penalty_message = "Too much rep, not enough money (-5 Money)"
            elif self.morale > self.morale_high:
                self.money -= 5
                self.penalty_message = "Employee are not your priority(-5 Money)"
        if self.type == "Narcissist":
            if self.money > self.money_high and self.morale > self.morale_high:
                self.reputation -= 10
                self.penalty_message = "Think more about yourself (-10 Reputation)"
            elif self.money > self.money_high:
                self.reputation -= 5
                self.penalty_message = "You are punished for your greed (-5 Reputation)"    
            elif self.morale > self.morale_high:
                self.reputation -= 5
                self.penalty_message = "Employees have it too good (-5 Reputation)"
        if self.type == "Socialist":
            if self.money > self.money_high and self.reputation > self.reputation_high:
                self.morale -= 10
                self.penalty_message = "Employees are your top priority (-10 Morale)"
            elif self.money > self.money_high:
                self.morale -= 5
                self.penalty_message = "Greed is the enemy (-5 Morale)"
            elif self.reputation > self.reputation_high:
                self.morale -= 5
                self.penalty_message = "Unnecessary rep holds you back (-5 Morale)"
        if self.type == "Idealist":
            if not (abs(self.money - self.reputation) <= 20 and 
                    abs(self.reputation - self.morale) <= 20 and 
                    abs(self.money - self.morale) <= 20):
                self.money -= 5
                self.reputation -= 5
                self.morale -= 5
                self.penalty_message = "All should be equal (-5 all)"

        # Clamp values
        self.money = max(0, self.money)
        self.reputation = max(0, self.reputation)
        self.morale = max(0, self.morale)

    def check_click(self, pos):
        for rect, choice in self.option_rects:
            if rect.collidepoint(pos):
                self.apply_effects(choice["effects"])
                self.feedback = choice["feedback"]
                self.feedback_timer = pygame.time.get_ticks()
                return

    def draw_stats(self):
        # Determine colors
        color_money = self.RED if self.money >= self.money_high else self.GREEN
        color_reputation = self.RED if self.reputation >= self.reputation_high else self.GREEN
        color_morale = self.RED if self.morale >= self.morale_high else self.GREEN
        if self.type == "Idealist":
            if not (abs(self.money - self.reputation) <= 20 and 
                    abs(self.reputation - self.morale) <= 20 and 
                    abs(self.money - self.morale) <= 20):
                color_money = self.RED
                color_reputation = self.RED
                color_morale = self.RED

        # Draw stat bars
        self.draw_stat_bar(50, 45, self.money, 150, "Money", color_money)
        self.draw_stat_bar(50, 70, self.reputation, 150, "Reputation", color_reputation)
        self.draw_stat_bar(50, 95, self.morale, 150, "Morale", color_morale)

    def check_game_over(self):
        if self.money <= 0 or self.reputation <= 0 or self.morale <= 0:
            self.game_over("You have lost the game!")
        elif (self.type == "Capitalist" and self.money >= 150)\
        or (self.type == "Narcissist" and self.reputation >= 150)\
        or (self.type == "Socialist" and self.morale >= 150)\
        or (self.type == "Idealist" and self.money >= 150 and self.reputation >= 150 and self.morale >= 150):
            self.game_over("Congratulations, you've won!")

    def game_over(self, message):
        win = "Congratulations" in message
        self.show_summary(win)

    def game_type(self, type):
        self.type = type
        if self.type == "Capitalist":
            self.money_high = 1000
            self.reputation_high = 70
            self.morale_high = 55
        elif self.type == "Narcissist":
            self.money_high = 60
            self.reputation_high = 1000
            self.morale_high = 60
        elif self.type == "Socialist":
            self.money_high = 55
            self.reputation_high = 70
            self.morale_high = 1000
        elif self.type == "Idealist":
            self.money_high = 150
            self.reputation_high = 150
            self.morale_high = 150
            return

    def show_summary(self, win):
        self.screen.fill(self.GREY)
        self.load_bg()

        title = "You Win!" if win else "Game Over"
        color = self.GREEN if win else self.RED

        self.draw_text(title, 250, 100, self.font, color)
        self.draw_text(f"CEO Type: {self.type}", 250, 180, self.small_font, self.BLACK)
        self.draw_text(f"Scenarios Played: {self.scenarios_played}", 250, 220, self.small_font, self.BLACK)
        self.draw_text(f"Final Money: {self.money}", 250, 260, self.small_font, self.BLACK)
        self.draw_text(f"Final Reputation: {self.reputation}", 250, 300, self.small_font, self.BLACK)
        self.draw_text(f"Final Morale: {self.morale}", 250, 340, self.small_font, self.BLACK)

        self.draw_text("Press R to Restart or ESC to Quit", 180, 400, self.small_font, self.BLACK)
        pygame.display.flip()

        # Wait for input
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset()
                        self.startup_screen()
                        waiting = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        exit()

    def launch_launcher(self):
        pygame.quit()
        subprocess.run([sys.executable, "_launcher.py"])

    def main(self):
        self.startup_screen()
        clock = pygame.time.Clock()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.check_click(event.pos)
                elif event.type ==pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.launch_launcher()
                    elif event.key == pygame.K_r:
                        self.reset()
                        self.startup_screen()   

            self.screen.fill(self.GREY)
            self.load_bg()
            self.draw_stats()

            self.draw_text(self.current["scenario"], 50, 130, self.font, self.BLACK)

            self.option_rects = []
            mouse_pos = pygame.mouse.get_pos()  # Get mouse position

            for i, choice in enumerate(self.current["choices"]):
                rect = pygame.Rect(70, 210 + i * 70, 660, 50)
                
                # Hover color logic
                is_hovered = rect.collidepoint(mouse_pos)
                button_color = (140, 140, 255) if is_hovered else self.BLUE

                pygame.draw.rect(self.screen, button_color, rect)
                pygame.draw.rect(self.screen, self.BLACK, rect, 2)  # Optional border
                self.draw_text(choice["text"], rect.x + 10, rect.y + 10, self.small_font, self.WHITE)

                if self.click:
                    self.option_rects.append((rect, choice))

            if any(rect.collidepoint(mouse_pos) for rect, _ in self.option_rects):
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            if self.feedback:
                self.click = False
                feedback_color = self.GREEN
                pygame.draw.rect(self.screen, self.GREY, (70, 210, 660, 200))
                self.draw_text(self.feedback, 70, 260, self.font, feedback_color)
                self.draw_text(self.penalty_message, 70, 310, self.font, self.RED)
                if pygame.time.get_ticks() - self.feedback_timer > 2000:
                    self.next_scenario()

            self.draw_text(self.type, self.screen_width - 200, 70, self.small_font, self.BLACK) 

            self.check_game_over()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = CEOSimulator()
    game.main()