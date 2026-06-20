import pygame

from .bip import *

class Enemy:
    def __init__(self, app, dimensions, start_pos):
        self.app = app
        self.dimensions = pygame.Vector2(dimensions)
        self.pos = pygame.Vector2(start_pos)
        
        self.falling = 23434

        self.movement = pygame.Vector2(0, 0)
        self.collisions = {"right": False, "left": False, "up": False, "down": False} # useful to keep track of

        self.dead = False # are we dead :)

        # for the animations
        self.flip = False

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)
    
    def update(self, dt):
        if self.dead:
            return
        
        self.falling += dt

        # ----- collision handling ----- #
        self.collisions = {"right": False, "left": False, "down": False, "up": False}
        
        # frame movement
        fm = pygame.Vector2(self.movement.x * dt, self.movement.y * dt)

        # first do x-axis movement
        self.pos.x += fm.x
        self.pos.x = max(0, min(TILE_SIZE * CHUNK_SIZE * LEVEL_WIDTH - self.dimensions.x, self.pos.x))
        r = self.get_rect()
        for rect in self.app.tile_map.physics_rects_around(r.center):
            if r.colliderect(rect):
                if fm.x >= 0:
                    r.right = rect.left
                    self.collisions["right"] = True
                elif fm.x < 0:
                    r.left = rect.right
                    self.collisions["left"] = True
                self.pos.x = r.x
                self.movement.x = 0
        
        # then do y-axis movement
        self.pos.y += fm.y
        r = self.get_rect()
        for rect in self.app.tile_map.physics_rects_around(r.center):
            if r.colliderect(rect):
                if fm.y >= 0:
                    r.bottom = rect.top
                    self.falling = 0
                    if self.controls["up"]:
                        self.jumping = 0
                    self.collisions["down"] = True
                elif fm.y < 0:
                    r.top = rect.bottom
                    self.controls["up"] = False
                    self.collisions["up"] = True
                self.movement.y = 0
                self.pos.y = r.y

        # one more time for dangerous stuff
        r = self.get_rect()
        for rect in self.app.tile_map.danger_rects_around(self.get_rect().center):
            if rect.colliderect(r):
                self.dead = True
                return
    
    def draw(self, surf, scroll):
        pygame.draw.rect(surf, (0, 0, 255), (self.pos.x - scroll[0], self.pos.y - scroll[1], self.dimensions.x, self.dimensions.y))