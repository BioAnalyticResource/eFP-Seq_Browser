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
#map_info_old = json.loads(urllib2.urlopen("http://bar.utoronto.ca/webservices/araport/gff/get_tair10_gff.php?locus=" + geneid).read())
#map_info = json.loads('{"features":[{"end":2260187,"name":"AT1G07350","subfeatures":[{"end":2260098,"subfeatures":[{"start":2258539,"score":0,"end":2258602,"strand":-1,"type":"exon"},{"start":2258539,"score":0,"end":2258602,"strand":-1,"type":"three_prime_UTR"},{"start":2258750,"score":0,"end":2258845,"strand":-1,"type":"exon"},{"start":2258750,"score":0,"end":2258815,"strand":-1,"type":"three_prime_UTR"},{"end":2258845,"start":2258816,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2259152,"start":2259003,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2259385,"start":2259277,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":2259586,"start":2259486,"score":0,"phase":"0","type":"CDS","strand":-1}],"start":2257384,"score":0,"type":"mRNA","strand":-1},{"end":2260098,"subfeatures":[{"start":2257384,"score":0,"end":2257906,"strand":-1,"type":"exon"},{"start":2257384,"score":0,"end":2257906,"strand":-1,"type":"three_prime_UTR"},{"start":2257988,"score":0,"end":2258447,"strand":-1,"type":"exon"},{"start":2257988,"score":0,"end":2258447,"strand":-1,"type":"three_prime_UTR"},{"start":2258539,"score":0,"end":2258845,"strand":-1,"type":"exon"},{"start":2258539,"score":0,"end":2258815,"strand":-1,"type":"three_prime_UTR"},{"end":2258845,"start":2258816,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2259152,"start":2259003,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":2259003,"score":0,"end":2259152,"strand":-1,"type":"exon"},{"end":2259385,"start":2259277,"score":0,"phase":"1","type":"CDS","strand":-1},{"start":2259277,"score":0,"end":2259385,"strand":-1,"type":"exon"},{"end":2259586,"start":2259486,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":2259486,"score":0,"end":2259586,"strand":-1,"type":"exon"},{"start":2260012,"score":0,"end":2260098,"strand":-1,"type":"exon"},{"start":2260012,"score":0,"end":2260098,"strand":-1,"type":"five_prime_UTR"}],"start":2257384,"score":0,"type":"mRNA","strand":-1},{"end":2260187,"subfeatures":[{"start":2257394,"score":0,"end":2257731,"strand":-1,"type":"three_prime_UTR"},{"end":2257906,"start":2257732,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":2258447,"start":2257988,"score":0,"phase":"2","type":"CDS","strand":-1},{"end":2258602,"start":2258539,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2259152,"start":2259003,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2259385,"start":2259277,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":2259586,"start":2259486,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2260101,"start":2260012,"score":0,"phase":"0","type":"CDS","strand":-1}],"start":2257394,"score":0,"type":"mRNA","strand":-1},{"end":2260187,"subfeatures":[{"start":2258539,"score":0,"end":2259152,"strand":-1,"type":"exon"},{"start":2258539,"score":0,"end":2258750,"strand":-1,"type":"three_prime_UTR"},{"end":2259152,"start":2258751,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2259385,"start":2259277,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":2259586,"start":2259486,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2260101,"start":2260012,"score":0,"phase":"0","type":"CDS","strand":-1}],"start":2257394,"score":0,"type":"mRNA","strand":-1},{"end":2260187,"subfeatures":[{"start":2257394,"score":0,"end":2257906,"strand":-1,"type":"exon"},{"start":2257394,"score":0,"end":2257906,"strand":-1,"type":"three_prime_UTR"},{"end":2258845,"start":2258816,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2259152,"start":2259003,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2259385,"start":2259277,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":2259586,"start":2259486,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2260101,"start":2260012,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":2260012,"score":0,"end":2260187,"strand":-1,"type":"exon"},{"start":2260102,"score":0,"end":2260187,"strand":-1,"type":"five_prime_UTR"}],"start":2257394,"score":0,"type":"mRNA","strand":-1},{"end":2260089,"subfeatures":[{"start":2257409,"score":0,"end":2257906,"strand":-1,"type":"exon"},{"start":2257409,"score":0,"end":2257906,"strand":-1,"type":"three_prime_UTR"},{"end":2259152,"start":2258751,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":2259385,"start":2259277,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":2259586,"start":2259486,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":2260012,"score":0,"end":2260089,"strand":-1,"type":"exon"},{"start":2260012,"score":0,"end":2260089,"strand":-1,"type":"five_prime_UTR"}],"start":2257409,"score":0,"type":"mRNA","strand":-1}],"start":2257384,"score":0,"uniqueID":"AT1G07350","type":"gene","strand":-1,"description":"RNA-binding (RRM\/RBD\/RNP motifs) family protein"}]}')
#map_info = json.loads('{"features":[{"end":10330048,"name":"AT2G24270","subfeatures":[{"end":10330048,"subfeatures":[{"start":10326918,"score":0,"end":10327438,"strand":-1,"type":"exon"},{"start":10326918,"score":0,"end":10327324,"strand":-1,"type":"three_prime_UTR"},{"end":10327438,"start":10327325,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10327635,"start":10327519,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":10327519,"score":0,"end":10327635,"strand":-1,"type":"exon"},{"end":10328094,"start":10327716,"score":0,"phase":"1","type":"CDS","strand":-1},{"start":10327716,"score":0,"end":10328094,"strand":-1,"type":"exon"},{"end":10328336,"start":10328181,"score":0,"phase":"1","type":"CDS","strand":-1},{"start":10328181,"score":0,"end":10328336,"strand":-1,"type":"exon"},{"end":10328550,"start":10328414,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":10328414,"score":0,"end":10328550,"strand":-1,"type":"exon"},{"end":10328743,"start":10328624,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":10328624,"score":0,"end":10328743,"strand":-1,"type":"exon"},{"end":10328964,"start":10328836,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":10328836,"score":0,"end":10328964,"strand":-1,"type":"exon"},{"end":10329251,"start":10329058,"score":0,"phase":"2","type":"CDS","strand":-1},{"start":10329058,"score":0,"end":10329251,"strand":-1,"type":"exon"},{"end":10329601,"start":10329457,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":10329457,"score":0,"end":10330048,"strand":-1,"type":"exon"},{"start":10329602,"score":0,"end":10330048,"strand":-1,"type":"five_prime_UTR"}],"start":10326918,"score":0,"type":"mRNA","strand":-1},{"end":10330008,"subfeatures":[{"start":10326925,"score":0,"end":10327438,"strand":-1,"type":"exon"},{"start":10326925,"score":0,"end":10327324,"strand":-1,"type":"three_prime_UTR"},{"end":10327438,"start":10327325,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10327635,"start":10327519,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10328094,"start":10327716,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":10328336,"start":10328181,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":10328550,"start":10328414,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10328743,"start":10328624,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10328964,"start":10328836,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10329251,"start":10329058,"score":0,"phase":"2","type":"CDS","strand":-1},{"end":10329618,"start":10329457,"score":0,"phase":"2","type":"CDS","strand":-1},{"start":10329457,"score":0,"end":10329618,"strand":-1,"type":"exon"},{"end":10329824,"start":10329722,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":10329722,"score":0,"end":10330008,"strand":-1,"type":"exon"},{"start":10329825,"score":0,"end":10330008,"strand":-1,"type":"five_prime_UTR"}],"start":10326925,"score":0,"type":"mRNA","strand":-1},{"end":10329941,"subfeatures":[{"start":10327035,"score":0,"end":10327438,"strand":-1,"type":"exon"},{"start":10327035,"score":0,"end":10327324,"strand":-1,"type":"three_prime_UTR"},{"end":10327438,"start":10327325,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10327635,"start":10327519,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10328094,"start":10327716,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":10328336,"start":10328181,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":10328550,"start":10328414,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10328743,"start":10328624,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10328964,"start":10328836,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10329251,"start":10329058,"score":0,"phase":"2","type":"CDS","strand":-1},{"end":10329601,"start":10329457,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":10329457,"score":0,"end":10329607,"strand":-1,"type":"exon"},{"start":10329602,"score":0,"end":10329607,"strand":-1,"type":"five_prime_UTR"},{"start":10329722,"score":0,"end":10329941,"strand":-1,"type":"exon"},{"start":10329722,"score":0,"end":10329941,"strand":-1,"type":"five_prime_UTR"}],"start":10327035,"score":0,"type":"mRNA","strand":-1},{"end":10329941,"subfeatures":[{"start":10327035,"score":0,"end":10327134,"strand":-1,"type":"exon"},{"start":10327035,"score":0,"end":10327108,"strand":-1,"type":"three_prime_UTR"},{"end":10327134,"start":10327109,"score":0,"phase":"2","type":"CDS","strand":-1},{"end":10327438,"start":10327330,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":10327330,"score":0,"end":10327438,"strand":-1,"type":"exon"},{"end":10327635,"start":10327519,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10328094,"start":10327716,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":10328336,"start":10328181,"score":0,"phase":"1","type":"CDS","strand":-1},{"end":10328550,"start":10328414,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10328743,"start":10328624,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10328964,"start":10328836,"score":0,"phase":"0","type":"CDS","strand":-1},{"end":10329251,"start":10329058,"score":0,"phase":"2","type":"CDS","strand":-1},{"end":10329601,"start":10329457,"score":0,"phase":"0","type":"CDS","strand":-1},{"start":10329602,"score":0,"end":10329618,"strand":-1,"type":"five_prime_UTR"}],"start":10327035,"score":0,"type":"mRNA","strand":-1}],"start":10326918,"score":0,"uniqueID":"AT2G24270","type":"gene","strand":-1,"description":"aldehyde dehydrogenase 11A3"}]}')
map_info = json.loads(urllib2.urlopen("http://bar.utoronto.ca/webservices/araport/api/bar_araport11_gene_structure_by_locus.php?locus=" + geneid).read())

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