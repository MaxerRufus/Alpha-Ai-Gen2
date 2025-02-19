import pygame
import random
import os

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Set up the game window
WIDTH = 400
HEIGHT = 600
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 255)  # Changed to blue for sky color
GREEN = (0, 255, 0)

# Game variables
GRAVITY = 0.25
BIRD_JUMP = -5
GAME_SPEED = 5
PIPE_WIDTH = 50
PIPE_GAP = 150

# Load images
BIRD_IMG = pygame.image.load("placeholder_bird.png")  # Replace with actual image path
PIPE_IMG = pygame.image.load("placeholder_pipe.png")  # Replace with actual image path
BG_IMG = pygame.image.load("placeholder_bg.png")  # Replace with actual image path

# Scale images
BIRD_IMG = pygame.transform.scale(BIRD_IMG, (40, 30))
PIPE_IMG = pygame.transform.scale(PIPE_IMG, (PIPE_WIDTH, HEIGHT))
BG_IMG = pygame.transform.scale(BG_IMG, (WIDTH, HEIGHT))

# Load sounds
JUMP_SOUND = pygame.mixer.Sound("sfx_wing.mp3")  # Replace with actual sound path
SCORE_SOUND = pygame.mixer.Sound("sfx_point.mp3")  # Replace with actual sound path
DIE_SOUND = pygame.mixer.Sound("sfx_die.mp3")  # Replace with actual sound path

class Bird:
    def __init__(self):
        self.x = 50
        self.y = HEIGHT // 2
        self.velocity = 0
        self.image = BIRD_IMG

    def jump(self):
        self.velocity = BIRD_JUMP
        JUMP_SOUND.play()

    def move(self):
        self.velocity += GRAVITY
        self.y += self.velocity

    def draw(self):
        WINDOW.blit(self.image, (int(self.x), int(self.y)))

class Pipe:
    def __init__(self):
        self.x = WIDTH
        self.height = random.randint(100, HEIGHT - PIPE_GAP - 100)
        self.image = PIPE_IMG

    def move(self):
        self.x -= GAME_SPEED

    def draw(self):
        WINDOW.blit(self.image, (self.x, self.height - HEIGHT))
        WINDOW.blit(pygame.transform.flip(self.image, False, True), (self.x, self.height + PIPE_GAP))

def load_high_score():
    if os.path.exists("high_score.txt"):
        with open("high_score.txt", "r") as file:
            return int(file.read())
    return 0

def save_high_score(score):
    with open("high_score.txt", "w") as file:
        file.write(str(score))

def main():
    clock = pygame.time.Clock()
    bird = Bird()
    pipes = []
    score = 0
    high_score = load_high_score()
    font = pygame.font.Font(None, 36)
    game_over = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_over:
                        # Restart the game
                        bird = Bird()
                        pipes = []
                        score = 0
                        game_over = False
                    else:
                        bird.jump()

        if not game_over:
            bird.move()

            if len(pipes) == 0 or pipes[-1].x < WIDTH - 200:
                pipes.append(Pipe())

            for pipe in pipes:
                pipe.move()
                if pipe.x + PIPE_WIDTH < 0:
                    pipes.remove(pipe)
                    score += 1
                    SCORE_SOUND.play()

                if (pipe.x < bird.x < pipe.x + PIPE_WIDTH and
                    (bird.y < pipe.height or bird.y > pipe.height + PIPE_GAP)):
                    DIE_SOUND.play()
                    game_over = True

            if bird.y > HEIGHT or bird.y < 0:
                DIE_SOUND.play()
                game_over = True

        # Draw background
        WINDOW.blit(BG_IMG, (0, 0))

        for pipe in pipes:
            pipe.draw()
        bird.draw()

        # Draw score
        score_text = font.render(f"Score: {score}", True, WHITE)
        WINDOW.blit(score_text, (10, 10))

        # Draw high score
        high_score_text = font.render(f"High Score: {high_score}", True, WHITE)
        WINDOW.blit(high_score_text, (10, 50))

        if game_over:
            if score > high_score:
                high_score = score
                save_high_score(high_score)

            game_over_text = font.render("Game Over!", True, WHITE)
            WINDOW.blit(game_over_text, (WIDTH // 2 - 180, HEIGHT // 2))

        pygame.display.update()
        clock.tick(60)

if __name__ == "__main__":
    main()
   