import pygame, sys, time, moderngl, array, random
import pygame.geometry

from src.bip import *
from src.util import *
from src.tiles import *
from src.player import Player
from src.enemies import Enemy
from src.particles import *
from src.anim import Anim

import pygame.gfxdraw

pygame.init()
pygame.mixer.init()
pygame.font.init()

SERIES_1 = [["data/maps/0.json", "Outside 'The Vista'"], ["data/maps/1.json", "The Vista"], ["data/maps/2.json", "Bart's Kitchen"]]
SERIES_2 = [["data/maps/3.json", "Outside 'Sérénité'"], ["data/maps/4.json", "Sérénité"], ["data/maps/5.json", "Elsa's Kitchen"]]

class App:
    def __init__(self):
        self.time = 0
        print(f"Running from {get_script_path()}")
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 4)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 1)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)

        self.display = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF)
        self.screen = pygame.Surface((WIDTH // SCALE, HEIGHT // SCALE))
        self.tileSurf = pygame.Surface(self.screen.get_size())
        self.ls_scale = 1
        self.level_surf_pos = pygame.Vector2(0, 0)
        self.level_surf = pygame.Surface((TILE_SIZE * CHUNK_SIZE * LEVEL_WIDTH, TILE_SIZE * CHUNK_SIZE * LEVEL_HEIGHT))
        self.ui_surf = self.level_surf.copy()
        self.ui_render_surf = self.screen.copy()

        self.fade = 0
        self.fade_dir = 0

        self.ctx: moderngl.Context = None
        self.prog: moderngl.Program = None
        self.vbo = None
        self.vao = None
        self.setup_gl()
        self.setup_framebuffer()

        self.clock = pygame.time.Clock()

        self.dt = 1
        self.last_time = time.time() - 1/60

        self.assets = {
            'tiles/grass': load_tile_imgs('tiles/grass.png', 16),
            'tiles/kitchen': load_tile_imgs('tiles/kitchen.png', 16),
            'tiles/wood': load_tile_imgs('tiles/wood.png', 16),
            "tiles/kitchen_decor": [load_image("appliances/dishwasher.png"), load_image("appliances/fridgey.png"), load_image("appliances/little-oven.png"), load_image("appliances/mini-fryer.png")],
            "particle/leaf": load_animation("particles/leaf.png", 8, 8, 17),
            "tiles/table": [load_image("tiles/table.png")],
            "tiles/table2": load_animation("tiles/table2.png", 32, 32, 6),
            "tiles/tree": load_animation("tiles/tree.png", 32, 32, 2),
            "grass": load_animation("grass.png", 17, 17, 10),
            'player': {
                "black": {
                    "idle": load_animation("player/black/idle.png", 15, 31, 4),
                    "run": load_animation("player/black/walk.png", 15, 31, 4),
                    "jump": load_animation("player/black/jump.png", 15, 31, 2),
                    "land": load_animation("player/black/land.png", 16, 31, 3),
                    "punch": load_animation("player/black/punch.png", 32, 32, 7)
                },
                "white": {
                    "idle": load_animation("player/white/idle.png", 15, 31, 4),
                    "run": load_animation("player/white/walk.png", 15, 31, 4),
                    "jump": load_animation("player/white/jump.png", 15, 31, 2),
                    "land": load_animation("player/white/land.png", 16, 31, 3),
                    "punch": load_animation("player/white/attack.png", 32, 32, 7)
                },
                "knife": load_image("player/knife.png"),
                "shotgun": load_image("player/shotgun.png"),
                "bullet": load_image("player/bullet.png"),
                "pepper": load_image("player/pepper.png")
            },
            "npc": {
                "kitchen": {
                    "1": {
                        "idle": load_animation("npcs/kitchen/1/idle.png", 16, 31, 4),
                        "run": load_animation("npcs/kitchen/1/walk.png", 16, 31, 4),
                        "jump": load_animation("npcs/kitchen/1/jump.png", 16, 31, 2),
                        "land": load_animation("npcs/kitchen/1/land.png", 16, 31, 3),
                        "punch": load_animation("npcs/kitchen/1/attack.png", 32, 32, 7)
                    },
                    "2": {
                        "idle": load_animation("npcs/kitchen/2/idle.png", 16, 31, 4),
                        "run": load_animation("npcs/kitchen/2/walk.png", 16, 31, 4),
                        "jump": load_animation("npcs/kitchen/2/jump.png", 16, 31, 2),
                        "land": load_animation("npcs/kitchen/2/land.png", 16, 31, 3),
                        "punch": load_animation("npcs/kitchen/2/attack.png", 32, 32, 7)
                    },
                    "3": {
                        "idle": load_animation("npcs/kitchen/3/idle.png", 15, 31, 4),
                        "run": load_animation("npcs/kitchen/3/walk.png", 15, 31, 4),
                        "jump": load_animation("npcs/kitchen/3/jump.png", 16, 31, 2),
                        "land": load_animation("npcs/kitchen/3/land.png", 16, 31, 3),
                        "punch": load_animation("npcs/kitchen/3/attack.png", 32, 32, 7)
                    }
                }
            },
            "placeholder": load_image("placeholder.png"),
            "firefly": load_animation("firefly.png", 5, 5, 20),
            "particle/explosion": load_animation("particles/explosion.png", 5, 5, 15),
            "particle/particle": load_animation("particles/particle.png", 5, 5, 4),
            "clouds": load_imgs("clouds.png", (1, 2), (64, 32)),
            "background": load_image("background.png"),
            "logo": load_image("logo.png"),
            "noise": load_image("noise.png"),
            "kitchen_bg": load_image("backgrounds/kitchen-bg.png"),
            "restaurant_bg": load_image("woodgrain.png"),
            "restaurant_bg2": load_image("backgrounds/restaurant-bg-no-plants.png"),
            "rewind": load_image("rewind.png")
        }

        self.noiseTex = self.ctx.texture(self.assets["noise"].get_size(), 4)
        self.noiseTex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.noiseTex.swizzle = "BGRA"
        self.noiseTex.repeat_x = True
        self.noiseTex.repeat_y = True
        self.noiseTex.write(self.assets["noise"].get_view('1'))

        self.bold_font = load_font("dogicapixelbold.ttf", size=8)
        self.font = load_font("dogicapixel.ttf", size=8)
        self.difficulty = -0.5

        self.tile_map = TileMap(self)
        self.tile_map.load("data/maps/0.json")

        # extract enemies
        self.enemies = []
        for loc in self.tile_map.tile_map.copy():
            if self.tile_map.tile_map[loc]["type"] == "enemy":
                tile = self.tile_map.tile_map[loc]
                self.enemies.append(Enemy(self, [15, 31], [self.tile_map.tile_map[loc]["pos"][0] * TILE_SIZE, self.tile_map.tile_map[loc]["pos"][1] * TILE_SIZE], num=len(self.enemies)))
                del self.tile_map.tile_map[loc]

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0

        self.player = Player(self, [9, 31], self.tile_map.player_pos, "black")

        self.particles = []
        self.wind = ([0, 10], [0, 15], [0, 5])
        self.kickup = []
        self.kickup_surf = pygame.Surface((1, 1))
        self.sparks = []
        self.smoke = []
        self.fireflies = []
        self.slime = []
        self.splat = []
        for _ in range(10):
            # [pos, dir, angle]
            self.fireflies.append([[random.random() * 10000, random.random() * 10000], random.random() * math.pi * 2, random.random() * 10 + 10, random.random() * 4 * random.choice([-1, 1]), random.random() * 50])
        self.cinders = PhysicsParticles(self, trail=True, bounce=0.3, explode=True, friction=0.7)

        self.clouds = []
        for _ in range(6):
            self.clouds.append([random.random() * 10000, random.random() * 10000, random.choice([0, 1]), random.random() * 0.5 + 0.25])
        self.clouds.sort(key=lambda x: -x[3])

        self.leaf_spawners = []
        for tree in self.tile_map.extract([("tree", 0), ("tree", 1)], keep=True):
            self.leaf_spawners.append((pygame.Rect(tree['pos'][0] + 5, tree['pos'][1] + 5, 21, 13), True))

        self.slomo = 1.0

        self.level_complete = False
        self.series = 0
        self.level = 0

        self.state = "menu"

        self.text = [[
            "Food is a very serious business...", 
            "The young chef Elsa Turner has a promising career ahead of her, were it not for the raucious visitors attending the grimy tavern - 'The Vista' near her restaurant, the Sérénité.",
            "Elsa has politely requested the owner, Bart Freeman, many times to cut down the noise around his tavern, as the ordinary folk repulse the wealthy patrons of her fine dining establishment.",
            "However, that cantankerous old fool has stubbornly refused to hear Elsa's pleas, laughing in her face! The impertinence!","Drastic times call for drastic measures, so Elsa has decided to take matters into her own hands..."
        ], [
            "Bart is not very happy...",
            "Elsa brutally slaughtered his guests and hard-working staff last night - this is personal now!",
            "Consumed by a primal rage, Bart is going to pay the Sérénité a quick well-meaned visit..."
        ], [
            "Elsa is ruined...",
            "All of her loyal customers and talented workers have been cruelly murdered by that savage - BART!",
            "Yet she will not be deterred! It seems that imbecile has not learned his lesson yet...",
            "Bart had better watch out; Elsa will not abandon her new-born vendetta and will not stop until one of them is six feet undergound!"
        ], [
            "Oh how the tables have turned! The rough wood of Bart's bar and furniture has now been soiled with the blood and internals of those who sat there!",
            "However, Bart is still out there - and Elsa must pay for her crimes.",
            "In her hubris, the Sérénité may once again end up becoming soaked with the sticky, stale blood of her clients clinging to the floor and walls..."
        ], [
            "This is war..."
        ], [
            "This is madness..."
        ], [
            "This is SPARTA!!! BWAHAHAHAHA!"
        ], [
            "That evil murdering hag is insane. Bart must end this quick!"
        ], [
            "That little kretin has escaped again!",
            "In the meantime, best slay some more upstanding citizens..."
        ]]
        self.texts_idx = 0
        self.text_idx = 0
        self.text_timer = 0

        self.wheel_angle = math.radians(math.floor(random.random() * 1000 / 90) * 90)
        self.wheel_vel = 0
        self.wheel_scale = 1
        self.wheel_scale_vel = 0
        self.spin_alpha = 1
        self.wheel_text = ""

        self.attack_anim = Anim(self.assets["player"][self.player.color]["punch"].copy(), 0.2, True)
        for i, img in enumerate(self.attack_anim.animation):
            surf = pygame.Surface((img.get_width() + 2, img.get_height() + 2))
            mask = pygame.mask.from_surface(img)
            msurf = mask.to_surface(setcolor=(219, 224, 231), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                surf.blit(msurf, (1 + offset[0], 1 + offset[1]))
            surf.blit(img, (1, 1))
            surf.set_colorkey((0, 0, 0))
            self.attack_anim.animation[i] = surf.copy()
        
        rot_surf = pygame.transform.rotate(self.assets["player"]["shotgun"], -90)
        self.shotgun_item = pygame.Surface((rot_surf.get_width() + 2, rot_surf.get_height() + 2))
        mask = pygame.mask.from_surface(rot_surf)
        msurf = mask.to_surface(setcolor=(247, 172, 55), unsetcolor=(0, 0, 0, 0))
        for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            self.shotgun_item.blit(msurf, (1 + offset[0], 1 + offset[1]))
        self.shotgun_item.blit(rot_surf, (1, 1))
        self.shotgun_item.set_colorkey((0, 0, 0))

        self.weapon = "shotgun"

        self.strikes = 3
        self.rs_hover = False

        self.cycles = 0
        self.max_cycles = 0

    
    def death(self):
        level_size = (self.level_surf.get_width() * self.ls_scale, self.level_surf.get_height() * self.ls_scale)
        self.level_surf_pos = pygame.Vector2(
            self.screen.get_width() * 0.5 - level_size[0] * 0.5,
            self.screen.get_height() * 0.5 - level_size[1] * 0.5,
        )
        self.ui_render_surf.fill((0, 0, 0))
        self.ui_surf.fill((0, 0, 0))

        font_surf = self.bold_font.render(f"{"Elsa" if self.player.color == "black" else "Bart"} {self.player.death_message}", False, (53, 20, 40))
        self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, self.ui_surf.get_height() * 0.4 * 50))
        font_surf = self.bold_font.render(f"{"Elsa" if self.player.color == "black" else "Bart"} {self.player.death_message}", False, (219, 224, 231))
        self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, self.ui_surf.get_height() * 0.4 - 1))

        font_surf = self.bold_font.render(f"High Score: {self.max_cycles} Cycles", False, (219, 224, 231))
        self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, 8))
        font_surf = self.font.render(f"Survived: {self.max_cycles} Cycles", False, (219, 224, 231))
        self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, 8 + TILE_SIZE))

        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        mouse_pos /= SCALE
        mouse_pos -= self.level_surf_pos
        mouse_pos /= self.ls_scale
        rs = pygame.transform.scale2x(self.assets["rewind"])
        self.rs_hover = pygame.Rect(self.ui_surf.get_width() * 0.5 - rs.get_width() * 0.5, self.ui_surf.get_height() * 0.6 - rs.get_height() * 0.5, rs.get_width(), rs.get_height()).collidepoint(mouse_pos)
        if self.rs_hover:
            rs.set_alpha(200)
        self.ui_surf.blit(rs, (self.ui_surf.get_width() * 0.5 - rs.get_width() * 0.5, self.ui_surf.get_height() * 0.6 - rs.get_height() * 0.5 - int(self.rs_hover)))

        font_surf = self.bold_font.render(f"Rewinds left: {max(self.strikes, 0)}", False, (219, 224, 231))
        self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, self.ui_surf.get_height() * 0.5 - 1))

        # if self.time * 0.02 % 2 < 1.54:
        if self.strikes < 1:
            font_surf = self.bold_font.render("Press [ENTER] to play again!", False, (219, 224, 231))
            self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, self.ui_surf.get_height() - TILE_SIZE))
        else:
            font_surf = self.bold_font.render("Press [ENTER] to rewind!", False, (219, 224, 231))
            self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, self.ui_surf.get_height() - TILE_SIZE))
    
        self.fade = pygame.math.clamp(self.fade + self.fade_dir * self.dt * 0.03, 0, 1)
        if self.fade_dir == 1 and self.fade == 1:
            if self.strikes >= 0:
                temp_strikes = self.strikes
                self.level -= 1
                self.next_level()
                self.strikes = temp_strikes
                self.state = "game"
                self.fade_dir = -1
            else:
                self.fade_dir = -1
                self.level = -1
                self.series = 0
                self.next_level()
                self.difficulty = -0.5
                self.state = "menu"
                self.text_idx = 0
                self.texts_idx = 0
            self.cycles = 0
        
        if self.fade == 0 and self.fade_dir == -1:
            self.fade_dir = 0

        pygame.draw.rect(self.ui_surf, (20, 16, 32), (0, 0, self.ui_surf.get_width(), self.ui_surf.get_height() * 1.6 * self.fade))

        self.ui_render_surf.blit(pygame.transform.scale(self.ui_surf, level_size), self.level_surf_pos)
        self.uiTex.write(self.ui_render_surf.get_view('1'))
        self.prog["scrollX"].value = 0
        self.prog["scrollY"].value = 0
        self.prog["scrWidth"].value = self.screen.get_width()
        self.prog["scrHeight"].value = self.screen.get_height()
        self.prog["levelX"].value = self.level_surf_pos.x
        self.prog["levelY"].value = self.level_surf_pos.y
        self.prog["levelW"].value = level_size[0]
        self.prog["levelH"].value = level_size[1]
        self.prog["levelScale"].value = self.ls_scale
    
    def menu(self):
        level_size = (self.level_surf.get_width() * self.ls_scale, self.level_surf.get_height() * self.ls_scale)
        self.level_surf_pos = pygame.Vector2(
            self.screen.get_width() * 0.5 - level_size[0] * 0.5,
            self.screen.get_height() * 0.5 - level_size[1] * 0.5,
        )
        self.ui_render_surf.fill((0, 0, 0))
        self.ui_surf.fill((0, 0, 0))

        self.ui_surf.blit(self.assets["logo"], (self.ui_surf.get_width() * 0.5 - self.assets["logo"].get_width() * 0.5, self.ui_surf.get_height() * 0.5 - self.assets["logo"].get_height() * 0.5 + math.sin(time.time() * 1) * 5 - TILE_SIZE + max(0, 30 - self.time) * 50))

        if self.time * 0.02 % 2 < 1.54:
            font_surf = self.bold_font.render("Press [ENTER] to begin!", False, (219, 224, 231))
            self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, self.ui_surf.get_height() * 0.6+ max(0,  30 - self.time) * 50))
    
        self.fade = pygame.math.clamp(self.fade + self.fade_dir * self.dt * 0.014, 0, 1)
        if self.fade_dir == 1 and self.fade == 1:
            self.state = "talk"
            self.fade_dir = -1
        
        if self.fade == 0 and self.fade_dir == -1:
            self.fade_dir = 0

        pygame.draw.rect(self.ui_surf, (20, 16, 32), (0, 0, self.ui_surf.get_width(), self.ui_surf.get_height() * 1.6 * self.fade))

        self.ui_render_surf.blit(pygame.transform.scale(self.ui_surf, level_size), self.level_surf_pos)
        self.uiTex.write(self.ui_render_surf.get_view('1'))
        self.prog["scrollX"].value = 0
        self.prog["scrollY"].value = 0
        self.prog["scrWidth"].value = self.screen.get_width()
        self.prog["scrHeight"].value = self.screen.get_height()
        self.prog["levelX"].value = self.level_surf_pos.x
        self.prog["levelY"].value = self.level_surf_pos.y
        self.prog["levelW"].value = level_size[0]
        self.prog["levelH"].value = level_size[1]
        self.prog["levelScale"].value = self.ls_scale

    def talk(self):
        level_size = (self.level_surf.get_width() * self.ls_scale, self.level_surf.get_height() * self.ls_scale)
        self.level_surf_pos = pygame.Vector2(
            self.screen.get_width() * 0.5 - level_size[0] * 0.5,
            self.screen.get_height() * 0.5 - level_size[1] * 0.5,
        )
        self.ui_render_surf.fill((0, 0, 0))
        self.ui_surf.fill((0, 0, 0))

        pygame.draw.rect(self.ui_surf, (20, 16, 32), (TILE_SIZE, TILE_SIZE, self.ui_surf.get_width() - TILE_SIZE * 2, self.ui_surf.get_height() - TILE_SIZE * 2))
        pygame.draw.rect(self.ui_surf, (219, 224, 231), (TILE_SIZE, TILE_SIZE, self.ui_surf.get_width() - TILE_SIZE * 2, self.ui_surf.get_height() - TILE_SIZE * 2), width=1)

        self.fade = pygame.math.clamp(self.fade + self.fade_dir * self.dt * 0.014, 0, 1)
        if self.fade_dir == 1 and self.fade == 1:
            self.state = "spin"
            self.wheel_angle = math.radians(math.floor(random.random() * 1000 / 90) * 90)
            self.wheel_vel = 0
            self.wheel_scale = 1
            self.wheel_scale_vel = 0
            self.spin_alpha = 1
            self.wheel_text = ""
            self.fade_dir = -1
        
        if self.fade == 0 and self.fade_dir == -1:
            self.fade_dir = 0

        padding = 4

        if self.texts_idx == len(self.text):
            pygame.draw.rect(self.ui_surf, (20, 16, 32), (0, 0, self.ui_surf.get_width(), self.ui_surf.get_height() * 1.6 * self.fade))

            self.ui_render_surf.blit(pygame.transform.scale(self.ui_surf, level_size), self.level_surf_pos)
            self.uiTex.write(self.ui_render_surf.get_view('1'))

            self.prog["scrollX"].value = 0
            self.prog["scrollY"].value = 0
            self.prog["scrWidth"].value = self.screen.get_width()
            self.prog["scrHeight"].value = self.screen.get_height()
            self.prog["levelX"].value = self.level_surf_pos.x
            self.prog["levelY"].value = self.level_surf_pos.y
            self.prog["levelW"].value = level_size[0]
            self.prog["levelH"].value = level_size[1]
            self.prog["levelScale"].value = self.ls_scale

            self.state = "spin"
            return

        if self.time * 0.02 % 2 < 1.54:
            font_surf = self.bold_font.render("Press [ENTER] to continue", False, (219, 224, 231))
            self.ui_surf.blit(font_surf, (TILE_SIZE + padding + 1, self.ui_surf.get_height() - font_surf.get_height() - padding - 1 - TILE_SIZE))
        
        self.text_timer += self.dt
        offset = 0
        delay = 30
        for m in range(self.text_idx + 1):
            full_text = self.text[self.texts_idx][m]
            render_text = [""]
            idx = 0 
            type_speed = 0.8
            tempt = self.text_timer
            if m != self.text_idx:
                self.text_timer = len(full_text) / type_speed + delay
            
            for i in range(min(int(max(0, self.text_timer - delay) * type_speed), len(full_text))):
                if full_text[i] == " ":
                    temp = render_text[idx]
                    break_text = False
                    for j in range(len(full_text) - i - 1):
                        if full_text[i + j + 1] == " ":
                            break_text = False
                            break
                        else:
                            temp += full_text[i + j]
                        if self.font.size(temp)[0] >= self.ui_surf.get_width() - 2 * TILE_SIZE - 2 - padding * 3:
                            break_text = True
                            break
                    if break_text:
                        render_text.append("")
                        idx += 1
                render_text[idx] += full_text[i]
            
            for k, line in enumerate(render_text):
                text_surf = self.font.render(line, False, (219, 224, 231))
                self.ui_surf.blit(text_surf, (TILE_SIZE + padding + 1, TILE_SIZE + padding + 1 + 12 * k + offset))
                offset
            self.text_timer = tempt

            if m == self.text_idx:
                if (self.text_timer - delay) * type_speed > len(full_text):
                    pygame.draw.rect(self.ui_surf, (219, 224, 231), (1 + padding + TILE_SIZE + text_surf.get_width() + 2, TILE_SIZE + padding + 1 + 12 * idx + offset, 5, 8))
                else:
                    if time.time() * 0.2 % type_speed * 2 < type_speed:
                        pygame.draw.rect(self.ui_surf, (219, 224, 231), (1 + padding + TILE_SIZE + text_surf.get_width() + 2, TILE_SIZE + padding + 1 + 12 * idx + offset, 5, 8))

            offset += 16 * len(render_text)
        
        # self.text_timer += self.dt
        # temp = self.text_timer
        # for i in range(self.text_idx):
        #     full_text = self.text[i][self.text_idx]
        #     render_text = [""]
        #     idx = 0
        #     type_speed = 0.8
        #     if i != self.text_idx:

        #     for i in range(min(int(max(0, self.text_timer - 100) * type_speed), len(full_text))):
        #         if full_text[i] == " ":
        #             temp = render_text[idx]
        #             break_text = False
        #             for j in range(len(full_text) - i - 1):
        #                 if full_text[i + j + 1] == " ":
        #                     break_text = False
        #                     break
        #                 else:
        #                     temp += full_text[i + j]
        #                 if self.font.size(temp)[0] >= self.ui_surf.get_width() - 2 * TILE_SIZE - 2 - padding * 3:
        #                     break_text = True
        #                     break
        #             if break_text:
        #                 render_text.append("")
        #                 idx += 1
        #         render_text[idx] += full_text[i]
            
        #     for i, line in enumerate(render_text):
        #         text_surf = self.font.render(line, False, (219, 224, 231))
        #         self.ui_surf.blit(text_surf, (TILE_SIZE + padding + 1, TILE_SIZE + padding + 1 + 12 * i))
        
        pygame.draw.rect(self.ui_surf, (20, 16, 32), (0, 0, self.ui_surf.get_width(), self.ui_surf.get_height() * 1.6 * self.fade))

        self.ui_render_surf.blit(pygame.transform.scale(self.ui_surf, level_size), self.level_surf_pos)
        self.uiTex.write(self.ui_render_surf.get_view('1'))

        self.prog["scrollX"].value = 0
        self.prog["scrollY"].value = 0
        self.prog["scrWidth"].value = self.screen.get_width()
        self.prog["scrHeight"].value = self.screen.get_height()
        self.prog["levelX"].value = self.level_surf_pos.x
        self.prog["levelY"].value = self.level_surf_pos.y
        self.prog["levelW"].value = level_size[0]
        self.prog["levelH"].value = level_size[1]
        self.prog["levelScale"].value = self.ls_scale
    
    def wheel_spin(self):
        level_size = (self.level_surf.get_width() * self.ls_scale, self.level_surf.get_height() * self.ls_scale)
        self.level_surf_pos = pygame.Vector2(
            self.screen.get_width() * 0.5 - level_size[0] * 0.5,
            self.screen.get_height() * 0.5 - level_size[1] * 0.5,
        )
        self.ui_render_surf.fill((0, 0, 0))
        self.ui_surf.fill((0, 0, 0))

        font_surf = self.bold_font.render("Choose your weapon!".upper(), False, (219, 224, 231))
        self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, 8))
        font_surf = self.bold_font.render("Press [ENTER] to spin!", False, (219, 224, 231))
        if self.spin_alpha < 1:
            self.spin_alpha = max(0, self.spin_alpha - 0.167 * self.dt)
        font_surf.set_alpha(255 * self.spin_alpha)
        self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, self.ui_surf.get_height() - 16))

        self.fade = pygame.math.clamp(self.fade + self.fade_dir * self.dt * 0.014, 0, 1)
        if self.fade_dir == 1 and self.fade == 1:
            self.state = "game"
            self.fade_dir = -1
        
        if self.fade == 0 and self.fade_dir == -1:
            self.fade_dir = 0

        self.wheel_angle += self.wheel_vel * self.dt
        self.wheel_vel *= 0.98 ** self.dt
        segments = 10
        self.wheel_scale_vel += (1.0 - self.wheel_scale) * 0.5 * self.dt
        self.wheel_scale += self.wheel_scale_vel * self.dt
        self.wheel_scale_vel *= 0.7 ** self.dt
        radius = min(self.ui_surf.get_height(), self.ui_surf.get_width()) * 0.4 * self.wheel_scale / (self.wheel_vel * 0.1 + 1)
        colors =  [(120, 31, 44), (237, 82, 89), (247, 172, 55), (180, 94, 179)]
        center = [self.ui_surf.get_width() * 0.5, self.ui_surf.get_height() * 0.5]
        shadow_length = 4
        for i in range(4):
            points = []
            points.append([center[0], center[1] + shadow_length])
            start_angle = self.wheel_angle + math.pi * 0.5 * i
            for j in range(segments + 1):
                angle = start_angle + j/segments * math.pi * 0.5
                points.append([center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius + shadow_length])
            pygame.draw.polygon(self.ui_surf, pygame.Color(colors[i][0], colors[i][1], colors[i][2]).lerp((20, 16, 32), 0.7), points)
        for i in range(4):
            points = []
            points.append(center)
            start_angle = self.wheel_angle + math.pi * 0.5 * i
            for j in range(segments + 1):
                angle = start_angle + j/segments * math.pi * 0.5
                points.append([center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius])
            pygame.draw.polygon(self.ui_surf, colors[i], points)
            
            surf = pygame.Surface((40, 40), pygame.SRCALPHA).convert_alpha()
            surf.fill((0, 0, 0, 0))
            pygame.draw.rect(surf, (38, 36, 58), (0, 0, surf.get_width(), surf.get_height()), border_radius=10)
            surf.set_alpha(255 / (self.wheel_vel * 5 + 1) * 0.5)
            self.ui_surf.blit(surf, (center[0] + math.cos(start_angle + math.pi * 0.25) * radius * 0.65 - surf.get_width() * 0.5,
                                    center[1] + math.sin(start_angle + math.pi * 0.25) * radius * 0.65 - surf.get_height() * 0.5 + shadow_length))
            pygame.draw.rect(surf, (219, 224, 231), (0, 0, surf.get_width(), surf.get_height()), border_radius=10, width=2)
            font_surf = self.bold_font.render("Boning Knife", False, (219, 224, 231))
            if i == 0:
                font_surf = self.bold_font.render("Chilli Bomb", False, (219, 224, 231))
                surf.blit(pygame.transform.scale(self.assets["player"]["pepper"], (14, 26)), (surf.get_width() * 0.5 - 7, surf.get_height() * .5 - 13))
                if random.random() / self.dt + self.wheel_vel < 0.1:
                    self.smoke.append([list((center[0] + math.cos(start_angle + math.pi * 0.25) * radius * 0.65 - surf.get_width() * 0.5 + 20,
                                    center[1] + math.sin(start_angle + math.pi * 0.25) * radius * 0.65 - surf.get_height() * 0.5 + 20)),[random.random() - 0.5, -random.random() - 0.5], 1, random.randint(200, 255), 0, random.randint(0, 360), random.choice([(237, 82, 89), (196, 44, 54), (120, 31, 44)])])
            elif i == 1:
                font_surf = self.bold_font.render("Bare Hands", False, (219, 224, 231))
                self.attack_anim.update(self.dt)
                self.attack_anim.draw(surf, (0, 0), (surf.get_width() * 0.5 - 17, surf.get_height() * 0.5 - 17))
            elif i == 2:
                font_surf = self.bold_font.render("Shotgun", False, (219, 224, 231))
                surf.blit(self.shotgun_item, (surf.get_width() * 0.5 - 24, surf.get_height() * 0.5 - self.shotgun_item.get_height() * 0.5 + math.cos(self.time * 0.1) * 2))
            elif i == 3:
                img = self.assets["player"]["knife"]
                img_copy = pygame.transform.rotate(pygame.transform.scale2x(img), -45)
                surf.blit(img_copy, (-5, 1 + math.sin(self.time * 0.1) * 2))

            font_surf.set_alpha(255 * self.spin_alpha)
            self.ui_surf.blit(font_surf, (center[0] - font_surf.get_width() * 0.5 + math.cos(start_angle + math.pi * 0.25) * radius * 1.25, center[1] + math.sin(start_angle + math.pi * 0.25) * radius * 1.25 - font_surf.get_height() * 0.5))
            surf.set_alpha(255 / (self.wheel_vel * 5 + 1))
            self.ui_surf.blit(surf, (center[0] + math.cos(start_angle + math.pi * 0.25) * radius * 0.65 - surf.get_width() * 0.5,
                                    center[1] + math.sin(start_angle + math.pi * 0.25) * radius * 0.65 - surf.get_height() * 0.5))
        

        pygame.draw.circle(self.ui_surf, (20, 16, 32), center, 10 * self.wheel_scale / (self.wheel_vel + 1) + math.sin(time.time() * 5))

        # radius = min(self.ui_surf.get_height(), self.ui_surf.get_width()) * 0.4
        pygame.gfxdraw.filled_trigon(self.ui_surf, int(center[0] + radius - 5), int(center[1]), int(center[0] + radius + 5), int(center[1] - 5), int(center[0] + radius + 5), int(center[1] + 5), (38, 36, 58))
        pygame.gfxdraw.trigon(self.ui_surf, int(center[0] + radius - 5), int(center[1]), int(center[0] + radius + 5), int(center[1] - 5), int(center[0] + radius + 5), int(center[1] + 5), (219, 224, 231))

        if self.wheel_vel < 0.001 and self.spin_alpha < 1:
            self.wheel_vel = 0
            idx = 0
            min_dist = 12232
            for i in range(4):
                angle = self.wheel_angle + math.pi * 0.5 * i + math.pi * 0.25
                dist = (center[0] + math.cos(angle) * radius - (center[0] + radius)) ** 2 + (center[1] + math.sin(angle) * radius - center[1])
                if dist < min_dist:
                    min_dist = dist
                    idx = i
                
            text = ["Chilli Bomb", "Bare Hands", "Shotgun", "Boning Knife"][idx]
            if self.wheel_text == "":
                self.wheel_text = [random.choice(["blow stuff up!", "paint it red!"]), random.choice(["kick some ass!", "mess up those scurvy dogs!"]), random.choice(["hunt down some civilians!", "shoot some upstanding citizens!"]), random.choice(["gut them like a fish!", "spill their intestines!"])][idx]

                self.player.mode = ["pepper", "fists", "shotgun", "sword"][idx]
                self.weapon = self.player.mode
            # mask = font_surf.
            font_surf = self.bold_font.render(f"Press [ENTER] to go {self.wheel_text}", False, (20, 16, 32))
            self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, self.ui_surf.get_height() - 16))
            font_surf = self.bold_font.render(f"Press [ENTER] to go {self.wheel_text}", False, colors[idx])
            self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, self.ui_surf.get_height() - 16 - 1))
            font_surf = self.bold_font.render(text, False, (20, 16, 32))
            self.ui_surf.blit(font_surf, (center[0] + radius * 1.25, center[1] - font_surf.get_height() * 0.5))
            font_surf = self.bold_font.render(text, False, (219, 224, 231))
            self.ui_surf.blit(font_surf, (center[0] + radius * 1.25, center[1] - font_surf.get_height() * 0.5 - 1))

        self.ui_surf.fblits([self.calc_smoke(smoke, [0, 0]) for smoke in self.smoke.copy()])

        pygame.draw.rect(self.ui_surf, (20, 16, 32), (0, 0, self.ui_surf.get_width(), self.ui_surf.get_height() * 1.6 * self.fade))

        self.ui_render_surf.blit(pygame.transform.scale(self.ui_surf, level_size), self.level_surf_pos)
        self.uiTex.write(self.ui_render_surf.get_view('1'))

        self.prog["scrollX"].value = 0
        self.prog["scrollY"].value = 0
        self.prog["scrWidth"].value = self.screen.get_width()
        self.prog["scrHeight"].value = self.screen.get_height()
        self.prog["levelX"].value = self.level_surf_pos.x
        self.prog["levelY"].value = self.level_surf_pos.y
        self.prog["levelW"].value = level_size[0]
        self.prog["levelH"].value = level_size[1]
        self.prog["levelScale"].value = self.ls_scale
    
    def next_level(self):
        self.strikes = 3
        orig_series = self.series
        self.level += 1
        series = SERIES_1 if self.series == 0 else SERIES_2
        if self.level > 2:
            self.series = (self.series + 1) % 2
            self.level = 0
            self.difficulty += 0.25
        series = SERIES_1 if self.series == 0 else SERIES_2
        if self.series != orig_series:
            self.cycles += 1
            self.state = "talk"
            self.texts_idx += 1
            self.fade_dir = -1
            self.text_idx = 0
        self.tile_map.load(series[self.level][0])
        self.leaf_spawners = []
        for tree in self.tile_map.extract([("tree", 0), ("tree", 1)], keep=True):
            self.leaf_spawners.append((pygame.Rect(tree['pos'][0] + 5, tree['pos'][1] + 5, 21, 13), True))

        # extract enemies
        self.enemies = []
        for loc in self.tile_map.tile_map.copy():
            if self.tile_map.tile_map[loc]["type"] == "enemy":
                tile = self.tile_map.tile_map[loc]
                self.enemies.append(Enemy(self, [15, 31], [self.tile_map.tile_map[loc]["pos"][0] * TILE_SIZE, self.tile_map.tile_map[loc]["pos"][1] * TILE_SIZE], num=len(self.enemies)))
                del self.tile_map.tile_map[loc]

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0

        self.player = Player(self, [9, 31], self.tile_map.player_pos, "black" if self.series < 1 else "white")
        self.player.mode = self.weapon

        self.particles = []
        self.wind = ([0, 10], [0, 15], [0, 5])
        self.kickup = []
        self.kickup_surf = pygame.Surface((1, 1))
        self.sparks = []
        self.smoke = []
        self.fireflies = []
        self.slime = []
        self.splat = []
        for _ in range(10):
            # [pos, dir, angle]
            self.fireflies.append([[random.random() * 10000, random.random() * 10000], random.random() * math.pi * 2, random.random() * 10 + 10, random.random() * 4 * random.choice([-1, 1]), random.random() * 50])
        self.cinders = PhysicsParticles(self, trail=True, bounce=0.3, explode=True, friction=0.7)

        self.clouds = []
        for _ in range(6):
            self.clouds.append([random.random() * 10000, random.random() * 10000, random.choice([0, 1]), random.random() * 0.5 + 0.25])
        self.clouds.sort(key=lambda x: -x[3])

        self.slomo = 1.0

        self.level_complete = False

   
    def update_fireflies(self, scroll):
        for fly in self.fireflies:
            fly[0][0] += math.cos(fly[1]) * fly[2] * self.dt * 0.05
            fly[0][1] += math.sin(fly[1]) * fly[2] * self.dt * 0.05
            fly[1] += fly[3] * self.dt * 0.003
            if random.random() * 4 < self.dt:
                fly[3] = random.random() * 2 * random.choice([-1, 1])
                fly[2] = random.random() * 5 + 5
            loc = (((fly[0][0] - scroll[0]) % self.level_surf.get_width()), ((fly[0][1] - scroll[1]) % self.level_surf.get_height()))
            fly[4] = (fly[4] + 0.1 * self.dt) % len(self.assets["firefly"])
            surf = self.assets["firefly"][math.floor(fly[4])]
            surf.set_alpha(100)
            self.level_surf.blit(surf, loc)
    
    def update_kickup(self, render_scroll):
        # p: [pos, vel, size, color]
        decay = 0.01
        bounce = 0.7
        friction = 0.98
        gravity = 0.125

        for i, p in sorted(enumerate(self.kickup), reverse=True):
            p[2] -= decay * self.dt
            if p[2] <= 0:
                self.kickup.pop(i)
            else: 
                self.kickup_surf.fill(p[3])
                self.kickup_surf.set_alpha(int(p[2] * 255))
                self.level_surf.blit(self.kickup_surf, (int(p[0][0] - render_scroll[0]), int(p[0][1] - render_scroll[1])))
            p[0][0] += p[1][0] * self.dt
            if self.tile_map.solid_check(p[0]):
                p[0][0] -= p[1][0] * self.dt
                p[1][0] *= -bounce
                p[1][1] *= friction
            p[0][1] += p[1][1] * self.dt
            if self.tile_map.solid_check(p[0]):
                p[0][1] -= p[1][1] * self.dt
                p[1][1] *= -bounce
                p[1][0] *= friction
            p[1][1] = min(8, p[1][1] + gravity * self.dt)
    
    def update_sparks(self, render_scroll):
        for i, spark in sorted(enumerate(self.sparks), reverse=True):
            spark.update(self.dt)
            if spark.speed >= 0:
                spark.draw(self.level_surf, render_scroll)
            else:
                self.sparks.pop(i)
    
    @staticmethod
    def alpha_surf(dim, alpha, color):
        surf = pygame.Surface(dim)
        surf.fill(color)
        surf.set_alpha(alpha)
        return surf.convert_alpha()
    
    def calc_smoke(self, smoke, render_scroll):
        smoke[0][0] += smoke[1][0] * self.dt
        smoke[0][1] += smoke[1][1] * self.dt
        smoke[1][0] += (smoke[1][0] * 0.98 - smoke[1][0]) * self.dt
        smoke[1][1] += (smoke[1][1] * 0.98 - smoke[1][1]) * self.dt
        smoke[4] += (smoke[5] - smoke[4]) / 2 * self.dt
        smoke[3] = max(0, smoke[3] - SMOKE_DELAY * self.dt)
        smoke[2] += 0.2 * self.dt
        surf = pygame.transform.rotate(self.alpha_surf([smoke[2], smoke[2]], smoke[3], smoke[6]), smoke[4])
        if not smoke[3]:
            self.smoke.remove(smoke)
        return (surf, (smoke[0][0] - surf.get_width() * 0.5 - render_scroll[0], smoke[0][1] - surf.get_height() * 0.5 - render_scroll[1]))
    
    def update_slime(self, render_scroll):
        slime_width = 2
        for splat in self.splat.copy():
            splat[0][0] += splat[1][0] * self.dt
            splat[0][1] += splat[1][1] * self.dt
            if self.tile_map.solid_check(splat[0]):
                angle = random.random() * math.pi * 2
                vel = 0.2
                self.slime.append([list(splat[0]), [math.cos(angle) * vel, math.sin(angle) * vel], splat[2]])
                splat[3] = -1
            splat[1][1] += 0.14 * self.dt
            splat[1][0] += (splat[1][0] * 0.995 - splat[1][0]) * self.dt

            splat_circle = pygame.geometry.Circle(splat[0][0], splat[0][1], max(1, splat[3]))

            for enemy in self.enemies:
                big_rect = pygame.Rect(enemy.pos.x - TILE_SIZE, enemy.pos.y - TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if not big_rect.collidepoint(splat[0]):
                    continue
                if enemy.particle_check(splat[0])[0]:
                    angle = random.random() * math.pi * 2
                    vel = 0.2
                    self.slime.append([list(splat[0]), [math.cos(angle) * vel, math.sin(angle) * vel], splat[2]])
                    splat[3] = -1

            if self.player.dead:
                big_rect = pygame.Rect(self.player.pos.x - TILE_SIZE, self.player.pos.y - TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if big_rect.collidepoint(splat[0]):
                    if self.player.particle_check(splat[0])[0]:
                        angle = random.random() * math.pi * 2
                        vel = 0.2
                        self.slime.append([list(splat[0]), [math.cos(angle) * vel, math.sin(angle) * vel], splat[2]])
                        splat[3] = -1

            pygame.draw.circle(self.level_surf, splat[2], [splat[0][0] - render_scroll[0], splat[0][1] - render_scroll[1]], splat[3])
            splat[3] -= 0.001 * self.dt
            if splat[3] <= 0:
                self.splat.remove(splat)
        locs = []
        for i, slime in sorted(enumerate(self.slime), reverse=True):
            prev_pos = slime[0].copy()
            slime[0][0] += slime[1][0] * self.dt
            slime[0][1] += slime[1][1] * self.dt
            slime[1][0] += (slime[1][0] * 0.9 - slime[1][0]) * self.dt
            slime[1][1] += (slime[1][1] * 0.9 - slime[1][1]) * self.dt
            tile_loc = f"{math.floor(slime[0][0] / TILE_SIZE)};{math.floor(slime[0][1] / TILE_SIZE)}"
            drawn = 0
            if tile_loc in self.tile_map.tile_map:
                target_tile = self.tile_map.tile_map[tile_loc]
                if target_tile["type"] in PHYSICS_TILES:
                    tile_x = math.floor(slime[0][0] / TILE_SIZE) * TILE_SIZE
                    tile_y = math.floor(slime[0][1] / TILE_SIZE) * TILE_SIZE
                    prev_img_pos = (prev_pos[0] - tile_x, prev_pos[1] - tile_y)
                    img_pos = (slime[0][0] - tile_x, slime[0][1] - tile_y)
                    pygame.draw.line(target_tile["img"], slime[2], prev_img_pos, img_pos, width=slime_width)
                    try:
                        if 0 < img_pos[0] < TILE_SIZE - 1 and 0 < img_pos[1] < TILE_SIZE - slime_width - 1:
                            if not (target_tile["img"].get_at((img_pos[0], img_pos[1] + slime_width)) == slime[2]):
                                target_tile["img"].set_at((img_pos[0], img_pos[1] + slime_width), (20, 16, 32))
                    except IndexError:
                        pass
                    
                    locs.append(tile_loc)
                    target_tile["img"].set_colorkey((0, 255, 0))
                    drawn = 1
            for enemy in self.enemies:
                if not enemy.dead:
                    continue
                big_rect = pygame.Rect(enemy.pos.x - TILE_SIZE, enemy.pos.y - TILE_SIZE, TILE_SIZE * 3, TILE_SIZE * 3)
                if not big_rect.collidepoint(slime[0]):
                    continue
                collide, local_pos = enemy.particle_check(slime[0])
                if collide:
                    img_mask = enemy.hurt_mask
                    local_x = max(0, min(enemy.scribble_surf.get_width() - 1, int(local_pos[0])))
                    local_y = max(0, min(enemy.scribble_surf.get_height() - 1, int(local_pos[1])))
                    if img_mask.get_at((local_x, local_y)):
                        _, prev_local_pos = enemy.particle_check(prev_pos)
                        if prev_local_pos is None:
                            prev_local_pos = local_pos
                        prev_local_x = max(0, min(enemy.scribble_surf.get_width() - 1, int(prev_local_pos[0])))
                        prev_local_y = max(0, min(enemy.scribble_surf.get_height() - 1, int(prev_local_pos[1])))

                        pygame.draw.line(enemy.scribble_surf, slime[2], (prev_local_x, prev_local_y), (local_x, local_y), width=slime_width)

                        drawn = 1
            if self.player.dead:
                collide, local_pos = self.player.particle_check(slime[0])
                if collide:
                    img_mask = self.player.hurt_mask
                    local_x = max(0, min(self.player.scribble_surf.get_width() - 1, int(local_pos[0])))
                    local_y = max(0, min(self.player.scribble_surf.get_height() - 1, int(local_pos[1])))
                    if img_mask.get_at((local_x, local_y)):
                        _, prev_local_pos = self.player.particle_check(prev_pos)
                        if prev_local_pos is None:
                            prev_local_pos = local_pos
                        prev_local_x = max(0, min(self.player.scribble_surf.get_width() - 1, int(prev_local_pos[0])))
                        prev_local_y = max(0, min(self.player.scribble_surf.get_height() - 1, int(prev_local_pos[1])))

                        pygame.draw.line(self.player.scribble_surf, slime[2], (prev_local_x, prev_local_y), (local_x, local_y), width=slime_width)

                        # self.player.img.set_colorkey(None)
                        # self.player.img.blit(img_mask.to_surface(setcolor=(0, 0, 0, 0), unsetcolor=(0, 255, 0)), (0, 0))
                        # self.player.img.set_colorkey((0, 255, 0))
                        drawn = 1
            if not drawn:
                pygame.draw.line(self.level_surf, slime[2], [prev_pos[0] - render_scroll[0], prev_pos[1] - render_scroll[1]], [slime[0][0] - render_scroll[0], slime[0][1] - render_scroll[1]])
            if abs(slime[1][0]) < 0.01:
                if abs(slime[1][1]) < 0.01: # (22, 19, 35)
                    self.slime.pop(i)
        for loc in locs:
            tt = self.tile_map.tile_map[loc]
            tt["img"].blit(tt["mask_surf"])
            tt["img"].set_colorkey((0, 255, 0))

    
    def reset(self):
        self.screen_shake = 0
        self.scroll = pygame.Vector2(0, 0)
    
    def create_prog(self, vert_path, frag_path):
        vert_src = ""
        frag_src = ""
        with open(get_script_path() + vert_path, "r") as f:
            vert_src = f.read()
        with open(get_script_path() + frag_path, "r") as f:
            frag_src = f.read()
        
        return self.ctx.program(
            vertex_shader=vert_src,
            fragment_shader=frag_src
        )
    
    def setup_gl(self):
        self.ctx = moderngl.create_context()
        self.prog = self.create_prog("data/shaders/screenShader.vert", "data/shaders/screenShader.frag")
        self.prog["screenTex"].value = 0
        self.prog["lightTex"].value = 1
        self.prog["tileTex"].value = 2
        self.prog["uiTex"].value = 3
        self.prog["noiseTex"].value = 4

        vertices = array.array("f", [-1.0, 1.0, 0.0, 0.0, -1.0, -1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, -1.0, 1.0, 1.0])
        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, "2f 2f", "aPos", "aTexCoord")])
    
    def setup_framebuffer(self):
        self.screenTex = self.ctx.texture(self.screen.get_size(), 4)
        self.screenTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.screenTex.swizzle = "BGRA"
        self.screenTex.repeat_x = False
        self.screenTex.repeat_y = False

        self.uiTex = self.ctx.texture(self.ui_render_surf.get_size(), 4)
        self.uiTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.uiTex.swizzle = "BGRA"
        self.uiTex.repeat_x = False
        self.uiTex.repeat_y = False

        self.tileTex = self.ctx.texture(self.screen.get_size(), 4)
        self.tileTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.tileTex.swizzle = "BGRA"
        self.tileTex.repeat_x = False
        self.tileTex.repeat_y = False

        light_size = (
            math.ceil(self.screen.get_width() / TILE_SIZE) + 2,
            math.ceil(self.screen.get_height() / TILE_SIZE) + 2,
        )
        self.lightTex = self.ctx.texture(light_size, 4)
        self.lightTex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.lightTex.swizzle = "BGRA"
        self.lightTex.repeat_x = False
        self.lightTex.repeat_y = False
    
    def close(self):
        self.screenTex.release()
        self.lightTex.release()
        self.uiTex.release()
        self.tileTex.release()
        self.noiseTex.release()
        pygame.quit()
        sys.exit()
    
    def __contains__(self, pos):
        return self.scroll[0] <= pos[0] <= self.scroll[0] + self.level_surf.get_width() and self.scroll[1] <= pos[1] <= self.scroll[1] + self.level_surf.get_height()
    
    def update(self):
        # update entities
        self.player.update(self.dt)
        self.tile_map.grass_manager.update([self.player.get_rect()])

        complete = True
        for enemy in self.enemies:
            enemy.update(self.dt)
            if not enemy.dead:
                complete = False
            if self.player.dead:
                enemy.mood = "passive"
        if complete:
            self.level_complete = True
            # if not self.player.dead and random.random() < 0.005:
                # enemy.pepper.shoot(pygame.Vector2(self.player.get_rect().center) + pygame.Vector2(random.random() * 50 - 25, random.random() * 50 - 25))

        # render to screen
        self.screen.fill((14, 130, 206))
        # self.level_surf.fill((14, 130, 206))

        if self.level in {0, 3}:
            self.level_surf.blit(pygame.transform.scale(self.assets["background"], self.level_surf.get_size()), (0, 0))

            for cloud in self.clouds:
                cloud[0] += self.dt * cloud[3] * 0.1
                
                pos = [cloud[0] % (self.level_surf.get_width() + 128) - 64, cloud[1] % (self.level_surf.get_height() * 0.5 + 64) - 32]
                self.level_surf.blit(self.assets["clouds"][cloud[2]], pos)
        elif self.level in {1, 4}:
            if self.series == 0:
                self.level_surf.blit(pygame.transform.scale(self.assets["restaurant_bg"], self.level_surf.get_size()), (0, 0))
            else:
                self.level_surf.blit(pygame.transform.scale(self.assets["restaurant_bg2"], self.level_surf.get_size()), (0, 0))

        elif self.level in {2, 5}:
            self.level_surf.blit(pygame.transform.scale(self.assets["kitchen_bg"], self.level_surf.get_size()), (0, 0))

        screen_shake_offset = (
            (random.random() - 0.5) * self.screen_shake,
            (random.random() - 0.5) * self.screen_shake
        )

        render_scroll = (int(self.scroll[0] + screen_shake_offset[0]), int(self.scroll[1] + screen_shake_offset[1]))
        self.screen_shake = max(0, self.screen_shake - SCREEN_SHAKE_DECAY * self.dt)

        self.tile_map.draw(self.level_surf, render_scroll)
        self.tile_map.draw_decor(self.level_surf, render_scroll)
        for enemy in self.enemies:
            enemy.draw(self.level_surf, render_scroll)
        self.player.draw(self.level_surf, render_scroll)

        average_gust = 0
        for gust in self.wind:
            gust[0] -= (gust[1] + math.sin(gust[0] * 0.025) * 0.3) * self.dt * 0.5
            if not ((gust[0], self.scroll[1] + self.screen.get_height() / 2) in self):
                gust[1] = 5 * (random.random() + 0.5) * 2
                gust[0] = self.scroll[0] + self.screen.get_width() - gust[1] * self.dt
            average_gust += gust[1]
        average_gust *= 0.5

        for rect, fix in self.leaf_spawners:
            if random.random() * 20000 / (average_gust * 0.15) / self.dt < rect.width * rect.height:
                pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                if not self.tile_map.solid_check(pos) and fix:
                    self.particles.append(Particle(self, 'leaf', pos, (-0.1, 0.3), frame=random.randint(0, 16), solid=True))
                else:
                    self.particles.append(Particle(self, 'leaf', pos, (-0.1, 0.3), frame=random.randint(0, 16), solid=False))

        for particle in self.particles.copy():
            kill = particle.update()
            particle.draw(self.level_surf, render_scroll)
            if particle.particle_type == 'leaf' and (not particle.done):
                particle.pos[0] += math.sin(particle.frame * 0.08) * 0.8 * self.dt - 0.5 * self.dt * (average_gust * 0.1)
                particle.vel[1] = min(0.2, particle.vel[1] + 0.005 / (average_gust * 0.1) * self.dt)
            if kill:
                self.particles.remove(particle)
        self.update_kickup(render_scroll)
        self.update_sparks(render_scroll)
        self.cinders.update(self.level_surf, render_scroll)
        self.update_slime(render_scroll)

        self.level_surf.fblits([self.calc_smoke(smoke, render_scroll) for smoke in self.smoke.copy()])
        self.update_fireflies(render_scroll)

        level_size = (self.level_surf.get_width() * self.ls_scale, self.level_surf.get_height() * self.ls_scale)
        self.level_surf_pos = pygame.Vector2(
            self.screen.get_width() * 0.5 - level_size[0] * 0.5,
            self.screen.get_height() * 0.5 - level_size[1] * 0.5,
        )

        if not self.player.dead:
            if self.player.mode == "shotgun" and pygame.mouse.get_focused():
                # get shotgun screen space position
                ss_pos = pygame.Vector2(self.player.get_rect().centerx, self.player.get_rect().centery + 4)

                mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                mouse_pos /= SCALE
                mouse_pos -= self.level_surf_pos
                mouse_pos /= self.ls_scale
                d = mouse_pos- ss_pos
                self.player.shotgun.angle = math.atan2(-d.y, d.x) - math.pi * 0.5
                self.player.shotgun.flipped = mouse_pos.x > self.player.get_rect().centerx
                self.player.flip = not self.player.shotgun.flipped
            else:
                self.player.shotgun.angle += (math.pi * 0.5 * (int(self.player.flip) * 2 - 1) - self.player.shotgun.angle) * 0.3 * self.dt
                self.player.shotgun.flipped = not self.player.flip
        
        self.screen.blit(pygame.transform.scale(self.level_surf, level_size), self.level_surf_pos)

        self.level_surf.fill((0, 0, 0))
        self.tile_map.draw(self.level_surf, render_scroll)
        self.tileSurf.fill((0, 0, 0))
        self.tileSurf.blit(pygame.transform.scale(self.level_surf, level_size), self.level_surf_pos)

        self.prog["scrollX"].value = render_scroll[0]
        self.prog["scrollY"].value = render_scroll[1]
        self.prog["scrWidth"].value = self.screen.get_width()
        self.prog["scrHeight"].value = self.screen.get_height()
        self.prog["levelX"].value = self.level_surf_pos.x
        self.prog["levelY"].value = self.level_surf_pos.y
        self.prog["levelW"].value = level_size[0]
        self.prog["levelH"].value = level_size[1]
        self.prog["levelScale"].value = self.ls_scale

        light_surf = self.tile_map.get_light_data(self.screen, render_scroll)
        self.lightTex.write(light_surf.get_view('1'))

        self.ui_render_surf.fill((0, 0, 0))
        self.ui_surf.fill((0, 0, 0))

        pygame.draw.rect(self.ui_surf, (20, 16, 32), (0, 0, self.ui_surf.get_width(), TILE_SIZE - 1))
        series = SERIES_1 if self.series == 0 else SERIES_2
        font_surf = self.bold_font.render(series[self.level][1], False, (219, 224, 231))
        self.ui_surf.blit(font_surf, (self.ui_surf.get_width() * 0.5 - font_surf.get_width() * 0.5, 4))

        if self.player.finished and not (self.fade_dir == 1):
            self.fade_dir = 1
    
        self.fade = pygame.math.clamp(self.fade + self.fade_dir * self.dt * 0.014, 0, 1)
        if self.fade_dir == 1 and self.fade == 1:
            if not self.player.dead:
                self.next_level()
            else:
                self.state = "death"
                if self.cycles > self.max_cycles:
                    self.max_cycles = self.cycles
            self.fade_dir = -1

        if self.fade == 0 and self.fade_dir == -1:
            self.fade_dir = 0

        pygame.draw.rect(self.ui_surf, (20, 16, 32), (0, 0, self.ui_surf.get_width(), self.ui_surf.get_height() * 1.6 * self.fade))

        self.ui_render_surf.blit(pygame.transform.scale(self.ui_surf, level_size), self.level_surf_pos)
        self.uiTex.write(self.ui_render_surf.get_view('1'))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                    return
                elif event.type == pygame.VIDEORESIZE:
                    width, height = event.size
                    width = max(width, WIDTH)
                    height = max(height, HEIGHT)
                    self.ctx.viewport = (0, 0, width, height)
                    self.display = pygame.display.set_mode((width, height), flags=pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF)
                    self.screen = pygame.Surface((width // SCALE, height // SCALE))
                    self.tileSurf = pygame.Surface(self.screen.get_size())
                    self.ui_render_surf = pygame.Surface(self.screen.get_size())
                    self.screenTex.release()
                    self.lightTex.release()
                    self.tileTex.release()
                    self.uiTex.release()

                    resolution = 1
                    xscale = self.screen.get_width() / self.level_surf.get_width() * resolution
                    yscale = self.screen.get_height() / self.level_surf.get_height() * resolution
                    self.ls_scale = math.floor(min(xscale, yscale)) / resolution
                    self.level_surf_pos = pygame.Vector2(0, 0)
                    self.setup_framebuffer()

                elif event.type == pygame.KEYDOWN:
                    if self.state == "game":
                        if event.key in {pygame.K_UP, pygame.K_SPACE, pygame.K_w}:
                            self.player.controls["up"] = True
                            if self.player.falling < 5:
                                self.player.jumping = 0
                                self.player.falling = 873745
                        elif event.key in {pygame.K_DOWN, pygame.K_s}:
                            self.player.controls["down"] = True
                        elif event.key in {pygame.K_LEFT, pygame.K_a}:
                            self.player.controls["left"] = True
                        elif event.key in {pygame.K_RIGHT, pygame.K_d}:
                            self.player.controls["right"] = True
                        elif event.key in {pygame.K_x}:
                            if self.player.mode == "sword":
                                if self.player.sword.attacked > 10:
                                    self.player.sword.attack()
                                self.player.sword.update()
                            elif self.player.mode == "shotgun":
                                self.player.shotgun.shoot()
                            elif self.player.mode == "pepper":
                                if pygame.mouse.get_focused():
                                    mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                                    mouse_pos /= SCALE
                                    mouse_pos -= self.level_surf_pos
                                    mouse_pos /= self.ls_scale
                                    self.player.pepper.shoot(mouse_pos)
                                else:
                                    self.player.pepper.shoot(pygame.Vector2(self.player.pepper.pos) + pygame.Vector2(300 * -(2 * int(self.player.flip) - 1), -5))
                            elif self.player.mode == "fists" and not self.player.attacking:
                                self.player.punch.reset()
                                self.player.attacking = True
                        elif event.key == pygame.K_z:
                            self.player.die(pygame.Vector2(0, 5), self.player.pos - pygame.Vector2(5, 5))
                    elif self.state == "menu":
                        if event.key == pygame.K_RETURN and self.time > 30:
                            self.fade_dir = 1
                    elif self.state == "talk":
                        if event.key == pygame.K_RETURN:
                            full_text = self.text[self.texts_idx][self.text_idx]
                            if self.text_timer > 10:
                                if (self.text_timer - 30) * 0.8 < len(full_text):
                                    self.text_timer = len(full_text) / 0.8 + 30
                                else:
                                    self.text_idx += 1
                                    if self.text_idx == len(self.text[self.texts_idx]):
                                        self.text_idx -= 1
                                        self.fade_dir = 1
                                    self.text_timer = 0
                    elif self.state == "spin":
                        if event.key == pygame.K_RETURN:
                            if not self.spin_alpha < 1:
                                self.wheel_vel = math.pi * 0.3 + random.random() * math.pi
                                self.spin_alpha = 0.99
                                self.wheel_scale = 0.8
                                self.wheel_text = ""
                            elif self.wheel_vel < 0.001:
                                self.fade_dir = 1
                    elif self.state == "death":
                        if event.key == pygame.K_RETURN:
                            self.fade_dir = 1
                            self.strikes -= 1
                elif event.type == pygame.KEYUP:
                    if self.state == "game":
                        if event.key in {pygame.K_UP, pygame.K_SPACE, pygame.K_w}:
                            self.player.release_jump()
                        elif event.key in {pygame.K_DOWN, pygame.K_s}:
                            self.player.controls["down"] = False
                        elif event.key in {pygame.K_LEFT, pygame.K_a}:
                            self.player.controls["left"] = False
                        elif event.key in {pygame.K_RIGHT, pygame.K_d}:
                            self.player.controls["right"] = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "game":
                        if self.player.mode == "sword":
                            if self.player.sword.attacked > 10:
                                self.player.sword.attack()
                            self.player.sword.update()
                        elif self.player.mode == "shotgun":
                            self.player.shotgun.shoot()
                        elif self.player.mode == "pepper":
                            mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
                            mouse_pos /= SCALE
                            mouse_pos -= self.level_surf_pos
                            mouse_pos /= self.ls_scale
                            self.player.pepper.shoot(mouse_pos)
                        elif self.player.mode == "fists" and not self.player.attacking:
                            self.player.punch.reset()
                            self.player.attacking = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    if self.state == "death":
                        if self.rs_hover:
                            self.fade_dir = 1
                            self.strikes -= 1
                elif event.type in {pygame.WINDOWEXPOSED, pygame.WINDOWMOVED, pygame.WINDOWRESIZED}:
                    self.last_time = time.time()
            
            # delta time
            self.dt = (time.time() - self.last_time) * 60
            self.slomo = min(1.0, self.slomo + max(0.01, (1.0 - self.slomo) * 0.08) * self.dt)
            self.dt = min(self.dt, 3) * self.slomo # if you're under 20 fps you're screwed anyway
            self.last_time = time.time()
            self.time += self.dt

            if self.state == "game":
                self.update()
            elif self.state == "menu":
                self.menu()
            elif self.state == "talk":
                self.talk()
            elif self.state == "spin":
                self.wheel_spin()
            elif self.state == "death":
                self.death()
            
            self.prog["menu"] = int(self.state != "game")
            self.screenTex.write(self.screen.get_view('1')) # update opengl texture using pygame surface data
            self.tileTex.write(self.tileSurf.get_view('1'))

            # render using opengl
            self.ctx.clear(0, 0, 0)
            self.screenTex.use(0)
            self.lightTex.use(1)
            self.prog["tintFactor"] = self.slomo * 0.25 + 0.75
            self.tileTex.use(2)
            self.uiTex.use(3)
            self.noiseTex.use(4)
            self.prog["time"] = -self.time * 0.5
            self.vao.render(moderngl.TRIANGLE_STRIP) # render screen quad

            pygame.display.flip()
            pygame.display.set_caption(f"The Revenge Cycle at {self.clock.get_fps() :.1f} fps")

            self.clock.tick(120)

if __name__ == "__main__":
    App().run()
