# The MIT License (MIT)
# 
# Copyright (c) 2016 Pinecone Robotics
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

from simpletransform import *
import inkex
import simplepath
import string

import xplotter_serial
import xplotter_motion
import plot_utils

import xplotter_conf


class XPER(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)

		self.OptionParser.add_option("--tab",
			action="store", type="string",
			dest="tab", default="controls",
			help="The active tab when Apply was pressed")

		self.OptionParser.add_option("--penUpPosition",
			action="store", type="int",
			dest="penUpPosition", default=160,
			help="Position of pen when lifted")
		
		self.OptionParser.add_option("--penDownPosition",
			action="store", type="int",
			dest="penDownPosition", default=140,
			help="Position of pen for painting")
		
		self.OptionParser.add_option("--travellingSpeed",
			action="store", type="int",
			dest="travellingSpeed", default=50,
			help="speed for painting")

		self.svgHeight = 0
		self.svgWidth = 0		

		self.xBoundsMin = xplotter_conf.StartPos_X
		self.xBoundsMax = xplotter_conf.N_PAGE_WIDTH
		self.yBoundsMin = xplotter_conf.StartPos_Y
		self.yBoundsMax = xplotter_conf.N_PAGE_HEIGHT
		
		self.fCurrX = xplotter_conf.StartPos_X
		self.fCurrY = xplotter_conf.StartPos_Y
		self.ignoreLimits = False

		self.svgLayer = int(0)
		self.plotCurrentLayer = False

		self.serialPort = None

		self.svgTransform = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]

		self.warnOutOfBounds = False


	def effect(self):
		self.svg = self.document.getroot()

		self.serialPort = xplotter_serial.openPort()

		if self.serialPort is None:
			inkex.errormsg("Failed to connect to X-plotter!!!")
		
		if self.options.tab == '"plot"':
			xplotter_serial.command(self.serialPort, 'G20')
			self.svgLayer = 12345
			self.plotDocument()
			xplotter_motion.setPenPos(self.serialPort, 150)
			xplotter_motion.doTimedPause(self.serialPort, 1000)
			self.plotSegment(0.4, 0.4)	
		
		elif self.options.tab == '"setup"':
			xplotter_serial.command(self.serialPort, 'G20')
			self.testPenPos()
		
		if self.serialPort is not None:
			xplotter_serial.closePort(self.serialPort)			

	def plotDocument(self):
		if self.serialPort is None:
			return
		
		if (not self.getDocProps()):
			# Cannot handle the document's dimensions!!!
			inkex.errormsg( gettext.gettext(
			'This document does not have valid dimensions.\r' +
			'The document dimensions must be in either' +
			'millimeters (mm) or inches (in).\r\r'	+			
			'Consider starting with the "Letter landscape" or ' +
			'the "A4 landscape" template.\r\r' +
			'Document dimensions may also be set in Inkscape,\r' +
			'using File > Document Properties.') )
			return

		# Viewbox handling
		# Also ignores the preserveAspectRatio attribute
		viewbox = self.svg.get('viewBox')
		if viewbox:
			vinfo = viewbox.strip().replace(',', ' ').split(' ')
			offsetx = -float(vinfo[0])
			offsety = -float(vinfo[1])
			
			if (vinfo[2] != 0) and (vinfo[3] != 0):
				sx = self.svgWidth / float(vinfo[2])
				sy = self.svgHeight / float(vinfo[3])
			else:
				sx = 1.0 / float(plot_utils.pxPerInch)
				sy = sx
				offsetx = 0.0
				offsety = 0.0
		self.svgTransform = parseTransform('scale(%f,%f) translate(%f,%f)' % (sx, sy, offsetx, offsety))
		
		try:
			self.recursivelyTraverseSvg(self.svg, self.svgTransform)			
		
		finally:
			pass

	def getDocProps(self):
		"""
		Get the document's height and width attributes from the <svg> tag.
		Use a default value in case the property is not present or is 
		expressed in units of percentages
		"""
		self.svgHeight = plot_utils.getLengthInches(self, 'height')
		self.svgWidth = plot_utils.getLengthInches(self, 'width')
		if(self.svgHeight == None) or (self.svgWidth == None):
			return False
		else:
			return True

	

	def DoWePlotLayer(self, strLayerName):
		"""
		Parse layer name for layer number .
		
		First: scan layer name for first non-numeric character,
		and scan the part before that (if any) into a number
		Then, (if not printing all layers)
		see if the number matches the layer number that we are printing.
		
		"""

		# Look at layer name.  Sample first character, then first two, and
		# so on, until the string ends or the string no longer consists of digit characters only.
		TempNumString = 'x'
		stringPos = 1	
		layerNameInt = -1
		layerMatch = False	
		CurrentLayerName = string.lstrip(strLayerName.encode('ascii', 'ignore')) #remove leading whitespace
	
		MaxLength = len(CurrentLayerName)
		if MaxLength > 0:
			while stringPos <= MaxLength:
				if str.isdigit(CurrentLayerName[:stringPos]):
					TempNumString = CurrentLayerName[:stringPos] # Store longest numeric string so far
					stringPos = stringPos + 1
				else:
					break

		self.plotCurrentLayer = True    #Temporarily assume that we are plotting the layer
	
		if (str.isdigit(TempNumString)):
			layerNameInt = int(float(TempNumString))
			if (self.svgLayer == layerNameInt):
				layerMatch = True	#Match! The current layer IS named in the Layers tab.
			
			elif (self.svgLayer == 12345):
				layerMatch = True
				
		if (layerMatch == False):
			self.plotCurrentLayer = False
	



	def recursivelyTraverseSvg(self, aNodeList,
			matCurrent=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
			parent_visibility='visible'):
		"""
		Recursively traverse the svg file to plot out all of the
		paths.  The function keeps track of the composite transformation
		that should be applied to each path.

		This function handles path, group, line, rect, polyline, polygon,
		circle, ellipse and use (clone) elements.  Notable elements not
		handled include text.  Unhandled elements should be converted to
		paths in Inkscape.
		"""
		for node in aNodeList:
			# Ignore invisible nodes
			v = node.get('visibility', parent_visibility)
			if v == 'inherit':
				v = parent_visibility
			if v == 'hidden' or v == 'collapse':
				pass

			# first apply the current matrix transform to this node's transform
			matNew = composeTransform(matCurrent, parseTransform(node.get("transform")))

			if node.tag == inkex.addNS('g', 'svg') or node.tag == 'g':

				if (node.get(inkex.addNS('groupmode', 'inkscape')) == 'layer'): 
					self.sCurrentLayerName = node.get(inkex.addNS('label', 'inkscape'))
					self.DoWePlotLayer(self.sCurrentLayerName )
				self.recursivelyTraverseSvg(node, matNew, parent_visibility=v)		

			elif node.tag == inkex.addNS('use', 'svg') or node.tag == 'use':

				# A <use> element refers to another SVG element via an xlink:href="#blah"
				# attribute.  We will handle the element by doing an XPath search through
				# the document, looking for the element with the matching id="blah"
				# attribute.  We then recursively process that element after applying
				# any necessary (x,y) translation.
				#
				# Notes:
				#  1. We ignore the height and width attributes as they do not apply to
				#     path-like elements, and
				#  2. Even if the use element has visibility="hidden", SVG still calls
				#     for processing the referenced element.  The referenced element is
				#     hidden only if its visibility is "inherit" or "hidden".

				refid = node.get(inkex.addNS('href', 'xlink'))
				if refid:
					# [1:] to ignore leading '#' in reference
					path = '//*[@id="%s"]' % refid[1:]
					refnode = node.xpath(path)
					if refnode:
						x = float(node.get('x', '0'))
						y = float(node.get('y', '0'))
						# Note: the transform has already been applied
						if (x != 0) or (y != 0):
							matNew2 = composeTransform(matNew, parseTransform('translate(%f,%f)' % (x,y)))
						else:
							matNew2 = matNew
						v = node.get('visibility', v)
						self.recursivelyTraverseSvg(refnode, matNew2, parent_visibility=v)
					else:
						pass
				else:
					pass
			elif self.plotCurrentLayer:	#Skip subsequent tag checks unless we are plotting this layer.
				if node.tag == inkex.addNS('path', 'svg'):
	
					# if we're in resume mode AND self.pathcount < self.svgLastPath,
					#    then skip over this path.
					# if we're in resume mode and self.pathcount = self.svgLastPath,
					#    then start here, and set self.nodeCount equal to self.svgLastPathNC
					
					self.plotPath(node, matNew)
					
				elif node.tag == inkex.addNS('rect', 'svg') or node.tag == 'rect':
	
					# Manually transform 
					#    <rect x="X" y="Y" width="W" height="H"/> 
					# into 
					#    <path d="MX,Y lW,0 l0,H l-W,0 z"/> 
					# I.e., explicitly draw three sides of the rectangle and the
					# fourth side implicitly
	
					# Create a path with the outline of the rectangle
					newpath = inkex.etree.Element(inkex.addNS('path', 'svg'))
					x = float(node.get('x'))
					y = float(node.get('y'))
					w = float(node.get('width'))
					h = float(node.get('height'))
					s = node.get('style')
					if s:
						newpath.set('style', s)
					t = node.get('transform')
					if t:
						newpath.set('transform', t)
					a = []
					a.append(['M ', [x, y]])
					a.append([' l ', [w, 0]])
					a.append([' l ', [0, h]])
					a.append([' l ', [-w, 0]])
					a.append([' Z', []])
					newpath.set('d', simplepath.formatPath(a))
					self.plotPath(newpath, matNew)
						
				elif node.tag == inkex.addNS('line', 'svg') or node.tag == 'line':
	
					# Convert
					#
					#   <line x1="X1" y1="Y1" x2="X2" y2="Y2/>
					#
					# to
					#
					#   <path d="MX1,Y1 LX2,Y2"/>
	
					# Create a path to contain the line
					newpath = inkex.etree.Element(inkex.addNS('path', 'svg'))
					x1 = float(node.get( 'x1' ))
					y1 = float(node.get( 'y1' ))
					x2 = float(node.get( 'x2' ))
					y2 = float(node.get( 'y2' ))
					s = node.get('style')
					if s:
						newpath.set('style', s)
					t = node.get('transform')
					if t:
						newpath.set('transform', t)
					a = []
					a.append(['M ', [x1, y1]])
					a.append([' L ', [x2, y2]])
					newpath.set('d', simplepath.formatPath(a))
					self.plotPath(newpath, matNew)
						
	
				elif node.tag == inkex.addNS('polyline', 'svg') or node.tag == 'polyline':
	
					# Convert
					#  <polyline points="x1,y1 x2,y2 x3,y3 [...]"/> 
					# to 
					#   <path d="Mx1,y1 Lx2,y2 Lx3,y3 [...]"/> 
					# Note: we ignore polylines with no points
	
					pl = node.get('points', '').strip()
					if pl == '':
						pass
					
					pa = pl.split()
					if not len(pa):
						pass
					# Issue 29: pre 2.5.? versions of Python do not have
					#    "statement-1 if expression-1 else statement-2"
					# which came out of PEP 308, Conditional Expressions
					#d = "".join( ["M " + pa[i] if i == 0 else " L " + pa[i] for i in range( 0, len( pa ) )] )
					d = "M " + pa[0]
					for i in range(1, len(pa)):
						d += " L " + pa[i]
					newpath = inkex.etree.Element(inkex.addNS('path', 'svg'))
					newpath.set('d', d );
					s = node.get('style')
					if s:
						newpath.set('style', s)
					t = node.get('transform')
					if t:
						newpath.set('transform', t)
					self.plotPath(newpath, matNew)
	
				elif node.tag == inkex.addNS('polygon', 'svg') or node.tag == 'polygon':
	
					# Convert 
					#  <polygon points="x1,y1 x2,y2 x3,y3 [...]"/> 
					# to 
					#   <path d="Mx1,y1 Lx2,y2 Lx3,y3 [...] Z"/> 
					# Note: we ignore polygons with no points
	
					pl = node.get('points', '').strip()
					if pl == '':
						pass
	
					pa = pl.split()
					if not len(pa):
						pass
					# Issue 29: pre 2.5.? versions of Python do not have
					#    "statement-1 if expression-1 else statement-2"
					# which came out of PEP 308, Conditional Expressions
					#d = "".join( ["M " + pa[i] if i == 0 else " L " + pa[i] for i in range( 0, len( pa ) )] )
					d = "M " + pa[0]
					for i in range(1, len(pa)):
						d += " L " + pa[i]
					d += " Z"
					newpath = inkex.etree.Element(inkex.addNS('path', 'svg'))
					newpath.set('d', d);
					s = node.get('style')
					if s:
						newpath.set('style', s)
					t = node.get('transform')
					if t:
						newpath.set('transform', t)
					self.plotPath(newpath, matNew)
					
				elif node.tag == inkex.addNS('ellipse', 'svg') or node.tag == 'ellipse' or node.tag == inkex.addNS('circle', 'svg') or node.tag == 'circle':
	
						# Convert circles and ellipses to a path with two 180 degree arcs.
						# In general (an ellipse), we convert 
						#   <ellipse rx="RX" ry="RY" cx="X" cy="Y"/> 
						# to 
						#   <path d="MX1,CY A RX,RY 0 1 0 X2,CY A RX,RY 0 1 0 X1,CY"/> 
						# where 
						#   X1 = CX - RX
						#   X2 = CX + RX 
						# Note: ellipses or circles with a radius attribute of value 0 are ignored
	
					if node.tag == inkex.addNS('ellipse', 'svg') or node.tag == 'ellipse':
						rx = float(node.get('rx', '0'))
						ry = float(node.get('ry', '0'))
					else:
						rx = float(node.get('r', '0'))
						ry = rx
					if rx == 0 or ry == 0:
						pass
	
					cx = float(node.get('cx', '0'))
					cy = float(node.get('cy', '0'))
					x1 = cx - rx
					x2 = cx + rx
					d = 'M %f,%f ' % (x1, cy) + 'A %f,%f ' % (rx, ry) + '0 1 0 %f,%f ' % (x2, cy) + 'A %f,%f ' % (rx, ry) + '0 1 0 %f,%f' % (x1, cy)
					newpath = inkex.etree.Element(inkex.addNS('path', 'svg'))
					newpath.set('d', d);
					s = node.get('style')
					if s:
						newpath.set('style', s)
					t = node.get('transform')
					if t:
						newpath.set('transform', t)
					self.plotPath(newpath, matNew)
							
								
				elif node.tag == inkex.addNS('metadata', 'svg') or node.tag == 'metadata':
					pass
				elif node.tag == inkex.addNS('defs', 'svg') or node.tag == 'defs':
					pass
				elif node.tag == inkex.addNS('namedview', 'sodipodi') or node.tag == 'namedview':
					pass
				elif node.tag == inkex.addNS('WCB', 'svg') or node.tag == 'WCB':
					pass
				elif node.tag == inkex.addNS('eggbot', 'svg') or node.tag == 'eggbot':
					pass			
				elif node.tag == inkex.addNS('title', 'svg') or node.tag == 'title':
					pass
				elif node.tag == inkex.addNS('desc', 'svg') or node.tag == 'desc':
					pass
				elif (node.tag == inkex.addNS('text', 'svg') or node.tag == 'text' or
					node.tag == inkex.addNS('flowRoot', 'svg') or node.tag == 'flowRoot'):
					if (not self.warnings.has_key('text')) and (self.plotCurrentLayer):
						inkex.errormsg( gettext.gettext( 'Warning: in layer "' + 
							self.sCurrentLayerName + '" unable to draw text; ' +
							'Please convert text to a path before drawing, using \n' +
							'Path > Object to Path. Or, use the Hershey Text extension, '+
							'which can be found under Extensions > Render.' ) )
						self.warnings['text'] = 1
					pass
				elif node.tag == inkex.addNS('image', 'svg') or node.tag == 'image':
					if (not self.warnings.has_key('image')) and (self.plotCurrentLayer):
						inkex.errormsg( gettext.gettext('Warning: in layer "' + 
						self.sCurrentLayerName + '" unable to draw bitmap images; ' +
						'Please convert images to line art before drawing. ' +
						' Consider using the Path > Trace bitmap tool. ' ) )
						self.warnings['image'] = 1
					pass
				elif node.tag == inkex.addNS('pattern', 'svg') or node.tag == 'pattern':
					pass
				elif node.tag == inkex.addNS('radialGradient', 'svg') or node.tag == 'radialGradient':
					# Similar to pattern
					pass
				elif node.tag == inkex.addNS('linearGradient', 'svg') or node.tag == 'linearGradient':
					# Similar in pattern
					pass
				elif node.tag == inkex.addNS('style', 'svg') or node.tag == 'style':
					# This is a reference to an external style sheet and not the value
					# of a style attribute to be inherited by child elements
					pass
				elif node.tag == inkex.addNS('cursor', 'svg') or node.tag == 'cursor':
					pass
				elif node.tag == inkex.addNS('color-profile', 'svg') or node.tag == 'color-profile':
					# Gamma curves, color temp, etc. are not relevant to single color output
					pass
				elif not isinstance(node.tag, basestring):
					# This is likely an XML processing instruction such as an XML
					# comment.  lxml uses a function reference for such node tags
					# and as such the node tag is likely not a printable string.
					# Further, converting it to a printable string likely won't
					# be very useful.
					pass
				else:
					if (not self.warnings.has_key(str(node.tag))) and (self.plotCurrentLayer):
						t = str(node.tag).split('}')
						inkex.errormsg( gettext.gettext( 'Warning: in layer "' + 
							self.sCurrentLayerName + '" unable to draw <' + str(t[-1]) +
							'> object, please convert it to a path first.'))
						self.warnings[str(node.tag)] = 1
					pass





	def plotPath(self, path, matTransform):
		'''
		Plot the path while applying the transformation defined
		by the matrix [matTransform].
		'''
		# turn this path into a cubicsuperpath (list of beziers)...

		d = path.get('d')
		if len(simplepath.parsePath(d)) == 0:
			return

		if self.plotCurrentLayer:
			p = cubicsuperpath.parsePath(d)

			# ...and apply the transformation to each point
			applyTransformToPath(matTransform, p)
	
			# p is now a list of lists of cubic beziers [control pt1, control pt2, endpoint]
			# where the start-point is the last point in the previous segment.
			for sp in p:
			
				plot_utils.subdivideCubicPath(sp, 0.02)
				nIndex = 0

				singlePath = []		
				if self.plotCurrentLayer:
					for csp in sp:

						fX = (self.svgWidth) - float(csp[1][0]) # Set move destination
						fY = float(csp[1][1])
						
						if nIndex == 0:
							if (plot_utils.distance(fX-self.fCurrX, fY-self.fCurrY) > xplotter_conf.MIN_GAP):
								xplotter_motion.setPenPos(self.serialPort, 150)
								xplotter_motion.doTimedPause(self.serialPort, 1000)
						
						elif nIndex == 1:
							xplotter_motion.setPenPos(self.serialPort, 100)
							xplotter_motion.doTimedPause(self.serialPort, 1000)
						
						nIndex += 1
						
						self.plotSegment(fX, fY)	
						
						self.fCurrX = fX
						self.fCurrY = fY						


	def plotSegment(self, xDest, yDest):

		#check page size limits:
		if (self.ignoreLimits == False):
			xDest, xBounded = plot_utils.checkLimits(xDest, self.xBoundsMin, self.xBoundsMax)
			yDest, yBounded = plot_utils.checkLimits(yDest, self.yBoundsMin, self.yBoundsMax)
			if (xBounded or yBounded):
				self.warnOutOfBounds = True

		if self.warnOutOfBounds:
			inkex.errormsg('Warning:out of bounds!')			

		xplotter_motion.doXYMove(self.serialPort, xDest, yDest, self.options.travellingSpeed)			

	def testPenPos(self):
		self.plotSegment(1,1)
		xplotter_motion.setPenPos(self.serialPort, self.options.penDownPosition)
		xplotter_motion.doTimedPause(self.serialPort, 500)
		self.plotSegment(2,2)
		xplotter_motion.setPenPos(self.serialPort, self.options.penUpPosition)
		xplotter_motion.doTimedPause(self.serialPort, 500)
		self.plotSegment(1,1)
		


e = XPER()
e.affect()
		
