import pygame, math, random

class Particle:
    def __init__(self, app, particle_type, pos, vel=[0, 0], frame=0, solid=False, friction=(1, 1)):
        self.app = app
        self.particle_type = particle_type
        self.pos = list(pos)
        self.vel = list(vel)
        self.animation = self.app.assets['particle/' + self.particle_type].copy()
        self.alpha = 255
        if self.particle_type == 'leaf':
            self.alpha = 10
        self.frame = frame % len(self.animation)
        self.done = False
        self.speed = 0.1
        self.solid = solid
        self.friction = pygame.Vector2(friction)
        self.timer = 0
        self.angle = random.random() * 360
        self.decay = 4
    
    def img(self):
        self.frame += max(0.025, self.speed) * self.app.dt
        if self.frame >= len(self.animation):
            self.done = True
            return self.animation[-1]
        return self.animation[math.floor(self.frame)]
    
    def update(self):
        kill = False
        if self.particle_type == "bubble" and self.done:
            return True
        if self.done:
            if self.particle_type == 'particle':
                self.alpha -= 200 * self.app.dt
            self.alpha -= self.decay * self.app.dt
            kill = self.particle_type == 'explode' or self.particle_type == 'star' or self.particle_type == "bubble"
            if self.alpha < 15:
                kill = True
                self.alpha = 0
        else:
            self.alpha = min(255, self.alpha + 4 * self.app.dt)
        self.pos[0] += self.vel[0] * self.app.dt
        self.vel[0] += (self.vel[0] * self.friction.x - self.vel[0]) * self.app.dt
        if self.solid:
            check = self.app.tile_map.solid_check(self.pos)
            if check: 
                self.pos[0] -= self.vel[0] * self.app.dt
                self.vel[0] *= -0.5
                self.vel[1] *= 0.9
        self.pos[1] += self.vel[1] * self.app.dt
        self.vel[1] += (self.vel[1] * self.friction.y - self.vel[1]) * self.app.dt
        self.vel[1] += 0.02 * self.app.dt
        if self.solid:
            check = self.app.tile_map.solid_check(self.pos)
            if check:
                self.done = True
                self.vel[1] *= -0.5
                self.vel[0] *= 0.9
                self.speed = 0
        self.timer += 1 * self.app.dt
        if self.timer > 600:
            kill = True
        return kill
    
    def draw(self, surf, scroll):
        img = self.img()
        if self.particle_type == "bubble":
            img = pygame.transform.rotate(img, self.angle)
        if self.pos in self.app:
            self.alpha = (1 - self.frame / len(self.animation)) * 255
            img.set_alpha(self.alpha)
            surf.blit(img, (self.pos[0] - scroll[0] - img.get_width() // 2, self.pos[1] - scroll[1] - img.get_height() // 2))

class Bubble(Particle):
    def __init__(self, app, particle_type, pos, vel=[0, 0], frame=0, solid=False, friction=(1, 1)):
        super().__init__(app, particle_type, pos, vel, frame, solid, friction)
        self.speed = 0.5

class PhysicsParticles:
    def __init__(self, app, trail=False, friction=0.999, bounce=0.7, explode=False, gravity=0.125):
        self.trail = trail
        self.friction = friction
        self.bounce = -bounce
        self.particles = []
        self.gravity = gravity
        self.explode = explode
        self.app = app
    
    def append(self, item):
        self.particles.append(item)
    
    def update(self, surf, scroll=(0, 0)):
        for particle in self.particles.copy():
            speed = (abs(particle[1][0]) + abs(particle[1][1]))
            particle[1][0] *= 0.999
            particle[0][0] += particle[1][0] * self.app.dt
            if self.app.tile_map.solid_check(particle[0]):
                particle[0][0] -= particle[1][0] * self.app.dt
                particle[1][0] *= self.bounce
                particle[1][1] *= self.friction
            particle[1][1] += self.gravity * self.app.dt
            particle[1][1] *= 0.999
            particle[0][1] += particle[1][1] * self.app.dt
            if self.app.tile_map.solid_check(particle[0]):
                particle[0][1] -= particle[1][1] * self.app.dt
                particle[1][1] *= self.bounce
                particle[1][0] *= self.friction
            if self.trail:
                angle = math.atan2(particle[1][1], particle[1][0])
                scale = 0.5
                pygame.draw.polygon(surf, particle[3], [
                    (particle[0][0] - scroll[0], particle[0][1] - scroll[1]),
                    (particle[0][0] - math.cos(angle + math.pi * 0.5) * scale - scroll[0], particle[0][1] - math.sin(angle + math.pi * 0.5) * scale - scroll[1]),
                    (particle[0][0] - scroll[0] - particle[1][0] * 3 * scale, particle[0][1] - scroll[1] - particle[1][1] * 3 * scale),
                    (particle[0][0] - math.cos(angle + math.pi * -0.5) * scale - scroll[0], particle[0][1] - math.sin(angle + math.pi * -0.5) * scale - scroll[1]),
                ])
            else:
                pygame.draw.circle(surf, particle[3], (particle[0][0] - scroll[0], particle[0][1] - scroll[1]), particle[2] / 2)
            particle[2] -= (particle[2] / 20 + 0.0000001) * self.app.dt
            if self.explode:
                if random.random() / self.app.dt / min(1, particle[2]) < 0.01:
                    self.app.particles.append(Particle(self.app, 'explosion', (particle[0][0], particle[0][1] - 2), [(random.random() - 0.5) * 0.1, random.random() - 1], random.randint(3, 7) + 1))
                if speed > 5:
                    self.app.particles.append(Particle(self.app, 'particle', (particle[0][0], particle[0][1]), [0, 0], random.randint(2, 3)))
            if particle[2] < 0:
                self.particles.remove(particle)