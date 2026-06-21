import pygame, math

from .anim import Anim
from .util import draw_arc
from .bip import *

class Shotgun:
    def __init__(self, img, app, target, offset):
        self.img = img.copy()
        self.app = app
        self.pos = pygame.Vector2(target.get_rect().center)
        self.offset = offset

        self.angle = 0
        self.rebound = 0
        self.reboud_vel = 0
        self.flipped = False
        self.target = target
    
    def update(self):
        if self.target:
            self.pos = pygame.Vector2(self.target.get_rect().center)
    
    def draw(self, surf, scroll):
        offset = list(self.offset)
        if not self.flipped:
            offset[0] -= 4
        img_copy = pygame.transform.rotate(pygame.transform.flip(self.img, not self.flipped, False), math.degrees(self.angle))
        surf.blit(img_copy, (self.pos[0] + int(self.img.get_width() / 2) - int(img_copy.get_width() / 2) - scroll[0] + offset[0], self.pos[1] + int(self.img.get_height() / 2) - int(img_copy.get_height() / 2) - scroll[1] + offset[1]))
        

class Sword:
    def __init__(self, img, app, pos, target=None, offset=(0, 0)):
        self.pos = pygame.Vector2(pos)
        self.app = app
        self.target = target
        self.angle = 0
        self.offset = offset
        self.img = img.copy()
        self.attacking = False
        self.angle_offset = 90
        self.swing_dir = 0
        self.shadow_release = 0
        self.swing_vel = 0
        self.slash = None
        self.arm_length = 5
        self.attacked = 1000
        self.target_turn = 180
        self.flipped = False
        self.target_dir = 1 * math.pi
        self.damp = 0.5
        self.attack_surf = pygame.Surface((32, 32))
        self.attack_mask = pygame.mask.from_surface(self.attack_surf)
        self.attack_offset = (0, 0)

        self.arc_end = self.angle
        self.arc_start = 0
    
    def attack(self):
        #self.app.world.window.camera.screen_shake = max(self.app.world.window.camera.screen_shake, 1)
        if self.target_dir == -math.pi * 0.25:
            self.target_dir = math.pi * 0.75
        else:
            self.target_dir = -math.pi * 0.25
        if self.target_turn == 90:
            self.target_turn = 200
        else:
            self.target_turn = 90
        self.attacking = True
        self.attacked = 0
        self.damp = 0.6
        # if not self.flipped:
        #     self.slash = Slash(self.app, (self.target.rect().centerx - 5, self.target.pos[1] - 5), target=self.target, vflip=bool(self.target_dir == -math.pi * 0.25))
        # else:
        #     self.slash = Slash(self.app, (self.target.rect().centerx - 10, self.target.pos[1] - 5), flip=True, target=self.target, vflip=bool(self.target_dir == -math.pi * 0.25))

    def update(self):
        self.attacked += 1 * self.app.dt
        self.shadow_release += 1 * self.app.dt
        if self.target:
            self.pos = list(self.target.get_rect().center)
        if not self.attacking:
            self.target_dir = -math.pi * 0.25
            self.target_turn = 90
        else:
            if self.angle + self.angle_offset > self.target_dir:
                self.damp = 0.5
            if self.attacked > 40:
                self.attacking = False
                self.attacked = 4
                self.damp = 0.4
            if self.shadow_release > 2 and self.slash:
                if self.slash.animation.frame < 13:
                    self.shadow_release = 0
                    img_copy = pygame.transform.rotate(self.img, math.degrees(self.angle) - 90 + self.angle_offset)
                    self.flipped = False
                    offset = list(self.offset)
                    if self.target.flip:
                        img_copy = pygame.transform.flip(img_copy, True, False)
                        self.flipped = True
                        offset[0] -= 3
                        offset[1] += 0
                    # self.app.world.gfx_manager.shadows.append(Shadow(img_copy, (self.pos[0] + int(self.img.get_width() / 2) - int(img_copy.get_width() / 2) + offset[0], self.pos[1] + int(self.img.get_height() / 2) - int(img_copy.get_height() / 2)+ offset[1]),
                    # self.app, self, decay=20, start_alpha=100))
        force = (-self.target_dir - self.angle) * 0.3
        self.swing_vel += force * self.app.dt
        self.angle += self.swing_vel * self.app.dt
        if self.flipped:
            self.pos[0] += -math.cos(-self.angle) * self.arm_length
            self.pos[1] += math.sin(-self.angle) * self.arm_length
        else:
            self.pos[0] += math.cos(-self.angle) * self.arm_length
            self.pos[1] += math.sin(-self.angle) * self.arm_length
        self.angle_offset = 90 + (self.target_turn - 90) * self.angle / self.target_dir
        self.swing_vel += (self.swing_vel * self.damp - self.swing_vel) * self.app.dt

        self.arc_end = self.angle
        if self.target_dir == -math.pi * 0.25:
            self.arc_start = math.pi * 0.75
        else:
            self.arc_start = -math.pi * 0.25
    
    def draw_slash(self, surf, scroll):
        if self.attacking:
            draw_arc(surf, (255, 255, 255), self.target.get_rect().center, self.arm_length + self.img.get_height(), self.arc_end * (int(not self.flipped) * 2 - 1), self.arc_start * (int(not self.flipped) * 2 - 1), 3, 20)
    
    def draw(self, surf, scroll):
        img_copy = pygame.transform.rotate(self.img, math.degrees(self.angle) - 90 + self.angle_offset)
        self.flipped = False
        offset = list(self.offset)
        if self.target.flip:
            img_copy = pygame.transform.flip(img_copy, True, False)
            self.flipped = True
            offset[0] -= 3
        alpha = max(0, min(255, 255 - (self.attacked - 30)))
        img_copy.set_alpha(alpha)
        surf.blit(img_copy, (self.pos[0] + int(self.img.get_width() / 2) - int(img_copy.get_width() / 2) - scroll[0] + offset[0], self.pos[1] + int(self.img.get_height() / 2) - int(img_copy.get_height() / 2) - scroll[1] + offset[1]))
        if self.slash:
            self.slash.draw(surf, scroll)
            if self.slash.animation.finished:
                self.slash = None
        self.attack_surf.fill((0, 0, 0, 0))
        if self.attacking and self.slash:
            self.attack_surf.blit(img_copy, (16 + int(self.img.get_width() / 2) - int(img_copy.get_width() / 2) + offset[0], 16 + int(self.img.get_height() / 2) - int(img_copy.get_height() / 2) + offset[1]))
            self.attack_surf.blit(self.slash.img, (16 - self.slash.offset[0], 16 - self.slash.offset[1]))
        self.attack_mask = pygame.mask.from_surface(self.attack_surf)
        self.attack_surf = self.attack_mask.to_surface()
        self.attack_offset = (self.target.pos.x - 16, self.target.pos.y - 16)
        return self.attack_mask, self.attack_offset


class Player:
    def __init__(self, app, dimensions, start_pos, color="black"):
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
        self.speed = 1.0
        self.jump_height = 9 # number of frames we can jump for
        self.jump_strength = 4 # value of movement.y each frame during jump
        self.gravity = 0.3
        self.friction = 0.7
        self.collisions = {"right": False, "left": False, "up": False, "down": False} # useful to keep track of

        self.dead = False # are we dead :)

        # for the animations
        self.flip = False

        self.build_animation(color)

        self.sword = Sword(self.app.assets["player"]["knife"], app, self.pos, self, offset=(0, -5))
        self.shotgun = Shotgun(self.app.assets["player"]["shotgun"], app, self, (0, -10))
        self.mode = "shotgun"
    
    def build_animation(self, color):
        self.color = color
        self.idle = Anim(self.app.assets["player"][self.color]["idle"], 0.1)
        self.run = Anim(self.app.assets["player"][self.color]["run"], 0.2)
        self.jump = Anim(self.app.assets["player"][self.color]["jump"], 0.1, False)
        self.land = Anim(self.app.assets["player"][self.color]["land"], 0.2, False)

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

        if self.mode == "sword":
            self.sword.update()
        elif self.mode == "shotgun":
            self.shotgun.update()
    
    def release_jump(self):
        self.controls["up"] = False
        if self.jumping < self.jump_height:
            self.movement.y *= 0.65
        self.jumping = self.jump_height + 1
    
    def handle_animation(self, dt):
        if self.falling > 3:
            self.jump.update(dt)
            self.idle.reset()
            self.run.reset()
            self.land.reset()
            return self.jump
        if self.controls["left"] or self.controls["right"]:
            self.run.update(dt)
            self.idle.reset()
            self.jump.reset()
            self.land.frame = 23434
            self.land.finished = True
            return self.run
        if not self.land.finished:
            self.land.update(dt)
            return self.land
        self.idle.update(dt)
        self.run.reset()
        self.jump.reset()
        return self.idle

    def draw(self, surf, scroll):
        self.sword.offset = (-4, -4)
        anim = self.handle_animation(self.app.dt)
        anim.flip = self.flip
        # pygame.draw.rect(surf, (255, 0, 0), (self.pos.x - scroll[0], self.pos.y - scroll[1], self.dimensions.x, self.dimensions.y))
        if self.mode == "sword":
            if self.sword.target_dir == -math.pi * 0.25:
                self.sword.draw(surf, scroll)
                anim.draw(surf, scroll, (self.pos.x, self.pos.y))
            else:
                anim.draw(surf, scroll, self.pos)
                self.sword.draw(surf, scroll)
        else:
            anim.draw(surf, scroll, self.pos)
            self.shotgun.draw(surf, scroll)
        # self.sword.draw_slash(surf, scroll)