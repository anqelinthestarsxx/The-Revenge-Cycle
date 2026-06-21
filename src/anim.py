import pygame, math

class Anim:
    def __init__(self, animation, speed, looping=True):
        self.animation = animation
        self.speed = speed
        self.looping = looping
        self.finished = False
        self.frame = 0
        self.step = 0
        self.flip = False

    def reset(self):
        self.finished = False
        self.frame = 0
        self.step = 0

    def update(self, dt):
        self.frame += self.speed * dt
        self.step = math.floor(self.frame) % len(self.animation)
        if not self.looping:
            if self.frame >= len(self.animation):
                self.finished = True
                self.step = len(self.animation) - 1

    def draw(self, surf, scroll, pos, angle=0):
        anim = pygame.transform.flip(self.animation[self.step], self.flip, False)
        rot_surf = pygame.transform.rotate(anim, angle)
        surf.blit(
            rot_surf,
            (
                pos[0] + int(anim.get_width() / 2) - int(rot_surf.get_width() / 2) - scroll[0],
                pos[1] + int(anim.get_height() / 2) - int(rot_surf.get_height() / 2) - scroll[1],
            ),
        )
