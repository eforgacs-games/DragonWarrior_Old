import random
import sys

import numpy as np
import pygame
from pygame import init, Surface, QUIT, USEREVENT, time, quit
from pygame.display import set_mode, set_caption, flip
from pygame.event import get
from pygame.image import load_extended
from pygame.time import Clock
from pygame.time import get_ticks
from pygame.transform import scale

from src import maps
from src.common import Direction, get_initial_character_location, play_sound, bump_sfx
from src.config import MAP_TILES_PATH, UNARMED_HERO_PATH, KING_LORIK_PATH, LEFT_FACE_GUARD_PATH, \
    RIGHT_FACE_GUARD_PATH, ROAMING_GUARD_PATH, NES_RES, SCALE, WIN_WIDTH, WIN_HEIGHT, TILE_SIZE
from src.maps import TantegelThroneRoom
from src.player import Player


class Game(object):
    FPS = 60
    GAME_TITLE = "Dragon Warrior"
    WIN_WIDTH = NES_RES[0] * SCALE
    WIN_HEIGHT = NES_RES[1] * SCALE

    COLOR_KEY = (0, 128, 128)
    ORIGIN = (0, 0)
    BLACK = (0, 0, 0)
    BACK_FILL_COLOR = BLACK
    MOVE_EVENT = USEREVENT + 1
    time.set_timer(MOVE_EVENT, 100)

    def __init__(self):

        # Initialize pygame
        init()

        # Create the game window.
        self.screen = set_mode((WIN_WIDTH, WIN_HEIGHT))
        set_caption(self.GAME_TITLE)
        self.clock = Clock()
        self.last_roaming_character_clock_check = get_ticks()
        self.roaming_character_go_cooldown = 3000
        self.sprite_movement_wait_period = 10
        if maps.current_map is None:
            maps.current_map = maps.TantegelThroneRoom
        self.map_tiles = []
        self.bigmap_width = None
        self.bigmap_height = None
        self.bigmap = None
        self.current_map_width = None
        self.current_map_height = None
        self.background = None
        self.current_map = None
        self.king_lorik_images = None
        self.left_face_guard_images = None
        self.right_face_guard_images = None
        self.roaming_guard_images = None
        self.unarmed_hero_images = None
        self.load_images()
        self.map_tilesheet = None

    def main(self):
        self.load_current_map()
        # Make the big scrollable map
        self.make_bigmap()
        self.background = Surface(self.screen.get_size()).convert()
        self.get_roaming_guard_images()

        initial_hero_location = get_initial_character_location(self.current_map.layout, 'HERO')
        # TODO: Fix the initial camera_pos calculation.
        camera_pos = self.get_initial_camera_position(initial_hero_location)
        while True:
            self.clock.tick(self.FPS)
            for event in get():
                if event.type == QUIT:
                    quit()
                    sys.exit()
            # TODO: Smooth out movement even more.
            key = pygame.key.get_pressed()
            camera_pos_x, camera_pos_y = camera_pos
            self.current_hero_layout_x_pos = self.current_map.player.rect.y // TILE_SIZE
            self.current_hero_layout_y_pos = self.current_map.player.rect.x // TILE_SIZE
            camera_pos_x, camera_pos_y = self.move_player(camera_pos, key)
            # # TODO: implement actual function of B, A, Start, Select buttons.
            # if key[pygame.K_z]:
            #     # B button
            #     print("You pressed the z key.")
            # if key[pygame.K_y]:
            #     # A button
            #     print("You pressed the y key.")
            # if key[pygame.K_SPACE]:
            #     # Start button
            #     print("You pressed the space bar.")
            # if key[pygame.K_ESCAPE]:
            #     # Select button
            #     print("You pressed the escape key.")
            camera_pos = int(camera_pos_x), int(camera_pos_y)
            # For debugging purposes, this prints out the current tile that the hero is standing on.
            # print(Player.get_tile_by_value(self.current_map.layout[self.current_map.player.rect.y // TILE_SIZE][
            #                                    self.current_map.player.rect.x // TILE_SIZE]))

            # THESE ARE THE VALUES WE ARE AIMING FOR FOR INITIAL TANTEGEL THRONE ROOM
            # camera_pos = -160, -96
            self.current_map.draw_map(self.bigmap)
            for sprites in self.current_map.character_sprites:
                sprites.clear(self.screen, self.background)
            self.screen.fill(self.BACK_FILL_COLOR)

            self.background = self.bigmap.subsurface(self.ORIGIN[0], self.ORIGIN[1], self.current_map.width,
                                                     self.current_map_height).convert()
            # TODO: Disable moving of roaming characters if a dialog box is open.
            # TODO: Extend roaming characters beyond just the roaming guard.
            for roaming_character in self.current_map.roaming_characters:
                # initial_pos_x, initial_pos_y = roaming_character.position.take(0), roaming_character.position.take(1)
                roaming_character_x_pos = roaming_character.rect.y // TILE_SIZE
                roaming_character_y_pos = roaming_character.rect.x // TILE_SIZE
                now = get_ticks()
                # Useful for debugging roaming characters:
                # print(
                #     Player.get_tile_by_value(self.current_map.layout[roaming_character_x_pos][roaming_character_y_pos]))
                # print("roaming_character_x_pos: " + str(roaming_character_x_pos))
                # print("roaming_character_y_pos: " + str(roaming_character_y_pos))
                if now - self.last_roaming_character_clock_check >= self.roaming_character_go_cooldown:
                    self.last_roaming_character_clock_check = now
                    roaming_character.direction = random.randrange(4)
                    self.move_roaming_character(roaming_character.position.take(0), roaming_character.position.take(1),
                                                roaming_character, roaming_character_x_pos,
                                                roaming_character_y_pos)

                # roaming character sides collision
                self.handle_roaming_character_map_edge_side_collision(roaming_character)
            for character in self.current_map.characters:
                character.animate()
            for sprites in self.current_map.character_sprites:
                sprites.draw(self.background)

            self.screen.blit(self.background, camera_pos)

            # self.screen.blit(self.background, self.ORIGIN)
            flip()

    def get_initial_camera_position(self, initial_hero_location):
        return np.negative(initial_hero_location.take(0) * TILE_SIZE / 2), np.negative(
            initial_hero_location.take(1) * TILE_SIZE / 4.333333333333333)

    def get_roaming_guard_images(self):
        self.current_map.roaming_guard.down_images = self.roaming_guard_images[Direction.DOWN.value]
        self.current_map.roaming_guard.left_images = self.roaming_guard_images[Direction.LEFT.value]
        self.current_map.roaming_guard.up_images = self.roaming_guard_images[Direction.UP.value]
        self.current_map.roaming_guard.right_images = self.roaming_guard_images[Direction.RIGHT.value]

    def move_player(self, camera_pos, key):
        # TODO: Move only if button is pressed for 0.5 seconds.
        curr_pos_x, curr_pos_y = camera_pos
        next_pos_x, next_pos_y = curr_pos_x, curr_pos_y
        if key[pygame.K_DOWN]:
            self.current_map.player.direction = Direction.DOWN.value
            is_down_passable = Player.get_tile_by_value(self.current_map.layout[self.current_hero_layout_x_pos + 1][
                                                 self.current_hero_layout_y_pos]) not in self.current_map.current_map_impassable_tiles
            if is_down_passable:
                for x in range(TILE_SIZE):
                    self.current_map.player.rect.y += 1
                    next_pos_y = curr_pos_y - TILE_SIZE
                    pygame.time.delay(10)
            else:
                play_sound(bump_sfx)
        if key[pygame.K_LEFT]:
            self.current_map.player.direction = Direction.LEFT.value
            is_left_passable = Player.get_tile_by_value(self.current_map.layout[self.current_hero_layout_x_pos][
                                                 self.current_hero_layout_y_pos - 1]) not in self.current_map.current_map_impassable_tiles
            if is_left_passable:
                for x in range(TILE_SIZE):
                    self.current_map.player.rect.x -= 1
                    next_pos_x = curr_pos_x + TILE_SIZE
                    pygame.time.delay(10)
            else:
                play_sound(bump_sfx)
        if key[pygame.K_UP]:
            self.current_map.player.direction = Direction.UP.value
            is_up_passable = Player.get_tile_by_value(self.current_map.layout[self.current_hero_layout_x_pos - 1][
                                                 self.current_hero_layout_y_pos]) not in self.current_map.current_map_impassable_tiles
            if is_up_passable:
                for i in range(TILE_SIZE):
                    self.current_map.player.rect.y -= 1
                    next_pos_y = curr_pos_y + TILE_SIZE
                    pygame.time.delay(10)
            else:
                play_sound(bump_sfx)
        if key[pygame.K_RIGHT]:
            self.current_map.player.direction = Direction.RIGHT.value  # Turn character to face right
            is_right_passable = Player.get_tile_by_value(self.current_map.layout[self.current_hero_layout_x_pos][
                                                 self.current_hero_layout_y_pos + 1]) not in self.current_map.current_map_impassable_tiles
            if is_right_passable:  # Check for collisions
                for x in range(TILE_SIZE):
                    self.current_map.player.rect.x += 1
                    next_pos_x = curr_pos_x - TILE_SIZE
                    pygame.time.delay(10)
                #  THIS MOVES SMOOTHLY
                # self.current_map.player.rect.x += 1  # increment
                # curr_pos_x -= 1
                # pygame.time.delay(10)
            else:
                play_sound(bump_sfx)

        # Sides collision
        next_pos_x = self.handle_lr_sides_collision(curr_pos_x, next_pos_x)
        next_pos_y = self.handle_tb_sides_collision(curr_pos_y, next_pos_y)
        # for reference:
        # self.current_map.height - TILE_SIZE is equal to WIN_HEIGHT - ((WIN_HEIGHT // 23) * 1.5)
        return next_pos_x, next_pos_y

    def handle_tb_sides_collision(self, curr_pos_y, next_pos_y):
        max_bound = self.current_map.height
        min_bound = 0
        player_pos = self.current_map.player.rect.y
        if player_pos < min_bound:
            self.current_map.player.rect.y = min_bound
            play_sound(bump_sfx)
            next_pos_y = curr_pos_y
        elif player_pos > max_bound - TILE_SIZE:
            self.current_map.player.rect.y = max_bound - TILE_SIZE
            play_sound(bump_sfx)
            next_pos_y = curr_pos_y
        return next_pos_y

    def handle_lr_sides_collision(self, curr_pos_x, next_pos_x):
        max_bound = self.current_map.width
        min_bound = 0
        player_pos = self.current_map.player.rect.x
        if player_pos < min_bound:  # Simple Sides Collision
            self.current_map.player.rect.x = min_bound  # Reset Player Rect Coord
            play_sound(bump_sfx)
            next_pos_x = curr_pos_x
        elif player_pos > max_bound - TILE_SIZE:
            self.current_map.player.rect.x = max_bound - TILE_SIZE
            play_sound(bump_sfx)
            next_pos_x = curr_pos_x
        return next_pos_x

    def move_roaming_character(self, pos_x, pos_y, roaming_character, roaming_character_x_pos, roaming_character_y_pos):
        if roaming_character.direction == Direction.DOWN.value:
            if Player.get_tile_by_value(self.current_map.layout[roaming_character_x_pos + 1][
                                            roaming_character_y_pos]) not in maps.impassable_tiles:
                roaming_character.rect.y += TILE_SIZE
                pos_y -= 1
        elif roaming_character.direction == Direction.LEFT.value:
            if Player.get_tile_by_value(self.current_map.layout[roaming_character_x_pos][
                                            roaming_character_y_pos - 1]) not in maps.impassable_tiles:
                roaming_character.rect.x -= TILE_SIZE
                pos_x -= 1
        elif roaming_character.direction == Direction.UP.value:
            if Player.get_tile_by_value(self.current_map.layout[roaming_character_x_pos - 1][
                                            roaming_character_y_pos]) not in maps.impassable_tiles:
                roaming_character.rect.y -= TILE_SIZE
                pos_y += 1
        elif roaming_character.direction == Direction.RIGHT.value:
            if Player.get_tile_by_value(self.current_map.layout[roaming_character_x_pos][
                                            roaming_character_y_pos + 1]) not in maps.impassable_tiles:
                roaming_character.rect.x += TILE_SIZE
                pos_x += 1
        else:
            print("Invalid direction.")

    def handle_roaming_character_map_edge_side_collision(self, roaming_character):
        if roaming_character.rect.x < 0:  # Simple Sides Collision
            roaming_character.rect.x = 0  # Reset Player Rect Coord
        elif roaming_character.rect.x > self.current_map.width - TILE_SIZE:
            roaming_character.rect.x = self.current_map.width - TILE_SIZE
        if roaming_character.rect.y < 0:
            roaming_character.rect.y = 0
        elif self.current_map.roaming_guard.rect.y > self.current_map_height - TILE_SIZE:
            self.current_map.roaming_guard.rect.y = self.current_map_height - TILE_SIZE

    def make_bigmap(self):
        self.bigmap_width = self.current_map.width
        self.bigmap_height = self.current_map.height
        self.bigmap = Surface((self.bigmap_width, self.bigmap_height)).convert()
        self.bigmap.fill(self.BACK_FILL_COLOR)

    def load_current_map(self):
        self.current_map = TantegelThroneRoom(self.map_tiles, self.unarmed_hero_images, self.king_lorik_images,
                                              self.left_face_guard_images, self.right_face_guard_images,
                                              self.roaming_guard_images)
        self.current_map.width = len(self.current_map.layout[0]) * TILE_SIZE
        self.current_map_height = len(self.current_map.layout) * TILE_SIZE
        self.current_map.load_map()

    def load_images(self):
        """Load all the images for the game graphics.
        """
        # Load the map tile spritesheet
        self.map_tilesheet = load_extended(MAP_TILES_PATH).convert()
        # Load unarmed hero images
        unarmed_hero_sheet = load_extended(UNARMED_HERO_PATH)
        # Load King Lorik images
        king_lorik_sheet = load_extended(KING_LORIK_PATH)
        # Guard images.
        left_face_guard_sheet = load_extended(LEFT_FACE_GUARD_PATH)
        right_face_guard_sheet = load_extended(RIGHT_FACE_GUARD_PATH)
        roaming_guard_sheet = load_extended(ROAMING_GUARD_PATH)

        self.map_tilesheet = scale(self.map_tilesheet,
                                   (self.map_tilesheet.get_width() * SCALE,
                                    self.map_tilesheet.get_height() * SCALE))
        unarmed_hero_sheet = scale(unarmed_hero_sheet,
                                   (unarmed_hero_sheet.get_width() * SCALE, unarmed_hero_sheet.get_height() * SCALE))

        king_lorik_sheet = scale(king_lorik_sheet,
                                 (king_lorik_sheet.get_width() * SCALE, king_lorik_sheet.get_height() * SCALE))

        left_face_guard_sheet = scale(left_face_guard_sheet,
                                      (left_face_guard_sheet.get_width() * SCALE,
                                       left_face_guard_sheet.get_height() * SCALE))

        right_face_guard_sheet = scale(right_face_guard_sheet,
                                       (right_face_guard_sheet.get_width() * SCALE,
                                        right_face_guard_sheet.get_height() * SCALE))

        roaming_guard_sheet = scale(roaming_guard_sheet,
                                    (roaming_guard_sheet.get_width() * SCALE, roaming_guard_sheet.get_height() * SCALE))

        self.parse_map_tiles()

        # Get the images for the initial hero sprites
        self.unarmed_hero_images = self.parse_animated_spritesheet(unarmed_hero_sheet, is_roaming=True)

        # Get images for the King
        self.king_lorik_images = self.parse_animated_spritesheet(king_lorik_sheet)

        self.left_face_guard_images = self.parse_animated_spritesheet(left_face_guard_sheet)

        self.right_face_guard_images = self.parse_animated_spritesheet(right_face_guard_sheet)

        self.roaming_guard_images = self.parse_animated_spritesheet(roaming_guard_sheet, is_roaming=True)

    def parse_map_tiles(self):

        width, height = self.map_tilesheet.get_size()

        for x in range(0, width // TILE_SIZE):
            row = []
            self.map_tiles.append(row)

            for y in range(0, height // TILE_SIZE):
                rect = (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                row.append(self.map_tilesheet.subsurface(rect))

    def parse_animated_spritesheet(self, sheet, is_roaming=False):
        """
        Parses spritesheets and creates image lists. If is_roaming is True
        the sprite will have four lists of images, one for each direction. If
        is_roaming is False then there will be one list of 2 images.
        """
        sheet.set_colorkey(self.COLOR_KEY)
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


def run():
    game = Game()
    game.main()


if __name__ == "__main__":
    run()
