import pygame, math

from .bip import *

BOUNCE = 0.5
FRICTION = 0.999

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

        self.img = app.assets["placeholder"]

        self.node_radius = self.dimensions.x * 0.5
        self.p1 = {}
        self.p2 = {}

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)
    
    def die(self, impact: pygame.Vector2):
        if not self.dead:
            self.dead = True

            p1 = (self.pos.x + self.node_radius, self.pos.y + self.node_radius)
            self.p1 = {"x": p1[0], "y": p1[1], "oldx": p1[0] - impact.x, "oldy": p1[1] - impact.y}
            p2 = (self.pos.x + self.node_radius, self.pos.y + self.dimensions.y - self.node_radius)
            self.p2 = {"x": p2[0], "y": p2[1], "oldx": p2[0] - impact.x, "oldy": p2[1] - impact.y}
    
    def update(self, dt):
        if self.dead:
            vels = []
            for p in [self.p1, self.p2]:
                vx = (p['x'] - p['oldx']) * FRICTION
                vy = (p['y'] - p['oldy']) * FRICTION
                vels.append((vx, vy))
                p['oldx'] = p['x']
                p['oldy'] = p['y']
                p['x'] += vx * dt
                p['y'] += vy * dt
                p['y'] += 0.5 * dt * dt

            dx, dy = self.p1['x'] - self.p2['x'], self.p1['y'] - self.p2['y']
            distance = math.sqrt(dx ** 2 + dy ** 2)
            difference = (self.dimensions.y - self.node_radius * 2) - distance
            percentage = difference / max(0.001, distance) * 0.5
            offset_x = dx * percentage
            offset_y = dy * percentage
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
                            p['oldy'] = p['y'] - vy * 0.97
                        else:
                            p['oldy'] = p['y'] + vy * BOUNCE
                            p['oldx'] = p['x'] - vx * 0.97

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
    
    def draw(self, surf, scroll):
        if not self.dead:
            surf.blit(self.img, (self.pos.x - scroll[0], self.pos.y - scroll[1]))
        else:
            angle = math.atan2(self.p1['y'] - self.p2['y'], self.p1['x'] - self.p2['x'])
            deg = -math.degrees(angle) - 90 
            
            img_copy = pygame.transform.rotate(self.img, deg)

            mp_x = (self.p1['x'] + self.p2['x']) * 0.5
            mp_y = (self.p1['y'] + self.p2['y']) * 0.5
            
            surf.blit(img_copy, (mp_x - (img_copy.get_width() / 2) - scroll[0], mp_y - (img_copy.get_height() / 2) - scroll[1]))
            # pygame.draw.circle(surf, (255, 255, 0), (self.p1['x'], self.p1['y']), self.node_radius)
            # pygame.draw.circle(surf, (255, 255, 0), (self.p2['x'], self.p2['y']), self.node_radius)