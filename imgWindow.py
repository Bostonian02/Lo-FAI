import pygame
import os
from PIL import Image, UnidentifiedImageError

#shoutout to chatGPT for this code lmao

def average_color(image_path):
    # Open the image
    img = Image.open(image_path)
    
    # Convert the image to RGB (if it's not already in that mode)
    img = img.convert('RGB')
    
    # Get the image data
    data = img.getdata()
    
    # Compute the average color
    r, g, b = 0, 0, 0
    num_pixels = len(data)
    for pixel in data:
        r += pixel[0]
        g += pixel[1]
        b += pixel[2]
    
    avg_r = (r // num_pixels)
    avg_g = (g // num_pixels)
    avg_b = (b // num_pixels)
    
    return (avg_r, avg_g, avg_b)

def round_corners(surface, radius, border_thickness, border_color):
    """Rounds the corners of a given surface."""
    new_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(new_surface, (255, 255, 255), new_surface.get_rect(), border_radius=radius)
    new_surface.blit(surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    
    # Draw a black outline
    pygame.draw.rect(new_surface, border_color, new_surface.get_rect(), border_radius=radius, width=border_thickness)
    
    return new_surface

def add_drop_shadow(surface, offset, shadow_color, radius):
    """Adds a drop shadow to a given surface."""
    shadow = pygame.Surface((surface.get_width() + offset * 2, surface.get_height() + offset * 2), pygame.SRCALPHA)
    pygame.draw.rect(shadow, shadow_color, shadow.get_rect(), border_radius=radius)
    return shadow

image_path = r"C:\Users\saget\Desktop\Shellhacks2023\Lo-FAI\output.png"

pygame.init()

image = pygame.image.load(image_path)
image_width, image_height = image.get_size()

# Calculate the desired window dimensions based on a 16:9 ratio
desired_width = image_width
desired_height = int(desired_width * 9 / 16)

# Adjust if the desired height is less than the image height
if desired_height < image_height:
    desired_height = image_height
    desired_width = int(desired_height * 16 / 9)

screen = pygame.display.set_mode((desired_width, desired_height))
pygame.display.set_caption("Display Image with Border, Rounded Corners, and Drop Shadow")

last_mod_time = os.path.getmtime(image_path)

avg_color = average_color(image_path)
#print(f"Complement of the average color: {avg_color}") testing

# Round the corners of the image and add a thinner black outline
radius = 20
border_thickness = 2  # Thinner border
border_color = (0, 0, 0)
image = round_corners(image, radius, border_thickness, border_color)

# Add a drop shadow to the image
shadow_offset = 10  # Adjust this value to change the size of the shadow
shadow_color = (0, 0, 0, 100)  # Semi-transparent black for the shadow
shadow = add_drop_shadow(image, shadow_offset, shadow_color, radius)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_mod_time = os.path.getmtime(image_path)

    if current_mod_time != last_mod_time:
        try:
            new_image = pygame.image.load(image_path)
            new_image = round_corners(new_image, radius, border_thickness, border_color)
            shadow = add_drop_shadow(new_image, shadow_offset, shadow_color, radius)
            image = new_image
            last_mod_time = current_mod_time
            avg_color = average_color(image_path)
            #print(f"Complement of the average color: {avg_color}") #testing
        except FileNotFoundError:
            pass

    # Fill the window with the complementary average color
    screen.fill(avg_color)
    
    # Draw the shadow and then the image centered in the window
    x_offset = (desired_width - image_width) // 2
    y_offset = (desired_height - image_height) // 2
    screen.blit(shadow, (x_offset - shadow_offset, y_offset - shadow_offset))
    screen.blit(image, (x_offset, y_offset))
    
    pygame.display.flip()

pygame.quit()