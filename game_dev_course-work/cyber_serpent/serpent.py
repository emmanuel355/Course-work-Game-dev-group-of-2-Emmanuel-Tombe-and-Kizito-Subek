import pygame
import sys
import random
import time
import json
import math
from enum import Enum
from typing import List, Tuple, Optional
import os

# Initialize Pygame and mixer
pygame.init()
pygame.font.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = 35
GRID_HEIGHT = 23
CELL_SIZE = min(SCREEN_WIDTH // GRID_WIDTH, SCREEN_HEIGHT // GRID_HEIGHT)
GAME_AREA_WIDTH = CELL_SIZE * GRID_WIDTH
GAME_AREA_HEIGHT = CELL_SIZE * GRID_HEIGHT
GAME_AREA_X = (SCREEN_WIDTH - GAME_AREA_WIDTH) // 2
GAME_AREA_Y = (SCREEN_HEIGHT - GAME_AREA_HEIGHT) // 2 + 25

FPS = 60

# Colors (Neon Cyberpunk Theme)
BACKGROUND = (10, 10, 40)  # Deep space blue
GRID_COLOR = (20, 20, 60, 100)
GRID_LINE_COLOR = (0, 255, 255, 30)  # Cyan with transparency
SNAKE_HEAD_COLOR = (0, 255, 255)  # Neon cyan
SNAKE_BODY_COLOR = (0, 200, 200)
SNAKE_GLOW = (100, 255, 255, 100)
FOOD_COLORS = {
    'basic': (255, 255, 0),      # Yellow
    'power': (0, 150, 255),      # Blue
    'multiplier': (255, 0, 255), # Magenta
    'shield': (0, 255, 100),     # Green
    'boss': (255, 50, 50)        # Red
}
OBSTACLE_COLOR = (100, 100, 255, 200)
UI_COLOR = (0, 200, 255)
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (0, 100, 200)      # Darker blue
BUTTON_HOVER = (50, 150, 250)     # Blue hover color
BUTTON_TEXT_COLOR = (255, 255, 255)  # White text always
BUTTON_BORDER = (255, 255, 255)   # White border
PANEL_COLOR = (20, 20, 60, 200)

# Game states
class GameState(Enum):
    MAIN_MENU = 0
    INSTRUCTIONS = 1
    READY_TO_PLAY = 2      # NEW: Game loaded but waiting for space
    PLAYING = 3
    LEVEL_TRANSITION = 4
    GAME_OVER = 5
    PAUSED = 6

# Directions
class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class SoundManager:
    def __init__(self):
        self.sounds = {}
        self.create_all_sounds()  # Generate ALL sounds immediately
        self.music_playing = False
        self.music_channel = None
    
    def create_all_sounds(self):
        
        
        # Create all sound effects
        self.sounds = {
            'eat_basic': self.generate_beep_sound(440, 100, 0.3),
            'eat_power': self.generate_beep_sound(523, 150, 0.4),
            'eat_multiplier': self.generate_beep_sound(659, 200, 0.5),
            'eat_shield': self.generate_beep_sound(392, 150, 0.4),
            'eat_boss': self.generate_beep_sound(784, 250, 0.6),
            'collision': self.generate_collision_sound(),
            'game_over': self.generate_game_over_sound(),
            'level_complete': self.generate_success_sound(0.6),
            'mission_complete': self.generate_victory_sound(),
            'button_hover': self.generate_beep_sound(262, 50, 0.2),
            'button_click': self.generate_beep_sound(330, 80, 0.3)
        }
        
        # Create background music as a continuous sound
        self.background_music = self.generate_background_music()
        
        # Set volumes
        for name, sound in self.sounds.items():
            if 'eat' in name:
                sound.set_volume(0.5)
            elif 'collision' in name:
                sound.set_volume(0.7)
            elif 'button' in name:
                sound.set_volume(0.3)
            else:
                sound.set_volume(0.6)
    
    def generate_background_music(self):
        """Generate ambient background music"""
        sample_rate = 44100
        duration = 44100 * 2  # 2 seconds of audio for looping
        buf = bytearray(duration * 2)
        
        # Create a simple ambient loop
        for i in range(duration):
            # Multiple layered tones for ambiance
            t = i / sample_rate
            tone1 = 0.1 * math.sin(220 * math.pi * 2 * t)
            tone2 = 0.05 * math.sin(329.63 * math.pi * 2 * t)  # E
            tone3 = 0.03 * math.sin(440 * math.pi * 2 * t)     # A
            tone4 = 0.02 * math.sin(554.37 * math.pi * 2 * t)  # C#
            
            # Pulsing effect
            pulse = 0.3 + 0.2 * math.sin(0.5 * math.pi * 2 * t)
            
            combined = int(pulse * 32767.0 * (tone1 + tone2 + tone3 + tone4))
            buf[2*i] = combined & 0xff
            buf[2*i+1] = (combined >> 8) & 0xff
        
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        sound.set_volume(0.15)  # Low volume for background
        return sound
    
    def generate_beep_sound(self, frequency, duration, volume):
        """Generate a simple beep sound"""
        sample_rate = 44100
        n_samples = int(round(duration * 0.001 * sample_rate))
        buf = bytearray(n_samples * 2)
        
        for i in range(n_samples):
            sample = int(volume * 32767.0 * 
                        math.sin(frequency * math.pi * 2 * i / sample_rate))
            buf[2*i] = sample & 0xff
            buf[2*i+1] = (sample >> 8) & 0xff
        
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        return sound
    
    def generate_collision_sound(self):
        """Generate a collision sound"""
        sample_rate = 44100
        duration = 500  # ms
        n_samples = int(round(duration * 0.001 * sample_rate))
        buf = bytearray(n_samples * 2)
        
        # Create a descending tone
        for i in range(n_samples):
            freq = 440 - (300 * i / n_samples)  # Descend from 440 to 140 Hz
            sample = int(0.5 * 32767.0 * 
                        math.sin(freq * math.pi * 2 * i / sample_rate))
            buf[2*i] = sample & 0xff
            buf[2*i+1] = (sample >> 8) & 0xff
        
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        return sound
    
    def generate_game_over_sound(self):
        """Generate a game over sound"""
        sample_rate = 44100
        duration = 800  # ms
        n_samples = int(round(duration * 0.001 * sample_rate))
        buf = bytearray(n_samples * 2)
        
        # Create a sad descending tone
        for i in range(n_samples):
            freq = 330 - (200 * i / n_samples)  # Descend from 330 to 130 Hz
            sample = int(0.4 * 32767.0 * 
                        math.sin(freq * math.pi * 2 * i / sample_rate))
            buf[2*i] = sample & 0xff
            buf[2*i+1] = (sample >> 8) & 0xff
        
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        return sound
    
    def generate_success_sound(self, volume=0.6):
        """Generate a success sound"""
        sample_rate = 44100
        duration = 800  # ms
        n_samples = int(round(duration * 0.001 * sample_rate))
        buf = bytearray(n_samples * 2)
        
        # Create an ascending tone
        for i in range(n_samples):
            freq = 220 + (440 * i / n_samples)  # Ascend from 220 to 660 Hz
            sample = int(volume * 32767.0 * 
                        math.sin(freq * math.pi * 2 * i / sample_rate))
            buf[2*i] = sample & 0xff
            buf[2*i+1] = (sample >> 8) & 0xff
        
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        return sound
    
    def generate_victory_sound(self):
        """Generate a victory sound (multiple ascending tones)"""
        sample_rate = 44100
        duration = 1000  # ms
        n_samples = int(round(duration * 0.001 * sample_rate))
        buf = bytearray(n_samples * 2)
        
        # Create multiple ascending tones
        for i in range(n_samples):
            # Three different ascending frequencies
            freq1 = 220 + (440 * i / n_samples)
            freq2 = 330 + (660 * i / n_samples)
            freq3 = 440 + (880 * i / n_samples)
            
            sample1 = 0.3 * math.sin(freq1 * math.pi * 2 * i / sample_rate)
            sample2 = 0.2 * math.sin(freq2 * math.pi * 2 * i / sample_rate)
            sample3 = 0.2 * math.sin(freq3 * math.pi * 2 * i / sample_rate)
            
            combined = int(0.6 * 32767.0 * (sample1 + sample2 + sample3))
            buf[2*i] = combined & 0xff
            buf[2*i+1] = (combined >> 8) & 0xff
        
        sound = pygame.mixer.Sound(buffer=bytes(buf))
        return sound
    
    def play_background_music(self):
        """Start playing generated background music"""
        if not self.music_playing:
            self.background_music.play(-1)  # -1 means loop indefinitely
            self.music_playing = True
    
    def stop_background_music(self):
        """Stop background music"""
        if self.music_playing:
            self.background_music.stop()
            self.music_playing = False
    
    def play_sound(self, sound_name):
        """Play a sound effect by name"""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

class CyberSerpent:
    def __init__(self):
        self.reset()
        
    def reset(self):
        # Start in the middle of the grid
        start_x = GRID_WIDTH // 2
        start_y = GRID_HEIGHT // 2
        self.segments = [(start_x, start_y), (start_x-1, start_y), (start_x-2, start_y)]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.growth_pending = 0
        self.speed = 8  # Moves per second
        self.last_move_time = 0
        self.length = 3
        self.score_multiplier = 1
        self.multiplier_timer = 0
        self.shield_active = False
        self.shield_timer = 0
        self.speed_boost = False
        self.speed_timer = 0
        self.combo = 0
        self.combo_timer = 0
        
    def change_direction(self, new_direction):
        # Prevent 180-degree turns
        opposite_directions = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT
        }
        
        if new_direction != opposite_directions.get(self.direction):
            self.next_direction = new_direction
    
    def update(self, current_time, game_speed_multiplier=1.0):
        # Update timers
        if self.multiplier_timer > 0:
            self.multiplier_timer -= 1
            if self.multiplier_timer == 0:
                self.score_multiplier = 1
        
        if self.shield_timer > 0:
            self.shield_timer -= 1
            if self.shield_timer == 0:
                self.shield_active = False
        
        if self.speed_timer > 0:
            self.speed_timer -= 1
            if self.speed_timer == 0:
                self.speed_boost = False
        
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo = 0
        
        # Calculate actual speed
        actual_speed = self.speed
        if self.speed_boost:
            actual_speed *= 1.5
        actual_speed *= game_speed_multiplier
        
        # Move based on time
        move_interval = 1.0 / actual_speed
        if current_time - self.last_move_time >= move_interval:
            self.last_move_time = current_time
            self.direction = self.next_direction
            
            # Get head position
            head_x, head_y = self.segments[0]
            dx, dy = self.direction.value
            
            # Calculate new head position
            new_head = (head_x + dx, head_y + dy)
            
            # Add new head
            self.segments.insert(0, new_head)
            
            # Remove tail if no growth pending
            if self.growth_pending > 0:
                self.growth_pending -= 1
                self.length += 1
            else:
                self.segments.pop()
            
            return True
        return False
    
    def grow(self, amount=1):
        self.growth_pending += amount
        self.combo += 1
        self.combo_timer = 30  # 0.5 seconds at 60 FPS
        
    def activate_multiplier(self, duration=300):  # 5 seconds at 60 FPS
        self.score_multiplier = 2
        self.multiplier_timer = duration
    
    def activate_shield(self, duration=180):  # 3 seconds at 60 FPS
        self.shield_active = True
        self.shield_timer = duration
    
    def activate_speed_boost(self, duration=240):  # 4 seconds at 60 FPS
        self.speed_boost = True
        self.speed_timer = duration
    
    def get_head_position(self):
        return self.segments[0]
    
    def check_self_collision(self):
        head = self.segments[0]
        return head in self.segments[1:]
    
    def draw(self, screen):
        # Draw each segment with glow effect
        for i, (x, y) in enumerate(self.segments):
            # Calculate color based on position and state
            if i == 0:  # Head
                color = SNAKE_HEAD_COLOR
                size_mod = 1.2
            else:
                # Gradient from head to tail
                t = i / len(self.segments)
                color = (
                    int(SNAKE_BODY_COLOR[0] * (1 - t) + 50 * t),
                    int(SNAKE_BODY_COLOR[1] * (1 - t) + 50 * t),
                    int(SNAKE_BODY_COLOR[2] * (1 - t) + 50 * t)
                )
                size_mod = 1.0 - (0.3 * t)
            
            # Apply shield effect
            if self.shield_active and i < 3:
                shield_color = (0, 255, 100, 100)
                shield_rect = pygame.Rect(
                    GAME_AREA_X + x * CELL_SIZE - 2,
                    GAME_AREA_Y + y * CELL_SIZE - 2,
                    CELL_SIZE + 4,
                    CELL_SIZE + 4
                )
                pygame.draw.rect(screen, shield_color, shield_rect, 2, border_radius=3)
            
            # Draw segment
            segment_rect = pygame.Rect(
                GAME_AREA_X + x * CELL_SIZE + (CELL_SIZE * (1 - size_mod)) / 2,
                GAME_AREA_Y + y * CELL_SIZE + (CELL_SIZE * (1 - size_mod)) / 2,
                CELL_SIZE * size_mod,
                CELL_SIZE * size_mod
            )
            
            # Draw with rounded corners for cybernetic look
            pygame.draw.rect(screen, color, segment_rect, border_radius=4)
            
            # Draw inner glow
            inner_rect = segment_rect.inflate(-4, -4)
            pygame.draw.rect(screen, (*color[:3], 150), inner_rect, border_radius=3)
            
            # Draw connector lines between segments (except for head)
            if i > 0:
                prev_x, prev_y = self.segments[i-1]
                center_x = GAME_AREA_X + x * CELL_SIZE + CELL_SIZE // 2
                center_y = GAME_AREA_Y + y * CELL_SIZE + CELL_SIZE // 2
                prev_center_x = GAME_AREA_X + prev_x * CELL_SIZE + CELL_SIZE // 2
                prev_center_y = GAME_AREA_Y + prev_y * CELL_SIZE + CELL_SIZE // 2
                
                pygame.draw.line(
                    screen, 
                    (*color[:3], 200), 
                    (prev_center_x, prev_center_y), 
                    (center_x, center_y), 
                    3
                )

class EnergyOrb:
    def __init__(self, orb_type='basic'):
        self.type = orb_type
        self.position = (0, 0)
        self.spawn_time = time.time()
        self.spawn()
        self.pulse_phase = 0
        self.particles = []
        
    def spawn(self, avoid_positions=None, obstacles=None):
        if avoid_positions is None:
            avoid_positions = []
        if obstacles is None:
            obstacles = []
        
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            
            if (x, y) not in avoid_positions and (x, y) not in obstacles:
                self.position = (x, y)
                self.spawn_time = time.time()
                
                # Create initial particles
                self.particles = []
                for _ in range(15):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(0.5, 2)
                    lifetime = random.randint(20, 60)
                    self.particles.append({
                        'x': x * CELL_SIZE + CELL_SIZE // 2,
                        'y': y * CELL_SIZE + CELL_SIZE // 2,
                        'dx': math.cos(angle) * speed,
                        'dy': math.sin(angle) * speed,
                        'lifetime': lifetime,
                        'max_lifetime': lifetime
                    })
                return True
        return False
    
    def update_particles(self):
        new_particles = []
        for p in self.particles:
            p['x'] += p['dx']
            p['y'] += p['dy']
            p['lifetime'] -= 1
            if p['lifetime'] > 0:
                new_particles.append(p)
        self.particles = new_particles
        
        # Occasionally add new particles
        if random.random() < 0.3 and len(self.particles) < 20:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.5, 1.5)
            lifetime = random.randint(30, 50)
            self.particles.append({
                'x': self.position[0] * CELL_SIZE + CELL_SIZE // 2,
                'y': self.position[1] * CELL_SIZE + CELL_SIZE // 2,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'lifetime': lifetime,
                'max_lifetime': lifetime
            })
    
    def update(self):
        self.pulse_phase = (self.pulse_phase + 0.1) % (2 * math.pi)
        self.update_particles()
    
    def draw(self, screen):
        x, y = self.position
        center_x = GAME_AREA_X + x * CELL_SIZE + CELL_SIZE // 2
        center_y = GAME_AREA_Y + y * CELL_SIZE + CELL_SIZE // 2
        
        # Draw particles
        for p in self.particles:
            alpha = int(255 * (p['lifetime'] / p['max_lifetime']))
            color = (*FOOD_COLORS.get(self.type, (255, 255, 0)), alpha)
            radius = int(2 * (p['lifetime'] / p['max_lifetime']))
            pygame.draw.circle(screen, color, (int(p['x'] + GAME_AREA_X), int(p['y'] + GAME_AREA_Y)), radius)
        
        # Pulse effect
        pulse_size = 1 + 0.2 * math.sin(self.pulse_phase)
        radius = int(CELL_SIZE * 0.4 * pulse_size)
        
        # Draw orb with glow
        for i in range(3, 0, -1):
            glow_radius = radius + i * 2
            alpha = 100 - i * 30
            glow_color = (*FOOD_COLORS.get(self.type, (255, 255, 0)), alpha)
            pygame.draw.circle(screen, glow_color, (center_x, center_y), glow_radius)
        
        # Main orb
        pygame.draw.circle(screen, FOOD_COLORS.get(self.type, (255, 255, 0)), 
                          (center_x, center_y), radius)
        
        # Inner highlight
        highlight_radius = radius // 2
        highlight_color = tuple(min(c + 100, 255) for c in FOOD_COLORS.get(self.type, (255, 255, 0)))
        pygame.draw.circle(screen, highlight_color, 
                          (center_x - radius//3, center_y - radius//3), 
                          highlight_radius)
        
        # Draw orb type symbol
        font = pygame.font.SysFont('Arial', 14, bold=True)
        symbols = {
            'basic': '●',
            'power': '⚡',
            'multiplier': '×2',
            'shield': '🛡',
            'boss': '★'
        }
        symbol = symbols.get(self.type, '●')
        text = font.render(symbol, True, (255, 255, 255))
        text_rect = text.get_rect(center=(center_x, center_y))
        screen.blit(text, text_rect)

class Obstacle:
    def __init__(self, x, y, moving=False):
        self.position = (x, y)
        self.moving = moving
        if moving:
            self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            self.speed = 0.5  # cells per second
            self.last_move_time = 0
    
    def update(self, current_time):
        if self.moving:
            move_interval = 1.0 / self.speed
            if current_time - self.last_move_time >= move_interval:
                self.last_move_time = current_time
                x, y = self.position
                dx, dy = self.direction
                
                new_x = x + dx
                new_y = y + dy
                
                # Bounce off walls
                if new_x < 0 or new_x >= GRID_WIDTH:
                    self.direction = (-dx, dy)
                    new_x = max(0, min(new_x, GRID_WIDTH - 1))
                if new_y < 0 or new_y >= GRID_HEIGHT:
                    self.direction = (dx, -dy)
                    new_y = max(0, min(new_y, GRID_HEIGHT - 1))
                
                self.position = (new_x, new_y)
    
    def draw(self, screen):
        x, y = self.position
        rect = pygame.Rect(
            GAME_AREA_X + x * CELL_SIZE + 2,
            GAME_AREA_Y + y * CELL_SIZE + 2,
            CELL_SIZE - 4,
            CELL_SIZE - 4
        )
        
        # Draw with cyberpunk style
        pygame.draw.rect(screen, OBSTACLE_COLOR, rect, border_radius=3)
        
        # Draw inner pattern
        inner_rect = rect.inflate(-4, -4)
        pygame.draw.rect(screen, (150, 150, 255, 150), inner_rect, 1, border_radius=2)
        
        # Draw moving indicator
        if self.moving:
            center_x = rect.centerx
            center_y = rect.centery
            arrow_size = 3
            if self.direction == (1, 0):  # Right
                points = [(center_x - arrow_size, center_y - arrow_size),
                         (center_x + arrow_size, center_y),
                         (center_x - arrow_size, center_y + arrow_size)]
            elif self.direction == (-1, 0):  # Left
                points = [(center_x + arrow_size, center_y - arrow_size),
                         (center_x - arrow_size, center_y),
                         (center_x + arrow_size, center_y + arrow_size)]
            elif self.direction == (0, 1):  # Down
                points = [(center_x - arrow_size, center_y - arrow_size),
                         (center_x, center_y + arrow_size),
                         (center_x + arrow_size, center_y - arrow_size)]
            else:  # Up
                points = [(center_x - arrow_size, center_y + arrow_size),
                         (center_x, center_y - arrow_size),
                         (center_x + arrow_size, center_y + arrow_size)]
            
            pygame.draw.polygon(screen, (255, 255, 255), points)

class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.is_hovered = False
        self.was_hovered = False  # To detect hover state changes
        self.pulse = 0
        
    def update(self):
        self.pulse = (self.pulse + 0.1) % (2 * math.pi)
        
    def draw(self, screen):
        # Pulse effect when hovered
        pulse_offset = 0
        if self.is_hovered:
            pulse_offset = int(5 * math.sin(self.pulse))
        
        # Draw button with glow when hovered
        color = BUTTON_HOVER if self.is_hovered else BUTTON_COLOR
        
        # Draw glow effect when hovered
        if self.is_hovered:
            glow_rect = self.rect.inflate(pulse_offset * 2, pulse_offset * 2)
            pygame.draw.rect(screen, (*BUTTON_HOVER[:3], 100), glow_rect, border_radius=12)
        
        # Main button - FIXED: Always use white text for good contrast
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, BUTTON_BORDER, self.rect, 3, border_radius=10)
        
        # Draw text - ALWAYS WHITE for maximum visibility
        font = pygame.font.SysFont('Courier New', 24, bold=True)
        text_surf = font.render(self.text, True, BUTTON_TEXT_COLOR)  # Always white
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
        # Draw additional hover effect (blue instead of white)
        if self.is_hovered:
            highlight_rect = self.rect.inflate(-8, -8)
            pygame.draw.rect(screen, (100, 150, 255, 40), highlight_rect, border_radius=6)
        
    def check_hover(self, pos, sound_manager):
        self.was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(pos)
        
        # Play hover sound when button is first hovered
        if self.is_hovered and not self.was_hovered and sound_manager:
            sound_manager.play_sound('button_hover')
        
        return self.is_hovered
        
    def handle_event(self, event, sound_manager):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered and self.action:
                if sound_manager:
                    sound_manager.play_sound('button_click')
                return self.action
        return None

class CyberSerpentGame:
    def __init__(self):
        # Make window resizable and maximizeable
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Cyber Serpent: Neon Nexus - Ready to Play")
        self.clock = pygame.time.Clock()
        
        # Sound manager - uses only generated sounds
        self.sound_manager = SoundManager()
        
        # Game state
        self.state = GameState.MAIN_MENU
        self.score = 0
        self.high_score = self.load_high_score()
        self.level = 1
        self.orbs_collected = 0
        self.orbs_required = 10
        self.boss_orbs_collected = 0
        self.boss_orbs_required = 0
        self.game_time = 0
        self.level_start_time = 0
        
        # Level transition control
        self.level_transition_start_time = 0
        self.can_proceed_to_next_level = False
        
        # Ready state control
        self.ready_start_time = 0
        self.ready_blink = True
        
        # Resize tracking
        self.original_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.current_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.needs_redraw = False
        
        # Game objects
        self.serpent = CyberSerpent()
        self.orbs = []
        self.obstacles = []
        self.particles = []
        
        # UI elements
        self.buttons = []
        self.font_large = pygame.font.SysFont('Courier New', 48, bold=True)
        self.font_medium = pygame.font.SysFont('Courier New', 32, bold=True)
        self.font_small = pygame.font.SysFont('Courier New', 20)
        self.font_hud = pygame.font.SysFont('Courier New', 18, bold=True)
        
        # Level configuration
        self.level_configs = {
            1: {'speed': 8, 'grid': (30, 25), 'obstacles': 0, 'moving_obstacles': 0, 'orbs_required': 10},
            2: {'speed': 10, 'grid': (30, 25), 'obstacles': 5, 'moving_obstacles': 0, 'orbs_required': 12},
            3: {'speed': 12, 'grid': (30, 25), 'obstacles': 8, 'moving_obstacles': 2, 'orbs_required': 15},
            4: {'speed': 14, 'grid': (30, 25), 'obstacles': 12, 'moving_obstacles': 4, 'orbs_required': 18},
            5: {'speed': 16, 'grid': (30, 25), 'obstacles': 15, 'moving_obstacles': 6, 'orbs_required': 20}
        }
        
        # Initialize
        self.create_menu_buttons()
        self.reset_game()
    
    def load_high_score(self):
        try:
            with open('high_score.json', 'r') as f:
                data = json.load(f)
                return data.get('high_score', 0)
        except:
            return 0
    
    def save_high_score(self):
        data = {'high_score': self.high_score}
        with open('high_score.json', 'w') as f:
            json.dump(data, f)
    
    def create_menu_buttons(self):
        # Calculate button positions relative to current screen size
        center_x = self.current_size[0] // 2
        button_width = 250
        button_height = 50
        button_spacing = 70
        
        # Position buttons at 40% from top of screen
        start_y = int(self.current_size[1] * 0.4)
        
        self.buttons = [
            Button(center_x - button_width//2, start_y, button_width, button_height, "START MISSION", "start"),
            Button(center_x - button_width//2, start_y + button_spacing, button_width, button_height, "INSTRUCTIONS", "instructions"),
            Button(center_x - button_width//2, start_y + button_spacing * 2, button_width, button_height, "HIGH SCORES", "high_scores"),
            Button(center_x - button_width//2, start_y + button_spacing * 3, button_width, button_height, "QUIT", "quit")
        ]
    
    def create_game_over_buttons(self):
        center_x = self.current_size[0] // 2
        button_width = 200
        button_height = 45
        
        self.buttons = [
            Button(center_x - button_width - 10, self.current_size[1] // 2 + 100, button_width, button_height, "RETRY", "retry"),
            Button(center_x + 10, self.current_size[1] // 2 + 100, button_width, button_height, "MAIN MENU", "menu")
        ]
    
    def handle_resize(self, new_width, new_height):
        """Handle window resizing"""
        self.current_size = (new_width, new_height)
        self.screen = pygame.display.set_mode(self.current_size, pygame.RESIZABLE)
        
        # Update global game area position - FIXED: Center properly
        global GAME_AREA_X, GAME_AREA_Y
        
        # Calculate centered position
        GAME_AREA_X = (new_width - GAME_AREA_WIDTH) // 2
        GAME_AREA_Y = (new_height - GAME_AREA_HEIGHT) // 2
        
        # Recalculate button positions if needed
        if self.state in [GameState.MAIN_MENU, GameState.GAME_OVER]:
            if self.state == GameState.MAIN_MENU:
                self.create_menu_buttons()
            elif self.state == GameState.GAME_OVER:
                self.create_game_over_buttons()
        
        self.needs_redraw = True
    
    def reset_game(self):
        self.score = 0
        self.level = 1
        self.orbs_collected = 0
        self.boss_orbs_collected = 0
        self.game_time = 0
        self.level_start_time = 0
        self.serpent.reset()
        self.orbs = []
        self.obstacles = []
        self.particles = []
        self.setup_level()
    
    def setup_level(self):
        config = self.level_configs[self.level]
        self.orbs_required = config['orbs_required']
        self.boss_orbs_required = 1 if self.level >= 3 else 0
        
        # Set serpent speed
        self.serpent.speed = config['speed']
        
        # Clear existing objects
        self.orbs = []
        self.obstacles = []
        
        # Create obstacles
        for _ in range(config['obstacles']):
            while True:
                x = random.randint(0, GRID_WIDTH - 1)
                y = random.randint(0, GRID_HEIGHT - 1)
                pos = (x, y)
                
                # Avoid spawn near serpent head
                head_x, head_y = self.serpent.get_head_position()
                distance = abs(head_x - x) + abs(head_y - y)
                
                if (pos not in self.serpent.segments and 
                    pos not in [obs.position for obs in self.obstacles] and
                    distance > 5):
                    moving = _ < config['moving_obstacles']
                    self.obstacles.append(Obstacle(x, y, moving))
                    break
        
        # Create initial orbs
        self.spawn_orb('basic')
        if self.level >= 2:
            self.spawn_orb('power')
        if self.level >= 3:
            self.spawn_orb('multiplier')
        if self.level >= 4:
            self.spawn_orb('shield')
        
        self.level_start_time = 0  # Will be set when game actually starts
    
    def spawn_orb(self, orb_type='basic'):
        avoid_positions = self.serpent.segments + [obs.position for obs in self.obstacles]
        avoid_positions += [orb.position for orb in self.orbs]
        
        orb = EnergyOrb(orb_type)
        if orb.spawn(avoid_positions, [obs.position for obs in self.obstacles]):
            self.orbs.append(orb)
            return True
        return False
    
    def handle_collisions(self):
        head = self.serpent.get_head_position()
        
        # Check wall collision
        x, y = head
        if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
            if not self.serpent.shield_active:
                return "wall"
        
        # Check obstacle collision
        for obstacle in self.obstacles:
            if head == obstacle.position:
                if not self.serpent.shield_active:
                    return "obstacle"
        
        # Check self collision
        if self.serpent.check_self_collision():
            return "self"
        
        # Check orb collision
        for orb in self.orbs[:]:
            if head == orb.position:
                # Play appropriate eating sound
                if orb.type == 'basic':
                    self.sound_manager.play_sound('eat_basic')
                elif orb.type == 'power':
                    self.sound_manager.play_sound('eat_power')
                elif orb.type == 'multiplier':
                    self.sound_manager.play_sound('eat_multiplier')
                elif orb.type == 'shield':
                    self.sound_manager.play_sound('eat_shield')
                elif orb.type == 'boss':
                    self.sound_manager.play_sound('eat_boss')
                
                # Calculate points
                points = {
                    'basic': 10,
                    'power': 25,
                    'multiplier': 50,
                    'shield': 75,
                    'boss': 100
                }.get(orb.type, 10)
                
                # Apply multiplier
                points *= self.serpent.score_multiplier
                
                # Add combo bonus
                combo_bonus = min(self.serpent.combo * 5, 50)
                points += combo_bonus
                
                # Add to score
                self.score += points
                self.orbs_collected += 1
                
                # Handle orb effects
                if orb.type == 'basic':
                    self.serpent.grow()
                elif orb.type == 'power':
                    self.serpent.grow()
                    self.serpent.activate_speed_boost()
                elif orb.type == 'multiplier':
                    self.serpent.grow()
                    self.serpent.activate_multiplier()
                elif orb.type == 'shield':
                    self.serpent.grow()
                    self.serpent.activate_shield()
                elif orb.type == 'boss':
                    self.serpent.grow(2)  # Grow by 2
                    self.boss_orbs_collected += 1
                
                # Remove collected orb
                self.orbs.remove(orb)
                
                # Create particles
                self.create_particles(head, orb.type)
                
                # Spawn new orb
                if orb.type == 'boss':
                    # Spawn random special orb
                    special_types = ['power', 'multiplier', 'shield']
                    new_type = random.choice(special_types) if self.level >= 2 else 'basic'
                    self.spawn_orb(new_type)
                else:
                    # Chance to spawn special orb based on level
                    spawn_chance = 0.1 + (self.level * 0.05)
                    if random.random() < spawn_chance and self.level >= 2:
                        special_types = ['power', 'multiplier', 'shield']
                        weights = [0.5, 0.3, 0.2]
                        new_type = random.choices(special_types, weights=weights, k=1)[0]
                        self.spawn_orb(new_type)
                    else:
                        self.spawn_orb('basic')
                
                # Check level completion
                if (self.orbs_collected >= self.orbs_required and 
                    self.boss_orbs_collected >= self.boss_orbs_required):
                    return "level_complete"
                
                return "orb"
        
        return None
    
    def create_particles(self, position, orb_type):
        x, y = position
        color = FOOD_COLORS.get(orb_type, (255, 255, 0))
        
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            lifetime = random.randint(20, 40)
            self.particles.append({
                'x': x * CELL_SIZE + CELL_SIZE // 2,
                'y': y * CELL_SIZE + CELL_SIZE // 2,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'lifetime': lifetime,
                'max_lifetime': lifetime,
                'color': color
            })
    
    def update_particles(self):
        new_particles = []
        for p in self.particles:
            p['x'] += p['dx']
            p['y'] += p['dy']
            p['lifetime'] -= 1
            if p['lifetime'] > 0:
                new_particles.append(p)
        self.particles = new_particles
    
    def draw_particles(self):
        for p in self.particles:
            alpha = int(255 * (p['lifetime'] / p['max_lifetime']))
            color = (*p['color'][:3], alpha)
            pos = (int(p['x']) + GAME_AREA_X, int(p['y']) + GAME_AREA_Y)
            radius = int(3 * (p['lifetime'] / p['max_lifetime']))
            pygame.draw.circle(self.screen, color, pos, radius)
    
    def draw_grid(self):
        # Draw background
        grid_rect = pygame.Rect(GAME_AREA_X, GAME_AREA_Y, GAME_AREA_WIDTH, GAME_AREA_HEIGHT)
        pygame.draw.rect(self.screen, GRID_COLOR, grid_rect)
        
        # Draw grid lines
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(
                self.screen,
                GRID_LINE_COLOR,
                (GAME_AREA_X + x * CELL_SIZE, GAME_AREA_Y),
                (GAME_AREA_X + x * CELL_SIZE, GAME_AREA_Y + GAME_AREA_HEIGHT),
                1
            )
        
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(
                self.screen,
                GRID_LINE_COLOR,
                (GAME_AREA_X, GAME_AREA_Y + y * CELL_SIZE),
                (GAME_AREA_X + GAME_AREA_WIDTH, GAME_AREA_Y + y * CELL_SIZE),
                1
            )
        
        # Draw border
        pygame.draw.rect(self.screen, (0, 255, 255), grid_rect, 3)
        
        # Draw corner accents
        corner_size = 10
        corners = [
            (GAME_AREA_X, GAME_AREA_Y),
            (GAME_AREA_X + GAME_AREA_WIDTH, GAME_AREA_Y),
            (GAME_AREA_X, GAME_AREA_Y + GAME_AREA_HEIGHT),
            (GAME_AREA_X + GAME_AREA_WIDTH, GAME_AREA_Y + GAME_AREA_HEIGHT)
        ]
        
        for cx, cy in corners:
            pygame.draw.line(self.screen, (0, 255, 255), (cx, cy), (cx + corner_size, cy), 3)
            pygame.draw.line(self.screen, (0, 255, 255), (cx, cy), (cx, cy + corner_size), 3)
    
    def draw_hud(self):
        # Draw HUD background
        hud_height = 80
        hud_rect = pygame.Rect(0, 0, self.current_size[0], hud_height)
        pygame.draw.rect(self.screen, PANEL_COLOR, hud_rect)
        
        # Draw HUD border
        pygame.draw.line(self.screen, (0, 255, 255), (0, hud_height), (self.current_size[0], hud_height), 3)
        
        # Score
        score_text = self.font_hud.render(f"SCORE: {self.score}", True, UI_COLOR)
        self.screen.blit(score_text, (20, 20))
        
        # High Score
        high_score_text = self.font_hud.render(f"HIGH SCORE: {self.high_score}", True, UI_COLOR)
        self.screen.blit(high_score_text, (20, 45))
        
        # Level
        level_text = self.font_hud.render(f"LEVEL: {self.level}/5", True, UI_COLOR)
        level_x = self.current_size[0] // 2 - level_text.get_width() // 2
        self.screen.blit(level_text, (level_x, 20))
        
        # Orbs collected
        orbs_text = self.font_hud.render(f"ORBS: {self.orbs_collected}/{self.orbs_required}", True, UI_COLOR)
        orbs_x = self.current_size[0] // 2 - orbs_text.get_width() // 2
        self.screen.blit(orbs_text, (orbs_x, 45))
        
        # Boss orbs (if needed)
        if self.boss_orbs_required > 0:
            boss_text = self.font_hud.render(f"BOSS ORBS: {self.boss_orbs_collected}/{self.boss_orbs_required}", True, (255, 50, 50))
            boss_x = self.current_size[0] // 2 - boss_text.get_width() // 2
            self.screen.blit(boss_text, (boss_x, 65))
        
        # Length
        length_text = self.font_hud.render(f"LENGTH: {self.serpent.length}", True, UI_COLOR)
        self.screen.blit(length_text, (self.current_size[0] - 150, 20))
        
        # Multiplier
        if self.serpent.score_multiplier > 1:
            multiplier_text = self.font_hud.render(f"MULTIPLIER: {self.serpent.score_multiplier}x", True, (255, 0, 255))
            self.screen.blit(multiplier_text, (self.current_size[0] - 150, 45))
        
        # Shield indicator
        if self.serpent.shield_active:
            shield_text = self.font_hud.render(f"SHIELD: {self.serpent.shield_timer // 60}s", True, (0, 255, 100))
            self.screen.blit(shield_text, (self.current_size[0] - 150, 65))
        
        # Combo
        if self.serpent.combo > 1:
            combo_text = self.font_hud.render(f"COMBO: {self.serpent.combo}x", True, (255, 255, 0))
            combo_x = self.current_size[0] // 4 * 3 - combo_text.get_width() // 2
            self.screen.blit(combo_text, (combo_x, 20))
    
    def draw_ready_overlay(self):
        """Draw the 'Press Space to Start' overlay"""
        width, height = self.current_size
        
        # Create semi-transparent overlay
        overlay = pygame.Surface(self.current_size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Blinking effect
        current_time = time.time()
        blink_rate = 0.5  # seconds per blink
        self.ready_blink = int(current_time / blink_rate) % 2 == 0
        
        if self.ready_blink:
            # Draw ready text
            ready_text = self.font_large.render("READY TO PLAY", True, (0, 255, 255))
            self.screen.blit(ready_text, (width//2 - ready_text.get_width()//2, 
                                         height//2 - 100))
            
            # Draw instructions
            start_text = self.font_medium.render("PRESS SPACE TO START", True, (255, 255, 0))
            self.screen.blit(start_text, (width//2 - start_text.get_width()//2, 
                                         height//2))
            
            # Draw additional instructions
            controls_text = self.font_small.render("Use ARROW KEYS to move | ESC to return to menu", True, TEXT_COLOR)
            self.screen.blit(controls_text, (width//2 - controls_text.get_width()//2, 
                                           height//2 + 60))
    
    def draw_menu(self):
        # Draw animated background
        self.screen.fill(BACKGROUND)
        
        # Draw grid pattern in background
        width, height = self.current_size
        for x in range(0, width, 40):
            for y in range(0, height, 40):
                if (x + y) % 80 == 0:
                    pygame.draw.rect(self.screen, (0, 50, 100, 50), (x, y, 40, 40))
        
        # Draw title
        title = self.font_large.render("CYBER SERPENT", True, (0, 255, 255))
        subtitle = self.font_medium.render("NEON NEXUS", True, (255, 0, 255))
        
        # Add glow effect to title
        for offset in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
            glow_title = self.font_large.render("CYBER SERPENT", True, (0, 150, 255, 100))
            self.screen.blit(glow_title, (width//2 - title.get_width()//2 + offset[0], 
                                        100 + offset[1]))
        
        self.screen.blit(title, (width//2 - title.get_width()//2, 100))
        self.screen.blit(subtitle, (width//2 - subtitle.get_width()//2, 160))
        
        # Draw animated serpent preview
        preview_time = pygame.time.get_ticks() / 1000
        preview_length = 10
        preview_x = width // 2
        preview_y = 230
        
        for i in range(preview_length):
            offset_x = math.sin(preview_time + i * 0.3) * 100
            offset_y = math.cos(preview_time * 0.7 + i * 0.2) * 30
            segment_x = preview_x + offset_x
            segment_y = preview_y + offset_y + i * 5
            
            color = (
                int(100 + 155 * abs(math.sin(preview_time + i * 0.1))),
                int(100 + 155 * abs(math.cos(preview_time + i * 0.2))),
                255
            )
            
            pygame.draw.circle(self.screen, color, (int(segment_x), int(segment_y)), 10)
        
        # Draw buttons
        for button in self.buttons:
            button.update()
            button.draw(self.screen)
        
        # Draw version info
        version_text = self.font_small.render("v5.0 | READY TO PLAY SYSTEM", True, (100, 100, 200))
        self.screen.blit(version_text, (width - version_text.get_width() - 20, 
                                       height - 30))
    
    def draw_instructions(self):
        width, height = self.current_size
        self.screen.fill(BACKGROUND)
        
        # Draw header
        title = self.font_large.render("MISSION BRIEFING", True, (0, 255, 255))
        self.screen.blit(title, (width//2 - title.get_width()//2, 50))
        
        # Draw instructions
        font = self.font_small
        instructions = [
            "CONTROL CYB-01 THROUGH THE NEON NEXUS:",
            "",
            "CONTROLS:",
            "↑ ↓ ← →   - NAVIGATE THE SERPENT",
            "SPACE     - START/PAUSE/RESUME MISSION",
            "ESC       - RETURN TO COMMAND CENTER",
            "R         - RESTART CURRENT LEVEL",
            "F11       - TOGGLE FULLSCREEN",
            "M         - TOGGLE MUSIC ON/OFF",
            "",
            "GAME FLOW:",
            "• Click START MISSION to load the game",
            "• Press SPACE to actually start playing",
            "• Press SPACE again to pause/resume",
            "",
            "OBJECTIVES:",
            "• COLLECT ENERGY ORBS TO GROW AND GAIN POINTS",
            "• AVOID WALLS, OBSTACLES, AND SELF-COLLISION",
            "• COMPLETE ALL 5 LEVELS TO RESTORE THE GRID",
            "",
            "ORB TYPES:",
            "● YELLOW  - BASIC ORB (+10, GROWTH)",
            "⚡ BLUE    - POWER ORB (+25, SPEED BOOST)",
            "×2 PURPLE - MULTIPLIER ORB (+50, 2x SCORE)",
            "🛡 GREEN   - SHIELD ORB (+75, WALL IMMUNITY)",
            "★ RED     - BOSS ORB (+100, LEVEL PROGRESS)",
            "",
            "PRESS ESC TO RETURN"
        ]
        
        y_offset = 120
        for line in instructions:
            if '●' in line or '⚡' in line or '×2' in line or '🛡' in line or '★' in line:
                # Split line to color code parts
                parts = line.split(' - ')
                if len(parts) == 2:
                    # Draw symbol
                    symbol_font = pygame.font.SysFont('Arial', 20, bold=True)
                    symbol_text = symbol_font.render(parts[0], True, (255, 255, 255))
                    self.screen.blit(symbol_text, (width//2 - 200, y_offset))
                    
                    # Draw description
                    desc_text = font.render(parts[1], True, (200, 200, 255))
                    self.screen.blit(desc_text, (width//2 - 150, y_offset))
            else:
                text = font.render(line, True, TEXT_COLOR)
                self.screen.blit(text, (width//2 - text.get_width()//2, y_offset))
            y_offset += 25
    
    def draw_game_over(self, collision_type=None):
        width, height = self.current_size
        self.screen.fill(BACKGROUND)
        
        # Determine game over reason
        if collision_type == "wall":
            title = "GRID BOUNDARY BREACH"
            message = "CYB-01 collided with the digital perimeter"
            color = (255, 50, 50)
        elif collision_type == "obstacle":
            title = "OBSTACLE IMPACT"
            message = "System integrity compromised by barrier collision"
            color = (255, 100, 50)
        elif collision_type == "self":
            title = "SELF-CORRUPTION DETECTED"
            message = "Recursive loop caused system failure"
            color = (255, 0, 255)
        else:
            title = "MISSION COMPLETE" if self.level > 5 else "MISSION FAILED"
            message = "All levels cleared!" if self.level > 5 else "Return to command center"
            color = (50, 255, 50) if self.level > 5 else (255, 50, 50)
        
        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
        
        # Draw title
        title_text = self.font_large.render(title, True, color)
        self.screen.blit(title_text, (width//2 - title_text.get_width()//2, 100))
        
        # Draw message
        message_text = self.font_small.render(message, True, TEXT_COLOR)
        self.screen.blit(message_text, (width//2 - message_text.get_width()//2, 170))
        
        # Draw stats
        stats_font = self.font_medium
        stats = [
            f"FINAL SCORE: {self.score}",
            f"HIGH SCORE: {self.high_score}",
            f"LEVEL REACHED: {self.level}",
            f"SERPENT LENGTH: {self.serpent.length}",
            f"ORBS COLLECTED: {self.orbs_collected}",
            f"TOTAL TIME: {int(self.game_time)}s"
        ]
        
        y_offset = 220
        for stat in stats:
            stat_text = stats_font.render(stat, True, UI_COLOR)
            self.screen.blit(stat_text, (width//2 - stat_text.get_width()//2, y_offset))
            y_offset += 45
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
    
    def draw_level_transition(self):
        width, height = self.current_size
        self.screen.fill(BACKGROUND)
        
        # Calculate time since transition started
        transition_time = time.time() - self.level_transition_start_time
        
        # Calculate level bonus
        time_taken = self.level_transition_start_time - self.level_start_time
        time_bonus = max(0, 60 - int(time_taken)) * 2
        level_bonus = self.level * 100
        total_bonus = time_bonus + level_bonus
        
        # Add bonus to score (only once)
        if not self.can_proceed_to_next_level:
            self.score += total_bonus
            self.can_proceed_to_next_level = True
            
            # Play level complete sound
            if self.level < 5:
                self.sound_manager.play_sound('level_complete')
            else:
                self.sound_manager.play_sound('mission_complete')
        
        # Draw level complete message
        title = self.font_large.render(f"LEVEL {self.level} COMPLETE", True, (0, 255, 255))
        self.screen.blit(title, (width//2 - title.get_width()//2, 100))
        
        # Draw bonus breakdown
        font = self.font_medium
        bonuses = [
            f"LEVEL BONUS: {level_bonus}",
            f"TIME BONUS: {time_bonus}",
            f"TOTAL BONUS: {total_bonus}"
        ]
        
        y_offset = 180
        for bonus in bonuses:
            bonus_text = font.render(bonus, True, (255, 255, 0))
            self.screen.blit(bonus_text, (width//2 - bonus_text.get_width()//2, y_offset))
            y_offset += 40
        
        # Draw next level info
        next_level = self.level + 1
        if next_level <= 5:
            next_text = font.render(f"NEXT LEVEL: {next_level}", True, (255, 0, 255))
            self.screen.blit(next_text, (width//2 - next_text.get_width()//2, 320))
            
            config = self.level_configs[next_level]
            info_text = self.font_small.render(
                f"Speed: {config['speed']} | Obstacles: {config['obstacles']} | Target: {config['orbs_required']} orbs",
                True, TEXT_COLOR
            )
            self.screen.blit(info_text, (width//2 - info_text.get_width()//2, 360))
        
        # Draw continue prompt with blinking effect
        if int(transition_time * 2) % 2 == 0:  # Blink every 0.5 seconds
            prompt = self.font_small.render("PRESS SPACE TO CONTINUE", True, (0, 255, 100))
            self.screen.blit(prompt, (width//2 - prompt.get_width()//2, 450))
        
        # Only show ready message after 1 second
        if transition_time >= 1.0:
            ready_text = self.font_small.render("Ready!", True, (0, 255, 0))
            self.screen.blit(ready_text, (width//2 - ready_text.get_width()//2, 500))
    
    def draw_game(self):
        # Draw background
        self.screen.fill(BACKGROUND)
        
        # Draw grid
        self.draw_grid()
        
        # Update and draw obstacles
        current_time = time.time()
        for obstacle in self.obstacles:
            obstacle.update(current_time)
            obstacle.draw(self.screen)
        
        # Update and draw orbs
        for orb in self.orbs:
            orb.update()
            orb.draw(self.screen)
        
        # Update and draw particles
        self.update_particles()
        self.draw_particles()
        
        # Draw serpent
        self.serpent.draw(self.screen)
        
        # Draw HUD
        self.draw_hud()
        
        # Draw pause overlay if paused
        if self.state == GameState.PAUSED:
            overlay = pygame.Surface(self.current_size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            width, height = self.current_size
            pause_text = self.font_large.render("MISSION PAUSED", True, (255, 255, 0))
            self.screen.blit(pause_text, (width//2 - pause_text.get_width()//2, 
                                         height//2 - 50))
            
            continue_text = self.font_small.render("Press SPACE to resume | R to restart | ESC for menu", 
                                                  True, TEXT_COLOR)
            self.screen.blit(continue_text, (width//2 - continue_text.get_width()//2, 
                                           height//2 + 20))
    
    def draw_ready_to_play(self):
        """Draw the game in READY_TO_PLAY state"""
        # Draw the full game
        self.draw_game()
        
        # Draw the ready overlay
        self.draw_ready_overlay()
    
    def next_level(self):
        """Proceed to the next level"""
        if self.level < 5:
            self.level += 1
            self.orbs_collected = 0
            self.boss_orbs_collected = 0
            self.setup_level()
            self.state = GameState.READY_TO_PLAY  # Changed from PLAYING to READY_TO_PLAY
            self.can_proceed_to_next_level = False
            self.ready_start_time = time.time()
            # Don't start music yet - wait for space press
        else:
            # Game won
            self.state = GameState.GAME_OVER
            self.create_game_over_buttons()
            self.sound_manager.stop_background_music()
    
    def run(self):
        running = True
        fullscreen = False
        
        while running:
            current_time = time.time()
            mouse_pos = pygame.mouse.get_pos()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Handle window resize
                if event.type == pygame.VIDEORESIZE:
                    self.handle_resize(event.w, event.h)
                
                # Handle keyboard input
                if event.type == pygame.KEYDOWN:
                    # Handle READY_TO_PLAY state
                    if self.state == GameState.READY_TO_PLAY:
                        if event.key == pygame.K_SPACE:
                            # Start the game!
                            self.state = GameState.PLAYING
                            self.level_start_time = time.time()  # Start the timer
                            self.sound_manager.play_background_music()
                        elif event.key == pygame.K_ESCAPE:
                            # Return to main menu
                            self.state = GameState.MAIN_MENU
                            self.create_menu_buttons()
                            self.sound_manager.stop_background_music()
                        elif event.key == pygame.K_UP:
                            # Allow direction changes even in ready state
                            self.serpent.change_direction(Direction.UP)
                        elif event.key == pygame.K_DOWN:
                            self.serpent.change_direction(Direction.DOWN)
                        elif event.key == pygame.K_LEFT:
                            self.serpent.change_direction(Direction.LEFT)
                        elif event.key == pygame.K_RIGHT:
                            self.serpent.change_direction(Direction.RIGHT)
                        elif event.key == pygame.K_F11:
                            # Toggle fullscreen
                            fullscreen = not fullscreen
                            if fullscreen:
                                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                                info = pygame.display.Info()
                                self.handle_resize(info.current_w, info.current_h)
                            else:
                                self.screen = pygame.display.set_mode(self.original_size, pygame.RESIZABLE)
                                self.handle_resize(self.original_size[0], self.original_size[1])
                    
                    # Handle PLAYING state
                    elif self.state == GameState.PLAYING:
                        if event.key == pygame.K_UP:
                            self.serpent.change_direction(Direction.UP)
                        elif event.key == pygame.K_DOWN:
                            self.serpent.change_direction(Direction.DOWN)
                        elif event.key == pygame.K_LEFT:
                            self.serpent.change_direction(Direction.LEFT)
                        elif event.key == pygame.K_RIGHT:
                            self.serpent.change_direction(Direction.RIGHT)
                        elif event.key == pygame.K_SPACE:
                            self.state = GameState.PAUSED
                            self.sound_manager.stop_background_music()
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MAIN_MENU
                            self.create_menu_buttons()
                            self.sound_manager.stop_background_music()
                        elif event.key == pygame.K_F11:
                            # Toggle fullscreen
                            fullscreen = not fullscreen
                            if fullscreen:
                                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                                info = pygame.display.Info()
                                self.handle_resize(info.current_w, info.current_h)
                            else:
                                self.screen = pygame.display.set_mode(self.original_size, pygame.RESIZABLE)
                                self.handle_resize(self.original_size[0], self.original_size[1])
                        elif event.key == pygame.K_m:
                            # Toggle music
                            if self.sound_manager.music_playing:
                                self.sound_manager.stop_background_music()
                            else:
                                self.sound_manager.play_background_music()
                    
                    elif self.state == GameState.PAUSED:
                        if event.key == pygame.K_SPACE:
                            self.state = GameState.PLAYING
                            self.sound_manager.play_background_music()
                        elif event.key == pygame.K_r:
                            self.reset_game()
                            self.state = GameState.READY_TO_PLAY  # Changed to READY_TO_PLAY
                            self.ready_start_time = time.time()
                            self.sound_manager.stop_background_music()
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MAIN_MENU
                            self.create_menu_buttons()
                            self.sound_manager.stop_background_music()
                        elif event.key == pygame.K_F11:
                            # Toggle fullscreen from pause
                            fullscreen = not fullscreen
                            if fullscreen:
                                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                                info = pygame.display.Info()
                                self.handle_resize(info.current_w, info.current_h)
                            else:
                                self.screen = pygame.display.set_mode(self.original_size, pygame.RESIZABLE)
                                self.handle_resize(self.original_size[0], self.original_size[1])
                    
                    elif self.state == GameState.LEVEL_TRANSITION:
                        # Only proceed if enough time has passed and space is pressed
                        if (event.key == pygame.K_SPACE and self.can_proceed_to_next_level and 
                            current_time - self.level_transition_start_time >= 1.0):  # 1 second delay
                            self.next_level()
                    
                    elif self.state == GameState.INSTRUCTIONS:
                        if event.key == pygame.K_ESCAPE:
                            self.state = GameState.MAIN_MENU
                    
                    elif self.state == GameState.GAME_OVER:
                        if event.key == pygame.K_SPACE:
                            self.reset_game()
                            self.state = GameState.READY_TO_PLAY  # Changed to READY_TO_PLAY
                            self.ready_start_time = time.time()
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.MAIN_MENU
                            self.create_menu_buttons()
                
                # Handle mouse for buttons
                if self.state in [GameState.MAIN_MENU, GameState.GAME_OVER]:
                    for button in self.buttons:
                        button.check_hover(mouse_pos, self.sound_manager)
                        action = button.handle_event(event, self.sound_manager)
                        if action:
                            if action == "start":
                                # NEW: Go to READY_TO_PLAY instead of PLAYING
                                self.reset_game()
                                self.state = GameState.READY_TO_PLAY
                                self.ready_start_time = time.time()
                                # Don't start music yet - wait for space press
                            elif action == "instructions":
                                self.state = GameState.INSTRUCTIONS
                            elif action == "high_scores":
                                # In a full implementation, this would show high scores
                                # For now, just show a message
                                print("High scores feature coming soon!")
                            elif action == "quit":
                                running = False
                            elif action == "retry":
                                self.reset_game()
                                self.state = GameState.READY_TO_PLAY  # Changed to READY_TO_PLAY
                                self.ready_start_time = time.time()
                            elif action == "menu":
                                self.state = GameState.MAIN_MENU
                                self.create_menu_buttons()
            
            # Update game state
            if self.state == GameState.PLAYING:
                # Update game time
                self.game_time += 1 / FPS
                
                # Update serpent
                self.serpent.update(current_time)
                
                # Check collisions
                collision_result = self.handle_collisions()
                if collision_result:
                    if collision_result in ["wall", "obstacle", "self"]:
                        # Play collision sound
                        self.sound_manager.play_sound('collision')
                        self.sound_manager.stop_background_music()
                        
                        # Play game over sound after a short delay
                        pygame.time.delay(300)
                        self.sound_manager.play_sound('game_over')
                        
                        self.state = GameState.GAME_OVER
                        self.create_game_over_buttons()
                    elif collision_result == "level_complete":
                        # Stop background music for level transition
                        self.sound_manager.stop_background_music()
                        
                        # Set up level transition
                        self.level_transition_start_time = time.time()
                        self.can_proceed_to_next_level = False
                        self.state = GameState.LEVEL_TRANSITION
            
            # Update particles (always update for visual effect)
            self.update_particles()
            
            # Draw based on state
            if self.state == GameState.MAIN_MENU:
                self.draw_menu()
            elif self.state == GameState.INSTRUCTIONS:
                self.draw_instructions()
            elif self.state == GameState.READY_TO_PLAY:  # NEW state
                self.draw_ready_to_play()
            elif self.state == GameState.GAME_OVER:
                collision_type = None  # This would be set based on how game ended
                self.draw_game_over(collision_type)
            elif self.state == GameState.LEVEL_TRANSITION:
                self.draw_level_transition()
            else:  # PLAYING or PAUSED
                self.draw_game()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = CyberSerpentGame()
    game.run()