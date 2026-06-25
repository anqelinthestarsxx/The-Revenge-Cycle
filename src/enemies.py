import pygame, math, random

from .bip import *
from .sparks import *
from .particles import *

from .player import Sword, Pepper, Shotgun
from .anim import Anim

BOUNCE = 0.5
FRICTION = 0.8

class Enemy:
    def __init__(self, app, dimensions, start_pos, num=0):
        self.app = app
        self.num = num
        self.dimensions = pygame.Vector2(dimensions)
        self.pos = pygame.Vector2(start_pos)
        
        self.falling = 23434
        self.grounded = 0
        self.attacking = False

        self.movement = pygame.Vector2(0, 0)
        self.collisions = {"right": False, "left": False, "up": False, "down": False} # useful to keep track of

        self.dead = False # are we dead :)

        # for the animations
        self.flip = False

        self.build_animation(self.app.assets["npc"]["kitchen"]["1"])
        self.img = self.idle.animation[0].copy()

        self.node_radius = self.dimensions.x * 0.35
        self.p1 = {}
        self.p2 = {}

        self.sword = Sword(self.app.assets["player"]["knife"], app, self.pos, self, offset=(0, -5))
        self.shotgun = Shotgun(self.app.assets["player"]["shotgun"], app, self, (0, -10), player=False)
        self.pepper = Pepper(self.app.assets["player"]["pepper"], app, self, (0, 0), player=False)
        self.mode = random.choice(["sword", "shotgun", "pepper"])

        self.gravity = 0.3
        self.friction = 0.7

        self.mood = "passive" # possible: passive, angry, panic
        self.wander = random.random() * 100
        self.wander_dir = round(random.random()) * 2 - 1

        self.last_node = self.app.tile_map.get_closest_node_id(self.get_rect().center)
        self.recalc = 0

        self.hurt_mask = None
        self.hurt_mask = pygame.mask.from_surface(self.img)
        self.mask_surf = self.hurt_mask.to_surface(setcolor=(0, 0, 0, 0), unsetcolor=(0, 255, 0))

        self.scribble_surf = pygame.Surface(self.img.get_size(), pygame.SRCALPHA).convert_alpha()
        self.scribble_surf.blit(self.mask_surf, (0, 0))
        self.scribble_surf.set_colorkey((0, 255, 0))

        self.pause_time = 0
        self.verlet_timer = 0

    
    def build_animation(self, dictionary):
        self.asset_dict = dictionary
        self.idle = Anim(dictionary["idle"], 0.1)
        self.run = Anim(dictionary["run"], 0.1)
        self.jump = Anim(dictionary["jump"], 0.1, False)
        self.land = Anim(dictionary["land"], 0.2, False)
        self.punch = Anim(dictionary["punch"], 0.4, False)
    
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
        if abs(self.movement.x) > 0.1:
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

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)
    
    def die(self, impact: pygame.Vector2, impact_point: pygame.Vector2):
        if not self.dead:
            impact = pygame.Vector2(impact)
            impact_point = pygame.Vector2(impact_point)
            self.dead = True

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
            for _ in range(random.randint(20, 30)):
                angle = 2 * math.pi * random.random()
                speed = random.random() * 4 - 2
                self.app.kickup.append([list(kpos), [math.cos(angle) * speed, math.sin(angle) * speed * 2], random.random() * 0.05 + 2, random.choice([(237, 82, 89), (196, 44, 54), (120, 31, 44)])])
            for _ in range(random.randint(15, 25)):
                angle = random.random() * math.pi * 2
                speed = random.random() * 3 + 3
                self.app.sparks.append(
                    Spark(list(kpos), angle, speed, random.choice([(237, 82, 89), (196, 44, 54)]))
                )
            for _ in range(random.randint(30, 40)):
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
            
            for enemy in self.app.enemies:
                if enemy.num != self.num:
                    if self.pos.distance_squared_to(enemy.pos) < (TILE_SIZE * 10) ** 2 and enemy.mood != "angry":
                        if enemy.mood == "panic":
                            enemy.mood = "angry"
                        else:
                            enemy.mood = random.choice(["panic", "angry"])

    def update(self, dt):
        self.verlet_timer += dt
        if self.mode == "sword":
            self.sword.update()
        elif self.mode == "shotgun":
            self.shotgun.angle = math.atan2(-(self.app.player.get_rect().centery - self.get_rect().centery), self.app.player.get_rect().centerx - self.get_rect().centerx) - math.pi * 0.5
            self.shotgun.flipped = self.app.player.get_rect().centerx > self.get_rect().centerx
            self.shotgun.update()
        elif self.mode == "pepper":
            self.pepper.update()
        if self.dead:
            if self.verlet_timer < 1:
                return
            self.verlet_timer = 0
            # print(self.get_dead_midpoint())
            # print(self.p1, self.p2)
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

        else:
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
                        self.collisions["down"] = True
                    elif fm.y < 0:
                        r.top = rect.bottom
                        self.collisions["up"] = True
                    self.movement.y = 0
                    self.pos.y = r.y
            
            # update movemen
            self.movement.x *= self.friction ** dt

            self.movement.y += self.gravity * dt
            self.movement.y = min(self.movement.y, 24)

            # one more time for dangerous stuff
            r = self.get_rect()
            for rect in self.app.tile_map.danger_rects_around(self.get_rect().center):
                if rect.colliderect(r):
                    self.die(pygame.Vector2(0, 0))
                    return
                
            if self.mood == "angry" and self.sword.attacking and self.mode == "sword" and not self.app.player.attacking and not self.app.player.sword.attacking:
                if self.app.player.collide_mask(self.sword.attack_mask, self.sword.attack_offset):
                    self.app.player.die(pygame.Vector2(2, 2), (pygame.Vector2(self.app.player.get_rect().center) + pygame.Vector2(self.get_rect().center)) * 0.5)
            
            if self.app.player.sword.attacking and self.app.player.mode == "sword":
                if self.collide_mask(self.app.player.sword.attack_mask, self.app.player.sword.attack_offset):
                    self.die(pygame.Vector2(2, 2), (pygame.Vector2(self.app.player.get_rect().center) + pygame.Vector2(self.get_rect().center)) * 0.5)
            if self.app.player.mode == "fists" and self.app.player.attacking:
                if self.get_rect().colliderect(self.app.player.get_attack_rect()):
                    self.die(pygame.Vector2(2, 2), (pygame.Vector2(self.app.player.get_rect().center) + pygame.Vector2(self.get_rect().center)) * 0.5)
            
            if self.app.player.dead:
                self.mood = "passive"
            
            if self.mood == "passive":
                # do idle stuff (chill)
                self.wander += self.app.dt
                if self.wander_dir > 0:
                        self.flip = False
                elif self.wander_dir < 0:
                        self.flip = True
                if self.wander > 240:
                    self.wander = random.random() * 200
                    if abs(self.wander_dir) > 0:
                        self.wander_dir = 0
                    else:
                        self.wander_dir = random.choice([-1, 1])
                    if self.wander_dir > 0:
                        self.flip = False
                    elif self.wander_dir < 0:
                        self.flip = True
                    else:
                        self.wander = 0
                self.movement.x += self.wander_dir * 0.1 * self.app.dt
                if self.movement.x < 0:
                    self.flip = True
                if self.app.tile_map.solid_check((self.get_rect().centerx + TILE_SIZE, self.get_rect().bottom - 1)) or self.app.tile_map.solid_check((self.get_rect().centerx - TILE_SIZE, self.get_rect().bottom - 1)):
                    if self.wander > 40:
                        self.wander = 0
                        self.wander_dir *= -1
            elif self.mood == "panic":
                self.wander += self.app.dt
                if self.wander_dir == 0:
                    self.wander_dir = random.choice([-1, 1])
                self.movement.x += self.wander_dir * 0.4 * self.app.dt
                if self.movement.x < 0:
                    self.flip = True
                else:
                    self.flip = False
                if self.app.tile_map.solid_check((self.get_rect().centerx + TILE_SIZE, self.get_rect().bottom - 1)) or self.app.tile_map.solid_check((self.get_rect().centerx - TILE_SIZE, self.get_rect().bottom - 1)) or (abs(self.app.player.get_rect().centerx - self.get_rect().centerx) < 50 and abs(self.app.player.get_rect().centery - self.get_rect().centery) < 64):
                    if self.wander > 40:
                        self.wander = 0
                        self.wander_dir *= -1
            elif self.mood == "angry":
                self.follow_player()
                if self.mode == "sword":
                    # follow player
                    pass
                elif self.mode == "shotgun":
                    # follow player until certain distance then shoot
                    pass
                elif self.mode == "pepper":
                    # same as sword but fire occasionally
                    pass
    
    def follow_player(self):
        self.pause_time += self.app.dt
        pause = False
        if self.pause_time > 150:
            self.pause_time = random.random() * 60
            pause = True
        
        if pause:
            if self.mode == "shotgun":
                self.shotgun.shoot()
                return
            elif self.mode == "pepper":
                self.pepper.shoot(self.app.player.get_rect().center, speed=7)
            
        self.recalc += self.app.dt
        if self.recalc > 120:
            self.last_node = self.app.tile_map.get_closest_node_id(self.get_rect().center)
            self.recalc = 0
        tree_dir = 0
        if self.last_node < self.app.player.current_node:
            tree_dir = 1
        elif self.last_node > self.app.player.current_node:
            tree_dir = -1

        gcx = self.get_rect().centerx
        gcy = self.get_rect().top
        speed = 0.5
        if tree_dir == 0:
            # follow player directly
            pcx = self.app.player.get_rect().centerx
            if abs(pcx - gcx) > TILE_SIZE:
                if pcx > gcx:
                    self.movement.x += speed * self.app.dt
                    self.flip = False
                else:
                    self.movement.x -= speed * self.app.dt
                    self.flip = True
            elif self.mode == "sword":
                if self.sword.attacked > 12:
                    self.sword.attack(  )
                self.sword.update()
        else:
            target_node = self.app.tile_map.path_nodes[self.last_node + tree_dir]
            if gcx > target_node[0]:
                self.movement.x -= speed * self.app.dt
                self.flip = True
            else:
                self.movement.x += speed * self.app.dt
                self.flip = False
            if gcy > target_node[1]:
                if self.falling < 3:
                    self.movement.y = -5
            if pygame.geometry.Circle(target_node[0], target_node[1], TILE_SIZE).colliderect(self.get_rect()):
                self.last_node += tree_dir
                
    
    def collide_mask(self, mask, pos):
        if not self.hurt_mask:
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
            if self.mood == "angry":
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
            # pygame.draw.circle(surf, (255, 255, 0), (self.p1['x'], self.p1['y']), self.node_radius)
            # pygame.draw.circle(surf, (255, 255, 0), (self.p2['x'], self.p2['y']), self.node_radius)