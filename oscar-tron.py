import sys
import pygame
from enum import IntEnum
import argparse
import random
import math

SCREEN_WIDTH = 1152
SCREEN_HEIGHT = 864
SCREEN_TITLE = "Tron"
DEADZONE = 0.1
BLACK = 0, 0, 0
WIDTH = 3
SECONDS_DECAY = 3
MS_DECAY = SECONDS_DECAY * 1000.0


pygame.init()

pygame.mouse.set_visible(False) 

pygame.joystick.init()


font = pygame.image.load("reduction-rotated.bmp")
font_size = 50

def write( surface, x, y, text ):
    for l in range(0,len(text)):
        letter = text[l]
        i = ord( letter ) - 32
        a = (i // 10 * font_size)
        b = font.get_height() - (i % 10 * font_size) - font_size
        surface.blit( font, (x, y-l*font_size - font_size), (a,b,font_size,font_size) )

class Keys(IntEnum):
    """The order the keys are stored."""
    DOWN = 0
    UP = 1
    LEFT = 2
    RIGHT = 3

# function to check if point q lies on line segment 'pr'
def on_segment(p, q, r):
    return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
            q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))

# function to find orientation of ordered triplet (p, q, r)
# 0 --> p, q and r are collinear
# 1 --> Clockwise
# 2 --> Counterclockwise
def orientation(p, q, r):
    val = (q[1] - p[1]) * (r[0] - q[0]) - \
          (q[0] - p[0]) * (r[1] - q[1])

    # collinear
    if val == 0:
        return 0

    # clock or counterclock wise
    # 1 for clockwise, 2 for counterclockwise
    return 1 if val > 0 else 2


# function to check if two line segments intersect
def intersect(points):
    # find the four orientations needed
    # for general and special cases
    o1 = orientation(points[0][0], points[0][1], points[1][0])
    o2 = orientation(points[0][0], points[0][1], points[1][1])
    o3 = orientation(points[1][0], points[1][1], points[0][0])
    o4 = orientation(points[1][0], points[1][1], points[0][1])

    # general case
    if o1 != o2 and o3 != o4:
        return True

    # special cases
    # p1, q1 and p2 are collinear and p2 lies on segment p1q1
    if o1 == 0 and on_segment(points[0][0], points[1][0], points[0][1]):
        return True

    # p1, q1 and q2 are collinear and q2 lies on segment p1q1
    if o2 == 0 and on_segment(points[0][0], points[1][1], points[0][1]):
        return True

    # p2, q2 and p1 are collinear and p1 lies on segment p2q2
    if o3 == 0 and on_segment(points[1][0], points[0][0], points[1][1]):
        return True

    # p2, q2 and q1 are collinear and q1 lies on segment p2q2 
    if o4 == 0 and on_segment(points[1][0], points[0][1], points[1][1]):
        return True

    return False


def collision( seg, path ):
    for previous, current in zip( path, path[1:]):
        if intersect( ( seg, (previous, current) ) ):
            return True
    return False


def jitter():
    return ( random.random() - 0.5 ) * 2;

def limit( a ):
    return max( min( round( a ), 255 ), 0 )

class Particle:
    def __init__(self, start, vel, col ):
        self.pos = start
        self.vel = vel
        self.col = col
        self.heat = 1


class Player:
    def __init__(self, keys, start, vel, col ):
        self.keys = keys
        self.pos = start
        self.vel = vel
        self.col = pygame.Color(col)
        self.path = [ start, start ]
        self.joystick = None
        self.time_of_death = 0
        self.time = 0
        self.score = 0

class Level():

    def __init__(self, width, height):

        self.speed = height * 0.1

        self.particles = []

        self.players = [
                    Player( [pygame.K_a,pygame.K_d,pygame.K_w,pygame.K_s], [width*0.2, height*0.5], [self.speed,0], (230,20,20) ),
                    Player( [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN ], [width*0.8,height*0.5], [-self.speed,0], (20,20,230) )
            ]

        self.lookup = { pygame.joystick.Joystick(x).get_instance_id() : self.players[x]  for x in range(pygame.joystick.get_count()) }

        for x in range(pygame.joystick.get_count()):
            self.players[x].joystick = pygame.joystick.Joystick(x)

    def draw(self, width, height, surface):
        for player in self.players:
            if not player.time_of_death:
                pygame.draw.lines( surface, player.col, False, player.path, WIDTH)
                pygame.draw.rect( surface, player.col, pygame.Rect( player.pos[0]-2, player.pos[1]-2, 5, 5) )
            else:
                col = player.col
                col.a = round( 255 * ( 1.0 - min(player.time - player.time_of_death, MS_DECAY) / MS_DECAY ) )
                pygame.draw.lines( surface, col, False, player.path, WIDTH)

        for particle in self.particles:
            SPARKLE = 100
            r = limit( 300 * particle.heat + jitter() * SPARKLE )
            g = limit( 300 * particle.heat + jitter() * SPARKLE )
            b = limit( 100 * particle.heat + jitter() * SPARKLE )
            col = particle.col + pygame.Color( r, g, b )  
            col.a = round( 255 * particle.heat )
            surface.set_at( (round(particle.pos[0]),round(particle.pos[1]) ), col )

        write( surface, 10, height - 10, "00000" )
        write( surface, 10, height // 2 - 10, "00000" )

    def update( self, delta_time):

        for player in self.players:
            player.time += delta_time
            player.pos = ( 
                player.pos[0] + player.vel[0] * delta_time / 1000, 
                player.pos[1] + player.vel[1] * delta_time / 1000)

            for opponent in self.players:
                for previous, current in zip( opponent.path, opponent.path[1:]):
                    if opponent != player and collision( (player.pos, player.path[-1]), opponent.path ):
                        self.crash( player )
                    elif collision( (player.pos, player.path[-1]), opponent.path[:-2] ):
                        self.crash( player )

            player.path[-1] = player.pos

        for particle in self.particles:
            particle.pos = ( 
                particle.pos[0] + particle.vel[0] * delta_time / 1000.0, 
                particle.pos[1] + particle.vel[1] * delta_time / 1000.0)
            particle.vel = ( 
                particle.vel[0] * 0.99, 
                particle.vel[1] * 0.99)
            particle.heat *= math.pow( math.e, - delta_time / 1000.0 )


    def crash( self, player ):
        if player.time_of_death:
            return

        for i in range(0,10):
            particle = Particle( player.pos, player.vel, pygame.Color( player.col ) )
            particle.pos = player.pos
            particle.vel = ( player.vel[0] + jitter() * self.speed * 5, 
                             player.vel[1] + jitter() * self.speed * 5 )
            self.particles.append( particle )
        player.vel = [0,0]
        player.time_of_death = player.time


    def handle(self, event):

        if event.type == pygame.KEYDOWN:
            for player in self.players:
                if player.time_of_death:
                    continue
                vel = None
                if event.key == player.keys[ Keys.UP ] and player.vel[0] != 0:
                    vel = [0, -self.speed]
                if event.key == player.keys[ Keys.DOWN ] and player.vel[0] != 0:
                    vel = [0, +self.speed]
                if event.key == player.keys[ Keys.RIGHT ]and player.vel[1] != 0:
                    vel = [+self.speed, 0]
                if event.key == player.keys[ Keys.LEFT ] and player.vel[1] != 0:
                    vel = [-self.speed, 0]
                if vel:
                    player.vel = vel
                    player.path.append( player.pos )
        if event.type == pygame.JOYBUTTONDOWN:
            player = self.lookup[ event.instance_id ]
        if event.type == pygame.JOYAXISMOTION:
            vel = None
            player = self.lookup[ event.instance_id ]
            if not player.time_of_death:
                if player.joystick.get_axis(0) < -DEADZONE and player.vel[0] != 0:
                    vel = [0, +self.speed]
                if player.joystick.get_axis(0) > DEADZONE and player.vel[0] != 0:
                    vel = [0, -self.speed]
                if player.joystick.get_axis(1) < -DEADZONE and player.vel[1] != 0:
                    vel = [-self.speed, 0]
                if player.joystick.get_axis(1) > DEADZONE and player.vel[1] != 0:
                    vel = [+self.speed, 0]
            if vel:
                player.vel = vel
                player.path.append( player.pos )





class TronGame():

    """ Our custom Tron Window."""


    def __init__(self, fullscreen, rotate):

        """ Initializer """

        if fullscreen:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
            self.screen_width, self.screen_height = info.current_w, info.current_h
        else:
            self.screen_width, self.screen_height = SCREEN_WIDTH, SCREEN_HEIGHT

        if rotate:
            self.width = self.screen_height
            self.height = self.screen_width
            self.background = pygame.Surface( (self.screen_width, self.screen_height) )
            self.background.fill(BLACK)
            self.surface = pygame.Surface( (self.width, self.height), pygame.SRCALPHA)
        else:
            self.width = self.screen_width
            self.height = self.screen_height
            self.background = None
            self.surface = self.screen

        if not fullscreen:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.DOUBLEBUF)

        self.rotate = rotate

        self.run = True
        
        self.level = None

    def start( self, players ):
        if players == 2:
            self.level = Level( self.width, self.height )


    def draw(self):

        """ Draw everything """

        self.surface.fill(BLACK)

        if self.level:
            self.level.draw( self.width, self.height, self.surface )

        write( self.surface, 100, 500, "Hello" )
        if self.rotate:
            self.screen.blit( self.background, (0, 0))
            self.screen.blit( pygame.transform.rotate( self.surface, -90 ), (0, 0))
        
        pygame.display.flip()

    def update(self, delta_time):
        
        """ Update state """

        if self.level:
            self.level.update( delta_time )


    def handle(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                self.run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.run = False
            if event.type == pygame.JOYBUTTONDOWN:
                # Start button stops.
                if event.button == 9:
                    self.run = False
            if self.level:
                self.level.handle( event )


def main( fullscreen, rotate ):

    """ Main function """

    tron = TronGame( fullscreen, rotate )
    tron.start(2)

    ticks = pygame.time.get_ticks()

    while tron.run:
        now = pygame.time.get_ticks()
        tron.handle()
        tron.update( now - ticks )
        ticks = now
        tron.draw()




if __name__ == "__main__":
    parser = argparse.ArgumentParser( description = 'Tron.' )
    parser.add_argument( '--fullscreen', action='store_true')
    parser.add_argument( '--rotate', action='store_true')
    args = parser.parse_args()
    main(args.fullscreen,args.rotate)
