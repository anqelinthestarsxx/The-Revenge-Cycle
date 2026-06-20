import pygame, math, time, random

from .bip import *
from .util import read_json
from .grass import GrassManager


class TileMap:
    def __init__(self, app):
        self.app = app
        self.tile_map = {}
        self.off_grid = []
        self.springs = []
        self.water = []
        self.grass_map = {}
        self.grass_manager = None
        self.light_map = {}
        self.anchors = []
        self.blasters = []
        self.start_pos = [10, 10]
    
    def load(self, path):
        data = read_json(path)

        self.tile_map = {}
        self.off_grid = []

        for tile in data["level"]["tiles"]:
            tile_loc = f"{tile['pos'][0]};{tile['pos'][1]}"
            img = None
            try:
                img = self.app.assets[f"tiles/{tile['type']}"][tile["variant"]].copy()
            except KeyError:
                pass
            self.tile_map[tile_loc] = {
                "type": tile["type"],
                "variant": tile["variant"],
                "pos": tile["pos"],
                "img": img
            }

        # load off grid tiles
        self.off_grid.extend(data["level"]["off_grid"])
        for tile in self.off_grid:
            tile["type"] = tile["type"]
        
        # self.extract_grass()
        self.calculate_light_map()
    
    def extract_blasters(self):
        self.blasters = []
        for loc in self.tile_map.copy():
            if self.tile_map[loc]["type"] == "blaster":
                self.blasters.append(Blaster(self.app, [self.tile_map[loc]["pos"][0] * TILE_SIZE, self.tile_map[loc]["pos"][1] * TILE_SIZE]))
                del self.tile_map[loc]
    
    def extract_grass(self):
        grass_locs = []
        self.grass_map = {}
        for loc in self.tile_map:
            if self.tile_map[loc]["type"] == "grass_key":
                self.grass_map[loc] = None
                grass_locs.append(loc)
        
        for loc in grass_locs:
            del self.tile_map[loc]
        
        self.grass_manager = GrassManager(self.app, self.app.assets["grass"])
        self.grass_manager.load(self.grass_map, 8, 2)
    
    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.off_grid.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.off_grid.remove(tile)
        for loc in self.tile_map.copy():
            tile = self.tile_map[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= TILE_SIZE
                matches[-1]['pos'][1] *= TILE_SIZE
                if not keep:
                    del self.tile_map[loc]
        return matches

    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // TILE_SIZE), int(pos[1] // TILE_SIZE))
        for offset in OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ";" + str(tile_loc[1] + offset[1])
            if check_loc in self.tile_map:
                tiles.append(self.tile_map[check_loc])
        return tiles

    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // TILE_SIZE)) + ";" + str(int(pos[1] // TILE_SIZE))
        if tile_loc in self.tile_map:
            if self.tile_map[tile_loc]["type"] in PHYSICS_TILES:
                return self.tile_map[tile_loc]

    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile["type"] in PHYSICS_TILES:
                rects.append(
                    pygame.Rect(tile["pos"][0] * TILE_SIZE, tile["pos"][1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                )
        return rects

    def danger_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile["type"] in DANGER_TILES:
                rects.append(
                    pygame.Rect(tile["pos"][0] * TILE_SIZE, tile["pos"][1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                )
        return rects

    def draw_decor(self, surf, scroll):
        for tile in self.off_grid:
            surf.blit(
                self.app.assets[f"tiles/{tile['type']}"][tile["variant"]], (tile["pos"][0] - scroll[0], tile["pos"][1] - scroll[1])
            )

    def draw(self, surf, scroll):
        # self.grass_manager.draw(surf, (scroll[0] + 8, scroll[1] - 3))
        for x in range(scroll[0] // TILE_SIZE, (scroll[0] + surf.get_width()) // TILE_SIZE + 1):
            for y in range(scroll[1] // TILE_SIZE, (scroll[1] + surf.get_height()) // TILE_SIZE + 1):
                loc = str(x) + ";" + str(y)
                if loc in self.tile_map:
                    tile = self.tile_map[loc]

                    surf.blit(
                        tile["img"],
                        (x * TILE_SIZE - scroll[0], y * TILE_SIZE - scroll[1]),
                    )

    def calculate_light_map(self):
        print("Generating light map...")
        start = time.time()
        self.light_map = {}
        levelMin = [1000000, 1000000]
        levelMax = [0, 0]
        for loc in self.tile_map:
            x, y = [int(c) for c in loc.split(';')]
            levelMin[0] = min(levelMin[0], x)
            levelMin[1] = min(levelMin[1], y)
            levelMax[0] = max(levelMax[0], x)
            levelMax[1] = max(levelMax[1], y)
        # levelMin[0] -= 100
        # levelMax[0] += 100
        levelMin[1] -= 10
        # levelMax[1] += 100
        
        queue = []
        for x in range(levelMax[0] - levelMin[0]):
            for y in range(levelMax[1] - levelMin[1]):
                loc = f'{x};{y}'
                tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                attenuation = 1.0
                for water in self.water:
                    if water.get_rect().colliderect(tile_rect):
                        attenuation = 0.7
                if not (loc in self.tile_map):
                    queue.append({"pos": [x, y], "attenuation": attenuation})
                elif not (self.tile_map[loc]["type"] in PHYSICS_TILES):
                    queue.append({"pos": [x, y], "attenuation": attenuation})
        
        absorb = 0.7
        while len(queue) > 0:
            for tile in queue.copy():
                self.light_map[str(tile["pos"][0]) + ";" + str(tile["pos"][1])] = tile["attenuation"]
                for shift in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
                    pos = [tile["pos"][0] + shift[0], tile["pos"][1] + shift[1]]
                    check_loc = f"{pos[0]};{pos[1]}"
                    if not (check_loc in self.light_map) and (levelMin[0] <= pos[0] < levelMax[0] and levelMin[1] <= pos[1] < levelMax[1]):
                        solid = False
                        if check_loc in self.tile_map:
                            if self.tile_map[check_loc]["type"] in PHYSICS_TILES:
                                solid = True
                        if solid:
                            attenuation = max(tile["attenuation"] * absorb, 0.0)
                            self.light_map[check_loc] = attenuation
                            queue.append({"pos": pos, "attenuation": attenuation})
                        else:
                            tile_rect = pygame.Rect(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                            attenuation = 1.0
                            self.light_map[check_loc] = attenuation
                            queue.append({"pos": pos, "attenuation": attenuation})
                queue.remove(tile)
            # print(f"{len(self.light_map)}/{(levelMax[0] - levelMin[0]) * (levelMax[1] - levelMin[1])}")
        print(f"Generated light map! ({(time.time() - start) * 1000 :.2f} ms)")
                

    def get_light_data(self, surf, scroll) -> pygame.Surface:
        grid_size = (math.ceil(surf.get_width() / TILE_SIZE) + 2, math.ceil(surf.get_height() / TILE_SIZE) + 2)

        light_surf = pygame.Surface(grid_size)
        light_surf.fill((0, 0, 0))

        offset_x = math.floor(scroll[0] / TILE_SIZE) - 1
        offset_y = math.floor(scroll[1] / TILE_SIZE) - 1

        for x in range(grid_size[0]):
            tile_x = offset_x + x
            for y in range(grid_size[1]):
                tile_y = offset_y + y
                loc = f"{tile_x};{tile_y}"
                if loc in self.light_map:
                    r = self.light_map[loc]
                    g = self.light_map[loc] ** 1.2
                    b = self.light_map[loc] ** 1.5
                    light_surf.set_at((x, y), (r * 255, g * 255, b * 255))

        return light_surf