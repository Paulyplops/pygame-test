import sys
import pygame

pygame.init ()

if len (sys.argv) < 4  or sys.argv[3] == sys.argv[1]:
    print( "usage: %s fontfile size bitmapfile" % sys.argv[0] )
    sys.exit ()

filename = sys.argv[1]
size = int(sys.argv[2])
outname = sys.argv[3]

font = pygame.font.Font (filename, size)

surface = pygame.Surface( (10 * size, 10 * size), depth=32)
surface.fill ((0, 0, 0))

for i in range( 32, 127 ):
    sf = font.render (chr(i), True, (255, 255, 255))
    x = (i - 32) % 10
    y = (i - 32) // 10
    surface.blit (sf, (x * size, y * size))
pygame.image.save (surface, outname)

