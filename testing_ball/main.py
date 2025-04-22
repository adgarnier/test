import pygame
import random
import time
import threading
import subprocess
import sys
import asyncio

class GameWindow():
    def __init__(self):
        # pygame setup
        pygame.init()

        # Set up the game window dimensions
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

        # Set the title of the window
        pygame.display.set_caption("Ball Mover")

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

        # Initialize font
        self.font = pygame.font.SysFont(None, 55)
        self.dt = 0

        self.reset_game()

    def reset_game(self):
        # Resets the game state
        self.player_pos = pygame.Vector2(self.screen_width / 2, self.screen_height / 2)
        self.balls_top = []
        self.balls_bottom = []
        self.balls_left = []
        self.balls_right = []
        self.bomb = []
        self.player_total_points = 0
        self.gamestate = True
        self.mode_switch = True
        self.timer = ''
        self.points = ''
        self.mode = 'easy'
        self.ball_size = 20
        self.player_ball_size = 20
        self.bomb_size = 20
        self.player_speed = 400
        self.interval = 0.02
        self.point_multiplier = 0.05
        
    def easy_mode(self):
        self.mode = 'easy'
        self.ball_size = 20
        self.player_ball_size = 20
        self.bomb_size = 20
        self.player_speed = 400
        self.interval = 0.02
        self.point_multiplier = 0.05  
        
    def hard_mode(self):
        self.mode = 'hard'
        self.ball_size = 10
        self.player_ball_size = 10
        self.bomb_size = 10
        self.player_speed = 300
        self.interval = 0.06
        self.point_multiplier = 0.5

    def countdown(self, t): 
        while t: 
            mins, secs = divmod(t, 60) 
            self.timer = '{:01d}'.format(secs) 
            time.sleep(1) 
            t -= 1
        self.timer = ''
        self.mode_switch = True    

    def bonus_points_thread(self, t):
        while t:
            mins, secs = divmod(t, 60) 
            self.points = '{:01d}'.format(secs) 
            time.sleep(1) 
            t -= 1
        self.points = ''      

    # Method to spawn a new ball at a random horizontal position at the top
    def spawn_ball_top(self):
        x_pos = random.randint(0, self.screen_width)
        y_pos = 0
        speed = random.randint(100, 300)
        self.balls_top.append({"pos": pygame.Vector2(x_pos, y_pos), "speed": speed})

    def spawn_ball_bottom(self):
        x_pos = random.randint(0, self.screen_width)
        y_pos = self.screen_height
        speed = random.randint(100, 300)
        self.balls_bottom.append({"pos": pygame.Vector2(x_pos, y_pos), "speed": speed})

    def spawn_ball_left(self):
        x_pos = 0
        y_pos = random.randint(0, self.screen_height)
        speed = random.randint(100, 300)
        self.balls_left.append({"pos": pygame.Vector2(x_pos, y_pos), "speed": speed})
        
    def spawn_ball_right(self):
        x_pos = self.screen_width
        y_pos = random.randint(0, self.screen_height)
        speed = random.randint(100, 300)
        self.balls_right.append({"pos": pygame.Vector2(x_pos, y_pos), "speed": speed})

    def spawn_bomb(self):
        self.bomb = []
        x_pos = random.randint(0, self.screen_width)
        y_pos = random.randint(0, self.screen_height)
        speed = 0
        self.bomb.append({"pos": pygame.Vector2(x_pos, y_pos), "speed": speed})

    def draw_text(self, text, x, y, color):
        text_surface = self.font.render(text, True, color)
        self.screen.blit(text_surface, (x, y))

    def launch_launcher(self):
        pygame.quit()
        subprocess.run([sys.executable, "_launcher.py"])

    # Main game loop
    async def main(self):
        running = True
        clock = pygame.time.Clock()

        while running:
            # Poll for events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.launch_launcher()
                    if event.key == pygame.K_r:
                        print('Restarting...')
                        self.reset_game()
                    if self.mode_switch == True:
                        if event.key == pygame.K_q and self.mode_switch == True and self.mode == 'easy' and self.gamestate == True:
                            self.p = 1000
                            self.player_total_points += self.p
                            self.hard_mode()
                            self.mode_switch = False
                            t = 3
                            countdown_thread = threading.Thread(target=self.countdown, args=(t,))
                            countdown_thread.start()
                            point_thread = threading.Thread(target=self.bonus_points_thread, args=(t,))
                            point_thread.start()
                        if event.key == pygame.K_e and self.mode_switch == True and self.mode == 'hard' and self.gamestate == True:
                            self.p = 50
                            self.player_total_points += 50
                            self.easy_mode()
                            self.mode_switch = False
                            t = 3
                            countdown_thread = threading.Thread(target=self.countdown, args=(t,))
                            countdown_thread.start()
                            point_thread = threading.Thread(target=self.bonus_points_thread, args=(t,))
                            point_thread.start()                            

            # Fill the screen with a color to wipe away anything from last frame
            self.screen.fill(self.GREY)

            if self.gamestate == True:
                # Draw the player circle
                pygame.draw.circle(self.screen, self.GOLD, self.player_pos, self.player_ball_size)

                # Cooldown timer for mode change
                countdown = str(self.timer)
                self.draw_text(countdown, self.screen_width // 10, self.screen_height // 10, self.BLACK)

                keys = pygame.key.get_pressed()
                if keys[pygame.K_w] or keys[pygame.K_UP]:
                    self.player_pos.y -= self.player_speed * self.dt
                if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                    self.player_pos.y += self.player_speed * self.dt
                if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                    self.player_pos.x -= self.player_speed * self.dt
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                    self.player_pos.x += self.player_speed * self.dt
                
                # Ensure the player doesn't go out of bounds
                self.player_pos.x = max(self.player_ball_size, min(self.player_pos.x, self.screen_width - self.player_ball_size))
                self.player_pos.y = max(self.player_ball_size, min(self.player_pos.y, self.screen_height - self.player_ball_size))

                # Spawn a new ball at random intervals
                if random.random() < self.interval:
                    self.spawn_ball_top()
                if random.random() < self.interval:
                    self.spawn_ball_bottom()
                if random.random() < self.interval:
                    self.spawn_ball_left()                    
                if random.random() < self.interval:
                    self.spawn_ball_right()

                # Spawn bomb
                if random.random() < self.interval * 0.05:
                    self.spawn_bomb()

                # Update and draw balls
                for ball in self.balls_top:
                    ball["pos"].y += ball["speed"] * self.dt
                    pygame.draw.circle(self.screen, self.RED, (int(ball["pos"].x), int(ball["pos"].y)), self.ball_size)
                    
                for ball in self.balls_bottom:
                    ball["pos"].y -= ball["speed"] * self.dt
                    pygame.draw.circle(self.screen, self.RED, (int(ball["pos"].x), int(ball["pos"].y)), self.ball_size)

                for ball in self.balls_left:
                    ball["pos"].x += ball["speed"] * self.dt
                    pygame.draw.circle(self.screen, self.RED, (int(ball["pos"].x), int(ball["pos"].y)), self.ball_size)  
                                        
                for ball in self.balls_right:
                    ball["pos"].x -= ball["speed"] * self.dt
                    pygame.draw.circle(self.screen, self.RED, (int(ball["pos"].x), int(ball["pos"].y)), self.ball_size)                    

                # Update and draw bomb
                for bomb in self.bomb:
                    bomb["pos"].y += bomb["speed"] * self.dt
                    pygame.draw.circle(self.screen, self.BLACK, (int(bomb["pos"].x), int(bomb["pos"].y)), self.bomb_size)                

                # Display points
                player_points_text = f'{int(self.player_total_points)}'
                self.draw_text(player_points_text, self.screen_width - 200, self.screen_height // 10, self.BLACK) 

                # Bonus points pop-up
                if self.points == '3':
                    bonus_points = '+ ' + str(self.p)
                    self.draw_text(bonus_points, self.screen_width - 200, self.screen_height // 6, self.PURPLE)

                # Remove balls that have fallen off the screen
                self.balls_top = [ball for ball in self.balls_top if ball["pos"].y < self.screen_height + self.ball_size]
                self.balls_bottom = [ball for ball in self.balls_bottom if ball["pos"].y > -self.ball_size]
                self.balls_left = [ball for ball in self.balls_left if ball["pos"].x < self.screen_width + self.ball_size]
                self.balls_right = [ball for ball in self.balls_right if ball["pos"].x > -self.ball_size]
                
                # Lose if hit by ball
                for ball in self.balls_top + self.balls_bottom + self.balls_left + self.balls_right:
                    if self.player_pos.distance_to(ball["pos"]) < self.player_ball_size + self.ball_size:
                        self.gamestate = False
                        break

                # Destory balls with bomb
                for bomb in self.bomb:
                    if self.player_pos.distance_to(bomb["pos"]) < self.player_ball_size + self.bomb_size:
                        self.p = 500
                        self.balls_top = []
                        self.balls_bottom = []
                        self.balls_left = []
                        self.balls_right = []
                        self.bomb = []
                        self.bomb = []
                        self.player_total_points += self.p
                        t=3
                        point_thread = threading.Thread(target=self.bonus_points_thread, args=(t,))
                        point_thread.start()
                        break

                # Increment score
                self.player_total_points += self.point_multiplier

            else:
                player_points_text = f'FINAL SCORE: {int(self.player_total_points)}'
                self.draw_text(player_points_text, self.screen_width // 5, self.screen_height // 2, self.BLACK)

            # Flip the display to put your work on screen
            pygame.display.flip()

            # Limits FPS to 60
            self.dt = clock.tick(60) / 1000
            await asyncio.sleep(0)

        pygame.quit()

if __name__ == "__main__":
    game = GameWindow()
    asyncio.run(game.main())
