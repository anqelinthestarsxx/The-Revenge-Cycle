import pygame, math, time, random

from .anim import Anim
from .util import draw_arc
from .bip import *
from .particles import *
from .sparks import *

import pygame.geometry

BOUNCE = 0.5
FRICTION = 0.8

class Pepper:
    def __init__(self, img, app, target, offset, player=False):
        self.img = img.copy()
        self.app = app
        self.pos = pygame.Vector2(target.get_rect().center)
        self.offset = list(offset)

        self.target = target

        self.timer = 234234
        self.cooldown = 30

        self.peppers = []

        self.gravity = 0.4
        self.explode_radius = 4

        self.player = player
    
    def explode(self, pos, vel):
        self.app.assets["sfx"]["explosion0"].play()
        self.app.assets["sfx"]["fire"].play()
        self.app.screen_shake = max(self.app.screen_shake, 8)
        circle = pygame.geometry.Circle(pos[0], pos[1], self.explode_radius)
        for _ in range(random.randint(20, 30)):
            spread = 5
            self.app.particles.append(Particle(self.app, "explosion", [pos[0] + random.random() * spread - spread / 2, pos[1] + random.random() * spread - spread / 2], [random.random() - 0.5, random.random() * -1 - 0.5], random.random(), False))
            self.app.particles[-1].speed = 0.3
            self.app.particles[-1].decay = 50
        for _ in range(random.randint(30, 30)):
            angle = math.pi * 2 * random.random()
            speed = random.random() * 0.5 + 0.25
            self.app.smoke.append([list(pos),[math.cos(angle) * speed, math.sin(angle) * speed], 1, random.randint(200, 255), 0, random.randint(0, 360), random.choice([(163, 172, 190)])])
        kpos = pygame.Vector2(pos)
        while self.app.tile_map.solid_check(kpos):
            kpos -= pygame.Vector2(vel) * 0.2
        for _ in range(random.randint(20, 30)):
            angle = 2 * math.pi * random.random()
            speed = random.random() * 4 - 2
            self.app.kickup.append([list(kpos), [math.cos(angle) * speed, math.sin(angle) * speed * 2], random.random() * 0.05 + 2, random.choice([(80, 155, 75), (237, 82, 89), (196, 44, 54), (120, 31, 44)])])
        for _ in range(random.randint(30, 30)):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.app.particles.append(Particle(self.app, 'particle', list(kpos), [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], random.randint(0, 7)))
            self.app.particles[-1].speed += 0.1
            self.app.cinders.append([list(kpos), [math.cos(angle) * speed, math.sin(angle) * speed], random.randint(2, 20), (251, 223, 107)])
        for _ in range(random.randint(20, 30)):
            angle = random.random() * math.pi * 2
            speed = random.random() * 3 + 3
            self.app.sparks.append(
                Spark(list(kpos), angle, speed, random.choice([(237, 82, 89), (196, 44, 54)]), scale=1)
            )
        vn = pygame.Vector2(vel).normalize()
        for _ in range(15):
            angle = (random.random() - 0.5) * math.pi
            speed = random.random() * 3
            self.app.slime.append([list(kpos), list(vn.rotate_rad(angle) * speed), (20, 16, 32)])
        for _ in range(20):
            angle = random.random() * math.pi * 2
            pvel = random.random() * 5 
            self.app.splat.append([list(kpos), [math.cos(angle) * pvel, math.sin(angle) * pvel], random.choice([(196, 44, 54), (123, 207, 92)]), 3])
        
        if self.player:
            for enemy in self.app.enemies:
                if circle.colliderect(enemy.get_rect()) and not enemy.dead:
                    enemy.die(pygame.Vector2(vel), pos)
        else:
            if circle.colliderect(self.app.player.get_rect()) and not self.app.player.dead:
                self.app.player.death_message = random.choice(["was reduced to a sizzling spicy corpse.", "was shown some chilli power!", "felt a sharp burst, then everything went red..."])
                self.app.player.die(pygame.Vector2(vel), pos)
    
    def shoot(self, pos, speed=9):
        if self.timer < self.cooldown or self.target.dead:
            return

        start = list(self.pos)
        start[0] += self.offset[0]
        start[1] += self.offset[1]
        dx = pos[0] - start[0]
        dy = pos[1] - start[1]
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance == 0:
            distance = 1
        
        t = distance / speed
        vx = dx / t
        vy = (dy - (0.5 * self.gravity * t * t)) / t
        vel = [vx, vy]
        self.timer = 0

        self.peppers.append([start, vel, 0, 0])
        self.app.assets["sfx"]["button"].play()
    
    def update(self):
        self.timer += self.app.dt
        if self.target:
            self.pos = pygame.Vector2(self.target.get_rect().center)

            if self.target.flip:
                self.offset[0] = -9
            else:
                self.offset[0] = 1

    def draw(self, surf, scroll):
        if not self.target.dead:
            alpha = min(1, self.timer / self.cooldown) * 255
            self.img.set_alpha(alpha)
            surf.blit(self.img, (self.pos.x - scroll[0] + self.offset[0], self.pos.y - scroll[1] + self.offset[1] + math.sin(time.time() * 5) * 2))

        self.img.set_alpha(255)
        for p in self.peppers.copy():
            kill = False
            p[1][1] += self.gravity * self.app.dt
            p[0][0] += p[1][0] * self.app.dt
            p[0][1] += p[1][1] * self.app.dt

            circle = pygame.geometry.Circle(p[0][0], p[0][1], 2)
            if self.player:
                for enemy in self.app.enemies:
                    if circle.colliderect(enemy.get_rect()) and not enemy.dead:
                        kill = True
                        self.explode(p[0], p[1])
            else:
                if circle.colliderect(self.app.player.get_rect()) and not self.app.player.dead:
                    kill = True
                    self.explode(p[0], p[1])

            if self.app.tile_map.solid_check(p[0]):
                kill = True
                self.explode(p[0], p[1])

            p[2] += self.app.dt * 5 # make it spin
            p[3] += self.app.dt

            if p[3] > 1000:
                kill = True
            
            if kill:
                self.peppers.remove(p)
            else:
                img_copy = pygame.transform.rotate(self.img, p[2])
                surf.blit(img_copy, (p[0][0] + (self.img.get_width() / 2) - img_copy.get_width() / 2 - scroll[0], p[0][1] + self.img.get_height() / 2 - img_copy.get_height() / 2 - scroll[1]))


class Shotgun:
    def __init__(self, img, app, target, offset, player=False):
        self.img = img.copy()
        self.app = app
        self.pos = pygame.Vector2(target.get_rect().center)
        self.offset = offset

        self.angle = 0
        self.rebound = 0
        self.rebound_vel = 0
        self.flipped = False
        self.target = target

        self.bullets = []
    
        self.timer = 1234
        self.cooldown = 10

        self.player = player
    
    def shoot(self):
        if self.timer <= self.cooldown or self.target.dead:
            return
        self.timer = 0
        offset = list(self.offset)
        if not self.flipped:
            offset[0] -= 4
        angle = -float(self.angle + math.pi * 0.5)
        pos = [self.target.get_rect().centerx + math.cos(angle) * self.img.get_height() / 2, self.target.get_rect().centery + 4 + math.sin(angle) * self.img.get_height() / 2]
        self.bullets.append([list(pos), angle, 0])
        self.rebound = -5
        self.target.movement += pygame.Vector2(self.rebound * math.cos(angle), self.rebound * math.sin(angle)) * 0.4

        for _ in range(random.randint(10, 15)):
            spread = 1
            self.app.particles.append(Particle(self.app, "explosion", [pos[0] + 1, pos[1] + 1], [math.cos(angle) * 3, math.sin(angle) * 3], random.random(), False))
            self.app.particles[-1].speed = 2
            self.app.particles[-1].decay = 50
            self.app.sparks.append(Spark([pos[0] + 1, pos[1] + 1], angle +( random.random() - 0.5) * 0.25, random.random() * 3, (219, 224, 231)))
        
        self.app.assets["sfx"]["shoot"].play()
    
    def update(self):
        self.timer += self.app.dt
        if self.target:
            self.pos = pygame.Vector2(self.target.get_rect().center)
        
        self.rebound_vel += (0 - self.rebound) * 0.3 * self.app.dt
        self.rebound += self.rebound_vel * self.app.dt
        self.rebound_vel *= 0.3 ** self.app.dt
    
    def draw(self, surf, scroll):
        speed = 4
        bullet_img = self.app.assets["player"]["bullet"]
        for bullet in self.bullets.copy():
            kill = False
            bullet[0][0] += math.cos(bullet[1]) * speed
            bullet[0][1] += math.sin(bullet[1]) * speed

            if self.app.tile_map.solid_check(bullet[0]):
                self.app.assets["sfx"]["bullet_hit"].play()
                kill = True
            else:
                if self.player:
                    for enemy in self.app.enemies:
                        if enemy.get_rect().collidepoint(bullet[0][0], bullet[0][1]) and not enemy.dead:
                            kill = True
                            force = 1
                            enemy.die(pygame.Vector2(math.cos(bullet[1]) * speed * force, math.sin(bullet[1]) * speed * force), pygame.Vector2(bullet[0]))
                            self.app.assets["sfx"]["shoot"].play()
                            self.app.assets["sfx"]["explosion1"].play()
                else:
                    if self.app.player.get_rect().collidepoint(bullet[0][0], bullet[0][1]) and not self.app.player.dead:
                        kill = True
                        force = 1
                        self.app.player.death_message = random.choice(["was shot like a dog.", "got their belly pumped full of lead.", "ate buckshot."])
                        self.app.player.die(pygame.Vector2(math.cos(bullet[1]) * speed * force, math.sin(bullet[1]) * speed * force), pygame.Vector2(bullet[0]))
                        self.app.assets["sfx"]["shoot"].play()
                        self.app.assets["sfx"]["explosion1"].play()

            bullet[2] += self.app.dt
            if bullet[2] > 240:
                kill = True
            
            if kill:
                for _ in range(random.randint(10, 15)):
                    spread = 1
                    pos = bullet[0]
                    angle = bullet[1]
                    self.app.particles.append(Particle(self.app, "explosion", [pos[0] + 1, pos[1] + 1], [math.cos(angle) * 3, math.sin(angle) * 3], random.random(), False))
                    self.app.particles[-1].speed = 2
                    self.app.particles[-1].decay = 50
                    self.app.sparks.append(Spark([pos[0] + 1, pos[1] + 1], angle +( random.random() - 0.5) * 0.25, random.random() * 3, (219, 224, 231)))
                self.bullets.remove(bullet)
            else:
                img_copy = pygame.transform.rotate(bullet_img, math.degrees(bullet[1]))
                surf.blit(bullet_img, (bullet[0][0] + int(bullet_img.get_width() / 2) - int(img_copy.get_width() / 2) - scroll[0], bullet[0][1] + int(bullet_img.get_height() / 2) - int(img_copy.get_height() / 2) - scroll[1])) 
                
        if self.target.dead:
            return
        offset = list(self.offset)
        if not self.flipped:
            offset[0] -= 4
        img_copy = pygame.transform.rotate(pygame.transform.flip(self.img, not self.flipped, False), math.degrees(self.angle))
        angle = -float(self.angle + math.pi * 0.5)
        surf.blit(img_copy, (self.pos[0] + int(self.img.get_width() / 2) - int(img_copy.get_width() / 2) - scroll[0] + offset[0] + math.cos(angle) * self.rebound, self.pos[1] + int(self.img.get_height() / 2) - int(img_copy.get_height() / 2) - scroll[1] + offset[1] + math.sin(angle) * self.rebound))
        

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
        self.attack_surf = pygame.Surface((64, 64))
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
        if self.attacking:
            fuzziness = 2
            for o in {(-1, 0), (1, 0), (0, 1), (0, -1)}:
                self.attack_surf.blit(img_copy, (32 + int(self.img.get_width() / 2) - int(img_copy.get_width() / 2) + offset[0] + o[0] * fuzziness, 32 + int(self.img.get_height() / 2) - int(img_copy.get_height() / 2) + offset[1] + o[1] * fuzziness))
        self.attack_mask = pygame.mask.from_surface(self.attack_surf)
        self.attack_surf = self.attack_mask.to_surface()
        self.attack_offset = (self.pos[0] - 32, self.pos[1] - 32)
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
        self.shotgun = Shotgun(self.app.assets["player"]["shotgun"], app, self, (0, -10), player=True)
        self.pepper = Pepper(self.app.assets["player"]["pepper"], app, self, (0, 0), player=True)
        self.mode = "shotgun"

        self.attacking = False

        self.node_radius = self.dimensions.x * 0.4
        self.p1 = {}
        self.p2 = {}

        self.img = self.idle.animation[0].copy()
        self.hurt_mask = None
        self.hurt_mask = pygame.mask.from_surface(self.img)
        self.mask_surf = self.hurt_mask.to_surface(setcolor=(0, 0, 0, 0), unsetcolor=(0, 255, 0))

        self.scribble_surf = pygame.Surface(self.img.get_size(), pygame.SRCALPHA).convert_alpha()
        self.scribble_surf.blit(self.mask_surf, (0, 0))
        self.scribble_surf.set_colorkey((0, 255, 0))

        self.current_node = self.app.tile_map.get_closest_node_id(self.pos)

        self.verlet_timer = 0

        self.finished = False

        self.death_message = ""
    
    def die(self, impact: pygame.Vector2, impact_point: pygame.Vector2):
        if not self.dead:
            if self.color == "black":
                self.app.assets["sfx"]["pain2"].play()
            else:
                self.app.assets["sfx"]["pain3"].play()

            impact = pygame.Vector2(impact)
            impact_point = pygame.Vector2(impact_point)
            self.dead = True
            self.app.fade_dir = 1

            self.app.slomo = 0.1

            force = min(impact.length(), 16)
            p1 = pygame.Vector2(self.pos.x + self.node_radius, self.pos.y + self.node_radius)
            angle = math.atan2(p1.y - impact_point.y, p1.x - impact_point.x)
            self.p1 = {"x": p1[0], "y": p1[1], "oldx": p1[0] - math.cos(angle) * force - self.movement.x, "oldy": p1[1] - math.sin(angle) * force - self.movement.y}
            p2 = pygame.Vector2(self.pos.x + self.node_radius, self.pos.y + self.dimensions.y - self.node_radius)
            angle = math.atan2(p2.y - impact_point.y, p2.x - impact_point.x)
            self.p2 = {"x": p2[0], "y": p2[1], "oldx": p2[0] - math.cos(angle) * force - self.movement.x, "oldy": p2[1] - math.sin(angle) * force - self.movement.y}

            self.app.screen_shake = max(self.app.screen_shake, 16)
            kpos = list(impact_point)
            while self.app.tile_map.solid_check(kpos):
                kpos[1] -= 2
            for _ in range(random.randint(40, 60)):
                angle = 2 * math.pi * random.random()
                speed = random.random() * 4 - 2
                self.app.kickup.append([list(kpos), [math.cos(angle) * speed, math.sin(angle) * speed * 2], random.random() * 0.05 + 2, random.choice([(237, 82, 89), (196, 44, 54), (120, 31, 44)])])
            for _ in range(random.randint(20, 30)):
                angle = random.random() * math.pi * 2
                speed = random.random() * 3 + 3
                self.app.sparks.append(
                    Spark(list(kpos), angle, speed, random.choice([(237, 82, 89), (196, 44, 54)]))
                )
            for _ in range(random.randint(50, 60)):
                angle = random.random() * math.pi * 2
                speed = random.random() * 5
                self.app.particles.append(Particle(self.app, 'particle', list(kpos), [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], random.randint(0, 7)))
                self.app.particles[-1].speed += 0.1
                self.app.cinders.append([list(kpos), [math.cos(angle) * speed, math.sin(angle) * speed], random.randint(2, 20), random.choice([(237, 82, 89), (196, 44, 54), (120, 31, 44)])])
            for _ in range(15):
                angle = random.random() * math.pi * 2
                speed = random.random() * 5
                self.app.slime.append([pygame.Vector2(kpos) + pygame.Vector2(random.random() * 10 - 5, random.random() * 10 - 5), [math.cos(angle) * speed, math.sin(angle) * speed], random.choice([(237, 82, 89), (196, 44, 54), (120, 31, 44)])])
            angle = random.random() * math.pi * 2
            vel = random.random() * 2.5 + 7.4
            self.app.splat.append([pygame.Vector2(kpos), [math.cos(angle) * vel, math.sin(angle) * vel], random.choice([(237, 82, 89), (196, 44, 54), (120, 31, 44)]), 3])
            self.app.slime.append([pygame.Vector2(kpos) + pygame.Vector2(random.random() * 10 - 5, random.random() * 10 - 5), [math.cos(angle) * speed, math.sin(angle) * speed], random.choice([(237, 82, 89), (196, 44, 54), (120, 31, 44)])])
            for _ in range(random.randint(50, 60)):
                angle = random.random() * math.pi * 2
                vel = random.random() * 2.5 + 7.4
                self.app.splat.append([pygame.Vector2(kpos) + pygame.Vector2(random.random() * 10 - 5, random.random() * 10 - 5), [math.cos(angle) * vel, math.sin(angle) * vel], random.choice([(237, 82, 89), (196, 44, 54), (120, 31, 44)]), 3])
            for _ in range(random.randint(30, 50)):
                angle = math.pi * 2 * random.random()
                speed = random.random()
                self.app.smoke.append([list(kpos),[math.cos(angle) * speed, math.sin(angle) * speed], 1, random.randint(200, 255), 0, random.randint(0, 360), random.choice([(237, 82, 89), (196, 44, 54), (120, 31, 44)])])

    def get_attack_rect(self):
        return pygame.Rect(self.get_rect().centerx - 15 * int(self.flip), self.pos.y + 10, 15, self.dimensions.y - 10)
    
    def build_animation(self, color):
        self.color = color
        self.idle = Anim(self.app.assets["player"][self.color]["idle"], 0.1)
        self.run = Anim(self.app.assets["player"][self.color]["run"], 0.2)
        self.jump = Anim(self.app.assets["player"][self.color]["jump"], 0.1, False)
        self.land = Anim(self.app.assets["player"][self.color]["land"], 0.2, False)
        self.punch = Anim(self.app.assets["player"][self.color]["punch"], 0.4, False)

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)
    
    def update(self, dt):
        self.verlet_timer += dt
        self.current_node = self.app.tile_map.get_closest_node_id(self.pos)
        if self.mode == "sword":
            self.sword.update()
        elif self.mode == "shotgun":
            self.shotgun.update()
        elif self.mode == "pepper":
            self.pepper.update()
        if self.dead:
            if self.verlet_timer < 1:
                return
            self.verlet_timer = 0
            vels = []
            for p in [self.p1, self.p2]:
                vx = (p['x'] - p['oldx'])
                vx = min(16, max(-16, vx))
                vy = (p['y'] - p['oldy'])
                vy = min(16, max(-16, vy))
                vels.append((vx, vy))
                p['oldx'] = p['x']
                p['oldy'] = p['y']
                p['x'] += vx
                p['y'] += vy
                p['y'] += 2

            dx, dy = self.p1['x'] - self.p2['x'], self.p1['y'] - self.p2['y']
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance < 0.1:
                self.p1['x'] += random.choice([-1, 1])
                self.p2['y'] += random.choice([-1, 1])
                dx, dy = self.p1['x'] - self.p2['x'], self.p1['y'] - self.p2['y']
                distance = math.sqrt(dx ** 2 + dy ** 2)
            difference = (self.dimensions.y - self.node_radius * 2) - distance
            percentage = difference / max(0.001, distance) * 0.5
            offset_x = dx * percentage
            offset_y = dy * percentage
            offset_x = pygame.math.clamp(offset_x, -(self.dimensions.y - self.node_radius * 2), self.dimensions.y - self.node_radius * 2)
            offset_y = pygame.math.clamp(offset_y, -(self.dimensions.y - self.node_radius * 2), self.dimensions.y - self.node_radius * 2)
            self.p1['x'] += offset_x
            self.p1['y'] += offset_y
            self.p2['x'] -= offset_x
            self.p2['y'] -= offset_y

            for p, (vx, vy) in zip([self.p1, self.p2], vels):
                # constrain
                for rect in self.app.tile_map.physics_rects_around([p['x'], p['y']]):
                    cx = max(rect.left, min(p['x'], rect.right))
                    cy = max(rect.top, min(p['y'], rect.bottom))

                    dx = p['x'] - cx
                    dy = p['y'] - cy
                    distance = math.sqrt(dx ** 2 + dy ** 2)
                    if distance < self.node_radius:
                        if distance == 0:
                            nx = 0
                            ny = -1
                            overlap = self.node_radius
                        else:
                            overlap = self.node_radius - distance
                            nx = dx / distance
                            ny = dy / distance

                        vx = p['x'] - p['oldx']
                        vy = p['y'] - p['oldy']

                        p['x'] += nx * overlap
                        p['y'] += ny * overlap

                        if abs(nx) > abs(ny):
                            p['oldx'] = p['x'] + (vx * BOUNCE)
                            p['oldy'] = p['y'] - (vy * FRICTION)
                        else:
                            p['oldy'] = p['y'] + (vy * BOUNCE)
                            p['oldx'] = p['x'] - (vx * FRICTION)
            return
        
        # ----- collision handling ----- #
        self.collisions = {"right": False, "left": False, "down": False, "up": False}
        
        # frame movement
        fm = pygame.Vector2(self.movement.x * dt, self.movement.y * dt)

        # first do x-axis movement
        self.pos.x += fm.x

        if not self.app.level_complete:
            self.pos.x = max(0, min(TILE_SIZE * CHUNK_SIZE * LEVEL_WIDTH - self.dimensions.x, self.pos.x))
        elif not self.finished:
            if self.color == "black":
                self.pos.x = max(0, self.pos.x)
                if self.pos.x > TILE_SIZE * CHUNK_SIZE * LEVEL_WIDTH:
                    self.finished = True
                    self.app.assets["sfx"]["vanish"].play()
            elif self.color == "white":
                self.pos.x = min(TILE_SIZE * CHUNK_SIZE * LEVEL_WIDTH - self.dimensions.x, self.pos.x)
                if self.pos.x < -self.dimensions.x:
                    self.finished = True
                    self.app.assets["sfx"]["vanish"].play()
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
    
    def handle_animation(self, dt):
        if self.attacking:
            self.punch.update(dt)
            self.jump.reset()
            self.idle.reset()
            self.run.reset()
            if self.punch.finished:
                self.attacking = False
            else:
                return self.punch
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
    
    def collide_mask(self, mask, pos):
        if self.hurt_mask is None:
            self.hurt_mask = pygame.mask.from_surface(self.img)
        offset = (pos[0] - self.pos.x, pos[1] - self.pos.y)
        return self.hurt_mask.overlap(mask, offset)

    def get_dead_midpoint(self):
        return pygame.Vector2(
            (self.p1['x'] + self.p2['x']) * 0.5,
            (self.p1['y'] + self.p2['y']) * 0.5
        )

    def get_dead_angle(self):
        angle = math.atan2(self.p1['y'] - self.p2['y'], self.p1['x'] - self.p2['x'])
        return -math.degrees(angle) - 90
    
    def particle_check(self, pos):
        if not self.dead:
            return self.get_rect().collidepoint(pos), (pos[0] - self.pos.x, pos[1] - self.pos.y)
        mp = self.get_dead_midpoint()
        angle_rad = math.radians(-self.get_dead_angle() + 90)
        dx = pos[0] - mp.x
        dy = pos[1] - mp.y

        c = math.cos(-angle_rad)
        s = math.sin(-angle_rad)

        x = dx * c - dy * s
        y = dx * s + dy * c

        if -self.img.get_width() / 2 <= x <= self.img.get_width() * 0.5 and -self.img.get_height() * 0.5 <= y <= self.img.get_height() * 0.5:
            return True, (x + self.img.get_width() * 0.5, y + self.img.get_height() * 0.5)
        return False, None

    def draw(self, surf, scroll):
        self.scribble_surf.blit(self.mask_surf, (0, 0))
        self.scribble_surf.set_colorkey((0, 255, 0))
        ss = pygame.transform.flip(self.scribble_surf, self.flip, False)
        if not self.dead:
            self.sword.offset = (-4, -4)
            offset = pygame.Vector2(-3, 0)
            anim = self.handle_animation(self.app.dt)
            anim.flip = self.flip
            # pygame.draw.rect(surf, (255, 0, 0), (self.pos.x - scroll[0], self.pos.y - scroll[1], self.dimensions.x, self.dimensions.y))
            # if self.sword.attacking:
            # pygame.draw.rect(surf, (255, 0, 0), self.get_attack_rect())
            if self.mode == "sword":
                if self.sword.angle > 0:
                    self.sword.draw(surf, scroll)
                    anim.draw(surf, scroll, (self.pos.x + offset.x, self.pos.y + offset.y))
                    surf.blit(ss, self.pos + offset - pygame.Vector2(scroll))
                else:
                    anim.draw(surf, scroll, self.pos + offset)
                    surf.blit(ss, self.pos + offset - pygame.Vector2(scroll))
                    self.sword.draw(surf, scroll)
            elif self.mode == "shotgun":
                anim.draw(surf, scroll, self.pos + offset)
                surf.blit(ss, self.pos + offset - pygame.Vector2(scroll))
                self.shotgun.draw(surf, scroll)
            elif self.mode == "pepper":
                anim.draw(surf, scroll, self.pos + offset)
                surf.blit(ss, self.pos + offset - pygame.Vector2(scroll))
                self.pepper.draw(surf, scroll)
            else:
                if self.attacking:
                    offset = pygame.Vector2(-12, 0)
                anim.draw(surf, scroll, self.pos + offset)
                surf.blit(ss, self.pos + offset - pygame.Vector2(scroll))
        else:
            deg = self.get_dead_angle()
            
            img = pygame.transform.flip(self.img, self.flip, False)
            img.blit(ss, (0, 0))
            img_copy = pygame.transform.rotate(img, deg)

            midpoint = self.get_dead_midpoint()
            
            surf.blit(img_copy, (midpoint.x - (img_copy.get_width() / 2) - scroll[0], midpoint.y - (img_copy.get_height() / 2) - scroll[1]))
            if self.mode == "shotgun":
                self.shotgun.draw(surf, scroll)
            elif self.mode == "pepper":
                self.pepper.draw(surf, scroll)
        # self.sword.draw_slash(surf, scroll)
