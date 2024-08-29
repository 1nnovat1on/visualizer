import pygame
import numpy as np
import pygame.mixer as mixer
from pygame.locals import QUIT
import time
import wave
import struct

# Initialize Pygame and mixer
pygame.init()
mixer.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
# Light Brown
LIGHT_BROWN = (181, 101, 29)

# Emerald Green
EMERALD_GREEN = (80, 200, 120)

BACKGROUND_COLOR = (0, 0, 0)
CENTER_RECT_COLOR = (0, 0, 0)  # Color for the rectangle behind the center image
TRIANGLE_COLOR = (255, 0, 0)
# Cyan (Light Blue)
CYAN = (0, 255, 255)
CIRCLE_COLOR = CYAN
SQUARE_COLOR = EMERALD_GREEN
POINT_COLOR = (255, 255, 255)
FPS = 60
DESPAWN_TIME = 2  # Time in seconds after which shapes will despawn
LOUDNESS_THRESHOLD = 0.015  # Minimum loudness for spawning shapes
DIVISOR = 2500000000  # Divisor to control the number of shapes
MIN_SPEED = 2  # Minimum speed to ensure the speed is never zero

# Image Scaling Factor
IMAGE_SCALE = 0.3  # Adjust this to resize the image

# Initialize screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Audio Reactive Shapes')

# Load circular PNG image
center_image = pygame.image.load('center_image.png')
center_image = pygame.transform.scale(center_image, 
                                      (int(center_image.get_width() * IMAGE_SCALE), 
                                       int(center_image.get_height() * IMAGE_SCALE)))
center_image_rect = center_image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

# Load MP3 file and extract audio data
mixer.music.load('song.wav')

# Function to analyze the audio file in real-time
def analyze_audio():
    current_time = mixer.music.get_pos() / 1000
    try:
        with wave.open('song.wav', 'r') as wf:
            sample_rate = wf.getframerate()
            chunk_size = 1024
            position = int(current_time * sample_rate)
            wf.setpos(position)
            audio_data = wf.readframes(chunk_size)
    except:
        return None

    data_format = f"{len(audio_data) // wf.getsampwidth()}h"
    audio_chunk = np.array(struct.unpack(data_format, audio_data))

    frequency_array = np.fft.rfft(audio_chunk)
    frequencies = np.abs(frequency_array)

    return frequencies

# Helper function to spawn shapes
def spawn_shape(shape_type, color, pos, direction, speed):
    if shape_type == 'triangle':
        pygame.draw.polygon(screen, color, [
            (pos[0], pos[1] - 10),
            (pos[0] - 10, pos[1] + 10),
            (pos[0] + 10, pos[1] + 10)
        ])
    elif shape_type == 'circle':
        pygame.draw.circle(screen, color, pos, 10)
    elif shape_type == 'square':
        pygame.draw.rect(screen, color, (*pos, 20, 20))
    pos[0] += direction[0] * speed
    pos[1] += direction[1] * speed
    return pos

# Helper function to spawn twinkling points
def spawn_twinkling_points(loudness):
    num_points = int(loudness * .3)
    for _ in range(num_points):
        x, y = np.random.randint(0, SCREEN_WIDTH), np.random.randint(0, SCREEN_HEIGHT)
        pygame.draw.circle(screen, POINT_COLOR, (x, y), 2)

# Main loop
def main():
    clock = pygame.time.Clock()
    shapes = []

    # Start the music playback
    mixer.music.play(loops=0)
    music_playing = True

    while True:
        screen.fill(BACKGROUND_COLOR)

        frequencies = analyze_audio() if music_playing else np.zeros(1024)
        if frequencies is None:
            frequencies = np.zeros(1024)  # Continue with silence when audio ends
            music_playing = False

        loudness = np.max(frequencies) / 32768.0  # Normalize loudness

        if loudness > LOUDNESS_THRESHOLD:
            low_range = frequencies[:len(frequencies)//3]
            mid_range = frequencies[len(frequencies)//3:2*len(frequencies)//3]
            high_range = frequencies[2*len(frequencies)//3:]

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    return

            num_triangles = max(1, int(np.mean(low_range) * len(low_range) * loudness / DIVISOR))
            num_circles = max(1, int(np.mean(mid_range) * len(mid_range) * loudness / DIVISOR))
            num_squares = max(1, int(np.mean(high_range) * len(high_range) * loudness / DIVISOR))

            current_time = pygame.time.get_ticks() / 1000

            triangle_speed = max(MIN_SPEED, int(10 * (1 - np.mean(low_range) / np.max(low_range))))
            circle_speed = max(MIN_SPEED, int(10 * (1 - np.mean(mid_range) / np.max(mid_range))))
            square_speed = max(MIN_SPEED, int(10 * (1 - np.mean(high_range) / np.max(high_range))))

            for _ in range(num_triangles):
                direction = (np.random.choice([-1, 1]) * np.random.random(), np.random.choice([-1, 1]) * np.random.random())
                shapes.append(('triangle', TRIANGLE_COLOR, [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2], direction, triangle_speed, current_time))

            for _ in range(num_circles):
                direction = (np.random.choice([-1, 1]) * np.random.random(), np.random.choice([-1, 1]) * np.random.random())
                shapes.append(('circle', CIRCLE_COLOR, [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2], direction, circle_speed, current_time))

            for _ in range(num_squares):
                direction = (np.random.choice([-1, 1]) * np.random.random(), np.random.choice([-1, 1]) * np.random.random())
                shapes.append(('square', SQUARE_COLOR, [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2], direction, square_speed, current_time))

        # Update and draw shapes
        for shape in shapes[:]:
            pos = spawn_shape(shape[0], shape[1], shape[2], shape[3], shape[4])
            shape_type, color, pos, direction, speed, spawn_time = shape
            if pos[0] < 0 or pos[0] > SCREEN_WIDTH or pos[1] < 0 or pos[1] > SCREEN_HEIGHT or (pygame.time.get_ticks() / 1000) - spawn_time > DESPAWN_TIME:
                shapes.remove(shape)

        # Spawn twinkling points
        spawn_twinkling_points(loudness)

        # Draw a black circle behind the center image to ensure full coverage
        pygame.draw.circle(screen, CENTER_RECT_COLOR, center_image_rect.center, center_image_rect.width // 5)

        # Draw the circular PNG image on top
        screen.blit(center_image, center_image_rect)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
