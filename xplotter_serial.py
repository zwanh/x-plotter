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

import inkex
import serial
import gettext
import time

def findPort():
	try:
		from serial.tools.list_ports import comports
	except ImportError:
		comports = None
		return None
	
	if comports:
		comPortsList = list(comports())
		xplotterPort = None

		for port in comPortsList:
			if port[1].startswith("USB2.0-Serial"):
				xplotterPort = port[0]
				break				# break when done
		if xplotterPort is not None:
			for port in comPortsList:
				if port[2].startswith("USB VID:PID=1A86:7523"):
					xplotterPort = port[0]
					break
	return xplotterPort
		
def testPort(comPort):
	if comPort is not None:
		try:
			serialPort = serial.Serial(comPort, 115200, timeout=1)
			time.sleep(5)
			serialPort.reset_input_buffer()
			serialPort.write("\x18\x0A")
			strFirmware = serialPort.readline()
			if strFirmware and strFirmware.startswith('Grbl'):
				serialPort.reset_input_buffer()
				return serialPort
			serialPort.close()
		except serial.SerialException:
			pass
		return None
	else:
		return None
			

def openPort():
	foundPort = findPort()
	serialPort = testPort(foundPort)
	if serialPort:
		return serialPort
	return None


def closePort(comPort):
	if comPort is not None:
		try:
			comPort.close()
		except serial.SerialException:
			pass


def command(comPort, cmd):
	if (comPort is not None) and (cmd is not None):
		try:
			comPort.write(cmd)
			response = comPort.readline()
			nRetryCnt = 0
			while (len(response) == 0) and (nRetryCnt < 20):
				response = comPort.readline()
				nRetryCnt += 1
			
			if response.strip().startswith("ok"):
				pass
		
		except:
			inkex.errormsg('Failed after command:' + cmd)
			pass	
