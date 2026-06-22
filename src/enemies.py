import pygame, math, random

from .bip import *
from .sparks import *
from .particles import *

BOUNCE = 0.8
FRICTION = 0.9

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

        self.img = app.assets["placeholder"].copy()

        self.node_radius = self.dimensions.x * 0.5
        self.p1 = {}
        self.p2 = {}

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)
    
    def die(self, impact: pygame.Vector2, impact_point: pygame.Vector2):
        if not self.dead:
            impact = pygame.Vector2(impact)
            impact_point = pygame.Vector2(impact_point)
            self.dead = True

            force = min(impact.length(), 16)
            p1 = pygame.Vector2(self.pos.x + self.node_radius, self.pos.y + self.node_radius)
            angle = math.atan2(p1.y - impact_point.y, p1.x - impact_point.x)
            self.p1 = {"x": p1[0], "y": p1[1], "oldx": p1[0] - math.cos(angle) * force, "oldy": p1[1] - math.sin(angle) * force}
            p2 = pygame.Vector2(self.pos.x + self.node_radius, self.pos.y + self.dimensions.y - self.node_radius)
            angle = math.atan2(p2.y - impact_point.y, p2.x - impact_point.x)
            self.p2 = {"x": p2[0], "y": p2[1], "oldx": p2[0] - math.cos(angle) * force, "oldy": p2[1] - math.sin(angle) * force}

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

    def update(self, dt):
        if self.dead:
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
                p['x'] += vx * dt
                p['y'] += vy * dt
                p['y'] += 2 * dt * dt

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
                            distance = 0.001
                            dx = self.node_radius
                        overlap = self.node_radius - distance
                        nx = dx / distance
                        ny = dy / distance
                        p['x'] += nx * overlap
                        p['y'] += ny * overlap

                        if abs(nx) > abs(ny):
                            p['oldx'] = p['x'] + vx * BOUNCE
                            p['oldy'] = p['y'] - vy * FRICTION
                        else:
                            p['oldy'] = p['y'] + vy * BOUNCE
                            p['oldx'] = p['x'] - vx * FRICTION

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
            
            # update movement
            self.movement.y += 0.3 * dt

            # one more time for dangerous stuff
            r = self.get_rect()
            for rect in self.app.tile_map.danger_rects_around(self.get_rect().center):
                if rect.colliderect(r):
                    self.die(pygame.Vector2(0, 0))
                    return
            
            if self.app.player.sword.attacking:
                if self.collide_mask(self.app.player.sword.attack_mask, self.app.player.sword.attack_offset):
                    self.die(pygame.Vector2(5, 5), self.app.player.get_rect().center)
    
    def collide_mask(self, mask, pos):
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
        if not self.dead:
            surf.blit(self.img, (self.pos.x - scroll[0], self.pos.y - scroll[1]))
        else:
            deg = self.get_dead_angle()
            
            img_copy = pygame.transform.rotate(self.img, deg)

            midpoint = self.get_dead_midpoint()
            
            surf.blit(img_copy, (midpoint.x - (img_copy.get_width() / 2) - scroll[0], midpoint.y - (img_copy.get_height() / 2) - scroll[1]))
            # pygame.draw.circle(surf, (255, 255, 0), (self.p1['x'], self.p1['y']), self.node_radius)
            # pygame.draw.circle(surf, (255, 255, 0), (self.p2['x'], self.p2['y']), self.node_radius)