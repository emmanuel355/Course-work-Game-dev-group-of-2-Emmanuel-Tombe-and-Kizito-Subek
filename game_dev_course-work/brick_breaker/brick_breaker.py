import pygame
import sys
import random
from math import sqrt

# Initialize Pygame
pygame.init()
pygame.font.init()
# Try to initialize the mixer for audio; continue gracefully if unavailable
try:
    pygame.mixer.init()
except Exception:
    # Audio will be disabled if mixer cannot initialize
    print('Warning: audio mixer could not be initialized; sounds will be disabled.')

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 20
BALL_SIZE = 15
BRICK_WIDTH = 70
BRICK_HEIGHT = 30
BRICK_ROWS = 5
BRICK_COLS = 10
FPS = 60

# Colors
BACKGROUND = (15, 10, 35)
PADDLE_COLOR = (106, 13, 173)  # Royal purple
BALL_COLOR = (255, 215, 0)     # Gold
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (106, 13, 173)
BUTTON_HOVER = (140, 50, 200)

# Brick colors with varying point values
BRICK_COLORS = [
    (255, 50, 50, 200),    # Red - 10 points
    (255, 140, 50, 200),   # Orange - 20 points
    (50, 200, 50, 200),    # Green - 30 points
    (255, 255, 50, 200),   # Yellow - 40 points
    (200, 200, 200, 200),  # Silver - 50 points (2 hits required)
    (255, 215, 0, 200)     # Gold - 100 points
]

# Game states
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_INSTRUCTIONS = 3
STATE_LEVEL_COMPLETE = 4
STATE_PAUSED = 5
STATE_READY = 6

class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 8
        self.color = PADDLE_COLOR
        
    def move(self, direction, screen_width):
        if direction == "left" and self.rect.left > 0:
            self.rect.x -= self.speed
        if direction == "right" and self.rect.right < screen_width:
            self.rect.x += self.speed
            
    def draw(self, screen):
        # Draw paddle with a slight 3D effect
        pygame.draw.rect(screen, self.color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (150, 80, 200), self.rect, 3, border_radius=8)

# Safe font helper: prefer bundled/default font to avoid blocking SysFont calls
def safe_font(name, size, bold=False):
    try:
        f = pygame.font.Font(None, size)
        if bold and f:
            try:
                f.set_bold(True)
            except Exception:
                pass
        return f
    except Exception:
        return None

class Ball:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BALL_SIZE, BALL_SIZE)
        self.dx = random.choice([-4, -3, 3, 4])
        self.dy = -4
        self.color = BALL_COLOR
        self.speed_increase_counter = 0
        self.max_speed = 8
        
    def move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        
    def increase_speed(self):
        if abs(self.dx) < self.max_speed and abs(self.dy) < self.max_speed:
            self.dx *= 1.1
            self.dy *= 1.1
            self.speed_increase_counter = 0
            
    def draw(self, screen):
        # Draw ball with a glowing effect
        pygame.draw.circle(screen, self.color, self.rect.center, BALL_SIZE // 2)
        pygame.draw.circle(screen, (255, 255, 200), self.rect.center, BALL_SIZE // 4)

class Brick:
    def __init__(self, x, y, color_index):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
        self.color_index = color_index
        self.color = BRICK_COLORS[color_index]
        self.points = (color_index + 1) * 10
        self.hits_required = 2 if color_index == 4 else 1  # Silver bricks require 2 hits
        self.hits = 0
        
    def draw(self, screen):
        # Draw brick with a border
        pygame.draw.rect(screen, self.color, self.rect, border_radius=4)
        pygame.draw.rect(screen, (255, 255, 255, 100), self.rect, 2, border_radius=4)
        
        # Show hit count for silver bricks
        if self.color_index == 4 and self.hits_required > 1:
            font = safe_font(None, 20)
            text = font.render(str(self.hits_required - self.hits), True, (0, 0, 0))
            screen.blit(text, (self.rect.centerx - 5, self.rect.centery - 8))

class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.is_hovered = False
        
    def draw(self, screen):
        color = BUTTON_HOVER if self.is_hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 3, border_radius=10)
        
        font = safe_font('Arial', 28, bold=True)
        text_surf = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.action:
                return self.action
        return None

class Game:
    def __init__(self):
        # Allow window to be resized / maximized by the OS
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Castle Defender - Brick Breaker")
        self.clock = pygame.time.Clock()
        
        # Game state
        self.state = STATE_MENU
        self.score = 0
        self.lives = 3
        self.level = 1
        self.total_bricks = 0
        self.bricks_broken = 0
        
        # Game objects
        self.paddle = None
        self.ball = None
        self.bricks = []
        
        # UI elements
        self.buttons = []
        self.create_menu_buttons()
        
        # Sounds
        self.sounds = {}
        self.bgm_loaded = False
        self.load_sounds()
        
        # Initialize game
        self.reset_game()
        
    def create_menu_buttons(self):
        center_x = SCREEN_WIDTH // 2
        button_width = 200
        button_height = 50
        self.buttons = [
            Button(center_x - button_width//2, 250, button_width, button_height, "Start Game", "start"),
            Button(center_x - button_width//2, 320, button_width, button_height, "Instructions", "instructions"),
            Button(center_x - button_width//2, 390, button_width, button_height, "Quit", "quit")
        ]
        
    def create_game_over_buttons(self):
        center_x = SCREEN_WIDTH // 2
        button_width = 200
        button_height = 50
        self.buttons = [
            Button(center_x - button_width//2, 250, button_width, button_height, "Restart", "restart"),
            Button(center_x - button_width//2, 320, button_width, button_height, "Menu", "menu"),
            Button(center_x - button_width//2, 390, button_width, button_height, "Quit", "quit")
        ]
    def reset_game(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.bricks_broken = 0
        self.reset_level()
        
    def reset_level(self):
        # Create paddle and ball
        paddle_x = SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2
        paddle_y = SCREEN_HEIGHT - 50
        self.paddle = Paddle(paddle_x, paddle_y)
        
        ball_x = SCREEN_WIDTH // 2 - BALL_SIZE // 2
        ball_y = paddle_y - BALL_SIZE - 10
        self.ball = Ball(ball_x, ball_y)
        
        # Create bricks based on level
        self.create_bricks()

    def load_sounds(self):
        """Load optional sound files from assets/sounds/. Files are optional; missing files are ignored."""
        sound_dir = 'assets/sounds'
        files = {
            'brick': 'brick_hit.wav',
            'paddle': 'paddle_hit.wav',
            'life': 'life_lost.wav',
            'level': 'level_complete.wav',
            'menu': 'menu_select.wav',
            'bgm': 'bgm.mp3'
        }
        for key, fname in files.items():
            path = f"{sound_dir}/{fname}"
            try:
                if key == 'bgm':
                    # Background music handled separately. Try mp3 first, then fallback to wav.
                    if pygame.mixer.get_init():
                        import os
                        if os.path.exists(path):
                            pygame.mixer.music.load(path)
                            pygame.mixer.music.set_volume(0.2)
                        else:
                            # try .wav fallback
                            wavpath = path.rsplit('.', 1)[0] + '.wav'
                            if os.path.exists(wavpath):
                                pygame.mixer.music.load(wavpath)
                                pygame.mixer.music.set_volume(0.2)
                else:
                    if pygame.mixer.get_init() and __import__('os').path.exists(path):
                        self.sounds[key] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Warning: failed to load sound {path}: {e}")

    def play_sound(self, key):
        try:
            if key == 'bgm':
                if pygame.mixer.get_init() and self.bgm_loaded and not pygame.mixer.music.get_busy():
                    try:
                        pygame.mixer.music.play(-1)
                    except Exception as e:
                        print(f"Warning: failed to play bgm: {e}")
            else:
                snd = self.sounds.get(key)
                if snd:
                    snd.play()
        except Exception:
            pass
        
    def create_bricks(self):
        self.bricks = []
        brick_start_y = 80
        brick_gap = 5
        
        # Different layouts for different levels
        if self.level == 1:
            # Level 1: Basic layout
            rows = 4
            color_range = 4  # Only basic colors
        elif self.level == 2:
            # Level 2: More complex
            rows = 5
            color_range = 5  # Include silver bricks
        else:
            # Level 3: Most complex
            rows = 6
            color_range = 6  # Include gold bricks
            
        for row in range(rows):
            for col in range(BRICK_COLS):
                brick_x = col * (BRICK_WIDTH + brick_gap) + brick_gap
                brick_y = row * (BRICK_HEIGHT + brick_gap) + brick_start_y
                
                # Assign colors based on row (basic) or random (advanced levels)
                if self.level == 1:
                    color_index = row % 4
                else:
                    color_index = random.randint(0, color_range - 1)
                    
                brick = Brick(brick_x, brick_y, color_index)
                self.bricks.append(brick)
                
        self.total_bricks = len(self.bricks)
        self.bricks_broken = 0
        
    def handle_collisions(self):
        # Ball with walls
        if self.ball.rect.left <= 0 or self.ball.rect.right >= SCREEN_WIDTH:
            self.ball.dx *= -1
            # Keep ball in bounds
            if self.ball.rect.left <= 0:
                self.ball.rect.left = 1
            if self.ball.rect.right >= SCREEN_WIDTH:
                self.ball.rect.right = SCREEN_WIDTH - 1
                
        if self.ball.rect.top <= 0:
            self.ball.dy *= -1
            self.ball.rect.top = 1
            
        # Ball with paddle
        if self.ball.rect.colliderect(self.paddle.rect) and self.ball.dy > 0:
            # Calculate hit position (from -1 to 1)
            hit_pos = (self.ball.rect.centerx - self.paddle.rect.centerx) / (PADDLE_WIDTH / 2)
            
            # Adjust angle based on hit position
            self.ball.dx = hit_pos * 6
            self.ball.dy *= -1
            
            # Increase speed every 5 paddle hits
            self.ball.speed_increase_counter += 1
            if self.ball.speed_increase_counter >= 5:
                self.ball.increase_speed()
            
            # Move ball above paddle
            self.ball.rect.bottom = self.paddle.rect.top - 1
            # Play paddle sound
            self.play_sound('paddle')
            
        # Ball with bricks
        for brick in self.bricks[:]:
            if self.ball.rect.colliderect(brick.rect):
                # Calculate collision side
                dx1 = abs(self.ball.rect.right - brick.rect.left)
                dx2 = abs(self.ball.rect.left - brick.rect.right)
                dy1 = abs(self.ball.rect.bottom - brick.rect.top)
                dy2 = abs(self.ball.rect.top - brick.rect.bottom)
                
                min_overlap = min(dx1, dx2, dy1, dy2)
                
                if min_overlap == dx1 or min_overlap == dx2:
                    self.ball.dx *= -1
                else:
                    self.ball.dy *= -1
                
                # Handle brick hit
                brick.hits += 1
                if brick.hits >= brick.hits_required:
                    self.score += brick.points
                    self.bricks_broken += 1
                    self.bricks.remove(brick)
                    # Play brick hit sound
                    self.play_sound('brick')
                    
                    # Check if level is complete
                    if len(self.bricks) == 0:
                        self.level_complete()
                break
        
        # Ball falling below paddle
        if self.ball.rect.top > SCREEN_HEIGHT:
            self.lives -= 1
            if self.lives <= 0:
                self.state = STATE_GAME_OVER
                self.create_game_over_buttons()
            else:
                # Reset ball position
                self.ball.rect.centerx = self.paddle.rect.centerx
                self.ball.rect.bottom = self.paddle.rect.top - 10
                self.ball.dx = random.choice([-4, -3, 3, 4])
                self.ball.dy = -4
                self.ball.speed_increase_counter = 0
                # Play life lost sound
                self.play_sound('life')
                
    def level_complete(self):
        # Add bonus points for completing level
        self.score += 100
        # Play level complete sound (if available)
        self.play_sound('level')
        self.state = STATE_LEVEL_COMPLETE
        
    def next_level(self):
        self.level += 1
        if self.level > 3:
            # Game won
            self.state = STATE_GAME_OVER
            self.create_game_over_buttons()
        else:
            self.reset_level()
            self.state = STATE_PLAYING
            
    def draw_hud(self):
        font = safe_font('Arial', 24, bold=True)
        
        # Score
        score_text = font.render(f"Score: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_text, (10, 10))
        
        # Lives
        lives_text = font.render(f"Lives: {self.lives}", True, TEXT_COLOR)
        self.screen.blit(lives_text, (SCREEN_WIDTH - 100, 10))
        
        # Level
        level_text = font.render(f"Level: {self.level}/3", True, TEXT_COLOR)
        self.screen.blit(level_text, (SCREEN_WIDTH // 2 - 40, 10))
        
        # Bricks remaining
        bricks_text = font.render(f"Bricks: {self.total_bricks - self.bricks_broken}/{self.total_bricks}", True, TEXT_COLOR)
        self.screen.blit(bricks_text, (10, 40))
        
    def draw_menu(self):
        # Draw background
        self.screen.fill(BACKGROUND)
        
        # Draw title
        title_font = safe_font('Arial', 64, bold=True)
        title = title_font.render("CASTLE DEFENDER", True, (255, 215, 0))
        subtitle_font = safe_font('Arial', 32)
        subtitle = subtitle_font.render("Brick Breaker", True, (200, 200, 255))
        
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        self.screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 170))
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
            
        # Draw instructions at bottom
        instr_font = safe_font('Arial', 18)
        instr = instr_font.render("Use LEFT/RIGHT arrows to move, SPACE to launch/pause, ESC for menu", True, (150, 150, 200))
        self.screen.blit(instr, (SCREEN_WIDTH//2 - instr.get_width()//2, SCREEN_HEIGHT - 30))
        
    def draw_instructions(self):
        self.screen.fill(BACKGROUND)
        
        title_font = safe_font('Arial', 48, bold=True)
        title = title_font.render("INSTRUCTIONS", True, (255, 215, 0))
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 50))
        
        font = safe_font('Arial', 24)
        lines = [
            "You are a royal defender protecting the Crystal Castle!",
            "",
            "GAMEPLAY:",
            "- Use LEFT and RIGHT arrow keys to move the paddle",
            "- Bounce the ball to break all the corrupted bricks",
            "- Don't let the ball fall below your paddle!",
            "",
            "SCORING:",
            "- Red Bricks: 10 points",
            "- Orange Bricks: 20 points",
            "- Green Bricks: 30 points",
            "- Yellow Bricks: 40 points",
            "- Silver Bricks: 50 points (requires 2 hits)",
            "- Gold Bricks: 100 points",
            "- Level Complete: 100 bonus points",
            "",
            "WIN CONDITION:",
            "- Clear all 3 levels to restore the castle!",
            "",
            "Press ESC to return to main menu"
        ]
        
        y_offset = 120
        for line in lines:
            text = font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, y_offset))
            y_offset += 30
            
    def draw_game_over(self):
        self.screen.fill(BACKGROUND)

        if self.level > 3:
            title = "CASTLE RESTORED!"
            message = f"Final Score: {self.score}"
            color = (50, 255, 50)

        else:
            title = "Game Over"
            message = f"Score: {self.score}"
            color = (255, 50, 50)

        title_font = safe_font('Ariel', 64, bold=True)
        title_text = title_font.render(title, True, color)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 120))

        # Draw score
        font = safe_font('Arial', 36)
        score_text = font.render(message, True, TEXT_COLOR)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 210))

            # Draw buttons FIRST
        for button in self.buttons:
            button.draw(self.screen)

        # Draw level reached AFTER buttons
        level_text = font.render(f"Level Reached: {self.level}/3", True, TEXT_COLOR)
        self.screen.blit(
            level_text,
            (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 460)
        )

            
    def draw_level_complete(self):
        self.screen.fill(BACKGROUND)
        
        title_font = safe_font('Arial', 64, bold=True)
        title = title_font.render("LEVEL COMPLETE!", True, (50, 255, 150))
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
        
        font = safe_font('Arial', 36)
        score_text = font.render(f"Score: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, 250))
        
        next_level_text = font.render(f"Next Level: {self.level + 1}/3", True, TEXT_COLOR)
        self.screen.blit(next_level_text, (SCREEN_WIDTH//2 - next_level_text.get_width()//2, 300))
        
        # Draw continue prompt
        prompt_font = safe_font('Arial', 24)
        prompt = prompt_font.render("Press SPACE to continue to next level", True, (200, 200, 255))
        self.screen.blit(prompt, (SCREEN_WIDTH//2 - prompt.get_width()//2, 400))
        
    def draw_game(self):
        # Draw background
        self.screen.fill(BACKGROUND)
        
        # Draw bricks
        for brick in self.bricks:
            brick.draw(self.screen)
            
        # Draw paddle and ball
        self.paddle.draw(self.screen)
        self.ball.draw(self.screen)
        
        # Draw HUD
        self.draw_hud()
        
        # Draw pause indicator if paused
        if self.state == STATE_PAUSED:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            font = safe_font('Arial', 72, bold=True)
            pause_text = font.render("PAUSED", True, (255, 215, 0))
            self.screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
            
            small_font = safe_font('Arial', 24)
            continue_text = small_font.render("Press SPACE to continue", True, TEXT_COLOR)
            self.screen.blit(continue_text, (SCREEN_WIDTH//2 - continue_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
            
    def run(self):
        running = True
        
        while running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Handle window resize so layout stays usable when maximized
                if event.type == pygame.VIDEORESIZE:
                    new_w, new_h = event.w, event.h
                    # Update screen surface and globals used for layout
                    self.screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
                    # Update module-level width/height so drawing uses new dimensions
                    global SCREEN_WIDTH, SCREEN_HEIGHT
                    SCREEN_WIDTH = new_w
                    SCREEN_HEIGHT = new_h
                    # Ensure paddle remains inside new bounds
                    if self.paddle:
                        if self.paddle.rect.right > SCREEN_WIDTH:
                            self.paddle.rect.right = SCREEN_WIDTH - 1
                    
                # Handle buttons based on game state
                if self.state in [STATE_MENU, STATE_GAME_OVER]:
                    for button in self.buttons:
                        button.check_hover(mouse_pos)
                        action = button.handle_event(event)
                        if action:
                            # menu select sound
                            self.play_sound('menu')
                            if action == "start":
                                self.reset_game()
                                # go to ready state so player can press SPACE to launch
                                self.state = STATE_READY
                            elif action == "instructions":
                                self.state = STATE_INSTRUCTIONS
                            elif action == "quit":
                                running = False
                            elif action == "restart":
                                self.reset_game()
                                self.state = STATE_READY
                            elif action == "menu":
                                self.state = STATE_MENU
                                self.create_menu_buttons()
                
                # Keyboard controls for gameplay
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == STATE_PLAYING or self.state == STATE_PAUSED:
                            self.state = STATE_MENU
                            self.create_menu_buttons()
                        elif self.state == STATE_INSTRUCTIONS:
                            self.state = STATE_MENU
                            
                    if event.key == pygame.K_SPACE:
                        if self.state == STATE_READY:
                            # launch ball
                            self.state = STATE_PLAYING
                        elif self.state == STATE_PLAYING:
                            self.state = STATE_PAUSED
                        elif self.state == STATE_PAUSED:
                            self.state = STATE_PLAYING
                        elif self.state == STATE_LEVEL_COMPLETE:
                            self.next_level()
                            
            # Game state updates
            # Allow paddle movement in PLAYING and READY states
            if self.state in (STATE_PLAYING, STATE_READY):
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:
                    self.paddle.move("left", SCREEN_WIDTH)
                if keys[pygame.K_RIGHT]:
                    self.paddle.move("right", SCREEN_WIDTH)

            # When playing, update ball and collisions. When ready, keep ball on paddle.
            if self.state == STATE_PLAYING:
                # Update ball position
                self.ball.move()

                # Handle collisions
                self.handle_collisions()
            elif self.state == STATE_READY:
                # keep ball positioned on paddle until player launches
                self.ball.rect.centerx = self.paddle.rect.centerx
                self.ball.rect.bottom = self.paddle.rect.top - 10
                
            # Drawing based on game state
            if self.state == STATE_MENU:
                self.draw_menu()
            elif self.state == STATE_INSTRUCTIONS:
                self.draw_instructions()
            elif self.state == STATE_GAME_OVER:
                self.draw_game_over()
            elif self.state == STATE_LEVEL_COMPLETE:
                self.draw_level_complete()
            else:  # PLAYING or PAUSED
                self.draw_game()

            # Background music: play when in PLAYING, stop otherwise
            try:
                if pygame.mixer.get_init():
                    if self.state == STATE_PLAYING:
                        self.play_sound('bgm')
                    else:
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.stop()
            except Exception:
                pass

            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()