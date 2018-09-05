#!/usr/bin/python
print 'Access-Control-Allow-Origin: *'
print 'Content-Type: application/json\n'     # HTML is following
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

'''
**********************************************************************************
Currently used by index.html to get the gene structure. -- PRYNK Feb 28, 2016
**********************************************************************************
'''

# ----- CONSTANTS -----
EXON_IMG_WIDTH = 450
EXON_IMG_HEIGHT = 8

# ----- VARIABLES -----
exon_and_CDS = {"start":[],"end":[]}
mRNA = {"start":[],"end":[]}

expression_score = []
variants = []
variant_count = 0

# ----- GET THE LOCUS OF INTEREST -----
geneid = cgi.FieldStorage().getvalue('locus')

# ----- GETS MAPPING INFO FOR THE GENE ID -----
map_info = json.loads(urllib2.urlopen("https://bar.utoronto.ca/webservices/bar_araport/gene_structure_by_locus.php?locus=" + geneid).read())

printout = ""
printout = printout + "{"
printout = printout + "\"locus\" : \"" + geneid + "\", "
printout = printout + "\"locus_start\" : \"" + str(map_info[u'features'][0][u'start']) + "\", "
printout = printout + "\"locus_end\" : \"" + str(map_info[u'features'][0][u'end']) + "\", "
printout = printout + "\"splice_variants\" : ["

# Get start/end of the LOCUS
start = int(map_info[u'features'][0][u'start'])
end = int(map_info[u'features'][0][u'end'])
strand = int(map_info[u'features'][0][u'strand'])

i = 0
for subfeature in map_info[u'features'][0][u'subfeatures']:
	# Need a comma if it is not the first element
	if i == 0:
		printout = printout + "{"
	else:
		printout = printout + ", {"

	# To return a count of the number of variants returned by Araport
	variant_count = variant_count + 1

	# Extract variant
	variants.append(subfeature[u'subfeatures'])

	# Return all exons' coordinates
	printout = printout + "\"exon_coordinates\" : ["

	'''
	Generate gene structure image based on the information in map_info.
	'''
	# Create an image for gene structure
	exongraph = gd.image((EXON_IMG_WIDTH, EXON_IMG_HEIGHT))

	# Define the colours
	white = exongraph.colorAllocate((255,255,255))
	black = exongraph.colorAllocate((0,0,0))

	red = exongraph.colorAllocate((220,20,60))
	orange = exongraph.colorAllocate((255,140,0))
	blue = exongraph.colorAllocate((0,0,255))
	# TO DO: Fix the green and dark green shades...
	green = exongraph.colorAllocate((166,220,166))
	darkgreen = exongraph.colorAllocate((0,125,0))

	count = 0 # Need a comma if the it is not the first element...
	for region in variants[i]:
		# We want to return regions marked as type = exons and type = CDS
		if region[u'type'] == u'exon' or region[u'type'] == u'CDS':
			exon_and_CDS["start"].append(int(region [u'start']))
			exon_and_CDS["end"].append(int(region [u'end']))
			if (count == 0):
				printout = printout + "{" + "\"exon_start\" : " + str(int(region [u'start'])) + ", \"exon_end\" : " + str(int(region [u'end'])) + "}"
			else:
				printout = printout + ", {" + "\"exon_start\" : " + str(int(region [u'start'])) + ", \"exon_end\" : " + str(int(region [u'end'])) + "}"
			count = count + 1 # To add a comma only...
		# We want to graph all types of features in the gene structure image
		if region[u'type'] == u'exon':
			exongraph.filledRectangle((int(float(region[u'start'] - start) /(end-start) * EXON_IMG_WIDTH), EXON_IMG_HEIGHT), (int(float(region[u'end'] - start)/(end-start) * EXON_IMG_WIDTH), 0), darkgreen)
		elif region[u'type'] == u'CDS':
			exongraph.filledRectangle((int(float(region[u'start'] - start) /(end-start) * EXON_IMG_WIDTH), EXON_IMG_HEIGHT), (int(float(region[u'end'] - start)/(end-start) * EXON_IMG_WIDTH), 0), darkgreen)
		elif region[u'type'] == u'five_prime_UTR':
			exongraph.filledRectangle((int(float(region[u'start'] - start) /(end-start) * EXON_IMG_WIDTH), EXON_IMG_HEIGHT), (int(float(region[u'end'] - start)/(end-start) * EXON_IMG_WIDTH), 0), green)
		elif region[u'type'] == u'three_prime_UTR':
			exongraph.filledRectangle((int(float(region[u'start'] - start) /(end-start) * EXON_IMG_WIDTH), EXON_IMG_HEIGHT), (int(float(region[u'end'] - start)/(end-start) * EXON_IMG_WIDTH), 0), green)

	# Nucleotide padding
	nucleotidePadding = 100
	exongraph.filledRectangle((0, EXON_IMG_HEIGHT), ((EXON_IMG_WIDTH / nucleotidePadding), 0), white)
	exongraph.filledRectangle(((EXON_IMG_WIDTH - (EXON_IMG_WIDTH / nucleotidePadding)), EXON_IMG_HEIGHT), ((EXON_IMG_WIDTH), 0), white)

	# Line in the middle
	exongraph.filledRectangle((0, EXON_IMG_HEIGHT/2), (EXON_IMG_WIDTH, EXON_IMG_HEIGHT/2), black)

	# Insert appropriate arrows to indicate direction of the gene
	if (strand == -1):
		exongraph.filledPolygon(((0, EXON_IMG_HEIGHT/2), (3, (EXON_IMG_HEIGHT)-(EXON_IMG_HEIGHT-1)), (3, EXON_IMG_HEIGHT-1)), black)
	elif (strand == +1):
		exongraph.filledPolygon(((EXON_IMG_WIDTH, EXON_IMG_HEIGHT/2), (EXON_IMG_WIDTH-3, (EXON_IMG_HEIGHT)-(EXON_IMG_HEIGHT-1)), (EXON_IMG_WIDTH-3, EXON_IMG_HEIGHT-1)), black)

	f = open("get_exon_base64_exongraph.png", "w")
	exongraph.writePng(f)
	f.close()

	printout = printout + "], " + "\"start\" : " + str(start) + ", " + "\"end\" : " + str(end) + ", " + "\"gene_structure\" : "
	printout = printout + "\""
	with open("get_exon_base64_exongraph.png", "rb") as fl:
		printout = printout + fl.read().encode("base64")
	printout = printout + "\""
	fl.close()

	#For returning the gene structure data...
	#printout = printout + ", \"BAMdata\" : \"" + str(subfeature[u'subfeatures']) + "\""

	i = i + 1
	printout = printout + "}"

printout = printout + "]" + ", \"variant_count\" : \"" + str(variant_count) + "\"" + "}"

print printout.replace('\n', ' ')
