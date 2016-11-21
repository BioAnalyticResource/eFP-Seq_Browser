#!/usr/bin/python
print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers
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
Currently used by multitrack-rnaseq.html to get the gene structure. -- PRYNK Feb 4, 2016
**********************************************************************************
'''

# ----- CONSTANTS -----
EXON_IMG_WIDTH = 450
EXON_IMG_HEIGHT = 7

# ----- VARIABLES -----
exon = {"start":[],"end":[]}
mRNA = {"start":[],"end":[]}
expression_score = []


# ----- LOCUS TAG OF INTEREST -----
geneid = cgi.FieldStorage().getvalue('locus')


# ----- GETS MAPPING INFO FOR THE GENE ID -----
map_info = json.loads(urllib2.urlopen("http://bar.utoronto.ca/webservices/araport/gff/get_tair10_gff.php?locus=" + geneid).read())

start = map_info[u'result'][0][u'start'] if map_info[u'result'][0][u'strand'] == u'+' else map_info[u'result'][0][u'end']
end = map_info[u'result'][0][u'end'] if map_info[u'result'][0][u'strand'] == u'+' else map_info[u'result'][0][u'start']
chromosome = int(map_info[u'result'][0][u'chromosome'])


'''
Figures out true starts and ends of the CDS based on the information retrieved into map_info.
'''
for region in map_info[u'result']:
	if region[u'strand'] == u'+':
		if region[u'start'] < start:
			start = region[u'start']
			mRNA["start"].append(int(region['start']))
		if region[u'end'] > end:
			end = region[u'end']
			mRNA["end"].append(int(region['end']))
	else:
		if region[u'start'] < start:
			start = region[u'start']
			mRNA["start"].append(int(region['start']))
		if region[u'end'] > end:
			end = region[u'end']
			mRNA["end"].append(int(region['end']))



'''
Generates exon-intron image based on the information in map_info.
'''
def generate_exon_graph():
	exongraph = gd.image((EXON_IMG_WIDTH, EXON_IMG_HEIGHT))
	white = exongraph.colorAllocate((255,255,255))
	black = exongraph.colorAllocate((0,0,0))
	blue = exongraph.colorAllocate((0,0,255))
	exongraph.lines(((0, EXON_IMG_HEIGHT), (EXON_IMG_WIDTH, EXON_IMG_HEIGHT)), black)
	for region in map_info[u'result']:
		if region[u'type'] == u'exon':
			exon["start"].append(int(region [u'start']))
			exon["end"].append(int(region [u'end']))
			exongraph.filledRectangle((int(float(region[u'start'] - start) /(end-start) * EXON_IMG_WIDTH), EXON_IMG_HEIGHT), (int(float(region[u'end'] - start)/(end-start) * EXON_IMG_WIDTH), 0), blue)
	
	exongraph.filledRectangle((0, 3), (EXON_IMG_WIDTH, 3), blue)
	f = open("get_exon_base64_exongraph.png", "w")
	exongraph.writePng(f)
	f.close()
	with open("get_exon_base64_exongraph.png", "rb") as fl:
		print fl.read().encode("base64") ################################ PRINT OUT
	fl.close()

generate_exon_graph()