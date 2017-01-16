# xplotter_conf.py
# Part of the AxiDraw driver for Inkscape
# Version 1.1.0, dated August 9, 2016.
#
# https://github.com/evil-mad/AxiDraw
#
# "Change numbers here, not there." :)



# Page size values typically do not need to be changed. They primarily affect viewpoint and centering.
# Measured in page pixelssteps.  Default printable area for AxiDraw is 300 x 218 mm

N_PAGE_HEIGHT = 8.58     # Default page height in inches 	218 mm = about 8.58 inches
N_PAGE_WIDTH = 11.81      # Default page width in inches 	300 mm = about 11.81 inches


StartPos_X = 0   #parking position, in pixels. Default: 0
StartPos_Y = 0      #parking position, in pixels. Default: 0


#Skip pen-up moves shorter than this distance, when possible:
MIN_GAP = 0.010  #Distance Threshold (inches)
