#!/usr/bin/python
print 'Access-Control-Allow-Origin: *'
print 'Content-Type: text/html\n'     # HTML is following
import os
import tempfile
import base64
import cgi
import cgitb
import re
import urllib2
import json
import gd
import pysam
import base64
from random import randint

cgitb.enable()

def generate_colour(start, end, percent):
	# print percent
	start_color = start
	end_color = end

	start_red = int(start[0:2], 16)
	start_green = int(start[2:4], 16)
	start_blue = int(start[4:6], 16)

	#print start_red, start_green, start_blue, "<br/>"

	end_red = int(end[0:2], 16)
	end_green = int(end[2:4], 16)
	end_blue = int(end[4:6], 16)

	#print end_red, end_green, end_blue, "<br/>"

	diff_red = ((end_red - start_red) * percent) + start_red;
	diff_green = ((end_green - start_green) * percent) + start_green;
	diff_blue = ((end_blue - start_blue) * percent) + start_blue;

	#print diff_red, diff_green, diff_blue, "<br/>"

	hex_red = hex(int(diff_red))[2:]
	hex_green = hex(int(diff_green))[2:]
	hex_blue = hex(int(diff_blue))[2:]

	return (diff_red, diff_green, diff_blue)

'''
#
#
# ABSOLUTE RPKM SCALE GENERATOR CODE
#
#
'''
# ----- CONSTANTS -----
EXON_IMG_WIDTH = 100
EXON_IMG_HEIGHT = 15

# The image object
exongraph = gd.image((EXON_IMG_WIDTH, EXON_IMG_HEIGHT))

# Define the colours
white = exongraph.colorAllocate((255,255,255))
gray = exongraph.colorAllocate((80,80,80))
black = exongraph.colorAllocate((0,0,0))

red = exongraph.colorAllocate((220,20,60))
orange = exongraph.colorAllocate((255,140,0))
blue = exongraph.colorAllocate((0,0,255))

green = exongraph.colorAllocate((166,220,166))
darkgreen = exongraph.colorAllocate((0,125,0))

count = 0 # Need a comma if the it is not the first element...
for iiii in range(EXON_IMG_WIDTH):
	variable_colour = exongraph.colorAllocate(generate_colour("FFFF00", "FF0000", float(iiii*1.0/EXON_IMG_WIDTH)))
	exongraph.filledRectangle((iiii, 0), (iiii, EXON_IMG_HEIGHT), variable_colour)

exongraph.string(0, (1, (EXON_IMG_HEIGHT*0.5)-4), "O", black)
exongraph.string(0, (EXON_IMG_WIDTH-15, (EXON_IMG_HEIGHT*0.5)-4), "Max", black)

f = open("get_exon_base64_exongraph.png", "w")
exongraph.writePng(f)
f.close()

printout = ""

with open("get_exon_base64_exongraph.png", "rb") as fl:
	printout = printout + fl.read().encode("base64")

print('<img src="get_exon_base64_exongraph.png" />')
print "</br>"
print "</br>"
print(printout)

fl.close()


'''
#
#
# RELATIVE RPKM SCALE GENERATOR 
#
#
'''
print("<br/><br/>")
# ----- CONSTANTS -----
EXON_IMG_WIDTH = 100
EXON_IMG_HEIGHT = 15

# The image object
exongraph1 = gd.image((EXON_IMG_WIDTH, EXON_IMG_HEIGHT))

# Define the colours
white = exongraph1.colorAllocate((255,255,255))
gray = exongraph1.colorAllocate((80,80,80))
black = exongraph1.colorAllocate((0,0,0))
red = exongraph1.colorAllocate((220,20,60))
orange = exongraph1.colorAllocate((255,140,0))
blue = exongraph1.colorAllocate((0,0,255))
green = exongraph1.colorAllocate((166,220,166))
darkgreen = exongraph1.colorAllocate((0,125,0))

count = 0 # Need a comma if the it is not the first element...
for iiii in range(EXON_IMG_WIDTH):
	if (iiii <= 50):
		variable_colour = exongraph1.colorAllocate(generate_colour("0000FF", "FFFF00", float(iiii*1.0/(EXON_IMG_WIDTH/2))))
		exongraph1.filledRectangle((iiii, 0), (iiii, EXON_IMG_HEIGHT), variable_colour)
	elif (iiii > 50):
		variable_colour = exongraph1.colorAllocate(generate_colour("FFFF00", "FF0000", float(iiii*1.0/(EXON_IMG_WIDTH/2))))
		exongraph1.filledRectangle((iiii, 0), (iiii, EXON_IMG_HEIGHT), variable_colour)

exongraph1.string(0, (1, (EXON_IMG_HEIGHT*0.5)-4), "Min", white)
exongraph1.string(0, (EXON_IMG_WIDTH/2, (EXON_IMG_HEIGHT*0.5)-4), "O", black)
exongraph1.string(0, (EXON_IMG_WIDTH-15, (EXON_IMG_HEIGHT*0.5)-4), "Max", black)

f = open("get_exon_base64_exongraph1.png", "w")
exongraph1.writePng(f)
f.close()

printout = ""

with open("get_exon_base64_exongraph1.png", "rb") as fl:
	printout = printout + fl.read().encode("base64")

print('<img src="get_exon_base64_exongraph1.png" />')
print "</br>"
print "</br>"
print(printout)

fl.close()


print("<br/><br/>")

'''
#
#
# ABSOLUTE RPKM SCALE GENERATOR CODE
#
#
'''
# ----- CONSTANTS -----
EXON_IMG_WIDTH = 180
EXON_IMG_HEIGHT = 15

# The image object
exongraph3 = gd.image((EXON_IMG_WIDTH, EXON_IMG_HEIGHT))

# Define the colours
white = exongraph3.colorAllocate((255,255,255))
gray = exongraph3.colorAllocate((80,80,80))
black = exongraph3.colorAllocate((0,0,0))

red = exongraph3.colorAllocate((220,20,60))
orange = exongraph3.colorAllocate((255,140,0))
blue = exongraph3.colorAllocate((0,0,255))

green = exongraph3.colorAllocate((166,220,166))
darkgreen = exongraph3.colorAllocate((0,125,0))

count = 0 # Need a comma if the it is not the first element...
for iiii in range(EXON_IMG_WIDTH):
	if (iiii < 60):
		exongraph3.filledRectangle((iiii, 0), (iiii, EXON_IMG_HEIGHT), darkgreen)
	elif (iiii > 60 and iiii < 120):
		exongraph3.filledRectangle((iiii, 0), (iiii, EXON_IMG_HEIGHT), green)
	elif (iiii >= 120):
		exongraph3.filledRectangle((iiii, EXON_IMG_HEIGHT*0.66), (EXON_IMG_WIDTH, EXON_IMG_HEIGHT*0.66), black)

# Grey box surrounding the exon, cds, and utr region
exongraph3.rectangle((0, 0), (120, EXON_IMG_HEIGHT-1), gray)

exongraph3.string(0, (3, 3), "Exon", white)
exongraph3.string(0, (60-3-(5*len("CDS")), 3), "CDS", white)
exongraph3.string(0, (63, 3), "UTR", black)
exongraph3.string(0, (135, 1), "Intron", black)

f = open("get_exon_base64_exongraph3.png", "w")
exongraph3.writePng(f)
f.close()

printout = ""

with open("get_exon_base64_exongraph3.png", "rb") as fl:
	printout = printout + fl.read().encode("base64")

print('<img src="get_exon_base64_exongraph3.png" />')
print "</br>"
print "</br>"
print(printout)

fl.close()
