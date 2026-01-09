import sys
import pygame
from enum import IntEnum

class Keys(IntEnum):
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3

pygame.init()

pygame.mouse.set_visible(False) 

pygame.joystick.init()

black = 0, 0, 0

speed = 1
deadzone = 0.1

info = pygame.display.Info()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)

width, height = info.current_w, info.current_h

joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
joysticks += [None] * (2-len(joysticks))

class Player:
    def __init__(self, position, keys, col, joystick):
        self.position = position
        self.speed = [0,0]
        self.keys = keys
        self.col = col
        self.joystick = joystick


players = [
            Player( [100,300], [pygame.K_a,pygame.K_d,pygame.K_w,pygame.K_s], "royalblue", joysticks[0] ),
            Player( [300,100], [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN ], "red", joysticks[1] )
    ]

lookup = {}

if joysticks[0]:
    lookup[ joysticks[0].get_instance_id() ] = 0
if joysticks[1]:
    lookup[ joysticks[1].get_instance_id() ] = 1



run = True

while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                run = False
            for player in players:
                if event.key == player.keys[ Keys.UP ]:
                    player.speed = [0, -speed]
                if event.key == player.keys[ Keys.DOWN ]:
                    player.speed = [0, +speed]
                if event.key == player.keys[ Keys.RIGHT ]:
                    player.speed = [+speed, 0]
                if event.key == player.keys[ Keys.LEFT ]:
                    player.speed = [-speed, 0]
        if event.type == pygame.JOYBUTTONDOWN:
            player = players[ lookup[ event.instance_id ]]
            if event.button == 9:
                run = False
        if event.type == pygame.JOYAXISMOTION:
            player = players[ lookup[ event.instance_id ]]
            if player.joystick.get_axis(0) < -deadzone:
                player.speed = [0, +speed]
            if player.joystick.get_axis(0) > deadzone:
                player.speed = [0, -speed]
            if player.joystick.get_axis(1) < -deadzone:
                player.speed = [-speed, 0]
            if player.joystick.get_axis(1) > deadzone:
                player.speed = [+speed, 0]

    for player in players:
        player.position[0] += player.speed[0]
        player.position[1] += player.speed[1]
        if player.position[0] < 0 or player.position[0] > width:
            player.speed[0] = -player.speed[0]
        if player.position[1] < 0 or player.position[1] > height:
            player.speed[1] = -player.speed[1]


    screen.fill(black)

    for player in players:
        pygame.draw.rect( screen, player.col, pygame.Rect( player.position[0], player.position[1], 100, 100) )
    pygame.display.flip()


