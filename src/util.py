# Created by Jens Kromdijk 29/03/2026
import pygame, os, json, sys, math
from pathlib import Path

BASE_IMG_PATH = "data/images/"
BASE_AUDIO_PATH = "data/audio/"
BASE_FONT_PATH = "data/fonts/"

def get_script_path():
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return str(Path(sys._MEIPASS)) + "/"
        bundle_dir = Path(sys.executable).resolve().parent
        if ".app/Contents/MacOS" in str(bundle_dir):
            return bundle_dir.parent / "Resources"
        return str(bundle_dir) + "/"
    return str(Path(sys.argv[0]).resolve().parent) + "/"

def load_font(path, size=8) -> pygame.Font:
    print(f"Loaded font from `{get_script_path() + BASE_FONT_PATH + path}`")
    return pygame.font.Font(get_script_path() + BASE_FONT_PATH + path, size)

def load_image(path) -> pygame.Surface:
    surf = pygame.image.load(get_script_path() + BASE_IMG_PATH + path).convert()
    surf.set_colorkey((0, 0, 0))
    print(f"Loaded image from `{get_script_path() + BASE_IMG_PATH + path}`")
    return surf

def load_images(path):
    imgs = []
    for img_path in os.listdir(get_script_path() + BASE_IMG_PATH + path):
        imgs.append(load_image(path + "/" + img_path))
    return imgs

def load_sound(path) -> pygame.mixer.Sound:
    print(f"Loaded sound from `{get_script_path() + BASE_AUDIO_PATH + path}`")
    sound = pygame.mixer.Sound(get_script_path() + BASE_AUDIO_PATH + path)
    sound.set_volume(0.4)
    return sound

def load_animation(path, xsize, y, length):
    sheet = load_image(path)
    animation = []
    for x in range(length):
        animation.append(snip(sheet, [x * xsize, 0], [xsize, y]))
    return animation

def load_animation_alpha(path, xsize, y, length):
    sheet = pygame.image.load(path).convert_alpha()
    sheet.set_colorkey((0, 0, 0))
    print(f"Loaded image from `{get_script_path() + BASE_IMG_PATH + path}`")
    animation = []
    for x in range(length):
        animation.append(snip(sheet, [x * xsize, 0], [xsize, y]))
    return animation

def load_tile_imgs(path, tile_size):
    img = load_image(path)
    img_surf = pygame.Surface((tile_size, tile_size))
    tiles = []
    dimensions = [int(img.get_width() / tile_size), int(img.get_height() / tile_size)]
    for y in range(dimensions[1]):
        for x in range(dimensions[0]):
            img_surf.fill((0, 0, 0))
            img_surf.blit(img, (-x * tile_size, -y * tile_size))
            img_surf.convert()
            img_surf.set_colorkey((0, 0, 0))
            tiles.append(img_surf.copy())
    print(f'Extracted tile images from `{get_script_path() + BASE_IMG_PATH + path}`')
    return tiles

def snip(spritesheet, pos, dimensions):
    clip_rect = pygame.Rect(pos, dimensions)
    image = spritesheet.subsurface(clip_rect)
    return image

def load_imgs(path, dimensions, tile_dimensions):
    tile_set = load_image(path)
    images = []
    for y_pos in range(dimensions[1]):
        for x_pos in range(dimensions[0]):
            images.append(snip(tile_set, (x_pos * tile_dimensions[0], y_pos * tile_dimensions[1]), tile_dimensions))
    return images

def read_json(path):
    f = open(get_script_path() + path, "r")
    data = json.load(f)
    f.close()
    print(f'Read json from `{get_script_path() + BASE_IMG_PATH + path}`')
    return data

def write_json(path, data):
    f = open(get_script_path() + path, "w")
    json.dump(data, f)
    f.close()
    print(f'Wrote json to `{get_script_path() + BASE_IMG_PATH + path}`')

def load_palette(img: pygame.Surface):
    img_array = pygame.pixelarray.PixelArray(img)
    palette = []
    for row in img_array:
        for color in row:
            c = img.unmap_rgb(color)
            if c != (0, 0, 0, 0) and c != (0, 0, 0, 255):
                palette.append(tuple(c))
    return palette

def get_circumcenter(a: pygame.Vector2, b: pygame.Vector2, c: pygame.Vector2):
    d = 2 * (a.x * (b.y - c.y) + b.x * (c.y - a.y) + c.x * (a.y - b.y))    
    u = pygame.Vector2(0, 0)
    u.x = ((a.x * a.x + a.y * a.y) * (b.y - c.y) + (b.x * b.x + b.y * b.y) * (c.y - a.y) + (c.x * c.x + c.y * c.y) * (a.y - b.y)) / d
    u.y = ((a.x * a.x + a.y * a.y) * (c.x - b.x) + (b.x * b.x + b.y * b.y) * (a.x - c.x) + (c.x * c.x + c.y * c.y) * (b.x - a.x)) / d
    return u

def draw_arc(surf, color, pos, radius, start_angle, end_angle, bulge, subdivisions=10, width=0):
    pos = pygame.Vector2(pos)
    if end_angle < start_angle:
        end_angle += 2 * math.pi
    mid_angle = (start_angle + end_angle) * 0.5
    start_pos = pygame.Vector2(pos.x + math.cos(start_angle) * radius, pos.y + math.sin(start_angle) * radius)
    end_pos = pygame.Vector2(pos.x + math.cos(end_angle) * radius, pos.y + math.sin(end_angle) * radius)
    
    bulge_pos = pygame.Vector2(pos.x + math.cos(mid_angle) * (radius + bulge), pos.y + math.sin(mid_angle) * (radius + bulge))

    cc = get_circumcenter(start_pos, end_pos, bulge_pos)
    cc_radius = cc.distance_to(bulge_pos)

    cc_start_angle = math.atan2(start_pos.y - cc.y, start_pos.x - cc.x)
    cc_end_angle = math.atan2(end_pos.y - cc.y, end_pos.x - cc.x)

    if cc_end_angle < cc_start_angle:
        cc_end_angle += 2 * math.pi
    
    cc_mid_angle = math.atan2(bulge_pos.y - cc.y, bulge_pos.x - cc.x)
    if cc_mid_angle < cc_start_angle:
        cc_mid_angle += 2 * math.pi
    
    if not (cc_start_angle <= cc_mid_angle <= cc_end_angle):
        cc_start_angle, cc_end_angle = cc_end_angle, cc_start_angle + 2 * math.pi

    # generate the points
    points = []
    num_points = subdivisions // 2
    for i in range(num_points + 1):
        points.append(pygame.Vector2(
            pos.x + radius * math.cos(start_angle + i / num_points * (end_angle - start_angle)),
            pos.y + radius * math.sin(start_angle + i / num_points * (end_angle - start_angle))
        ))
    for i in range(num_points + 1):
        points.append(pygame.Vector2(
            cc.x + cc_radius * math.cos(cc_end_angle - i / num_points * (cc_end_angle - cc_start_angle)),
            cc.y + cc_radius * math.sin(cc_end_angle - i / num_points * (cc_end_angle - cc_start_angle))
        ))
    
    pygame.draw.polygon(surf, color, points, width)