import pygame, sys, time, moderngl, array, random

from src.bip import *
from src.util import *
from src.tiles import *
from src.player import Player
from src.enemies import Enemy

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
            'player': {
                "black": {
                    "idle": load_animation("player/black/idle.png", 15, 31, 4),
                    "run": load_animation("player/black/walk.png", 15, 31, 4),
                    "jump": load_animation("player/black/jump.png", 15, 31, 2),
                    "land": load_animation("player/black/land.png", 16, 31, 3)
                },
                "white": {
                    "idle": load_animation("player/white/idle.png", 15, 31, 4),
                    "run": load_animation("player/white/walk.png", 15, 31, 4),
                    "jump": load_animation("player/white/jump.png", 15, 31, 2),
                    "land": load_animation("player/white/land.png", 16, 31, 3)
                },
                "knife": load_image("player/knife.png"),
                "shotgun": load_image("player/shotgun.png"),
                "bullet": load_image("player/bullet.png"),
                "pepper": load_image("player/pepper.png")
            },
            "placeholder": load_image("placeholder.png")
        }

        self.tile_map = TileMap(self)
        self.tile_map.load("data/maps/0.json")

        # extract enemies
        self.enemies = []
        for loc in self.tile_map.tile_map.copy():
            if self.tile_map.tile_map[loc]["type"] == "enemy":
                tile = self.tile_map.tile_map[loc]
                self.enemies.append(Enemy(self, [15, 31], [self.tile_map.tile_map[loc]["pos"][0] * TILE_SIZE, self.tile_map.tile_map[loc]["pos"][1] * TILE_SIZE - 100]))
                del self.tile_map.tile_map[loc]

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0

        self.player = Player(self, [15, 31], [20, 50], "black")

    
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
    
    def update(self):
        # update entities
        self.player.update(self.dt)
        for enemy in self.enemies:
            enemy.update(self.dt)

        # render to screen
        self.screen.fill((14, 130, 206))
        self.level_surf.fill((14, 130, 206))

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

        level_size = (self.level_surf.get_width() * self.ls_scale, self.level_surf.get_height() * self.ls_scale)
        self.level_surf_pos = pygame.Vector2(
            self.screen.get_width() * 0.5 - level_size[0] * 0.5,
            self.screen.get_height() * 0.5 - level_size[1] * 0.5,
        )
        if self.player.mode == "shotgun" and pygame.mouse.get_focused():
            # get shotgun screen space position
            ss_pos = pygame.Vector2(self.player.shotgun.pos.x + self.player.shotgun.offset[0], self.player.shotgun.pos.y + self.player.shotgun.offset[1])

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
            
            # delta time
            self.dt = (time.time() - self.last_time) * 60
            self.dt = min(self.dt, 3) # if you're under 20 fps you're screwed anyway
            self.last_time = time.time()

            self.update()
            self.screenTex.write(self.screen.get_view('1')) # update opengl texture using pygame surface data
            self.tileTex.write(self.tileSurf.get_view('1'))

            # render using opengl
            self.ctx.clear(0, 0, 0)
            self.screenTex.use(0)
            self.lightTex.use(1)
            self.tileTex.use(2)
            self.vao.render(moderngl.TRIANGLE_STRIP) # render screen quad

            pygame.display.flip()
            pygame.display.set_caption(f"The Revenge Cycle at {self.clock.get_fps() :.1f} fps")

            self.clock.tick(120)

if __name__ == "__main__":
    App().run()
