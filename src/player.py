import pygame
from .bip import *

class Player:
    def __init__(self, app, dimensions, start_pos):
        self.app = app # to access tile map and particle managers
        # for collisions
        self.dimensions = pygame.Vector2(dimensions)
        # for respawning if needed
        self.start_pos = start_pos
        self.pos = pygame.Vector2(start_pos)

        # for jumping + land animation
        self.falling = 30
        self.grounded = 0
        self.jumping = 30

        # controls (WASD + arrow keys)
        self.controls = {"up": False, "down": False, "left": False, "right": False}

        # player velocity (modify using controls^), used to calculate frame_movement in Player.update
        self.movement = pygame.Vector2(0, 0)

        # player stats ig
        self.speed = 0.7
        self.jump_height = 9 # number of frames we can jump for
        self.jump_strength = 3 # value of movement.y each frame during jump
        self.gravity = 0.3
        self.friction = 0.7
        self.collisions = {"right": False, "left": False, "up": False, "down": False} # useful to keep track of

        self.dead = False # are we dead :)

        # for the animations
        self.flip = False

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)
    
    def update(self, dt):
        if self.dead:
            return

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

        # ----- player input ----- #
        
        # update counters
        self.falling += dt
        temp = self.jumping
        self.jumping += dt
        if temp < self.jump_height and self.jumping > self.jump_height:
            self.jumping = 0
            self.release_jump()
        self.grounded += dt

        # x movement
        if self.controls["right"]:
            self.movement.x += self.speed * dt
            self.flip = False
        if self.controls["left"]:
            self.movement.x -= self.speed * dt
            self.flip = True
        
        self.movement.x *= self.friction ** dt

        self.movement.y += self.gravity * dt
        self.movement.y = min(self.movement.y, 24)

        if self.jumping <= self.jump_height:
            if self.controls["up"]:
                self.movement.y = -self.jump_strength 
    
    def release_jump(self):
        self.controls["up"] = False
        if self.jumping < self.jump_height:
            self.movement.y *= 0.65
        self.jumping = self.jump_height + 1

    def draw(self, surf, scroll):
        pygame.draw.rect(surf, (255, 0, 0), (self.pos.x - scroll[0], self.pos.y - scroll[1], self.dimensions.x, self.dimensions.y))