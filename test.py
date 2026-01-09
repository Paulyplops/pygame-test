import sys
import pygame
from enum import IntEnum

class Keys(IntEnum):
    LEFT = 0
    RIGHT = 1
    UP = 2
    DOWN = 3

file = open("out.txt","w")

def log( text ):
    file.write( text + '\n' )
    file.flush()

log("Hello")

pygame.init()

pygame.mouse.set_visible(False) 

pygame.joystick.init()

black = 0, 0, 0

speed = 1

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


font_size = 30
# pygame.joystick.init()
# font = pygame.font.SysFont("Futura", font_size)
font = None

def draw_text(text, font, text_col, x, y):
     #img = font.render(text, True, text_col)
    #screen.blit(img, (x, y))
    log(text)



run = True

while run:
    msg = ""
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
            msg = str( event.instance_id ) + " " + str( event.button )
            if event.button == 11:
                player.speed = [0, -speed]
            if event.button == 12:
                player.speed = [0, +speed]
            if event.button == 13:
                player.speed = [+speed, 0]
            if event.button == 14:
                player.speed = [-speed, 0]


    for player in players:
        player.position[0] += player.speed[0]
        player.position[1] += player.speed[1]
        if player.position[0] < 0 or player.position[0] > width:
            player.speed[0] = -player.speed[0]
        if player.position[1] < 0 or player.position[1] > height:
            player.speed[1] = -player.speed[1]


    screen.fill(black)

    draw_text("Controllers: " + str(pygame.joystick.get_count()), font, pygame.Color("azure"), 10, 10)
    draw_text("Button: " + msg, font, pygame.Color("azure"), 10, 35)
    for joystick in joysticks:
        if joystick:
            draw_text("Controller Type: " + str(joystick.get_name()), font, pygame.Color("azure"), 10, 60)
            draw_text("Number of axes: " + str(joystick.get_numaxes()), font, pygame.Color("azure"), 10, 85)


    for player in players:
        pygame.draw.rect( screen, player.col, pygame.Rect( player.position[0], player.position[1], 100, 100) )
    pygame.display.flip()


file.close()
