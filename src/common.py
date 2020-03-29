# Constants
from enum import Enum
from os.path import join, sep

import pygame

from src.config import SFX_DIR, SOUND_ENABLED, MUSIC_ENABLED, MUSIC_DIR, IMAGES_DIR, COLOR_KEY, TILE_SIZE


class Direction(Enum):
    DOWN = 0
    LEFT = 1
    UP = 2
    RIGHT = 3


_sound_library = {}
bump_sfx = join(SFX_DIR, '42 Dragon Quest 1 - Bumping into Walls (22khz mono).wav')


def play_sound(path='data/sound/sfx'):
    if SOUND_ENABLED:
        global _sound_library
        sound = _sound_library.get(path)
        if sound is None:
            canonicalized_path = path.replace('/', sep).replace('\\', sep)
            sound = pygame.mixer.Sound(canonicalized_path)
            _sound_library[path] = sound
        sound.play()


_music_library = {}
tantegel_castle_throne_room_music = join(MUSIC_DIR, '02_Dragon_Quest_1_-_Tantegel_Castle_(22khz_mono).ogg')


def play_music(path='data/sound/music'):
    if MUSIC_ENABLED:
        global _music_library
        music = _music_library.get(path)
        if music is None:
            canonicalized_path = path.replace('/', sep).replace('\\', sep)
            music = pygame.mixer.Sound(canonicalized_path)
            _music_library[path] = music
        music.play()


_image_library = {}
MAP_TILES_PATH = join(IMAGES_DIR, 'tileset.png')
UNARMED_HERO_PATH = join(IMAGES_DIR, 'unarmed_hero.png')
KING_LORIK_PATH = join(IMAGES_DIR, 'king_lorik.png')
RIGHT_FACE_GUARD_PATH = join(IMAGES_DIR, 'right_face_guard.png')
LEFT_FACE_GUARD_PATH = join(IMAGES_DIR, 'left_face_guard.png')
ROAMING_GUARD_PATH = join(IMAGES_DIR, 'roaming_guard.png')


def get_image(path):
    global _image_library
    image = _image_library.get(path)
    if image is None:
        canonicalized_path = path.replace('/', sep).replace('\\', sep)
        image = pygame.image.load(canonicalized_path)
        _image_library[path] = image
    return image


def parse_animated_spritesheet(sheet, is_roaming=False):
    """
    Parses spritesheets and creates image lists. If is_roaming is True
    the sprite will have four lists of images, one for each direction. If
    is_roaming is False then there will be one list of 2 images.
    """
    sheet.set_colorkey(COLOR_KEY)
    sheet.convert_alpha()
    # width, height = sheet.get_size()

    facing_down = []
    facing_left = []
    facing_up = []
    facing_right = []

    for i in range(0, 2):

        rect = (i * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE)
        facing_down.append(sheet.subsurface(rect))

        if is_roaming:
            rect = ((i + 2) * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE)
            facing_left.append(sheet.subsurface(rect))

            rect = ((i + 4) * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE)
            facing_up.append(sheet.subsurface(rect))

            rect = ((i + 6) * TILE_SIZE, 0, TILE_SIZE, TILE_SIZE)
            facing_right.append(sheet.subsurface(rect))

    return facing_down, facing_left, facing_up, facing_right