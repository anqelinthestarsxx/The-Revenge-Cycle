# tile size
TILE_SIZE = 16
# world is split into chunks (size = relative tilesize, actual pixel size = tile_size * chunk_size)
CHUNK_SIZE = 2
# level width (relative chunk size, "")
LEVEL_WIDTH = 12
LEVEL_HEIGHT = 9

SCALE = 3 # screen scaling
WIDTH, HEIGHT = LEVEL_WIDTH * CHUNK_SIZE * TILE_SIZE * SCALE, LEVEL_HEIGHT * CHUNK_SIZE * TILE_SIZE * SCALE # starting window dimensions
OFFSETS = {(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (0, 0)}
PHYSICS_TILES = {"grass"}
DANGER_TILES = ["spikes"]
SCREEN_SHAKE_DECAY = 1
SCROLL_LIMIT = 8