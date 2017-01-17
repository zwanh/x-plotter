# xplotter_conf.py
# Part of the AxiDraw driver for Inkscape
# Version 1.0, dated Dec 9th, 2016.
#



# Page size values typically do not need to be changed. They primarily affect viewpoint and centering.
# Measured in page pixelssteps.  Default printable area for X-Plotter is A4 page size.

N_PAGE_HEIGHT = 245     # Default page height in inches 	245 mm = about 9.65 inches
N_PAGE_WIDTH = 300      # Default page width in inches 		300 mm = about 11.81 inches


StartPos_X = 0   #parking position, in pixels. Default: 0
StartPos_Y = 0      #parking position, in pixels. Default: 0


#Skip pen-up moves shorter than this distance, when possible:
MIN_GAP = 0.254  #Distance Threshold (millimeters)
