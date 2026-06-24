import pygame, sys, time, moderngl, array, random
import pygame.geometry

from src.bip import *
from src.util import *
from src.tiles import *
from src.player import Player
from src.enemies import Enemy
from src.particles import *

pygame.init()
pygame.mixer.init()
pygame.font.init()

class App:
    def __init__(self):
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
            "placeholder": load_image("placeholder.png"),
            "firefly": load_animation("firefly.png", 5, 5, 20),
            "particle/explosion": load_animation("particles/explosion.png", 5, 5, 15),
            "particle/particle": load_animation("particles/particle.png", 5, 5, 4),
            "clouds": load_imgs("clouds.png", (1, 2), (64, 32)),
            "background": load_image("background.png")
        }

        self.tile_map = TileMap(self)
        self.tile_map.load("data/maps/1.json")

        # extract enemies
        self.enemies = []
        for loc in self.tile_map.tile_map.copy():
            if self.tile_map.tile_map[loc]["type"] == "enemy":
                tile = self.tile_map.tile_map[loc]
                self.enemies.append(Enemy(self, [15, 31], [self.tile_map.tile_map[loc]["pos"][0] * TILE_SIZE, self.tile_map.tile_map[loc]["pos"][1] * TILE_SIZE], num=len(self.enemies)))
                del self.tile_map.tile_map[loc]

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0

        self.player = Player(self, [9, 31], [20, 50], "black")

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
                        angle = random.random() * mathpi * 2
                        vel = 0.2
                        self.slime.append([list(splat[0]), [math.cos(angle) * vel, math.sin(angle) * vel], splat[2]])
                        splat[3] = -1

            pygame.draw.circle(self.level_surf, splat[2], [splat[0][0] - render_scroll[0], splat[0][1] - render_scroll[1]], splat[3])
            splat[3] -= 0.001 * self.dt
            if splat[3] <= 0:
                self.splat.remove(splat)
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
                        
                    target_tile["img"].blit(target_tile["mask_surf"])
                    target_tile["img"].set_colorkey((0, 255, 0))
                    drawn = 1
            for enemy in self.enemies:
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

        vertices = array.array("f", [-1.0, 1.0, 0.0, 0.0, -1.0, -1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, -1.0, 1.0, 1.0])
        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, "2f 2f", "aPos", "aTexCoord")])
    
    def setup_framebuffer(self):
        self.screenTex = self.ctx.texture(self.screen.get_size(), 4)
        self.screenTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.screenTex.swizzle = "BGRA"
        self.screenTex.repeat_x = False
        self.screenTex.repeat_y = False

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
        pygame.quit()
        sys.exit()
    
    def __contains__(self, pos):
        return self.scroll[0] <= pos[0] <= self.scroll[0] + self.level_surf.get_width() and self.scroll[1] <= pos[1] <= self.scroll[1] + self.level_surf.get_height()
    
    def update(self):
        # update entities
        self.player.update(self.dt)
        for enemy in self.enemies:
            enemy.update(self.dt)
            # if not self.player.dead and random.random() < 0.005:
                # enemy.pepper.shoot(pygame.Vector2(self.player.get_rect().center) + pygame.Vector2(random.random() * 50 - 25, random.random() * 50 - 25))

        # render to screen
        self.screen.fill((14, 130, 206))
        # self.level_surf.fill((14, 130, 206))
        self.level_surf.blit(pygame.transform.scale(self.assets["background"], self.level_surf.get_size()), (0, 0))

        for cloud in self.clouds:
            cloud[0] += self.dt * cloud[3] * 0.1
            
            pos = [cloud[0] % (self.level_surf.get_width() + 128) - 64, cloud[1] % (self.level_surf.get_height() * 0.5 + 64) - 32]
            self.level_surf.blit(self.assets["clouds"][cloud[2]], pos)

        screen_shake_offset = (
            (random.random() - 0.5) * self.screen_shake,
            (random.random() - 0.5) * self.screen_shake
        )

        render_scroll = (int(self.scroll[0] + screen_shake_offset[0]), int(self.scroll[1] + screen_shake_offset[1]))
        self.screen_shake = max(0, self.screen_shake - SCREEN_SHAKE_DECAY * self.dt)

        self.tile_map.draw(self.level_surf, render_scroll)
        for enemy in self.enemies:
            enemy.draw(self.level_surf, render_scroll)
        self.player.draw(self.level_surf, render_scroll)

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
                    self.screenTex.release()
                    self.lightTex.release()
                    self.tileTex.release()

                    resolution = 1
                    xscale = self.screen.get_width() / self.level_surf.get_width() * resolution
                    yscale = self.screen.get_height() / self.level_surf.get_height() * resolution
                    self.ls_scale = math.floor(min(xscale, yscale)) / resolution
                    self.level_surf_pos = pygame.Vector2(0, 0)
                    self.setup_framebuffer()

                elif event.type == pygame.KEYDOWN:
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
                elif event.type == pygame.KEYUP:
                    if event.key in {pygame.K_UP, pygame.K_SPACE, pygame.K_w}:
                        self.player.release_jump()
                    elif event.key in {pygame.K_DOWN, pygame.K_s}:
                        self.player.controls["down"] = False
                    elif event.key in {pygame.K_LEFT, pygame.K_a}:
                        self.player.controls["left"] = False
                    elif event.key in {pygame.K_RIGHT, pygame.K_d}:
                        self.player.controls["right"] = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
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
                elif event.type in {pygame.WINDOWEXPOSED, pygame.WINDOWMOVED, pygame.WINDOWRESIZED}:
                    self.last_time = time.time()
            
            # delta time
            self.dt = (time.time() - self.last_time) * 60
            self.slomo = min(1.0, self.slomo + max(0.01, (1.0 - self.slomo) * 0.08) * self.dt)
            self.dt = min(self.dt, 3) * self.slomo # if you're under 20 fps you're screwed anyway
            self.last_time = time.time()

            self.update()
            self.screenTex.write(self.screen.get_view('1')) # update opengl texture using pygame surface data
            self.tileTex.write(self.tileSurf.get_view('1'))

            # render using opengl
            self.ctx.clear(0, 0, 0)
            self.screenTex.use(0)
            self.lightTex.use(1)
            self.prog["tintFactor"] = self.slomo * 0.25 + 0.75
            self.tileTex.use(2)
            self.vao.render(moderngl.TRIANGLE_STRIP) # render screen quad

            pygame.display.flip()
            pygame.display.set_caption(f"The Revenge Cycle at {self.clock.get_fps() :.1f} fps")

            self.clock.tick(120)

if __name__ == "__main__":
    App().run()
