import sys
import pygame
from enum import IntEnum
import argparse
import random
import math
import json

SCREEN_WIDTH = 1152
SCREEN_HEIGHT = 864
SCREEN_TITLE = "Tron"
DEADZONE = 0.1
BLACK = 0, 0, 0
LINE_WIDTH = 3
SECONDS_DECAY = 3
MS_DECAY = SECONDS_DECAY * 1000.0
FONT_SIZE = 50
MARGIN = 10
WINNER_BONUS = 500
TIME_BONUS = 10
ROLL_ON_TIME = 3000

pygame.init()

pygame.mouse.set_visible(False) 

pygame.joystick.init()

font = pygame.image.load("reduction-rotated.bmp")

highscores = {}

try:
    with open('highscores.json','r') as f:
        highscores = json.load( f )
except FileNotFoundError:
    pass

def write( surface, x, y, text, centered = False ):
    if centered:
        y += len(text) * FONT_SIZE // 2
    for l in range(0,len(text)):
        letter = text[l]
        i = ord( letter ) - 32
        a = (i // 10 * FONT_SIZE)
        b = font.get_height() - (i % 10 * FONT_SIZE) - FONT_SIZE
        surface.blit( font, (x, y-l*FONT_SIZE - FONT_SIZE), (a,b,FONT_SIZE,FONT_SIZE) )

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


def check( player, opponent ):
    for previous, current in zip( opponent.path, opponent.path[1:]):
        if opponent != player and collision( (player.pos, player.path[-1]), opponent.path ):
            return True
        elif collision( (player.pos, player.path[-1]), opponent.path[:-2] ):
            return True

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

class Boundary:
    def __init__( self, path ):
        self.path = path

class Player:
    def __init__(self, keys, start, vel, col, name ):
        self.keys = keys
        self.pos = start
        self.vel = vel
        self.col = pygame.Color(col)
        self.name = name
        self.path = [ start, start ]
        self.joystick = None
        self.time_of_death = 0
        self.score = 0
        self.bonus = 0

class ScoreScreen():

    def __init__( self, players ):
        self.players = players
        self.alphabet = "-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        self.wheel_offsets = [0,0]
        self.wheel_vels = [0,0]

        self.letters = [[0,0,0],[0,0,0]]
        self.columns = [0,0]
        self.shift = [0,0]


    def draw(self, width, height, surface):

        write( surface, MARGIN, height - MARGIN, str(int(self.players[0].score) ) )
        write( surface, MARGIN, height // 2 - MARGIN, str(int(self.players[1].score) ) )

        if self.players[1].time_of_death:
            write( surface, 100, height * 3 // 4, self.players[0].name, True)
            write( surface, 100 + FONT_SIZE + MARGIN, height * 3 // 4, "WINS!", True)
                
        if self.players[0].time_of_death:
            write( surface, 100, height // 4, self.players[1].name, True )
            write( surface, 100 + FONT_SIZE + MARGIN, height // 4, "WINS!", True )

        f = FONT_SIZE * 3 // 2

        for p in range(0,2):
            for c in range(0,3):
                if c != self.columns[p]:
                    l = self.letters[p][c] 
                    y = c * FONT_SIZE - f
                    write( surface, 500, height * 3 // 4 - p * height // 2 - y, self.alphabet[ l ] )
            if self.columns[p] == 3:
                pygame.draw.rect( surface, [255,255,255], 
                          [ 500 + 10, height * 3 // 4 - p * height // 2 - f - 10, 
                           20,20 ])


                continue
            for letter in range(-4,+4):
                l = ( self.letters[p][self.columns[p]] + letter ) % len( self.alphabet )
                x = letter * FONT_SIZE + self.wheel_offsets[p]
                y = self.columns[p] * FONT_SIZE - f
                write( surface, 500 + x, height * 3 // 4 - p * height // 2 - y, self.alphabet[ l ] )

        m = 15
        pygame.draw.lines( surface, [0,0,255], True, [
                          [ 500 + FONT_SIZE, height // 4 - f], 
                          [ 500 + FONT_SIZE, height // 4 + f + m ], 
                          [ 500 - m, height // 4 + f + m ], 
                          [ 500 - m, height // 4 - f] ] , LINE_WIDTH)

        pygame.draw.lines( surface, [255,0,0], True, [
                          [ 500 + FONT_SIZE, height * 3 // 4 - f ], 
                          [ 500 + FONT_SIZE, height * 3 // 4 + f + m ], 
                          [ 500 - m, height * 3 // 4 + f + m ], 
                          [ 500 - m, height * 3 // 4 - f] ] , LINE_WIDTH)

        pygame.draw.line( surface, [255,255,0], [ MARGIN * 2 + FONT_SIZE, height // 2 ], [ width - MARGIN, height // 2 ], LINE_WIDTH)

    def update( self, delta_time):
        delta = delta_time
        for player in self.players:
            delta_score = 0
            if player.bonus > delta:
                delta_score = delta
                player.bonus -= delta
            else:
                delta_score = player.bonus
                player.bonus = 0
            player.score += delta_score


        for p in range(0,2):
            l = int( self.wheel_offsets[p] / FONT_SIZE )
            if l:
                self.letters[p][self.columns[p]] = ( self.letters[p][self.columns[p]] - l ) % len( self.alphabet )
                self.wheel_offsets[p] -= FONT_SIZE * l

        for p in range(0,2):
            self.wheel_offsets[p] += self.wheel_vels[p] * delta_time / 1000.0
            self.wheel_offsets[p] *= math.pow( math.e, - delta_time / 1000.0 * 1 )
            self.wheel_vels[p] *= math.pow( math.e, - delta_time / 1000.0 * 10 )


    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self.columns[0] == 3 and self.columns[1] == 3:
                    self.save()
            for p in range(0,2):
                if self.columns[p] == 3:
                    continue
                player = self.players[p]
                if event.key == player.keys[ Keys.RIGHT ]:
                    self.wheel_vels[p] = -800
                if event.key == player.keys[ Keys.LEFT ]:
                    self.wheel_vels[p] = +800
        if event.type == pygame.KEYUP:
            for p in range(0,2):
                player = self.players[p]
                if event.key == player.keys[ Keys.UP ]:
                    self.columns[p] = min( self.columns[p] + 1, 3 )
                if event.key == player.keys[ Keys.DOWN ]:
                    self.columns[p] = max( self.columns[p] - 1, 0 )
        if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    if self.columns[0] == 3 and self.columns[1] == 3:
                        self.save()
        if event.type == pygame.JOYAXISMOTION:
            p = event.instance_id
            player = self.players[p]
            if player.joystick.get_axis(0) < -DEADZONE and abs( player.joystick.get_axis(1) ) < DEADZONE:
                self.shift[p] = -1
            if player.joystick.get_axis(0) > DEADZONE and abs( player.joystick.get_axis(1) ) < DEADZONE:
                self.shift[p] = +1
            if self.columns[p] != 3:
                if player.joystick.get_axis(1) < -DEADZONE and abs( player.joystick.get_axis(0) ) < DEADZONE:
                    self.wheel_vels[p] = +800
                if player.joystick.get_axis(1) > DEADZONE and abs( player.joystick.get_axis(0) ) < DEADZONE:
                    self.wheel_vels[p] = -800
            if abs(player.joystick.get_axis(0) ) < DEADZONE and abs( player.joystick.get_axis(1) ) < DEADZONE and self.shift[p] != 0:
                self.columns[p] = max( min( self.columns[p] + self.shift[p], 3 ), 0 )

    
    def save(self):
        scores = {}
        names=["",""]
        for p in range(0,2):
            name = ""
            for l in self.letters[p]:
                name += self.alphabet[l]
            score = self.players[p].score
            scores[name] = score
            names[p] = name

        for p in range(0,2):
            name = names[p]
            other = names[(p+1)%2]
            if name not in highscores:
                highscores[name] = {}
            highscores[name][other] = scores[name]
       
        with open('highscores.json','w') as f:
            json.dump( highscores, f )



        

class Level():

    def __init__(self, width, height):

        self.speed = height * 0.1
        self.time = 0

        self.particles = []

        self.players = [
                    Player( [pygame.K_a,pygame.K_d,pygame.K_w,pygame.K_s], [width*0.2, height*0.5], [self.speed,0], (230,20,20), "RED" ),
                    Player( [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN ], [width*0.8,height*0.5], [-self.speed,0], (20,20,230), "BLUE" )
            ]

        border = 20
        self.boundary = Boundary( [ [ 50 + border, border], [ 50 + border, height - border ], [ width - border, height - border ], [width - border, border], [ 50 + border, border] ] )

        self.lookup = { pygame.joystick.Joystick(x).get_instance_id() : self.players[x]  for x in range(pygame.joystick.get_count()) }

        for x in range(pygame.joystick.get_count()):
            self.players[x].joystick = pygame.joystick.Joystick(x)

    def draw(self, width, height, surface):
        pygame.draw.lines( surface, [255,255,0], False, self.boundary.path, LINE_WIDTH)

        for player in self.players:
            if not player.time_of_death:
                pygame.draw.lines( surface, player.col, False, player.path, LINE_WIDTH)
                pygame.draw.rect( surface, player.col, pygame.Rect( player.pos[0]-2, player.pos[1]-2, 5, 5) )
            else:
                col = player.col
                col.a = round( 255 * ( 1.0 - min(self.time - player.time_of_death, MS_DECAY) / MS_DECAY ) )
                pygame.draw.lines( surface, col, False, player.path, LINE_WIDTH)

        for particle in self.particles:
            SPARKLE = 100
            r = limit( 300 * particle.heat + jitter() * SPARKLE )
            g = limit( 300 * particle.heat + jitter() * SPARKLE )
            b = limit( 100 * particle.heat + jitter() * SPARKLE )
            col = particle.col + pygame.Color( r, g, b )  
            col.a = round( 255 * particle.heat )
            surface.set_at( (round(particle.pos[0]),round(particle.pos[1]) ), col )

        write( surface, MARGIN, height - MARGIN, str(int(self.players[0].score) ) )
        write( surface, MARGIN, height // 2 - MARGIN, str(int(self.players[1].score) ) )

    def update( self, delta_time):
        self.time += delta_time
        time_of_death = 0

        for player in self.players:
            if player.time_of_death:
                if time_of_death:
                    time_of_death = min( player.time_of_death, time_of_death)
                else:
                    time_of_death = player.time_of_death
                continue
            player.pos = ( 
                player.pos[0] + player.vel[0] * delta_time / 1000, 
                player.pos[1] + player.vel[1] * delta_time / 1000)
        
            if check( player, self.boundary ):
                self.crash(player)

            for opponent in self.players:
                if check( player, opponent ):
                    self.crash(player)

            player.path[-1] = player.pos

        for particle in self.particles:
            particle.pos = ( 
                particle.pos[0] + particle.vel[0] * delta_time / 1000.0, 
                particle.pos[1] + particle.vel[1] * delta_time / 1000.0)
            particle.vel = ( 
                particle.vel[0] * 0.99, 
                particle.vel[1] * 0.99)
            particle.heat *= math.pow( math.e, - delta_time / 1000.0 )

        if time_of_death and self.time - time_of_death > ROLL_ON_TIME:
            for player in self.players:
                if player.time_of_death:
                    player.bonus += player.time_of_death * TIME_BONUS // 1000
                else:
                    player.bonus += self.time * TIME_BONUS // 1000

            return ScoreScreen( self.players )


    def crash( self, player ):
        if player.time_of_death:
            return

        for opponent in self.players:
            if opponent != player:
                opponent.bonus += WINNER_BONUS

        for i in range(0,10):
            particle = Particle( player.pos, player.vel, pygame.Color( player.col ) )
            particle.pos = player.pos
            particle.vel = ( player.vel[0] + jitter() * self.speed * 5, 
                             player.vel[1] + jitter() * self.speed * 5 )
            self.particles.append( particle )
        player.vel = [0,0]
        player.time_of_death = self.time


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
                if player.joystick.get_axis(0) < -DEADZONE and abs( player.joystick.get_axis(1) ) < DEADZONE and player.vel[0] != 0:
                    vel = [0, +self.speed]
                if player.joystick.get_axis(0) > DEADZONE and abs( player.joystick.get_axis(1) ) < DEADZONE and player.vel[0] != 0:
                    vel = [0, -self.speed]
                if player.joystick.get_axis(1) < -DEADZONE and abs( player.joystick.get_axis(0) ) < DEADZONE and player.vel[1] != 0:
                    vel = [-self.speed, 0]
                if player.joystick.get_axis(1) > DEADZONE and abs( player.joystick.get_axis(0) ) < DEADZONE and player.vel[1] != 0:
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
            if rotate:
                self.screen_width, self.screen_height = SCREEN_HEIGHT, SCREEN_WIDTH
            else:   
                self.screen_width, self.screen_height = SCREEN_WIDTH, SCREEN_HEIGHT
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.DOUBLEBUF)

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

        if self.rotate:
            self.screen.blit( self.background, (0, 0))
            self.screen.blit( pygame.transform.rotate( self.surface, -90 ), (0, 0))
        
        pygame.display.flip()

    def update(self, delta_time):
        
        """ Update state """

        if self.level:
            new_level = self.level.update( delta_time )
            if new_level:
                self.level = new_level


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
