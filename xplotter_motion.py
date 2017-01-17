# The MIT License (MIT)
# 
# Copyright (c) 2016 Evil Mad Scientist Laboratories
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import xplotter_serial

def version():
	return "0.1"	# Version number for this document

def doTimedPause(portName, nPause):
	if(portName is not None):
		strOutput = ' '.join(['G4', 'P'+str(nPause)]) + '\n'
		xplotter_serial.command(portName, strOutput)


def setPenPos(portName, penPos):
	if (portName is not None):
		strOutput = ' '.join(['G1', 'Z'+str(penPos)]) + '\n'
		xplotter_serial.command(portName, strOutput)


def doXYMove(portName, fX, fY, plotSpeed):
	if (portName is not None):
		strOutput = ' '.join(['G1', 'X'+str(fX), 'Y'+str(fY), 'F'+str(plotSpeed)]) + '\n'
		xplotter_serial.command(portName, strOutput)
