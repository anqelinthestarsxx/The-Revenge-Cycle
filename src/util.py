# Created by Jens Kromdijk 29/03/2026
import pygame, os, json, sys
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