import pygame
import math
import time
import random
import asyncio

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (76, 81, 247)
PURPLE = (157, 77, 187)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
GOLD = (243, 175, 25)
G = 6.67430e-11
BASE_GRAVITY_MULTIPLIER = 80
BASE_COLLISION_PENALTY = 10
BASE_ORBIT_LIMIT = 1000

font = pygame.font.SysFont(None, 24)

class CelestialBody:
    def __init__(self, x, y, mass, radius, color, vx=0, vy=0):
        self.x = x
        self.y = y
        self.mass = mass
        self.radius = radius
        self.color = color
        self.vx = vx
        self.vy = vy
        self.trail = []

    def draw(self, screen):
        if len(self.trail) > 2:
            pygame.draw.lines(screen, self.color, False, self.trail, 1)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def update_position(self, bodies, star, gravity_multiplier):
        ax, ay = 0, 0
        for body in bodies:
            if body != self:
                dx = body.x - self.x
                dy = body.y - self.y
                distance = math.hypot(dx, dy)
                if distance < 1e-2:
                    continue
                adjusted_G = G * (gravity_multiplier if (body != star and self != star) else 1)
                force = adjusted_G * self.mass * body.mass / (distance ** 2)
                ax += force * dx / distance / self.mass
                ay += force * dy / distance / self.mass
        self.vx += ax
        self.vy += ay
        self.x += self.vx
        self.y += self.vy
        if len(self.trail) > 100:
            self.trail.pop(0)
        self.trail.append((int(self.x), int(self.y)))

class FloatingText:
    def __init__(self, text, x, y, color, duration=1.5):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.duration = duration
        self.start_time = time.time()

    def draw(self, screen):
        elapsed = time.time() - self.start_time
        if elapsed > self.duration:
            return False
        offset = int(elapsed * 30)
        alpha = max(0, 255 - int(elapsed / self.duration * 255))
        surf = font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        screen.blit(surf, (self.x, self.y - offset))
        return True

class Level:
    def __init__(self, number, target_planets, survive_time):
        self.number = number
        self.target_planets = target_planets
        self.survive_time = survive_time
        self.completed = False

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.radius = random.randint(2, 4)
        self.color = color
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.lifetime = 3.0
        self.birth_time = time.time()

    def update(self):
        self.x += self.vx
        self.y += self.vy
        return time.time() - self.birth_time < self.lifetime

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class GameWindow:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("S p a c e")
        self.clock = pygame.time.Clock()
        self.reset()
        self.levels = [
            Level(1, 1, 5), Level(2, 2, 5), Level(3, 3, 5),
            Level(4, 5, 10), Level(5, 7, 10), Level(6, 9, 10),
            Level(7, 12, 15), Level(8, 15, 15), Level(9, 18, 15),
            Level(10, 20, 30)
        ]

    def reset(self):
        self.bodies = []
        self.floating_texts = []
        self.particles = []
        self.score = 0
        self.last_bonus_time = time.time()
        self.last_rogue_spawn = time.time()
        self.game_start_time = time.time()
        self.level_start_time = time.time()
        self.key_mass = 1e10
        self.key_radius = 5
        self.key_color = BLUE
        self.star = CelestialBody(WIDTH / 2, HEIGHT / 2, 1e14, 10, YELLOW)
        self.bodies.append(self.star)
        self.current_level = 0

    def spawn_rogue_body(self):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.randint(400, 600)
        x = self.star.x + math.cos(angle) * distance
        y = self.star.y + math.sin(angle) * distance
        speed = random.uniform(1, 2)
        vx = -math.sin(angle) * speed
        vy = math.cos(angle) * speed
        mass = random.uniform(1e5, 1e8)
        radius = random.randint(5, 8)
        color = random.choice([RED, GREEN, GOLD, PURPLE])
        return CelestialBody(x, y, mass, radius, color, vx, vy)

    def spawn_collision_particles(self, x, y, color, count=15):
        return [Particle(x, y, color) for _ in range(count)]

    def check_collisions(self, collision_penalty):
        i = 1
        while i < len(self.bodies):
            j = i + 1
            while j < len(self.bodies):
                a, b = self.bodies[i], self.bodies[j]
                dist = math.hypot(a.x - b.x, a.y - b.y)
                if dist < (a.radius + b.radius):
                    x, y = int((a.x + b.x) / 2), int((a.y + b.y) / 2)
                    self.floating_texts.append(FloatingText(f"Planets collide!", x, y, RED))
                    self.particles.extend(self.spawn_collision_particles(x, y, (255, 100, 100)))
                    self.bodies.pop(j)
                    self.bodies.pop(i)
                    return True
                j += 1
            i += 1
        return False

    def draw_level_goal(self, level, elapsed):
        lines = [
            f"Goals",
            f"Planets: {len(self.bodies) - 1}/{level.target_planets}",
            f"Level Time: {elapsed}/{level.survive_time}"
        ]
        for i, line in enumerate(lines):
            self.screen.blit(font.render(line, True, WHITE), (20, 520 + i * 20))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.launch_launcher()
                elif event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_1:
                    self.key_mass = 1e-50
                    self.key_color = BLUE
                    self.key_radius = 5
                elif event.key == pygame.K_2:
                    self.key_mass = 1e5
                    self.key_color = PURPLE
                    self.key_radius = 10
                elif event.key == pygame.K_3:
                    self.key_mass = 1e10
                    self.key_color = RED
                    self.key_radius = 15
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                dx, dy = x - self.star.x, y - self.star.y
                distance = math.hypot(dx, dy)
                if distance == 0:
                    return True
                speed = math.sqrt(G * self.star.mass / distance)
                vx, vy = -dy / distance * speed, dx / distance * speed
                new_body = CelestialBody(x, y, self.key_mass, self.key_radius, self.key_color, vx, vy)
                self.bodies.append(new_body)
                self.score += 10
                # self.floating_texts.append(FloatingText("+10", x, y, GREEN))
        return True

    # def update(self):
    #     now = time.time()
    #     elapsed = int(now - self.game_start_time)
    #     level_elapsed = int(now - self.level_start_time)
    #     difficulty = self.current_level
    #     gravity_multiplier = BASE_GRAVITY_MULTIPLIER + difficulty * 10
    #     collision_penalty = BASE_COLLISION_PENALTY + difficulty * 10

    #     self.screen.fill(BLACK)

    #     for body in self.bodies:
    #         body.update_position(self.bodies, self.star, gravity_multiplier)
    #         body.draw(self.screen)

    #     for i in range(len(self.bodies) - 1, 0, -1):
    #         body = self.bodies[i]
    #         dist = math.hypot(body.x - self.star.x, body.y - self.star.y)
    #         if dist > BASE_ORBIT_LIMIT:
    #             self.floating_texts.append(FloatingText("Planet escaped orbit!", WIDTH // 2 - 80, 560, RED))
    #             self.bodies.pop(i)
    #         elif dist < (body.radius + self.star.radius):
    #             self.score -= collision_penalty
    #             self.floating_texts.append(FloatingText(f"Planet crashed!", int(body.x), int(body.y), RED))
    #             self.bodies.pop(i)

    #     if self.check_collisions(collision_penalty):
    #         self.level_start_time = now
    #         self.floating_texts.append(FloatingText("Timer Reset!", 150, 560, RED))

    #     if now - self.last_bonus_time >= 10:
    #         self.score += 10
    #         # self.floating_texts.append(FloatingText("+10 (survive)", 10, 70, GREEN))
    #         self.last_bonus_time = now

    #     if now - self.last_rogue_spawn >= 20 - min(difficulty, 15) and self.current_level >= 3:
    #         self.bodies.append(self.spawn_rogue_body())
    #         self.last_rogue_spawn = now

    #     if self.current_level < len(self.levels):
    #         level = self.levels[self.current_level]
    #         if len(self.bodies) <= level.target_planets:
    #             self.level_start_time = now
    #         if not level.completed and len(self.bodies) - 1 >= level.target_planets and level_elapsed >= level.survive_time:
    #             level.completed = True
    #             self.floating_texts.append(FloatingText(f"Level {level.number} Complete!", WIDTH // 2 - 80, HEIGHT // 2, GREEN))
    #             self.current_level += 1
    #             self.level_start_time = now

    #     self.particles = [p for p in self.particles if p.update()]
    #     for p in self.particles:
    #         p.draw(self.screen)

    #     self.floating_texts = [t for t in self.floating_texts if t.draw(self.screen)]

    #     # self.screen.blit(font.render(f"Score: {self.score}", True, WHITE), (680, 20))
    #     # self.screen.blit(font.render(f"Time: {elapsed}s", True, WHITE), (680, 560))
    #     self.screen.blit(font.render(f"Level: {self.levels[self.current_level].number if self.current_level > 0 else 1}", True, WHITE), (20, 20))

    #     if self.current_level < len(self.levels):
    #         self.draw_level_goal(self.levels[self.current_level], level_elapsed)

    #     pygame.display.flip()
    #     self.clock.tick(60)
    #     await asyncio.sleep(0)

    async def main(self):
        running = True
        while running:
            running = self.handle_events()
            now = time.time()
            elapsed = int(now - self.game_start_time)
            level_elapsed = int(now - self.level_start_time)
            difficulty = self.current_level
            gravity_multiplier = BASE_GRAVITY_MULTIPLIER + difficulty * 10
            collision_penalty = BASE_COLLISION_PENALTY + difficulty * 10

            self.screen.fill(BLACK)

            for body in self.bodies:
                body.update_position(self.bodies, self.star, gravity_multiplier)
                body.draw(self.screen)

            for i in range(len(self.bodies) - 1, 0, -1):
                body = self.bodies[i]
                dist = math.hypot(body.x - self.star.x, body.y - self.star.y)
                if dist > BASE_ORBIT_LIMIT:
                    self.floating_texts.append(FloatingText("Planet escaped orbit!", WIDTH // 2 - 80, 560, RED))
                    self.bodies.pop(i)
                elif dist < (body.radius + self.star.radius):
                    self.score -= collision_penalty
                    self.floating_texts.append(FloatingText(f"Planet crashed!", int(body.x), int(body.y), RED))
                    self.bodies.pop(i)

            if self.check_collisions(collision_penalty):
                self.level_start_time = now
                self.floating_texts.append(FloatingText("Timer Reset!", 150, 560, RED))

            if now - self.last_bonus_time >= 10:
                self.score += 10
                # self.floating_texts.append(FloatingText("+10 (survive)", 10, 70, GREEN))
                self.last_bonus_time = now

            if now - self.last_rogue_spawn >= 20 - min(difficulty, 15) and self.current_level >= 3:
                self.bodies.append(self.spawn_rogue_body())
                self.last_rogue_spawn = now

            if self.current_level < len(self.levels):
                level = self.levels[self.current_level]
                if len(self.bodies) <= level.target_planets:
                    self.level_start_time = now
                if not level.completed and len(self.bodies) - 1 >= level.target_planets and level_elapsed >= level.survive_time:
                    level.completed = True
                    self.floating_texts.append(FloatingText(f"Level {level.number} Complete!", WIDTH // 2 - 80, HEIGHT // 2, GREEN))
                    self.current_level += 1
                    self.level_start_time = now

            self.particles = [p for p in self.particles if p.update()]
            for p in self.particles:
                p.draw(self.screen)

            self.floating_texts = [t for t in self.floating_texts if t.draw(self.screen)]

            # self.screen.blit(font.render(f"Score: {self.score}", True, WHITE), (680, 20))
            # self.screen.blit(font.render(f"Time: {elapsed}s", True, WHITE), (680, 560))
            self.screen.blit(font.render(f"Level: {self.levels[self.current_level].number if self.current_level > 0 else 1}", True, WHITE), (20, 20))

            if self.current_level < len(self.levels):
                self.draw_level_goal(self.levels[self.current_level], level_elapsed)

            pygame.display.flip()
            self.clock.tick(60)
            await asyncio.sleep(0)
            
        pygame.quit()

if __name__ == "__main__":
    game = GameWindow()
    asyncio.run(game.main())
