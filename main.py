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
        self.ls_scale = 1
        self.level_draw_pos = pygame.Vector2(0, 0)
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
            'tiles/grass': load_tile_imgs('tiles/grass.png', 16)
        }

        self.tile_map = TileMap(self)
        self.tile_map.load("data/maps/0.json")

        # extract enemies
        self.enemies = []
        for loc in self.tile_map.tile_map.copy():
            if self.tile_map.tile_map[loc]["type"] == "enemy":
                tile = self.tile_map.tile_map[loc]
                print(tile)
                self.enemies.append(Enemy(self, [16, 32], [self.tile_map.tile_map[loc]["pos"][0] * TILE_SIZE, self.tile_map.tile_map[loc]["pos"][1] * TILE_SIZE]))
                del self.tile_map.tile_map[loc]

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0

        self.player = Player(self, [16, 32], [20, 10])

    
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

        vertices = array.array("f", [-1.0, 1.0, 0.0, 0.0, -1.0, -1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, -1.0, 1.0, 1.0])
        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, "2f 2f", "aPos", "aTexCoord")])
    
    def setup_framebuffer(self):
        self.screenTex = self.ctx.texture(self.screen.get_size(), 4)
        self.screenTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.screenTex.swizzle = "BGRA"
        self.screenTex.repeat_x = False
        self.screenTex.repeat_y = False

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
        self.screen.fill((0, 0, 0))
        self.level_surf.fill((0, 0, 0))

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
        self.level_draw_pos = pygame.Vector2(
            self.screen.get_width() * 0.5 - level_size[0] * 0.5,
            self.screen.get_height() * 0.5 - level_size[1] * 0.5,
        )
        self.screen.blit(pygame.transform.scale(self.level_surf, level_size), self.level_draw_pos)

        self.prog["scrollX"].value = render_scroll[0]
        self.prog["scrollY"].value = render_scroll[1]
        self.prog["scrWidth"].value = self.screen.get_width()
        self.prog["scrHeight"].value = self.screen.get_height()
        self.prog["levelX"].value = self.level_draw_pos.x
        self.prog["levelY"].value = self.level_draw_pos.y
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
                    self.screenTex.release()
                    self.lightTex.release()

                    xscale = self.screen.get_width() / self.level_surf.get_width()
                    yscale = self.screen.get_height() / self.level_surf.get_height()
                    self.ls_scale = math.floor(min(xscale, yscale))
                    self.level_draw_pos = pygame.Vector2(0, 0)
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
                elif event.type == pygame.KEYUP:
                    if event.key in {pygame.K_UP, pygame.K_SPACE, pygame.K_w}:
                        self.player.release_jump()
                    elif event.key in {pygame.K_DOWN, pygame.K_s}:
                        self.player.controls["down"] = False
                    elif event.key in {pygame.K_LEFT, pygame.K_a}:
                        self.player.controls["left"] = False
                    elif event.key in {pygame.K_RIGHT, pygame.K_d}:
                        self.player.controls["right"] = False
            
            # delta time
            self.dt = (time.time() - self.last_time) * 60
            self.dt = min(self.dt, 3) # if you're under 20 fps you're screwed anyway
            self.last_time = time.time()

            self.update()
            self.screenTex.write(self.screen.get_view('1')) # update opengl texture using pygame surface data

            # render using opengl
            self.ctx.clear(0, 0, 0)
            self.screenTex.use(0)
            self.lightTex.use(1)
            self.vao.render(moderngl.TRIANGLE_STRIP) # render screen quad

            pygame.display.flip()
            pygame.display.set_caption(f"The Revenge Cycle at {self.clock.get_fps() :.1f} fps")

            self.clock.tick(120)

if __name__ == "__main__":
    App().run()
