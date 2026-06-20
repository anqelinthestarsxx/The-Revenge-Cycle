import pygame, math

from .bip import *

class StationaryQuads:
    def __init__(self, items, chunk_size):
        self.items = list(items)
        self.chunk_size = pygame.Vector2(chunk_size)
        self.chunk_data = self.load_chunks(items, chunk_size)

    @staticmethod
    def load_chunks(items, chunk_size):
        chunk_data = {}
        for item in items:
            loc = str(math.floor(item.pos[0] / chunk_size[0] / TILE_SIZE)) + ';' + str(math.floor(item.pos[1] / chunk_size[1] / TILE_SIZE))  # item must have attribute pos as a pygame.Vector2 or list
            if not loc in chunk_data:
               chunk_data[loc] = []
            chunk_data[loc].append(item)
        return chunk_data

    def add_item(self, item):
        loc = str(math.floor(item.pos[0] / self.chunk_size[0] / TILE_SIZE)) + ';' + str(math.floor(item.pos[1] / self.chunk_size[1] / TILE_SIZE))  # item must have attribute pos as a pygame.Vector2 or list
        if not loc in self.chunk_data:
            self.chunk_data[loc] = []
        self.chunk_data[loc].append(item)

    def updateables(self, surf, scroll):
        for y in range(math.ceil(surf.get_height() / (self.chunk_size.y * TILE_SIZE)) + 2):
              for x in range(math.ceil(surf.get_width() / (self.chunk_size.x * TILE_SIZE)) + 2):
                  target_x = x - 2 + math.ceil(scroll.x / (self.chunk_size.x * TILE_SIZE))
                  target_y = y - 2 + math.ceil(scroll.y / (self.chunk_size.y * TILE_SIZE))
                  target_chunk = f'{target_x};{target_y}'
                  if target_chunk in self.chunk_data:
                      for item in self.chunk_data[target_chunk]:
                          yield item

    def update(self, surf, scroll, *args, **kwargs):
        for y in range(math.ceil(surf.get_height() / (self.chunk_size.y * TILE_SIZE)) + 1):
            for x in range(math.ceil(surf.get_width() / (self.chunk_size.x * TILE_SIZE)) + 1):
                target_x = x - 1 + math.ceil(scroll.x / (self.chunk_size.x * TILE_SIZE))
                target_y = y - 1 + math.ceil(scroll.y / (self.chunk_size.y * TILE_SIZE))
                target_chunk = f'{target_x};{target_y}'
                if target_chunk in self.chunk_data:
                    for item in self.chunk_data[target_chunk]:
                        item.update(*args, **kwargs)
