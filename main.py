import pygame, sys, time, moderngl, array, random

from src.bip import *
from src.util import *
from src.tiles import *
from src.player import Player

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

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0

        self.player = Player(self, [10, 16], [20, 10])
    
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

        vertices = array.array("f", [-1.0, 1.0, 0.0, 0.0, -1.0, -1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, -1.0, 1.0, 1.0])
        self.vbo = self.ctx.buffer(vertices)
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, "2f 2f", "aPos", "aTexCoord")])
    
    def setup_framebuffer(self):
        self.screenTex = self.ctx.texture(self.screen.get_size(), 4)
        self.screenTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.screenTex.swizzle = "BGRA"
        self.screenTex.repeat_x = False
        self.screenTex.repeat_y = False
    
    def close(self):
        self.screenTex.release()
        pygame.quit()
        sys.exit()
    
    def update(self):
        # update entities
        self.player.update(self.dt)

        # render to screen
        self.screen.fill((0, 0, 0))

        # calculate camera scroll
        lookahead = 10
        if self.player.flip:
            lookahead *= -1
        target_scroll = [self.player.get_rect().centerx + lookahead - self.screen.get_width() * 0.5, self.player.get_rect().centery - self.screen.get_height() * 0.5]
        
        if abs(target_scroll[0] - self.scroll[0]) > SCROLL_LIMIT:
            self.scroll[0] += (target_scroll[0] - self.scroll[0]) / 30 * self.dt
        if abs(target_scroll[1] - self.scroll[0]) > SCROLL_LIMIT:
            self.scroll[1] += (target_scroll[1] - self.scroll[1]) / 30 * self.dt

        screen_shake_offset = (
            (random.random() - 0.5) * self.screen_shake,
            (random.random() - 0.5) * self.screen_shake
        )

        render_scroll = (int(self.scroll[0] + screen_shake_offset[0]), int(self.scroll[1] + screen_shake_offset[1]))
        self.screen_shake = max(0, self.screen_shake - SCREEN_SHAKE_DECAY * self.dt)

        self.tile_map.draw(self.screen, render_scroll)
        self.player.draw(self.screen, render_scroll)
    
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                    return
                elif event.type == pygame.VIDEORESIZE:
                    width, height = event.size
                    self.ctx.viewport = (0, 0, width, height)
                    self.display = pygame.display.set_mode((width, height), flags=pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF)
                    self.screen = pygame.Surface((width // SCALE, height // SCALE))
                    self.screenTex.release()
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
            self.vao.render(moderngl.TRIANGLE_STRIP) # render screen quad

            pygame.display.flip()
            pygame.display.set_caption(f"The Revenge Cycle at {self.clock.get_fps() :.1f} fps")

            self.clock.tick(120)

if __name__ == "__main__":
    App().run()
