import os
import io
from PIL import Image, UnidentifiedImageError
import pygame
from pygame.locals import KEYDOWN, K_BACKSPACE

def average_color(image_path):
    img = Image.open(image_path)
    img = img.convert('RGB')
    data = img.getdata()
    r, g, b = 0, 0, 0
    num_pixels = len(data)
    for pixel in data:
        r += pixel[0]
        g += pixel[1]
        b += pixel[2]
    return (r // num_pixels, g // num_pixels, b // num_pixels)

def round_corners(surface, radius, border_thickness, border_color):
    new_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(new_surface, (255, 255, 255), new_surface.get_rect(), border_radius=radius)
    new_surface.blit(surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    pygame.draw.rect(new_surface, border_color, new_surface.get_rect(), border_radius=radius, width=border_thickness)
    return new_surface

def add_drop_shadow(surface, offset, shadow_color, radius):
    shadow = pygame.Surface((surface.get_width() + offset, surface.get_height() + offset), pygame.SRCALPHA)
    pygame.draw.rect(shadow, shadow_color, (offset, offset, surface.get_width(), surface.get_height()), border_radius=radius)
    return shadow

fullscreen = False

image_path = r"C:\Users\saget\Desktop\Shellhacks2023\Lo-FAI\output.png"

pygame.init()

# Load a font
font = pygame.font.SysFont('Arial', 36, bold=True)
with open('prompt.txt', 'r') as file:
    text = file.read()
text_color = (255, 255, 255)

# Render the "Now Playing:" text
now_playing_surface = font.render("Now Playing:", True, text_color)

image = pygame.image.load(image_path)
image_width, image_height = image.get_size()

# Calculate the desired window dimensions based on the image size and the 16:9 ratio
desired_width = image_width
desired_height = int(desired_width * 9 / 16)

if fullscreen:
    screen = pygame.display.set_mode((desired_width, desired_height), pygame.FULLSCREEN)
else:
    screen = pygame.display.set_mode((desired_width, desired_height))

# If the desired height is less than the image height, adjust the width and height to maintain the 16:9 ratio
if desired_height <= image_height:
    desired_height = int(image_height * 1.2)  # Increase the height by 20% to ensure a strip of background is visible above and below the image
    desired_width = int(desired_height * 16 / 9)

screen = pygame.display.set_mode((desired_width, desired_height))
pygame.display.set_caption("Display Image with Border, Rounded Corners, and Drop Shadow")

last_mod_time = os.path.getmtime(image_path)
avg_color = average_color(image_path)

radius = 20
border_thickness = 2
border_color = (0, 0, 0)
image = round_corners(image, radius, border_thickness, border_color)

shadow_offset = 10
shadow_color = (0, 0, 0, 100)
shadow = add_drop_shadow(image, shadow_offset, shadow_color, radius)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Add this to toggle fullscreen with the F key
        elif event.type == KEYDOWN:
            if event.key == pygame.K_f:
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((desired_width, desired_height), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((desired_width, desired_height))

    current_mod_time = os.path.getmtime(image_path)

    if current_mod_time != last_mod_time:
        try:
            new_image = pygame.image.load(image_path)
            new_image = round_corners(new_image, radius, border_thickness, border_color)
            shadow = add_drop_shadow(new_image, shadow_offset, shadow_color, radius)
            image = new_image
            last_mod_time = current_mod_time
            avg_color = average_color(image_path)
        except FileNotFoundError:
            pass

    # Fill the entire screen with the average color
    screen.fill(avg_color)

    # Calculate the position to move the image to the left in the window
    x_offset = (desired_width - image_width) // 10  # Adjust this value to move the image further to the left or right
    y_offset = (desired_height - image_height) // 2

    # Draw the shadow and then the image
    screen.blit(shadow, (x_offset, y_offset))
    screen.blit(image, (x_offset, y_offset))

    # Define a spacing variable to increase the separation between the two texts
    spacing = 5

    # Read the text from prompt.txt
    with open('prompt.txt', 'r') as file:
        text = file.read()

    # Render the text from prompt.txt
    text_surface = font.render(text, True, text_color)

    # Calculate the position for the "Now Playing:" text and the text from prompt.txt
    text_x = x_offset + (spacing * 10) + image_width + (desired_width - (x_offset + image_width) - max(text_surface.get_width(), now_playing_surface.get_width())) // 2
    now_playing_y = (desired_height - text_surface.get_height() - now_playing_surface.get_height() - spacing) // 2
    text_y = now_playing_y + now_playing_surface.get_height() + (spacing*10)

    # Draw the "Now Playing:" text and the text from prompt.txt
    screen.blit(now_playing_surface, (text_x, now_playing_y))
    screen.blit(text_surface, (text_x, text_y))


    pygame.display.flip()

pygame.quit()