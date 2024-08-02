from distutils import debug
import cv2
import numpy as np
import math
from rembg import remove
from scipy.ndimage import binary_fill_holes
from openai import OpenAI, OpenAIError
from PIL import Image, ImageOps, ImageEnhance, ImageDraw, ImageFilter, ImageColor
import requests
import random
import os



def remove_bg_unicolor(input_img, color='w'):
    image = input_img.copy()
    if (color == 'w'):
        white = np.all(image[:, :, :3] >= [240, 240, 240], axis=2)
        image[white, :] = 0
        return image
    if (color == 'b'):
        white = np.all(image[:, :, :3] <= [15, 15, 15], axis=2)
        image[white, :] = 0
        return image
    else:
        return remove_bg_anycolor(image)

def remove_bg_anycolor(input_img):
    image = remove(input_img).copy()
    return image

def scale_image(image, bg_shape, bg_partition_shape, scale):
    image_shape = image.size[::-1]
    x_scale = bg_shape[1] / image_shape[1]
    y_scale = bg_shape[0] / image_shape[0]
    scale_up = scale * (y_scale if x_scale > y_scale else x_scale)
    x_size = scale_up * image_shape[1]
    y_size = scale_up * image_shape[0]
    if (x_size > bg_partition_shape[1]):
        partition_shrink = bg_partition_shape[1] / x_size
        x_size *= partition_shrink * scale
        y_size *= partition_shrink * scale
    new_dims = (int(x_size), int(y_size))
    return cv2.cvtColor(np.array(image.resize(new_dims)), cv2.COLOR_RGB2RGBA)

def mask_bg(image, bg_color='any'):
    if bg_color == 'any':
        scaled_product_rgba_nb = remove_bg_anycolor(image)
    elif bg_color == 'none':
        scaled_product_rgba_nb = image
    else:
        scaled_product_rgba_nb = remove_bg_unicolor(image, color=bg_color) 
    # creating mask and applying to product
    mask = np.asarray(scaled_product_rgba_nb[:, :, 3] != 0)
    mask = np.repeat(binary_fill_holes(mask[:,:])[:,:,np.newaxis], 4, axis=2).astype(np.uint8)
    image *= mask
    return image, mask

def overlay_product_image_on_bg(product_img, bg_img, frame=None, scale=1, bg_color='any'):
    """
    - frame: A tuple (top, left, right, bottom) defining the area to fit the text in.
    """
    bg_img = bg_img.resize((2199, 1419))
    bg_shape = bg_img.size[::-1]
    if (frame != None):
        frame_height = min(abs(frame[3] - frame[0]), bg_shape[0])
        frame_width = min(abs(frame[2] - frame[1]), bg_shape[1])
        bg_shape = (frame_height, frame_width)
    num_products = len(product_img)
    bg_img_rgba = cv2.cvtColor(np.array(bg_img), cv2.COLOR_RGB2RGBA)
    bg_partition_shape = (bg_shape[0], (bg_shape[1] / num_products))
    
    
    for idx, product in enumerate(product_img):
        product_shape = product.size[::-1]
        
        # scaling product image relative to bg size
        scaled_product_rgba = scale_image(product, bg_shape, bg_partition_shape, np.min([1, scale]))
        scaled_product_shape = np.shape(scaled_product_rgba)
        
        # removing product background
        scaled_product_rgba, mask = mask_bg(scaled_product_rgba, bg_color=bg_color)
        # masking bg image in evenly spaced position
        center_y = math.floor((bg_shape[0] - scaled_product_shape[0]) / 2)
        center_x = math.floor(idx * bg_partition_shape[1] + (bg_partition_shape[1] - scaled_product_shape[1]) / 2)
        if (frame):
            center_y += frame[0]
            center_x += frame[1]
        bg_img_rgba[center_y + int((bg_partition_shape[0] - scaled_product_shape[0]) / 2):scaled_product_shape[0] + center_y + int((bg_partition_shape[0] - scaled_product_shape[0]) / 2), center_x:scaled_product_shape[1] + center_x] *= 1 - mask
        bg_img_rgba[center_y + int((bg_partition_shape[0] - scaled_product_shape[0]) / 2):scaled_product_shape[0] + center_y + int((bg_partition_shape[0] - scaled_product_shape[0]) / 2), center_x:scaled_product_shape[1] + center_x] += scaled_product_rgba
        
    # overlaying product image
    return Image.fromarray(bg_img_rgba)

def generate_bg(occasion, bg_prompt="", model="dall-e-2"):
    if (bg_prompt == ""):
        bg_prompt = "Generate an image that represents a background for a product promotion. The image should be composed of two main elements: a ground and a background. The ground should feature a table with a matte neutral color, positioned about a quarter from the bottom of the image. This table will serve as the base for multiple products which will be added later. Do not include a product. The background should depict a blurred scene that corresponds to the target consumer or purpose or occasion of the promotion, which is" + str(occasion) + ". The scene should be designed in such a way that even a viewer without any context can understand the occasion or purpose. To ensure consistency across all images, use a 50mm lens. Set the aperture to f/1.8 to achieve a shallow depth of field, which will help blur the background. The ISO should be set to 100 for optimal image quality, and the shutter speed can be adjusted based on the lighting conditions.Remember, the goal is to create a consistent series of images where the only variable element is the occasion or purpose of the promotion, represented in the background scene."

    client = OpenAI()
    response = client.images.generate(
        model=model,
        prompt=bg_prompt,
        size="1792x1024",
        quality="standard",
        n=1,
    )
    
    image_url = response.data[0].url
    return Image.open(requests.get(image_url, stream=True).raw)

def draw_title_text(image, text, font, area, color='white'):
    """
    Draws centered text on an image with the font size scaled to fit within a specified area.

    Parameters:
    - img_path: Path to the image file.
    - text: Text string to be written.
    - font_path: Path to the .ttf font file.
    - area: A tuple (top, left, right, bottom) defining the area to fit the text in.
    - max_font_size: Maximum possible starting font size.

    Returns: Image with text centered in given box
    """
    
    draw = ImageDraw.Draw(image)
    
    # TODO: ADD PRESET POSITIONS FOR HEADER, DISCOUNT, SKU, ETC
    area_width = abs(min(area[2] - area[1], image.size[0]))
    area_height = abs(min(area[3] - area[0], image.size[1]))
    font = font.font_variant(size=area_height)
    
    # Scale Font Size to Area
    text_width = draw.textlength(text, font=font)
    text_height = area_height

    if (text_width > area_width):
        text_height = math.floor(text_height * (area_width / text_width))
        font = font.font_variant(size=text_height)
        text_width = draw.textlength(text, font=font)

    # Center Position
    x = area[1] + (area_width - text_width) // 2
    y = area[0] + (area_height - text_height) // 2
    
    draw.text((x, y), text, font=font, fill=color)

def add_box(image, area, color='gray', outline='gray', rounded=False, isOutline=False):
    """
    - area: A tuple (top, left, right, bottom) defining the area to fit the text in.
    """
    if (not isOutline):
        outline = color
    draw = ImageDraw.Draw(image)
    rect_width = area[2] - area[1]
    rect_height = area[3] - area[0]
    if (rounded):
        corner_radius = min(rect_width, rect_height)
        draw.rounded_rectangle(area, fill=color, outline=outline, radius=corner_radius, width=10)
    else:
        draw.rectangle(area, fill=color, outline=outline, width=10)

def add_discount_sticker(image, discount, font, position, diameter):
    draw = ImageDraw.Draw(image)
    circle_color = 'white'
    draw.ellipse([position[0], position[1], position[0] + diameter, position[1] + diameter], outline=circle_color, fill=circle_color)
    area = (position[1] + diameter * 0.1, position[0], position[0] + diameter, position[1] + diameter * 0.65)
    draw_title_text(image, f"{discount}%", font, area, color='black')
    draw_title_text(image, "DISCOUNT", font, (position[1] + 275, position[0] + 76, position[0] + 345, position[1] + 337), color='black')

def add_SKU_label(image, SKUs, font, product_image_area):
    top, left, right, bottom = product_image_area
    n = len(SKUs)
    if (n <= 1):
        draw_title_text(image, SKUs[0], font, (bottom, left, right, bottom + 70), color='black')
        return

    width = right - left
    partition_width = width / n
    partitions = []
    for i in range(n):
        partition_left = left + i * partition_width
        partition_right = partition_left + partition_width
        draw_title_text(image, SKUs[i], font, (bottom, partition_left, partition_right, bottom + 70), color='black')
        if (i == 0 or i == n - 2):
            draw_title_text(image, "+", font, (bottom, partition_left, partition_right + partition_width, bottom + 70), color='black')

def create_reflection(original_image, footer_height=250, reflection_opacity=0.4):    
    original_image = original_image.filter(ImageFilter.GaussianBlur(radius=4))
    reflected_image = ImageOps.flip(original_image)
    reflected_image = reflected_image.crop((0, 0, original_image.width, footer_height))
    gradient = Image.new('L', (original_image.width, footer_height), color=0xFF)
    for y in range(footer_height):
        transparency = int((255 * reflection_opacity) * (1 - y / footer_height))
        for x in range(original_image.width):
            gradient.putpixel((x, y), transparency)
    reflected_image = reflected_image.convert("RGBA")
    white_bg = Image.new('RGBA', reflected_image.size, (255, 255, 255, 255))
    blended_reflection = Image.composite(reflected_image, white_bg, gradient)
    total_height = original_image.height + footer_height
    footer_image = Image.new('RGBA', (original_image.width, total_height), (255, 255, 255, 255))
    footer_image.paste(original_image, (0, 0))
    footer_image.paste(blended_reflection, (0, original_image.height), blended_reflection)
    footer_image = footer_image.filter(ImageFilter.BLUR)    
    return footer_image

def add_quantity_stickers(image, product_frame, quantities, font, color="gray", outline="darkgrey", text_color="black"):
    draw = ImageDraw.Draw(image)
    num_products = len(quantities)
    diameter = 200
    top, left, right, bottom = product_frame
    width = right - left
    height = bottom - top
    partition_width = width / num_products
    partitions = []
    for i in range(num_products):
        partition_left = left + i * partition_width
        partition_right = partition_left + partition_width
        if (num_products == 1):
            part_left, part_top, part_right, part_bottom = (partition_left + 400, product_frame[0] + height * 0.65 - 100, partition_left + 600, product_frame[0] + height * 0.65 + 100)
        else:
            part_left, part_top, part_right, part_bottom = (partition_left + 125, product_frame[0] + height * 0.65 - 100, partition_left + 325, product_frame[0] + height * 0.65 + 100)
        draw.ellipse((part_left, part_top, part_right, part_bottom), outline=outline, fill=color, width=6)
        draw_title_text(image, str(quantities[i]) + "x", font, (part_top, part_left + 15, part_right - 15, part_bottom - 50), color=text_color)

def generate_product_card(product_image, occasion, frame=None, scale=1, bg_color='any'):
    try:
        bg = generate_bg(occasion)
        return overlay_product_image_on_bg(product_image, bg, frame, scale, bg_color=bg_color)
    except OpenAIError as e:
        print(e.http_status)
        print(e.error)

def generate_product_card_with_bg(product_image, bg_image, frame=None, scale=1, bg_color='any'):
    return overlay_product_image_on_bg(product_image, bg_image, frame, scale, bg_color=bg_color)

def generate_card_basic(SKUs, dev_set, bundle_ID, quantities, max_quantity, font, discount, theme_color='white', text_color='black', bg_color='any'):

    bg_image = Image.open("./BGs/" + dev_set + "_BG.png")
    product_frame = (350, 100, 1900, 1300)

    product_images = []
    for SKU in SKUs:
        SKU = SKU.replace("/", "-") if "/" in SKU else SKU
        product_images.append(Image.open("SKUs/" + SKU + ".png"))
    
    # Add BG Reflection
    bg_image = create_reflection(bg_image)
    
    # Overlay Products
    product_on_bg = generate_product_card_with_bg(product_images, bg_image, frame=product_frame, bg_color=bg_color)
    # Output Dims will be 2199 x 1419

    # Add Header
    add_box(product_on_bg, (0, 0, product_on_bg.size[0], 230), color=theme_color)
    theme_rgb = ImageColor.getrgb(theme_color)
    theme_color_dark = tuple(int(c * 0.8) for c in theme_rgb)
    add_box(product_on_bg, (-100, 26, 880, 213), color=theme_color_dark, rounded=True)
    draw_title_text(product_on_bg, bundle_ID, font, (40, 46, 745, 165), color=text_color)
    add_box(product_on_bg, (1700, 60, 2000, 170), color=theme_color, outline=text_color, isOutline=True, rounded=False)
    draw_title_text(product_on_bg, "Max: " + str(max_quantity), font, (60, 1700, 2000, 150), color=text_color)
    
    
    # Add Footer
    add_SKU_label(product_on_bg, SKUs, font, product_frame)

    # Add Discount Sticker
    add_discount_sticker(product_on_bg, discount, font, (1700, 200), 400)

    # Add Quantities
    add_quantity_stickers(product_on_bg, product_frame, quantities, font, color=theme_color, outline=theme_color_dark, text_color=text_color)

    return product_on_bg
