#!/usr/bin/python3
################################################################################
# This program return the base64 of the RNA-Seq mapping coverage image.
#
# Authors: Asher, Alexander and Priyank
# Date: January 2016
################################################################################
import cgi
import json
import math
import os
import random
import re
import subprocess
import sys
import time
import base64
from PIL import Image, ImageDraw

print("Access-Control-Allow-Origin: *")
print("Content-Type: text/html\n\n")


# Precision for the PCC and RPKM values that are returned
PRECISION = 5

# Global variables
EXON_IMG_WIDTH = 450
EXON_IMG_HEIGHT = 7

RNA_IMG_WIDTH = 450
RNA_IMG_HEIGHT = 50

exp_arr = []
exp_arr0 = []

start_time = str(time.time()).replace('.', '')

################################################################################
# Validation functions
################################################################################

''' Check the format of tissue string and returns error if incorrect. '''
def validateTissue(tissue):
    if tissue == "":
        return False
    elif tissue is None:
        return False
    if re.search(r"^[a-z0-9\-_\s]{1,20}$", tissue, re.I):  # Can only have upto 20 alpha numeric charactors
        return True
    else:
        return False


''' Check the format of locus. '''
def validateLocus(locus):
    if locus == "":
        return False
    elif re.search(r'^at[12345cm]g\d+$', locus, re.I):
        return True
    else:
        return False


# Validate Chromosome
def validateChromosome(chromosome):
    if re.search(r'[12345cmCM]', chromosome):
        return chromosome
    else:
        dumpError("Chromosome validation error: 2.")


# Validate Start
def validateStart(start, end):
    if 0 < start < end:
        return start
    else:
        dumpError("Start error.")


# Validate End
def validateEnd(start, end):
    if end > 0 and start < end:
        return end
    else:
        dumpError("End error.")


################################################################################
# Data processing functions
################################################################################
''' For converting from HEX to RGB values
http://stackoverflow.com/questions/214359/converting-hex-color-to-rgb-and-vice-versa '''


def hex_to_rgb(val):
    if val[:2] == "0x":
        val = val[2:]
    length = len(val)
    return tuple(int(val[i:i + length // 3], 16) for i in range(0, length, length // 3))


''' Used if in the instance the user does not know how many reads are mapped to
their locus '''
def determineReadMapNumber(filedir, filename, readMappedNumber, remoteDrive, bamType):
    if readMappedNumber == 0:
        readsMappedHold = []  # Holds the number

        # Clear temporary files and name a new one
        os.system("find ../temp/* -mtime +1 -exec rm -f {} \\;")

        # Set the environment
        bai_directory = ("data/" + filedir)
        if os.path.isdir(bai_directory):
            os.chdir(bai_directory)
        else:
            os.makedirs(bai_directory)
            os.chdir(bai_directory)
        my_env = os.environ.copy()
        my_env["LD_LIBRARY_PATH"] = "/usr/local/lib/"

        flagstat = None

        try:
            flagstat = subprocess.check_output(['samtools', 'flagstat', filename], env=my_env)
        except:
            pass

        os.chdir("../../../")

        if flagstat is None:
            return "FAILED: determineReadMapNumber-flagstat NONE"

        # Read pileup output
        for read in flagstat.splitlines():
            read = str(read.decode("utf-8"))
            if ("mapped" in read) and ("with mate" not in read):  # Search for reads mapped position
                readsMappedHold.append(float(read.split(' ')[0]))  # Reads mapped position

        if len(readsMappedHold) > 0:
            return float(readsMappedHold[0])
        else:
            return "FAILED: determineReadMapNumber-readsMappedHold - No mapped"
    elif readMappedNumber > 0:
        return float(readMappedNumber)


''' Once we have chromosome, start, end and filename, we can make the image.'''
def makeImage(filedir, filename, chromosome, start, end, record, yscale, hexcodecolour, remoteDrive, bamType):
    max_mapped_reads_count = 0  # For setting the appropriate Y scale

    x_bp_vals = []  # Holds nucleotide positions...
    y_reads_values = []  # Holds the valid mapped reads for the position...

    if bamType == "Google Drive":
        # Clear temporary files and name a new one
        # os.system("find ../temp/* -mtime +1 -exec rm -f {} \\;")
        tempfile = "../temp/RNASeqGraph.png"

    # Call samtools and get mpileup
    region = chromosome + ":" + str(start) + "-" + str(end)

    # Set the environment
    bai_directory = ("data/" + filedir)
    if os.path.isdir(bai_directory):
        os.chdir(bai_directory)
    else:
        os.makedirs(bai_directory)
        os.chdir(bai_directory)
    my_env = os.environ.copy()
    my_env["LD_LIBRARY_PATH"] = "/usr/local/lib/"

    mpileup = None

    try:
        mpileup = subprocess.check_output(
            ['bcftools', 'mpileup', '--max-depth', '8000', '--no-reference', '-r', region, filename], env=my_env)
    except:
        pass

    os.chdir("../../../")

    if mpileup is None:
        return "FAILED"

    # Read pileup output
    for read in mpileup.splitlines():
        read = str(read.decode("utf-8"))
        split_Read_Lines = read.split('\t')
        if split_Read_Lines[0].strip()[0] != '#':
            readPos = split_Read_Lines[1]
            x_bp_vals.append(float(readPos))  # nucleotide position
            # get the number of mapped reads and subtract the reference skips
            dpNum = split_Read_Lines[7].split(';')[0]
            mapped_reads_count = float(re.sub(r'[^0-9]', "", dpNum))
            exp_arr0.append((float(readPos), mapped_reads_count))
            y_reads_values.append(mapped_reads_count)
            # Figure out the max number of reads mapped at any given locus
            if mapped_reads_count > max_mapped_reads_count:
                max_mapped_reads_count = mapped_reads_count

    # IF the user specified a custom y-scale, use that
    if yscale == -1:  # If the user did not specify a yscale, use the highest mapped read count
        yscale = max_mapped_reads_count
        # To leave a little room at top of graph for Y-axis scale label, multiply by 1.1
        max_mapped_reads_count = max_mapped_reads_count * 1.1
    else:
        max_mapped_reads_count = yscale * 1.1

    # Scale all y-axis values
    if max_mapped_reads_count > 0:
        for i in range(len(y_reads_values)):
            y_reads_values[i] = int(y_reads_values[i] / max_mapped_reads_count * RNA_IMG_HEIGHT)
    else:
        for i in range(len(y_reads_values)):
            y_reads_values[i] = 0

    # Specify colours
    white = (255, 255, 255)
    red = (255, 0, 0)
    green = (100, 204, 101)
    yellow = (255, 255, 0)
    black = (0, 0, 0)
    gray = (192, 192, 192)
    rnaseq_img_colour_hex = hex_to_rgb(hexcodecolour)
    rnaseq_img_colour = rnaseq_img_colour_hex

    # Create an image
    rnaseq_graph_image = Image.new("RGB", (RNA_IMG_WIDTH, RNA_IMG_HEIGHT), white)
    rnaseqgraph = ImageDraw.Draw(rnaseq_graph_image)

    # Max line at top
    rnaseqgraph.rectangle(((0, 5), (RNA_IMG_WIDTH, 5)), gray)
    # Actual RNA-Seq image
    for i in range(len(x_bp_vals)):
        rnaseqgraph.rectangle(((int(float(x_bp_vals[i] - start) / (end - start) * RNA_IMG_WIDTH), RNA_IMG_HEIGHT - y_reads_values[i]), (
        int(float(x_bp_vals[i] - start) / (end - start) * RNA_IMG_WIDTH), RNA_IMG_HEIGHT)),
                              rnaseq_img_colour)

    # Nucleotide padding
    nucleotidePadding = 100
    rnaseqgraph.rectangle(((0, 0), ((RNA_IMG_WIDTH / nucleotidePadding), RNA_IMG_HEIGHT)), white)
    rnaseqgraph.rectangle((((RNA_IMG_WIDTH - (RNA_IMG_WIDTH / nucleotidePadding)), 0),
                                (RNA_IMG_WIDTH, RNA_IMG_HEIGHT)), white)

    rnaseqgraph.text((420, 5), str(int(yscale)), fill=black)  # Y-axis scale label

    if bamType == "Amazon AWS":
        # Clear temporary files and name a new one
        os.system("find ../temp/* -mtime +1 -exec rm -f {} \\;")

    tempfile = "../temp/RNASeqGraph.png"
    # Output the GD image to temp PNG file
    f = open(tempfile, "wb")
    rnaseq_graph_image.save(f)
    f.close()

    # Convert the PNG to base64
    with open(tempfile, "rb") as fl:
        my_base64 = base64.b64encode(fl.read()).decode("utf-8")

    return [my_base64, exp_arr0]


################################################################################
# Ouput functions
################################################################################
# Error function
def dumpError(result, locus=None, record=None, my_base64img=None, abs_fpkm=None, r=None, totalReadsMapped=None):
    """Dumps and prints an error to the client/user

    Arguments:
        result {string} -- The error message to be displayed

    Keyword Arguments:
        locus {string} -- The AGI ID of the gene that the RNA-Seq map coverage is interpreting (default: {None})
        record {string} -- The SRA record of the BAM data being interpreted (default: {None})
        base64img {string} -- The base64 version of the RNA-Seq map coverage image (default: {None})
        abs_fpkm {string, integer} -- The absolute FPKM/RPKM value (default: {None})
        r {string, integer} -- The r coefficient value (default: {None})
        totalReadsMapped {string, integer} -- The total number of reads mapped to the gene within the BAM file (default: {None})
    """
    print(json.dumps({"status": "fail", "result": result, "record": record, "locus": locus, "rnaseqbase64": my_base64img,
                      "absolute-fpkm": abs_fpkm, "r": r, "totalReadsMapped": totalReadsMapped}))
    sys.exit(0)


# Final output, if everything at this point succeded
def dumpJSON(status, locus, variant, chromosome, start, end, record, tissue, base64img, reads_mapped_to_locus, abs_fpkm,
             r, totalReadsMapped):
    print(json.dumps(
        {"status": "success", "locus": locus, "variant": variant, "chromosome": chromosome, "start": start, "end": end,
         "record": record, "tissue": tissue, "rnaseqbase64": base64img, "reads_mapped_to_locus": reads_mapped_to_locus,
         "absolute-fpkm": abs_fpkm, "r": r, "totalReadsMapped": totalReadsMapped}))  # and svg stuff
    sys.exit(0)


def dumpJSON_full(status, locus, variant, chromosome, start, end, record, tissue, base64img, reads_mapped_to_locus,
                  abs_fpkm, r, totalReadsMapped, exp_arr0, exp_arr, expected_expr_in_variant):
    print(json.dumps(
        {"status": "success", "locus": locus, "variant": variant, "chromosome": chromosome, "start": start, "end": end,
         "record": record, "tissue": tissue, "rnaseqbase64": base64img, "reads_mapped_to_locus": reads_mapped_to_locus,
         "absolute-fpkm": abs_fpkm, "r": r, "totalReadsMapped": totalReadsMapped,
         "ReadsMappedNucleotidePosition": exp_arr0, "exp_arr": exp_arr,
         "expected_expr_in_variant": expected_expr_in_variant}))  # and svg stuff
    sys.exit(0)


################################################################################
################################################################################
################################################################################
################################################################################
################################################################################

record = None
locus = None
base64img = None
totalReadsMapped = None
r = None
abs_fpkm = None
''' The main program. '''


def main():
    # Get query details
    form = cgi.FieldStorage()
    tissue = form.getvalue('tissue')
    record = form.getvalue('record')
    locus = form.getvalue('locus')
    variant = form.getvalue('variant')
    hexcode = form.getvalue('hexcodecolour')
    bamfilename = form.getvalue('filename')
    totalReadsMapped = form.getvalue('numberofreads')
    dumpMethod = form.getvalue('dumpMethod')
    status = form.getvalue('status')
    remoteDrive = form.getvalue('remoteDrive')
    bamType = form.getvalue('bamType')
    cachedDatapoints = form.getvalue('cachedDatapoints')
    if (cachedDatapoints is not None and cachedDatapoints.lower() == 'true') or (
            cachedDatapoints is True):  # Verify cachedDatapoint is a boolean
        cachedDatapoints = True
    else:
        cachedDatapoints = False

    base64img = None
    r = None
    abs_fpkm = None

    ############################################################################
    # Generate new data or return cached data for speedy first-load.
    ############################################################################
    # (status == 0) => RETURN NEWLY GENERATED DATA
    # subprocess.check_output(['export', 'LD_LIBRARY_PATH=/usr/local/lib/'])
    if status == 0 or status == "0":
        # Get info required for generating new data
        variant_structure = json.loads(form.getvalue('struct'))  # Exon-Intron
        chromosome = validateChromosome(str(locus[2]))
        start = validateStart(int(form.getvalue('start')), int(form.getvalue('end'))) - 1
        end = validateEnd(int(form.getvalue('start')), int(form.getvalue('end'))) + 1
        yscale = -1  # RNA-Seq Mapping Coverage image y-axis max value
        if form.getvalue('yscale'):
            yscale = int(form.getvalue('yscale'))

        # Now validate the data
        if not validateTissue(tissue):
            tissue = 'undefined'
        if not validateLocus(locus):
            dumpError('Locus validation error', locus, record, base64img, abs_fpkm, r, totalReadsMapped)

        region = "Chr" + str(chromosome) + ":" + str(start) + "-" + str(end)

        exons_in_variant = []
        variants_count = -1
        expected_expr_in_variant = []
        expected_exonLength_in_variant = []
        for vrnt in variant_structure:
            variants_count += 1
            exons_in_variant.append([])
            expected_expr_in_variant.append([])
            # Keep track of exons' start and end positions
            for exon in vrnt['exon_coordinates']:
                exons_in_variant[variants_count].append((exon['exon_start'], exon['exon_end']))
            # Append 100 for each exonic base, 1 for each intronic base.
            for i in range(start, end):
                i_in_exon = 0
                for exon in exons_in_variant[variants_count]:
                    if exon[0] <= i <= exon[1]:
                        i_in_exon = 1
                        expected_expr_in_variant[variants_count].append(100)
                        break
                if i_in_exon == 0:
                    expected_expr_in_variant[variants_count].append(1)
            expected_exonLength_in_variant.append(expected_expr_in_variant[variants_count].count(100))

        # Calculate gene length without introns
        expectedGeneLength = []
        for i in range(variants_count + 1):
            exonGeneLength = (end - start) - expected_exonLength_in_variant[i]
            if exonGeneLength < 0:
                exonGeneLength = 0
            expectedGeneLength.append(exonGeneLength)

        # Public datasets and their directories:
        publicDatapoints = {
            'aerial': ['ERR274310', 'SRR547531', 'SRR548277', 'SRR847503', 'SRR847504', 'SRR847505', 'SRR847506'],
            'carpel': ['SRR1207194', 'SRR1207195'],
            'dark': ['SRR1019436', 'SRR1019437', 'SRR1049784', 'SRR477075', 'SRR477076', 'SRR493237', 'SRR493238'],
            'flower': ['SRR314815', 'SRR800753', 'SRR800754'],
            'Klepikova': ['SRR3581336', 'SRR3581345', 'SRR3581346', 'SRR3581347', 'SRR3581352', 'SRR3581356',
                          'SRR3581383', 'SRR3581388', 'SRR3581499', 'SRR3581591', 'SRR3581639', 'SRR3581672',
                          'SRR3581676', 'SRR3581678', 'SRR3581679', 'SRR3581680', 'SRR3581681', 'SRR3581682',
                          'SRR3581683', 'SRR3581684', 'SRR3581685', 'SRR3581686', 'SRR3581687', 'SRR3581688',
                          'SRR3581689', 'SRR3581690', 'SRR3581691', 'SRR3581692', 'SRR3581693', 'SRR3581694',
                          'SRR3581695', 'SRR3581696', 'SRR3581697', 'SRR3581698', 'SRR3581699', 'SRR3581700',
                          'SRR3581701', 'SRR3581702', 'SRR3581703', 'SRR3581704', 'SRR3581705', 'SRR3581706',
                          'SRR3581707', 'SRR3581708', 'SRR3581709', 'SRR3581710', 'SRR3581711', 'SRR3581712',
                          'SRR3581713', 'SRR3581714', 'SRR3581715', 'SRR3581716', 'SRR3581717', 'SRR3581719',
                          'SRR3581720', 'SRR3581721', 'SRR3581724', 'SRR3581726', 'SRR3581727', 'SRR3581728',
                          'SRR3581730', 'SRR3581731', 'SRR3581732', 'SRR3581733', 'SRR3581734', 'SRR3581735',
                          'SRR3581736', 'SRR3581737', 'SRR3581738', 'SRR3581740', 'SRR3581831', 'SRR3581833',
                          'SRR3581834', 'SRR3581835', 'SRR3581836', 'SRR3581837', 'SRR3581838', 'SRR3581839',
                          'SRR3581840', 'SRR3581841', 'SRR3581842', 'SRR3581843', 'SRR3581844', 'SRR3581845',
                          'SRR3581846', 'SRR3581847', 'SRR3581848', 'SRR3581849', 'SRR3581850', 'SRR3581851',
                          'SRR3581852', 'SRR3581853', 'SRR3581854', 'SRR3581855', 'SRR3581856', 'SRR3581857',
                          'SRR3581858', 'SRR3581859', 'SRR3581860', 'SRR3581861', 'SRR3581862', 'SRR3581863',
                          'SRR3581864', 'SRR3581865', 'SRR3581866', 'SRR3581867', 'SRR3581868', 'SRR3581869',
                          'SRR3581870', 'SRR3581871', 'SRR3581872', 'SRR3581873', 'SRR3581874', 'SRR3581875',
                          'SRR3581876', 'SRR3581877', 'SRR3581878', 'SRR3581879', 'SRR3581880', 'SRR3581881',
                          'SRR3581882', 'SRR3581883', 'SRR3581884', 'SRR3581885', 'SRR3581886', 'SRR3581887',
                          'SRR3581888', 'SRR3581889', 'SRR3581890', 'SRR3581891', 'SRR3581892', 'SRR3581893',
                          'SRR3581894', 'SRR3581895', 'SRR3581896', 'SRR3581897', 'SRR3581898', 'SRR3581899',
                          'SRR3724649', 'SRR3724650', 'SRR3724651', 'SRR3724652', 'SRR3724663', 'SRR3724668',
                          'SRR3724737', 'SRR3724739', 'SRR3724741', 'SRR3724768', 'SRR3724774', 'SRR3724778',
                          'SRR3724782', 'SRR3724785', 'SRR3724786', 'SRR3724787', 'SRR3724798', 'SRR3724806',
                          'SRR3724814', 'SRR3725446', 'SRR3725458', 'SRR3725471', 'SRR3725482', 'SRR3725493',
                          'SRR3725503', 'SRR3725516', 'SRR3725527', 'SRR3725538', 'SRR3725550', 'SRR3725561',
                          'SRR847501', 'SRR847502'],
            'leaf': ['SRR1105822', 'SRR1105823', 'SRR1159821', 'SRR1159827', 'SRR1159837', 'SRR314813', 'SRR446027',
                     'SRR446028', 'SRR446033', 'SRR446034', 'SRR446039', 'SRR446040', 'SRR446484', 'SRR446485',
                     'SRR446486', 'SRR446487', 'SRR493036', 'SRR493097', 'SRR493098', 'SRR493101', 'SRR764885',
                     'SRR924656', 'SRR934391', 'SRR942022'],
            'light': ['SRR070570', 'SRR070571', 'SRR1001909', 'SRR1001910', 'SRR1019221', 'SRR345561', 'SRR345562',
                      'SRR346552', 'SRR346553', 'SRR394082', 'SRR504179', 'SRR504180', 'SRR504181', 'SRR515073',
                      'SRR515074', 'SRR527164', 'SRR527165', 'SRR584115', 'SRR584121', 'SRR584129', 'SRR584134',
                      'SRR653555', 'SRR653556', 'SRR653557', 'SRR653561', 'SRR653562', 'SRR653563', 'SRR653564',
                      'SRR653565', 'SRR653566', 'SRR653567', 'SRR653568', 'SRR653569', 'SRR653570', 'SRR653571',
                      'SRR653572', 'SRR653573', 'SRR653574', 'SRR653575', 'SRR653576', 'SRR653577', 'SRR653578',
                      'SRR797194', 'SRR797230', 'SRR833246'],
            'pollen': ['SRR847501', 'SRR847502'],
            'RAM': ['SRR1260032', 'SRR1260033', 'SRR1261509'],
            'receptacle': ['SRR401413', 'SRR401414', 'SRR401415', 'SRR401416', 'SRR401417', 'SRR401418', 'SRR401419',
                           'SRR401420', 'SRR401421'],
            'root': ['ERR274309', 'SRR1046909', 'SRR1046910', 'SRR1524935', 'SRR1524938', 'SRR1524940', 'SRR314814'],
            'SAM': ['SRR949956', 'SRR949965', 'SRR949988', 'SRR949989']
        }

        ### Generate BAM directory link
        bam_dir = ''  # Reset bam_dir value
        # Check if data is public or private dataset
        if cachedDatapoints:
            for x in publicDatapoints:  # If public, find tissue (x) to create bam_dir
                if record in publicDatapoints[x]:
                    bam_dir = x + '/' + record
            if bam_dir == '':  # If tissue not found, download new bam index file
                if record is not None:
                    bam_dir = "uploads" + "/" + record + "_" + start_time
                else:
                    bam_dir = "uploads" + "/unknownRecord_" + start_time
        else:  # If private, download new bam index file
            if record is not None:
                bam_dir = "uploads" + "/" + record + "_" + start_time
            else:
                bam_dir = "uploads" + "/unknownRecord_" + start_time

        bam_file = ''  # Reset bam_file value
        if bamType == "Google Drive":
            # Create a Google Drive mount point and muont the bam file.
            uniqId = str(random.randint(1, 1000000))
            try:
                pid = subprocess.Popen(["perl", "gDriveMountFast.pl", remoteDrive, uniqId, bamfilename])
            except:
                sys.exit(1)

            # Make S3FS filename here
            bam_file = "/mnt/gDrive/" + remoteDrive + "_" + uniqId + "/" + bamfilename

            # Wait unilt the file is ready, without locking up the system forever, locking system for five minutes
            startTime = time.time()
            while not (os.path.isfile(bam_file)):
                # pass
                currentTime = time.time()
                if currentTime > (startTime + 300):
                    subprocess.call(["fusermount", "-u", "/mnt/gDrive/" + remoteDrive + "_" + uniqId])
                    subprocess.call(["rm", "-rf", "/mnt/gDrive/" + remoteDrive + "_" + uniqId])
                    dumpError("Mounting timed out", locus, record, base64img, abs_fpkm, r, totalReadsMapped)

            # Now make a image using samtools
            base64img = makeImage(bam_dir, bam_file, "Chr" + chromosome, start, end, record, yscale, hexcode,
                                  remoteDrive, bamType)

            if base64img == "FAILED":
                base64img = makeImage(bam_dir, bam_file, "chr" + chromosome, start, end, record, yscale, hexcode,
                                      remoteDrive, bamType)
                region = "chr" + str(chromosome) + ":" + str(start) + "-" + str(end)

            if base64img == "FAILED":
                base64img = makeImage(bam_dir, bam_file, chromosome, start, end, record, yscale, hexcode, remoteDrive,
                                      bamType)

            if base64img == "FAILED":
                subprocess.call(["fusermount", "-u", "/mnt/gDrive/" + remoteDrive + "_" + uniqId])
                subprocess.call(["rm", "-rf", "/mnt/gDrive/" + remoteDrive + "_" + uniqId])
                dumpError("Failed to get data.", locus, record, base64img, abs_fpkm, r, totalReadsMapped)

        elif bamType == "Amazon AWS":
            # Make S3FS filename here
            bam_file = "s3://" + remoteDrive

            # Now make a image using samtools
            base64img = makeImage(bam_dir, bam_file, "Chr" + chromosome, start, end, record, yscale, hexcode,
                                  remoteDrive, bamType)

            if base64img == "FAILED":
                base64img = makeImage(bam_dir, bam_file, "chr" + chromosome, start, end, record, yscale, hexcode,
                                      remoteDrive, bamType)
                region = "chr" + str(chromosome) + ":" + str(start) + "-" + str(end)

            if base64img == "FAILED":
                base64img = makeImage(bam_dir, bam_file, chromosome, start, end, record, yscale, hexcode, remoteDrive,
                                      bamType)

        # Correct total reads mapped:
        if totalReadsMapped is None or totalReadsMapped == "0" or totalReadsMapped == 0:
            totalReadsMapped = 0
            totalReadsMapped = determineReadMapNumber(bam_dir, bam_file, totalReadsMapped, remoteDrive, bamType)

        # OFTEN, mpileup output doesn't include all the bases assigned to locus
        # The ones that are not included should get a mpileup expression value of 0
        # Take the exp_arr0 (generated in makeImage) and create exp_arr based on the above explanation
        for i in range(start, end):
            found = 0
            for base in exp_arr0:
                if i == base[0]:
                    found = 1
                    exp_arr.append(base[1])
            if found == 0:
                exp_arr.append(0)

        # Compute sum(x) and sum(x^2)
        sum_x = []
        sum_xx = []
        for var in expected_expr_in_variant:
            tmp_sum_x = 0
            tmp_sum_xx = 0
            for val in var:
                tmp_sum_x += val
                tmp_sum_xx += val * val
            sum_x.append(tmp_sum_x)
            sum_xx.append(tmp_sum_xx)

        # Compute SS_x - Standard deviation
        ss_x = []
        for i in range(len(sum_x)):
            ss_x.append(sum_xx[i] - ((sum_x[i] * sum_x[i]) / (end - start)))

        # Compute sum(y) and sum(Y^2)
        sum_y = 0
        sum_yy = 0
        for val in exp_arr:
            sum_y += val
            sum_yy += val * val

        # Compute SS_y - Standard deviation
        ss_y = 0
        ss_y = sum_yy - ((sum_y * sum_y) / (end - start))

        # Compute sum(X * Y)
        sum_xy = []
        for variant11 in expected_expr_in_variant:
            variant_sum_xy = 0
            for i in range(len(variant11)):
                variant_sum_xy += int(variant11[i]) * int(exp_arr[i])
            sum_xy.append(variant_sum_xy)

        # Count the number of mapped reads to the locus
        # TODO: modify the mpileup call to include this information in it
        # Hypothesis: since you need this info to create the mpileup output
        # the same info would be there. So just pass that along instead of
        # making this call .. to speed things up
        # Set the environment
        bai_directory = ("data/" + bam_dir)
        if os.path.isdir(bai_directory):
            os.chdir(bai_directory)
        else:
            os.makedirs(bai_directory)
            os.chdir(bai_directory)
        my_env = os.environ
        my_env["LD_LIBRARY_PATH"] = "/usr/local/lib/"

        lines = ""
        try:
            lines = subprocess.check_output(['samtools', 'view', bam_file, region], env=my_env)
            lines = str(lines.decode("utf-8"))
        except:
            dumpError("Unable to retrieve BAM data", locus, record, base64img, abs_fpkm, r, totalReadsMapped)

        os.chdir("../../../")
        mapped_reads = lines.lower().count('chr')

        abs_fpkm = []
        for i in range(len(expectedGeneLength)):
            rpkm = float(mapped_reads) / (float((expectedGeneLength[i])) / 1000.0) / (
                        float(totalReadsMapped) / 1000000.0)
            abs_fpkm.append(round(rpkm, PRECISION))

        # Calculate the r values for each variant.
        r = []
        for i in range(len(sum_xy)):
            sp = sum_xy[i] - ((sum_x[i] * sum_y) / float(end - start))
            if math.sqrt(ss_x[i] * ss_y) == 0:
                r.append(float(0.00000))
            else:
                r_val = float(sp / (math.sqrt(ss_x[i] * ss_y)))
                r.append(round(r_val, PRECISION))

        if bamType == "Google Drive":
            try:
                subprocess.call(["fusermount", "-u", "/mnt/gDrive/" + remoteDrive + "_" + uniqId])
            except:
                sys.stderr.write("Failed to unmount FUSE file system.")

            try:
                subprocess.call(["rm", "-rf", "/mnt/gDrive/" + remoteDrive + "_" + uniqId])
            except:
                sys.stderr.write("Failed to delete FUSE mount point.")

        RNASeq_ReadsPerNucleotide = base64img[1]

        # Output the newly generated data
        if dumpMethod == "complex":
            dumpJSON_full(200, locus, int(variant), chromosome, start, end, record, tissue,
                          base64img[0].replace('\n', ''), mapped_reads, abs_fpkm, r, totalReadsMapped, base64img[1],
                          exp_arr, expected_expr_in_variant)
        elif dumpMethod != "complex":
            dumpJSON(200, locus, int(variant), chromosome, start, end, record, tissue, base64img[0].replace('\n', ''),
                     mapped_reads, abs_fpkm, r, totalReadsMapped)

    else:
        if dumpMethod != "complex":
            # Araport 11 data starts here:
            if record == "ERR274310":
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "ERR274310", "aerial",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACYElEQVRoge2YXZaDIAyFeehkXX3oFmae85T9L2GQFgmSqEjw7/TOOe2Ikns/QaU699VXX321g35+LfT3Z1KmRrTiGMPzBGRYbJ0Ux9fLvYYPc7vTELrHwz3dw96O0LzmkqXS/vRj6D+MBWciHMbwae52BKHs+PB/zx6T9ABC2dLDvVouQ5BbT0TYXFZsPYKw16VP4iAGwi5+ugbPDmWVqoPb3k/ELoSAymy8F2EsixO3WxASIwTkO4JQ6NJPPQiBgxxO2MERMkJeHQ8ghA6OFPXewmKPsd+swNTxMyELwvhohMsTxnmZE5Jf3wBzux4hjP1VQnyP7uUJQSHEgZBcIgw75KW5uYBFaagR/8HwPSWMGzQSosteZ2CT/2K6tkH00288QzRLiDkhpCV49cupmuEHnmWLfDrfHWLm0LZM6HdBsq31x2wRsaAsyxYROT4qWVGabFGhcABUTiIQDtcJGgmHFTZ+CFNQhVBQTJxuu6Fh3lTICzpCIyEP20aILt2y5gnTCRmFOiFEK9wECDxsKrOFkFy6HrXLDNPh2RGQahUarbYR8rDMuJlQjgMa4QxCGoNNhEBTNRASMkJxQOKvsSLwDMM02qGEtEAIGSFLPAfRSFgmbiLkDcuEY+TUfWiZ3KXOS4jvnrlbThh3QtbblJAnMyeE6VIHCsJiO9ztLAmFxIaE4VUIZm6LhGMFhbDysT+pbEvI60H84dVKCJUrmx0JKSxa2gjfy8vTEspElYSpy0pJiU9PWDWI1ySsGEUoO1+CcO0oiny3IlQSX4FwHSJIPe9EqCauJcwJdiJUbjb/AGmTJXBx7W0AAAAASUVORK5CYII=",
                         8485, [370.51093, 311.19754, 259.19298, 222.75943], [0.56793, 0.59246, 0.6823, 0.59941],
                         29098868)
            elif (record == "SRR548277"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR548277", "aerial",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAB50lEQVRoge3YzZKDIAwAYA5unouDr7B75pT3f4QVx2oCgaqkFhhy2JlFSfjKj7bGjBgxYsQD8fNbHn+okOQTofYpITq1XKUxz2Yyk9VNCoj1GO2C9H9UA7Ei4myXObRWNSdUJfRr1MyTasq6hNYLra4QqxIuh8xsS04acFFTXcLiQBSaOhO6uGkIm4ruhZKkKyEMYfPRv1CUfEEI8VNZKXLCjxUVIhaCUmZR8hWh40OQ3ibvJT4hVKr1biCsitomIULiDISaGzK1MNbdcixM0FpCQCTkQzuEvo0sIMDC3RFO1R7B2aYlBGTCvcAuXK8xYeF8ig8nE33nBq2z/IyQLNej9XbF1MC5MPAWxDXh6+7btenAg9XO8z4ndCnh1mCujQFI92AZiEKFjcjGGxcIQUKDY+lcnkzXgCxEPoAyXZR3F8bAtJAR342K9k8I+Qj0hWuB2JcTroctS+fKhayKrnCpIMxgXuh3q6PXk8Q4ZXxp3dy1CfGkUEgpCMn51ogQEts7IWR38UxKQhF4TZh4hb4hLJ/EWJiIO0LA15K4IszdVKNQ/v+8sJjYvZDnaV8IbvtSgOGDtQ/hlp+9dzQgdFeBvOMQtiNEF2ZoRnhuIwr9ehKC2K8doY/8L/5yn6tCLnhaSJIs8Q9cwG/c9g5H8gAAAABJRU5ErkJggg==",
                         4192, [500.28703, 420.19839, 349.97857, 300.78372], [0.57105, 0.51184, 0.60217, 0.65404],
                         10647001)
            elif (record == "SRR847504"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR847504", "aerial",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACCklEQVRoge2YQZKEIAxFXTg5FwuvMHs2k/sfYdTuEgiJghigbX/VTE2Byf9PwLF7GB49evSogn5+P1R/Cde0vrllsvzwaIZpmKaqUZSE/LAZx8GYqkm0JBAuiGYyNZNoSSJcl3CsGkVJ4i6df8w9CC07vD5p5l83EErb9DZCYRHvo28gVN+mVttgX6i+iK1POqojNj4HoE4Il5wDKPLX3UbX9O+YEK7pf76FIuGrK0bH4MRyQDGhPbwuU0tDkTA/7elFsFqEgDOGTJhph6fP8mz1Arya8N11/bucsCBjI8Jcv3e3d1HW/cFNWY7JmZxJ0D/XkBLuFZOnWD1CpJM5htghIUaEzgAi5MRuH0OY75hMCNGLgRYhNCKcJ9oROmekA4eKCKVaxFqEAQQBAiQDgsBdERMKcRHp65ISYQhBHDCYlMWU2K07H5dpq0QYQpwjBK8oiRDYtlcTkkQcIXCWYmAblFg3IxV0ReiyQOzvF7GEUWB+a1xMaBMInSV5ugadwC/iCKPAEHUldrTgjJCeG4bQW8Llrd8bY4PJhDRxfN8IYfGHfN+WJURi6C7YFmVLETLxhEFi78Y1JLTLfyuZ0E+RROivYgVCOCbkROPRgRRCv3yP0A5FakHIHO09wsJFDDw7JbS3JyxaRQg8uyVcZ3O+rY0Td08ImLNbmcTdE3p1RwKQa3sn5Bn/Ab1ai42mikrwAAAAAElFTkSuQmCC",
                         3267, [235.16092, 197.5151, 164.50813, 141.38399], [0.49921, 0.53496, 0.61362, 0.66986],
                         17652623)
            elif (record == "SRR847505"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR847505", "aerial",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACIklEQVRoge2XQbKDIAyGWfhyLhe9wttnlfsfodUWJCQiYGphxn/RGTAk/9cgqnO3bt26dYH+/itEVBP9e9X/HUT2f7Gxptk9lp9GEWE0kNdRTl2t2U2vn6lxNVDcxJjWX29MbKh5nhbEtsULYPeEj2ma1z62iBMSCUSQ0JdraeHcukuHIDx10jBC6JTwlFZCjAaYBNAAT5OsyJoQtCfOLyUIU8Rawu56fhNqx+tRQgtfdmKEJAmTN4LDdDAa4TpTQ1gXfoXyhFBJCMouqBIo743nxBEEz+dycdGzhF/YAmWExUV7J5R70hNiXbrjcNBDvkeIW34LwmOTr28y4DMUHJQWa7BkR/iO32nUu5QgRNcxYTBL5YRpo68kjCqQQqgY4I+bjXDfbNeE0oG4kwPh3h0JYxFCjlC3qxGSwQuDIm8pHvgKCJ6fuRF9aSBMc7qfEL7KSUJcppH3cSMM8RguqHZBJcSLCTc63td1kDQ1Q0jyZPJbI3ViSbgd47uExPVZ8PEGFYT6wfR1wsQxJySXdjBUlU1lHCphyqLPrl/OVoSgOGYjdNEdaEwYJZaEaepWaY45YcoX7IgJ8MFlhBCnFq7AiFB1zAklIHHLciJLGI1zhCz4NCFmCDVZEaYZFMLTiP0Tnv1CHIAQb8KsYADCRkR4rxyCsOlO9KVYzW4JGxDDykEIsZIvyT0AYWUTFcfdE1Yhglg9AiGVb1XV8RCEMmrVE52ZdHKDJWf2AAAAAElFTkSuQmCC",
                         7038, [614.71858, 516.31113, 430.0298, 369.58253], [0.5243, 0.56367, 0.64475, 0.69137],
                         14547829)
            elif (record == "SRR547531"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR547531", "aerial",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACDklEQVRoge2YS46EIBCGWfTUuVx4hdnXqu5/hAFRuniKWDJi/JPuDKYe/wcCnVHq1atXrzro51dAJFHkAslNE8mVOq1JfdRnEi0JighFK56Rhps1paiA7kQ4mTXUX5IyhL0R8+3mWRPOH9FuRN0RobDxlzV8OOE8CZ801B+xRHiBzhBCU1bvw7uRUCdg48TAKITNS28JoSGzTa2E7S+3JfT24qW4gdXaXicITV6wFxs3dH0/ZrXW8xHCYNbCVI0nR5iw1IEwuBzCjnpF5e6PXUK9R2orpQjTyUXC5XdxP0LTzv4RxZXSCuXNG7pLSLXzuq88IbnB2ne3UkyYemtNoTQhbQGShCkLOcIoMJnGouwN6Ya4xeGdCIETlu8N3+b3ia0PmlYXQ1SJTbalmlCUJYQjhASLtSCeUmmhbbcwy70X2f+G2o8wYVSKW/32cha9BPLO+BpCrCVEJaHkZDGrUEG4WfGJ3PAIIdlX+BpC1xOcF9c6JHQPVjfoIwTh4fjfCJE/qiTkXkQIaVtjKULghBA288/t7oQiRw2rtFrxODJA1xLmYpoEjyfklVYrXofhCYFXWs3kW41I6FWyZiDf6hmEGb2EFxHi4wnPL+LtCU8jvoSDEpr/RKJf9r6EeJwPWOIAhA2LyHuOQIjH8AIPIxAeWcV4ZsYgxDo8SGWNQRgH79GNSFhCTCcMR8ji/wBMqFOCS9h7YgAAAABJRU5ErkJggg==",
                         4068, [379.3159, 318.59297, 265.35255, 228.05318], [0.58381, 0.51408, 0.60322, 0.69146],
                         13627154)
            elif (record == "SRR847503"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR847503", "aerial",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACBElEQVRoge2YS5KEIAyGWTg5FwuvMPtsJvc/wmj76ABBQI0i5b/oqkaS/B8vKY159erVqwv08/tQ/WX0uXtwjwkj7db0408DIrm5s52xXXetFx1FCK01jRP2velM04TDFrStEKLcbrveNnLSxBCbkT4hxTbCRSJtA1ABoa4DUB/DhEZC1CxQBaGqA/UhTAhewn1Cs9zpoVVCwPm2RHUQnu3gc7o0TfjJGSOEk4slpEII24QnV0uI1AgpSli47f3+ReEI1xMW3+I+y4FgTgIlbocgHULyCRkTFJebljztI1xUVjLLk0uIzjMsqueaLCKkuwjL6gWEG6vcO6e1CGGDcEfBbEKsibDksMkmpOCc1SKkkHCpDOT+L0mHawYU+0FdhOmKq9ksQph6XEPozpNL+C3JAlC4xzFT+YR0EaEL4VaQCEl6fXxDvGkHeY1PvYLrz7mEOKfZIATiD4m1ic7QiWEpwuKkTzhkTxIyQKINQhCDGCEGjsOlcTIhTxMn5IDjiDAcx0GScAw3UsTNhM4Urh1g6QBetm1CeUyihIc/Y6QJESiQay7ySkkRUlhTIkRzSMCziISiDhGu/5E3RgkPTqJTcz8her7yCIc9mUOINRD6DbmEfgaRcCciTK+gRxDuW6hzpWYJfce1E45Py75lPo7wG5YjiAVXTpi7WMXQhxCuPnnXfyPdrovuMON7AAAAAElFTkSuQmCC",
                         3642, [243.40659, 204.44075, 170.27643, 146.34147], [0.51589, 0.54839, 0.62808, 0.67733],
                         19012222)
            elif (record == "SRR847506"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR847506", "aerial",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACLElEQVRoge3ZO3qDMAwAYIZU52LIFdrZk+5/hAIJoJcTywYi8qGpBkvoB2JI2nVXXHHFFQfEz68n/sjf6Mr8SPhPB2JuECZufXfrur42XQhTcz/bR3/r+n5gVgZFQUzhgOuHqMweUOtFxJjC6Rre75XZSIQQWVj7OYS3QrXh+GhaaZRQEsG5uoa7CxjKFooNbwKjPXAuoVPIbnp/eA5VGkhRaAh9HWObcI/LH0wI9bnZmpsKoVW4w0IcTbi9kaIe/dEGAX1LR4MQ5m5SVXo+KMoS+loG6y4wJ9pbGm8BM5D0hIcKBXLK2kEIVJUVJl+5gunDUYTks8LigxZPR5Tvu6OwdaGywhImvTuZyTocQjlrHBffAo7YR/icDymbZwnTJ4RoCI0GlmaFMNsshBYaHfBXBiLM3bAxhDCud0XCdYYW2u3GECLivHftJhk/qYJfyGrOm/YRMoFqb415fjLejlfhkkNKWEcFU4iHCacBuX5cCNa7uUsoay5b2QvWVmEKk7yC5LMJ00D8Tv5KqJ4YyyTVCewg5Edb+xNXkH428XGyZY2sUDWcF/JjtcHmIlmhDC5Ej1C2vL8QrI65UAGfE0CMC4XMYpU4XGhFTjhvKhEO42SepI2FtEq9EEWBl0IyPkwontC1QmEoEKpzpIXNX5/iC1uJXy+EEwhTtW5MZUW+S/iofwqh2lkG5PWjC71EUBW+Swgy+wxChFT+jyir4/hCLF5xwMo9hzCD/AeJq3e4+BfdGQAAAABJRU5ErkJggg==",
                         8470, [739.79346, 621.36335, 517.52663, 444.78033], [0.51588, 0.55626, 0.63728, 0.68627],
                         14547829)
            elif (record == "SRR1207194"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1207194", "carpel",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD//wAQdckaAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAClElEQVRoge3YS5KjMAwAUC8yOheLXGF6rU3r/kdogo0tWcIxxOaTQtVVCf7qNcZAnLvjjjvu2CH+/W8ZP7rot+kE66LD/wt0EXWYphDPp3u4x9BtfNDEnYXD+DcMj5ZDChNoD2HL2d7GcxiFjc4hiI9wcLhwXKPNzmGgEVeR9uwsHLoKEUgRx6Ims9XGuECb7TQA+PoYhRhKiN4KWS1kLQszrU9ua4hkyee+VQjm8rXKlLDjqsiF6D8olbwRsoOTCLO9USS1VYhzRdZyCqtMbVb9hFgjzKbnwnFBE8z5GduuebcxNquW27OYEegLhbQshI3CcAy6qTtcSAUhhAbqQqRMODdYEqIq6y3km19BSKEkFwoIUVmIzlIfLfSZQvz6gXBconovdjsLNdhnSg2EONZUChveLsRVJPPnQuDC1AM5BGI9zt2zmy2fgD3SgTrZDYVicCEE8EKkOTGKX0PzKcuyMDFcHIkJYVGIrlHwS0+eIfD7YhKSFqZFXCMkXuuF6b5ynJAKQsqE6XRbQhC1hwhl/jGhJSF0FTa7EHkWb4UkWgQhK1gnpLiHdhdSeN6XGRSA4qksK1ghhNcvBkDWjbOFEJiDf4+zVQqhLEzvUk7WTtc5G0IJQxbbhfxMdRXGR21D6A8LQvsVsyqAOz4QYoUQrVp2XBC+drejhXlBLkQtyo/TCELor3Hcehalo6PQENUKUf5oUv/L3Tx8E6Fd0EgIomrdyYTQE84sjFvRXFbNQ4r3qksI40NitXB626P0QHIJYXh/qwSSXOenFbIOwHrWCJHUEGcWUmxdBcxGvobQbvVFQrBbfZFwodVCWB0vI8RbqAf+QmGhY71QCs4lhELHD4RZQTeh71vacGzghYRiiCn+AEqEpXKjLFaoAAAAAElFTkSuQmCC",
                         10293, [316.71072, 266.00997, 221.55674, 190.41355], [0.60702, 0.62834, 0.72183, 0.72763],
                         41295666)
            elif (record == "SRR1207195"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1207195", "carpel",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD//wAQdckaAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACqUlEQVRoge3YQdajIAwAYBZOzuWiV5hZZ5X7H2FUFBIINWq01tcs/veLEvMJijaEX/ziF7+4IP789Yx/rtkOh9M1gsb/n4nXK7xC6D1TAmDeoI8T+9CF0PWeKbkQiKr9dcup8eq7LvS9Z0qCZMAbCEPX9f0wVR2DCekGwmkIfe9DLhyj2o+HT7Hl5h5uwSNPGm08BhTmf6kCyYZyrylK4a4kpsAdQnAQlqc9beJrd5lByDtBsdcWZc7ThEX5kFopH7Am3FVceWUdbu0UoiIHIbFXAvN4VnPnOiHOrTRPnDXhuF5ml7nOzwnj1izEqZJ6ueDl0SQk0d1UxKlC4v+L1HETKqE8PbWE9bpiKSJ2tfY0BBVCfi4uhHfC1EDTRcpC40peCx0fprUQ+T5kQlKFwK8K8RTa+48elwnL+uNGHNhpaGhVyA4AXSg7x7+KEINXsCrmERLbmIWjsTgi9WLZ1oRUb0B1oLNwSSaFAFxIBiGkDCh3yMN57Z8VxqdGSCxFOC59TIjvhThOSjkhLxACExKvLwkzsBQS5EncErJCh1Vk2ISUP8TFmHSh26NGE5LcagnnrlwortEsTAtGFOYriPHDk7Tp7CFMIzUmw/1CkA2KMM16sXcZ8WuEYBTKA2Jhq0LiZ6qFw0zXhXgQCLyqE4W0LiRdeHQQvYS4JoSmUElZCe0v700hnS1UREYhTR9jmIgbfz0gL2HZ4CqcTrDAtgvzJy17U94q1Bt8hNP8yMKNd+Y3CMWHylYhLF2/QJh/I3qesDwenypsvZ63Y/7aq36WuLVQey9oBTChOOdthXkobEIiKsu/uZDC8l1mAo7HYpHh7sJUsFlYJbi7UHZdiXbHhwih3fEhwjcdnyGENx3tQixTXSU0PGq+XYi7fA7CouE8Ic2LeZb+B7TRlwIk74OhAAAAAElFTkSuQmCC",
                         11302, [367.52895, 308.69294, 257.10692, 220.9666], [0.61017, 0.63474, 0.72791, 0.73422],
                         39074103)
            elif (record == "SRR1019436"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1019436", "dark",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACD0lEQVRoge3XQXKEIBAFUBeTfy4XuUKyZjN9/yMEHMUWGwFBByZ0paxSoNuHwFSGoUePHj1uiK+f/PilJz0L5CkexWYJRKSKZcuLxzg8zKVs1CQc9d84ls5K0ULEdcsIrRvLE+OEGO4Qfj+0UF+KBiahCnUjkBYiOmswoRijEY7nhZAKT8LwRzR9WL8Q9UAIncfXlnvSGMq+4CT01tz2sh2JXeVSh28RrHcu1sx8UYaE4L2Wjnh9TP+n56sCbtMNQv5mFKi4kJZQ861uwDrMyWtzmqkQhZecWkzIiAEhfEK9m1whlrRgQt1ReI1LfoLBhWsBOiZ6hfw9Z6oVL82Dwj61HVl8pTIIE9p39YyKFZoE2/upWUi9NpWz8aq2iNo8XsopdxhFC5EmpOILNSScdg3ceaV4odmWrpBP3lXC+SADeDVRCL566fWbjRShdH8oLLNM51N5m5SlZ/XYsYCGhOQVOg30WmYr6EOEtAsu3D4oL8zdicgVomqh3kYmNfzCqeVICOfBBcIMopGZDBlCz4PCwuj/OJ2YBvOaktB2eaPw7GnDKxwJpbhbqHKBHymEkKFe4ZllKs1RxULVhf9QCClBF75RmH7UiFNUs1B1YfPC1GXqZG9BqNKE8vCqhWkf0TNBdQtTiNgNbkKYQNyP7cI6hCoWCN/Y2oWxH1EAdmFTQoiDGxFGGH0DmxGqvekPQRmx5ysd18YAAAAASUVORK5CYII=",
                         7455, [427.75846, 359.28058, 299.2408, 257.17793], [0.62399, 0.62238, 0.71695, 0.72895],
                         22144930)
            elif (record == "SRR1019437"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1019437", "dark",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACGklEQVRoge3WS3qEIAwAYBY252LhFTrrbJr7H6EOijxMLA+xOB9ZVSokvxEcpUaMGDHihvj6vjNe36/Xz33pbn+aqACBqGmOeVazmnTTHHLQIiQrhEZJpkkpXTGfbUBqsaSIrBAIl542CL0QtS6eDgTIjGLKq7e8oGiEuK5EyCxVH3rSep5KZ6NrgT8MtuzTICAKhE125KTeLSwWupcsECUJre8aoZhvsdWcNJ7QL49KhVh63rQ6kSEQ4j5uikV+jrJvNCckuReK2/BBxtSqcyIUUjgsF3QqFAs9E7baxFuN5m/f5I8z3xMg/65QKD4ZOH1kQcILQxKSn/CYmFKEgNsouly4LxHt1tNnUxO+RBIeE2OacL3Lv/badI8QbE0uiQpKN13w3x6zk4BShe/7YiHeIty2/F6guwqKMQPghJQvNL8JwkXNNo7f/HDqfwlh+xLUCtHlPAivOmwoXUi+0PyfgoG/hMx1D0KK41IhJ6Ho5soAWbj+50wInyA8AD2QigceJ9wOeFEIrYU1GxHtz6/DdouuzoT8QBdCe26T+wYLQiaeINzWV+th3bOwdCtu66O/RrfCoj7ukx8gLOsit8JHCYFboV9hAXEIh3AIrxbmfy/YR9SzED9emN3E5wkzidHqjxBiDlCY3bcwp4lwmPwIIaYLpcmdCzOIQ9irMHUnAjN1CDsRYppQntq9MKWLwsRcYSi4UcgQfwFlb7MtehYEZQAAAABJRU5ErkJggg==",
                         9437, [496.34415, 416.88671, 347.22031, 298.41318], [0.62001, 0.62555, 0.72142, 0.7293],
                         24158853)
            elif (record == "SRR1049784"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1049784", "dark",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCYmAB3UenfAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACXUlEQVRoge3YTZakIAwAYBZOzuXCK0yvs8r9jzDS/CVIAUrKonvM69dPLUj4pPCnjHniiSeeuCH+/J0lvvRTfvrkZgE6aVazmG0zm0421dARLqtZV6ucMNTmcF23dZmRCAZQIY0VmmXZ/00XikI7hatCLuXQES7bvgb3xTjnlUZlDieORzhB0Fj3R/j5oEfYiP9BSKgyELXIQb9QmD0q/0Ih1ffPBsBkQjgKcSAdXRAOntJWvEeIZ0Y9LKwnKAhHKhLSeeHouqjPibaQrBDwzBfhzcIDSEFIUdj1k8aPE9p4hFkfHKhYWGiHIRUPyLF1/4D2k4S8KuQPPrV0QoiVtkChT61VO64K+eFGDtnbG11HrI4sJK+1asc1IdwgdI2QC+HKNaBfuG/Ye/X3AbpFaLOqCNtl3Kb9Iy/0h90Q+6+vVeHhLYbsm8itQghCvEvonhBi9kvvJd1CKAq/O98mvHTRoaYQ4xbE8WkJRe3CNW0iYbVymqrXwr1NXeiWf7VOi1AcE8UzOCDkk5AJ2RJrClFV6Kq5dRcUSUhcCPQ2IbBatk//cpB5CqMLwjQcyiMMEdiuO5Y/wmH6uCCEuNkUHtt0BAwL+a4/liVkHxeEflPmKArFRafLhgVheOoUQn9/qAv9gXD7QZ6zIvQP4dlZyoR4SUhS6L8sNgUchEffQUhSGLI2hdQjJNf0tJCCEIQQUrULQjcqZOctMVhzsW94zaIQoxDPCn0J++uQTCuEpXglFAYQe6eFLDmkjp3zCFyYasrx3iTEKH0pZB2hZyLTXeyzwlJKF/iyNqTuMf4B+mKg08nHhqUAAAAASUVORK5CYII=",
                         12298, [302.45506, 254.03643, 211.58412, 181.84273], [0.42622, 0.4294, 0.49922, 0.51709],
                         51665293)
            elif (record == "SRR477076"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR477076", "dark",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACqElEQVRoge3YSZKFIAwAUBZ2zuXCK/Q+m879j9AODAlEQD9S+sssfjlB8gTUbmPeeOONNzrEz+/F8Xd1gkz0uYXYJ42LYRymcZp6psS+XY/DMP9cl7OyjEZBWt/zGJppvC5pGloVjYJIObgO4dA0D+TPYtNkIjThMkvH8ZuFw2im5adlgCdqGtBmUqNQZ+lnPWoHIRi0lU+UH+NTdaDrW0n4SYDaIZWE4b5AYUbXRi+hnZNcqAyyEMJBIeqHuwm30oMQisKDC8f1HK9l101r4VyfqHDLS7EQk0assgcIie/jmmU7hrqQdoVY/hawMtgRQgshXzexcO1/PbhchYB0RAhVQlx/UyHagopdFOO4MHonLqeR7fjtnfJEcyeMJ3dDIeSFxA7O2ZYNkEKIhcTOiCvtjji4Tfuc8ONXvpgeqpCCcN2IkqpCVx7HJEJ0Ga4VbhPRJZdC4EKwG8hHyZSEwJYB2k7RhI19IX0s9KgghIwQnZByQtCE7mQiXO8WrU/SC4RudtYLIRGCfxAJIdr+Ni76Vx7y2oVQrg171fIkbi2MRkgKiUVeSCYsIgpP1zkjRsKtZyOz+lLmBm2EFAtduXZR5YSEJSEyIYWVVyOky4TsM9vnl0LIC5EJw9ntQpD7BaG44QfDtdyGSRUCF8pgQuJVCFMr4cm/x8pCkb8gJGNEDy2FZ+epeKVGQr6HYnom90AK/bW7QkqFtC+EHkI9fIkoivDn94XK/r5Q3M+DAbYhaUK6m/CMkQspGbW+Qt6DKjw1iq2EsoSvF0aGhkI8KfRz7PbCo0T7sQv+cfwEYfSfhSohPUmIRxYjUtL9/YXJFZkA/738ICFrVylU236LcO3ukcLaeao1fYU3EeLXC+uImZb3F1bM052GjxHiSWBsKgqlID3QU/gPaD+RF4FY+rIAAAAASUVORK5CYII=",
                         9459, [594.95424, 499.71077, 416.20354, 357.69976], [0.60856, 0.61366, 0.70647, 0.71542],
                         20201654)
            elif (record == "SRR477075"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR477075", "dark",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACp0lEQVRoge3YO5rjIAwAYIqszuUiV9hezer+R1iblwALMOYxk3xWkwEbxB8Uk4xSTzzxxBML4s/fyfFvdoJCrHkLcU0aF++3eqvXNnROKF/GocmqsamX2rbX0DmBipdxaLJqvLfXvoPb0DnLQsChyepxbKFauYeRsFLQI+Io0LVVulq4l+j4J01RSMFViEsWVWd0T3AxGoRhg/o/obSgJo6oCfnycGH5KT4qgIUoriInJOl2YVfOXa5HnmJ4EAulhK3Cc+e5RtzI2UK7GGKDkBBCIYVL2v8WNkycInfTbKGdnoVmi+KklBNCj5Dc6/nukWHztAl9A6Ir3ItCX1q6VgYDhFB6HCdCQOoRou3FqG360l2cJky4ZoHHQnWiO0LkEkTba4fztu035oXdx4WewcEgSWTyOCEaYfK1RTm/b5BdvBVSKvQV70YJ5eyqRs92kxYi3Jp1UfD6TY1AKowLBypCSoQUCaEuxM5dPAnjwy0U6ldKC+eykI+eUOgzZIW9dZoK6SQ0sP25Tz6yQvtu8IdICzERIgs5w0lIvUL0U/kjCpL1m0ZeqJ9SFSFf3UWIkZBc+prwltE9U0JhukOx0C+Yhb7Ergndhvk2FoU4XQiRkCQhNQrJOYPLWaE+aY6o/JvothASYRDsQUlIeSG2CMl/MO4IKS/kK4EwCl7GACFOE/pVtAv5DldI0cLahLRACIkwbBWEwBswSZjMcEtoM8RCClroswwRiu1rwsaNhEBIRaEEzAljQ78wGtEu5N8NPUJYIgx/orQJwU+QE8ohCxPDaCE28D5T2LCJ5E+JOOcNYaZjgtCPe4R6uDmnVTjBbxdCgxD4m8jnCKV7SkKSzpvvEUpDH+EvEeLXCy8SP1l4qU5BGvhNQnngxwjxnu9kqgpjwc8K/wM4q4LfZfcFtAAAAABJRU5ErkJggg==",
                         15676, [593.35275, 498.36565, 415.08321, 356.73691], [0.61422, 0.59983, 0.69073, 0.70777],
                         33569708)
            elif (record == "SRR800753"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR800753", "flower",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD//2UtrVzNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACL0lEQVRoge3ZOXKFMAwAUBdE56L4V0hqVbr/ERIwNpYXsLwQw6BJ8Vks6YHZJkq98cYbb1wQX9/VQT/1OfpEq4NEoKBVruqYZjUpNTfNCUSKmmasiXlS8zxNpcMxtvJPSOMIVZ0wChlMOHcSEha31DaWi7BcCMwBaNaOJPx8au40fDoa1FjCqgAuebwQzPm8Xtjt6TuMsNudm3whmh9XC3sVcyWA5rcGEl744tbt8asluP7eT5wVon1+5Ebu/uiJegkNxVlAtbn1AggrQ2arvYVm+p0LpZUz3/aCA7FOmYYXo0mfI5RVrRE2vLcBf7Jv1QwKuVBUlvKEEOxmhJJih33gXikQkhNK9tQAT5i6G0eFJKt1GEdCYkLYN+cEeE2mOu4sBDCJ8FQoLOtkWyutc8+rTtHPT3mtkzZ0HooJgYI4rOpORL47xkbrR1BXoTOTbFq+FMZBOraZNxnt2V7pYZrTWpnRVsgMwEwQjAZ9+qCz0OmhWAixbBlCSkr+W2gIuPwt96e9Z3cz390K7d4HR62REL2epMLlPoh6lomE23J/4foWXSTcP4zRXQF885kQyY2UEFVpoM5aIYTkCuD5EsLYQWsoBOooZB/OlcLSaWpHuzXHFGKdEJ4qNNmRZXmQcK99A2HJhejlHl2IcmHY8cOEXurhhfJpGul4bCEKgV7mGwilZ/GOwmVE/v8UYh2PLnSGPVmYO1chNvYeQiwH3kSYcxZTHUuFXHCdMHYafwGi60jJVS5tiAAAAABJRU5ErkJggg==",
                         2435, [412.18621, 346.20122, 288.34715, 247.81554], [0.58824, 0.62905, 0.72155, 0.71168],
                         7506384)
            elif (record == "SRR314815"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR314815", "flower",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD//2UtrVzNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACUElEQVRoge2ZTZKrMAyEWfD6XCy4wttrpfsfYUKA2LLF4B+BPSm6UlNgopY+27gm9jA8evTo0Q36999CbOJiLsN+YkOvOs3zMA/jVBpOaitTR4TDOA7TNJZGqyBgen2KK7LW9PpMc2GwDsLMfRGOyzgWCfwarbiZF1FVVYYa36NYTsjKPO2NcJyn0pVGJ0RfhFXSUXhVg3oWkambRghqSgjbvCohNyYkSzsN5asIoaHsgI2WGtu8GuFnCBsN4kJIZm4dEsI2s0bIPRCSrV2HhGapoSwpHiHpUZfKuHMVEnwloe/nEzaYp7iSkEWKRqN4LSH5TY0IjROjO0JcS8jr35YvojUhx4RoS2g3eUj6bXdDP4TViUn6bXcUTVK+d9sU5YThT0BaWwNCjgnvXWxqCCH2DI8IKZykN0/UGsLgXzPaWyWhKgrNrlNFv349IYKYreo0Qi+QLz6SKu9XBDF5hORsSo6k9q0lnBaNSkJ/LNb4ZMIttCT1+2hkvTiNrCCMZht5zaeELH52ZKZ2S8D5Vq8kVE6MziLJ3dOePImQKgiRQSi79XzM40iXlaRj7B+O4l5sLiFcCJzNAazs1gxCiDoHt+l6A6EXgu0CRy4QKXMIXZAFYd5iKgnfV4cuIWF6ppCQ6whfsYeLQDg4CAiXBUT2tlZnLqHrGvISlROy/0aJSuPSY0IIS1/7od6u5CMav1uCMiwIVyvynsfJSYSrhMu34rRJiL7v8vKinjBo+KzNEA89yzRCTSmI+CXShvDjB3EXPi0iPH8Vdb4/RKgg/gDe+3G014a31gAAAABJRU5ErkJggg==",
                         5556, [276.74425, 232.44155, 193.59798, 166.38482], [0.43078, 0.35219, 0.40696, 0.40304],
                         25509908)
            elif (record == "SRR493238"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR493238", "dark",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACIElEQVRoge3WS3qEIAwAYBY252LhFTrrbJr7H6EoikGC5eUU5yOb6VCT+BMfo9SIESNGvCG+vlvEi36a1GkcDfcJCBtWq4l5VrNSuqYESovUjVCrSelJlxcgoPUTvFVMF4Ki8u4JMWszQ62L82EXkr+aIaR7hWoyMzSXamHQEvYvvrwKMa3E3UK9CMvvQyZEtgzH+nW6LWFT4fLQ4ph0zZOGZCFQshDQCc2HQQJeZrw5uISD0oW4HopbkvnezzN4DV+Ibvv3dfgDaY7zhOi+LIGRrEjccjf7wuPkyAWKaefDkBU7Ri/mXpwK3jB+OgnJX48JCfaTEoW4//ecJxbbAqLdqqJUSMdJXQmXnWAXOsTvUlep3mTDtiHgZU8n51qGXSlZSOwBBkeH8LXC+jWJ7YniV40Lz10zhMTelrg3W8YKQcmmwv39FRG62S4BvKvdmhwhUrBt5gWD0JkQy4XCd/sKjQlRtYi4cP0PnWPrilboploqFGbVWAiXwsB3gNoIWcl/EUrAA/QEIay/HqJCOZjwtNBcWP2oAdazQBhZaCqsHGP/wqoL1TwoniAsv1LB3UYfKlxafLAQvB8qvQuxSBhW6FdYMkRpjzoW4hAGAVKBjoX5RDF/CIfwTmE28XnCzBeGvEF9CzHDB5HsvoU5QwyTh7ALIVYAnyFMHiIIuc8QYqIwnvshQojn9i5Mu0xF4FOECVO8PuV0oS94n1Ai/gLMg5QidXVB2AAAAABJRU5ErkJggg==",
                         7195, [355.67064, 298.73297, 248.81137, 213.83712], [0.6225, 0.62287, 0.71903, 0.73408],
                         25704434)
            elif (record == "SRR493237"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR493237", "dark",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACDUlEQVRoge3WS27EIAwGYBbpf64s5grde+X7H6F5QYCxKYE8SBRXqtQEY3/BM6kxb7zxxhsnxM/vLYOzVl39cGuCSbnR9eZjTH9iKwcFs3KjN53pB2YLgeGnOFcXtnOGAGld/hc8HKFG/HTDGV4qhFlaG5uksj2YdWFfL6TpdzRgyG7WzdckVIdtWUPfpUxaOH3TdJ/MbsQOaa3trpn844Bdyqk+7VqaEuJVGanlweCliLWauQlSEsIYPnvLUixtpvKm27owr+S2INhqQYWdhLGDpvu68AjiOhzBmOQPDTgWujQahetc2F1Twv3nFLIQttw4U6Rm2295TTje8Jp2CxLC3Ynerv6UWOHcIiXyIQjJ2+NqIbxdfaHXCZJVfZMoXN8eoPOFXCq07zO2PetC6e8ThO4N6O+qNAP+HlO37ABhXKtOGFSTeo2rwvYjGVoShv+D/C9k+1zmR8O3F3LUjAPNQhwq3OWDiIRwfj8owrnZ9oXgpFAKT4jwQoNCVAn5eGG1EWvNEiHFFw4QUj2wdWHVKdYK5Qv7CutO0d/hFV4nLB1TuHdd80Iq4AX/qDxRCGGDZwmlDRoWFhAfL4SU37JwM1FMb1q49YVxQyFtAkLMblu46RCV59O4kPKBUJIbF244xOcLv3PvIaRcILTcpwgF4E2EuWN6YyHlCfXU5oU5pwg5cauQ4r3OEgrEPwTcl5VSzpa3AAAAAElFTkSuQmCC",
                         8403, [394.87021, 331.65726, 276.23365, 237.40478], [0.61693, 0.61593, 0.71123, 0.74097],
                         27039911)
            elif (record == "SRR800754"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR800754", "flower",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD//2UtrVzNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACOklEQVRoge3awY6EIAwAUA5uv8uDv7D3Xrb//wmrDCLQagSK4sQmm4zM0vYpA5PNGvPGG2+8cUH8/CoE/Wlk0Q+920QEqJetKobRTMaMylmhI+E4DPanOEAc7EhoBlMlBJIGuxKOs7FCSITSIInjt8RgjQrC4JlBV8JpGqaxfKeZMYifVxgOdiSsjI0SfCC/VojroBNebGy0tVnLp0AqvPIpLkdWGyFtwhm0Ho3XC5cexHOrNiASbtvqK1SPpdY9QmxQVIqliSZCSoRuz1mFZNxZ2aAyawSvEaJ95YXtFioXEigW85mY0BahMGrqHOz/glDxdvrlAN8rxPVFW+HB7KZCYHtmUoS0iLuTId1VVD/14IVIkhBqhOEfDObNcWcysHdIkWiPAozShkIyhBTH+aqAQeOwP7excEskCoFYnM+N9qsJboXkucDe0PhMhNmPhEKcTf355VgoTj4QYr5IbAPjtPEVi5NVYV0EGF4Kk4HLCxbMcRsYp02K5D1EAnfuQXxHILpiPSRJehWCTXgs5LMbCSNVphBdZ8h7td+Z6bxwuRQkrFZ+ADvXM4Tk20iyumwnhUD2rIUmQp+1QgisftzWntDPcSNthL7TG4TsuoEQ1q8p8RZeIHQW0XCncJsepSkSfpZ6O2HZZso6Lhcuc6k7YZK7VpgOKAtL1invuEYoDdwsTFJ3L8xfp0LHfQsxE5hkfoAwlyh13Lkwc50+UZhDlDvuXkhG/i8YHsCmPkS4zTuOvY6fIZSR/+lwxGEJzAEcAAAAAElFTkSuQmCC",
                         2401, [431.88925, 362.75009, 302.13052, 259.66145], [0.55687, 0.6021, 0.68916, 0.6737],
                         7063908)
            elif (record == "SRR1159837"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1159837", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACc0lEQVRoge3YQZKrIBAGYBeZ/1xZ5Aqz783r+x/hGRUC+LeigKMpu2pqEiDdfAKOk66744477jggfn4bx7/NHfXikCsIsXrMjqJ4vbpXk8Rm2EJtUu/ZPfqfI8MUooKQ5H49T7OGXGiN5sFGPw5fQ2upaIe9p2mQFM8y4bb6Q0QQBK9VSbZtQnaRHmW7dKU+XZVtwk2HEyxFWazUryEkjVYITVES4EJfhZ+scBbBCBQLUV+oQoW+cV2okZDM7++FLGNN4ZY58wxF0QuZwZehvQhbdwpB2toIlRn6RrhXpKDGqvcvsefHKoAfjgbCd0aV2fX0Qn7vSITvoeKzden6fCatbmC8C5L5kIIFMQpn1dQRzSX208AwYnzvhJoMnkYPZ1rcSHM+Qnv2xooQyioiVzg8zSTC/rWYQhwqVPfb7B22o6ZCiYVIhTq1srkArF5JQJcMyBBOgExh3zC+Y0JtL4S7R2ASyh6hdmIK+5vaolAbC/3cpkYVvsShcByASOg/oP1tJRbqKCQQrS2UgOJmoO6RyQldJM+uc6FSIYaNMBfq+YTxoxvWhR9RKgwym8IqRFChGsLgoCZCRBmIENlCdyQqCIfTEQuD4/eZCVSToggdplBmu/Jg4ZAiRxiFE8q6cC7KEgYhTYWyLNQawiBDM2Fw8hKhxsVi4VA9bNgnDDL8iTCZyPcJZYswntRFhPE99KpCLRCmDQ2EhX8uCoVGQ12hfL3QfUvUSEjjYOGefequCq4hHJ885LuF8zHL4f8r/VYhpjrwCU4uZGOWwo+Pa55eKNuA7guSCwmzF9FXupwwlzj/4GWEkuOD+cFbeAIh2ab/ARqLTe2ooKEtAAAAAElFTkSuQmCC",
                         1048, [235.30652, 197.63739, 164.60998, 141.47153], [0.57497, 0.59357, 0.67881, 0.74618],
                         5659168)
            elif (record == "SRR1159827"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1159827", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACTklEQVRoge3YQZaDIAwGYBednMtFrzD7bOa//xEGqyIh0UpEW33mzZtXkCAfFGrbNHfccccdB8TPb0GgpPEQf46cWlE+HXBMITtytkTbPLt/zjiB8NE+mvbR+pLJJfTkbIm2CcTWl+sS0vHCpn0+fbk4hzAsoXMfklPIrrt54/H0nzQEez3oTRa77vaJIKBciGsIF4w1hOqts9ekBaDZNZgGIunLRk7xZv68sFtbNPaWg1h4auJ4l3eviHAAZJ1aw6gQ24WgqVWRMFvEPYXGOwxRGCZAjVsKw2s6t1Bf10KUCvUJZ5942wM28VXbLQwbl0kJEYWL+5GmR/ajhRzLlFTT62+FkKOwr587hkN5zDtM2AvS8fJwO4xITVRCKGHfSxTGcjhzOfYhe7VPvM3hF/bLRErIyWBNIWIfstdjhfReGDdcJgQlQsjBE2NJOFZUpWZCRibMJyAxyVKSlwrH2lSIwTMvrLkjtRDjR8QMMReOPUxCpllh7I0WhOrKppACGsaaL2F6S5QLsVaIqkIWwnQErJdw2hkcLw9C0YJk+zkhWw8aQ003P1U2IllCcX9TSP0SrRdyX7laSHsJkZQs4XhP9B/vk5BFAyVEmTD4OJ3QLboFIWoKYQkxJ0QtYfesvCA0Qw5RV9QRyvk8iZBkOe/h/EK7vLMQiD8lXVOI7xduJJ5IaPzOt1aILxcOvV9f6HxCvYVfI9RtriTkWHNVIWLr6wrtVotBiF9ITyDMUlfFq3n8unNBIVmJlxKaiScQrtuI0F/cS4VScKRQG/8Bslsj3ph17PMAAAAASUVORK5CYII=",
                         2393, [332.71558, 279.45268, 232.75303, 200.03603], [0.56527, 0.59063, 0.67292, 0.76046],
                         9138919)
            elif (record == "SRR1159821"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1159821", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACP0lEQVRoge3XXXKEIAwAYB9szuVDr9A+56W5/xG6CgIJQVcEVh0y0+kiP8knrLXD0KNHjx4N4uunbvz+VU6wFU3uIGCTND6m4XsYp4YJWwvHaRym10+76HtYPNrvIYUN1oVVEp4Twv6QaAqlGoS5ZWzF+H3qlNL+EBlJIVHGatXjrJDKCCt+tzNqEigMG/Ovdw6+HAP1dl/96oBWhJ/CUVFDTFQTSFDFA54Wzj2gdEsUyQav1S0RHkQgcRvqCTkB/G9YhJQhhEsJga9sPyPtCKNtc4vFQndDuFCAqglJFb6uEcEBoRm1CMkJ7ea9LYwzFQjgwjWvE4J2a5VtY0InkkLyD51o3apCCptrurXYmAiREJgQvcg8d2IhxMsqiYqEqQmCFq7pDghfKPQN4kII2v78bgmLSleJT4zBZRJbHJRnbgo4FLoeKZRtt35cCdqPWMznKOhrR5yfoiyip7+r7w0hREJoKWT12SzoC/WB0aRMIS6P1E8JwX7eEVIoZAMUoWzj8sBJCM1LrfYadZDlF+AV2IY4oyFoGXhS6K4mhHFXlhCYqaFQLsmFCAh+fHYsN5IL2V/BLeE8N7zATcWEJzdxXmBLKAppLNT6jgMJ+LkUbzIHhNxwWpjoayyELiwhxA8KExcKC09tYpjz4sLMrezC6wgh87DeQ4hdmA64h9C+WRyjsTRPFJL7+t5CaF6P8QAQ7HiW88pCddSekOR/9c8T4pOFZryo4QZCfBcI6sRHCNXFnyQ0a6Um3kCoEP8BEOeJVvJ+cZcAAAAASUVORK5CYII=",
                         3592, [235.9531, 198.18046, 165.0623, 141.86027], [0.59216, 0.59686, 0.68307, 0.76291],
                         19343538)
            elif (record == "SRR1105822"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1105822", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACSElEQVRoge3YTXKFIAwAYBY252LhFbrPprn/EeoPYILBB4hvxDGd6Yw8EvieArXGvPHGG298IX5+8+OPCjrfIUq/DEC64jtuG+NoxvlXVQB1IDTDYIytzJ2EHRDtRBxtXS6lhFA/n/ZhB2vNUJdLCSLCjW7tMP1YWyeEhPBeD+9kG81gq3KPhDcinoiEEB4vJCFEJe/KSTWNHKGy53R0f1chxs3E5d8R7ifRJuqETf4Qih70q4SUEBIT7j+HqIkQ/Af5Q18s9OUEhQ1XKnTXJff2WiH6croQeLNy+KeERU9v1FV5kk4E+Gqe4i79GMSbc4Rb13ji6dgJW+5e7AHkwti9XGtnf9zEhNmvm3HRpkLYTD7WK1wXx14oB2dPsKyXOF0Tc5ANLYVAKSFNr/y8db4hYqGyrLVU6I6hMvEtBOZdFvVJyIYvCad2QGLh76ebNXM4gDhSgT/zy3JfVmaYOjNoQjRtgs1IEZIUouiwHHcgGkgR+uogko1Ye5rw7E30pzGfgybkwFbCcI0mtUGzflgpnEviZ2Ei3BRRHqGZQnYNR0L3DVYKQe4jzYRQJnSZoYIQ0lnhOtI5YVimmiFPiOohG6pS7ZYDrEK9MNlQIPRHkCYEdlh3LMS0cN3azgjxDkJeIRay7k8W+lfvMmEYqgehL1clhC6Ey+FfKRRj3loIhQuyMyGwvDxfb0K1z0FstZ8q3FL8KM8VyjGfIgQltRNhJrFnYfb/tR4u1BK7EWIGENKJzxAeJXYg/Gg8TssXSsG+4ULhrvc/AhyPBEYuSIoAAAAASUVORK5CYII=",
                         11402, [376.47148, 316.2039, 263.36271, 226.34305], [0.62558, 0.63284, 0.728, 0.72283],
                         38483470)
            elif (record == "SRR1105823"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1105823", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACRUlEQVRoge3XS3LDIAwAUBapzuVFrtCutdL9j1CD+RlL5WPsQMeaaaYm/B7CxFbqiSeeeOKG+PruET9deuke9ctBQjnAqVXuGa9FvfRHYxDwRqBhiMtLLcv60RRAgnD9Qsru7bG8V6FqF/ISqfwT8dI5VEtbYxIkUvlnQgvPpHB4oTlp3u+mtpJQlE8Xm+R4aFphrfHE6XvVwU0UJwvDeKYYC4XkGgo/PCUBmK3S1NtOSKEY9vRMrEuBtrvqtIc+GhsKvbnuLATthdsrRNEX2dVFJwQtLN1uSb2OQmSE5C6sJggxv/XCGtm7t2yuFwrRJ+0o9Nmk8E1ur6bCwr2dCvsd3fEkIC/MzhgahUmt7kKM/o+F222UCFHuDTihq//XHZyCOglRZYW0K5eEbu7rPcoIydcSjx24RmjmlRNi6uPGdmiddFEIekcIG+AK4brcZrSs0M8zRJoKioRRf7C72t7M+D0OB5AZmataJ9Sj5YRsCPMLiyEIw0WBcHtTbX582xbUb8FKoR0WW4QckRfqsvYHP7CDtQkdqJfQd5kIQah/nzBMvULoj1ZyhzBIwl39NuF+XW8SovLNzR/3fn1eSB2FUUGd0Px6IuuIB8MTQv9a1Co0aagVHq4HFoYehhMmvZ8Q8gVdhS034mHGYwv9++u/FdZnMel7AiFWCo8zHl2om9Q8oT7CAYVU9ww+o/BYRQ5g2s4hxEc4vbB0m3JNH+EgQvz3wrIsAtdwGiE2AucRFiSRbzePMEeUmp0W7klXCkMHNn4BWEsiqTNCj30AAAAASUVORK5CYII=",
                         16537, [687.0589, 577.07082, 480.63587, 413.07514], [0.63356, 0.64517, 0.74182, 0.70408],
                         30583559)
            elif (record == "SRR314813"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR314813", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACDklEQVRoge2ZSbaCMBBFM+DXujJwCzquUe1/CcIHk0oDpKkkyuGdYxetvHdJA6pSt27dutVBf8+f1uv1pP13Rx9cCQHN4g2Tnh560oPiNBD5hHq56WlMmhYKCbWa1KXH8DHzqQuNIYRjOPNdm3CeoPpKszQkvJpWQhwdo6HkCeHLZgT1IQRUo8DFCeO9EcGopdCCMDJaAxe7NGFwmWtb5UxyBNKE8ZPPwHPSRihmvoNyIcKdKSFrkiW6Ccv6W59vbSC/2tMFHQgBxNdCfiAxbwdlGzNazvajCKEt4eeBuaCQUaqst5BzhBA4YfdxbE2IKiTsut+AOCG5hEu3FEjIK0XtCed+f5VwZzkFhFFVhc6LWUEY/boHDsOPE0aDJhLmmpWr4rjGg7q9jScE7lpSyhrw/z6bsGzCQl7MIkI/KSBrPiU0ZnOCgquczxYAp6XjCJFMAMweRqBkwp2Zk2biHhZ7kZ1LWLTJrSW5hMmTW9UTUjkh2JLzn549wgwnf+ChHyErOSUExzKH0FSiaUBr35HQPonC+oTpS94WSRAutZn7vwWjj89hzlU1hFRFSObLctQK+euA0FzapxBi5EOHgCxpFSHyBp4CguwBofmFZOevhIjtqYCX4NZTFaHbEDgxZu7qLTMvPUPPRvRrmKcI4dLVuu2Z932iJMID42NBtFCQcHlBzQjxOwipHWEE8Q3y61gEEPun2AAAAABJRU5ErkJggg==",
                         4937, [240.86312, 202.30445, 168.49713, 144.81228], [0.44529, 0.29639, 0.35004, 0.33927],
                         26044624)
            elif (record == "SRR446027"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR446027", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACGklEQVRoge2YS3LDIAyGWaQ6lxe5QrvWSvc/Qu0kBj0gBaO4xuN/JpmxApI+yRDsEC5dunRpB319t+inafS/a0M9iNxL7K0p3MNt2jqbjk94m25hmj8blSWEnoTcNS09nBu5UQMQ3u9zD4NzD7EjIX9136WoTIBHI+zdaVCZgODwu0+1gCzhbANDPaxqCI+17bQqR0jKNnY/i4TEhqAaMJQUzSIg2USwW9FIyhDSqQh1vxa9CImP2T0xN0lCZKZEZZo8lIDTPEFXwNjYsxHGFkas0xPCRXhs1RLi51PxCwH8uaGCUG6sH5NjEcXfmySkwLbStXG7Ebod8B+5I7soEj6swAnReNsuBeRYRdYeQ4gC0BC6PhcrXzsR0icIC5MsoRciJwRNSIaQegkLG7Hm4XXvFF9XgqWGsD0HyPbGWsWt1addCYEF0/ZMWq3u8yLmy51Qv4WEQuIFQpeVCB6EpQVpEheEDN/S+BGSB2EpFXNTimipLvCOcBkMHa+kWwjRENLjeFUstmlEK+E88hmkdU0q39WEKI91y4VATuL+Ym6iVK8CpR/yhLB+tSGm4U2E7AQQJ6MyLI7gdW5enScifY1/EYrg1YJUEGoklAOKhFRLSIDR6kw4B0EbcwNhwVBLWAQoBq1RDMNCDEGIjYTiWD0EYW0TITf3VITZuWcihOzcMQjx9IRVTcwDNhOi9rUPYQXi24wHIMzdqL9v/gu/5zcCKAAAAABJRU5ErkJggg==",
                         4965, [200.39733, 168.31665, 140.18907, 120.48335], [0.53715, 0.52608, 0.60994, 0.61117],
                         31481295)
            elif (record == "SRR446028"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR446028", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACVklEQVRoge2YS3LEIAxEWTg6lxdzhWStTXT/IySk/AHRePiIGTtl1SxsFW71QxgX49wdd9xxxwvi47M7vr77NcaE0RyRsJGSRTwe7uGm2VTzXIRumtw8T6aSJGKq1xmz/82mkmaEZKIyu98GmveQTYTgTCHpoxmd/lrYTIjKWRJy2kb2rVXpY8LpMTfvNMQwa0TodVIlnyNNaFIPW8ikTV5Er5Mqie+syo4kRNLIV6M8JkyyIwkBCvTVKp9IweSwz5MvxTBrMqkSwqyvvLycUPQ7sXhgI/lV6QmhQTkQBKthDy2hCdn5+cwQcn+9NFC1NWcxq4qQ2G3iKaHpOl0WDKFqhoSkCUWOCLvrhaV5kQ2rUWxrAKEcE1o2cakZVxMXJ/sJY6GogylhkuoJwoQquREme21p1BKaIZKUEco2ntsKnZMw9MFr9eWCq+tUElYWyIZkCMVvQMDFelG7WtVMFRBaNTFL6C/6CSkh0vd5Qu7hChzkCQXs6NvFr3V8nNT6vNV5D+GuBAhTFxQQFlnoIbQ70XDMFN+FLqieMCXS9weEBfpPo45Q+JgQOHo7YSBUQhgM2FnHERogUg0hp4TKATu9x9K1CKMBgJCW495yt8j0EPbvNVWE8YAdZrURM5D/nLyJMDiaWBBSlNgJ16Z3EXITYCAZyjQSsmQJMdHFCNXnYwRh/VJNOToIZTghBQ/VEbL20EaIEgMIa/q4i16DEA44CqV8ekKKnioJ5PjEhNtfxuVNvBphZkQ+CD38rwih40sQchkgoWdvwnMQli3TjONrEDJE+gEE7CiWokVdOAAAAABJRU5ErkJggg==",
                         8658, [260.51637, 218.81151, 182.24568, 156.62826], [0.56495, 0.57833, 0.67021, 0.67381],
                         42228711)
            elif (record == "SRR446033"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR446033", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAB+ElEQVRoge3YS2KEIAwGYBY253LhFbrPprn/ETozUgwkKDBoTcu/6jAE+HygU+dGRkZGLsjHZ02+qnr/ehqOB2HvI9w7y+IWN82t5UTUcTGnZHaTm+eptdyAcHkSH87GGBCuvr98DufpjasUyIDwscm07zQvIfZczt1CQ2g+Q2g+MITm81+Et3/kv5EhtBkghxj+5jcirt8m3dFZC7C9xQtX1asV1u82p71THL1rCyGsHyCw+PEwEuB3HiVCzycILBM/r+LsCmkTeuJVQug4VKmQtu7Yb/pcOs7Bnw+gCon3OUuY7tndheiniYSEUkjnCCG99DveClxIiTDJ1thtdh8QYxoRFm8XdoVY2lERltYe5lShWCc6tVYTktP7VudkIYkGLOnohT2IUCFEVyhE2MZDOZsskK2PhtzhKAl7+NQIf17jDoV+PNn5MiGrZKfnWEhlQsgKM9WgCosOph5eWSfEqPvO+BgWLo+mrN4T7k+lJ7pU+gshdIC4N1BSjVFJRthC9MJnJcWLaBGKFUhh+k64feb27sLXkMkwh8K4A+uVrq1QSOwRlBM23IlBuE3ZLkw/I1QKwwadFWK1UFtxmzBteC61WhgPqS2ylpgM/IYQ8g1nCIvf49UV31roI/6xmQkotTaEpXuOZSEWCfUV1wpjwVVC/SR+AwPBcvsiB8w5AAAAAElFTkSuQmCC",
                         4701, [97.15559, 81.6024, 67.96573, 58.41211], [0.50447, 0.5379, 0.6179, 0.59714], 61481964)
            elif (record == "SRR446039"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR446039", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACXklEQVRoge3YSXaDMAwAUBZU5/KCK3Svle5/hAbwKGxjG5khRa+vjwCS/BmdDMMbb7zxxgnx81sVVLf7xdFyQEj6CLdEdhBqmOZ/fYqfFblBjGoc1Kjaa18jBDYKzOyrPn9KNbeibPFuUScch2lqbuWEuSbiwa6cHaE6ch9aIeSaiAcXZu6VcRon1SqE+wg7dYdPaXP4Tr0fYSPs9MD7B0Kchbg2wT49osFB3YS0CEkv9+kRC3iFYhEIT5zcbED9hPSlQlstFKJok+wAzhLCRUK4TIiiXdJxghBdp38vbO+cmed2F0JC6HfR39/w24RuULDOHBuEoGlXCikptG0+wOWipfrW5vjxyXWwS0SIlX1yYatRWqjP6DOFkBGi22dej7VC9IXJ1KhQ8DK1QkoL1/VAYWcc9gJDYSLhwcL5ymwWyl2n5UK91XbeHcJcijxh4rzcTWgnAplnh03DJwotMS1cdoClMlwvdPdHRGgaUxh2ZXwQ68sd5pcolQi3W4LmR0NCuK74wNAsLIULhZEtrg0ewtnyGDK8T97ouBC8JQ3TMzPCIAl5I9PaXM4Z4f69LiNkwJSQ9LOzVKjz88LDv73HHFzITyEXUijkWSmhyXclmZD8CVc3IWzPoC9ELowcl4TQbksLEXmSvHB93qeFxISeSUJIPKlU5eXsCmMRCqlc6H+nNtv4hkjzI0LwxtAkxDoh2q/CYErFEMeEsJx9KeEyL6sQEoVCslI5YZAkIIQaYexzJyE+TQjlT5zIMI8IYyukhbjuX8QDluj3vK9QvzaKiGFddJOHewvD1CD+AHhfnlDgOs1DAAAAAElFTkSuQmCC",
                         5328, [112.22497, 94.25939, 78.5076, 67.47216], [0.4787, 0.50595, 0.57795, 0.62009], 60325368)
            elif (record == "SRR446034"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR446034", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACKElEQVRoge3YXXKEMAgAYB9SzuWDV2ifeeL+R6jbtREQdzHB1TjSmU6XBpLPn2jbdXfccccdH4iv78r4qW2wY8QcIoppExWpT0Of+siWJxP2XRq/pciWZxOO57DrYoWAke1qY3icwvErMIhOdRb7lIIv0rMJx01m6IahtByXKRiFRrrVIFicr0sJwboiryVEQ0PE2dC2Fv40KJNaWLftHPLkEcvPwrwUKazdWI/Yl9l1RzRz/rPQuhD4+teFyIZjVx54eeEBbw/A1g9KSNOamMrYiTbFAU8eWhVOP/CcOB7F01WUFwS8FKLK6W3nXW+0JtN79c4hhKSFlFO7CnfFciEthZBzyIb7e1uT5VZzHnVp4JX8RsiCDd/Q25hsKVx2DNyOioTO6UEPXRdqY6CQz+kQ8uG+3jyhhMjTurTA8mIV0UJgvflYuogQ8LlzAKsTDZ/lTQlBfpoGuIVy2JTCqA01Qqj+8UG2EBZCmgv2E4JfaLyk5uXIT1qYRbYQTCHpA/cBIepXOFMIWjjdlZaQ/8ISRhA3CsUA9qdHhVC2ZMK5USFNoIqEMGdyW2SPCGCFq0IQLbnQzHt1hCgZLiGLdSFsEZJDiCXCqfZxJ9cJ5wa59VahbBkk5FNVClEK5bIcQt0yRsg7g2izXUioE+HCAmKocCURKRyHy3emt2Gt+OTCjczmhFNcX+i+IWG9+BYeLPS+3pi1bQjRBYQXtWcXuk6iDWxFaBp/AarrmyNITS56AAAAAElFTkSuQmCC",
                         7852, [157.40157, 132.20388, 110.11114, 94.63334], [0.56019, 0.58674, 0.67547, 0.66481],
                         63386459)
            elif (record == "SRR446040"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR446040", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACNUlEQVRoge3XOYKDMAwFUBfMPxcFV5hele5/hAkQHHljhOWwJKhKHNnWQ2xx7o477rhjh/j5NQZbF3hjtDlEDGqzUKPoXee63g2V05EOMdhUUeOYcH3XPaQ1QZxqTiacdcOjkRUBxzkhM1mrahl9N4zIqh6CLiEc21d5loJzGs6xj4tuMNxpskKcTGgK/k4hf5ww1nygkOYvJAcpP+Ei4V/KwKKJCwrXF8KXrxJeEAt/lWmEuF4/xX1kRcginfYt0BryIR8Kn6PcVHjA8ZFCDoXzh1AIs3D3B4+4ypAIefo7JS9Ek3B6sT9SyKnQo5fC2FIjTLNNm9L0OSPkSGir8VuEpMms3WJ909bCpEy9sGGj3yqMMVwQIjkaDZ8pVULl9gXhcucmkcixsF0T5Z4KYakLMkDw6wXjy0r0TAt+icta32ND6IUUp5cCzwREJ3S40gmFHKevLElL3TI1FnLwS7JGq9tNlXB1a78ewlwUhXGz3VFCchrhq3OLEOTEVyEkOSUpSzbZEDAI8xUkQvpXmDloMnFXIWSCFwbURJi818dCFIU2ony+1QppKSeubYNwebvPCmvP03Ftv75eyDlhVAhhg5DlaF5YSfQ70TYhU5CAcV5YB7YJ6X9h1YkqSt4oDBMgzPOAr1cpTP9+NhGKVf0O1cLCgFYYr1ASTt2uEoZ7nlLI003jNU0RuYpPLpTTPlFYSCkGcnNv4TmEpBOuzD27UNdEZKdeRKgxrs7UC0PBjkJKSX8vm2oTjBuflAAAAABJRU5ErkJggg==",
                         17220, [292.97652, 246.07527, 204.95335, 176.14402], [0.54039, 0.56246, 0.64858, 0.64035],
                         74683660)
            elif (record == "SRR446484"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR446484", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACNElEQVRoge3YXZKDIAwAYB/cnMuHXmHf87K5/xFWLP4giUJIFTpmZtvuKgkfMMi265544oknLoifX138KdtdGkUjgzYDbB790PXuRReIy0dA8a57Y+i7YRhfVAGEME/e/UKhA8PLCV+6nEBE48/02b/dGEIHejeHvXoOp3jnr1XYOWGnFFIgREJdGoNwlaU5LNlpqhLCJxZRKKT7FqrbDCyFuOatRwiWwjlVPcLNnm6Tz7/HQrQrktcj2/EFD5mBrBDMyqUE2Y7vLKQj4bULlmwn8WPCjIPfbokYC0kWUnRTTgAm95EX5pfkI0UImoIZs7C70VIIrvO4TRsIfQ3QFIQpVRqSF5oQAROEENSby55tr5DaS4jOL4ZCmB6tGKSNhdsL61lDqD+OGfrU4TJAaUjGlILQYK8BxiELERHWukJ98Cd2WFotlVDuRPgXCtuWRIqQlr4S0SqMBn6XjxEKU3IgLJ9Ebqa2QgrKBTcAN8IaIXOlXuHWxAnZVXco5BoYC8d/hEVhNMKnQq7HNwvZWDq2r38ulFb2FwlDC5C/0IgwmKdEIR0Li7caE+HyJE8S4lL6/aznIHZCKBTSdLAJT69nwvV3FJ8KUbH7hBNy7kWucHuUkIVYJAySKIXMH1KF+wyssGwSmxCiiuZ2aWxEGF1NiqkSNiNEFTBKULEwn9icUPMdUWPCTCLfum5h1m4jjE/lQkwHgtC4cmH6t8tM2+8Scm3bEKIe2IgwaRKBb9qIkDX+A8/dLktpr31BAAAAAElFTkSuQmCC",
                         11131, [462.45707, 388.42446, 323.51442, 278.03951], [0.57488, 0.58873, 0.67788, 0.7109],
                         30583559)
            elif (record == "SRR493036"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR493036", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACbElEQVRoge2ZS3KDMAyGWVCdi0Wu0L021f2PUPxEFjKGAApk+DOTxkaW9NmK3Jl03aNHjx4Z6Of3ZP2dHWBBNluINmGS+qF7uTdDoWWwrhv6vhsGy4hAltFG9eMZmiKaEw7jGb56w4DWhH3nqvS6hIB7471e1p3mCEI4JJOzRIR8iLpVkr4fFcKGLysVhFDizqUazLDjuOHLSkTEB7hsvZIwGDV8GQnqhChtpcHkQ1ohBAeai7NUawYkCIl9Vs1R8S0ngxvA/Z1Xhlc5AMKzypoFQlTNlQhyMhG2an6rxmIpIkVcCoSVYAVhKFlMT5QlpMzCDDsSqtuxR56QJRDdbyAMA4retPwy4VSAQBohhQeVqO/J+SP+7YnuySezmnCsLf9Zz+/zhKQR+lclFvE0yI/CeJ44dh8jxORWJ/Qn4w5HtBvKT3lmVUJEvh+mhJBJBCHlBELqohNWCKkkTO3ZVS9sIBzvxBMIi3RjM5wIqWwe4AfLhJj7lV8rCdH9KYMeTugC6YQAwT+Vmm5MSJUUl0DejImQ8m0OKedM6Fu3e6sQErPeQ+iS0Aize0FYXH4rCIkR8pxD+woWFULm7FhCNhqbA0rCfIjetEVIdcI4FPtmTEg4O0Lih7yVUB03CPf+WzNjSi4XCPmNXhAWDIcR4i5AaBDyQlIJ+UQu6CsRch8qoaoKYZnTYYT7yvQhbBASWhDuQnwIW4T6xEO4mRC/nfCdC6PM4gsJIfosHFyZELb+tHE3QsWkobiijHl1QtxOKHL4PkIUa69OuL5Ma7vzLYSgLL0J4TpGDfA+hPgm4GZClK4uQ7i88AaECuI/mW9cvfT4ehUAAAAASUVORK5CYII=",
                         5406, [326.4174, 274.16275, 228.34711, 196.24942], [0.60356, 0.60858, 0.69799, 0.75239],
                         21043986)
            elif (record == "SRR446486"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR446486", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACB0lEQVRoge2XTZqDIAyGWTg5lwuvMPtsJvc/wggq8k/B0EIfvkWLlvy8BIMVYmpqauoN+vkt0F9w2K/KlwODw760ikUsq9jqrDE47EoKbl2WnbRCRHoIyJQRu2QNj49yARHBWbzOCRVkuSQh4VFHQkGZ6R+SJKzdpYrw3KkatTctm9jW2k5DFuHOyJlZsVpEdwk/W8QW0Sfhe9UgOvRDiLBnw+ju/PYJMWbSWHsm8N2EpAj5ol+LRT0Rsj4kpyfwCY3XVLZoL2VErAt8bQdKETZuOs4CvpFQx6C2b+IfJ4TWZ4fjm3gRKUt4PqGI+3XJA4mvTnZPBjuVx8oS6hYkm3hBUJCu9O6O/1cB4aLocBg0KBTkCMkkLAkqCcHcBxFTgCghSxEpS+joyjPXe0CV3Nrp8YleTmyEcOccIiThE15hc+Gv0uN9FZ9n36rZMck00HZrXokoIeTCd0JouAkS7v0zTpiObycJwYRl42pLaMYNEgalTb346mx1OrBJ6FYRLJcDEMp7gClCwwKOLto3oVuSw1uK0EiZEByXoxC67wk2IbmT04SPjwszhypC9dpir9drhECWuiU8ILGE0LtOEz5FZCC8s7CZuAhRPBInocPARfiwiCMQ4iQcntD7tUQwCTshrN+pln3PhNVlHIiwEnEkQqwBBMu4c8LyIhohxiDEIryQ7ZiE/2WaoFoOkKKoAAAAAElFTkSuQmCC",
                         12339, [504.47891, 423.71921, 352.91103, 303.30398], [0.53328, 0.55476, 0.63714, 0.72532],
                         31078655)
            elif (record == "SRR446485"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR446485", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCZmZnmW5lJAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAB8klEQVRoge3YzZKDIAwAYA5unotDX2HvuWze/xFWtEpAglT5KYzZmc60aJIPLNVV6oknnniiQvz8dhp/Cce0ntx7QeGPJ61e60v3IQj1NCm9vFTtpkQIQiPTel7Gmr2UCUk4mb9JjbuGerk+R7hKQdxpppceYKcBUThK1BBi6QLRoEJCxHny1gAsUSA1yESBvECoaFYuNbBAgfRGyglhy9xUuAAzdrBnmnlW2HIrW4X5Otgz8cQ5p/DjKCUEV9hwESnzZSoJMXBMncgshHcm8oVc1USYq+guJF+I7JiqRMq7iCQKiR1TduMB9219IWSpBslDbiu3IyJEp+CtKuZuAuUe/JZyEiFZKDcYTY9bmUiCZkLamwuUS7s3JyYU+p0TicKkGvGwcysJ918Rr9xZ9XX1ToRmENB/UsopBIoK0SlnRkjZlT1LjazJsNDQAiPthOuduSxEMEsLbj4mPDT8hUJ7AATKm7F55dCSPCE/BZZHNQSbsoSQz2xYiEeg3X/8+rytsJCdQvYL3lAYDldotwlHIQid+6Rz4e2fi7tCYv8V+FAYSFlCyHu4IBQ+iApRHU4fTHh4HxfeJXYgxOGFFHsmGUN4GH2EPQrxMhA6EV4ndiO8fKE6Nb9beJE4vHCr0oUQP/f5J3+5MG0RhY77EIaJ/0u8TRKkRbORAAAAAElFTkSuQmCC",
                         33169, [1196.25455, 1004.75169, 836.84652, 719.21492], [0.54398, 0.56021, 0.64452, 0.73207],
                         35231736)
            elif (record == "SRR446487"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR446487", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCZmZnmW5lJAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAB90lEQVRoge2XQZaDIAyGXTA5FwuvMPtsJvc/wiCvChGoSNIWrH9f+2w1yf+RlNZpunXr1q036Of3hP7OXNyBzi8H6a+wtow1szV2mtvCCbZD1DGkLmvc0xoz2ZZootBEVHKkLrM8rHtpEFBABNTzpKsFzjeyIdYTIvpjQkVTmvJsrVPqCR9ddIR9Qs7z0sXGnYYREvZJKBIxwnjbuYpuwvcKX5AzIXxFkXo3+imhG0JAuDihN3F5Qrg6IWkSYpSXE8qK+G9T5aX8LSlUZ/kwTssIsWChSlDvcXch7apLVUNIDfca9V3YT6QyIRwSgv+bej6v3xHXuGcJ9kvBnMh1TNi2osDCXJWSYUjGeXVytmQ2e2hPiZBgq0fo5mkre1AfmE0oGy4TajTR7XfPCJfjQIhEEMoerTBvBJQNQ3KGuBeRklnMECZafeXMolsz3JA+TwhHhBScpoSY5PPZqEiYbXuGPZTKBSgT5rSF7uvHtr6UMGHB7J2oImGc5s2E/kSBe2zC8B4nPCQUbzVCwsfRmm31W0mYpMwR4qcJ3S9DsPcKQmkTpYQYu+AMWoQoAgQpYf4DVUIZ4hCEokFlNfslFLRxFMJ2xGEIWyd1rTICYQNiVOKKhDx4CEI8BQi54M4JzzUxuzy9E+JN+CTBGIRVY1pwPAhhtov/7WjKWrq1OmUAAAAASUVORK5CYII=",
                         31513, [1144.17176, 961.00659, 800.41171, 687.90158], [0.56396, 0.57343, 0.66045, 0.72404],
                         34996434)
            elif (record == "SRR493101"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR493101", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACP0lEQVRoge3ZS5qDIAwAYBZOzsXCK3TW2Uzuf4TRKpCAtiAvPz/SLqrVhB/w1So1YsSIEQ3i55Ubf6/f7ByVolAfkYJCmYqEVrOa56Ip7yWc9KS0LpuTlteNQi/vWRdNSXQz4aTWd8FYhFg0YV7o9fUcYVh4mqdZT7polY5CaFN4CCtGO2Gvk2lDYZtKQTQUdhrENkLoKGwzd4awZgxhmdiETUqFpZuUHcK6pUunJPc0b3M/QMiyEBgi2rXUT1jqDCeEhJvxSULgwoVC+yf7dVdhibpMyC59TxLSbYXQRdjy5iZHyJ9KXJYds68l8zVbK/qjekDG7SITwkchkBRCy/mac3jkCLMGMen/gTyhLcWEVF+Y1OBdmLLLO1CJS+m5EFUFYcremzC54NpwfpKyQoQDIXlCOW/e9/5uMWKEjpp7SugmNMOJ7zz8Ceer8PBEdTotjDCRaITu9B8rBMWFq+yK0DWXteCkqReFtFtcmq1dR0J3GC5LJA7UVSaGN+Zhh00ehMOJv20GZmNTO00ImwU9oZyP+7AJodjgktDVtZ3M28ISoSeMv8yYgY8RohCC3ABIDvoVIdqywWaB0OuEzzXE0F8XyuWLQigt5E22K6KELKKF/tQyLPsxmAZnQnvUpgiXyYrfhIfAQIguN/KmiJ/KAENhONGd0Ove6J/dvLYiu3CEwrMI+srrvXdbYBMDnyusP8A0/EQYxjUhVRQaAnqb+8uxwshpGuxWTugZpLeEECN8cLxrqhD9XG2Eh8h/T4TbPdChAhwAAAAASUVORK5CYII=",
                         1464, [242.238, 203.45924, 169.45894, 145.63889], [0.45959, 0.44097, 0.50498, 0.46235],
                         7679343)
            elif (record == "SRR493097"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR493097", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACfklEQVRoge3YTXqEIAwGYBc253LhFdp1Ns39j9BRFEP4ETSCPjWbqiN8eR1HrV331ltvvVWhvr4fXD+/6c9bH9zzBehvG7qxG8fqrVxUAWE/9N0wKGaQ4lzlFRB+dH03DnoZtxNOJ+iEVCvyMyoWBQ7wfJbqCeGGws+Vph/UIm4oVI/AyzOS8RUi5gy4PCgWXyHCCBtdUl+hSsSUAY2E8B+EeHUGzRk1jmWo9IX+dDTV+musXhWE0FZI6kLPYYSgKCyaSF3oX0+MkJ4oDA5MCQ8niWor9L+qPWF5fjVhMKhcWHzylt1Yz/w8+EBkE3oNJYXlDwJthHb5bkI4IeQDbSg4ELQZKWFwc6LsiNB7Qn/nM0Jky2xCttlm6AqXIdnC0gQzNX8a2padQ2a+Wdoq3EJpPrUXot28NPRAIbn3mU1ozkaEZcVu4kK3MSncfdkBNYSUFn6eQu1uvlD8oyiFu2AmzLiEnBOyH5wQ0rqCQgjyfjINdRqQYE9BTYWwJzR/kU8lGiDxDZ8ULnm4u6NTMyhXaDdNa1AqpFxhjLDmxj5PjOKtxYXkCuXA9QWAM7mIEr2x0w74lWCv1xIgO+9kH+4HntA7NGeF7CbVThgCsry0EPKFEQI/qPlv3b3vQlEIh4TxL4llYrYQHOF0200IkYK1doZ8/7BQtO4KKbbb+jzgCPGIECgtjFUn9mBzsz4E34ZvwnmRqflQFD0cEprDeFQIYl3ePMAXkhQSX7hAaOIUhGzD3Biyz4FkNhdix2cQQp7g7ZIjNBGgK/w8xpEjZE/aASFFhRu+UJhoWUdoDVJoXixLYbj9eZPYI1MoR1UVRtZjwlhwspIjHyAMEP8Awg1CHEsF7JUAAAAASUVORK5CYII=",
                         5960, [236.83088, 198.91772, 165.67636, 142.38801], [0.48299, 0.46614, 0.53065, 0.46495],
                         31976667)
            elif (record == "SRR493098"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR493098", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACmElEQVRoge3ZS5rbIAwAYC9SnSuLXKFda1Pd/wgtTgC98BPhr6m1mEkAI/0DfiQzTXfccccdA+LHz384fv1e7r/6j3s+AG3b8/F6vl7DSwkKR/h4/kVOj+GlBIW7hon3HF1JVBDatv9B+EWb1BM+XjFC6D/llvDWMCrVsEwyLY5LNSyTTDsu7xcL8ZMK41M5cQu75Pj8wvhUNmCAEGi+U8BlwvC8sxC/W5h4NCCTn/0WdsnxFl5yQwwQmsfPRKPLhAF7xzhuYWxECPWE+4S9P2P1EpbinRPbCBcR6muV0+AIoV4qI1xcSy08u7U7CUEI1Yz7hOro0ydvNyGWV2wRMbcAF6plUftwg9BDo9Nm6jkRDSGVFikU5aj8stP7ZOBu3JYiSIi8lQkxD0F2rBaK994TySXCWoddLC1UOXW9W4SmqX1BihJifj1tEMp6ZT3edcIrebiQWClCSJ8R3qG5Ijmxra/ukXrkshAbnStB7CKYJ0EtRCFMd42JZM75NS91i/A9vgq9zVx6jgrBlDkdEaZevgLrQmCXLDbMKuY/QN47e3cq7hAyYLovqkfUuV4QYi1UtXNh7nOFVIWwV0gkc5dUmBeslGeEaIW8Prlm3h5rCA0BpBB1/4oQfGHdjk0hHwBY9jATslpWhe7l2QidWdaAeSnWhSiEJAdAXtGW0KutNhW/K6QuwnQYRghpYvOtCcEZ5Qm9/3e7AcQPS1MvCFuhZ+Jz18eA3JdFuWYmzF/kOR9LkWc4LITyo6eQn19pvxSRODU/MiwEJSRT637he5fVk+e4ENnc5dJnhezskIX4FyQ5wnugdcNUix2E5WGd1yvfyS23RagCNt4VnUOt6ahQ1rtLqKpvlLlmhPJMclYoBWTIYUKH+AfYfQHUnjh/WQAAAABJRU5ErkJggg==",
                         2647, [250.84385, 210.68741, 175.47921, 150.81292], [0.48128, 0.47837, 0.54465, 0.52681],
                         13408363)
            elif (record == "SRR764885"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR764885", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACN0lEQVRoge3ZQZaDIAwAUBZOzuXCK8yeVe5/hKlVkUCAwASlfWalU0jysVjbMeaJJ5544oL4+a0KrBt+c7QsCKL2EivHNJvFmNlMrQmGF87TdDBbAnB44Zs4N19D/ADhNM3zsnyx8H0J2/dhIIQBucedZpmbpntCsOuuVGtslKDC14m9s5seQYTw9UK8Twjd6kbCmzaiE2ovMYwn1CWCb9pOLhICPT1dj7C2zm3CoMyNQtVyXkRCdEeqJYkJGSH0+vSIheiONEtuJuuf0PzdPiAZIfao6F829IVwrmifjckJcT+yemVgTKFiRVaI2yvbw0VtPfG+ZYUtFUv9pISIsB5AtDHzIW8vJYQrhK+vifvOB4jvrsV8VjQ0K5SlEJVJCHEX+i9LQt5e+FuCE1ZWLAUvXLdgm1A+PCGE2oqyjhjhFkc9W5dPMrIgFFeUdaQmFF+A9XsaN9ViZUVpS6Ewirp0uSGQuF8yQmCmV0dXIXD/MID3rboo3NahHRa2pCwEh0H6fjuaZ3KGFa3SQ7+uELz2jIZQ4SJKhTafxWaEfpcDC4s3D6st3J8Y7QjCtY/j+wgntGSoXAjFpU0ExCWrhGFNOBlCIcqExaVNBSlbJ2R/Tx1IuJf6j5Ar2iAEiZAtlgduE2jZJqEleYtC/x1eISSpJDpW6B4hqoTcRs4JMRytLAQ/q3t4tzRtq5CaUkI3Pk75JUKH6SNEIqQTG4VnYaEwPK8QCoi5ee3C8A/3CSE77xOE0UjzB/JhCeP1gbdTAAAAAElFTkSuQmCC",
                         29808, [751.78153, 631.4323, 525.91294, 451.98782], [0.51648, 0.47672, 0.54538, 0.58735],
                         50380962)
            elif (record == "SRR934391"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR934391", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACA0lEQVRoge3YQXaEIAwAUBY253LhFdp1Vrn/EYoWlYAihHQEn9nMKATzEbEdY9544403PhBf3yXxU9T79iifDiQEVJ9k3RjNZKZJmo1EQMs3Qq2KlGMYBzOO0mygOZavzQqtbjDTKMwmT0i8qZnFOy/QGSkKOBMCYjv3dFml6kJ7FqtLU4p5pxlGWS4XeiZqSVgTxIXEGhBvqkoh3CYCkRDXDt75LsMJiR4rdBIFoRvIZVW9YGpyozgVriZ3/vqiSwKswprNCTRXDKgJbVmA4NLsJ8rLVN276UoIrCEOWLvB/FftOhWQNSlnQ2o+9pAQ4na5hNCy9m6BUFomaO5sVC8k3o0JQVSUotBbS9dCfk3cRwi64X4o+x8l+VCUBXiQA+HSQidCd3/SQlmhnxaS37J1gL9mYCcSwuTOGqzlv0TZAg/CqyhHiLGQ2IkjIW6twcVxf68HTSzzf4V24lkgv2Xo75hZQvKvbUcziMtr5j5hGKHQy7gWso0H3fR5kxYKNR7FSiGVCrdD7zglRFMbxcIjUJkwOt5HiIXVRDbMK+xQCMCGaVIo3mvmBzy85tOEfjxQGAz/Cu8UCvea5wuDipsWyohdCQXPYlRx68LS2xhX/Ar7EkKY3YOwiNinsORXyaOKOxBithDi5C6ElLtSD4GdCHNei8e+boQZxnTJHQgxNv0C3ePBqHt16o0AAAAASUVORK5CYII=",
                         7654, [268.6861, 225.67339, 187.96086, 161.54008], [0.60206, 0.63534, 0.72975, 0.73354],
                         36196662)
            elif (record == "SRR924656"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR924656", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACK0lEQVRoge3YS3qEIAwAYBY253LhFbrPKvc/QsUHEAhWMCr6mdXoSMLPy2mN+eKLL764IH5+a4OqW14WB8eGUGOEtaPrzWBMr5KrTWFvOtOPTIUAIo002tFPxF4jFd0n3Co8dKNyGDSq3CnE/Hd9N06hyj6UhKftTNhfR++kscKlEvl7ComlWrHwktXjhOCH9FhlwNwXcd7pGrf34+EAJyTbAbJSoMJlGk4NYaGQzjnNgdyHUGhLAZ4kBEGIS92icruCckJAKi05DolHzsOE4nMZ4SmnuZ8l8kIWJcmQ0OXzI+a+DopmhWiUwwpxKSILC0oylCDE4Dne0t5IG6iEn6bjQoCwxXIx3jXr9ZrqViHFwP+XqV98ktBuaHcdFE26AecIMRXGwKAvAFKO9cx0pLmTknD9QXGdEAJDVuhrSvXt4ptv54Ts2n3iWaaRuEiIidAXdacS71uJEPLCeDxVYp03XmRDuExCnGG/cPolsSVUfiGWCaee2V0FcYISIUhv9kaE7oriBCVCESJUu1RI7Gnw3Vt7rSnUncR9wuWBtYsQrdvGhADh+61K6G+4c1dViIeFPsNRIe9UI0Kbgv0CfpUQXaqmhfUbERIhS9mOEKuF9k9uluNdQkjfqrza44VCjlaFdRuR529cWEOk9wt5NC/EUmCUvXlh8SzGwAcIyw7UBPgEYcU/ah8nLFipaduXCYW2zxDiTiBk237Cu4U7l6kEfJVQbvoQoYj8A7kP7TqUGUxKAAAAAElFTkSuQmCC",
                         9003, [288.95019, 242.69349, 202.13671, 173.7233], [0.60259, 0.62211, 0.71272, 0.73875],
                         39590367)
            elif (record == "SRR942022"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR942022", "leaf",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBkzGUogG7sAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACeUlEQVRoge3YS3aFIAwAUAY263LwttCOM2n2v4SCCoQQ/0DVY85p6+cBuQ/5WGPeeOONNxrE13fl+GXHP7UbE9HmK0R2DA3a683HdH2DhkIgOwaq3lzXd6a3Pw2Do4CwdnN9byzxU7sZFkm3UX3hx+L6rmUfciEmQpQfLRPuKTWHhQdmCv5gko14p9KYPDfTlBQ2GJMHoqSwwZjcHXRMyFHxBC4otHPG/qEDlAnJ38BSmZUK+7ypwtixmN8kRYhjbdcT2pSSpED8VWfHTAhRuJko6wX9qz4dJHLyrUD4tSJ0qPA17RBme71k0SkYlC5nxicYcNr8X0u4sei+mBGOz90kBNmRsRDkwmTLiknSgAb9uAYSczjV6USaFdrNmHPhNMzyUmOea8KkICCgrwqkJxQt6xyFfP3GeN2egBciKwS5kBaFvuOs0FY6dt6cEIu9jDFJOjPG624lIX/kU14XYiJEtoZMwumaIqRBiKZEgC70yfi0idJPEEmhvx+Fdpfkh9h4nbgQFoUoXlWqCX3HsAhpbBBSHGvDbiAIh8dhUQhUVzjUj/GyFEImDL3MhMhFbkpOzkO/zgrPz6lOpwqnBLUunBOG+/NCzISUTUkhFYiVnRTyOVNkgFoXRhCuCmV9/yAcFgJF6I9XhOLCmlA5zzYaZYVAy0KqL2Q11BCOFR0W+iWkpvAkURNSerYo1C8UEur3XqEipFf4CmsL8fHCY52ITxdCksUThVOxmwjdK474T85auOoh1nR1odsdHhBSbOX6QqCdU+pYqWjzwkJWbo8QRdmrC7dPOGHT/kzhUPFNhZuI0nYv4RbizYW45lsuuF2YChoKlU78Azq2g6pRnDO+AAAAAElFTkSuQmCC",
                         8513, [601.76419, 505.43054, 420.96748, 361.79406], [0.59521, 0.60944, 0.69793, 0.75302],
                         17975524)
            elif (record == "SRR070570"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR070570", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACPElEQVRoge3ZSXaDMAwAUC9SnYtFrtC9NtX9j1AmY00EY6Yw6L02z8SR9Y2B+CWEJ5544okd4uf3xPE38f7Rk7s4ANEerMJ790I2CyI0x17Vq0ZeJTxhVYXX/pWsH9D+94Tvd7jEORwXhkusUsBWCL7wCncaog/CS8QdhNS8PMKSgLUTlsWGQlo7YWaomb2FEMMjLBvoKKEa9xGWBxz1/NlTeMxZvKOwsW0ipC8Trl0OXV0IfeYFUVjSqYRFn3eEtJ0wJS2o9gxCWigsqskT4k2E80v4FNcXEhMCFn2H+24hcCExYf4wpVeOJ6SthUTDl6YVhX4mvac5lVDubf1MMCJc/njWAykhlQllZynWmbo26GnpB5f3vRXCEVIYtjJdl/oGpMfkbSNUJVoKhgkhxpFnWVguSAVlCOvu6TsP2qo9IYqmGr65oeGIkISw9GROCTHwq6G9Nq1Qpoituh9qsUPphjWHlRCKr0hd3pSQXRqQDorS4i/TUtgsMhB19rkDS+kJ200G6rXxiSReTHkjQhI94nwM8yJTDHJ+IUHQe5fm55csIXSZsoVdT+bIF4oO0G9DuBDUuuJNtMJuzU8K41/mvWa4e1GmkFWthWabCpQ6w1Bh/9ZSYeaDA2YK+TC+kKeYELJmGmFSmCJXGJdWPD1ZwqjUQpYC+NLeRJhFZDQUU54hlAOBOTAc8oX9bOjR2BytIexp6oMo0xYLRT4jFM3UniOMy2hEN17xXKEU2AOqGZx3xcdNzeMjm+7/2xrMKkohGwYAAAAASUVORK5CYII=",
                         471, [68.0594, 57.16408, 47.61133, 40.91883], [0.44018, 0.43289, 0.49709, 0.52291], 8793425)
            elif (record == "SRR070571"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR070571", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACXklEQVRoge2ZPXrDIAyGGVKdK0Ov0F1Ldf8j9AFbRAKBgWCnafmWGqO/F2MwqXNLS0tLF+jj641F3/X+Vw/usIC2P0iY9d3u7vPick4QE5JBeL/d3P3ack5QjdC95zOEpFkjfM9nmBDS35ulHYRPrjR5wGuUEQZEe5Y+p+kBG7UI52l6wEZR0jyLEOYPWaOuJJTzBYqWs5UToluEI/IRQcSkomVFM5wehEPRyvqHhFiyrOhXE/rAkupPEtKzhPBOhHF77FlTh2rCSwlJNH2avjUbFqGpqwiB1DTFkX13rKYXEfI1nU+YOlmEMz6wfhUhOU3YvUZbI6IIwfFL2UvYbiwSZ1F8mOcIjTp2QopJQh7qKRqGCLMHv6f20bjQRWiUYpeXEUI3YRLZGssjn70Ombv7dG45WIQ0QBitPRy9iBDYU7qRRUjjhOFqAiHuVq1FxKjhQqYfJRS98AiwjWIcSv9a2FuacNGVMCFvHF2ITKj+f1UmjEbmAxGZJWHwm0AIvN4tQpuQ+gitCQsZIaoITEjJKZBbZUKRXlXRIBSE8ixxRAj8WihAdaSsE4L0w2bCZJwP8bZjQ/5t20RIeiclMKZBgdDXHE1DZqQaYaZWQtoJOXoLIUkLkQhkr/gQenQpQvFLV2ijd20nbHsRIcTd7ElP7xohyptbIExuNBLqNs/FRdhBKO2ZNc1ZIgRpALzCxRsthHkbOgjRHQuEvbUW9BCKSOEGgmV8RCgiHBK2PESw/FCHNZM0ENL5hDhImDDZSVw6KXNCVceZhDYoUFyaLUJQrUqSImFSx2mEMopzP9i/ek6QqJLMAAAAAElFTkSuQmCC",
                         521, [77.06114, 64.72478, 53.90855, 46.33088], [0.48604, 0.46155, 0.53279, 0.52464], 8590680)
            elif (record == "SRR1001909"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1001909", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACa0lEQVRoge3YS3asIBQFUBvmjouGU0j/dt6Z/xCefOvyUUGxQrnqrJVKVAS3IJKapm+++eabN+Tnt0P+9ajkhvS7TdyvqstR06I/OgcT9a7ybGY1T2pWvasdSKi7TynVu9ZVyL3rPBs1zdOy9K0TMELuW+vZKNOLfeu0wkF6cV7mRT1aeEuMUH88Ns8UCg49TIjol85Thcx+j8GtP+DyGVtpLP6G2GWLF748aBCaOmy5Aedea3OORIhKoanDlCN6jYJRYgUXhew7j6h1VN8fO5W4CeW6sPm5vT3rJenxFYRh6gzC48mUBhWy+dRCtAtZbqx1EFvZSEI36SEVwk0c+8LIEQuHeYHWC0uXnAoxoDDMnm7tErb0IRwK5c5EuPtKpMMbsHd2U/aFvC+MHzc0CI+7uNsY2BayeUXUC5EI9clbrXKFkI9KVCYSQgjdBYvky5RcCCFcz06+wgqb+0JTRy8hSWHoKJSTtYkjoXOQb8y3yv5EKoxlO5LKD357zgrdIk9eRi4MR8mX5mAwf9JUuG2EMYThVVIlNKudREiyL0UQhNmhdwj9QDsp9GNT/wUvTR5WW0zcj2tBixBBSKYgSaFHxUIvyoWAf78ko9Ee+zMhgpCvC2lbyL2E3CikXOgv40CILSHuFBKjTcgFob++yFQQcibEG4SvNuuEEEI0Cf3iIRJGbcZCUXgQIY0pFNVUCiGEfpDZHbFpECFdFJZ3bAnL27tCfeCSUrY5qJCuLd0+QIhzQzWs9IcXUn60Kq6hDxCKU1ribgxFFQwstP8PNwvTWzS8sLorky8mPkJoZ5y6XqTC2Z8gLBXT+Q/eVTsSlW1QEgAAAABJRU5ErkJggg==",
                         1774, [275.94071, 231.76664, 193.03586, 165.90171], [0.52487, 0.55807, 0.64239, 0.70444],
                         8168891)
            elif (record == "SRR1001910"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1001910", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACSklEQVRoge3YS3KGIAwAYBc252LhFbrPKvc/QlFESYzKy7+Umul01OH18RL/YXjjjTfe+EB8fZcGFZfwWFTqI6pUTqUwwzRMU9UiiaBqeWUxmnEwpm6ZRE2NohlHM5nc3OpgOSG2wjTzEI65udX5SAuxmYE09s8UCBWiF2J+qyrGaPcZuxhzs6tLri1hYVwKW5mmRXEuBOpjEFVGT0KdsQk7mKb/TehfHLlCvE3x6bAvQyb0oF2YRixYt5Cf9SqIuIIQt+cDJQshf2uCZ1YEHYRrC+eHECeE4GTbkhCX/1JIOcLgfK4Lo1peW7hOeiHc1iQFwrtRAboV3pQQ1h2TNCpShDddK4TzjTjK60KZyNVU7YjxkNClxhJhLaIQujYiF9K5MNjZ2fpxk9oLXSrbU1qjZbHrgnhWSCfCQ51yYoY7lX3f4JrjXIgXwkr7TbBl1hD67dRdExfyApaXC9kNuHXh9sylcPdwEMLh3GsPUephqaZwrlgX+ksOVIVsYp4L2ScY+PSnQtK/5VKDnhXuOexoseP7Mmv3YjWhHPGsgFshEI+gStCFFCfkvacJ1Q5NDboRohzCoDHgLqOFKISoFfqIkC6EpAh9pVIIkUJ/r3abFBZvNc6QJgw+G3HwR5cIIf2WkJKFmCvEzwtZG6KFtDeZCfkHiCLU758UshZVEDLDXxGqsWcOj6J9CvEfCMWD6sKyN2L3QtGGHGF4bm5PKOvMEqoPqgrzl2JQRYdC4KU0LkwmBj+c9SmUvK6Ec+EK8CB0v1W2I7xi/gDd74ZJRkzSWwAAAABJRU5ErkJggg==",
                         3035, [472.08572, 396.5117, 330.25019, 283.82846], [0.52508, 0.57503, 0.65759, 0.71778],
                         8168891)
            elif (record == "SRR1019221"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1019221", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAABwElEQVRoge2ZQZKDMAwEfWD1Lg58Ye866f9PWCgDsbAgMcyCAp5KpSoh9kzLCVYghKqqqqoT9PNbJCn7+MXaUxARdInRakMzPu2RiCZkQCKwmjZ0oWn6p13ShORyQdseb3jsG60JxSlh10IIickpYQCtYSRkVC6Ymi6eabp213BFKC4JD+qBhB5/iId0e0JKCeWGhCSV8Nt1f0J5JCFfGQiupxBGRK6EX6mUUJwQYv0VobggBAfwQ0ivSNAAjggnW2wAckmITOCUENhWiVNCXAST8JzGdOHSb1VpJpzNKuFQUob5WNZ5kiQTzHqDUOL9DPqvFTUII9gZhLNPQJ/ZUmsryewM83xHGBs5lJu2tpIwTc0xzMYklKAJGWWXaPntHwklaf/JHFioNUKJLyg9DLNja8+zCBGlXSXUOm6U2rG6hLlIMolBd/ouIjQmtQmPO68Qcm4HUQGh6MuABy0zwtwOoyJCjLNjQqqEJZbvCfmoUWo3bgh2ElRtp830U8ICo/lfkCG1POYhQG1JDSwjXNuCh2YrwtF2Pc4npFJCIxq95punG2dfaT7FmmbbeRtpg1BP8ymhfmODMAu5h5Azoj/efZinkpT6dQAAAABJRU5ErkJggg==",
                         7146, [183.57475, 154.18712, 128.42074, 110.36924], [0.36243, 0.31209, 0.35854, 0.4316],
                         49462416)
            elif (record == "SRR345561"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR345561", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAABiElEQVRoge2ZS3KDMAyGtaA6F4teoVn/m+r+RyglPKTYgDMTE+Tom8lkYvPQZ8mGAFEQBMEJfP1kuP3mWv2xrc04bYRfTdfTN1F/tJljw77rxs8BghNiqcSg17jhkMJjQ3Zs2HdUUKXi2LBspfFsWEbzhiwi746hLmHonzD0z2cY4t1BVEXC0D1h6J9/w7YX0zD0Txj6Z9ewBXXeN8SJoVTiboiN3hYM5bMNeapf19NxzxDzDPWcStkxZGnIMFuGytBxmYZhGF4etoZsTKTAEPView1iDYdvLH1cYnj5VdYa2geLxhCZnWm9JbgsYg3tlVG2DZefy9jY/svAqyHo8W8Gb6or4TX7dV+WDwefDs9P7mcMze1NktxlMcJazKa+6z2yU4P95LRYBRPDtHzvHZy06xiwRJAOdWYAOB/tQ6vIfFKMZ0wOU+I3Bqpcs4Zi2kE6tXMMemLa4U5yrNOup3GSJZUGns6Islq1hoxDQxD0DnoDVh26gWFSnwjOhtOAIfcqTHKAcvwBsPNdUqeCWLEAAAAASUVORK5CYII=",
                         1890, [134.62268, 113.07156, 94.17605, 80.93816], [0.28963, 0.29278, 0.34082, 0.03003],
                         17838931)
            elif (record == "SRR345562"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR345562", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACiElEQVRoge2YSaKkIAyGWfhyLhde4fU6m879j9AoMoVRBMuy/TclkcR8EgZLiFevXr26QD+/X6s/f0s9Pv1yzwowZp3FJJbl4lQGKUo4zWKRlM9QYgwnOYbztZmMElHMOk/LWqj1gk7pDFCCUOLNjyHE0DgtklBOxnp9G+Fx/QeE0WK/hToRxqfzLfQSVofpEWWIHk8IQwjvtLLSKULjCozwRoinCO2Z1i8FuFPNvoRZZQjbg/bWOUKyV08npAcSSjc4Q9j21AbJ1NpWhZWQnk1ILohPWFMYWOzRSWcI6QQhXDZTN8L4v1ElR0ZI7j0qDdFVWyao1BreJ3iEEBIWAFpL56hoNGESQ/ePHWB7HmplIo2EpLQ7hoR7Mxk5R9hxisJpQtKBUoRsEM2MN4SRR3clpBGEECXcWADB+FururKxj6eTUgdCtIFY2L2btaJwzgJpQui4kcBOiMWVL1SE0OTlETpWkSU09dC+kaDfJNSEDbs+5AgpSrhdUpLQq/iD2ZhHsKanrUbql2n7bmxT5+oTOkdXrCbkiJXIWcItaP3ZxicEZzhFidB47IFsQCc0T7UyKe7mCz9EqPwsoXV2Ug0TQPennrB6AhwgROthx8d00BZG6CYukBOiObh7626JcEugByEEhMg9DKmZwUnC9buAD6pcJGOE4dBHCFHUyeZrs08R4vbi3Oc4lbgTMmSyHzwrDRtUxwDrbq4XyDIhC5ST7+ESor5n+gWEKmcfKCQ085MTugZ1G9U2MIjQyV4RgtvSQMaaAooY0GvuRPvnkLcRq0USqIqwslKBuWQJNWUXQlIfCz7h1jYRyoQViBlCP98BhIm2jdCBkIWNjxprxR71GcJIRyH+AWWsx8mRswIbAAAAAElFTkSuQmCC",
                         1597, [148.9104, 125.07202, 104.1711, 89.52825], [0.45165, 0.42659, 0.48668, 0.37227],
                         13627154)
            elif (record == "SRR346552"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR346552", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACY0lEQVRoge2ZS3aDMAxFM0i1LgZsoR1rUu1/CfUHjOQPyAZ67Bw0wo71pGsZQZLX67HHHnvsH+zru9l+dct+2iOctZN7A3jtukorqU7veXpPzao8WyCdE5VyKSapk81PW7hpejerEvGBygdL67CU5KG5fS45Ty+D10oIESFqnDYfkGJ3Ek6NyhQRbgPIrE6WRYSErYRua8uE06kSSkLcrvec1ktzMhEyHxzFjTeQrErpPpwN4TzrlJNIxKE4ISgIgUxrsgPv5cR2Ss8UABNCUve5KisT7pSDEVIVISt2Qki0t6nt5pLadAOhnM44hQuICAmx5Id8+yL1Za+Kvs1GDAUQw0BP6KA4YZIlMTfYwuYSMaW9+mWCExIbZFNlme4RUrx8SdoRolSIEjGEV5eR7zqxASeMQx4ShuTRK3FCkgpRIjv72mpJ3XwIELWNfNSE/ikekvaE0BXhMi9jwvYJyLRAjBwhRoR+IAodE55uqDLdHKFp26E4psHHu6omBFfbBkIZr9qEsqxVICRGyLNxx66CkPzD5N8JWT8+IiTRbP15rSPMju8jtK4Eh4SYEK49p3dCiwZCIk+YsWW1/eogJjoklBIimoKQltbRPWFQrydcD/CdhO2Pi9DGwgOrgTA/cS0hNuHZXxjCXSTfRD+F0LsKjV4J286pD7VG+UDCSP4h7IFQ9YtPUaF3QnwIhyd0X1Kxgg9GJKzqN0nG3ROS+k+UnPYQhPYFWE+Yug9ASHpCKPr2Tqi9ER/C8QlzroMQ4kNY9h2EUHVOIev4QYR5wHEI8Qhw33F8wnLGpwkl0n2EGcQ/d3rNu0n1DM8AAAAASUVORK5CYII=",
                         2860, [189.26949, 158.97021, 132.40452, 113.79304], [0.63699, 0.64364, 0.73755, 0.73804],
                         19200418)
            elif (record == "SRR394082"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR394082", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACUUlEQVRoge3YQZaDIAwAUBZOzsXCK8w+m8n9jzAqggQCIq2p45j35rW2GPIh6rwa88QTTzyhEF/fJ8fP2RNUQmcJSWcaH4M1ozFWc0ploTWDsRNTMbSFdv6zmlMqC8dh2sRx1JySUHO2qUPni9BqTqksHOwwWlUhKAv14xH+/fgPQuXHhXpwIXysjvOCCW/ZsonwLS2rvU71zisLAXtnJOw+tSuqQigL+3eCUPfutQkp19IcYRgxYTeRlO/PW7cJa5sJIfoG09GlGfKkR4t8KSbhamgSYvTNfm43NCEeWJyjIV1y02xAixGEmplwHuBrgwYhuPXI7sAhC7aX3hggHDiDF6ZzMiE54TJGFoYd9rT1JU86veAJj1eWcT3YhCQULQjdeQWh72KYF6JBiKYzCg1UFC5lC0LIhVQThi5YLu51SFHYdCnL4XMS/5DfHaJK58IAEyHBrhCj7Mt2RMJtuszhPgdKUhwUoksV10B80dxbSoRhwJJjR8j+w6FUSJskFxK+JKQg3HJDmDIMwki4RZyjXxiyQd6LJwkTwLrPoZJUCJnQ7woXsgURhFgS0qvC0IL+Dp5uUUwQiG1CZCJJyJc1F3YSa8K4gl1h/MG+MMt/mnBd0PW1KhSAWkL5ux5h/NwLFfjsVSEhE7IMwI4+JASShBQfJYV8TEhw7BcgJ/SPh5pQjKxEyfA+oduLA78Y+EdQuGyuL1xKPSJ07RSa6vJC1/93FopjasDIdkchCKc+wosI8fbCxl2UTnyElxFiAxDKJ95BWD+xXcgFisJsoDG/ycia3KuoOuUAAAAASUVORK5CYII=",
                         10003, [274.6099, 230.64887, 192.10488, 165.1016], [0.62285, 0.61986, 0.71161, 0.7009],
                         46284902)
            elif (record == "SRR504180"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR504180", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA50lEQVRoge3aMQ7DIAyFYQbX52LgCs3M5PsfoSTqgoLiJQb54V/qUnnwRyLUoSlFURRN6PMddQy/ddeDm+usE347yqmklNU5v8JM1D5ZnZNqvopVRM2X1TER+1WMajxsIaULqY2xX2Ep7aahoo01YZ2wzcLwhRJC98nZ6iVMC6H/dhHW1WvYxZcQ+Tr9C4HfU3yhhNB9IfTfPsK6ehGz9hGCvqYsDC6UDYQSQt9xCN0HL+yAGwgRiT0Q8XdbCP23nRDvruGbEI14B2IJB0/QkMhTD29I64n936RYvYW0s3nj9M6dnu/DHwdQ+f3wYVLNAAAAAElFTkSuQmCC",
                         847, [50.96933, 42.80989, 35.65588, 30.6439], [0.17724, 0.19267, 0.21817, -0.20337], 21115421)
            elif (record == "SRR346553"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR346553", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACUklEQVRoge3YTXaEIAwAYBY253LhFdp1Vrn/EYoiEJAf0TijPvK6qAzEfBiZvirVo0ePHh+In1+B+JNIckHIbRORXK6TMYxqUtMknfZGwnEY1KgG6bQ3Emqc5o3SWRuEIH3vOMb5ZxROCkS4e67wveOYH+F4okkh+bC0cO9DREChjsb0sD5kph2vIWSWp4XYINRP20yFbI31WPrg8GqTIrOcfDtiMFoS8r6c+9mkaOnsTRnzynOtoIXJfWIU8ttQETqJbgDiwsNECeFaP8bDjgK2UlUXkptmpqLLdfDYMUIovE31FGv9BHyfAbyFvNCMYq5au8JMywvzxQJEuZd3ec5zRkhWyIhrjcEMN2zAsO08AWHcIUvKeVMP9zk4IZWExIetcNOuJSHLDtkmSAphObPOCUk1CZeJ/IUE/2lB6KbrojPlAiWEBOHyxggqpmiYCU2pXhg8lbXgmhA9A9NNmxaGyy8VspsF20rNwqBeUvYL4UphdNudQvvlMH8K/u+djJBtBJeAP0iC8Vh4kBhWnBe602j9gE+AdY/ahHquu75eSJHQFtEgXM+DFiHwa7S/CQsdpVEYTPCgNmF4jR8RuqOjJsyAzgjtYZAXHvq+iCvGknALFBYmGGeFQFFgmJZfpYCiQv4mp4XYLtxU/FUhyyAljHKXhcnoQmFh85u4rfjewvazpgu78PPC1sPmmcKG/2lBvPx1wkTFtxcuf72+W+jX1QOya7vwKcL82i78tnDvUfNgIb5euO8hQmrlU4R7nmIS+CZhGvgcYZVYXvcE4Zb4Dzahlhcu5XcPAAAAAElFTkSuQmCC",
                         3812, [204.16072, 171.47758, 142.82177, 122.74598], [0.64786, 0.65676, 0.75304, 0.68362],
                         23724986)
            elif (record == "SRR504179"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR504179", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACEklEQVRoge2YSZLDIAxFWbh1Lha5Qu+10v2P0AFjLDEFBw/QxU+qXGFQ/kNYOFFqampq6gb9/H4n+nLerWpaGTpphU+XXl560e1xoFdCA6f10hCB0F66JVRaLUq/GgIMQbg05ZD4pUPp90udQohn2Dlfy8tkUTdE6J2wXZNwfE3C8eUJuz0uWjUJx9e/J4RJOLw4ISjz/m/ihAYSn7VzgRghmjc+a+cCMUIrfNbO98JcR0g4ar2BbG6oRJib1KHAenfukfeUCPv97yaWJXSGebmkmBDXdtc2TBp5fgQhxoRokweuDQc5I0V+tr1HSUIzaj021g9jFB9gNxkwQkgSkto4xa3ZdSpJEqJtfOPBDhARUkBoV6P8NQ+uAS8jnlACUKSIcE9nRs898vlNatiolpDkANgC5PXcHcsJoY2wxPApxRcq3HooW8MxRcLtVI21r91nQ208cbxQKJvTg3KE6+9IZesKmgcCe4K6fqw0FI7baxRGLV8AthL6BvPy8WDvcd05Q0DhdoZt6s5+4ImROzuZUMRjsEqaFXofszGhm4qCMDm9B0J3ZMQY4mtShOuWwMOECceXEvrniRQhiAhJj56wdptyYzcQ+ujA3O6eZYQCYTwmq5Tj2wiJVUQ+v0RoOtcKNgShqDzVhFsgVBWC5NT7CD1LYKSGsO54LUysJ5QEBwmjzwcIP21UUlhwPARhjPgH6E82ui4Aap0AAAAASUVORK5CYII=",
                         1821, [90.69615, 76.17702, 63.447, 54.52855], [0.52627, 0.55326, 0.63397, 0.52229], 25512109)
            elif (record == "SRR515073"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR515073", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACcElEQVRoge3ZO2KkMAwAUApW55oiV9heTXT/IwT8lWSbOB5DxC4qZhg+sh42GJJleeKJJ564IP78HY7P8UMvijfPDeCMMzw71teyzsplU/hal49JqQBoUqapsb7WWX1oVLgBP15zUgEZFU67Do0KJ95pjAonhhTavLG+F/+FENkvbO13v8DwnYX7FyDWdr5loPuELHTzIvAOvXmg+wQ0IDznZh4uONrDLwLB/htPae4wTmkTm8JfmB1PEUaWEG4LbeEZVYScJwkpfnMhUnOYMjmIDY39OwJSw8Mp2tEQUpdQFPTGDJobHk5Rj70LSiFkIVbLqS6aEqaxtdUEpZCy0K1AXU4em1JYlKeOZM8QcnhvjYPPMF1I1BBSFurBiqwM4pWWw1rWy2fYQkh7O9OEKU1NiExIFSHym6xAKWFx6FVCYg0HCVvGb4XiFiSmFL8+1r5dAaiFeedSSF4oGxuJbTbHQyHFtbFTc6Pgy8xlgBL6p72wDXWnuu2BpvrqWiFKIRtb5KqmzHJCCHcUiEI8FIJpIVWFWBdSXej2OVeYRlm83JRQBnQIIQkx32/AXc6gR7EX6onlJGFSHAr3J7h0qBQ6A8YxURXykmP6hZ0jLqQ5QtZqrzC2urcPQhiOyUJWZBTyqSUd3xDSFUKqxQ+EVAhjzSDSmxWKFRVhfiVJvcWFOuUvCOtRlLjIQ7qEtZQ3FObsoHbuEPLzMRwwLgS9oleofz9CO0JlMCLkaUwKaexvpuyl3Lyw2NYFFM8V9oU/JkJ4NSWIzfxLQgjPIf7N7i5CHBD6J0oUGewK+3uRVNr7CJH9s+/A903JloXVvVx8Aes0PJxxSfkgAAAAAElFTkSuQmCC",
                         1658, [405.42308, 340.52078, 283.61597, 243.7494], [0.54602, 0.58813, 0.67477, 0.7252],
                         5196385)
            elif (record == "SRR504181"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR504181", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAABkklEQVRoge2ZS3aEIBBFGZC3LgZuIRkzqv0vITaKWoCKHoUU4Q7aDwh1ActuW6lOp9MpwNd3ip/kWXEceMOWGuGn0UYNSpnTenINjdajpj6tJ9dwtNMZhgCVCOYVjDbm3JBIrOE4gaptw2HIyjSCDfNANxTPx9DWDuJVuqF8nCFqR/Em9AHK1o7jPWbDhvMpTYrNG7b8UOyG8jk0nE4Kf17mGIqeX8oytCVDehYcGsIbCp7E9g1XQbI2Km3MMHGzdUMBoBu6TTf8yxAjKm7OMPJYDW3pyJ7i3xmGb6SIGdb9F+7my7LAkOC/2EBZgBnCz2gdbuYCRIbzcuTr1s1uMhWV4ylD2jNkpRXAtvMLt0sseGJItX4rcsPs6UxM4ZlhsFaLJZ/AMFcxIZhjaLcNzDtss5TecUmDTcegAoZwn0sFl6DGdE7b0cWTCzoM7tJlNwxBvAK8L3FDWvftY4YI+tlnE+Y1Q0bU1HxCsTimXd/6oW8Yu18zLjhau8odldcMWXtgR/MhFlOs6xlR7HsdJwbpFybw2BAciOu5AAAAAElFTkSuQmCC",
                         1628, [55.54555, 46.65352, 38.8572, 33.39522], [0.32582, 0.34443, 0.39635, 0.062], 37241776)
            elif (record == "SRR527164"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR527164", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAABhklEQVRoge2YS5qEIAyEWTA5FwuvMLPOivsfYcYWHwGJjRIc2tSOh6n6aYT+NEalUqka6Ou7P/28O/HuxT0tYMasM0OzIPUEbJPIWWucZBYZFRAaa3ok9GyTyo2M3amAsM+fMCFktukw2MGJhhFRAWGfgpiQfRF7VDvCuzaHEooZNVNKiG2MmkkJq+muQxpiYy+V5AmE9xymSlhPf4WlXnFWSlhPIyFbGmV89whlrJQQhHyVsKbR/yEUOWqeQojcBGbwghKeMYfEnw8lTHdTPV/acxTkipMSHlVgns5+BcoQCqzmUwjTwoCrMSajUQXaJKOZ0JCaKuFZ+d3CMEbAeQKyFaL9FgErYZzknczH2m6kmBCnGTgTwouQ++QYEUYrkgm9QzMFQdybXqqPJyT7KBDi3MLQSQm57UOzxndPKWGVO//zCUkdUhcmY9j0vQiXOMsdsgpILqAhfRJ7Pb8yhEv3BdZnEFKmLU4AClZAfWHTSQhD09PpCSFMQwk3fXZZ5bOM/RP+AkiBt9Tgw537AAAAAElFTkSuQmCC",
                         152, [9.66041, 8.11392, 6.75799, 5.80805], [0.28058, 0.30105, 0.34733, 0.39898], 19992786)
            elif (record == "SRR527165"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR527165", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAABZ0lEQVRoge2ZTRaCMAyEu8CcqwuvoOuucv8jqCi0tcT+BgkvswLaZObrs6BojEqlUu2gy61c94q5h1D1agDDCg+XNdf2YgmEk506qsGNysEoO3UgCiG0trlYCOFzK7YK3bAcfUJ6aLr23GkkEHY2dlydK8VFCHgQRFDC9sYHIWTLoYS7iZPwP4jf+04JO4yUkEkpIdPjQgnZtBshYq614zHeIORxUkLxhJAjBKbtkfR95eB4K6aEZyF0FUnGGccX8jeEZqMTEoaNsoQvWxj/xhESnFyQGinht7E4wuhX/Zvwx+d/Jhz/LCYIx2xEJUyMz0+Y/U4QTnfUtLTtllFh+W8p4ZaxOEKMToLGy4B3wpwzPHdpMLswIkW4BihrQ0RSQiOdMNpXEYDfoeszAjKE8SjMx2t3IOuAJHTzEV1ZIiX8XBZGGFREkXGRP1v857TreLIGJq5HH9yHh2Rxlnqa0HvW/S92LsIHYP63rDWDhpMAAAAASUVORK5CYII=",
                         114, [7.2726, 6.10836, 5.08759, 4.37245], [0.28643, 0.2923, 0.33665, 0.38327], 19917758)
            elif (record == "SRR515074"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR515074", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAChklEQVRoge3YOYLrIAwAUBcencvFXGF6Vbr/ESaETYBYHLBjEqv5Hj5IPPAWL8sdd9xxxwnx8zdvUK3DKwuC9gCGrfHrQZi2rdv6u/UktTnhqsJtWfuS2pxAxJvf4xWFjz3sSorGSJFQqHV4gCT8XdU+dgR5ISdeR7ita5cQyFi4EIrC4xYiulJ0rNvSdZY+hDorF5Jqzw4JhOyP/ktXFA5I6oVoGgmKQnSHfEryiF2bfIiQMsJCrUD1XUIUOhfOBamzmKMvZCF9jhAkoSr0DcJsrVSI+lgacQtdP1u4rXt7hEJyjQUhPzP1quj7ZZsQFunBCfrV6gghZYR0pJASIuA4YZS8IgRpvXcJ4zuWLFTnDI0ShhUrQlKTiYqmQj2tZiEIQl3wPUIQhMiGY06Ipkc0uiQsXBvtsV8YF2XTMPcpUagLJXMGcadIVz9ZSM+2uhC40KdXR/GuIKh7iuAYLWQnSVWYFo2FxIXkzkD1w5Oi39VqPU4R+jQwVoh1IRWEKh12E48UkhaiFZIk1Cmlh9ZT2L+JfkaSEFkr2X/5x40l+BigO6AXQpQk3DBikRV2/0L0M/KZI6GD2QPbXT/ZXxbadOcJSRSiW2p3gG6GyN9k3VmcF/LhWBWG6zlECLGQzAtUGIGQzQ+DDhUhtAp7N5HVJFuTFcGwWDBFdaRv9iQZwJyUWWGBMVDIazYLPQjjhosLg5TmfyTgPELATxdStzDT0CQUUo4XWkBeKEerUBbtFWLyk7Q1YB7hK/tIac3LCgGSDvWAqYRph4pu0R8TphFKPcrC5ysmLzGFEJMvRDmffQBMI7TDku8nmRAHzyBMe8kB0sDPET4uvrmFWPaJuDHCkHSq8B8iZQgeysDTjwAAAABJRU5ErkJggg==",
                         1536, [431.05911, 362.05285, 301.54979, 259.16235], [0.55827, 0.57701, 0.65979, 0.70617],
                         4527721)
            elif (record == "SRR584115"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR584115", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACRUlEQVRoge3YwWKDIAwAUA4u3+Whv7Cdc8r/f8KsIAQMCAy0OHPq1CQ8QWqn1BNPPPHECfH1fW78nNnskjsK2Lf+66Veapr7NkkGEfVtME1qnqe+PaKB6gThPE3zZXNIyxptIySMnpqXKbxsDhchWSH8qRLGzrxtZwvtnAHhKkR9ODEPhyWTwrN3GpCF8AchWwnNAwhKS9tVSevAmLB6lK5K80A7rKB+ot2WIQurnkZdpiYzr7T+xA9Dqp0TkiDMm4rgPjhhVnZJRISpOwopIWYutqiQGr8iQULoOtlPsOWwZF+YudjCZ18nQti4QbAh8ZGB38iAzCvoofB4hCALl0y9Dmo5QidP6EbmDRQtaBVCphAQVWyou8fcE7bccnyhK8yF9oJFuBzTGyjPjgnf48WgIfkl/YZkvl1PEOrDiKGQCoXhgjVnISrcop2QF2TrEuxxQDcc/QnIP5AQhmOFbCGqyqDw52og3Co7IVEoZBlZQranmAsyhNWTuN4/RgReLyKUQAVCvlLNBWxZRIWoqgL0XpUvRO+CWqHdW7fTrkJTIel3/zXbLFX7WumaNBcKf3cSgi5svlHRLxsIXZ8uQlahrZDdv7gQpXZjCLfMQYQVm6l0iwQhfYoQS4Eg5UtC/A/CPfACYfEyLRAGl95OuO1Flwuxm1CMC4RU+B8t8QZ9trBwnY4oxNsLiyYxqH4/4S53DCFmAyGSex9hLPcRXi3MfhCF1EGEmUQQMkcR5hGHFmKOMJ54DyEkEgcQHhNl4EDCPfEXZTNh30pIfzAAAAAASUVORK5CYII=",
                         10034, [508.00105, 426.67751, 355.37496, 305.42156], [0.63323, 0.59719, 0.69118, 0.69066],
                         25097748)
            elif (record == "SRR584121"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR584121", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACHElEQVRoge3XS5qDIAwAYBdMzuWiV5h9NpP7H2FQKfIISihY8DOLTosE+A3YzjQ98cQTT1wQP79Dxl9Wr2/f3E8Ck1fmSS0vr+vW0iSAiPgrasGpWWnk0JEWTrNSppBDhwYS8Jdm9ZqXAs61Z8T8vhVmW4OfcjuH1XdpvhAaC5U+hcvLB08aboH6WCA7H9vVvIHMDGYJJkrzjwO2cSlozJ4PzL1f/iZO0mlYYRPjW4heW64QkHZhcRGI2lXRPqW9wXOFumrkCRHyyhj0aikkVmgOPpw9biJh8oEYRFKYlS0KR7iPDrkT6u+wIiEEtWooJFdoh3eFR3X0UDbpfFYIO+3C6tuUF7q3NH1bgcTC9XZB3MkRln/lsOEsiReuiCgLzHK9rQXeJ6b2umUd7FhYd59CICSv2QqDOd/9zoXMdyyZh1NaWHWfRkJ0m4M59fYBkZC2Y/yeCw8Y3iX8mpDMrwKBkCZKDHokLP1lFAWhO9u+OAoWY0EgFyLJhTX2KfrDOp/wSLhdBomQ+3yBEHoXYmthFI4Q/IY2wo+LSGkhcUAHdJEQy3FA9v85XsjGvkQMG/oS2k1WLuQbqgvLtilsvzJvLFwnG0WIch/E+T0L5UX0x7+j0E8fQCgm3l4YDD+CUEh8hD0KUSRkkzsXyoo4pBAFQGBzbyRM5N5HmMrtXZh/EG8vZFIHEWIeEJKp3Qszq8glDiPEQuA4QqaI/2oGQBxlS5fjAAAAAElFTkSuQmCC",
                         16304, [527.89403, 443.38592, 369.2912, 317.38167], [0.6203, 0.59775, 0.69069, 0.72034],
                         39243947)
            elif (record == "SRR584129"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR584129", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACHklEQVRoge3XS5asIAwAUAa+rIuBW3g9zij7X0LzE8NHGxURPGZgn0aTyhXEKiG++OKLLxrEv/9jxk/JRU/f3EsBqA6Yjk9STPowfgCJrFAKMQs5Ne7mjjBCSselnkMxvBAXISan5knzZOOGaofWEem/mJyTWvjoFEKFGkoHVpgS1SYzy3mu8CknAzOPzuGwQtSHGuXCuDgFubt+PMgGmsP1cmHAhYpQWUi3CE9U9NOu7g5rCfdvFgHLjNbijUI6sfDXDEBYC+jZBMT4Yn+t7t2nthWi64CP487juZjAbAwq7NyBfY7WEhi84JzQnW8mxA0hUIkQgTflhEuD6tVmNkjnZ0JdupUQtoS7n7QKKRLyDs3GD7y+wjohwI6w6usCiHfA3mx5Ia2tc1IkZKLc/3oiIWZQGPcIeWU7HG+NUEVIkEFUFIaPFy/Ips3B41lUw6gevavCHOIZYbJOqXth+vvrT6FeqH6xOqHP6E4IZH6iYDASCl3nXgj6qfH7nhliGfcJT36TpAKhOUm+GdhqsUOhmohyYRKthWfe+mC/UYE9bAppXKFLdIdtIeaAIwjz5YN/l9IZYHshHf5lHpXH7oUYX1FPGF35lDC54pQwrJX7kE94qxAPCbPJnQuPTeIn7FKIB4CQzX2RMAa+TpgAXyfcyu1dWL7VfMLhhZnUQYRYBoTN1O6FhcSRhWXrNJc4jBBfLywgwk7eCMJ0of4CPXpPhxjgC/wAAAAASUVORK5CYII=",
                         8891, [273.14454, 229.41809, 191.07978, 164.22059], [0.63755, 0.60146, 0.69405, 0.69759],
                         41360269)
            elif (record == "SRR653555"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653555", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAB/0lEQVRoge3YS3qEIAwAYBY253LhFbrPprn/ESoi8laQOIN8ZGEtYwK/jzjfCDFixIgRH4ifX46gP5Yy3MF4nogYi9XFLCa5YQ4gQu6aN2OaxSI3zEHtCOd5mtYNc1VoSLgs0zIvC3PVloQMz6HqKWiNSGBHQlBCcoaaItYFkBaiGaSOhCgp2578g/uoErbzRqwJsoQIaI92KCQthGyhSgCWlXAUiZR1hNqUL3Qe4TroQzeNL8RtVwvxPHltUSQA9Rc8UC3rpvOhFxScC6VApE+tbMPrna3TpJQu7jZK+h/q3qEQrWE1Z2xiEO5hJmu9oullymKpTx/qbYFwWwD5QtILPNLsbEdoL/M43pktsZS8B6MwwHkrmH1bqPb3BYq92eYJg6t5YjClOIHCrWoWmxSCEpqBuBDNp8fZEOf9y8zHZMO0kOzpnANAr65AuPYq3Vysj0MGuaWqA6qEUCj0G7QcAa+ncgvpTBgLs0S7XeQIkeJC7zL6c31T6A9cCGP/RyA8QjiyK4TxgUaEx1xtC+8+ibAnyyZDXQp1XbtIo8KbRJ3cvdCp0ZXQK9+28FY/HcLGhFgujFZoV3iDOIStCYufRK/6C4SFxCD9BUIs+VUSwvT2hccP8P0KS27UMPcdQsz0QTJ3CL8tzL1NY6kvEWYRAWKZbxFeE1OJrxFGiP/AE+ewKaKMVQAAAABJRU5ErkJggg==",
                         4750, [444.69292, 373.50408, 311.0874, 267.3593], [0.62151, 0.63538, 0.7303, 0.73072],
                         13572463)
            elif (record == "SRR584134"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR584134", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACLklEQVRoge3VzX6DIAwAcA4uz+XBV1jPuSzv/wgDW2iAoBC1E2cO+1lmPv6UqjF33HHHHR+Ir+894rFLlYZ+P1W3aTYE5WWiDZusmIIKcxgzjGYy06SvTS9j0qFeCIXrpiEWhOMw2L+DsrIrDvRqwhbBCostkwB8u0CJpIV24+SIo6bsHBCEFK3WC4llkgP7D8UC+SYQlc/MMAzjuEEYakctqFJIFhSGg/msvfOKBXIMLRPtSa0YRg5kQjZRgzDcOl+xSe3ZcJd5GXD7kNRZaDg/afRCYsL3Lj7HrnjWEApCZDUMpFXApaSr0dbsG7EQ/RTVQmaShLZIWoUkzXFCVjkTrnck4KY6ob+rOMe+wSVcGI26kL0uTKuE1bhUWNO+UMszxkLft1YYIUpC/6RFzBd9PNe0b9OF4N34MPsK/WdLDGui0D2YVnq2RiZMhiu80gAkw6rQ1lsX7npU427icMnX+Nxhn9EuxBWh+2FD1UN8TyEw5SyEA4XiPxXxOuwlITAhAW9IG4VFRCLE44TzZXgJeCGFMS4gxLwdByF/5h4n3HxMSS0kky5cToifEeIW3TahvHAmIbACkpAkYFdCXkAUYtrsT4TaHyLhulCMzwtRBYSrC10L7EWoOqbZDl1MGDXoQNhMjOvfwjMIW4lx8i08hRCbgCAln1zY9iVeX5jk9iHEW/ivhHLuhYQg555dWP+oyYCXE+apnQhriUJmL8I6IgiJ3QhR5+tIKBB/AWKl5F5B1mwoAAAAAElFTkSuQmCC",
                         12874, [404.38289, 339.6471, 282.8883, 243.12401], [0.61877, 0.59175, 0.68576, 0.72435],
                         40452559)
            elif (record == "SRR653556"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653556", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACGUlEQVRoge3XTZqDIAwGYBbOdy4XvcLss5nc/wgjagUxKERawcesahDw5e+hxjzxxBNPfCF+frPiL5LnWMGloRkQjqSZToxyyXi9TGdMr67PshD1CPsBabpOXZ9FCmxayF8Rr36YQ72QbUy//HRNQuvTC+EJycuzy18e/SmhJ1mBahJ2vV2ovbJ2RIgcIZR9fyWwEhJIyB81UUpIh29oYi10p+qcT+kUVGY54xObAvMi3QqZkyaRh+MJ4XvKKcUn9j04FL77WAr2O2XMQhqbw4hblnr+x6gqyjF9BB8K9xcq1m9h+hGvsmu3zSgHJ96VIJwK4At3vngrZHehxebGYM+ySFNMyRs/KTKEw0IU+kXwGi2P7kILOzrG7UvQztZ241mAZ7KFrle8vycqDBtxZyT8wogwOgK5wVHhWMK+0L0AnoeGc4SbYZu9lQrHYnCGkEQhQgmvmzob2BGOZ0VMiBLC4XFp4VNC3hWy110gHCsiSyg8by8JpYU4EArhC9eJ4sISG5FPCNn/R6kVCpCSQrg+VcIwkS+UIH4JFQCeEMqJosIzs2jvDA0IWfuPczzsmxCqZhFzX20ISSGUWqhXqCHeXgipgVsJxQYe4YXC/NO0OSHdXpg7iUHrLQjzLjab2i0Ic2YRm8pNCCldGKtcuTBjElsVUioQsbp3EQrARoSpy7RhIaUJ41WrF6bNIqSKzQhJCWxHKMziP1AmW6u9Mj1eAAAAAElFTkSuQmCC",
                         5902, [464.22027, 389.90539, 324.74787, 279.09958], [0.62397, 0.6265, 0.7223, 0.73349],
                         16154755)
            elif (record == "SRR653557"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653557", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACD0lEQVRoge3WO2KEIBAGYArzn8siV0g/Teb+R4goREBgYVQWEqfYVXGQj5cq9cQTTzzRID6+quK77vY3h6A/wIqu7uOLY1af+kcYxLwYdbBfwEwnGnVlTPOk5mmSprOO7YiCAjre/ZaYZzUpsRCOkBXILaB4SvP41HNULOSEUMspkdM8Ts1ST2iPzAnRBa27Is7sNAiFdLw+dvQkpFtqTQm5Rgj7onE2KkHc06EcCg2xUIil40F224X5E7eFhJmZQEKIMuHyqaD3X/aFmYZSZqBwx6pgfiGk/OJYGwU3S/+nhUgLt+dJhz8S5FTrC9m0lX+RsaaysrdR0C/6N/XUdIV1C78gzJaQEsITRp7LuzAceeW0M8SYB5DuIcSKXk2a8sgJlxN2hIxIt2eE+zDh8MVgi3Ecrv15XQi5TBgmUkOh/04IhJvKOw6IxcJtzpusvTgiaS08xJZGe1NLhby/59xuywjpjULYT5cqIVoLse52UuG6gO8Vnp6mcNpQLTSv9BohcVPh+nY7K/QvdCW0DzwnRJ0wdn6T0HsF9CyU7jV+/WKhnQR/WBi/cKlw+eiRCP3qOxdK1mJQfd9C0UQdTCggRit4hCMJEa2gY2EtMZHfs7BuO8UhfQAh1QhT6V0Lq0ZxUGExEZHcMYT0CP+NMJ3bu7BwIUZTBxFSCRCZ1O6FJcRsZv/C18R84gDCCPIHUStnvP+TWSgAAAAASUVORK5CYII=",
                         5005, [469.1144, 394.01604, 328.17158, 282.04204], [0.62784, 0.63746, 0.73503, 0.73051],
                         13556594)
            elif (record == "SRR653561"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653561", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACF0lEQVRoge3YQXaEIAwAUBY053LhFbrPprn/EaqCKBgxQvShz8x7UwdN4IvidIz54osvvrghfn5Vgv506uiG4nkiQsVqNdH3pje2U6/bjrAzdnzTDmpH2HfWmq7TLtuQ0Fjbdb1VLgp0hgjKvcfhplBDiAZw3p6EJMmC4UV+65oYFpnalQan9wEUhA4oEI5nBfxsXzuTFUHgJGuTF+JxMgLOB4Jozu+P4OKEB2MmlxSEVYvTVeeHYiGuWg9nEQg1hdcQgRVCEGZ7hfhEgHRxYoLCta4aME+W6yQZa/jMdOwXT0aIwgUnOUq6sknDr5mE6zVzT8gsIJARgmgq0jv8KmF0Ke4LN0OmfaFsoJAedKNw3KaVcNrGJP9AiH5vmhZlpu1TX0xGWfi+RcJlyCbcPcVCcDthR6i31uSExAjDcNxJJqFwnbm0oLv7WaHahZoV4tKe9Et+WkqF8+6cEFWAkBVyEYaM/q9YiMvDBmkdO0KdSaRyIY3/SZwSpt8ErxfCMoYyYdJwIFwGLRSiCrBCiGmDQJh+/oQVQdE3lyIh36AorLkRwYQnwUuFqyotC4uvU9oWeZcwrv9GYVy+aWEh8fXCpHzbwiIicSWaFZY8MR4mLCA+TYhnfcAWaFh4chJT3xOE54jb9AcI8fVCkv12zpV+ilB+oTLAhwhRKNzPfYkwk9u6UEbMpTYvFNyK+SHLhbHgRiFuTf/VGTK9brhO7gAAAABJRU5ErkJggg==",
                         6372, [790.52727, 663.97541, 553.01774, 475.28263], [0.61365, 0.63794, 0.73347, 0.74352],
                         10241986)
            elif (record == "SRR653562"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653562", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACF0lEQVRoge3YwXqDIAwAYA4uz9VDX2E757K8/yMMhSpgEAjUxX7msK8iYH5CaTtj7rjjjjtOiK/vEUE/v0PmGRySBaFMM2HHKo+M6WEmYx7yCcgbMW7VI3xM5mmmSTwerGV5EYs0Ca2vR0irMNyuoEhocT1C4IVzqx5il5BY4eKmzBl0dtiT5vkQnzQQCjFpViLsCwqFBOibP0cIsXCtomuufiPCG1IbFKnwVbUmIeS+NPx/QE7omyu26byzwS+Fqkri8pciSFC1VVhM2nZZh4GiUvoTpSws7FOAsNtcSy11LAhpE/Jl8Y5kIZZLqxYmhcJxbOSFS66hkH2u372cEMVfhYZ+OHUL3QhOWNzZfND2C2BI+CTqhLBLmY6FR4nmbs61P0k4X1AY0dq64peE6O/unus+WNwcSUby8nMBh8IkIHzw8mo1l4Rpvr6DdUJar3imfmCLcOtgF79NmBaRmXJ/awAQSSh8LX3QUBDi7sFnCGHLoVlIyxarF7oFAUx6HwrjVWkLNzyYRiRMG46FaOLrdwr9cOgU8g1ZISGdJfTz49lC7vpQKH4jxvN/ojCeXrNQuE+T6VULZcRLCUUbNclYuVBCvIXKhNgLVC9sLuIuY/VCbANCOl6/sLGIVxRik3CfsX5hE5HJ+ALC8v/b1wBm9BWE9VW8rLD6tOHGXkOIdUDIj9UurCOywKsIKzYq79uZ9AoZ4h/LNvAThpKa2QAAAABJRU5ErkJggg==",
                         9898, [790.13316, 663.64439, 552.74204, 475.04568], [0.61211, 0.63215, 0.72812, 0.71877],
                         15917411)
            elif (record == "SRR653563"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653563", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACQElEQVRoge2YSY6sMAyGWfB8riy4wuu1N+37H6GZMpuQOAEFxC+1mjLx8MUOhWoYPn369OkG/fvfRD+/beK0VcN9IsKG0aqkhmmYpuZh+yEc1TgoVREAWCv1Q6jUOKpJyQMQ0PbfNUIRIb9JrTQP6NzCUey/sKwXEWE+Ip0vqZFa+yj1Xkh2QgzNmYXD1QO9PGlGJfV2CCk0FxLC9nftyBYLeMLNnNUaQL0QNjzI8bpP5BGa4mSEaygA4anMSSaQR4iGkLTOy7LPpO0qe7jjUvB0TbnAIySz/eQipiomp9lA7qeB7WWC4hZCvf1gCZcmJTIXExI/jvP8iJufEOgCbbG6OIcwmTlJiHHGo9OdeShKtR4ahpAcwvWaq8lbiKb8DMI1XfCd4nm2ELphzwnN3vp12WXofcT9blSvc58O7zTR/sxkCLfsLqFdMHtpR8ginGfET2vjhYfUS3QtISUIST8KjeGEkI4II5YD8yWEiBRrL3AfPMonjF/nTwixDaFpBUPIyhRYTOhWHIdkbjUBhDpCKCPUkHb19YQkJ6TlBbuEkPucJMQGgFBHGBh6JKQaQoSLCVuMaR1haOiPEGzOdxKCk1NCyBtaEladRHg7IZgXlq4J5XPqpOibEKWEUYxuCWU/SDK71CuhbE79+L0TYi1g94SCJrJ71DEhvp6wuIlB9AcQFiJG7g8gpJKvjNj7CYQFXWScH0GYjQiM7zMIMZPw2PclhHDs2zth1piyfI8hzGA8AAyZTgkxDHYXITOpfz/XLIv0Q57PAAAAAElFTkSuQmCC",
                         5577, [803.03318, 674.47931, 561.76632, 482.80146], [0.60422, 0.62611, 0.72083, 0.74604],
                         8824547)
            elif (record == "SRR653564"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653564", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACIElEQVRoge3YTXaEIAwAYBY252LhFdp1Vrn/ETpakH8EDBR9ZtHXcSThC8jMGyHeeOONNwbE1zdH/BBLGu5g7BMRMma7EusqVrFI7rQwj1CKRUi5cKeleYSr3JSSOStMJPws4bL94Y1NSMw5TwJTb3w2qBTsu3QDDl7EZLVFLqtkP2l24dhFHFsNxgtheLmHC6lOeH1uJDo2FGMFqeKoAWAQ9twzpCaI5pLapIUl9dcfgAuT6Cc0ma38hxDPhqMwX3+qltLrxl+5Cy1KhyVEU56KiPsXH0AjLCf63ah6LKrC2h3W/IwwO+dQWGoMmtFNCI7wqGAJozXVE7ffBsQo5DaS86mQFIZF1QhvMytrwcMEQSvKNk11uFnNf+AIw75SXujf7g7VdyamwiVEN615tb9BlpDC2WSFuY2mWhDbztxC1eak0A9v+ImQtAedDQ7HcZIVouCItHAvEAjdqseqpoSohWpP6qKZrnELKSfEUEi6L3trioV6wdC7+5+F5LbaFtK28YR5MkuEsdf9hZQRxuOYIjpnbg8hZc/iUxqaA61VCL2FF1YRzBI0C2mAsP0DA8wStAvRv9BBiG0+lfeqMH6BV9i2iG7+yYVNxOcL3QyzC/HxwgYixBK8wlsJowkmFtYTbyesPU697HcQ1v14Goy+g7BmGSEYew8hFgtTYx8jTI6dXVhKhOTQ6YVlT2J05F2E50RIDKwVop9slDBC/AWMppkPVpfdrgAAAABJRU5ErkJggg==",
                         5302, [570.92735, 479.53023, 399.3954, 343.25426], [0.61205, 0.62247, 0.71652, 0.72995],
                         11800058)
            elif (record == "SRR653565"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653565", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACG0lEQVRoge3YS5KEIAwAUBdOzuXCK8yss8r9jzDgh2+MCKJomYU1zQDJA9Tq7rovvvjiiwvi5/fa+Lsy2S0rCkh1Ewz9OIxj3Rxi1Bb2Q6+vVXPIQURYc/5B7aG6lk+UvRFGCFBeBRPj5BtKpsDpWiyEWnupTulQdEhhtmUKlau6sBuLbkNaheg0AqY+Pk4TlowVYqpvEZJymXZMKxfxHCFN+WsE+cI1iS1bf5DG+0ICuftyUOJehHSFEHlhvDO2PGXyhNTJG6lzoT4rFLbTvD5nB3hCqzJ/q1ogWlxyheQLxdOtNxxBX3lhhSdVLESnGc0pNP2XnutoiIRu7ygbmi5hp2pCN5vNYQoPhDg/imBtsPWi93Erm+PbEp5sdCQbQlrus7lAnG/JXSEu/w2r3RcKy3MslreCPysjJF9Ik5CcBlkYEl3gfUIKhS5IbwscEHpG/YpNEGJ3RkhClSL0uaCDQrJP3mDZbhRyYUvEsGFHOL0gjgjPOaZ0oZDuEEKBkG/YFnKfZSGeAWxaWEwE+538nUJwJvmEDxTiI4QFT1Mwb/O2hZgPDOZoVZj9TThapWaFeeeUniTEDCAwM7QrzCG+X8hN8AlvFB4nAje+ZSHJvyzHwa5Q40J8uRAh6CIHhMPbF1L8a6QQ8QI9QHjkabM1tnVh8jFlhr5LCMzQhwgxTbg9tHlh2i4CN/AxQtwHSiWnC33BhUJmF/8BBc12W6qUvxkAAAAASUVORK5CYII=",
                         5377, [587.77982, 493.68487, 411.18464, 353.38634], [0.61652, 0.63083, 0.72573, 0.75692],
                         11623867)
            elif (record == "SRR653566"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653566", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACLUlEQVRoge3ZS3KDMAwGYBbpfy4WuUL32kT3P0IxGD/lxAaFGgbNdCY4WNbnB0nbYbjjjjvuOCB+fjXi9VJJox2K88RMitn2xGMcnsMwaqdFP8Lx8Zh+Ru20TUJojFgezqzhOGqMEcQEPFo4jVh4x6zh86kxRhAtQtBS2j4nisJ5l6qfQ+bylKaxbuj9QhLf2f+kESrDLJQHzILVhLVz2pYYjCVxCFqEVQNOe3QV7iqwZU7bE9tXSWulkL1w+yryMUJ2T+xqIXMobNhmyWTwGiTevSMQCdf8+CDEetsQ1mWtpYUEhVdJbidUP4ocC23+WJjPq7tNEGbLwJZmDqxrTM/s14T4IDQNyEe1Bw6uLHKXgtA2IKg/y8lxKq1AdN6C/Gvpc7nCqLaHJMyWAXFS9zrNqCtEktZfLaUiHDAfFR+Eq6IkNB9Q3xZSUWje4VAYbi5fTpWQDDLdGIRCSnEH6As5FbIvZ6p37oha4fw6FS5NPQn9DebRSfbGaqF0fYCQy0LmaLhYOBcbN+gLVU7iWyG9F+IMQrwX5sCLCaXwJR4gVCDyDiGlDZcTyg1dCf1vrN0Kd3xguAfFVYX+k6Bz4TYilm9bFxYuT0E6h5A2ACFk6Fe4ZRGlOepYSM1ASAlu4T8K27fp6YTUKhT79yxsXsTzCan0l2U5kHbvX9j2T5B8gk4gbDmKpc6dC+uJxb69C2ufNhC63sJOhJVEqedZhDVEiB1bhZSmOkooEP8AiTNL0iFZCZIAAAAASUVORK5CYII=",
                         4389, [544.26413, 457.1354, 380.74299, 327.22373], [0.60963, 0.61891, 0.71156, 0.74151],
                         10246632)
            elif (record == "SRR653568"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653568", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACD0lEQVRoge2XSZLDIAxFvXDrXCx8he61Vrr/ETpOGBwQILAVm5R/qlIVQNJ/THam6datW7c+oJ/fT+vvc6VOmlPSTW+mZf06U4Sa2WczT2Y2miWqehGCVnozz8YYrewSkSXU2qxmMmZZlJJLBPqEK6RScokCoQ7ivCjdNIDCgRQIpSGXkNzuoIQNdgclJKldgC1h/xNDfCj69W5utS2quQJ6QuonVFt/wscnLRF81/RO2H+b7omt5HWpU0JJSYoIsTy86KMvVJLZEhLfXomPCIsxmH21ox2zUxRkCKFMGGymhAXEx2WSe+8h6ZS2KiL091nFbOiwznATlLf5GOeGxn+4lAgpIkQ/w2Wz4fUMOELM1vM5IU5dC20WbtN6wlDC90QlwfVO1mcLYSiWTp53ctAy2t2YJQzWnw3OMtrACmEyLe9JkXusuFA4aBnzhJFX58daRGogdIc6mTYsECYd+oQUtlQroR90AiGVCWlLGOzAq5/EhM9xxGz9IuEhiAVCignDANcKDYTs7wrhAUeR9hEyDUMRUlTuDMJdGxVgPeglwsjJCYT7jiJsavKEnMYgRPJP28sTYg8gvCK3Ga5L2LOIQEMRYjshl+CrCIFLcBOeSNh+ENkpujIhfj1h6yJG2UcgxF2AIxA2LWICOARhC2MaexNegxC/nlC8iEzoIIRCRC5yFEIBYjFyAEJMkf4BEHCaEOGdfmAAAAAASUVORK5CYII=",
                         1959, [274.83065, 230.83428, 192.25931, 165.23432], [0.61125, 0.61037, 0.70359, 0.72373],
                         9057212)
            elif (record == "SRR653567"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653567", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACEUlEQVRoge3WS3KEIBAGYBbmP5eLuUL2vUnf/wjRAZSXKNhaYNmZpMKUNHw8VeqNN95444b4+ZUI/hNJIx1yw0RMcsnOxTCqj1KjdFpmlk5ZG+MwTL+jcFY0JFTD9CM+h7OQhHNWxzh/RuGkLQnnKZQXckPCz2c6aYaPbFJuSXhJPF4ILaRbG7318NbCmyfxqvZIJfIa4e6gQrInV93Aa15nCPeEVsampKviHPgKIcyRwkELvAg32jSDAb1VYd5hcaqLwm9R9P3LdrJ0adl5zHmhrWE6Zevh1E6C6M6HzsTEgdD5L7NOPSFIQgjhC8oKeVeYbNIV8jr2s7B2K7IRSp1d20KaFyb7RPP0WntbOM/pwS74xZ1VUxzRfltKRJEQYau+cJ1qbc0vNTLjhSDnfULdR1cIhH3OCjkSkluRvtkQjRr7qc4GssIgELW61NgQ+p13Zss+kLgZhIXxrZARxn0+KpwGkl1hJmVbQuwKaX0Q64sE2IsLhcv9VSqEPiacL7JCXaSgfIMQ9ULWn2uFp09TOH0oFvJy0h4Wpso7QjrB07db68LaSTSr022zRpj+QlZIdUCT97lCW7kLYdX7t5++bWHVTgzSty6kxwsrJjE5Rg0Ly4ndCenxwtJJTI9Q00Iq8WGjetNCLrkUtwaobWEJsVNhwULtVXj4tElUfZYQiaqdCA8auxZSna8jYfSgUv8dB6cqefgeoAAAAABJRU5ErkJggg==",
                         2360, [278.9284, 234.27604, 195.12591, 167.69797], [0.61658, 0.62739, 0.72185, 0.73311],
                         10750893)
            elif (record == "SRR653569"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653569", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACPUlEQVRoge3YTZqDIAwGYBfOdy4WvcLss8r9jzBaUQGJJkCn6mPmmUUtJHkL2J+ue+KJJ574h/j5bRLcJk3jaPg6MZN6LBrW3Ubv+pfrXOu0sAi5dfUoXD/+u9Zp2STUD5VDztEPf841KBGFWggCpqGo26xyOTcIX6/ixMhusWGTDqGaT/OGzmdShzh73KRd+TkkZt9ZtGZaITUTQiw3LJ+rEPIq5PiyTsjv14J8j1Taxp6wMlZJWAFa4TRuFZYfRdOtzZh4FS79IWj8eHogLF0HdNpzbw0OhQyKLg+NHyCRCIvXgfW3NksgFS79zY3DLizbp6w9FtognxZ54dz4tIxiYQSjOsPWfg+OH7JlriY9hWkDobcEwr3CeaFuIb4mnJ5IhZumkQyj8OFe5YWQjJIKlUat0L+DCkLqpGB/5xrqC8JWRFn47gBHQi4Rjh9+MD473qHTlHGm+vB5JOF8A0qEy3vJgTBtfhb6Z98f80Rhm0VEpRAHwnkch4PTrf9RIe8IOSoXC9kjWSXE9BGHhcMtCakBELtC3hOyTchfEWJNkxdS0kogZLOQzyjMRSSERZh7vCusP4hBzUJhdKG9sHoV64Tsv/J+Ush1v92hUpi/0FZYt1PDmo/we0Iq5tGdhf677DWEJcRcglsJkUtwYqH9XnM5IT3CNLLzzyw0b9PrCckGRHb6qYW2RRReoHMLLcTt5EsI9URs515DSFqhOPcuQohz7yKU555dqD2IFxZqiMjPtAopzfVPwhzxD94XO5vrt+nlAAAAAElFTkSuQmCC",
                         3086, [273.88696, 230.04166, 191.59914, 164.66695], [0.60763, 0.61269, 0.70679, 0.73274],
                         14316928)
            elif (record == "SRR653570"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653570", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAABvElEQVRoge3YS5KDIBAGYBdOn8vFXGH2vUnf/wgjBOWpyEOhKf+pMhGR6m9AUsk0vXnz5s0D+flLyiete+Pk/ENo/fu+dpp5mWZxyA5B58JlnpZlPeQGiDoXTosQ/ubeDVqItSqqHTGHc+4cCl/vQrlKp1whGcJel2nBTgM8hAUhtUg3IbYtp2pQHgmHFQLKF0KyhAOt00PhMES1HonOhKwX7RUh68cSjoW4dVkXMPJds1eEvJ9KiguJtRDiQuAtpMGFBGdC+wq2KbEs4Dt8IexXGCKHFoL4oSImFO+Bp1DVGxWSelT3U0RsV3VKlCywnzhCtIW6g/rO1WtU0RgXhqKGaFX8pWwTVCZUX7u6jF0x2m2BHmGht/GoKw8hzgJVhM7WCusDiyB+CpHNbZ11hUbDd1eSzdCU6FSMdmOoS1go77Qa9HjQ9NOzmlB94pgNpvB8u8Ubt6qKwlAD6lM4nkjj1ruBdwr30YHsjda5XDVmaY8KRUfn/IBYyG4pDJ3rEbTQb0qJX3GfwnwiG6HYp3FsodG9DNi30LsYizMyC2HaPIYqHkkI7r08hIEuIwrxgu+o4meF3xvShWHkP7MmJOqDQUxQAAAAAElFTkSuQmCC",
                         2267, [298.29049, 250.53855, 208.67077, 179.3389], [0.52187, 0.56047, 0.64469, 0.57863],
                         9656892)
            elif (record == "SRR653571"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653571", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACEklEQVRoge2ZS5KEIAyGWTg5lwuvMPtsJvc/wvDQlkdQiLQNM/5dpaUhIR+JWFYr9ejRo0c36Ou7Sj91wz8syYJQ6xVurWlWizkIBdQ94TxN5iB114TQMp13aNKI8yL1Ji1smM07NE+zraNIYAhdn0bdit2UdtK/WUkJKUvYT2mX5cpO4xNiZEBm/HACnzAooiHsfpctUJYQ/gVh/2/KU8H6GG6EuJvcfWTdBtJawRfhTgTDE6I9UitCcAPBv/is1iTyhKHlOJbaXjSgT7bxW6crUI7whUhliKRIYwHthHoD7ptwS24nRNZ/7UfL4xEGPrXd2nRh1hwYQmeAM0LyhiFlCLmU2ZtbMAFJThWE7LRE0TAMLrcgGPth/imF/HpKVEeYTAuFhDHMSoEq/WxZfTGZS6gTQvIJMS1kMWHq58xprx62jACwhnAfoLcOt3tQMWGY8GbWFojKGE0lFpwSWkuekC4QAm72lP1s8y6WcScz9QGhXWKe0KRmPv6rCF+z7YRMrdoQurm8MBwhrz1ltJzFhN56RguXI7zSpuASvEbI38gTIt1I6EW5j5C7PiYU92n4CviDhGH8rgmFiMTEeAiHIozC900o2k7HIpQgRhEewk8TCh7Fh7A3wuo+5Zfo7xCmGfdPiNcAByCsgYSsc+eExZ06LmFpFfOu3ROWlZF1HIawABEOHO8iJPufhIww7dRf8LyVFRouYDAAAAAASUVORK5CYII=",
                         2703, [317.84559, 266.96316, 222.35065, 191.09586], [0.60955, 0.63045, 0.72437, 0.72495],
                         10805755)
            elif (record == "SRR653572"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653572", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAB+UlEQVRoge3YTXaDIBAHcBd0zsXCK3Q/m879j1CJfI6ggijQ+m9fEmPgzU8G816m6c2bN28eyNd3Vn7yPt44JReEal/h2hFSzHKSxeOhe6EUQjGLxxMRVivmnggxT1KWjiaVitXcEbn8z3PhYHJC5kTAK1VVjFj+ivch+EL0z3TUvMvyzVOpkFJC6Eh4JRAIiZ3BJjVVjQFGhPQ3hMSEyE61qapO8PPIhY60ri42qKxS9BfBRoj2AzT4IqaElkj/RTguMSnUJHuTHXYr6sJPCEclpoXriXGFujvhQEiecKyt6GTm+ZQQG5RaElK9h+oV7Ag/Z4gFmxScHUK7RLvC5dyhENiTeQG3Cg4C1gK7QnXEhZu9qN/RP/HAxHqjTexygFuVhNDfhVEhOSEh2N7wZm4RI4RjYST+TJ8Z1lf2eqA9xOdIYcy6oFlKlSIhUCh084F/8HggrHgtIl8Iust3hW2+QmsI1bYztyE2KQaH6+wP31hZxYXC5BtR4bPt2kRIeQ17rbtbCdWtzdSg3k7+zOzGjSYMjhH0NzLwXWqnLWX6xTUUrkfeDLEVqAJsKoxCNrVdBHYtLCEOJizo023FfQvxOrBzYTZxPGFmn7KZhxDmreKQwixirOL+hTmNOqiQzq4j7IztXXiOuDf0vDAUZAshcqXPlBnt1V9CK79M6znu2wAAAABJRU5ErkJggg==",
                         2170, [311.5808, 261.70127, 217.96808, 187.32933], [0.55968, 0.59637, 0.68549, 0.62373],
                         8849410)
            elif (record == "SRR653573"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653573", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACJUlEQVRoge3YS3qEIAwAYBY252IxV+g+m+b+R6iiII+IChkbp6b95oEG+eVla8wTTzzxxAXx9S0RPyK1iIfgfSISrKwrBmte04t0EKF4nW1hh8FYO0hXS3qExk6/VrpWTcJh/DHSfQiKhOMAtUZ8lGoSDnZ42Z6VBpmyCaiH2BcEZOZ9Id4dZqGa/aIrRgcswgj0QUJYJTGI/ovwE4gUCzErPixUeCfQf0iEoaEQhFikpkEICMtEBvFmtgegexublwp9Lwbh7o4xrlPoz7qtEEqlt6B7uAtCRYPVC5PpFk28RMj043IeEISzzF2EOB2hWAjMghOElAqxp1FdyXksTWGE7kgsdJ/zi28J3XvjdATJvQn2hEXMeZg1phS6WdnWKGaotAdVhGQ2hePYnoc3VYRMjx9r0noj+wOqQre28EI6Jqw2FH0j0mJJ4bp/bQi5CCBczgwFnBD9lcqrrwffJ4za0CZ0a88BITDj1Z3i1oFMEzKLlNMBfUKKn9V3hTxjqYg7JPFXd68Q84Kq0D0S5QysCftH6sVCip4DmCoZIZrOiKtpEfIFFeHynJSmV4TdnXi1ELPv+8KuXgx73XVC7vuOsIOYX1OrsJkIeRVqha1zsbhJHyZMLqBd2DJOgalAsbCByOVrFp4eqFn1dxCe/F/B/YRnByqbrFx4bqDeUognfMDmahce78Qy9SZCPOaDzVT1woO9yCXeRogtOsa0K0wFfyv8BaCxU7/4XF4XAAAAAElFTkSuQmCC",
                         3098, [372.78567, 313.10814, 260.78429, 224.12706], [0.59847, 0.60887, 0.70091, 0.73484],
                         10559600)
            elif (record == "SRR653574"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653574", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAB/ElEQVRoge3YSXaEIBAGYBemzsXCK/S+Nqn7HyEqqAwlQ0GnoZ//wplqP0HiyzQ9efLkyT/k51WU3xeZ9QiRPBAi0uumj7lhZjUvalnkBU4htrmh5lHzvC7EzYFOYbeduPbhtChhY6QBhHsXzsLGZAsJ2t1Vw2yjVCmREPQYvYTOqwjItflAZjUt20KQUHgNVKBuZ56CkH4Lv1lIgRDNKaDBhbgvv1hoJpGIcN9Gru0YyRP2+wcyHQO5F8LgQrgXmjNG2OcXQEbSQnJPJcq95y5rEjisvf0MXEJMVkPobjhDTEjmCkuI8Wp4FOinL8OxaO9tW5aQpng/Ilg9X2WM/Uph4sL1XIGQyBbKPxLWqaHZUAdIC/3cV7PfVohfGk3iZ8pr4bUZCCkU4tHYG4bECXOGKqBfqR0R0kIm153p1VELAiE6wlBLx114h7sQrjzd8DzgdrLDZSH6LCG8T4hVQsoTnkQkd+7RFwCnCR6OKLR9y1QJty3wDtwKzS4cFkCywwqrenF/dsc8KReifyAlZPYjQqwR6rq1Qv5AM2FFL5r62L0QpUK3/CP8oFBq9Mp3LZQRhxKKppvBhFguZCv0KxQQRxOWj9PhhKVEv/m3CSFoPoCw6J8+YesRhAWzDdw17lyYPVAZ4CBC/HphZidywFGEOb3I+gJTt0KO+AdOLFWqkwdazQAAAABJRU5ErkJggg==",
                         3412, [389.37919, 327.04527, 272.39238, 234.10345], [0.59206, 0.61022, 0.70366, 0.70145],
                         11134265)
            elif (record == "SRR653576"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653576", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACE0lEQVRoge3WS3LDIAwGYBauzsUiV+hem/73P0L9IOFhwEaQBDzWTCepeUSfpRArdccdd9zxgfj5LYq/sulfDskNQes73Dy0eqhJi5cTjLFb6aQnpec/YQAgI+RWKTUOrZcyaulyLGHeBSMsT6ppPOYeVaqmhnEhdSNcCyjuUiSF6Eg4PbT4pBlCWBWekMORb2TUOCgpxOBCNq++0CVeQ4hQaEk0uJB4fQEjEPJrBoCRz5qnECkh+UP5vajDB74CIcfW2wDPwg7b2eS9Fz5TxWmhM4vek6wkKC3cBnxhskIE6lSII6FtUiDzgBr0MtU1a+pTBEFlwkirGstOWHX41qz1ghg54TriCsl+PfnZiEgKjzo1zaBm55VTqojwlasfJgd7CCt/ml3F2V5NlplsVrVBB8LlPWzqvtBSnL0CYTbRrSEiN8H5mDoeHwv5WIiMMJeomTCXmcN23kZqT2NadnYyiguRFcK8ZoXsTn8VbH00CLYMhLORa4TO9jkhYx9OyluiZ4VsTxDyN07lJvd5NzAnjIWTMgUX8kLnx8ZL4B1Cb/sKYXjhQBj7PytkKdDfXy6MX+hB6G/fsVDcpuMIIfzVGEooqWOwfe9CvrxQUMToPepYyJcXlhdxOGEpMVw+gJCrgCMIi4pIu9UjCLlAmFrdt7CgiJHFQwhPEymydgwhX154sojRpYMITxDzKfcvjBn/AVN9gblAtYpxAAAAAElFTkSuQmCC",
                         4240, [426.10591, 357.89259, 298.08476, 256.18438], [0.60321, 0.615, 0.71145, 0.70514],
                         12643682)
            elif (record == "SRR653577"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653577", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACEUlEQVRoge3YS5aDIBAFUAd2rctBttDzmnTtfwkNqOFXoBT4weMbJBGF1BWkc3oY3rx58+aE/PwW5a/s8osjuB9EQFw71t3mhhmnYRw+H2l30pk/hSeqymqYSfmUU9o9JQQirKqrYfQcqhdhHCEG7chcfknGGiEkhHAj4TTORkFgmcJF6C7TOwnVTvOZDhHehigPIXhCdE7Z9j6D5jUUWhH0LgQ0b7Tme4TrBY8VrqalHREvqa8+aeF8Ar5n8JoCq7MUzgjnj1a4i7hOPey5+JxkhOZMmRDWq2404xtC8oSb+w3Y+4IHFVwaKBASV7ePphZCarqpUUaoP3tCZqnax9X8YXXXtryklvNPeSEMFAajAcw7kNpbwBOScL+xZbRIXhhNYE5Iy88iXA/1cyuptKXQVpQQcpm76gkbnNXICu0Nyf5eAP/Q/ZrayIXqsTMr0BNSILSjQzz5bhHHCZ0ayoW6I/hCOx4jTNQMRwqhRmg6+g0bwrBo0CuXsXs9LxYGDVtCjL6d3VbWrlCPrBQmGtJCT2IWOGJG2GAazxfaXTMekjs1RP+6LYtbwylCZ1b2CdWjKhd+H6NThdFxXhiffKIQZTozbh9CySQu42MnwnJiMPz9hfh4YfEksnfo1sJSYofCQmKPwhJi1PdpwrhvH0KUAx8mhGTfuwv3LtOOhSgG9iLcNYss8FFCvmM3Qmah/gNRq5fzbGiepgAAAABJRU5ErkJggg==",
                         3208, [416.72035, 350.00952, 291.51904, 250.54157], [0.59841, 0.59951, 0.69415, 0.71236],
                         9781713)
            elif (record == "SRR653575"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653575", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACEElEQVRoge3XSZLDIAwAQA4evcuHfGHuuoz+/4TxAmaxRNgqhhQ6pCpsUVsYO0rNmDFjxgfi57dJ0F+bddpG/uUgsYOw4iq3jGVVL/V6lU4fQLgui1rVUjqdFLLt0I/w5K2FkzcIX0WSOh6Iw7eWzIQTAlzX3oFVeTWLY5eWbVLAQ8gVqyfhcdLkCvH4JE/ogST5KLEVb4+N4ApdkG4f1ngJyROiHZAn5O7kZyNVmHYrQoelloS63elJyb2nR6cJnVEoJDAgK8R3a4Eyo6CjzSoJTcnAE8YSR+e5AnTtgcdDFp4dnjBax21nO8JutitkCsW89x3qCzs5c+iNEBwhRSoDZAae04YQHj3kCknOmxMi+5prA4WU8hVigD3dc4WkDx3QDXYYul8FxD5ASRer4Q283YMUFZL7rPAG7AmiHqkbWGHkT7XtDCrtPIurgkwaspCPJkKwY+EmjFyYjNjP0CqhTu+dEHVv8PPXYnD3RC9NOhCuv0tPCG23KKzdqUT1QsoR6nwhEDpLBsK6KnrLlwsxbIgITTMGo2PCCmMjId8gCI9xzIuSLKx47/PX/5iQ/R4VFhfRX75nYelxM46wcJ8Gy3ctLNunQcZ9C/HrhUVVnMLOhPkbFdgFvknIL/BFwlvG3QszifeMp/B5YdZ5ysweQZhuBGbuFPYhxEShPLd3YVoRgZ06iDDByPsGEjLEf+IUxfh6xDJrAAAAAElFTkSuQmCC",
                         3539, [411.93715, 345.99204, 288.17292, 247.66581], [0.60546, 0.62736, 0.72154, 0.70945],
                         10916285)
            elif (record == "SRR653578"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR653578", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACGUlEQVRoge3XS5qDIAwAYBadnMtFrzCzzmZy/yMMKMjDgLzqgJ9ZOFMxaX5A2wrxxBNPPHFBfH13iZ/fPnX6Rs+JAuxZrSUW8VKH7kHYv2ZVvBbxVofeAcMIF7WG8tA7iEYhvuUKqkNtRG43GEfYeB9KCdD6H4XnibiEfwh5Hy71QooIaSBhU5CVeJsSbikk/vzcAWkhZhlBDDwVMaE+n/c4Bdwug/79tQbopTJCtCNGmLM6ZiJADKekULh/NlohxpJ1CZmzC1WFjzVbFlpC6Auth7KFBOQKR/mWYIQUCs2mtEJK/8hw5wEyZuSqiAu3AXCEkOoaDkKZ8MnOc6NEmFoY4oRDLKNughOuI5lC8C8Ar1xhRxU5yXq4/TkKg17Dns3ibzsxJkT32lgLyZfNUSeULW/D+4m0kOt6va1BHcOOum5uSghJOLdXIDTN5wqPxPUSBHdbmJb6CcE+HVkhnQohWxg2fSjpjXQD2h54IaaEKjNfGHR9LOkPdeDJ9z4Xkt9JKNy+xeQKyX3gnAlRNIdan3MhEwGoQIh74276p4RA5pvodULudUzYvE2dtxhUSPpHah0VcAIh6c+SKqFXfmShzSgLv/7AQjelKLgCtxICV2BgYTlxOmHxw4adoaGFeHth4SIG1acQYgtwCmHJIh6AcwgLiMfcOYRYD7yZEKK5owtztymXOokQby/MIgKfWijEsNRFQo74B+NJhloAHHCCAAAAAElFTkSuQmCC",
                         4154, [432.60464, 363.35096, 302.63098, 260.09156], [0.6038, 0.60583, 0.70183, 0.71062],
                         12201145)
            elif (record == "SRR797194"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR797194", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACY0lEQVRoge3YS3LDIAwAUBauzuVFrtCutdL9j1ATgy2BiPnFwRlrptNAQPCAOEyMueOOO+44IX5+C+KvpPEAUb4c0H+Fu8dsHmaaa3tTx5m8KaZ5MvPyVxmtwjPOgN3D+VHbu1l4wiGweziduofIXp8lNH2Fr48eIC8QJpp1i+nR8KQBdQuwVohoBggxe1oibnIk5ChRoPdv6HGQnJ4qpAIhz0f1QnEu2qJYGGuB9+EJ9Gz6NIK0HTef5AaokxJVEBG5EGqFQcMPCqlcmHMJiIT9iBQcsZhIuA4HvkU4Y0hsGzQJO3yvYpwqFNJWaZgwXF5FiK4+VwhJYcNeuhQUPPwSwuULw7YDZZO1g4n+DdvJv+uej9rmJIUtFwgney3EZa6+MiWkUIhu4dfGBv0AgfBZhPVf/NFYp4URvU1IgdBOEalYSMiF6AcAX7sLl7VYVyMpbPg8wi7ccngM7m32WKaCnhsJZYoDoS8joJNAmJMLa8+pEPrzI4RAQmg7oGgQCWFLwYQs3/OayoR22WwJVCE1Cl1PSAtJBudWCp/NiAvhWYrPhRNCPFqlMDRpQh5uTNarRuiXLSXEDwodKBZ6VFIIihATQsIxhFAmlGV6KaRWIRl5qoqF9h7w5cL9aZApxNOFYkY1Qn/lcUJhUoSkCVmGQKi+lRnQSwi8Qpo0oVo+EuI4QjmnbsKqTewlTFSMI5Rjfo0Q/G0Bt0GuIMz5qWAT0iWFWACkMP3gQlrb5xKvKMTgx4gMYZxhcCEUCjHKcAVh7jNVm/HoQrXNLbyFIwrx64V5uwhax8sIsRJ4C8cRKsR/SUTpoA4oEroAAAAASUVORK5CYII=",
                         3922, [92.20335, 77.44294, 64.50136, 55.43471], [0.6248, 0.6431, 0.73473, 0.72005], 54048815)
            elif (record == "SRR797230"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR797230", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACiUlEQVRoge3YOXKFMAwAUAqic1HkCkmtSvc/Qv4HeZEsLxiGmD+oSMBg2c/bkEzTE0888cQF8fWzI373vDxA7B8OOH+Ez455mb7fPzqDrMKx2Ms8T8sy91YfRAhYeLhM88VzWOpNa6gmwOwHx2v6jswhGJyysDjeze2qW8onPbpKyRi90oCeI8QdwqMnTUwEX1iqUlxRzc3qezyeNNdU1JhrpibM9ab9hLpOCDlhwSiEYkLbJ/cq4epLhUjm7gy1ML6JntxASPzLF5Kx8grCViKkwhM2t0su8yoh+mIuQUsY1YiF0DwTlrCxajVEJiUEIQS+1ESQYxLl41wN583VQldiC/XyoRsJIRUSN/c+TdEdtagySKG+0Z0Xtflr4Z+EbsVuxet5wle6M3uE8guIX88K9bdOR9SEGAtRH0XutW0hgiFE3wLTZO2wSnS31hI84Ujd2uc+CCG4a0oiTgChBOQHgxsZnw9zQqCMMN31PULyQgeI7/qEGJ5QIkSuyK9gWYgHcOiFfgHFAnftOxoibjUVElJG+EqGQYhVIZwkxEnMmhamwNAq7BLSJgz7EhuE/ct0awgOClEKqSqM7vH9BeT3QSrEY0I4QQgoa9SF4v41g9y8LXQbBKeuYOGaAkrC0LFEGJUIITULozE8XUhHhKS67AqkqVWIOSG/gH1ETiraNIVmZITSUBO6wasJO7fiVhFEm1cL05RKaD/7IGHmWVus6cPGGVyIvUK/zkcX9kzihwsxyTC6EHcK0w+V0YX85/CnC6F9saY9voMQ2rcj6Oo3EJLx90c+jB6PL7Q+7XIBSe07CM23MmFVfITDCPER5up+khAKFW8grG/EYsV2oRRcKdz+MYHRq3+ctN9YxiOC6gAAAABJRU5ErkJggg==",
                         6977, [172.40423, 144.80483, 120.60634, 103.65327], [0.62168, 0.63526, 0.72969, 0.72756],
                         51421658)
            elif (record == "SRR833246"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR833246", "light",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/wBd7RS/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACdklEQVRoge2YTbazIAyGGXizLgfdwp1n8mX/S/isVElIQEDxlN6+7elRMD+PhOipc1999dVXN+jnt7P+9Q6Q0T23EO8Js2ma3eP5c6PwzmDOzdPk5vnOiIB3Rls0L992RGgwodZgjZqWz2NqtR6AcF6K9PnTqIZsgbA1WpOmeXrM7Z1mAMKTehPCjt2rifD6jXg3Yb79dCHs171OE16TWk9CtOJlTQThRal1KAsvJNM1ZRPvQ4iX+DEcm4iEmcSlSWNjpahMehHCSqh929zmZO7KbGDltMFNwrn0K/IFNu6PUDsIJhCnVvwK2JcQhV9BuC3nOgh8xEVG3pVa0OIkDEIfScerlSjKLCH5TNS6pAnNB+V+R7mjNOH5pSwhXAehntDcvnWEF7TmuE0cEsYhQRHuqZuEy5D3Chg2iEVIfgLdSeUIt7hh2HiaaMI9qQThax7YI0hdGAh10ZQLRcA9WUGI6HZC3FZTeDEJcZ/B8KgDGfBVD5AjRH7DavWy5EQUUNYMgGGJwyPCbQ+tM7QVIyD5QU64nuni5zVzCSGahP4YwjCICwxC0ITMn0EIGUI8RwicECzCGOtZcGWElCD0ROLcR0gRAjOvFnFCwURRf9kTDULpKBCKCwoIMUToQbi1/wNCDbils5pVEVJE6KeZS3HfVOtrIRQ5VBICS6KU0DxPEeIZQriIUA5cTWjP1RBGOZiEphKEkuE0YWKugnCvgncnxFZCGoWw+hUVlPtPI9TtYwzC8v04HiEe/FcUCVgfHosQiwGV3p3w9U780YTALI9kZfz2hPZVf5UQLMNhCLGAMGP4GYSQMRyA8LhMs4YjECLF//T/B9IkEH3wVdTYAAAAAElFTkSuQmCC",
                         5794, [128.96992, 108.32372, 90.22163, 77.53959], [0.62296, 0.63457, 0.72732, 0.71485],
                         57084121)
            elif (record == "SRR1260032"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1260032", "RAM",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMC9d0Dm7cNnAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABKElEQVRoge3WwQ6DIAwGYA+sz8XBV9i9p77/I8zpNKAj1IKTsv4HzZLR9kNDHAaLxWL5QR7PU6Fzf785kg2h2jtcPX4Yi9Y3L3TeTUhxCJoXeu+cly8nal44jhNSvlyB8P2KevlqHcKSk0aDsCwm1B8Tqg+ZUH1MqD8m1B8Tag/MQrx7jAtjQv35F2HPRw2QCTklsNI0F4SoXyHOVxMyAq2exThfTchIRWHdIx2Xmt+FZ8hKhBR32GaGfKFWhYBLzViIa6sOhJ+hksL9U02nlrD2pxVHiISdC3k9Tcie6IdCoA6ExBXmm6oXZqc/CIXecBBZokESwuUWC3M9j0LZnFWEFPzAsOwmnD4ECBchEF8YEcuEIFeyhCsvFGZe1Zxwvzi1AUG3HOUF0Bw63hoHCWMAAAAASUVORK5CYII=",
                         169, [5.19165, 4.36054, 3.63185, 3.12134], [0.22676, 0.25574, 0.29277, 0.31315], 41362473)
            elif (record == "SRR1260033"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1260033", "RAM",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMC9d0Dm7cNnAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA2klEQVRoge2USxLCIBAFWUTOxSV0zSbc/wimMGqU4Weh5VDdGwjwYJqkYgwAwA84nWtc1tiEde8oovEOrI9N8Hvnv1lcf0aXoVv6M7oMjeuPKDOc/h3O/5XO/6f5BAz1g6F+MNTPjIZh4/Fgg78N+pdhGbst8V+r60i1lEoawxwYjgPDWhrDHBiOA8NaGsMcGI4Dw1oawxwaDe295BDxh2U2VX5fktB+BcX7TIvpA8PnFIYJGMpFiJMYtm6OYZosnouhXIQ4iWHr5himyeK5GMpFiJMYtm6u3PAKLZ2uVpQ738wAAAAASUVORK5CYII=",
                         14, [0.45754, 0.3843, 0.32008, 0.27509], [0.22256, 0.251, 0.28763, 0.21188], 38879470)
            elif (record == "SRR401414"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR401414", "receptacle",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/wA2WJLTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACIklEQVRoge3XzXaDIBAFYBbpfS4XeYV2PZvO+z9CiUZ+5KpowIrH2bTHyDAfjJgYc8cdd9xxQHx9l4if3yJpSkfBdYIUTPZRPDrzMM9n8byqxVPujM76rLN0WpxHaHGW15XOqqpSOufe6GoIcSLh472LZeNMQnvIPLviQj2RsE5cXohb2Hz0wvO8ECtED7zMJgq5dikhWDMOwou0KXPgcGHFXzLUcbzQzoU6mfm3s23CEqWpotKKcsgolKwckM+N9XomQ4g1KGR7adPzrZoQfKsi4cpWWt+4FCa/Y+eFi5MtF8In8sLXHRJeHj5AKoy60n/Bg8LkPrrT/RrmQ9/ytNKcnDMzue6wf0ZrIGTdo14osZAezOTSjFDpgmYGb3KlQvVCEGFQXt+iC0IESxvsTXpuhhPKvtOZLg1WhewE8FeCG322sDzt3wPynmysADynW9LcXk9SSLKPE2H0XygUNyC6D8GNxpB3zDDp2PsZwjF2AOFGvh5lt6qJUOLZENfcd9yq0NUnEdkK1fgbKwlfm+JXNU7oqpkVYvJkLgsnn7qBYKfXRChmc7jJwwxcCE3DlZglFPapezNFyzAj3EF0I9eFBFhQGKcsJ+QJdgjHJmhYqCtCfuHfheAJqJDG4cKtxJnxZxbqpp/9SIY3IFT+TZpHOroF4ZZOvYXNC2fHnl2Y+yCCDG1EKJcXZm4iG9mKMI94eSHYwGaEssZbLrkBIdnFP2Rw0Al8+63sAAAAAElFTkSuQmCC",
                         2268, [302.21573, 253.83541, 211.41669, 181.69884], [0.62838, 0.60638, 0.69968, 0.66331],
                         9535671)
            elif (record == "SRR1261509"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1261509", "RAM",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMC9d0Dm7cNnAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAQUlEQVRoge3UQREAIAwDsD2GL0zg3woqxo5doqDtoxEAD6wzWPe4NXZ3gGqZ3Qmqafi/+Q3nPw0AAAAAAAAAQJsLgZBJsofrHUAAAAAASUVORK5CYII=",
                         2, [0.05436, 0.04566, 0.03803, 0.03268], [0, 0, 0, 0], 46745857)
            elif (record == "SRR401413"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR401413", "receptacle",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/wA2WJLTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACL0lEQVRoge3XwW7DIAwAUA6Zv4tDf2E7+zL//yeMpE1iO16BBBBUsTRpbcD2Iym0zt1xxx13NIiv7xLx81skTekouE5ABZNdism7h3O+eF4iLJ7zXPhpCn++eN5+hG6aJu994aQAHQm98/7xKJw0ALsRTm5BFs7akzDcvgo7DXUkrBJwC4ePRdj2yAdsWo5aC6n1d6inEBsWxMYHMLW+ie0fmuoVwSpYsZ6OLCHEhyzDUFSwCqYlyg2rP+BCo66cA5hkDMP2VHpfqSm08nKhsQOIKRBpbZsPfFwzIW8PwK2WVYguJiR+cpq3UghZAZ1yjvAgJz7yySGEoVtkb+9CvbbMzIVgbvckhOta2ML5zLByXAhg555c4tcF68sNN7OlSBOiziDyzItcxLhta6w/J5c4RQhaSMZDZgiNjy6xQHc9lJD2/3kz8yt2XXTzGqaFqMaCQ520vnDexda7tkqUELRQ1NxngGzqKMRnhbZCYDW3nEq4yUnc5ASh7FC2vC9nHSEiTxURbgF8gGONXhBiTHjyWFznRYTLlX+E4TgBvC4kvqeZQnQnAs4JxQDYb8BbodqQD0KsIASkDOERmClE6yp7HRXmf7HZeh9DmP9JfOUO2yhCTEgWkAvVG10JWbwRmnFI05nw2HHvQvx44TwlY7sxOu5fiPPv1cQAPXsEYdZPxVvYqZDS95txhamHhjV1ECF+vDCROLIw6TkFa+IwQjwJ/CDh+5bThVLQUGgQ/wAczDAmjrxM+AAAAABJRU5ErkJggg==",
                         3226, [306.68782, 257.59158, 214.54517, 184.38756], [0.62713, 0.62905, 0.72106, 0.70399],
                         13365743)
            elif (record == "SRR401415"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR401415", "receptacle",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/wA2WJLTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACHklEQVRoge3YQZaDIAwAUBdOzuUlZtZZ5f5HGLQVEggiNviwjyw6rUjIR1DfTNOIESNG3BA/vxbxZ5LFPAznidAw2UcxL9O8flgHkXnKi7HM07K4D+OAfoTT4oTm19ABO1qmLa5hT8I2q7QnYZs7TU/CNkFD+JxA0J4K8EVCXbIJb34gQpMpzV2rDfhuuAvaZkpPCdN24N/RpjB4Ca2Vx0J6f09OaCUE+xd+0vcbMCEoQvJEVNtFrsNWWQqYb0bgqzE9vgvjKWBHaCrdk0L2ZBge+KqkqdBN9j7fJ4Ugl7O7tFF528YKs3FQ/DsPfnC7EYNrkrWA+DiqO9WbAdmJ6/F4T7rzkAkPiBSiEpag+A+Z1P3ZS2CFK8s4CH0CZD9l2RjWyNqWq99AKHruz4FIiKlQG7UgDCeL1tfLvF/eIFJyIeLHQqCM0H/ThfuVLwl9hXkhxpeKCS/ea8LUQnhRU4R4JNyOgDygCP1IqTDcvFoIkY1bEIaxLglRa91/uzf9BkKmKglRDAf8BBvhnvVIGG3SE5GMkxWSFIoTzIQhgyqkC++BUZkFYQq8WVj/xIAqYVRJ1DWdrRbC2r0ILGlJSI8Wrml5Al2oABkIuxTytEWhGkmJ3Qplgp6FdY+MBwq3O953C0n/N6ceoHTvX0gVmzHbdwifIoRs396FZzfiEHYsPEl8svAcUev4GCEOYa7rY4TFZZrrVyuUgjuFqfEfi8WekIGdIAAAAAAASUVORK5CYII=",
                         3773, [303.7989, 255.16514, 212.52421, 182.65067], [0.6395, 0.6314, 0.72733, 0.69855],
                         15780686)
            elif (record == "SRR401417"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR401417", "receptacle",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/wA2WJLTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACIUlEQVRoge3XS3qEIAwAYBY253LRK3SfTXP/IxQfYHgKmKnoRxZTX2TyW4iOUiNGjBjxD/H1IxK/MmmEQ/A+AQkmuxaz+l4+pIMIxXO2xTRPap5m8bz9CDVP+2bprNCTUM3yQuhLqD4gpH6E07fuNPpDNnoSfiQW4BA+JgBjB+k9RA2JH32eEKNHEx1lE/bz3lYSiddM919lZ+x7hNAkdI6DQHEiEV9VntBungj5CZ3CkO/F5joK293+AmVbDRsB6wvsvn/rrI52FHIgeorazawQ2E2hJYmIMPrUqhl/LiQyb9tYKdwvhAuPF8Krv7jBzsZ1sWylGCGxveUMOcKgbmCpCLiQ0L+2NAj5fWuJraWQ2prqPiNOhdv1/hcfQvdWsBVZQPJ2LwttJWsiOy/LhBimWrdCoT11Fv6crBiaCFuyu/JCIe0LUkYI7DHlLFNfY7+v9YljS+YVpYXsBARFc6GTD3ju/QKFdDTocyE2t9QKoRPcUyo0VwO6ZjjyACWFrVPVr7xU6NbMLssJvdcGR3gMTBeINwgxSJUVYuws73F5YQsRyIs2IV4WkmleeWF9u7kqNCAJYax7+cL6tSglRDAvdBeEeCps6DZBxY3C5IEaIbEnarJCrAOCP/5eIcoLw4pvFbIMQ/hiYWWzeaSQoPypCOHoJwgrpmpy7FuEkBzbu7B0LcaGDmEnwkLj64UQG/gYIRYIMwPfIMyX/ABhhPgHXfNKVbSu1dsAAAAASUVORK5CYII=",
                         2209, [234.78869, 197.20246, 164.24773, 141.1602], [0.62937, 0.62873, 0.72512, 0.65], 11954841)
            elif (record == "SRR401419"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR401419", "receptacle",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/wA2WJLTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACTElEQVRoge3YQXaEIAwGYBY253LhFdp1Nv3vf4SqgxgwVNA4oz7ThW8shnyCyIxzTzzxxBNviK9vi/j5NUljHYb3idgw2a5oWtc41xpnJQcYp9wcbeO6gWkbBICNc26Opv9rW+OkpxIOs7TrjJOeSdi4Q57DCiEZ951GP3xday5EjZBPsyjpoZaHCiLOs+wqQUx5YVnhfG4hoApRKuTxifWjfUYoZRw3E/rCxDaNioUQTyzte7+QT2gbUtjXh+h0Xuhndn8A2QhpnAy779IyINbM/jiln4SZ3iY7IWpIK4POnMnnOz9QiNCJTx8VDpd2OgtRIBQTI02UFjIWsYGhBIdOpRC6cNFpXjgcky0OyamfLchQSMOCMs3LhXBadGJhUlgoVRFiIexPcmjNc4601StP0fKWkXEQ4jjh+Chx1Dq4CCJTmhMi4uuLI56AHKedP43/4FlIyh78XyGnrWMhh7O2Qgw1lwvnzvxy6fvkuZqsUA7UlEwI5yqMhamqQijqEq4SIWWFhGOEVCBE3Fu8fYNSqCacRP0WgjgRhpZ54Qaiz40SISe9iQY03qQKofaZXbLmGApfxnUhYRkhDe8VvjYuK8LqXw3k3fm8EPK9pArr34l1QgUohcmJDUINkfT3zw52RRj3qQnHbcXHhbWPoqEQ7xLWGauEaixKPFpYOYqXFOo/IN1KWDGMlLv2NsLstXcRUvbaswtLH8RH+Ag/KOQyYf7S0wsLB/HKQr69sGgQ1QsvI+RHqC6kVxKuTFP9u94WYSxYnjhOuCT+AW+2AAe9J/A7AAAAAElFTkSuQmCC",
                         2719, [260.40823, 218.72068, 182.17003, 156.56324], [0.64726, 0.63346, 0.72947, 0.68337],
                         13267215)
            elif (record == "SRR401416"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR401416", "receptacle",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/wA2WJLTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACR0lEQVRoge2YQZasIAxFHfCzLgdu4c8zyv6X0E0rJEAQUKoLqn2nTx1UEt8lgNrL8ujRo0e/oH//e4i6ZOmujuNE2DHZLZl1Mfant4i6p7yo1Syb/ekrABqoiMYs69Y56TfgOISr2VbTvYYDERr311U0EOG2vWCngZEIX6KPJfRQOyGedJ1IgNz2hLTrDXZeIMkxN2HOLnMQOEJoIoR7xnoJMnbRcwAzNRLiXXNdFNhlT8h7Zo6wWCLAIaoYbP6ecEfBo0dCiPuBiDyuyzZWFvt0GO7PA36RtrmONjqUnyMBGxAqD0Y2S0HptTvzEyhJo/W6LE/4/dHg2xTsmRlC5SMDuWYBoVpKInAWTvzd37fFnBPzEhJC2ckegEbIdqLprN/5KF4w2+Ol61NeLqZOSDohsnF1T/VnRMcYQXbeT4vL9usz6bUP0FVC9EaFoyyhP++KHN4VXAT4SZAnBJUwGTXnI0GvFDDIfUIUhE4HYYIIwOHico4Q8CqhA6EqQkqESbIcYbK8AkL5MFId8uhdI+SFlSekEiGcEoaDAc2EyXjWSTopE6aAYgEVCPla4Nv35pZOmIxnOyEWCVXtedBuFmVC5xAwQxiNQwfC1PElwt1iPWF0tyMQQGTQLb6VkCoIo5fb+EVJxVDcvYsQ4xMKYUzUTNhcxZ6E+omHsI2wfSU+hNMTKo5HJ7Qh9f8agTh6CkL3NfWxhCLuIfwLhPnY0QlrF+LEhPjxhHVFVCNnIaxBBDVwGkIsAp4GTkBYRDy3PAOh7Rf2/QJIa5jS5ILo4AAAAABJRU5ErkJggg==",
                         2928, [224.73224, 188.75589, 157.21268, 135.11403], [0.64038, 0.64695, 0.74364, 0.66603],
                         16555068)
            elif (record == "SRR401420"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR401420", "receptacle",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/wA2WJLTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACR0lEQVRoge3XwXqDIAwA4BxcnsuDr7Cdc1ne/xGmtWKAQBHSfujMaXYk4S9IFeCOO+644wPx9W0RP78mZazD8HtiMizWFiNMME3mZZnNS1bGMA6L0jz6EcI4DDCN1lWxK+E4wmBdlbsSwjg2CFXJvITdHDXDfM7MN2N9ge6FzXF5IWqSBfivhfi22bwh9O2YF9KphDqFs8Lgl8TiZwWTzZqjWYhkccN+RCiaYJkQl/Wbx1L7Ks7NXE3bWC1rE3bvE3khOiEjw16gJZjwWTPVtbpyRshb8yDHE7KRcCm1NLIWYla4XuWEXC0MdqPrVy/UM32hm6pcmuglA/PCMm44ypWpP7YMhRwLRfGSFcVo0C6s3vHqowvIJRBTDYQU53jDniMeX6IoEjbcP0gJl/OGa/epfjTqQpLC8DbDtJC9hyGkoGOJMNgQR0LNlBIhlBPf92SRUG4EChj7BJJCkV4jjHd4gZDDxJxwXQO51Zc/thnvc48n0y5ELdXNUDQhXxj3zArl8E0oji8Ckv9JCOvOmkBIftmkUPlWjwpRXgOL/ySFBBXhMh+/tJgVilbNQgLven1Kf5+Q+XkzZIQsm5E3AHgfVipkCK65RFjz+O0Lt+exV0J/wHxW4mFhdA3qw7ovrLkTXe7aJCNUw02RmoVeSV1Y9ZwbVKgWbm8TvQlDYINQ/8Ba+Lhbry2kg+9R0Yz7F7qX/qLAML9/oci7hXr6LTyZEFO5vQuLjxol9VpCVFJPIqTLCwuJ6cz+hSX7FM8tpJfAbOI5hX+1hEDKHBuHxAAAAABJRU5ErkJggg==",
                         1884, [254.40916, 213.68197, 177.97334, 152.95646], [0.61851, 0.61402, 0.70602, 0.67752],
                         9409649)
            elif (record == "SRR401418"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR401418", "receptacle",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/wA2WJLTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACF0lEQVRoge3XQZaDIAwAUBdMzsWiV5h9NpP7H2FUFILEgoAzYMmbN6+lJfANoJ2mESNGjPiD+PquEfRTJU3tqHidiComKwqlp9fyr3JgO0Kt1KS1qpwViAgr58wOvfw9WqgWnq6ctCXhvEDrl7ApodLqpV+vylmpIeE98XghfIawmRtiaUiQFfiUIoqlMsJnFFF+OnuOEBDtYgR0zRFhR3R+ogBZpCeEwIPdCXF9PYNsObkwPHFuWr6Fadka5K2eEI9CNK+PXdn6FbNmzrBUKHb3a8UWbJIQjBDsGEUzNFnzld4FEvfbufAwqm0BWvbu/LWNVlID3B6j8m/CXiV2IQVCdKOZd8KZyoRE648Q001eJonTQzMgZAtBEtKJkJwQYkJXbF7Ny7HnyX+QAjZRQHu2nAjdBwzgzcYl9YW5pwWxMUsywGQ2T5HQXaxQGJkibmcvBNuNCTOraAcHlkQQkj+aIATX45oQcL/jQvitYqHrHBNiudCf4bxy0H57yQd4gxBcZ55EFgIbDA5jAqYLVxhMtsFN4gYh6xwXkhD7lClFuIvQH41fufuEFBfiuZDokpDO3keFl+85h9xvhXIw4aHhBiFd/+1SUbg9e7QmDGecL5Qb6gqDT58oxE8QXjluOhSuh3YBsAPh8rSRCgShdw/C9M04hEP4f8LUjSh1HcJGhGnr9E3P9oUpVQSxYzdCzPN1JBSK+Aum6iqOTyR9BgAAAABJRU5ErkJggg==",
                         3586, [228.02358, 191.52034, 159.51516, 137.09286], [0.62751, 0.63048, 0.72514, 0.66408],
                         19982775)
            elif (record == "SRR401421"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR401421", "receptacle",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/wA2WJLTAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACbUlEQVRoge3YwXKEIAwGYA/2fy4PvkJ75tK8/yO0uAMkJCoi7qpjprOzIxDyCbK77bonnnjiiTfE13eL+PltkqZ1NLxPcA2T7Yp+6Hr/0jqISnui+dwyhr4b/UvbwL/QFfc9OPr+gDWE2yAs7VgbQz8O7deQloRy1cgVb+iq6P1fa6EHLgi5yK/2scJx3HfSmHtsWQgmwsrNOEGYC0CLZbMhRKnrzhPnqAMLVUISHZsIcdRmhyl51R165B1C0/8GF0Ij0aZCjhHaa8WFqkOsBQQh3FEh4oRGNfvCFILVvVdY5o63tPmHq2MPXMqdCbMamZCk0HoS4yZfrD0KWx/LEJKYvlpolEcpqdGaegVh44cR7IFjqxlKD+91NaJbFJLTxpjVPtNYTp8W9rlQZDHH1QixJNRLMCOE6jXl2SOcOQakkMTlKHRqjOiWhGq9pZB/U1C9pjyUz1YetUJSc6Z+5xKKlHHLsrXiForXGUAUE2teFgJpC0zv0i38qBCpcC1kDlPIOjveygZOn6OmkJWzNTDNEx7vIARPmYphhWdzokCYiKJVCBVDCF1XET4ppt918Pf2lcNp4dQyJyT/kbYuJDanEvp9epjwNRYpR/zSVSbEdKVYmLWy5lVhza+UNNeqEHyqKqGzWlkzuw2msOpJtIUiYXgvbqYWZhcqhBZir5DNxec0hSKUkM4pZLk3CkUHzF9oLdx62OiKzy90m/4pckGh+TPlZkLzx+a9hFvOm6sKXSkQc2NvI5wd+wivIsTs2LMLS4+aR3hiobu9sJA4P/IRfl5Y9CTCGngnoQm8jtDV+ZRpVejyZO8SGqv4B9kjFZEgi0uxAAAAAElFTkSuQmCC",
                         3326, [268.94161, 225.88799, 188.1396, 161.6937], [0.63475, 0.62304, 0.71786, 0.68465],
                         15714100)
            elif (record == "SRR1046910"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1046910", "root",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAr0lEQVRoge3RMQ5AQBBG4S1wri1cQa/h/kcQJAqjMJlBfnmvHLsTH6UQEb1QO9xuXpvun/8+78fYhOMDXzmzpgYuSwhrE7gsISz/F9bAXQlh5BdqCPs+cFlCGAqhfgj1Q6gfQv0Q6odQP4T6/UvYWc4+ms2R4+jp+drFKPX1Ll7Tu8KMECLMCaFjhRkhRJgTQscKM0KIMCeEjhVmhBBhTggdK8wIIcKcEDpWmJGYcAGnGSRFuA25IQAAAABJRU5ErkJggg==",
                         9, [2.13064, 1.78955, 1.4905, 1.28099], [0.27691, 0.22606, 0.25994, 0.25318], 5367327)
            elif (record == "SRR1046909"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1046909", "root",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA3klEQVRoge2XQQ6DMAwEc6C8i0/Qsy/4/08oVZsIWoPkJkVyNHPgwOJoJ0FIpAQAcAG32cF9VlUrUF0861yFfzvGtBpagapU7nQrhqlqPIDhNFSNBzBMU9V0BMPuz7D/t7T/L00lGMYHw/hgGJ/4hqPqgUIJ3/H+uWck61XWYHfzPzV128QHhhgKhm3A8AQMMRQM24DhCRhiKBi24WfDrHAwqp+Gr39C/WK7mBirSMndFY0mHjDEEMM8KCV3VzSaeMAQQwzzoJTcXdFo4gFDDDHMg1Jyd0WjiQcMIxo+AFQdtySM1i2+AAAAAElFTkSuQmCC",
                         15, [3.62698, 3.04636, 2.53728, 2.18062], [0.31726, 0.35782, 0.41002, 0.32195], 5254981)
            elif (record == "ERR274309"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "ERR274309", "root",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACJElEQVRoge3YTZqDIAwGYBbOdy4XvcLMOqvc/wjTjgYJBBwVWvQxm1a0aV758ce5O+644443xNd3jfipkqV61DtNQL1cR2N0jwZZwQ2S7othHFqk7Ug4jkMLYkfCx2MYx/ppOxK65ygdqydFV8IWKw24I2GTeArp0zW0jVt4+iDma09E8C08U1jz7WJCgzIJ6f3F1A84s7OuJKRlPAYi5ssM0/8ITw0FX1/IJeHUwB29z1gPkN5UQvbdxVH7CUKKBKkOiSV+YJ5QSNPn/NgnzEgC/21pJ2dcNpC0fDoQCdlvKSHHQnoeEj5lyJk5Imwzq6VzIEKS5kRITgnVpd+/2ThyM9BE6J+FXqTX+ZdVMhUSh+2cEx6Ymi1mNbxC6s0LWQsRHuBh8F9oezUtbga9EH5yTf9iCikUqgOQCHf0JVoIfeVzj5SFXBJOnYaYnMFYlpJw9wAWoQw5Lgu5IHztJFmv1l7mZJ48Mz9BTSGXhcFxtpAzQv0W2cQE/24JzT2rIQWHXVMUGrEkojUhyejcLATv7EURUhUha6EqabqArgtNx5x3z/KMpN5jQt0Qle/+etnv1eWiKJwK27PUWhXXE3KwZursSCygOYUx36B/3JfQOwyhqtcnSIdinLor4ativT8QxqtrjpHUtiHCuloIl3wZoVxDEC518Q34iYXWdlm4bZzCvH73IIwYR4RmfFwYM4zqrizc0otnFf6fmKu4eyHnx+ovJxmcRro15rcAAAAASUVORK5CYII=",
                         388, [16.8883, 14.18473, 11.8143, 10.15362], [0.54115, 0.58833, 0.67321, 0.56832], 29192485)
            elif (record == "SRR1524938"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1524938", "root",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABRElEQVRoge2YzRaCIBBGWdg8lwtfodazad7/ETJ/QASSOo2IfneDKDDf1aRTxgAAwA7c7jvznNrHDrXK3FKeWlJavzWd0sq58NQqGTZt00sWhadW7xk2SitnIiLjAbFOgdYUfob6hqU/pdqGTVd6p+kN2T84GzCsn+sYktg952TAsH5gWD8wPCbCmT+FmBiGx+TshpKdVUb4fQzDIwHD1cjDG9I61jL2R0QCw+1JKX6fuQkM01RhyO6vMouLnag6z4gYCjtJ+spY6yWGYSKMNxCGefzJUIalFmXFfom5Cja2BFVnpaFDMcNgmazcwVj6dc+C4bJcFYZDUXYTaZnIdeciftBIQv+couEqKAxhWL3hMJHeo20Gjqw7XwgMgxuyZcirq6EOm8QO1l/y6sPw9IZhVL9oopcaTukT2YYSOwnDqxm+AIgLEeyeGbxTAAAAAElFTkSuQmCC",
                         70, [5.30695, 4.45739, 3.71251, 3.19066], [0.48144, 0.47527, 0.55694, 0.5487], 16760164)
            elif (record == "SRR1524935"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1524935", "root",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABd0lEQVRoge2YQXqDIBCFWdg5l4tcoV2z6dz/CLUEBpQxzRA0lu+9FUqY9/5RNIlzEARBJ+jj8x/r6/vx/Lub+7rI1+dmdzs9x3FSCKd5WiCHkX4Np27luVelZrGvz82u2zW8KmG/u/SahNOt15OGmBfCN0Pykf4gPEUgfEm/hCwOrD3VDhcfagvCM3QAYb7tIyCLVeOO8HlIxrgUMtjW/CkQ2uXzEIRb9Sfk8E2U6X7ABSJxM2KKaCxBnFrsm2x3woCwqeiFCEM9SjEyoXjx459T+jZrJBR7EFoEwkEIJUa2yIQ7dhFcmrOp6mV2n3AzUZiD0KKBCePfrruEpR3VKdMKus9L1ZCNt4RK4hp9bRrXgxCEIxLKJjYQ5nmdkDlXXUbFMclyX5o+Qxh6pbQWhGMTJruUxEbIVS2NgVZHNWHak6R0bWvo48e8e1YgBOH1CSUqFZ5GwvSCKk7YCONYaRoIQVhXsBIKwWoXtRCuPXcJ10tBOBjhDwtMAjHpsFo5AAAAAElFTkSuQmCC",
                         93, [5.40691, 4.54134, 3.78243, 3.25076], [0.5047, 0.50715, 0.57373, 0.61652], 21855410)
            elif (record == "SRR1524940"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR1524940", "root",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABaElEQVRoge2YS5LDIAxEWXh0Lha+wmTNZnT/I4zj8BEmHix/GJPqXgUZtfRUBWXHGAiCoAb6+q7owT+1LbfVthEQu0tHfLasGZUZnREOdpggVeqM8IlndRmBkM9u5SJZMygz+iO0yozOCIdxGK0upTPCHYqE7mTj29xgINytuxASJ0I615fvcbRBeMAXhI3EkTD+OqrZhc7zOygQ7tDsAsJ2qhDqLx//BjETsqFk+V/AIFQbgrC1KCNk+cBHnfKPHJaE0f21dHJgjd4HQAjCUjcnZBGfwkyiyc2GLhiXhGKG0+DWfclli5fPvg8DEPZG6Muz8bVlD54wnr/0PD+goke3DIi30beEclyL5aJPl+35ay8IQdgh4bPbQEglYYDhUtEhWblFgJJfhTCtKbt/RPGyCxCC8AMIly3nB7hKyCEuWywCasJUc7VREILwYwjX0rYTZhtoPXAZ4dvNIEw1c4NqBVoPtCT8BTaE8KNywwsFAAAAAElFTkSuQmCC",
                         85, [7.35455, 6.17719, 5.14492, 4.42172], [0.57646, 0.53631, 0.62588, 0.5772], 14685479)
            elif (record == "SRR949956"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR949956", "SAM",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCZmZnmW5lJAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACdElEQVRoge2ZSYKsMAiGs6jmXF6i92we9z/CqyozQAbFmKSd/k0rIvBlttqYR48ePRqgn9+c/mWtp9MCNw1r4dZ6Teal8SsQYsNSOml6mWlS+BFmzXnrofTuw4sTKvsQ8oSQtR5L+wgLPXsoKVeaPCHQeZfYWDciJGm9DiFZQrgfIf5BMV10V0Ki6wxTh3JHwqsgKglxXEWtFQhRWgWhu/E+0L2wZnIkYvGEEqG3nWepBQUh+AMAXJOQABPCE515NISEYbKSkRfH1yhCXPXoJUZI0vq+908YIbqLbXmwtr7K91gEWzxkCDEmhGrC6kFNycVWjSGsn7a9CInY0Jwv8bNpeMKNZ7r6TxX3HowgJCoS4nqWNZeC/FGjegN2ZOIMAwXC+a+1iSArC4KWMP0N075Y30RfGDQzBnLjKiHyIK0IKZ5vYYipAuRz6whpkXBlliQF5st9u8XzrRMhLRG6QY0iSJqfd2vsUGiRkJObXJk6oLQOQWjnwRIhcUL0ZaCJxedURBj3OQCETDLKSEIxdFsTskwyyk5CsFPObCLE8BYjTAYin1F5Qt8G32CwRJg+6EDo5QjBHzRcAzAK2ehRJ89E6M5HaFuI5Uxc6wg/i4YlnOO7E8Qy4aclvkxusIH0Dy8tEKI4xVM0CYQrzB832f8+LAv2ElJCKJgClU2CPm+GMNNKgZBH20IYtnHYREjRhqkjdIPSjjkgLWH0RE0ImcpRSQjSIUMIgtDHb0Co3vphHtsJo4owSspKRB+e3YF8ClS6XyFEs2XbiMK2JrR30JTQrfl7ABsThg+DpoQqxFLFewljQx9CVCw3rQi/LuMIk0q5/gPTB0RtY8VYMQAAAABJRU5ErkJggg==",
                         1205, [337.41931, 283.40341, 236.04355, 202.86401], [0.48357, 0.51784, 0.59437, 0.49826],
                         4537769)
            elif (record == "SRR314814"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR314814", "root",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJesWPEEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABAElEQVRoge3USxLCIBAE0Cx0zuUiV3A/q77/EbTyIwikCIYMxu6NFXA+z0rZdQzDMCfk/vzpYPPW+sc9Ivg86HuLNSomEHY3gy1qJhQ+zl+iav5QeLWX9Bih6NgL4Rthn/dW0G+bUGgaCrNCoWlKhZ7FCdsjCgqJFDYTCpOhsJlQmK7zHsYGDQv370VhO6EwXec96PBJoUlKhMH/L1ZC1VjJcOm+eGImIIWxInUHFE6XFFYJhRtF6g4uJ8QSnQ/UXahM7by2QFBVmKWBZO2NRSj5oymkMHNMevrYgEJ/MIXRorkCnhBYCQWxRPrNO4fTZC3SXcLI9DwihRRSSOHBwhdmQEf1f5uCUgAAAABJRU5ErkJggg==",
                         32, [1.74005, 1.46149, 1.21726, 1.04615], [0.333, 0.1821, 0.21256, 0.12384], 23367623)
            elif (record == "SRR949965"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR949965", "SAM",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCZmZnmW5lJAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACE0lEQVRoge2ZQZqDIAxGWTg5l4teYfbZTO5/hCmtQAJB0FpnYvlXEiPkkQj46dzQ0NDQCfr61vSjWs1phZtOm+HDNbvJTXPTzS7hHW6e56nppxPiwdG8RQ/CW9ONUDGCZvx38oRTRw5RMYKJ2vWE7sqE061rpQG7hJ26PiF9KCFdnRAGoSUNQvsahPYVCIEbIeO2cRCvqIdQP/cY0Z3lWZAiTZckzJBEUz/3GFEiJGnFWsuaOgkNL63bCMVyZESfSkiCkGLT4r64k9AQKiPEZCW+tniXsGkG6yUIkbtEwsV6LUJSCA1tkIyQvYg1wuhkkBBKQmSNjNDS11WdMLZ1QjwzylcESz2SRki84WRJm0niLkLYTIiHBLtLIVhlByTkhOjSApQThm2ySv1Hmwv4iNYIKSOksABVCOsfyo2fBM3jrneo9b32GBaEy1CkEiYjkERc0OqEjYWpVfGPjld7qDznCUkS4hJQScgUcpxOqbGIU9A8oPCyi4iZqGL3utfMY7g9/4pSYmIq+wgxVDHynlASVo9IrtxO48G+JPRpABbMVkJZdxhmvkWYLkLAz1lOHCAiCplf7hJkVUtsqc7eSVYyrxHSFkImTsgz9QwWs5EwuftLYG1fqhqImFC36W1kYb2LMH6IdBCC7JITitEKhx4+rlcJ5UlvhZAywqIHlZD32lAt4oMIQb8viCBrdxAC76bQL7mfLjwP9dvpAAAAAElFTkSuQmCC",
                         1043, [332.64131, 279.3903, 232.70108, 199.99138], [0.3875, 0.41301, 0.47413, 0.34154],
                         3984129)
            elif (record == "SRR949988"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR949988", "SAM",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCZmZnmW5lJAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACTElEQVRoge2YTZKEIAyFXTg5l4u5wsw6m3n3P8LYKpgQsAXRbm1fVVcLISFfRPxpmlu3bt06QF8/9fT7VzFYDVWvFrh6yGy1XfvdFXvjmZ2LQ1dT1/a/Yu9nBO9A2HZNW+59BsL+HF6fsCt2pjMQ9qu0K3Y+BeEm3YRPK/D2IiRuiHB2PiyXfZQipMsT4mMIcVVCug4hlgkpYT+RED9JN+GJlCbk6f8DCGP28yhFcBO+t0geBwTEvp9j9lOIoBqXJIRqqM0yRnj0Zrq5pEuEmF8pXki4dUJLyLLF7oi9feOEudqbcDDiQUhNAWGFq3bzlQ9DCNVynQ9CIJtw+xnfkZBCQhhCeafZJ73k684qVxtAIYwNdv+ekOfxMULV91JC5BGCYAhj3zRUH20npOMIESO0k1MwgKUxI1d3K/YJPb0ijBYIIRo1CXO+Y1nC7OWwE2E4QD8UJpIk2y/euQsJXXkjhFCEIaAYD3uZkRpgCBEMplTyJJNIDVqWm3zIcqohRQgjMoRiajNgmTCZPAxh9qalCCdnzZAkZJ5DDNUJV4FqibwoyHImRLiRuDAqndVsHITIJexXriQ0TB5jMGHOPSTEMiGXEs7FYZdlJqHcBUTbd7GfaSB0TUaCEHHCR6+LPtyO1xOi8cUZc6hN6L+QQxCThJ8zGZ93OUh/cvT+AyE3q+SKIgixmdDNTaodI5R5TgykiqSLM/qTnmUFIbtUahH6p3UZz9vZ2uwMS4TGc0lTwQg6RiVCFS9BGCzpDMJ1iFPYVxJyMHg9YZTxH/ueurVzmNs8AAAAAElFTkSuQmCC",
                         1076, [275.8827, 231.71791, 192.99528, 165.86683], [0.44191, 0.44261, 0.50076, 0.51008],
                         4955792)
            elif (record == "SRR949989"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR949989", "SAM",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCZmZnmW5lJAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACM0lEQVRoge2ZTZqDIAyGWXRyLhe9wsw6q9z/CFMrIAEMv1qxfgttCYS8kQYeq9StW7duHaCf32z95Xc9iUqTAXtkuLsm9ZgvVRqC8DGpaXpdqjQEoZoJp6luLGDPSPbSTPh81o0l7BrKTpoJa3+HQxA+ng2VhqhrLCfUTTi+bsLxRalimjCfXvC1hGAXL0bt4yhNOMSRQNA2oWm+PCFcl5DMh6h9HGUQDr5hJgnpAoRRAkv+AcK+E34dod3eDeFsR3Ws9iRcC6chpIsRkk8IYxK6r9fokoRuyIwQTkLYOiHwp8YJ113wY4TtZ4yAEB3LWl8IQROyCVGJgg5LrDmnaULYJky9Im8n7LA/yYSkGxdCOp4wWDXl2iYkTkgKA8LU5A3518nZiZA7Jy2gCCGKzpsIyQ2i4W8xv3rO3x1CXAkpINSbCLLIMLBXKSAsdxU5S0cIKSRE1h+J78nAM1C9wiggLHUF24RQSri2vN0hs0sxCMZlKLiEkquY9wghX4jmgcqEM6PTtCZIpQ/qQqmFHoSWw47MI2SHuYXQSxIyf1IMumdYRaiF8L027AJ632GbEAVC4gMss+ngGYMIjQ3CNLD0Gs+5gPagshI6588uhJ4/1DaB0Kf3CamAkMoIY8okBN7/lVqPwyWEwOTMByU7Pyxd7Qg3hlxCM9U2IUYJXwKngAKbSSLU97xNH5YpjVNoIAS/IYPQ74zKbxUI8x4iuCNrCTFw5QUmEqLTGQNuiTBaT/8Bh6ReQei3E78AAAAASUVORK5CYII=",
                         1102, [296.83853, 249.31902, 207.65504, 178.46595], [0.42365, 0.41846, 0.47456, 0.49777],
                         4717225)
            # Klepikova data starts here:
            elif (record == "SRR3581896"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581896", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD3dwDtPIrhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA/klEQVRoge2XTQ6DIBBGWdA5F4teoV2z6dz/CNUKWP4aa6Ey5nsbSRhnvocJiUoBAMAfuNyG5P5o0eXow/0E2b1vGqUb5ujHbkNtlDENg3Tjl28IwzGAYRV9PftNIwYYygeG8oGhYNi+HmTtoTE6AkP5nN6QvKF7ng8YygeG4mGGoXRgODgb/hecIU2G04J7J2oNDBUMh0ew4XLxUbgIE9gVJbul69Ib8rzgumFhTnF0K2DoimCoxjWc82wxjPaXl/JO1tdyqCjWcXxG1elNgGGIAEMYZhPXfl8ahjDFGEnEJY51kbIpvgPF25RXc9TIK66iSeHbMfglDGEo0fAJWcSGFv/VY3QAAAAASUVORK5CYII=",
                         44, [1.54919, 1.30119, 1.08375, 0.93141], [0.24141, 0.24511, 0.29856, 0.33728], 36088816)
            elif (record == "SRR3581898"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581898", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCTcyYUg6nkAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAB9ElEQVRoge2YXXaEIAyFfaBZlw9uoX3OS7P/JVQEJPzEgbHYotyZc0aTEO7HMOqZaRoaGhq6QB+f/err+0XBXy/uaQGmMTWrZb7ayFnlQEyC0tisVEsvbVRFOCm1NPTSRiIh5Qjn7d2Xsl+VVo5Qra+5pZsWqiJclqm/XZrdjIeJ3nR7QpBA1gRe6qSVHkGIdYneNAjtyTVmmujBhPQwwnxNF7o/ISWE5v4IQaLny+ojCKOHGkOzEaINwSD8B0IhDkeEO1cPzzcoxK8jhKb3VHmXlRNKHUqVzBPY8N2ThcDDpbEe3yUkuapagzCcPhjoSjDFhyNCMpkSQhqEgoANSx8tdnfI/hNCB+T9MMKE43cIzeEgzIlfj8MWoG8fNrB+rDkdQW8H2DgbAAo5aMvi7pHnPGHG+zoZ2gSHfeeO+AxCsl5NC2fcw2hQ3I7tPG7jxIS61Xq8k2+4nJDiC5FeujyhjgzCtwjJ7EZ/xuKErwl9N7ctA8KNKJpdIkRHiN5DLaEzTCEhBWfo4xQRRr8iCMbbLw0jQs7Cm6aEZt8Yd24wVjLemdDspDLCvYrCApmQ/XSAEsLdY7BsGULWjh8PQku4VUbD6gnRZUVC3z3KxhhHhAeFjyUEO1ERoTgLyIESQj68hhCnAt2VEJKp2xKKROcI4/IflbwztPh9ap0AAAAASUVORK5CYII=",
                         265, [11.36531, 9.54589, 7.95067, 6.83308], [0.51049, 0.49804, 0.56878, 0.63384], 29627136)
            elif (record == "SRR3581899"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581899", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMALU5xZsz6cAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACh0lEQVRoge3XQZaDIAwAUBZOzuWiV5hZZzO5/xGmLVCSEBRasDivWfRVRMhHRHTuE5/4xCcOiK/vqeLXKvx5trV3D64RgGZpQwvL6i7OrV2yGRGmEKihhdUtd+asYWKAsL6FdV2W60+nfPpHnRCNSjEuy7Kul0u/lDpHnXBr1t5v4czP4cvC6VeaOiEatU4S5qJCpNxnFl4xqMvgtELr3Te/sGX3sSlkJ08mRFYX89MnEO5tsDD9LSwqvrRKaO9ix4bORQcbgSxv5zHo/yEv08Jw/IZ7CW3CrDITEi+zhXiUUCaTnRZp0KbwVsSFEBstCVs+Op4PSkLrtmjhY/rtCtHvzkwhusJ4jghK+5CUID/PSqBFSBtCcnxKDw4vvCduC4lXfaRrJC6F8fwswntfZGQNY4RwhDDMN58AISLPMNXKhRjKdV3IhHhdbIxh8yXHCn1vu0JqFvLbLtoZI0SxKQvN7wjTtNwRhrslhLQrVL29GCBfsWnNDsKYlZGNKwkfY3ZbPC1hqU30ffZ9X6hBZ0Kf2p4wVk1CSruzRzsoD0tt+u46b2tUV5lQpMgT9//iCNjC1EylMPQ5UAg+G5WKFqb8TCHGDRGoyyuFfdcakF21C0WFIMxFjcKODyLI9CEcZUDZJxNKQ19hFyfIvvyhQ8ojplEhNEStQnQvbcLZV7TqjOI9KAiB0i0eKnxxiwq3BtAQqgxKQpheeLuS7c6KGdhCOkSIhY+aaiHNLoyLwVNAYH3KDDaADISHCMGqUxmmqUWoC0YKsZHWRWgX9BbKK+sC/Ee0GJz5hQ3zFHxPss9/JAxPT3qZn0aIlcDChf9FCMULTyCsmqbnFlYQLWCzEHVLxwmzifoHfuauYdhY/nwAAAAASUVORK5CYII=",
                         10921, [410.30135, 344.61811, 287.02859, 246.68233], [0.5728, 0.5691, 0.65435, 0.71493],
                         33820866)
            elif (record == "SRR3581895"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581895", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD3dwDtPIrhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACJklEQVRoge2ZTYKDIAyFWTg5lwuvMF1nlfsfYawCJpBYcYoV6+um/CS8D5C21Llbt27dOkA/v+fXY2/gpyd3s8BswKxqGNzgur6imxoiq0EhdF3n+r6r6KaCoIiwH9ewHyraqSAgNFq0hnH9+q65NcTtDd346t21CRs8aYoImxR9HyFaDa0qAyGroVHBNxAmH/kejG7CVmQRwk3YjL6b8BqItEZo/rBqSQrhVL4C4WxfI0QXCPFoU2/VslRJfcOE/FqCrk9INiG5ExEWXSOxOlglhEB4wFED3Kni2pxllZDY2zVCioRW+l1Sb2aJX/YpU2pflFGejyQhumMJIR1pSk78LiEfMAtiDcp0LHX0AcIknSfjtYprScjWW3mGCGMywPCQGYR4COFUnA2gC2YwCxIho3Vuk4sfjt7+GKwcJ0cREiekMLLiWhRGQowIed/NhISxx7PG/vemQOl2md0EK+hUQhHzLPiV1wj5mrwmjJoq7P823k8ohxI1rGv43sw+MnjrQqjkTAhpfmbR/VsJoS8uVhC4xYwQNEKMGWOeckJCpU8BlSBi9mdCZOPsIFSIdhBqfQoIg2FhIPeQPPqeCRhhmIFahOj2iGWXg2V8mR1YTnRPKKy8n3Af4jPQHwYyzwogRYuSUDqpQFiyT4G7SghJltYIw8Y9IaF0dUFCCN35mHsI9YqzEGJ7hLgVLuwtEIEXIVwJbIDw9TY14koJJcGRhJgh/QHPM4ZUmWGqIwAAAABJRU5ErkJggg==",
                         9655, [369.24767, 310.13651, 258.30926, 221.99993], [0.54292, 0.50047, 0.57414, 0.63706],
                         33224602)
            elif (record == "SRR3581897"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581897", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCSkyZLPzA/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACfUlEQVRoge2YS3KDMAyGvUh1LhZcoV1rpfsfoeFpSX5ggR0gwz+dJtiypA9bgta5R48ePfqAfn6vr7+9C8++ucUCi3H36jvXNcqklchg++pew69WqbQRWAiHPXRd1yiVRjISvn/6vlEqjWTdQ3e7OiRCNeArU828S7B3vftqwlsqR2g6wFcVhIToCdXU4WB13RUGDQn9SG3CU85EGWGlm38WoYrrCdEToquh2meiSFHCaQQYYZ27fzlCugLh0chAtyLc0Q9yhLzlVCEMmppOJgYgIjMHeVfMaZoQBGGpw3ysvBeI3cgkYWFGG4S0jhX6y4m2vASpjINsDb8FBSkFGD6On8Jid9sKQ4UGYRhFCPPeDQcinxNaCMOGu0c7Cdm2jYRrG8x7AwQjYRjbqnhOwF70IwbyYBItxbxNGCk25gfnT//caEZIcAohufqEiZxoZYgakCKkdoSHC5F3rvF66hSjaxgmtAFPxl/ECZeDgGIlxnOfvVBzQl8MU6/OE0KU0HcKHJ4O7C+EswiZF4oSJg7U1Bs1IQaEy3KQ7SRGGLrbRRUQoojj+MZoAyMhvr8PTxMVbJMwVa2FhKJUZDAzIXnT1Zg/z9jscg1YRki7CTVRSLhmBo5nOPSMYTs2CDVRQEhJQmKEIEPXJOQSjWQp04OE1JoQLIRLRE4InyCESoSLQ30dyqchCCVDKSHzkCLUp8dKiOy7gRAqEcqgcUIUS02aPHG3/BAWEOqBmoShTITr/0G+lBBma74wm8E1CA0PRJit04QZQA10WUJMEJK8uichzJFEzDsQYinhbA1i3fcQ4vrycUPCTUSIr7sN4VJbKVBgrwlHCCXBZwm1/T+L1GYl9DSnQAAAAABJRU5ErkJggg==",
                         2364, [102.00556, 85.67596, 71.35856, 61.32802], [0.57775, 0.54427, 0.61984, 0.69561],
                         29447531)
            elif (record == "SRR3581894"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581894", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD3dwDtPIrhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACYUlEQVRoge2ZTZaDIAzHWXRyLhdeYWadzeT+RxhBqAkJohY76Ou/7/XZEEJ+fKnUuY8++uijN+jruyv9Wsafo9H+u3MtoWWEHQEeg3v4r14FaFlpR4Th4Ub/1atMQiDLWlAYQ3dnwmn4JryhTTonaBuh5ZQUCPsdwo2Ea+tymqXjMI7tUmossJLfRdi7yCbMrHcjnAALhPa9pW9tJMRYgmfn0167CNGc010L1IoL1hKhsvcmPcc0i22dCb1dhehKmpDMnO9PSDcj1Elfl5AwX3SMEKQ19wsu/ROqbYUTorDmfsHleoRgEsLFCOk5/fQWqQjhac2CBKduCTFe6QQV4XOoOiKsnRkBQRpFvW8KQnL+MwXsjbDSJEu3Tuj3WrIJyf0bYeVJkTFoQsoIqRdCTrWdEGqE8zXNVhUFnFVwkvghQ6VXYY0QTEKyCSl1yMvpbxAj1HcAeeRAGaFwNgipTojudPGXOmtpMANnUISxUBImYxbSW0SHnKO4b7IEjLUlXts5gyIkizApDzm52fBNpQmtToVVQuR+uwgLRU0Vk5lbIUR77dM6oXjEOUSIrqVES7Hh0AzQsvGpbNIl8JwSIcmyY4StDt1AdBjE6EtTYHTqkh9YhAbREcJWc1U2FQlZahVCFAzNCClERtjzN6otkOkD5YQyRU0oHdoRoqh4ACsLK3/2QFhw2k5I8e86GSdlgLohzOq/jfAQoq/H7nvFDIyGyL8sXoOQve0scVYAGZDLDecS4n5AeJHQNvRACDSfNfCKNyKENDfTHewyhNsWYrFrrkCIGwChWO8KhPHBioH+AbDkq2Jh7vacAAAAAElFTkSuQmCC",
                         10382, [320.82307, 269.46398, 224.43356, 192.88598], [0.5146, 0.49868, 0.57258, 0.6431],
                         41118826)
            elif (record == "SRR3581893"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581893", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD3dwDtPIrhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACR0lEQVRoge3YS2KEIAwAUBY253IxV+ieTXP/I1RHCQSCCBO/Y1ZVMeQpIFNjnnjiiSd2iJ/fK8bfumZHP9wPArNXut50xvT7lbJRoM1d6TvT9wPz6pEXmlF4h3eYH6b93YXjJLyT0CZXXq8B2b32LWeDyAtvEkBCe2gdm8UAdML8inPpQBIurKmXDhLCNwjtsaVsFBsKT/LEHuEnqZXzNYYTjl8Nq5xaOV9jPMJPUivnawwnRHXhWb4+XytU2N9oCK1Cjlk4TkNfkm3bhQO7S1kIrTkkIZxFiCSE9lE1C5EJG+dkSQi1SakOOKmQFwX1kyrYcLXPyLdsHqSqQtAVto/5SbaBEAUhP1Eed1RTTUXxkqQrDIqOP7DjQMNsazkKQnleQ5R2oqkI2bicMkZX43la+gIwYfo8wH/e2Nk0iZIQy0LLmwvCuT7gt0iPJxQGiZOhsb/QPWPxtWwtRF+MNdWxKPSPsFkYlvQeAKIwyaospNsiYTBIXF3LQutqs0I2Err+glXsYOE8tmivLyUhIeSF0yEJgdcuCX3/RhgSFUK6Lyf056OiwZ0koX/tJxbGh4EQwlFjYI3Q0to7HWKDEH0tbcCMEJJuDO/GLRuLQt+cEsXCwJoTuu0NmtrfAjVCqt83eAvpDQxdhxkAeXNJSP9uKgiDv6HuRXJhDIiFdMY3Xy8ElI7rhVjeVrULfY/hzV7IdyGrhHaVMC2lVmhZ2riijNBpPhUGKXPCtJSCKcnDhQyQ70ESCteXhdgkXCSeTcj6XC/0xn/mI/sEfeFXoQAAAABJRU5ErkJggg==",
                         1971, [51.66037, 43.3903, 36.1393, 31.05937], [0.46564, 0.44552, 0.49614, 0.59073], 48479083)
            elif (record == "SRR3581892"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581892", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD3dwDtPIrhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA2klEQVRoge2UQQ6DIBBFWVjPxSXaNZvO/Y/QWNM4SSHMmALFvLcw4oyfeWoMAQCgA7d7Tx4iz47bDXieq0hqu8MS2+bXaG8Yl7b5Ndobhtg4v0IHw8u/w+t/pdf/04wGw/nBcH4wnJ//NhSR93FfnM44eec36w+zdjA0ZmBoBkM/GBozMDSDoR8MjRkYmsHQD4bGjHGG2w3pON1I6lqQD3qlG4x7uPtLRT2PaQ4MMTRP7O0vFTHMpiUVjCGGxYm9/aUihtm0pIIxxLA4sbe/VMQwm5ZUMIZzGL4AI2n+dCbOf54AAAAASUVORK5CYII=",
                         18, [0.78506, 0.65939, 0.5492, 0.472], [0.28149, 0.2762, 0.31203, 0.27163], 29133506)
            elif (record == "SRR3581889"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581889", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/2ULgAcEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAChElEQVRoge2YQZrzIAiGXfTnXF30Cv+sWXH/I0w0RhF1KkaTdCbfok81CLxV1NSYW7du3TpA//5fX1+9A8/+cZsFGuOneZjXa1YqcwSA7caPp1nwHtOSmSIgVFjbOVw+PkqXItSsp2YRkcLaEk5cpOcTPl7m9ZxHqFtPzU4l4YQgrTqIULNoBwtUFdPu9CY8Trpdr1FXIsxzmeP1MMLsaNhPWLqB0nmE2cZpCWWfTqXztEC4L0iz8qPhjxJWX31yGjydMHWcHw1UIqwWDaCER5E7Bq/CZRZkkACTSK2ESQ/yB5KQTOqSglfpUvVO3C6BBBnOO0IgPqOZMUiWd4TD7/mdhHHQUrkUp1EYg4rQjRxOKFLKcaiEyNJzuYJvy22JVkJmbQmhSEjrLgfVGu/UGEIqE9JGuPWtS5rKhM4Mh9+gRKgkQ/e1QohsBIW0UltLxwmXXc32YJWQnMk+oEzOb0iKzQHaCsMyYbjJ+fVGKeF2qAJt8u2VkJIhPJFlhicREm/Zhg3ld51GQoxIOwiLC6ZD7OARwQKhTdJnWwgahgDqCYNqhDFa975KETENFgJIQoHYS5gA1gnDk959Ffjexl0GGrBLaS2qEiEwwoRhNYacqIswFvRoQj9x0EKYMkDSGkHYhwgkluXmJwRgqSUG9gQ3sVqnETrztU5GEVLS2iYuT4dcZUwntI/Q10kPIRunJASKB8hkQugh5Mcye027JqEbpSeE6OtHwhyQE8J8QvYbKwDBm8NbwpJiikcQxouPZqv5/YSbOR/YQ4iyYwZh1E0oPbhzZh9hueNswtrAm/AChG3HBeTjPocQTekvwLeAakKUjg4j9DfhOiEWAT+JkNjrmtM3TV+TbWweoCsAAAAASUVORK5CYII=",
                         1866, [86.19049, 72.39265, 60.29503, 51.81964], [0.59417, 0.59169, 0.68169, 0.72853], 27509175)
            elif (record == "SRR3581891"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581891", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDn/2U/mK4FAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACdklEQVRoge2YS3LDIAyGWbg6lxe+QvfaVPc/QmsbG/Qgxja40OafzjQm6PGBIkice+utt956QB+fTemrqLffXlxDgHc9TJObnBvvp1JJ9wndMLhxGG+7qSWbEM64GOe/sUAudVSEcOivSskctTX4XWxVRMYgSEI0Jm0a3DCNw1QupcLKI7Qm9aJ/SyhGeyG0ukomoWHZojQhKZZlXlOEZ04ug5BMQjXaC6HOcyZUg60RnohNJNeDzE1si/AwNjn06erEgcxNbIrQ7BRMBHmEUTG0RngQPBDqiswn/L0DUScjRfsi6IpMEOqleJxwbxhgdQo2ADsDHBAGM4uQG9ZWSMbsFPmEZBIay2YsQ01BuBjbhPEAFSaUwaqIjggpnvqCEARh1HMVIfn/MlgVRZfJQ0IShMQnMkLcX6UIrcPznmRRrI+B0G+CNMoj9MYUcc3nCjxMKLoGbmnPtMjLzDI6Sbj41Xu9oUF5QuER1sclgSWaSUjR9fMKoVUX60gdQuKP6EcxgxAswjDXJMQjwqKIqlxCrfjUWIpRMqsRbCvACPe7S3CTR4g6obtSoVKEukF6QsawEbI+LAkpTUipryLnuXB/JWJJwl3+bUnIGYA9yXelW4OQTb+uOZD/AVZ6BL5xMp2fzZkrsHnC2Qcwwu3sg0PCJfpjhFdRIyeCkEQOFiHF3aAuIVzsOWAQmhkkCLE+YbhY4Tm2OCtOSPzpNaEcqEQIwTAbMOa4TmgPlCeMLfMEi1PognC/S536JK6RNsvGCUPPy6RDYJ+hDggTs1ICfcZ1Q4hZhEnDv0IIScMOCLPK1LLrhxAP+eCFXT4hSlePES7fKNnUbyPdWSJbuMDoAAAAAElFTkSuQmCC",
                         11015, [530.44492, 445.52844, 371.07569, 318.91532], [0.57371, 0.58864, 0.67499, 0.72065],
                         26385752)
            elif (record == "SRR3581888"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581888", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/zJgayrdcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACYklEQVRoge3XS5KtIAwAUAZ21uXALfQ8o+x/Cc8fmoSgyMfW+26qu0oRY44ieJ37xje+8Y0b4uc3OSi960Pi6s2gFne4evRucF2fd+4rhF3fuX78zwrCqrU0in76+3BhNzNz4i3C7Ef4DmE3dEM/DHknv0JYFB8vhAcJsUlWoOcsiNgk6yhsk/h6ALZJ+xghGS8MVMirhTVyJl5ZXYqMF6bGY32QkNoISQtvm3i0xxJWeIMgFJYnTYskYXk1oPPet3qkCYursYRYmjT1yrIhIiytZhaibJh2xSzQZKFKFZY+xEBI/4tQtvGdWnEkBKPtYnZ+nUBIbpsGpiPTt0aD2SeonVVCvC0nOVvz0oQNZh84FCJry8zO0xpC8GMVjS6XwzrZFq5NxcL5NNzTsgqW1QMWIdQSGp+CYe21hev8aAvJP8lROLecEY8PW1VGhLgUgdFeaaGF7LVcPdtYJSXEINmSJtLur+cPb1kgLoS2QuJCYkISJargH7O6B/HJbKSNDXAgBPGpnCmENOEyWN0OdrFfHsAGsf5yF0MAcFp5tvtmCAn4nGr0qirEPKHs4nOtQp8sLsRKQrSFFISv6URI4aZIqIQYFcr+F4XAzrOFIXAPJURVGxOyQ2BUrFLaQtr7ZwqpUGh9B/nUfyf0vfk1l20Qe1lCVlIVIWYIIS6URw6F88aWitWNbBPkoRwhWTcsQUgVhKiXqUAo17MCocj1iUKZ604h8PoEaiNoUY7Q7na3cFvhqgtx3zq3kfNDa/nV93FCXhZumfKFoBraCDn2ZmGk4SlCfdorhKeTjba9UIiy6z+MktTa4FWFHgAAAABJRU5ErkJggg==",
                         1598, [68.38524, 57.43776, 47.83927, 41.11473], [0.55215, 0.55567, 0.63193, 0.6717], 29692016)
            elif (record == "SRR3581890"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581890", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDK/wAy1e5hAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACfElEQVRoge2XQZKEIAxFWfTkXC76CjPrrHL/I4yKQgIBQcFuLX/VVA34IXkBwTbm0aNHj07Qz+/362/vwE8Xt1hQ4X0Nr/dghl6pdBJguXd4TX9Dr1Q6CUi2MWd+mYmxXzJdRDWEwx0ISbfNsnhDx2w6CGoI3+9pFd9dE2quKsJLKibEj+TRTw9hQ21PXHM3F4tOIyyYOLyb28S9OyGcSJhIn30YK4Q1n8369GcRxoGUgBAHP5yOQtjnQpwCoeyZm8QZQovpRIgsgWYiCiIt60Vs3bR1Tha8ND+NkKpmKJRCOKMxQozXOfPD4Dhh4906E/KkPCGlLFoazqyeu+Fo8y2EoFtM9EHi63GcMPrWOagofdsE8g8UwjA9RqidzRp1kjB5uO9UnpCcRUbVCHF9ECY4Hsvkrk/3msZGHxlNE6ELJEJJQtQsURqQIwRRxPEA83tfGm1PJ0Ifa84HkBHyDctdKJtFhNPEuJ4nGiHaqdEcFy7bRSUkTwgqYdCRJeTDAcf/RgOlCMkSuif778ZxXwlC9A+E0MFGhMv1bMQqQWiVw5eGoXQpZMVrCdeRMO/EEkIqIORTrITojBohbBJaOzYk9EXbIGRXpG2jRihOzJiQFvANwnnuKkDghKQRAgGlxIuUJ5yqEhKFbVHW9oQsZj0hFBDGRDsI5yOp7uqAdVKFULaShEDrie46uhCSbUPsysrZNabdhGvWjFAhqiW0QT5ESJJQMDQjJJNw5QRrJLwCISRcRYQ85h5CDDu+izDI4WsJU66cgtrsJ9Q7Pk3IX91bEpLbW9cjxFJCfeBdCCE58CaEGuB1CAteRH1cLaEkOJNwaxUhO+wihCD9/7MUsTkqHvbPAAAAAElFTkSuQmCC",
                         4460, [182.82152, 153.55447, 127.89381, 109.91638], [0.6154, 0.60947, 0.70162, 0.72003],
                         30997938)
            elif (record == "SRR3581887"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581887", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/zJgayrdcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACt0lEQVRoge3ZS3LDIAwAUBapzpVFr9Cutanuf4T6A7aEhAHjUNyJOtOZgAC9kBoyde4d73jHOzrEx9dQ8VOV/Z3p/+s31wjAqmwyGp/uc/41athCSGUbwsfz4Z6P52UVXR3mrjizMZU9+h5WCckUTns4sNCs2Wansu8pxPLsx+f0KZ1+jRpVQjCzBw+r5gmCUVaq4waREEatgwlVzb4Bp58owO01750dhamD9zhiIQahPt2ZkHWSFmLoUFO0xUlhVIUvF8gQ4lZ0Rki+Q03RFiWXRp0iq8Dw0SoWQkdhwXxGimgiOhJSqZBGEspDiwt17mwpFKJ7iTB7wBpnMxfOH9HrhHC5EPXJGy9g3DJ4E1UIw4nQUagmNGo0hJQWquEVQjI3ty1SQgCREg8TQpLCONkQUmchRQ1zNSD/ZFCPEpUdCMESro0ysbOQ9q9vJUIqFhIbIhNfKeT10yYkloJy1LJta6cXcKFMlsLJuA/Rk+L1QopLWl4iv1QlhP6alhWy3nXvKYx4oRDmaxju6/OSlgWICxPFeCHWCvFISNEM5y7Ny00xHL6mELTQqDpMpYSicqwTYiSU65YLSQrlDWzdxfUjg81C3uuFW+SEVHKlNIPSQv/++nWWniYh8N7tVVrIs/njrl5IUrgBRA0lQlkV+I1QZdcJ2dwXCeXhJ6uAE0J1WJ4XyoULA5Rwf6qkhLKarJCfNGeEfLIqG6/KEoIWhtOALwQZIXvHWoRmVgaYFpoVNAjj+foI4UBIapGwlijRLYdwH6EcWirEfapCYbQOhOvAa4XkTgnDpKeExOboIMR4qmygC1fbdiF2EFL8kMoFhG9ejUJIN1ws3KNICPNsW/rNhEUP0yVvXQkB/qsQo3H3EWIeCOlxdxAWbKI57EZCzAHhYNgthGT837VAGJmGFi5fCHC7lLlf0xXyvT4rDGYAAAAASUVORK5CYII=",
                         3143, [120.8444, 101.49898, 84.53737, 72.65435], [0.58217, 0.58808, 0.67452, 0.7091], 33047842)
            elif (record == "SRR3581886"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581886", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/zJgayrdcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACXUlEQVRoge2YSXaDMAyGWVCdi0Wu0K61+u9/hJIYD5IHbB5Occq/yMODZH14EM403bp169Yb9PV9ff2oMmoN//rlVotUGZzvOy/T/PwZS9Blzvdd5ukxLR2D6aIWwhVxnpalXzBd1EQ4z4/lMXeMpoc0EZhT3V5aV+n8/BlKFBPqWfUa8qSJCeEI86gjKUVoa4pbchgR1Ez9C8Kthj+DEHlC3IRDiPKE9B8IPyFd7BDy+yM6W2MREuu7XoVNFWG73z4iELfbjEXYvqoKhLgeYcu+sTGjivAi+7HpZNgwaIfQ5f5zQpTiVoMWQioTsn3oSWhuNUT1vhPRFvtmbCwhOULu8/1mCBFd30oWpxFi8oS8HtFdMqO51SC63BQtqgNBLSHTRnjGOpVHsvGZc237sg7NINKUyozBit8jZEu4PuI4odpjkG2akML9njrGQ0LOEHLQ1w6zT4jjhGEYiAjBIaF5ma6VtkoZmSOUy9Xwwn7zkDxOyoRWxwghCizbNGEwkNv6kAvPEaqI3PG/EfIeIc4hFGaAmlHtOkVIBUL4bUCOhp3585nCnKcJFeBRQg4LkG1WbHZoghDhXEWEPo291oebNzc9q988oQY8QujfaZlw65Yi9BX+YEgThq2+nCf0Jm8jpHCgmJBjQuwTpmLvSmjd+Hi9fzFQTCgZSJT+lBCiYCNwOciLxUDGlDoSxuIGtPh2ohZhyn+CUFdchpAShG7M4iAJoEsS2t6hnRxtcEKyTkPDAQjbL6o0GiHXEtren08o7EYgbPn/IH4zQxA+jUuYr/yVSOXjEEL/YfML2CXuUWPdNZ0AAAAASUVORK5CYII=",
                         4722, [198.26251, 166.52358, 138.69564, 119.19984], [0.55648, 0.47738, 0.54848, 0.62944],
                         30262908)
            elif (record == "SRR3581884"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581884", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/zJgayrdcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACW0lEQVRoge3YTZKsIAwAYBZOzuXCK8yss8r9j/BEREkICjZo6zPVVVNNQ8in4M8Y88Ybb7xxQvz8fn/8HR149cHNDijoOwymM6ZvVUqjIMzv24+fvusbVdIqSoRDPwqfcw619u5JQlDa+2cJKW4bt2BnuqFpPdUD0sLED98cqLRFEH/q6IZCbWc9XwhAYr/9B8K51y2FytVxBOpCeIXfGEVCeoqQbitUryp5QnJ97ycE7eoImhDNTYXEi4alkfe7UljyNi7rduvRXyen7/azKVQWdeMoECrX+lBo/6SFZOIzXiP269euFMmusnDgQrpAuJ9vd9msGXaEtC3EJsLo+TBKv/+UsWaIC5dCJNoV1t2I4pAp75+7QuBCFD+GQicj1IV0hlBJH6+88KxNHWC+SShrjGKhU1wotF+DOdSdwW5wa1FxX+JCFlEhxA9IlQBMCGFxZArRqH3LhFhNuDx5yEUBU/pxm9gebk9qUwLxrVdLSLWEa4FyKiFc1k2JUK6JEiHWEQJtC6elO84CwbqJqskTQvhrhpB1/0w4r1OZEMJZHFeb0ybIEvKSC4XHnUESMZcoISVcxwA/S1K45CsVjofXbpWSZ36XIyXEFNBvDD80GOVG+CMQCv0COS60CwjtjbMMCJ8L5yeeUMgMjPuhkCXKFi7/KBBCvYK4nDkFb1CEUb5iIYTjcsMn1YQUT5IS+sPbVMjH5enWp+JHCsGfdzT8DnFASGcKc4k2My4DPhbKhpbCzPcMUAYeF+oNr7CpUAPeR4gZwo2BNxDO1/8UDjbHlQhRpjtNGHf/B9kPE49MrZLKAAAAAElFTkSuQmCC",
                         7126, [300.5155, 252.40736, 210.22729, 180.67662], [0.57501, 0.56748, 0.6488, 0.67649],
                         30130352)
            elif (record == "SRR3581882"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581882", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCytCqgAYiRAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACT0lEQVRoge2XS5qsIAyFGdhZl4PaQvc4o+x/CdcXj5CgYImK1zOoKiEk5y8wnxrz6tWrVyfo5/f++tu78Oo/N1tQENv15jN+tCXC/NjedKbvu2pe6qiIcEL8VPNSRVBC+Bm2r+8a28MiwpFu3MamVETYZKcpImxSghC1qJZFTycEQUiX+KingTBCIjdzupkq+i8JcfluscmiHHoWIaAyliKkKwhL3nPU9SjH6FmESu9IEcI1hLJkEXQmIc2xVxAqJdMulAmFEG5FCLEXExMGF3pX0XJKQjS3JSR/aBNdBaPJ2xGKmtweOeuDP3mLhoQ4b7hKSKYK4WY+tSazBwSWSxo3nJCMu93ShFuWyhS5l6eMFNfs4EIQocROs7gkh1VC5MkOUpTPvZhSECA2MUWoGGeELlInJBsSlftK8dOTdeBfwbcIkXwEKLFXE8b5lkvyDFpJv2nLfJowtGx/04mEwpIgnEuSXDX/WicENutyJQnxeEKRzxLO/zU6VyhWzZ5REpJvV0ThrM01MqYIbcCxhFHX8FiEtEnoQj0C8hOuEGoYAbor99VmYpKQDHoryEvmEsZEuYQ8/itCCAl9LWcxm5B5AnZ1AOHO4wqC0PqHyEMAGy4OCLmnwwinufF87CQcKnJC3jdVORu231UnHB8Gdx5T8DVXHUg7U8AphLgQFiECc6URrgAGS/EMQnd/lBDanCpTCWE8UIdQj1oT2ELfEuoDlxMGD0qPJAR7tjB157VO6CtFNRsgxBxASC58CmF6YQOEGccU1HXtEM7tMQz9B1Z68kA0HCb0AAAAAElFTkSuQmCC",
                         8840, [363.24163, 305.09196, 254.1077, 218.38897], [0.5764, 0.57201, 0.65501, 0.70195],
                         30923021)
            elif (record == "SRR3581885"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581885", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/zJgayrdcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACbklEQVRoge3YS4KjIBAAUBdOnctFrjC9rlXd/whjo0D9UPCX6KQWnVYKqBcIprvrvvGNb3zjgvjz9/PjZ2vHd7+51QENuf3Q9d3rdVot5wQ15A6jb3SeVsspAYQN2UM/8oaTSjkpykJv+/b9a3iQ0DaMu7S/2yYtC72GcNLcXoilhrsGaUg8W28pRHsLrBBji5P+6YH2VlloGm4QzuH4K1SP/FsLna8v/7EQP1KIy821Qpjv48p4+6LlG38KVqv/mXO6XCkUM3kVro+Q3xfbH9S+m6ZzhCEtCFv+7KiqT9Zj766tKxBgzLFCqhfSJDz6k6jmny6AP3e9XcZjFMZyneJYyYFPU5frhGq8+YrahLFc+xx3hNRdLiR5GV5ahLmoX6He01YI8GZhKIMJ3YVhv4MQ6sLBCseUq4UoLlMZOcFMyc8hqhdGQkmIYrSDgsRcUCvMN6hJiFQv1JM2RD7S5wFFPditCoF1MUKZy9dkFNKyEA4S5sH1pogzHybkrXG2spCIFQSkD63qACOU1+mFOrvKMS3NvigE3pqFVBSy/H3CWEV6U3lBqdJx16Be5dRt6rBR6LxrWojhsbIt2OhysrReU6XhhyfELIztTGjP2XYh8Um2CefDxhWSLkULcxdAkQAqd4dQD7VXKCtIC7MulAlzWfnr+2ahn7NOy/O4wnS1MBVUCK3oIqGoaklYngryU/kDhbQgJHlVnIpqhI5os7CFCNKxSRhKvFaI9cKUvleI+sapwoZFTOkPFc4PLjxA6N94txBY/jOFtuNthFgFhFLHxwiLHZ8ihGLHhwg94H2E68T4r4+dQim4Umid/wDSEL4hA77JlwAAAABJRU5ErkJggg==",
                         5815, [274.96352, 230.94588, 192.35226, 165.3142], [0.60425, 0.5713, 0.65584, 0.69761],
                         26871995)
            elif (record == "SRR3581883"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581883", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCBghG+O6sJAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACTElEQVRoge3ZS3KDMAwGYC+ozsWCK7Rrr3T/IzTYGCRZBswrgkEznUlsbP1feKSdOvfWW2+9dUH9/Nqvv60Lv/3hauWVMcCKDbrOdc61x6Q5ocBrgzVC1zSu/fxYrYJQGy1V654vbNyjhU0wGhZqt1ylsOlay08aTYhVV6nxQkUImbDq2WqsCkIx+gotV4ZxDxR6OaYIh2PU7xZDpeUbhWRyRmj8ZCpCqBNa/xrJhb3l9kKSNY+HqhBLQu2m/X4hpFefUwNyskoIXxHKzFnhGD2/+JhwnANjwoWWJG4eHFYLMU0stDuhlOe35/PrhRiXGhMqPVk6IeQHZ0IUS3gXO0LP5lMsWBKiHSG5MpWmsF6IQohlYf8YPkOo/5Y0GUAVIntTFqImhIIQzxGqO2Iw4JhRHEKFgGXhMCeFOJ1MmqM/TJvZWcDjD+cuCONrTUhDUIPMpwp9WYjstj2oRKsBHIQ4CbG8Zk6YgEyIaTgPgv58IVJW/MDrhSDmhDCd2TwIP/yYArFhJgSlZ4gZl2tCnx5eMG0j3i8Ij7wRdwtTai6Uolqhdztr3ABEL4jvSDSt5bQG0idAhYpoo3CrFKbdZf4oHGMX4lAhy2RK6Nm2qUvM4DGvYanv/9AgQp7pMCGGo+v+eyOE01/U5QRKnPAKrhNufOSQnrzbDJCALhGGCwmw8plDT8QOoZcD5wjZynUFLNVdhDXXKQyH055bhPqABWHq9FghxE6py22EfpUO093zVCEUF95AuOoy1dbdR+iXeDC3br3Qy70uE+bEf6f9MtHepR+EAAAAAElFTkSuQmCC",
                         10595, [348.79261, 292.95601, 243.99981, 209.7019], [0.56427, 0.56107, 0.6443, 0.70027],
                         38597480)
            elif (record == "SRR3581881"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581881", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD+zADl3MYdAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACmklEQVRoge3YTZKsIAwAYBdOzuWirzBvnVXuf4TXiEACUQP+jFqmuqYKGxO+BlGn69544403Toif3+vHv9YT//rHNQdgReeh67t+OGgkRwWhve8X9+mG/rCxHBM1wmHoezeRdwoAInvvz6f/uIV62cDyUCkMnUDL4HgXXqXanvIF1gqbdxql/M6hXXGlMDSr9lhLGBKqv2pF1AlrdiBTXEwIuL9wPSNU7HpaaLvmrJBOE7K5vbmwqBSOI+tiT6csevXOpwhxOl5m2BYzQhBCe1Flvh1GJoCx7EnCorxvABNWFb2c0FUXKadVRmxprRdlm62yJJIQpj80LyyPb4xRyFNOYxmFQasUpbxFKV/eNf2IY0ICV+RoYZyUUsgKeWExzeP3WSssznKAUCWEfYRs2VEmBCGkOESUGbKbeFrTFiH5z7wwL1YRmIqGtCRTZkLXIIMw9FAGqAhh/BRC18knyKuZA8qLRRFSHLMfhSYEObwKoW/mS8cnwc1CmhOmWkCpEDFhufRYI7lWhRxYCL9XqE/QeiWCECIXIusjhbgqpFzI+4JYJcJ3tDDcFaSQZoUoUvHh8RS5EKhKSGGOZbU9hPyLTKjWXBamvjGPUSi6178Kg2AtCGlN6A745xhQhcA7NgvrZzImXReyWlmPdJZvoypEVrJV2PAqvCTkLUysfDjAEiwJs626RQgNV+OSkGTLLpSGqQmFqFJI6hPuOUI8R6g9uK4GxEpbhPGJZ0lYis4VwlYhHC/UHlyXA3cTEp4nrPn/0PS+MlbiNS8rVLtYhLRdGO4l1xKmccWn+2cJWeZ4M7+HEI3C+XNbhPqBY4TWSbyxEB8vtBFh/szrC03r9PlC9cQnCUE98TZCXAUunmgXSsGJQv86LJz/ATFTYcRJBSvlAAAAAElFTkSuQmCC",
                         8497, [282.87316, 237.5893, 197.88549, 170.06965], [0.61782, 0.60553, 0.69749, 0.68929],
                         38167977)
            elif (record == "SRR3581880"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581880", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCBghG+O6sJAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACeElEQVRoge3YS4KDIAwAUBZOzuXCK8w+q9z/CKOjkBDCR6u2WrOq8glPRLHOPfHEE0+cED+/nx+0teG7L25rAK2p3bvODcNRYzkmEiEUKne9G3ndkePZP4AwPqGPZfR9100TealYJRyGbuhvLfxfhxe7SQtCUAVT3E2oSi4a9M1CWvWq/Ngg7QjCpOSiYQgxlODZozkgIBUuMHiEq1NhaUN4WJhC8iW4b6otwpefBacKo0wW1zh3JaHqL30ZkcXZPAZw6PO8T4hJBaPV1jH465UX0klC/kC1hVtv0zahL9rlIaiEyyHw3UoGcfPGatxvU6bXk4UUC/Ve+AUhNQmXfHts30ClEkLkCpW1KUqtjzuVzkrreP1FwnJvTWEIycnlbglVG/mnUkVIVaHMl3xDNoe4vQtCfiTo0RSEldvXjz4vpD2EsqEevhSic0EYpZpOzFcJ5sMwc9ZjyWDkhLSbkDvXw5dCXhaGcJnhcRGO3YVZfFkYXVCo3BGlNP6nXmVzZvQuF4SkOvBCjC56k3Ca/pwQQabbT8j9QJwHtRBzQrFoMZ8ZZyG2CwudlYXIPyOiT5ARAr/MtBAtoXpjh96zQpJCfmWtDFgjREMIUiimOwh5WSKO9yT4JxELo6SWEP+/65JKVVpFyOP1eaAq5IvBJcBPinnU64WU2WtUgGKxLDmj8ekZFMuCm0Is5Kp8iGl/6hizQpFbJj5OyD9DBb/y8kKjP7P/3YU+EWWFOkkynM8X8uZdm9qFfqkcLbRrnSK0T3yAEL5DiGorfQEhrhVC1PBWwrm6GsNdhCA3J1cTtixEs911hFjzQandHYQZ4Goh6s5OE8Z9TPEHNplotc7eS/kAAAAASUVORK5CYII=",
                         6948, [232.85963, 195.58221, 162.89825, 140.00041], [0.58672, 0.55897, 0.63632, 0.69001],
                         37913237)
            elif (record == "SRR3581878"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581878", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD+zADl3MYdAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACgUlEQVRoge2YS3aFIAyGHdisi8HdQueZNPtfQhVFQxKqgPjo8T+dgCH5P3nIbde9evXq1Qn6+r6Vfg7NdvXLtYTVGVz36XpXnaaZsDZB7/rOuXojrQRYncL1vbsxYh4hWJ1umMJPf4ibFsojJKvTDX/uvoSEVm+K24ruP/c+aWxCEpMVguzoWwski+9MEcK/IVS9FKKxuSOlytP+CYTm8ZYx3DA9dNqEVnBzVRKSgunShObraK66hTMCigTwJ2Hd+yxSDqHasyAJwcPcizBn4ahQTujxJ0K9dC8ktLZGyoU+NxUh+ddwJuFmQpMw6lkvy9qfJoTTCXEjwCoaD1ofa+OCkDwhWYQYEmwZypRYV8bX3TrtywnhcsKphVGAKhoNGicmDNggJN8al/15hDLj3GKcW4Sjbb6LpPGIMOg8wqlm1J4K+QYuIaiGrc4GQpw/mYowMGHUShNaxepkEPqW3y7D3IB5J4mOTM4gCRckjJskyk55sAWhLDUT+g0z1qR4mbFhIsUhhDQTxsWKtOQQ9v1JgMHpWBMtwsieIsROPttJSKTveGXyE4XcAnvg89NMSAthZKcZITDCGkxYV0Jca3GzukAw7Oi3chAhewJYcLcJpZmPuFpwgylCYKOmjiXDSsic1RCWLNaQc4uQ1xKELE54tgjF0yxCKiCEnYS2MgiH7VRJiIn/DGyIjiBE2EOov/B5hOaPj12EDKuQcBwIW4TGHeYlNIvv+PHKBTHIIwghax4XQqgkRNHRjtC4nyfhkM0cr1lASOcRGlFJwuX2Nd4VKgntjmsJfaAY+BhC3AEI6YEv4Q0IdyxTE/AlvBEhlgE+iHD61LUnRJnrPEKewusXLyPc2AqJ0kMAAAAASUVORK5CYII=",
                         3349, [109.83585, 92.25273, 76.83628, 66.03576], [0.6073, 0.59557, 0.68935, 0.70546], 38743274)
            elif (record == "SRR3581879"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581879", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCytCqgAYiRAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACiElEQVRoge2XzXKFIAyFXdg8lwtfoV2zyvs/QlH5CSEIeMFWxjPTmQohOZ9I9E7Tq1evXt2gr+//r5+rC//65hYLaoKXaZ7mpZOTXsKKWA23TsvczUsfoSqPXZZZ4z2MEGoI13VeF/2oPkpVhMc57GWlk9KEUgvaCNe1o50OShNWbe4/VkSIqYmnCkcnhJhQ2RnFZj4t1TZdcdkbCWu+LVqWRVaYELa1xAvdpDPCxpZa5ytUmlBPtO01vNJxLqHqy/+C7iWk+Uyvht4NSCA0PvoT7oWREgq0H1uQCNFONCXk+UwXR9pihXabPLv51oyubuTEGGhPSEsJhCD0oiRHvm+dEKI1pHJJygWc0KQnVUAkDDyQi3xr9jvFxpsSugyYJkQSElUMR/SpNdfZl5l5nScJoQkh2ZRCQl6SbasmRGqTy6+2dyBD6N7+ZUCRMoQ4VRL6CMH4Jr+6lpDVLRVxjNw/qRP59woIyYMlN0LStex8f0L7vuOEprLZWfAhUQb3vyon1A+zyZUgVIzw6oGMCH2iw6Iyg9s4sIgdivpTJCBFaMYMoV6bIMQ2hBATYjCH1vT2JxH6JRDeJIkQ/KkAVy5H6BpXJ0KiC4SszZLleUJbDm38dULymUsAICZkAfvZJB6cJcVTB0iXCdVUJUolEUZ8RMbG9qMDMoRoX2M+H8uvfIaQEGm6/aKGD9B/El4k3ANCwiADBFdpQnrTQkKyAHZC1YgQw6tzQjrQi1A/BwdhzSbaQp8SKj7QhdB1gDpCNM37I0J5oDmhHHUmOCrZ52pYQuZhPEKvwQjdj+cHEqoiwO2X9ciEe2IlLhyE8GThGIRwsnAIQhnwOYR5xNN15YQhwZ2EQYpdv7eJqY3BXVb6AAAAAElFTkSuQmCC",
                         7295, [267.84304, 224.96528, 187.37108, 161.03321], [0.61413, 0.59659, 0.6808, 0.71257],
                         34607498)
            elif (record == "SRR3581877"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581877", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCTcyYUg6nkAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACjElEQVRoge3XORajMAwAUBeMzpUiV5ipVen+RxhCvEiWvLEl8KIiAa/6wWDi3C9+8YtfnBB//n5//Fvb8dM/bndQsQZVyfRw0+vjUgEjwsfknq+PS8WQcNbNvFsLp+n5cI/DkjkkykJAVTQv0Olql7AiJFRFy5Pm+Twyn/2DSkIwhJeMewkNDChhgH2JEIdaGznPQrAb3UhIZiNUFQcF1KvHktBCKArpO4TllWRsZqZQQ5iwNPiuAYVjXzIkNFrXhadcRL4hjwitCxBbJ77h8D2JXcTGrbIt+KMO1ExFIewrPJLIE4D8wZ7tZgylHyDvsd4tGkKKNb4dmHf1TsHvd707F4XmTSSFyaFaxRoM06DbHFBY7TwDvfREeq/NG1NFXYgNIewuJJR7W8h1yeBdg8XfO+SRfgFLCFw4D4qvrxOFBJaQkpB0NjAihJSyT78oRCmEnYRyJn/mhegOEFKvkKwH83BoIYbiReiTkVNxExd0CqkkpCgMSaDbGpBnz4ULJCaVJYNiCHq/i0OfkFrClMRWoCVMS7MqJHHiG/QKqSWkVLKH0LinYhYNIRhC0fTjwjx9kPOkOEdIXAjrhexdKJssXNIBIfAGkGriZENC3EUIiwErQuVbLxTdVwjRrYilny2kopCnwxymEEFMNiIkNhxYrRqypBL/NweE1CWM/0VAPqiOF6b3lVxoZqDTgeVvoxCKEYIwLC5aLaSYWz8QwkR8TimsAImNwYWBwIVMtEFotzpHmBXUhKXzojBVyq7N8D2KQpJnNWG4LgcLs6E6hLib0C74vDAOCtcQZl17gZSO7yUEPujNhRiPLyPs2S7YwJiOLiPEEaDqdw9hrd8VhK1lWuo2KpSCU4Wqw3+0ktEHi5GNOwAAAABJRU5ErkJggg==",
                         5772, [223.92925, 188.08145, 156.65095, 134.63126], [0.60137, 0.57747, 0.66059, 0.69563],
                         32752222)
            elif (record == "SRR3581876"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581876", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCSkyZLPzA/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACUElEQVRoge2YTZqDMAiGs3A4lwuvMLNmxf2PMDX+ESAarNrGx2/VJgjfayKmDeHRo0ePLtDP7/frb++Fn765xSJHbNeFLjTtWVbOEXgI29CEtm1OM3OKgLA8uGubpm2708ycIhfhsISVrSF5CPsN2u/UquQifDWZ+jqNIkQrqmYpQk9vrUGgCcfvIMZr1YtQLNpEKMdr1RohXm3mFN2MEPVQlpBqJLR6x0NYl6yfEZQhhIfwK2UQgkFIEG5PiFcSAv+sSzpMgPWGMwn7sDjhyF5iwE7Hh40Qx8mK0PBsE9I4cey5DVBWj6N8ZxkV8x5UNlpWZblVVxLa+YgRgo4Qf0Gweb3eKSENwRuEKsk7kpUGi8QY9A8dAc3uRmY/ToTkJDxkMeUdmwmn7NaznxIOXXD8KCIF4XSUyRAiHE8ou/PonRmwtg1JQlre10GFlhPGTLy2qLtHBiEGF2FvihOaxnEutuQ3A4nFExxAqLYg2YTmMxPia5N70oR8diaEIkLYT5j2SbnjZkLMEi4gewinnVhCuPNBTPukIkw7GnCL3EwRIfBZByFZycrFDEv7Q1Z8ixBlpCRkFJuEGPYoXog8bUoYz1mTsQ1CHqpNQTLrJDQKFyrWgYSQkrmE0LLDCImF6k2fzvoI0Yx6l5CU0oh+yRIOkxA1kZuQzFtbKF5z1YG2AzH0EkKwo1YF7DghCckqkiMUA4rQIPITZqKuIMwMfJoQQ/qquxshzGhzl7wfIWOrjBAfwty11RCWbNPKCXETEFauKydEmeoywuF0zP/E+wckQwKxYb6I6gAAAABJRU5ErkJggg==",
                         8401, [252.87471, 212.39317, 176.89991, 152.03392], [0.58056, 0.55478, 0.63724, 0.67968],
                         42213450)
            elif (record == "SRR3581875"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581875", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD+mQAiEG8MAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACrklEQVRoge3YTZakIAwAYBdOzuWirjC9zmZy/yNMKyAhJCgopdarLLpfyU/yidhUD8M3vvGNb7wh/vy9ffyYLf82Rl59c/cGmC2YXxqn4TX/eFQAGg1E+bVpHIdpGnvWc35YQtSEwzgrp47ldAjQIMO8hFrD9GtsX0NsHXgoqoTzEh4QGqlODC1DQYjZxddrfLU/paimsl91DaFkAFAgS19NeCwM4Zkre60QPl5ImM7o3+JWAS2h3S2wIB2EZAjPW8QaIdxSyP94o9J6rVDOGJ7OGiGbQDmpQDylxBe0AiGr4WDIGUkRblm5MO9Ls9BPaqYdLhaWU8KGkNYUcYXntKKr6/MOofvICth6YG8upDOEbLnz8u4gpPQz+kRLwmFTmEywISQ/5YVCEMLfH7hDCLG+rLxUSLaQeAGnBaRCCJn9r/m8k9ciK0uEWX1COB8SqSw8ftZg3xuccD2armBX1bIkcqfKWIQYhaI+SISwHBIJewvZohHxVUyE5Dal3KkyFiGZQsqEy0J2FfJ9dVwYZkCjPin082odUZ+hPriQVCFuCpHPVhLy1rVvL6F25FSF6FnoH0AlZ9yZqjDu9CYhDm0RZHwKkWytRwpFTiwJMd5LvJswVksi0pz8QlFIbcJWIkUhhZ3ULORnuoIwad0Srq+4kK7232GJEEpCJUxhcg8g3B8p2icEKcRqIVlCtQIeqM1kCKFVSOt0/kqFENhByVWhCW2gKYSkgxMqop1C5MK8SykoHiPcFEJI6Sclgij0A82QeuuFyb5tFfI56oVuYLxwtpC3xXG7gGGgqKFSCO8W7l7EU4Xui0FnYai0WogiZ4OQ7ihkmU4Q8qNqPyEkI/cLYxwQqhd6Cfet4hOFYuhG2AM/RFgY+BlCKAx8gHDHRny6cJOoA58kpPUw5eM/qZIEaiL29N4AAAAASUVORK5CYII=",
                         3996, [93.34969, 78.40577, 65.30329, 56.12392], [0.59382, 0.60138, 0.69043, 0.68048], 54392355)
            elif (record == "SRR3581874"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581874", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCTcyYUg6nkAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACi0lEQVRoge3YS5qkIAwAYBZOzuXCK8w+q9z/CCOggklQYpeIPZVFfyXyyK8Rq9q5b3zjG99oEH/+9h90deDTF7c2gAydp2mYxmG8K5d7wiQc3TD/GW5L5paw3cNxmLzzTQFkEYZb6Pq9h4BKG5HSWopxGNzYcZXWCZVOW8ybzOQ63mnqhGvVar17Dy1nksLl2LQFdRHktCeuLLRtQT0EoZLzXKS8dRGiaQt6IGRF/gdCYXEHQpDl21m8UwiGvjK9eiG6Vwi5JlhQTKkIQ69nhIb9W77Ig2WZIJQwbK18FXQthfl7V1mzZAaReBTGCYKQ4pSKkKCFcKlIuFcITwrj9ARpHZk131DSaZm4JoSCkG4Rsu29IOSL7hrgSEi5cJ7WC2NbMyG7HfEwSwDOhPmP2XMhzp9PhB8mst1PCklZk6O2QhCJAxf63kUhwg1COhCGzzXC+c6s7ayvJlxDJCLOWN7ExdgvBQWhzIZnljyo5I3p9PNCSq1z1VQLcSNg1hHys/XCdYoP/N4HthTE6WOm8eBJ4fUnMk3B1qJMSBuTtNLTDEK4T9kuvPh7H6gkXDOsFgLukvqskIAu3kS/0PLPO3HNwgFma7EeFUJW9JeFcef9kJDSCfJvN5LRVEipN5polOZav51pQjUKQn7Z9133Z43CfGRdAGXCtdSPMlDSyUaVhVtS7OwloaVMj4QkF9GE86MBFUIQIqsQ3bYZGIT7rC4K/UBoIQS911EAKaV0QUjnQilqK8zXvCTkDVyoiKzC7S1VK/Q7Z8zO4Y+F2EKYWauEtF55/4j8VKg3PCv0M0cYsoG/T8gHvkBY9SBq494jxHMglMf9EuHBuHrhXtBSGF6ORp1i6lmYTxHiH62svWXfpHxwAAAAAElFTkSuQmCC",
                         9229, [277.13124, 232.76658, 193.8687, 166.61748], [0.59104, 0.59162, 0.6784, 0.71215],
                         42315008)
            elif (record == "SRR3581872"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581872", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD+mQAiEG8MAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACqklEQVRoge2YO4LrIAxFKTxal4vZwkytSvtfwosNGImfwQgnmRdVhogrHX5ybMzHPvaxj91gXz+j9jusMM2U5giUdHRsWc1izKqq+VqE62LWdVlUNeG1EGcQkqrcqK1DhJjr5IRzlrNHdTuE2oTECacg9oh+fw/dNNn9SIQhlymItx10oAJh6AZguGpWOOiojQ50Tkg0gbB0lWEJ/XqgfPrPI9TeMP8tId+8pUkYDZzXVA8Wpw+hm7vo1/+E0EW+kxCZyw2Erq1NuGfPFcNM+u7d5VZC1WAJISH6OMhc6kGx+mveEk3bVt8wKaFtMSq6n3C85tORVbJAZBcxIcQzve4cKoTDJ3E7AoAmCIo4SKaTUJS2xuTSdykbQ4eQAmGSviO7TAiNyaU7fyphKH0oCCG4RDFFkycLWDlEAT9zodgOQXj5PO7Jo38UhNRIKP498p8BK4eym7B1R8RxmIgkBNdCCIQQTYJzDKFJECaJb4b+1OO2+NumzhNCQnitcJwSkid8OCFJF0wJxRLvniIveHgf99rjYfduJLxYGvm2k/l7Qt+5uUmPY1hEyBUiwm2+2M1t75g84TG3QW0uISSE4B54eokCiI88ZtdpJozV5hLKBfUOGBWzVEF+xooIvUeeMMkHdQkrgIJQpEdMD/xCcMAQ7SDEM0KrthFeqRg5QtlqISQpxwlJ3jySMJasENq56CADpzlISMgIIdy/GUJAlO1mQgo9HYR8ahKmOYSkQIh/lPB4seogBOLvtgOE9rKYTygSPTd8DmGp3UIohp6aK7JoooHDhMcbgTZhEG5DVCXMdkwjbCwY7jUCjdxVL0zIWdsIvej7EbYcRXhzwnNG7inHvAthdaP6u89GinL4I4RZezPCCmJpRC+hJKDbCcuM9QGFVsaeT3jImH+iyQYW5Z4GBgAAAABJRU5ErkJggg==",
                         3522, [123.22851, 103.50143, 86.20519, 74.08773], [0.61979, 0.61711, 0.70428, 0.74116],
                         36316453)
            elif (record == "SRR3581873"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581873", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCSkyZLPzA/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACZElEQVRoge2YS3qFIAxGGdisy4Fb6Dyj7H8J9cEjhKCg4r1a/0G/CgnJEZKrGvPq1atXF+jn9/tFex0/fXNLBVRhPAxmMF3fKpc2qiLsTWf6vmuWTBMBYbnx0I972A/NkmmiKkLTjXvYPXkPJ7rppN5KVYRdf79OA1R1Sm+oFcLc+M2UEpKfuTqXNvqXhPb6KQU6Eoq9ehoh5Qjv2WQxHcoS0rcTApaNPZkQ5j8aIdoJZYnGggpbLb24/9MylBLOrs8mJPMpQpnLikCzpc8SisJRnii0/h1bhekk72WQGawRYhNCsZ5/qQE2lKYdDbC7kiY+D4Ugq4RkCeOUjkoE8oQUDJTbGnmFCyVx7g/otmiVsKIqSiTWc9mEF9RNwjEpsFteSEhbhDLcIemEFFqGFpI3lGka0N2XJHFICOlaQlnZ+wjDzgvbBSkQWmOjnMXF7HxCuV6GUO3sfF4ntHye0F3mCAlPJ1RTMgsh6wmVhCDmEsLMmqMdNz9FIEJ5Qh8JtJjcKSEk//MRiEoJoymseZjKSYZKCNH/J70We591TCiJdhES7EVknyozhD5td2yShusI/fy5hDhb130XjwinzWHLYtxVXL0vU/WEmBLtI9xdkNMSwAlJ1A1SKus6dxFGGDOcShj8iuUeshVCNYM0HXtwNgiV9WoJfS+oA/QbcYCQiHgDbkjIHfcQhq8iLNoK4NWEvhXUIMZp7CdEOdCCkEC3WhM486OE+sDZhBmrIkIe8zmEQKH6bkaIhYC2elB0z6cQQtbxKYR5xxsQlhSi6ncfQtzAg1W/ckKUi11GOD8nRq8ZfwoCTH3NiGQoAAAAAElFTkSuQmCC",
                         8899, [299.23572, 251.33246, 209.33201, 179.90719], [0.58887, 0.57876, 0.66378, 0.70888],
                         37787924)
            elif (record == "SRR3581870"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581870", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCXmZnsxbRDAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACUklEQVRoge2ZQXqEIAyFWdici8VcoV2/Ve5/hDoiI4TIgBVHrG/RfmAg7wcEbI25devWrQP09X1+/Wxt+OnBLRZVxD4e5mGMbWWlkQjlsdYMxg62lZVGYpTHPuw4h9a2stJINYRmGOdwXKpdiSQhtKhZ9knY23uYEHImeLAd7jRVhF0qJYQW1rGIxaTdhN2J/zFhzXXuxKIMIcwVpBD68kWWa5YQR7tpIY0Q/gkOt9NAWcJLXG/yhDjcz/7SCNn/vgQhFxH2fDSqhPBPMNf1eTRi+qkSPmsoJPzgcl1N/W7U2X0H0ioh705YsNSVkK2ExJQnnB4sh/8e5wZBYyR69c0azmpqFX2p81vosYSaKVo+wVMvmdTJV59LET7PESIm3Od6I08fV+A8oQBh8n9lUYIpHA4uJIRPA/NnCcK502ilpHliwufL5UIU4+O6FYTQA93cScIdlqlIlRASa67DGlo8RVt96Hx2jKlAtEqIhFD0Vi+ZimNCQuA/duOaz85WCMf9SjoOpipDyLsRJjPkirPT8RVSCQMPCmEyvQqhsjA40lSjjEMp1sswy1QBIUNk1AihEIIkUVIuISQtqpSQw8tT1I0rcCKEHYSEFAbsR4g/EU4mcoTgVO4xpsMtJIwYZsKUqJpwGeaNhLxCKDxIO+TMxhUJoUJUT/gauwowilzFhJhDCgg53E/aEa5EbSbkuJQlxLGEKCf0nYYNNxHKilMRYgdCveIEhOTCKWp4GUL21wjZsAPCoq2GlHb9EGIbYF+Eyb/E3/PVE0L2dRhh1MWkXwrPrQDPpFEFAAAAAElFTkSuQmCC",
                         7482, [402.01862, 337.66132, 281.23436, 241.70256], [0.57854, 0.54983, 0.62697, 0.6823],
                         23648130)
            elif (record == "SRR3581871"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581871", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCZzP+FRvQ1AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACOUlEQVRoge3YS5aEIAwFUAbVWReD3kL3OKPsfwntB5GQxBJLbPHwRiUg5Po9pXM9PT09F+Tr5/75Pbrjfx/c3aGCsd/f7uWcr1VKnYApBKXt5bx/+XrV1AgQWh1Kox+E3lcsp0LKhcOl2lRMISkd403o27sPUe8whC0+aVDv0IQtBkzI44U2vbGYEHquMLwkurCZDMLszT7DoAubCXVh64GHCVG0PEwIKJsUIS0dcvjdw//xwdykCHHpwIsKOy1cGE+VLSz5hHNKlKusKHR74WcrEqaXHcEeIboz83Y2UIT2hzIx3SgMJQ+dEwx0IbkqQuMEJfeOKrRqEMK0ZMBpa5j7WiGbDnDahPUjg7riR0KyhJQLtU+nxclWCjLiwvwkgvLwUKfLhBSiPU804RknMz9DYZNWg3bZCOGyLQoPKEw3lshK4pClLVv3QOCQEHl5tI4WhdMxYRx/WMYKwKyBtYMYkjlSgzhgQFnF20IUR+RToBNLsSNJw2MHlGp2CyPpYuH0JkBVONeQlMIvmxRlCsV0+4Xk0r7pgXRIOK4IqhDmGnCtYvlpCOPznwmB3cMlwrQP5MIFQmLC/HxoiQeBnSmIByMRIghRsZBcfHeWyFIVE6LTKlDKgfGVngq5IQilqFwYj10BEMJoRUhxxLZwGuDyhlyoiMqFxqjNzAuFWy0T8q1tId5SCLw6aSoQ6g3VhLgLyGxPFMLjhfaODQj33Iig7deOEN8LN/ZrQUjTf5cNp7FTU8JkjjF/6BXRlkIFJdwAAAAASUVORK5CYII=",
                         9396, [496.05534, 416.64414, 347.01827, 298.23954], [0.57634, 0.56058, 0.64118, 0.67447],
                         24067897)
            elif (record == "SRR3581869"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581869", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDK/wAy1e5hAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACQklEQVRoge3YzX6DIAwAcA8uz+Whr7Cdc8r7P8JQUZMQFPzGmv3WrRog/yLUtqreeOONN06In9/7x9/ahle/uMkBmJ5bN9WnfSgrCNNzm7qumqY+rJZjIkv4cb/up6iAHKGbQjeBhc1hltDh3BSWLkQry0fd1J+msJ0GgEgeITux2PgCIb3C0iMuzLnXuXN8pRD934dcrnNCPLuY7YHhIYoJoUShtbJe4bkBG9d+sHdAXNiuz/OJi0J23pgvdX8GXb4hJJ98gdDYv2URNCIpFGoLRYVt00uE1sqIC4NXQ5dM4JLBEroz/Yl93xGXbyEShOOF2JcpUydiK+iEaAv93O48iUlCY2LYeVZuWDhwoZcRxYRwgNDuDqbdw1oZfPNAVpRRuBQSD12IS6NDhKI/f43R9CWDJeTl8aKWhAJoCIl3tldoYf+MCY0hxXUbCGUuL/kSoe6PRiGxjNVCulwIeij/rDvaz6Mx5tTI7VOBkG9CsuRs4Q5vG8FQffddKe18wqJQFAUqV5WcLOxvbzDre3ERapGxfoAJ/al5oTR4IYjENUJsX7v1wnYg/5lNjgXkhWwokClpQqqss3lCIrYZrBCCEKKsiL1tjf/6hBShIcoV9jsUrN1zYBpTDqYqCMsBfe94mBCGh1VEQ0jy2YzQX0BHC1XLzGAtHyYEv/q2Cem+QhjyNwpRHzhUmLObDkLYKLQP3EE45D9S2K2/YTA+5lOEMMHUmAUIMUUYb/gQIcQbFiAkRPPLsCVgthB1V6cJw/R/G9Qwc5ZA/rAAAAAASUVORK5CYII=",
                         13619, [514.86698, 432.4443, 360.17805, 309.54951], [0.59139, 0.57073, 0.65465, 0.70923],
                         33610537)
            elif (record == "SRR3581868"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581868", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD//2a0pA13AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACaklEQVRoge2ZQXaEIAyGXdicy0Wv0K6zae5/hIoik4SgoKjDPP83fZ1hAvxfIoht1z169OjRBfr6eX/9/u3seHdyswWYH9sP3XfXDWdZOUklhEPfjz/DWVZOEmFB8Ig4NFdDTYhW0KKxhA0Skvq8Ejv0bhUOZ9qpLyghnHaa/vtUQ9VVRNikHsLmNQJqQrzFyGlKE8LlXs5RmrDJWmLc9BC2JTC2ySQhtU8Ivs0mjNtbkCwLTZCfRshNJwknRNeO19gqeUBdFTLT7hfNL4PQNUzBtaZeV7VM0otwytq7EMI6YfLgEZXeWX4RwpQ697IIPTlesRJhgzDpYYtwej+irBFW3mvs9Ub86G8ULMkfuYsJaW4yCf1XqdF3KXqKmadzzQuZkQTpAcKxJTYuCGf/aUJUhFVO4TpjM45zsdyoIc6puoYp3NRt44qQkoSLltGrbOiK0JeUzxTfutQdjl3TVQmxzoaupvIFYzNBvDA0s0hGxL6XEPDAIfXVT/snQejek4roVFaQjaFHA2E5n5DmaH2tZAte/USKu3BoAjaV4UY0+J3DJJRFKSDEMDB2OxQTis+CEMVCYmb8IwJGS/ZNCJd+cjLwHjghJAgpSTh2B020gxDMqDyxftrBPCyyqTYIJUNI0FFC0sk/TEjGJBK2gBBrEIIdlU/or6NNQhkAjCNNSLcR8oNH+KtIGeFYH9wmjImKCTERtS5a7jMHCCmk9ypCzAcEYoeUA4R4BSFjLSfkHfcQ2g03E0I4fn0ooRt5ubZAdGyAMGurAaNfO4SYQZju1wJhRhHB6tYQIW39N8MELCZEPdSFhDr8H2rhKkV1M/8xAAAAAElFTkSuQmCC",
                         5708, [269.42162, 226.29116, 188.47539, 161.98229], [0.59139, 0.56954, 0.65485, 0.70339],
                         26920107)
            elif (record == "SRR3581866"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581866", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDo6EaTIBzcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACZ0lEQVRoge3WTZqDIAwGYBed71wueoWZdVa5/xFGQRBCUNBi1ccsZixGyCs/bdc98cQTTxwQP7/nj7+tD3775RYHqDz31Xfv8c+1gqk8t3+9ur5/NaulTdQIR2Lfv1uV0iikkLQkF2YKLzaHYI4bWM8zMS7Qvruz8JInTZXwioFHeK2gtGkAZoQ1vwROE5Q23Uuo1awIKf5/ZGDnFqkS8hWF0tIhL8TphVDaEiGPbVnhF4hJhQuhrEjxvYDDhav9aQsnW0UqlOtxQYgmwvXDeaeQRc2MjJAHIWT2ByInnDeUNmYyLf6GTDU1h9nWoAmJmwj1/oYfVa4daTGKkNUb7vFwkLxwaLHJakmbQz9GWAjlmPFTDGJfpjhNQ6FZL0vCKeRoeyK3sSuFPiMtXBXysUJtEgOhNiaCqaJlIQshZoiWqN3ZEMvli0q1MeFahprHs9F1Il8YSAqRdWhC7fdDSYDzwuloTYRhTnDbEOZ1LIVi3YEXZiq5M76PeNgaYXaCbDG2Utv/unBOgEhNhFHkheT7biw014pwnqp5Vj4vNCcudVVBgZDCbn0/sB9spbYKRRisJPHa7RUS0QYh2xO3CujS80JOhISwHJQIeb+QbS4qhXDpwZjxYIiErAj5IKHd3uC6ZYqIpQvNnfDEoyhjKn1FSJ8Szk8WC4Mp0IQJS5YzvdQ1YSqqFQYvuULo0xUhx5+WhVgRKqJDhPAj7RO6rdlWiExWkRB7hbKhhTCXteCb67q70F1sF+oN3xb6de1HuYyQyoC5B+8iRPbBR3gCYclG1IAXEtLtheuTqAKrhSS7Ok4YdmHiH4DIqo3kYl0IAAAAAElFTkSuQmCC",
                         6603, [322.7782, 271.10613, 225.80128, 194.06145], [0.6103, 0.59194, 0.6828, 0.70466],
                         25993357)
            elif (record == "SRR3581867"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581867", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD//2a0pA13AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACW0lEQVRoge3YS3KEIBAAUBeTPpeLXCFZ96rvf4QEkV83H4HogLErNVUSfk8adGZZnnjiiScuiI+v8eO7teG7b+7hADxe97Uun+pjruBCjFXaY329lnV9nTibM4KQXecqqzX8/ZgqgBgpK1RruEy2hlXCKbO0SjjlSVOXpTPG/YV0KyHKIpDCSK1ZIvb28p+FcPZ0TojY6qSFM67lzYQoi7hFRVIIowtBatiTD/TfjYTcAtujjxJCKR8tpFBZ0L9OCUm3pzcsYs35LZfguFAVnCAs/5hQtTPExNWUgzIClZBRIZwjLKa9eEfOBF8wI0S/AqSEFOugO7hQrmls76fMeSFomeowKxRT6Ao+I/HyFD3dEvcZSkIoCPf/1wBKwWe0pySpVQKwI8tmwZXJBLHpUsKIY6vmC2t+bkwH8JH22Wx7RR8x0Z3hNUItRMeRI9ineUFoQncmRm0JkVZOqDIJE3sfvOmRnjg6jt/d4k3Z5OBBoTqP+oV8KDBCt1diGwNsJpnT0Rei3cNkFq1BuN1jbJaZlgkhWCFGhbbInY6BMOy+TUg9QrC954SUFIInDAxGSF69DiGIW3scGAoxFJI32n66oejAPzyZkECIKoWk60Lr0x/cmHys3eMJ+T2wrTJCKaoXhi27hSyrkHhcLcQ/F4ZXkQgGGldIXl/MVBK6pniFkJZErWxAwGoSwtYQLhCmapWE9mt0h5DGFZqR/DGbhLxgBOHvm6N9rQ/O/xYhDihUPYdfXHqE8YLThHhUGG/4CAcQHknTGHAiIZaFmXYzCMtEyDSbQrif3g76AyLVV4epcwZnAAAAAElFTkSuQmCC",
                         5862, [311.39278, 261.54335, 217.83655, 187.21629], [0.60016, 0.57447, 0.66226, 0.70056],
                         23920075)
            elif (record == "SRR3581865"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581865", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDo6EaTIBzcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACW0lEQVRoge3ZQXaDIBAAUBbpnMtFrtCuZ9O5/xEaBGSAwQDBxmmd9/oqiGR+QMTWmCuuuOKKX4iPz+b4+m5ve47o/TIAD/iGp8di7ua2jF1LNDWVY+K23Mzy+BkJJMK52RwRy2IevDEhqRDe73aiLiOXgg6hsbN0bAitUMONaFcaO5D9oUU4HpdQf1igiqVmOP6jUMcu7kkwhCB0RfjNhKbHuragP8yE4IQAqom7QlckULnCovsFVuhnqiS0NgKN608YlnWYuJCSRoqFgbKangtjrZrllQuhJlyLaJJaLfckcGG4+fjxVgF/T8gE/pyrXOsRe3aub3vIPIaBdoS4NXRlYMK+vfnb7tlOYRhJJOwUvm0Jfiz+I8IwYYu8a+b2h8zsTRPtC7eEgQmJCXPRBOHk5csL0WwI9PU7QtgRVvJrF85+8WZCahZuzEIItfyECS0HzH4t9UIyFaErQQkMwjSdPaFwRqgqhS+OaaOwBM4QCrcclA39R+Dg8ybOxqDApD4tCZF8LIgjFXqQOO7ymHxdWHybbbElOkeYpEfVM71CnCOsmJ4JC4erAOO2BX4EhMQTYbqi5TmiGf43A8Q8t8NZQp8rExYJUiksugyvPi8LMR6NCPk7l69Y+wasCwGZMFnSTin0U5IJQ79VIfs0e9rE9bxohxOEMQaF619A0grWnz9Dcc9JudDeKScXkskrciFGEfKzeR6FkE4ilCswKeaiRiEhsOYdIWV8amE3UY8w2yS2vmJlHZ9amPeOTUIx45MLa88UIbJeFQmBX1r3IdWiU5gKjhfWmtn4AaZx4KJ2My73AAAAAElFTkSuQmCC",
                         5836, [265.88131, 223.3176, 185.99875, 159.85378], [0.52993, 0.57636, 0.65997, 0.55553],
                         27890271)
            elif (record == "SRR3581864"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581864", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDo6EaTIBzcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACYklEQVRoge2YS5KEIAyGXTg5FwuvMLPOKvc/wjSKkITQBU7ja/yrq0sxkP+TZzkMjx49erSDvr7Pr5+tFY9+udUCbAh2w+T/rqUWwtGNgxtdLyudRFgf65zvQdfJSS+1EE7TMF5ulEIL4dKBro+TXsoI0Ypa5cbp9evnpoOANCGtT/a20kkvQpIl623T6D2xbkaIedE/JmxbY08i6/RyXUJrJZSES0SRMFtjzyarvyQLhbKMcK6Z7yJnUxUhvCVU5Qep6AKMJ9wz+qpUJszLD1LRheWPl1EFIX7CYZOMfim5AIMQomnwPfi69r9rEaYF1FgoSBLSjAcWIcD8Ng4gNPpFukjPjWlExAhnAjiU0FgLjX4BawOYryoJySD0JUtw7uGDikeKtyNPE8bg3DhwwghXIAzS6f4omSiZobU/jZScEPlSoo2TIhRSPnoRgiakyLA8MqaMIOR29TSCwwhZG+qkG9r3wyn0p0XoJ5NyhhEBedzAPdcS/n3P51SyvXXArRMGxUoh3CzxJqGm35+QJCGzHwlTLoMwuYDoOhFSfIOJqJFQpmsXpNZBpcoIcTByMkK8P6EwtTSHZyLUDcKSmVlbL0P8/EmCEUpTnybc+mURUhuKMFjQVhghAfKONwkNog2E6JesjWsOpJwqV7CAlIu9m/6EIcnmTxosp8y1OjgDof+HboSWUsCgCzoQLvsxUCMixMmkCeOXvBpC3IOwFPVeVCaUd1clBGIHTc3UQGgXPISbCbGOLh4w70oIbAdAXvEuhFCseAHCKsT7E5brXYEwfk8pCsxarYSom9qRkDUx6xe+yXJrfay2qwAAAABJRU5ErkJggg==",
                         6607, [355.28935, 298.41272, 248.54464, 213.60788], [0.58764, 0.58251, 0.67, 0.72041],
                         23629111)
            elif (record == "SRR3581862"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581862", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDT0zLQxEywAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACpklEQVRoge3YS3brIAwAUA/8tC4PsoXXsUba/xLqHyCBZIMNxOmJ2p76A0jXH+xkGL7xjW98o0P8+//4+Pm52vPdBzc3gAoaj9P4ml6vZsU0iSLhNM5/U6tS2gQQYUHzaRiH19SoFjVKToAahcJx/ll++0Vn4XyVTuul2i86C8dpuU6nu0lLwhZi3gAHwttH70JAWgVaTa0dcTtTWDTJVgol520hmcKyKahOUCIE+xLLPAOPEkKBUGmrx9uFwG495ZYhC6IL021gCpcd+p7LoQ5H7N4rFKbjKffxIoy2ot9RWahPDRROhna4WwgpZKs7m+q1bkLyxWDcySgiLXwdgT9uwqBR18HtqC5EUc22tgq3+UQRQrGQ9afl+aoJ0Q2NdecaQ0jZQvE6oAp9/3Xwc2Hl2TTKtD8HmFBJKYSie56QegrjC26fYRKhyCnKE/3PhLORAGhzRK3Q1dNciK7SsBjlvCHccD2F8XjZQmQryHonwpWztViELKJ2ON+f2F5InLUuZwh9raowtBa+VAh+Pw7VAk6E5BfjopGvmMMNBUJ7153QhMRLMYX7A1qetn245AHyRmEyXiIEJScT4i5k8wSKN0G4JMShVsSp4G8IITzeDCFLJYWYCPeC+FzvX7WDqJOQQmLktSZCZKlEOeydTghdTeCOSizqIwQ35jIErzUWilSKEM6EqejdQuRtDoXrfxAbUqEi6iYMLF0Y+xQhdRFee1yQKeQf563wDbCjEIuFFMYSwmTue4QQS78cdh3hrjDa0ESI61cDZfcjuEF5zscKKf1QcE8o1w6F1FOYf5kie8lWTQVCfUN1odbGDnKvX+jTPF0IoudZLK3dC6Ts+Vyh0epcGOX8S8I4PkaIOUK7Y75QCh4mPOj4AcJzIhz1+wRheiv+AsKB7rqIM4ksAAAAAElFTkSuQmCC",
                         6527, [332.53167, 279.29821, 232.62438, 199.92546], [0.5769, 0.58282, 0.66354, 0.69991],
                         24940541)
            elif (record == "SRR3581863"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581863", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDo6EaTIBzcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACYklEQVRoge3YS3aFIAwAUAY263LgFtpxRtn/EqookPARRfDhO2bQKoLkikZbpd544403boif3/7jr3Tgpy/u4SA83neahmkcxlaptAk4IxzVsPzoNzDSFghjnUzMCzipcayVT/UAjLQBkWyJdHKxLOE01EupchwTUtjJxjgM8xL2K4w9cTPwhHAuMpPquNJcF/Yer3DrdUsuTSKoKVvjK3xOfL0QTwqheUa1Y6ZESg2FQpS/HxPLYkUWMSnE7oXo7a9CvzUphNiCdxXBN+j3CQn8BifU/PV4X0LIFXJwBTAonIGQNDIljJal5pEXurQuCiFalppHVsgufLAGJIX6ClBMovc7FpLbxOAYE+rttS0UwiqUJ2gWbP7sVXXpgp8ghEJKCc0RVHcE+0dRtryxC+9nvgGNkDJCukFo3meLEExemUV0QsgJ9T58VrilqoVks/QnFQ07QvKEIrxTNiPKOkLstUSugPtzsoZtSVCZvuwYyJw/JBQnNHfk9rggmpn9QW4Mz6qSsO77AsQJzR25TAPrXLHLCmxMl0LwTIEQ2FwxIe0LwTt2WrieTM55DujdZDtCTAlXBchqWVV44XEMhMiOHBGCzQ8wIhTfcMVC0h85xULi23YPzOlDoVdwrVAa7K6KHT0l1EmWPpGBSWYkhSIdsO+SjNAXFQvLiOzscja7TWGYFG8RkqvmWCrEHSHtCekWIapEr5yMzYM7QqQw7FDkz24rIRUJ4bAwFm7oLcJUrwyQ1YkLQuxRCO6PSzPLBaHf0FaIB4GJgSXCeMNnhemBDxAeuk2fLcQy4IOEW/Vm0H9rVwSn2TB9iwAAAABJRU5ErkJggg==",
                         7821, [357.31614, 300.11505, 249.96249, 214.82643], [0.55215, 0.54895, 0.63179, 0.68011],
                         27812173)
            elif (record == "SRR3581861"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581861", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDT0zLQxEywAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACR0lEQVRoge3XTZaDIAwAYBZOzuXCK8yss8r9jzBajCT8FbQ44phF36tGkg9aSo154oknnjghvr6vHz97H/zryS0OqMgdRjMtL30FYXnuOAxmHIdmvbSJGqEZhmEcp1atNApfiLEkjnFZws7WEGqEi200vQspkzxNHe40VcIuA8gj3U04A/+vEE9upVFEhLjewbN7aRM3E2J4KSnEqrPOVQLlG3viTgnn62i6C/25m99BVnjxTTX2LdLXZgHdTqh6tkIKhWRzLy7EWH+3EPLSRfuTQsgI0VghtunxSMB2yIwJ1fb4WqP5fWdCkkKfuPTsmiYbEBMS2PtoTovSUsTLFGncmuxIcDlhupbqzq3SOyHmhbQOlSz76QDXmB/KXi4kvIyQFhV/uyDcPZSQckJQQhXekJuQy37AkR7oVYVrRfZHKRSGo0JOQL/GgYj+RAdCvxbIp0RT7vMqU8uFHGjsn4wPLGNQCcSvEm2vPlEK5bT7wuWUvVO45B5ZRp6coH03fE5IhUJCEHd3CPef4PjJoJQbnmtFhO4hyArlMLVCskJduALIO7JfChJCXUkIeZGEcN4RwRdVCtdNAIOkwhAz7dcCN4FauJ3KioSBaJ8wmNomQpAp9jZIoeoE+Jmjwq1snZDHDIXbMK9bqtgboTaswlBUKyRIZGUD0kLxzyAVYgLeCSOiamEqKxuUEVKFEK8sFJC7CVGeGQ8K4xf+WAi867s63QixDMgbJG5D3Uuo0uGGQjmwPoP0ICz5IkLsuX6EuA/YkTDM/gXlaxnvHtzdwAAAAABJRU5ErkJggg==",
                         4277, [206.62061, 173.54367, 144.5426, 124.22492], [0.57782, 0.54877, 0.63428, 0.67854],
                         26302127)
            elif (record == "SRR3581860"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581860", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDLyzJA6iYhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACiElEQVRoge2YSXKDMBBFWZA+FwtfIVn3qu9/hDAJ9SSQMGDh4qeSYA2t/zRaNM2jR48eXaCf3/r1t7fipzs3W1RQtu3aV9d2Z1k5R0CYX7hr+9/uLCsnCahoEPufmhHRJoEhDIXAi9D1hK/2UFOHCm1SD5gidEoPk3ScqpXKeAaPcP6I3vp8vYZR7I63dpCKCKlkB6pFJYRwS0LjmYahuiuht09YQrwbIfPqEuqTrzpC94Tiil7dc1ymwZiQIqTPEG59+ygnRIcQp/qVExrffZLaNmmciSuEJd/m3hGbmjmEOD8Zf6NnPi5EU9LnCaMp5xrA95ahB0InWIOccIxJi1RIbC4lZFTe9sZSpl1j2QlvSmgXF8ZHxrBNiGlCCqWxOVZ+vEjodSvfMme7mCirCJdFeB2hd0RPA8MtqkK0n5BWCKGhMwjdac8IvUZXCWXZAkIMhKq1N+W/L9GExs0+Qj5HnZgh23NUqhAD9AkGsTlBYNwIZ0nCeVQWQiETM5GzR8viA9SWcGmOPepuHXIFQZKQ515HCCQ3Sm5p/sRsOYSwuIieXUIQufmE2LwnoPQUpLhpc9idhMpyLYQYrShYYSZJKG4alRCiyEKxfBQhZhAiGKJqCedrTrQz/a+ecIyBPKwiRLLifbNBSAcR4vbbhRVCsVHqlbNKiNuElqiQcCxPOwgxRYiS0FPMvoYQhpffpdOVX1MlYWjMGzxLCOcTTo1A4dkPtEWoHCQI8RJCmgixkJDZqJwQwp8SwtCSR+g6SBDSFYSqZpYglOc1ZZwVQA1UHSGwoXOZqiXMm6ZDZB3h+wj1QfB9hFq3IcQcwnTFGxDmDCJ49e5DiJuAa/XyCSXBlYTsOjbrH4hy2XdIX6pzAAAAAElFTkSuQmCC",
                         4752, [246.22731, 206.80991, 172.24968, 148.03735], [0.5776, 0.58077, 0.66631, 0.70835],
                         24522542)
            elif (record == "SRR3581859"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581859", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDLyzJA6iYhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACcElEQVRoge3XXZKDIAwAYB7cnMuHXmHf85T7H2G18hNIUCj+FNfMdKYKIXxS0RrzxBNPPHFC/Px+f9CniVdf3NIAqug8jOZlXq/DJnNI5IVKwzgMZjTDkfPZP7JCIJQnJ+I4GbuKOuG0hN0JqUY4Dsunp4CcEEkRvneauwhJE/YY/0KIasNdhCAhdk0vEcIBQyrC5fj2QqXhhIBWIsohJ0iy1VwqrHlJ1kLma0JyDdhYrj5qhIDKyUIhmh6E2vSU/K8TltfsUygmkw/1YsRCskNKIZkzhXz73CwaWjNCfnJb2LqxlQXfMbaKsr7K6yYQF+KakE4VUvimFEV+wADKcke/u5lr+10ldNc7CEkTxncWAe8sRvRCQLDt1wvZL0sXIk8h4J3FiJ64COdlzAiR994nAJNC9kaicENpQkiEfpE2hBRF3G85pd4TLSE2Z3sshJikYZRCiOgJSQmWXixEs1uIKdljdloXEv8+NYf35iYh7i4UlZgQ33cbbAmJdVCEfMrVwh3+t4nZMyHNQqwXRl15a73w08Wcdz67+2WEto79iGkDHSz0/euE4J7T02M3EvJS0ZXMCaMcReh/XBCnbwupSejHZGOk0w80N7WccBkL/KwjYXjE1wrT/jsJk41RjXIhGSmqFS7/9z8VghS6gfLAGiHuJAyJZQGuP6/5kRBOEFJUplwY3npV4QowLH8s9LcsRgO0C8Ftq6U+9rLbKHQ7rWbYUej3uFKgTcgJ1RnkhOmJY4R6r1zAlpBWiyigbxOSE2LyltGBEEuArFKSeD9hmngXYT6xA2EJcSWvB+H739wqENS0WiGmQ50nFL3/AFAxTGspIIXXAAAAAElFTkSuQmCC",
                         5984, [291.31223, 244.6774, 203.78909, 175.14341], [0.57587, 0.57356, 0.65747, 0.68018],
                         26101059)
            elif (record == "SRR3581858"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581858", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/2ULgAcEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACh0lEQVRoge3XMZqsIAwAYAs357LwCvvqVLn/EZ6jIEkICiiO7meaHRFCfhRdu+6NN95444L4+b1//Ksd+O3FzQ4o6Tx0fdcPjSppFVTQd8KN3dA3q6VJQFJIGDUNQz/x/ooQDOE49uMw3aqPiiLhsg9bltMgIog/TgrHsXFJBwKNtqSQLOHdA422lJC+ISx6c1njrS0HpFpf4ZECdjuUvJxzx9OFwt36o+UuDEsIFwrxLkJyf84WZpQfFVM8BVrTXiVUGd2mBEh3KQ4wZrCE6NoPbnsdWrgc0blCPp5c09eFxJr2JmUJEo/NpQdgd70QlJBqhOysdbW5EG8gnA+J7Z3dScVqYHQWg5D80plC8ieiHEeC1FReyKbRXeY2mWPdtZaQmBCyhKdexH0hmUIMv4EJjfVXwikVpITohVGS+oiWLAgptMRzKqFYDmsKdD/nvtN2/K6Q5BLbQpJDEPlwXXkQ+mS2kBoIdfkghJ+nO1hCiITEh8dTYDg9dzHu/DOFEBKQrB+WEtEVEG6bDSFPEQuRl5wt9Kdqv9v85QnlrRnnA1jrqBIiL0wsYb7Q9a8UfpJsCnkd+iqXCQFtoZh0Q1j52vgkwfA1xiejKFD1CJUuvwwhhedQqRC1EKuEPAdtVZAUhoaUUOfLFLId0lX9x89VmUJZDuC8NbjQj0GR4AwhxH12AsI3ZkK4AQxvA5RCkeG4kJ07V0jyKF+43sV3ELr+cFgIsqGJ0K9jCdEviZjztkLydwfmC11SOWeFkPBSYe5FBPfqRlVDjdBuOF1o90qGf7GtD4bbCxO9doUhHiPETGBi4F8RQnLgK3yKMD3wAcKcR4057jlC3OHB5rh8Iepklwnji/gfarvRa/Uj0LUAAAAASUVORK5CYII=",
                         7509, [389.73182, 327.34146, 272.63906, 234.31547], [0.59938, 0.59274, 0.67983, 0.70736],
                         24481696)
            elif (record == "SRR3581857"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581857", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/XV2Znjo4AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACdUlEQVRoge2YTZqDIAyGWTg5lwuvMLPOKvc/wlgVCZigILG1j1n0UfL3vUDF1rnHHnvssQvs5/fj7a86892Te9SgJLjru6EfBistNgZYENx33fhhpMTKgEqixzV0Q28kxcjKCKcl7Ky02FgR4WuX9v03E3a9G14ft7KyXXpHo4fw7gZE+G4NzLB9SZ2w6FWgkYHBjsoQvmH7WuwoupJw9x24hPDgHgOd0GI6RQmxnLSpKuI0ITYnBBQrAgbGUU0yC/pOEotto2Fbc8nUF7fWkgVauIg/XSRCTYXkEObjvoSiIxBiGLqOMGklEEpqdELBsw6GL+kbCUOfDCFs5GU9nJC0mkvnzEO21lLCuQEbpckwk8NsjxAyhOQd6FoaJPJrCCH3lXVs4wFlCdFZEKby7QlxLZpGoTMgBIGQvIL5SNwjhPxjd3x2McLxitaicZwR4UY+JyQSQwRCED2LHyNC0gnJtSJMdlXUa7pDP45un3B2k+Dx3RLCtWgcFwjPI06EGOSxkvMTgCCM+8tETEjh/kUfpMExIWiEyJe5Fmy+QH/4UqJ/auChNEKmAuJJ8oRsD28JX3cyIZ0kjCb6GOHoqCHkJzzzrrVI4uCE2ICQvbuwZpxtcaRzkBKGdQmeakJqQ8h7xvq3gIRxBOdQCRmRQriZNC8FzxCCz5QI4zvJvOQ1bB5YZ0Am1O53COsQmxFCNNCWUPGVEUazFFf8IMK5XNk/i54w6llDGA8YEc4/NMr+d4Ml7xyhOmBACJuYvPm8+xCGxEN8ntB3+TZCWA62UOfjCf3BcYwvnNu3IVSiNEIh8TaE+BBqyV9EmE08ThgTXEgoIP4DSFdXN2bfxLQAAAAASUVORK5CYII=",
                         5436, [206.45406, 173.40378, 144.42609, 124.12479], [0.57894, 0.59719, 0.68359, 0.70513],
                         33456560)
            elif (record == "SRR3581856"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581856", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/2ULgAcEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACT0lEQVRoge3YS5qDIAwAYBdOzuWiV5h9NpP7H2FoBUlCqGCpFWsW7SfyyK9AmRmGK6644ood4ue34/hbuf/ph/t6UFo0TsN4/zhHgCGcxuF2/zhHAGFaOI2ON+2dymsBkLthCcfxdp+oXYU1Gf0NTMrcBB27m6VZIRnCLneanBAtYZfxDUKUBf6auhSiUXYqoTkhTy8EJ5ElXyAk/3UJDxjWKcUSki9Pax89aoW5084xAjApsYQGZH55hxdaGCwWkr6RPq+PRwZjFh5ImPtLzqpKiEnRkvMjYVKFIZhw6WKvTafiSRqriOVcKqRYtiHdlbA0q08Sl7dsCKlCSFIIbYQoerEX0vMe3F4SGq0KaRZSRohvEKpegjCuPXP7RtWFf4vWXs+FFLadFSEuHTcggtzpqEwo2sSVZghBCKlaiMOrQVq45MpG1sOAbpMVzhkXC2k3IUlhuj8iv3gipFRIAGVCsoauDp2Tv5yFIPMXjfJCUdcSusYlQmgj1J0E4ePLLQu5MGSl7ULICkl11kgYcwqvNAjD0k+nngLWCa3cmwrt9LSQeEJ5YZIUFwK/u02IQ32AEsVeQAiTMXkyyC9kUihrbhCS7rgWyA9+YrA5Bfd7vi7UXTChIaoV4ktCIz1Sl2lkhCDnYTMhm0dbhf4kKQdTGVhCkOf/sNe+QahHrhTKH1V9ZcXSOExhLxQ9tBPCJmH8f11qKhNCvqCxkG3kNUCKh5SOhFjGW46Cst1xhTHKhK7eXFu160FYNE2B284oBKNZR0I8vXCVafn6E/L6/ywNFzz9ypUkAAAAAElFTkSuQmCC",
                         4903, [218.88707, 183.84645, 153.12367, 131.59979], [0.56986, 0.55973, 0.64039, 0.6943],
                         28462107)
            elif (record == "SRR3581855"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581855", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDK/wAy1e5hAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACVUlEQVRoge3YSXqtIBAGUAY3tS4HbiEZ1+jf/xJiQ1M0KqgYMVbel/AAsY7AlUSpN954440L4uv79vGz+8q/fri5QVzSu/v0nerqZFIrCAWdP91n/FYrlzpRJBznUHVdpVQqRaFw+Nf3lVKpFKVzqBrch5zfeVijvWpMSCgRthj/Wlj2prxtrAgfMrnLwqKPoBtHLIRtCRrajAGI4IX4D4Ssf7Yo5KhmWYgmhfEB7VFCSh1BGxYmMKnPjmcJ+VHCFEYI2fVbERb9XnVJiINkLORJyLrV9YuFWGg4GicMNxhsEa48Dz8sOrvwCOPXXLpQyJtdaKMZILP+ovwwB+ueq0KOGjbunBXDQ08+MvL6RM3sNbustoVzO1aFbjGz2hcifYruZOptiRJCeZFIKp6aQIg8IZs6VvtiWwinSm4MUSUNx4RQgXD3IVzMCcknNlXo25FNYMolvNOakFUwfraQzxIKUyQ0+2kSkhP4I1CuEAkhh7vtYiHbzDRXppgrhN+WK0QkLH1xiOzJlX0hpJCXhfqjxV+H5j9w3WIhqJpQZi+F8PqwrR8XCZMnJHfVqtATXSYkIeS0cHgxCOGYjBGaWXGt+4VI7m15uxOEEPvNjWi3JeIwHUKhZ8gUekNKITzhdD5glR9m0IRQnEhWhTQXRAWfK/S6i+JxoZxdpIDizML1heJ4U7JOdXfaFCZDCGVFJaFINB9I+k6HhemKk4UoFZqlhSCH+wop3WspKN5cdxcGl24F7O55qJAWL2xAmLVMHy9MARsS6j/UlQKLhRwOdZkQCI9vv+It8oohrtdjAAAAAElFTkSuQmCC",
                         2109, [96.70066, 81.2203, 67.64749, 58.1386], [0.58289, 0.592, 0.67442, 0.69411], 27712289)
            elif (record == "SRR3581852"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581852", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/XV2Znjo4AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA1ElEQVRoge2YQRLCIAxFWVTOxaJX0LWr3P8I2ulYZYy2AylNmfeWDfnkUVaEAADQgMv1UG6yZ/rRhzsRxThwHI0DazE3TMZ51dj/w2QcWIu5YRisAyuxv6XdGw7JOLAW+1vqje4No6wYxjZz7AeGGPoHQwz9g+HpDZ+Ccq+o+wdDDP2DIYb+wbCxYdFu/5tkKauvGTKzZVeTs8CwoAlDDN9guAkMC5ow3M9wXj+l59/UJ4f4GkTZJW/6WvBpqGSvGy7xGGpDY5gXMNTHwBBDDH/Tj+EDRRiUvUk5iPoAAAAASUVORK5CYII=",
                         23, [1.21522, 1.02068, 0.85011, 0.73062], [0.25842, 0.26891, 0.30422, 0.31312], 24049129)
            elif (record == "SRR3581853"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581853", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDK/wAy1e5hAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAClklEQVRoge3WS5arIBAGYAbpWlcGvYXucY3+/S/hqlGpByAmYkJf65ycqEBRHz5DuOKKK644Ib5++ovf2o7vXtzqoI19Gbd7+G5ZS5uwInC+7z3chl9vkRVycHEfid0F7D4//sk2DPF9Cx2ewz3C+63Hq9Ted1FoGkKvTxrA7vP0nxL2Ge8Wlt5Ox0ROiEtYlz1uZiidCtehSphM+A4h5n9+IanbOFkoUQ2ExEtOmRycSkjPCsvjRPFUEKYqqglACMkfVX1VpRXcJUmtkFJClv9PxGIZziV4j7DmhM5JUp9cshevOd28rYR2JnqUC1IXVDnx0JNXoa1uHMzBtSaFmBtsjtpYhYhCqhMWpySOd/Yxwo0VzYYW8rqtheNxBHWYiqvKu4Q836lZIVoIZVHDDs/CdZ6EUPB5MJB4XZubdmyBmC3EIlx5XrjPulgm1fqZa5YMky9AysvCcXxeOK2mFyauxdeFa1IpxGM7CqZOoH1CVvkSQrGePPXICvWSbz3jEsJxhfNCLEIoIayQWgvn6YbnYPqLa0MoyzdCyglhU+m0HyDkEMv2QnEXQcTykqsX+sLHA0r4uAqrhdXPVaayEHpPnVpfDYnLNimMT5vThPHSQ72weGJKQtP6vFBsNxeyzrYlZNnqhZwR8ocIVXleyEGXGIfHXcgUBwgJQsg7hWrOML0q5AG/GAhOVC2kTxCioRBaaGZuIVw/9r1w/rxMCel5of6a2idUb7pqITHJ7kMmWjLlhV7k9jeEEN1PF+oRtKY9VghRTo3QV14rNN29UHd4XSjb/ryQkt1aC219f0gIl6m5UI89SUj5AwcL+T8Q2lLzNu5SiF1Ck7gPoehbEhL0+Xb564Va0F6oO7reUpgf1o+QdPd/W7EhZFsE3FgAAAAASUVORK5CYII=",
                         1118, [40.6672, 34.15698, 28.44897, 24.45003], [0.61872, 0.64954, 0.73764, 0.66664], 34931944)
            elif (record == "SRR3581854"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581854", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDLyzJA6iYhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACpklEQVRoge2XS2KEMAiGXbScy0Wv0D0r7n+E1kcyQCAPE52ZVlYmQ37+L0Z0pumOO+6444L4/H6poKFqz95cK6hbYZ4+Bvg4LxoJMZn5mKd5HmLlpOgmnP884dfXaxNCGyFgOtdzD/u7QDGAsCndyO7pNO9B2BNt1Q+FRQjgp6fZXUHn30ST0C87lhDgAkJKCSFDOPZU/QJeQZiYzm3sTdhcvEzoN4WqQJtQT4Xsxs5bigsIl2OymwYx6TrCrnqp3iHCjAn901sQpim+iSSZEyKfdB354rXB7slwQswThnV2Xah1VIp2QtRT6K1K9ThhFDLrrpszhJAZrtIzctxVdYTwWoTWM9NJSDdhZ2QJcdLRQghpK3wKIbFLpWd82Buu6wkBiRPuF2xOidpPaGMs34RB5HxCkoQUyyb3ej3howiJE4pK5l856+SleWYuWYRkEdL6/TqEkBQhF7Q+e6399myUCUHdV5mJYPzSHBsVMlnuEMOFyFc1E0LwchNCioRqj7Y5sJtQW2xK+LhmlqJ1eJRx3PCxbJJKLyGkImFQOPiv5p8QOm0bwhDko+oRQlzm6ylCrCAM4seOK+QIw5A0IQoNTcj2RVo3CANEBSEe6zmipnIPkXA7Tmg3PmAmgspYwih7AFDWVO73Ie3PnkfIt3l/VQvCmBxhqgl5/pZcC7bYXt8QOUII+7jPU/jIyBHuljmhbFJHCcHKcmN5lU58HSeMIrE2RELsIYx6FxHS+kEhazqEabiEYsfCAFDptRLSpBrGTRiyQT/7uxy2EAInlAlK3SbkFD4hOGkFQraBgpCKhPwNgBcQPozW3MTQG0VwQmojZBPnEWqnBUJ3XdaBZQfkxBWEFYgVhCRHfhnl7yUITb43I1w6tgm3ynjrjhByi9cRJkt+AOraCYOkiYtuAAAAAElFTkSuQmCC",
                         556, [26.83319, 22.53759, 18.77131, 16.13271], [0.53878, 0.54146, 0.61965, 0.63874], 26328598)
            elif (record == "SRR3581850"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581850", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/AACDUTRoAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABjElEQVRoge2XQXaDMAxEvaA6Fwuu0K61qe5/hBKwjWTjlARBSTqziR+WR/PNg5gQIAiCTtDH56X0lUff7SKRjW5/vblrojzidpHIHYc+dG5pjtBuwq4Pg1+cA/Tm95AkEKcxm+tGIPRN5SkPwm4IQ+8by1Eu99BR/n1GEuHkzuZ60fkcRBA+LhAunc8inFOQW7/RKHpaUxAeJRA+4wjC3HlvKxL9KltvRJsIqT1VazRUhByIUoeyDoS/CoSx5rUJa8Txoj3wx5q12pA+DkpCna1YdjMURThq3rxqCyPhHlAQmhoQFuHU2C47lTB3Uof9FuGUZV5VBOboVGdTBdawIJQmoTRuw1aBMGXgAMLrES65UvpkMj/5rCol16YHf/5dInJBqP2qgLJKyGQtQAjCf0F4WxzTcUkoYhPK9M2aUaZJ9iUUsRaWUPKpfPO/PwhBeH3CqUeyN095QWgTcI5Cogjtnqi3UprXiE8Rin3LgRCEb0BICqz0v0tYl7cJzXzZ+wFC3WCtCoQgfBHCH+a01ShnQHXjAAAAAElFTkSuQmCC",
                         140, [6.16326, 5.17662, 4.31155, 3.70549], [0.46521, 0.48974, 0.56289, 0.50071], 28863066)
            elif (record == "SRR3581851"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581851", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDK/wAy1e5hAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACd0lEQVRoge3YO5rjIAwAYAqvzuXCV9ipVen+R9gZAkZCIgYz+JG1mnzmqd9gnMS5J5544okD4s/f68fX3o5n39zqoJbGs5vcsoxKZUxAi3Ca3TdvGpbMkGgSzvM0/SzkraJJuCzTMn+00D+HN9ukHyZEowzIKnWt9GsEoFFG/7OwUHHhsFZFC+H1gUX6ZQMqheGazhBCZ++CMCs9Vdg1JaAlpBOFr/H5urWcbvpu/Ah14YnCkCLPtE9IdC1hzIarWoSEeWOycj5WKA6SIASuapgT3grTAltCihXVs9WGGDGc4mJnqWTKoY9IL4wbA3m7o4TZi4m0sGVSLQQuJFEqGx4tZAlsT4rrRteJZ0JipbLhMCEpIbltobgGWrffljAa6Vgh6UtWCtZhKLL7fh/E88VKnAspnESmEJ25uJ2Rj6iFZAox6xOOYNWWciGdImQ5CaHffGRkA7yA7cMrCnkCbIJXBuuh804IbIg+IbkBwpCePMUJw4ev2BJyQ60QjDHLNXtcJSEIoa8AS0i1QuC1aT8XhIWaHcCUxAqRCSVhxKIc4J1QPaJaWLhrKB5qt/+XKRu8IExhCnl6YpWCENR4XEhxVpUV5cKdr0a+AmYGQiga8F6vHpYQ9Xjm+JvCvX9KeWH4FiIz0MAsxdFCzIVtT2Rs7wfJhLRXiKIByObNwrhlOoV8kGpheu6kUBq6hap9I7BfiOkoHC80Gm0KU8d9Qp8ifyeMEqaXP7YJ0zemDiHmBUOF1YtILut4cSGtZ1glEEJeWHo/NAjtgt8WUqMwdbiNUHbdCCh2fIR3EZY73kBYQ4RyvzsIt88aE9gsxHyo44T+Jxxv+g8/9Hw9D6b4sQAAAABJRU5ErkJggg==",
                         7052, [327.26166, 274.87186, 228.93772, 196.75701], [0.58143, 0.59634, 0.68267, 0.71181],
                         27380567)
            elif (record == "SRR3581849"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581849", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMALU5xZsz6cAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACcElEQVRoge2XTZqDIAyGXTg5l4teYWadVe5/hKlFIJCgBsWqj9+mLYTke/lR2nWPHj16dIB+fs+vv9qB357c1QJL8NC/hm5o5KSVyBDbDyPk0MhJK1kI38vXd7dew0sSAqEh+nMIhzZOWslE2L/GVXw1M9NEtjW8oujuhHB2Qtya4CH8unBrAkloej/uIH5rBHGFhM12TkBI+nffgpvzU5b16F3LGXIvYgEqpv/rhMAIcTOh7IdDCbXMFAkB5ZFJ7QGxg6pkU04tUJFw98uOqORbffNoBou9LiISgmIvEMbOAwkV/59y0QApZnLCmEJLtpJwatibkGYI4eOIZEhiD/lTQ7VnI9z5KgDCPvhyNNldJkwWXLEXsA8jZCdfEE5uiALYIiEsE06tsXCZUN9TRjFCYT8lJLcFZwmJB6jPrdWE5D4wrVahnJCXijPpjCOJEGcP0hQUeqQ9YoTEUogomjLIFCvFnsf+aGiEOBlwiPOEgCGwYNyFRELsCoGMsPaKGg88kZkQc0KqInTfsESIPHcNIYVcJUI3hThPmG3LBULKCGm8xSkcrglEtUpCSghDQoiOc4UQNBFOU8QJRUruihOi8W8opK44YbyDFgGDnXH95wmJX06TAjbC96m1EzIb9YS8QSXEeIlJevP0ZUKaCG0HMhDymlmxMqB/ykPaoBMSe6bZCP0Gwc7tFtyZMHMg7UC5AZOfOVEFIcRxBkL2Nj8pYewDJWYDYfrrDISgxawgxFAmYzobYXglGwh9pWsQZiPX0AXCZOT5CdctIgTCfG7uRJjrXoTawIfwSoSgDrwMIT6E85bXE6YEBxL6Qoz0H4A3mRnBsGvFAAAAAElFTkSuQmCC",
                         2767, [111.62804, 93.75803, 78.09002, 67.11327], [0.6113, 0.60696, 0.69844, 0.70504], 31496414)
            elif (record == "SRR3581848"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581848", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMALU5xZsz6cAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACXklEQVRoge3YS7qrIAwAYAaerMtBt3Dmmdzsfwm3VkBCgqA81PM1o5YGwl9samvMN77xjW8MiJ/fW8W/pqtd/eYqAVi9xGxeZpqrl+kV9cJpnhblbaPFGU6TmefqZXoFkTYKR5aYp3l+TW220yGaCN9H+DAhqOwlG+XY9Lp1p4F64c0jJUQ9/QphvhfufqYKhZQYHxFZIe5lEBUK0abnqnUIvReGCYBoH0prUhiNrjK4QqhfZWGQT1FOMyEUo16Yq9Y+skLYhFQhJFvs1kJ4ppAyHw1gQor7qi6UkuuEkBUuBvcpkgdO0Xzyk+K8omodIluTQqE8gucL4ZRQJq5ZA4W+vrZrllggDDedFpIZKdxujOMdroPBw30h8Pm0XYzXCiEnJMNeD4V851wIu0IcKKTPbeOnVkMh4A2E9ht77fqE0EGI72tcF5LsSw0C+E8fu74VfrYjdx0KQQoRWGYgtLlpIfQQRr28idCtCJgQKmsGQjQtg3ShK6cL36+s5wQ5IZwQNj5EIfTtZa3GthgIaUfIWqcmhITQvwMNA1QhbMUyQmSGWEjs1XDZYcJ4QUgJSUzbEwrRQaG9gesgBFifRluJtwObkBuAPasU1h0lGgyXde3dCSVwsJDqhEsh983OiwHtC8NZnYVLLp7tqpQSuh0gybAJn2/zAUIM550S+n8nNaEWPgGHCNm84nDpipA/u4/wGBFo+/EpTOVCd5szRnik2+AzhVguXNLf/QWqheE9V39h6SH6StEeTgnVgbsIt/hjQpATHyPEk8C/JdSAh4UYrzRKWHCZqsAHCSXxP9l1iZ73ECcjAAAAAElFTkSuQmCC",
                         2644, [121.86651, 102.35746, 85.25239, 73.26886], [0.56501, 0.5541, 0.63938, 0.68495],
                         27567816)
            elif (record == "SRR3581847"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581847", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACnklEQVRoge3XQbqjIAwAYBadnKuLd4WZdTaT+x9htCAECJJAdbRfs3if+kLCbxFb577xjW9844T49Vsff7sZfwzV1DFe1HozAPspMHKX5/umeDzdY/0z1omonzJWer8oGpKfD/ez/hkK0gjJMh1d2G7bzGd4D+Hiu91n2G/L4jkhXGYvTp9vLo2UqVA8/iyWBfrzHFylDSHwjeD/Cyc7SdMn9pisKeV0hCHmvrMllEFNYbwqCdk5ZnuG9iVwyLPdaDQmTGOQpTrQzvsKwoiifSHdQCg8EUwopnAh5SfqvtjNekfU0/d9KyGWw+JxKcwz/VWxb5F4kLgShmXGrlJf2OCmq2LfIvEgYTV9sxBKocTZDniBMjG2yFvNRph+Khp2AI+Kh6WQjMIwPL1K2sL85WMLaSiFKGYTFm9LCIcIfdKcsB5bCUkjpFK4TV2YuOPCxn0JRV9JOLHJ5kKMc20K0SD0C31OSG7yNZIJw12XhJQuL82gIdx2DSCWoBZSnehrTglpQEhNoR8CMVUn3OrIQjpNmIDLSi0z5oTkX477wlFirPmqlAuRJe0IoRJiVkESvlJswtHdlAljT1HIoyekrAJktZwrrq2HsCfEICxKGIRpGrIQekI2akeYvdJYfZ+93qeGkKaEsDXiplwIacJVjAhhXXCVcDmDlhBnhWmFFELKz5pCShNtCin+SoS4BExCqlb65YSlqD7vCYf2mjhwSpi+BBwrXAfEbxVnC/kaE4WCSCvk/wTrJ/ku4fZsnSFEC+99QvnCVYQY21xfWKcohVnPCwvZOEXg9vTEverDhGvlICx6XlcIZiHdTMjHWYTl2KsLtVuNNPQmQvx4oY64M/L6Qs06BXHg5whln12IZbGzhNgB7s/4DkL/kzRz/gN+xIRdVtz9iAAAAABJRU5ErkJggg==",
                         6275, [280.55728, 235.64416, 196.2654, 168.67729], [0.60027, 0.6031, 0.69407, 0.68327],
                         28419567)
            elif (record == "SRR3581846"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581846", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACi0lEQVRoge2ZQXqEIAyFXdicy8VcoftsmvsfoQiiQR4KKg7jN29nfCH5EdBpu+6rr7766gb9/Lavv6OJ757cXJFwvrkfulf3elVrpoqKCIe+74aur9ZMFUWEjFxefW8e41CtmSoqIzR4zRBypo9EwoBgn9W4PodGFilxpq+I0Bwyr1a2YR3ClpRNKJ9KmPsOaJ4w2c4JwszMm5QijHaXFUNjQ4Rgb6XagYRobzZGGHedasf0Hd8B+YjwjRuxjBCYQe+x0VzbQam0vQuEmuaUdZeQEkZzPUb4DauV4pUXbzfy8ROEYwQUOyv8itbV9wnJP9QUoY6Jj6UIr0bEv9NEG+Kauj2y7h1CNYC4lPsIUUsmujxaAV2byLQsx47JuBUhR14fM4M6DDQV1kY3EooyoK4XQtOUX8hZhGwnBRKKG2A1wknhOZNl8QLCpT/XcxmhOTMpRejMl74ZGe4c2iaUNaEkCCnMJ5keFIGlrwmdPSx6UKhUF54Yoi28hJyRaYeQEGEwZlBHDXbNfowI3bObCSkkpOWoTxOq4UQQodc2IV/zGReVIrsNpijZY0F5yB0wmjCY9omQ5gmZhiollC51BOZqPq2iUmM3vgqpC09oew0C24T6bgEhg0/zEpns6X2n668JOag5t8i7hEwR0c2EY3KCkCIyQEh3EfLR3xkRoQS3sAoIAdExwsOfNyr3AKHcQSjx/jlHOA/UGmHhVvTLOiacX+jNEGLPnrw/SZjm00C8DtQk5BJACrpChBuA7yIseojermuGA304IblCdJoQB2oRchnh+JnJjyV0/lUP7RNmL1NZj/A0QooSH0YIEp9FSCDxYwg5hzCd+AhC2kq8i3D6q88RwvFfUivzP5Hc6xq2Qp7QAAAAAElFTkSuQmCC",
                         5205, [248.59171, 208.79581, 173.90371, 149.45888], [0.60004, 0.57061, 0.66096, 0.71079],
                         26604761)
            elif (record == "SRR3581845"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581845", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAfv+hd7twAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAChUlEQVRoge2YS3aEIBBFHXRqXQ6yhWRco9r/EiIoUj8/0GJHj2+QbqAo3gUEO1336NGjRyfo6+f/67e246cnd7cAC4L77tW9+kZOWolQltELmjTA9X3/auimhTQhrcT2gbC7GCGUEH5/R8iGdhqoiLALa3ixJRwIFdIG4Sss5KVkCfEjPtrpIbyW0FYNgA/hheS9n12X0KPxvDuEq9fF/xE4Pj3vHuFYAQ1cbQkKBvVodhPGcYp+cxwkZ10WdxTpLQkBxk6RSxhrPvE8OmtASyVjHCgQoqzLPKKnIpSdDpNNa+7mTk90brdLE2rSwsL0h1YIQ/AUba0cISctmJ1nCClNzAZh+FgnDOFIS1aO0D5C0ISpbI0rQop4+wjbXB82LVgz+jzJEZmGt2XCIf3wndBJGsPG+aCpoppCZVbj6HawrgUhQTblxArCMRYWCZPQt1IndY7YHUkuIcn2KcISgiSkkZA+Smh3pLsu2hnOCDwWeOtcIrYXdZ45HLxrtEYgLEFKH59HnEdG0WedkFRkBSF13rFcIv4YuYThWZnOVccNrxCrpAlnpApCJ2S/2GEP1tJESFMYt8jNjPEeIYp0VYT4HiFkE8rSXIrZxyEcO4wQBcOBhPAmIbGvXil8xFK6oUj159fDMqFsLSAkk6qWUI41EzLjgnB8H9gizGfgG4S83wGEtEwoIiCOuUmYjKnW8whZXznYbIes2NxsExqiWsLKB9EhJFFaJcRTCNGNOYzQEyNUFU0IZcf9ZEcQpuk9h7BoEUG4uilheqV9i9CvaEWIBYRjPFyMsGARU3rkY96KUHW8GSHYO+4yhLgTML9+3ZJwueNNCGG5435C1JnOIkz/lmKkf9iNjAErJq/5AAAAAElFTkSuQmCC",
                         6458, [337.94961, 283.84882, 236.41453, 203.18284], [0.58748, 0.5443, 0.63067, 0.6898],
                         24281268)
            elif (record == "SRR3581844"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581844", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAy/84xeGNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACaklEQVRoge3ZS5qkIAwAYBdOzsWirjB7NpP7H2FEEEISVFrwUW16UyKS/D5Avx6GN954440T4s/fW8W/pqNdfXKVAHt4CDN+zGgOD9MrjgsdzpjxeCmdQhdCxQjGDONgPm3K6RBotdaaK/v5TMLxvtdQF+qthTDT33BjISqNwIVW6RTDCW880+wTap0eEqAJQbS+whuHLsRX+JxwFqu25i1XCmvePuQ6jnuFtj5bq9h8+yBFgbgUyIgQ+ulC9ZbuHptCTD1khVyIsZX1s+H4rWwdYvO0YnKJwoEI5xPxK4SgChHhIuFmUkjlysKl0DqkKvTt68naRZo9NoToETZ03RCCnTrcRBgTyWkvW7yQGJI1DsKEs6MsVE5Rt0iFaks2FeKKEAeUwmlTkZTaW0f8qEmFaks2aVgTIhdC6F0Q+mjhKMcidLNjWpulECH9XBPSvUSoSJB1bhf5eOATzB83/lFUky7CeN8RobyDMZ22C4TsWzskmFc4X4WWFJb63NRYFgIr+ioh5ltRGLJpSWN9JSEX/UTYSgps8gvClK1UjWbwmxaEqE4YxjoiJMfmqaQQzhce/8rILluWCmYh0tKAlkjOw4oQjwpddxAd6oRIfpLyw+PHS+HCVJ8ulKKzhCiEef1LBfmyRXtMu+4shKKQ7JgTCGACuUWyuxDDjFD7Xyv6iePnqzhsvqVFLHF5me4qjC8SVUDIIMy0X4hnCJE9P7uFmPIcEPKGnsKqi7hkojl/IrRnCNlIu8JXN30wHBXqDY2FpV6bwhRfKGQHfpfQjczXuMcI7StURv5CYfnABwh3PIj6cc8Rysv4H9NYm6ASOfzFAAAAAElFTkSuQmCC",
                         7786, [344.67924, 289.50114, 241.12228, 207.22885], [0.58587, 0.57361, 0.6635, 0.70102],
                         28702818)
            elif (record == "SRR3581843"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581843", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACcUlEQVRoge3YS3brIAwGYAa5/7o86BZux5pU+19CgzFvYQx+BPdYg/QEI8RnMEmj1BNPPPHEBfHv//jx/dOZ+OmbuzlA2/u+JvXSL8MGCW1gqbUQ00tN0/tl1BAtTUKlhWo6ZDZnhGRBm3DSwnutYZvwbbvdLgW3CL++xjlphBPyjRH6FYU4dD7HR4NQaNVRaB4m+oU28RPCln2zVciZkO2FfITTAw23Ne/Lf18oPnElYdsZe1SUzgSxqyjMBxhNWC/q9hinT+0spKQzhhLWiwJ+ftl6pUJGRXj9YVov6g4TYeLIhFwQku1O6tio3jJJGE+C7TJXhPMGvlyYHH7IP9Ckk4KzHmQGWxeSMkK+UsiiEMHHfH5SpF+mY2F4iVMhsC6Uiu2L9BhZCuidtCCzWfvpBEmyEJmQjVD4CFkKHy1ESaj/fTPLKZz2e4S8LKAsNAOk1fZEulvghRzc1VSIMAkoCt16mbZFaCMec26AVG1XFIW8TI42CH2PXMixEBxEPKbuBUhXOoLcgZlOvySU7rcdLDCYCbpfmbzHCkNgPmZh/7YH/BiS0G6WbiEVhRFQEMbdjxNydEUXCGpBqAmXBDez4YQkCm2BitAn3UVIwYVUKNUMhHSKcO+DOAtpRSiFBSXC2LC8HULIoTB+KteE5m9NmItahbRPGIxhB4zerQp14qhCRA9fYmoR4nyhvtb+0zCWMekWQnQspMmx3yu6hXyNcE5qRIL9AuwR0hXCOdB4qJpKcc0uYdpwpnArEdbmP8v7hXLD54Xme/u9hD6zGsXM8YXbFhFC4iO8l1BK/FNCSIm3EdIG4UriDYTsfuJ08QszBev7BDml4AAAAABJRU5ErkJggg==",
                         3528, [178.65715, 150.05675, 124.9806, 107.41266], [0.58998, 0.59569, 0.68319, 0.71685],
                         25091894)
            elif (record == "SRR3581842"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581842", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAy/84xeGNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACdElEQVRoge3ZTXqEIAwGYBf2O5cLr9Cus8r9j9DBASQQFBx/mBmz6NPyQMg7INi26+644447Toif3/bjb+vAqz/c0gAqOvdDN5ovbxXgis5D33fD0B9WzBEBrhF2vVEOB9VSF+reI6Ufs9KajeFhbGQNQUqj0lYnNEvYslBtqxKOYz82sktxjLChUOv+AqFybGaFpD7J7USxkDNCUONry9o1VyVsfPdCFeptsYRdBko6NxQ5ISltcU8vrHrZ2SdKPtXnuwzUzacVfaGQ0qaSOWehqomzKh3PEoLiYspekp8GVTgv7HwRXClMd9nOQmQ6ctR5t4iOcs9B2rSYhWzXVSGb3Jpw6sOHC/3EYkclc8aMBSGXC3GQUCS0E3BwgKrCqGVJyJHwkVsXshMm070UnBcunI/JdV0jpJzQtu8uDKt1O4rNoiw8W7IFQkhx11jIutAH7XuaZoVmGV1F6aaci8C04mVCdj/yucIgYSi0z9+akGuE4CCUflYYpXglsCKkrNBeX9Mj6XsgrRxCKELmPEoYTWWFCKpYFfLcw6bzd6k5ruqFu9wXLrsq5FWhHwRSheT7XSX017xM6CoISiHkqrFChEXBjfGic4Xz6wtLIUMKfdkZIVaEqegkIQd7096qMiWn4QR+TrMD5/pAIsNewo1E+FdOxZQVynKMWAhlTRA/vSqkqv/ebBVG5Uzf4Xgh+0+zJmRZ24V0hpC2Csnn2iREvmFnIXfErPw6vhR4ziTP73aFYZWF8RwBd3a0LhQDi3SkDm1eWPgk4iuEcbyLkIqE+ZHtC4sWEdrAjxKqAz9JCHXgBwl1YLWQ4lxnCbmb/7hi4x+KHrFxN6rPXQAAAABJRU5ErkJggg==",
                         3780, [204.61381, 171.85813, 143.13873, 123.01839], [0.59276, 0.59402, 0.68116, 0.69706],
                         23473731)
            elif (record == "SRR3581840"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581840", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACWklEQVRoge3YS3qEIAwAYBY255rFXKFdZ5X7H6E+QBISVAa1aM2m3zBA8qsIHeeeeOKJJ06Ir+/24+fTgX99cTcHFfTtXq5z7nVUKfWBViOZrXa8OvcemK0GoNVYIuyJTd/DHYRd9341LLQsUCTsn9Km76EpJCp41Yxvmu69W0V7R72w8TCfRy28MBisu3UnIdxfaK646wr13tdTjIV4N6EmkhZiboa2YlEIsjXph7kZGghWOaiHjQtRtCb9UP5tKiCuIiWEVDhdjqyw7Lx6VlDcENSSKxW2edYRwqRAJaTQzxSeeJpbXFtJRKEuXAqn5xmaELKnbV04G1aE/aVAGpCwJER3QvB/38DICeLTbAC990nhBLOFFLqobEcErQhFC5QJqR9tCtH9G6FKVxdpQT5dLMBa/IxBzBAeQ97TEpLud5wwOST5e8cKMO5LWDQudM0JwfOlMEQ6JfnZ9hbKCX3iqYBYNaaDtglnDLr4dV4IYcQeMFGEKH2oZlomEKtGqxo3PgE7Cin0SNLVBOCCcPrKSjkPAgxVMyHy2f5amE7IhZQVxsuSGLwQlGijMFyveiE/RmohidKMamLLzkL5YqqIfh6/SSTJfIa4fuarepJQdK8C8nNkTBYqQFIx5+zfLXC4sJa4KjQiCmlVaIg+EOInTA6RQpKfjPBDh/3zBCENv7Ji+e9v1cKRh6LhIOE0qHTvD5lYzmJhtuEA4fjeKwEO/ccT2qWEWCAM8/KcbQuNXksRpsebCiHd4+4m1AMvI8QtPsgOvIswP/ACwg1EWBi3XYjpVKcJtfEXhFRJ7UUuEBgAAAAASUVORK5CYII=",
                         5146, [274.02561, 230.15812, 191.69614, 164.75031], [0.56896, 0.56932, 0.65392, 0.69747],
                         23861838)
            elif (record == "SRR3581841"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581841", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAy/84xeGNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACYklEQVRoge2ZS3bDIAxFPXC1LgbZQjvWSPtfQo2DMULCsRxwTJLXzzlRBHoX82s6DF999dVXJ+jn9/r6O9rw1YO7W2DIHd14c7dbMy9tBLg/143Tj2vlpJUIDcluGIeba+SklUyE4/Tlv3sSWAinWermqdqTTISj8/PUtfLSRoIQtayeJQjpJTbqSDsXAChD6plQW3EfQEiCMGRZbgJX0QcQKhOwSIimm8A1JFZcCKqE8P6E1CGhYAnBnHB+7cnxBFM1JZ+W17UILbubzM1ZQI36iG/aK2EapBnydYTqDWv/dQNk7n5CglcRKuuo5EIal4Q4QUKJMM+uId6fQqPt9kZCYq+LhCGOda+o2UNTRlA7okQElua58dnzmj7vrISbhJWfIl842tauxYSHeF5vEU6jGQgKhNiCkHfHFnrxufCJC9OsIxshFQipPuF0DWSVgLnBWDormTYKxnBpzkcsIwwElC/O0M+irNwBxc+bc0srod/y4gl1lBBoSC2fR7h2kZWihdBbgSIh5ISUEibOM8uMb4vw2c00MZh1GAmTBaEMKm/TgpDXq0cIsfeFkB4QQnSdECIMvPsLEFJKOB9Lq/FtQmSeFkJBZCX07z2BCWtN3YEk5G4SQs5QkRDm2pZ/wQ3rjSypyR3EV4k1YG7uN6AHhFSDMPxCCyBsEBInJKFoEdh+ohNKIjNhGCkbIu0m1BQt4rmEhoNjHZBuCJWsIh0mf7DAOxLSsrbwecJl87kUIa+U1jxEmAfaEqKNkOIl5DihHrgMYdbwXQjLDTsg3IMI5XY9ENL9zQ1QFbAnQvGxzj+jRisv6GLDIQAAAABJRU5ErkJggg==",
                         5461, [277.81225, 233.33857, 194.34511, 167.02692], [0.59075, 0.57412, 0.65972, 0.69216],
                         24977332)
            elif (record == "SRR3581836"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581836", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMC9d0Dm7cNnAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAwElEQVRoge3WTQqDQAxA4SzaOdcsvEL3bpr7H6F/WGSYKqaZ6aS8txBEDfkEQREiog6dL8Omev1ywq9f7l6qs+Gp7LxFy0zCU/Zeo2EmYc7eazTMJJwm9z3axXdYLztv0TKbMFII4/fvwqQIo4cwfgjjhzB+COOHMH6LMGn6JL3foR038g6hIBw+hIJw+BAKwuHrItydcPzfcTWynF6cP2a/K4fMywOvi+ujdZ16CDdHIkSI8OA69RBujkSIEOGzG5sTejUOe9AAAAAAAElFTkSuQmCC",
                         17, [0.85443, 0.71765, 0.59772, 0.5137], [0.25055, 0.20701, 0.22941, 0.29633], 25281241)
            elif (record == "SRR3581839"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581839", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAy/84xeGNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACX0lEQVRoge3ZwXKEIAwGYA/b/7k89BXacy7N+z9CVVQgBAVcFHfMdKa7FEg+wZXZdt0TTzzxxAnx9dN+/P4VDrz64iYHKKNz3726V1+pklrBlN53wPV9/6pWS5VAjrDvp59atVQJZAm/v0fhvdYwT9jdcJeCpZC0bkvc8JMmFPIlddSLQShIj/BuwU0JcXQCCpsaE1JG38TxbQllLd3GsmqaPOHhHVMQijD6uE4SQhWaXnTBWoaPrrgwqFvtzNNHqSoEZZ11kmJ3wuNC2cYcFyrJDgZEonD+8NEVFWpdCSxvMTahTanNcDDECVg5EIfFqBvPjA6WYFqtuXG6IflsoZgRiiZMGl4HWx/Lrg0I3Wrn+wDjbjUbGMzawshp1vq2hbQlhJrsaIhUcwIedWalOEWIROHQjxER8hXC8Y0mlFu74zTh9BqICIcW01lkOxhRIaULGTlCjgtNvPWhD5EKJsH0i7hM6PdVhEsEc1rjcRbZl4GQ5yOHEUKpxluqeU1aEy6zywnnepxcmtC2YK3MCt2+8DK0KdRy7gnXozaWey5TWHojLge0QMhOFyFUr6ojXNbYFZIj9IZXF7IjnD+RRf2ihEJhcAHzhdSVBFwhe0L3D5HwJ7JCryZ475z5ThM6rDKhPcexGPFeYdk2XQeWC3GmMOvfb7tCtQJNyKCThDQe4rKQWDJBEbL/bkPI5winxwzybshV6OYsEPI5wkV5hZBkQzWhHbmvo/XKwxtZItQbagnTFnGcWZ5TPk8o47OE2sBH2IyQEoCID/wMoQq8j3CXuD0uXegLzhTOXzQ40H9b77yR6kObwAAAAABJRU5ErkJggg==",
                         6753, [333.75745, 280.32776, 233.48188, 200.66243], [0.60415, 0.60295, 0.69269, 0.71294],
                         25709347)
            elif (record == "SRR3581835"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581835", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCOgm513YCZAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA3klEQVRoge2UQQ6DMAwEOdC8i0/07gv5/xOKqiJM5YBc6lqNZk4OOM4OIIYBAOAH3O5/z9y8k/1wv4XoxTjlhAhF9GIak1JEIrvVlJIhFtmtun+H/X+l/f9pukSyA4Qj2QHCkewA4Uh2gHAkO0A4kh0gHHHvKHWt6sJha63+8b4sS5qjI0qpH2TAUIHhZTDEsLELww0ML4Mhho1dGG5geBkMPYarTX0iu2tvLWtd6ukj8GGcp9KY7S9aI6zpGKoaQzcYGu0YGtMxVDWGbjA02jE0pmOoagzdYGi0nxg+AOnk+HUbDm4hAAAAAElFTkSuQmCC",
                         18, [0.9056, 0.76063, 0.63352, 0.54447], [0.29619, 0.15415, 0.19333, 0.15105], 25255784)
            elif (record == "SRR3581834"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581834", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDDjGB0pJ6DAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAxUlEQVRoge2UQRKCMBAEc8C8K5/wzmn+/wQtvcSwqJtixaS6j7A7mQaKlAAAfsDlehpS9AlnP1wpIHQpAaG9hBiWJSC0lxDDVCJCO4kxnP4dzv+Vzv+n+SswHB8MxwfD8RnIMPdUlbaG9YWs1RXnmvaCoQmGGLarrmkvGJpgiGG76pr2gqEJhhi2q65pLxiaDGSoB+u9kj4cU0/k59omR/Xt/bjXw3K7+r6HFwztWhhiiOGRYGjXwhBDDI8EQ7sWhhh+aXgDlsewvWhwMkQAAAAASUVORK5CYII=",
                         15, [0.72687, 0.61051, 0.50848, 0.43701], [0.26047, 0.26365, 0.30789, 0.35304], 26221759)
            elif (record == "SRR3581838"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581838", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/2b5PNDSAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACdUlEQVRoge2YS3KDMAyGvaA6Fwuu0K61qe5/hIIfQZIFGIIJUP7JZAZFlvRhW4Y49+jRo0cH6Ov7/Pr53Tjw0ze3WIDlvk3ruuHrWlpD2Lqm/2qq1VJHhOW+bdv0eFcnRMspqmuatu1n8lICImkg289rmMLLLdJVhL7TdF3VgnbXKsLTCw3brQitcwHuT0gZYfIyvM8uzTJomnDNk8BZdHvCbMdF4xThyTdkPgOUsXg/gxCjf4WydhQgKEsxYZxEWvPA+gEBLRGC/+Tc0QDnJ6TMIGum8LEIMbijO4FkdQBxD00RctsMIUVCdDVlRNfrzmlCenHlhQdC5M5D2zySUIYDY41YhMKLYGwTepEpwh7P3485wr27qWx+1i4wzmBFSNOExAj7QANeoJgjzBO+IbVxUkdjE2ec2HKmx2aStZWckMlljijcd5LqzjE8sScLk5DkFScUbYUkIRCTjBlMFQhlKhgJMT0/GRn5GHBjUZrwBRQCLBPC0YTITGqQrEwQjt6akITyQqT7LgI0CX0pcQEbxeAC4as1qZKLCdNP298zXjdJ3zJPiKGUgOmURxoVOhHUJdw6mcPExWNQ5/KExLYLThFSDGUSZkRrCb0/bn7PGBLZhCk+SwULhKlqRmgQbSEE2vyeAWNOmUxVwAjzE54sht0IKRFum8S3COEoQlSJ3yQ0K/A/kEpEyE+9eoQgRhaKvwCYhDmgLoclr0s4NrudCEleTRH6tKgNNQinvGYF/4Ew/RPyFqFtOANhysRz3ooQQiYSXfgChFhIl4W/F+EQWUe4F6F3vD2hPfAChCWtBqxx1yHERcC5ceWEkuBIQiL9D/Qfd/SXw6sLNcoAAAAASUVORK5CYII=",
                         10739, [462.51841, 388.47598, 323.55732, 278.07639], [0.59974, 0.58411, 0.67026, 0.71805],
                         29502586)
            elif (record == "SRR3581837"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581837", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAy/84xeGNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAClklEQVRoge3YS3KDMAwAUBZU52KRK7RrrXT/IxRjG2RZxlb4BDKoM20GZFkvOIa065544oknToif3+vH37sDP/3mNgaMP+3RD93L/bpTAAK2Zw99734d143h7W5NBSI0tOCIw8swwBZAhlxsrWkS9v0wXceD4gghmYTTJey+WXj0TgOGZuqp4EsWhZYdaK8Y22lPxdpeQ6HklYSGFTV2/ghrwvYF0xiFhvg7aRCOqbUGS8I4znYbaekJkVcMYGL758r7nVfTctN19wFhUjF0c4ZQXOw4bmchSGGoT+wO8bXCuQFNmH56kacqQmZBf14TUiyRFdgSgGKq2EBFyA7gdFlgThW5I48LaUWIMUHOtiWkEApCuUGyGzu67LASVSEKIbkvh5qQwp99hZQJqaMgxKUppW3/Igp9giKkXAgrQthFCHPzvnshxCB0L2LXmZBSITEh8U+pOzMm++Hj194w4bpw8z3fzRrvCoLoJ0AvpAYhAmVC/mgaJhBCuXRS4fanGlclFaa7ChE/zFsMsXx4YW6XC1m2EBKPTIh7CakoBEqFqAuXIZCkbhXS/YQA/CzLrgix2xZlIYlYhCQLrAiXDtOzdqHlP45NQtGBKgTkK+loIXbvBC+y2oEiBGoSZmuiUYhC+OZy5XNahe4YNghlvUYhHS2UwKkL3s40/6FCnv72932bMHbFhPLAjkJMT1l31TBQNRmE+oF9hGl+lyWtB/h0NAnjc9ZHhEC2i0j8KaxZWACdIPRPsd8q9A/hFiHOwjjLxYXTJg55VikgbBlY3D1LwhLoFKGSVReKOS8sBDWrDAzL7UZCPasqlHNeV1jIWhHKeIT3EmoDbyOchtacewhTwblCyJIbgHcSwlJBDygMvI0wS/8HfXt3PuzkgscAAAAASUVORK5CYII=",
                         7155, [252.81409, 212.34225, 176.8575, 151.99747], [0.61103, 0.62726, 0.71751, 0.75248],
                         35961155)
            elif (record == "SRR3581833"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581833", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCZ/wBcL36IAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACVElEQVRoge2YS5asIAyGHdhZl4PaQt9xRtn/Eq4vIAlBhRJbPfx9+rQG8vgiYHV1XVNTU9MF+vm9v/6VOv51cw+LMub2Q/8ZuqFWKZWUQzj0029frZY6yiHs+unnYYSQRTi8iRAMWz8zPo4Qjw98PtMxM1Qsp4IiEEoNPFUpQnwRodqIKxjRWwipET5KGJvgXYTGq+9dhNbLPUUIjfCWaoSLlvunEqJha4S1BYnrgkho1DyBRIRoD5ws12++d75LyQhDq64kVA8oECLLnREOIwv5hRcGKxMKKEBRE8WE0X8BW0osyDUojh9v0BuV55mEvAoVMBB6M2TsfeNQEYTj4vcHSkRIcvYXErFVwPWOJGHUVWkIAYy5xAjJjW8Tfv0QtwnnW0ZIVleFYXw0yCZH2RghbRKSm6LTZQo0IYmxhXD56y51ShlifDRu/Cih8aROJBQRIE1IyC5lCN0kSB4gS8WCEAEOEpa+iHlwtez9Pl8JyV2qauJlED43y24YhFM/EoR4DSFN33c52YTcgJuEZBCG2NFM3ZGzCFHeckIUKVkIbyAW4zRCWufLtCWEa/7wbawWihLTIRihPptzCMVYlDaH0J3vKllMqMsBP229dS6MkMLHJDFaQJi3TIG9isgmTAOSn4D7hHHHsgmJZzmDkPYA3caYi2UG7yMJNVE+IaAxZ58QO7UzCghJELp9egvC1eFrQuyUoQqh9NwXkOs/CM8iQriS8CiiO/ZR7psiQttwG0JVw1sIWSbl+D5C7fgAwkPHqeX3HELcB4S03xMI5/NRYP4Hclbopj4mUYAAAAAASUVORK5CYII=",
                         3681, [183.64837, 154.24895, 128.47224, 110.41349], [0.57071, 0.56134, 0.64384, 0.68134],
                         25468538)
            elif (record == "SRR3581831"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581831", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCXmZnsxbRDAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACpUlEQVRoge3WTXaEIAwAYBc253IxV2jXWeX+R6io4TdgQKTT1ry+eSODIR8CdpqeeOKJJwbEx+fN8XX3AIUYM4WEY8Y5Yl6ml/kYGIkQ4ob2gLRpmedpWeZuQyhisHBazN87CKXiqkNKMhve0iO7NnLCuLkpd9q0LtDBjzAV7g13Cedlfi2vV/G2i+snHvVWYVsSXwheDl02SIQy+R8IhRVWHX2E9lKXbaSQ+gpVywoE0JsKj/FXIVdyJoT941QI3YTUKFyHRsBaIRaEYUtXYVMSCoV2njTC9bZ4XuFthXiU44TFdNtgMF7Y8vI2QhKExQkDFmIKygmxobio0raHSEeY72jqO0rRCZNBewgzD+qycL2ZKoVubmxVkdDMGe7tqC5JFsJwIYZC76zav6A5j36V0D9ctUJqEsqMDkKsFAIJQrogBE4u/0quuJpg4HacEhWE/rVOaE5aJ4zSCaXmhTjdI6SoJxeCeSHqhZQgj1UiCCkR6pcrueCSPSEGPY+rtYJNSBoh5YSUCrcugEWh3e4NQEGIXg1wJsRU6OXTCVH832wdCroIya9oF8Zbr7sQ/PNru1USUvz2rTiay8LkcOFauwjR9BCFEHeN300dha4sFpqz43jAgtBrOBVSKARuEoXhHto66YynQluXL4Sgf5NwSxEKwQrTyXATinyzciueC7mCbXyS7mChPQ0OIfgZIuH+G8+a15QV+vUACb2uCoGLbxfumVAUrr1/XMiXWSFdE3KyM2HyauwtFML+HgrtbvWFvO8SoU1WIcSewgLQCTEUBhlYGORrFQaldRIWgDVC6CAkt2OGC/mdpRa6/O56vJBqhHFDLBREDcJMNymivJeFcgPay0eoE0Km2zsIJVG9MNdNDfxFQnyEnYQY5xomPCX+QeE3i4UIQjqKQ6oAAAAASUVORK5CYII=",
                         5581, [126.26679, 106.05332, 88.33063, 75.91441], [0.59486, 0.59752, 0.68137, 0.54809],
                         56162722)
            elif (record == "SRR3581737"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581737", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCTcyYUg6nkAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABzElEQVRoge2YQZqDIAyFWTg5lwuvMLPOKvc/wigqJJIKVrEfNm/RCkTe+ylaW+dMJpPpBv38Nqy/zPinF/e8IO3qetfdH6SSiCjt7Ds33B+lklTC8RNs8DNEvVsQhg3b5C5FvVsl7NzTCYfBDX3lPJcLtMtt6ibC2LopTBU9n5CDMBlhQyojVGsa0eMJwQjnllrThiB5/kR/Y5GE+iq0oTsJP7NOlBCSfwiYCCOjERZ6XTLLYddvJESFUH94PeqF2ZIKupFQ/9egunTCVRir0J2VEVZSMeH5dI8npLcmefED/aCvkiRosTHCQqd3CPGE5eqrJJH71AhLNF/cwNqb8fCySYPbieZIqAYSxX51lOySkEK6LMO+jLAtQlCiArtzTS7bC8yPJS6JMUC8cBILFHOOJUgFhOPX4/wFKQPt6vGEEKsh/KDge2L7F8I6nCX0UQLhdp9Pc6Jo0vL4kiMkI1QIl3IIt4qUMBwid5U2smdsCEJWOx4DO3+clDPsE858RpjMgNOtm+WQZvF4edfTgOihlBACETkeEyRChlBd3G8mjCeIE6VbGJmT8i2VEiJvcEJyKZERniL0c8GLE1XCnI/oUQjxUsI85AMJ/wHjfui7MWCRhAAAAABJRU5ErkJggg==",
                         205, [9.30901, 7.81877, 6.51217, 5.59678], [0.43385, 0.39039, 0.44464, 0.47206], 27981806)
            elif (record == "SRR3581736"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581736", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCSkyZLPzA/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACXklEQVRoge3YS3aFIAwAUAc263LgFtpxRtn/EvpQ+QTCJz618mpOT09VCLmiqB2GJ5544okL4uv7/vGzt+Nfn9zmAE3jaZjNr64CSNF4nMZhGqezajkngFDRejI/0zmVnBVa4djhVYp8R/GqndZZ7CpSIUrN1hjncZ7G+cx6jg+VsMv4j0LN46OHoFSIUrtuAyies0fYWzzC/uPzhSQIP+pxAaJQ9cl485CFds8nSMvCq+9I8Yy+WUNRiBcLCYTxdtew9SsJ4XKhNN7udW/LVRRe/dwQV3G2T1GQ/f9TQWgOtSdsGbOWrSh89U5rLY1Gg2MUhO5QrbiWqJ6vjNDeMzrha3pqQgofG/S+MX57sh+mbmrFi8b1Alpqtcut7ZUlixPFDi1AO6JJ3yopDYmsdmS1VoVLAKLdDJOk0pUBkBFSInz/VS4VusvPD4JDFBQJaVvgt2XQnSZRCK8HUFYITKi6A+SAWGg3F6kpnIRR/L5UaP7wQuQd0QqFrGsem/BYIVv5t1mA7Xw2CokJKSO01zRTnCxk10SQ01Sxzu8RQgCMWueETg/HCgOiFbrC1UKKhOBfUhRCcvtweCviwSAWSrVUhBiKjJAUQn5QLUwbZ4QgDTewRs1Cf1QtBK0weNWyTwNWn88ZjcZX25qQiTDabheiXkh+6lEWQlSCRAS73rUJM9t1oRlGKQTbekkuC3PAvxBmmrUK7Zg8TXYQLwTe43ZC//K+VxgNfEsh7BFSmORiYeOdiJsw6tYsDL/N7ygkt2z3KKxfpyD12ieMd1wjxPQrpcbbIcQ42YXCMIeJX6n+oSYTt1+/AAAAAElFTkSuQmCC",
                         1501, [76.98305, 64.65919, 53.85392, 46.28393], [0.56252, 0.54248, 0.61951, 0.67301], 24774839)
            elif (record == "SRR3581740"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581740", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJg85+yVAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACd0lEQVRoge2XQZbDIAhAs+hwrlxi9myG+x9hkjYYQDQm1aTxlUVaRYFfENNh+MpXvvKVE+Tn987yl1df/eNWEIxmHuPwmB+9CEYz42MYx+nRiQDGc+NEOD06EY9wzuHQcw77r9LOOg3Q1RHUEUhqqDph2ldL8frJU7B7QuqdkBoQKoOn4eYIE6rDoglrW09JjrBuEo290whTGFQ7iWDs8WXUvFovI+RRK8JgNyIEnj+LkNowMhfEhLgEUPkgpglJrNmwgXm9crf6NarFMdVOYgEh7CZMp38yBcGvVp1IOA9BENJuwnSVTeYp+DUq5PnWhM+hOAt2hWPDqsPe5ROF5qWD+LC1JJRNxSfMJ9EhxGXraxz0mCXEIRBWbDVgDMaE2w6jKraEa8FzfjzCZwFrwhr93P5kCUI021Ta4raoCUGVw7NkXEI6m1BewRbRnN3wFRaQlxr4bLGW2FgpoXF7RBxC4mmEdYVxJcYES/9dQgJDCOQQOqV/CSGVEoq2hICWkNYxuysjhKM9VVY3aQCOdoMQuIbBEM7FXUCIRYR0lFC2vrVuHEIKAWYJpZ7Dr0MYrSkmlK+chYTK1Tx2CVcEHuLgqhOE2JwQ2PoaKQmXMpjlpCDnGPcQxiaZkHX+jbIpyKbQJwT2HIIwhPIC0YTqnSsmKiUMOhhwN+HUtQOhfskIEQTP5YSa4V1CIYDeoqwoDpFPYSgmJEMo1jUmTKwqJgT1j9oSJh0Brf3uIwnF/ZYjNIEYQsR7EOqTpwnTjq4gxEK+V1hoYzhASGgnPoEQKXT19wn9iYsJkxt7IYTkxk4IPcD7EJYg3pxw+77wt+0l1ASnEkZZ/Aei6kE+fBN0YwAAAABJRU5ErkJggg==",
                         4467, [221.41785, 185.97209, 154.89409, 133.12135], [0.57833, 0.53969, 0.61863, 0.66096],
                         25634721)
            elif (record == "SRR3581738"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581738", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMALU5xZsz6cAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACVElEQVRoge3YS5asIAwAUAa+rMtBbeHNM8r+l9CioCEENbaoVJtZI1Zy+clp59544403Loh//58fdPTFuwd3bwAZOn8+7uO6vlYtdcIk7F3n+r6rVkyVsM1hP8xh/6lWTJUwCV03zGHX1hwCEO7v7XV+pbYUQBZh17d30tiELUYuNO3L58cAzISodWw2/rQQRHsTgVmLF4qNF4WyvYnArKUsxIccsqZxVq4vDxNC3lRDOMnyDXpBaMJSFdo5sVdITj2CLgglpVEI8iGpQrpHSJCfbvzajMkTrbz5/jIKwa/x+4VsYZKSk6ORI5XRYFtrEKLfwgT3C6d1RTGzLJtDkjlW+nIh+ekLP7kixBMExQhbhcbTYSyMlEkkgxC4cDTClrDqNz+e2TBmQwjlYFaNqEz7IzSlwuF7VxZiIqwDXYQhmyYcqgzHYxgBCBtX+QjwNQAzriCc0mHoXmdDTtXAMp6hJhSdQn1RGIqCfDT4CCW+TSHEYfwtqSQkgzB2CEJemE0YJzn2PkWY7msmhHlQV4QYyy0Ik9f3C9Gd9uGQP8OEUypZDmwK/agI4IOEYwKHSxVCCOP2Z8KlIxPOxUPydI+QPTtHCETrQlHO1HtDqIiOCEVpZwrVYAMAFwhxGuaDQnZvFqnKQAbCC4UHD1P/Yryd8QKeJOSfjTOE8RwpA7lQNjxO6N/FVoRolLE8qVCtoCDUG84W6p2OC2ktya1CNAhTRytCwyRCTPS1wrn7dwoh/HtruY81I8R9Qm77SmHxxQaEu5ap9p5VmAquFOIxYEPCnPkDoPeRXxJ8OPcAAAAASUVORK5CYII=",
                         9497, [388.46775, 326.27974, 271.75477, 233.55548], [0.59176, 0.56111, 0.64808, 0.70743],
                         31063954)
            elif (record == "SRR3581735"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581735", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD3dwDtPIrhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABFUlEQVRoge2YORKDMAxFXRCdy0WukNSqdP8jZMGAF8ADWGAz/zUZY1n6z8xQxBgAADiBx6ti3iKHzl99uXlIZPMZazqFJFrsMOyssVYhihL73iEMr0Q4Wst2xdsbds+qvzQl3mHd3N0w9YFha8CwfWDYPjBsn0oMFScmPgRDnRiKrWF4Drc31JwIw3OA4bHe1xqSsGEzjJydTJztIrSyF/sIDMsCQwPD/lxtht8J5P7EFGGaRo4/PBVTNs+vghdrQp9+mKxcCZf4ssMQhhF1Gspo6HArHh6SeAvOt+tr6B+d4924dqknhXH2A0MYzrWDYVBb3pCCjv6E2HDEHaH5OH4IP3EakYKl+CSOFG9T5m5hCMN6DT98qhrzPzcqAgAAAABJRU5ErkJggg==",
                         65, [1.27279, 1.06904, 0.89039, 0.76523], [0.32607, 0.34451, 0.39167, 0.43855], 64890506)
            elif (record == "SRR3581731"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581731", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD3dwDtPIrhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA0klEQVRoge3WMRLCIBBAUYrIuSi4gn0a9/5H0NGoFAxiWAib+b9zM254VHGOiGhAl+vO5Lb3n+NquxpZVW5YuxjVVk0qDHqrJhXGoLZqUqFb1DZNKgynFy5BbdWkQsXOLhQvcvQZ+obQfgjth9B+CC33golkhI/ZOvg0PUJoP4T2Q2g/hObzX2HCeU59lt3SIZ9NCFVfhrBLCFVfhrBLCFVf1lWYP+1nKilx++ElnfrcF84/d7Bty+55V3xYsb8wRYiw8gQIEf7aX5giRFh5gmbhHXQkaP6Z3OBbAAAAAElFTkSuQmCC",
                         19, [0.867, 0.7282, 0.60651, 0.52126], [0.23631, 0.23875, 0.27012, 0.28223], 27845864)
            elif (record == "SRR3581734"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581734", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD3dwDtPIrhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACJklEQVRoge2YS5qEIAyEWTh1LhZ9hZk1q9z/CGOrYALBFhVb/KxNNxFC/bx8GPPo0aNHJ+jn9/r629rw24O7WlRQ9/UyL2NsLSuVRK6gctcZ29lKTioJRYS266y1laxUUiGhsbZfqk2piLAzA2QlK5VUStjeSVO2SlsU5QiRibcmJIQUrpztpY56wojEF+N4q8oSJvFWpRC68Se7QRtTjhAPYTN6CBuTS0N0K0LtKeX2hLgZYXoP1wjJX3BnmDpUD+Gokez6hPqpwoNhqi5EiJK6Lo7Q/KjZX6TLEHKqkjc2hZASQiwTHo6o5mNUKHif6evGM84JaXyUIZ2QzER48PuTOkNgn1HS1/H8B+vUHgQhTYQKxxggVv0gRf4nMponThtURG24zY+EE59CSFUIo3xTiRnQupQLt1+ZLsQ14xEhTieUbof0HwhFm/fem3Zfek5AIfTSjKiX9mmBEOFvRAjehhhDTBiQnCxmCfXp3aDZBGRCjG4QVpOD0qUIKIThlhFgVhJG9TcLc3JECQUhMULR5YA/1lcIyaVEXyeUZeNYV1qXcxOEDMcT7vj4zQxHnSHykBlUTigqQFbfTvg+nt/bcjuhOChDMcsX2WGEkuFAwoFy44mDcYhEWtVBagfDsOIswtL9iCknbyt7WwCcgdx1CX3SnYT+8DmFsGiZwve0l1APVCJcO4vkR97f3tohXDeLUBrei1Br2Ayh+4iHpYYNECqT+A9UVnCK7SKz1wAAAABJRU5ErkJggg==",
                         9492, [435.13876, 365.4794, 304.40373, 261.61513], [0.54116, 0.52744, 0.60521, 0.65291],
                         27717575)
            elif (record == "SRR3581732"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581732", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD3dwDtPIrhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACbklEQVRoge3YwWKDIAwAUA8u3+Vhv7B7Lsv/f8KcAkkgILaolTaXWoohTxG1w/CJT3ziEyfE18+t47f469UHt0Vg0jIN38M4nV7IYYFxwziNs3K8oJSDgpKWaRy7OoeWcJp6P4dD38Lxu6+VBtJz2EUw6x2EeF0ZBwaz+hdSr0LiLbywjuPiHYQQttBtQabvPSKufhai38JMn3tFTgjYizC+rZODAXUjjMqfYQsa/Mbs8/P2lgE1wlsvqkDRNDWFr/eEWl9RVkgsTPq8QDQVUhshNF2v6i+c84TUkrijpG0hU58Litc0VwA+kgzqHymT6hUM3YrTYjHNZLlIOL8aniSkrX8S4p/XiVAvhJyQXkQI4Zbld0DXvHxuXz61wseIcgbGl7MrmZJHjqRAlQqVsOKvJFuIXkiusgeFYi+whbRTCAUhmKc0I6QgFNbdIf/oSZJAslCbQyghEOj3Ah4Bli6xZeCVU7QqIT4n5L1KQloE9oyTQiAlJBbOp9ZKQfLhMyqllRBzQveba6a1PONaIC2kjJBIv++F1m0hz9f9se6GMm2oYC0HeBxc7lB5IRnCcAiXDZXft+4T7r05r1VUCYlvwHmhSAF+lyCkVBiyloSyAnxISCVheix5iHW0J4R8+FoLQ0pZczQYAMkJIiIvlAcpVM/C6ADJ+XGAkN+hYyEKoRmiwv9rmIUoM+SE4buC1AmNrk8I80Mgp0ElVB02hYWyy8Ll+WPjXPqcakwyvxWE/5twvnDtDaQvaVvoR9kpdOVA1HCmELAslMfBML2+0K0RG0KKa9grjBtOFKpMJs7sqUcrZU5KbCrccund/gANv05NXhMx0AAAAABJRU5ErkJggg==",
                         1879, [63.58575, 53.4066, 44.48177, 38.22917], [0.55033, 0.462, 0.50078, 0.58722], 37548470)
            elif (record == "SRR3581733"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581733", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD3dwDtPIrhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACXUlEQVRoge2ZTWKEIAyFWdici4VX6D6r3P8IdVB+AkHQokLr28wQgbwPGERHqVevXr26QV/f/YvONnx6cCWhEAM60oNWs5rnNm4uEKAUPEI46Ulp3cbNFcoQStGMtJ4mPes2di5QHaFUyWpZoMsUTs0ctZa4IBPC3VWrzTw2c9RaTQjn5cfYzFFrSYRAFEVtUVzTnauSEPnnSIpZPsoSHtpje9EhwiQ+gkiYlhxhGh9AcJQwrd23ZM/jEqZ7Pf0LwtQ0pYSm3D+hzGLvBMiicT1T5SV8XETAAxAToovGLe0FvNbi75RuIIyQFCkHkhCi+hOE2CMhlCp4r6nxmJDyhKQeIyylJPeALhofgLBwUgQCxO1bbBA44QpGiuSheIqwdBb2XLWE0BchlAgpSwhIKSFuK1ckJLoL0T+IiqPKIjuEJBBSkfCW5ydPKI5qaCLYLePVZwFrCfE+QvBL8wSh23xlQqu4y0UQXLr2lRQZQmNMIoQCIRudI4ThpWP/bOxJGivj6rNSESQ3EERCBrCrMCaKyyVCVA0JeartzmYTkUzoIiARYgvCzza8/5a4VsBTbTuMT3WCUCA6QbgOcAPCKNXqJrDGLLphcIR4DaHdb1sRIitiYiVO5f2BnePWhCDWqVXwWhmA9wNrqZ6QV2hHmKlUKUo2Qlc2HtxZK820mr2TEE8Sov8a9pPJwgjpXsIzk2jybDfBXQdpIlMhPJv1SUgCIe0m4UAYB7ohtGeXMOcZQjnQASFwjmEIsZZvO0FHDQcgrJzE3NCMQIhlPMi3qyfEuKfbCNdXcBg8Av0AOxfcSptmGS0AAAAASUVORK5CYII=",
                         6671, [317.78435, 266.91172, 222.30781, 191.05904], [0.52201, 0.49582, 0.57278, 0.64379],
                         26673727)
            elif (record == "SRR3581730"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581730", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDn/2U/mK4FAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACdUlEQVRoge2YS3aDMAxFGVCti0G20I410v6XUIf4I8lysF0IJs1rT9pjJOtd/MFkmj766KOPXqCv7/H105t49s2tFjTEzss03z+uJWqIXebpdv+4lgjrY+dldngXI4QWQgd4W6blKC/HKCNEK8rLTdD5akOYEz5bl+tOc7sd6Wd/NREOL8ybAEghtazL4YR5kwN8I0JAo+0/ExrRQwnzJjA2kTKhFT2S7PGy2sqERhcD6f0JLXua5dGWEfpUGpGQea0khCIhnUG4+SaXvDrnOhqS6TSFRyPMSwp3QDEiX15uVGsJyV/Iyx0hPhLGTqEJg6vc+NoUCCmkPifEbtsN4lTGOhL3mdndJMQ7IRQIyfe18xMRrUZiezYY86ZACIlGXEyE9x/3u0FoeuqVfYRghIYZNazJ1CYhnUIouvObAaWXG6ukePWBJkIn/6eCsOX7uKJUpUBI1YTUTBiUGXFhilDV7ZKyFA8WRH7bK7gRzgQh6dB6QlKEu0xXTRifu+QLkKgZk4D9XyYEfrWCkE+IaRfCzBIjXCuhRQgxCSxC5N01EopLexzCNSE83CQrJmFKAhSj5AlBdt9BuMaz7a4ZK/rV9nNCMOxsEopdqpcQ/kIYExUhbRFiRigYimPWShgOcJ3TlCXKYhDcsJspCN3gwGsJ+wZxTcQnhEi5YgAKQsmwKyHP7CBkT/bMgSp2CiHG2dFCBsyVIiSjSIGQ+PQ5jDAe7VoIQbganbAQ9VSSo58QRybEXQh1w7GEWA0IodO/EtoNZxNSeguCtySkMLcwVrkMYdVCBCPvOoRYQVjOuwJhxSCClXYhwsfSagVsJkTd1esIs/BfZ4V34XDT2wsAAAAASUVORK5CYII=",
                         13255, [511.88466, 429.93941, 358.09176, 307.75648], [0.5946, 0.58088, 0.66676, 0.71829],
                         32902802)
            elif (record == "SRR3581727"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581727", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/2ULgAcEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACfElEQVRoge3XXZLCIAwA4D50c64+eIXd5zzl/kdYqZSfkFhSqKLT7DrjIJB8FGmdpiuuuOKKF8TP7/jxd3Tguxe3OsjSeZlu07ycVMk5ASbhvMzTcn99UgAQGrov7n85pxQX2H9Ks/B+AU+8hth/SrPw/tdZCMlb06EgBArTE9FupxDzbb4tvU+aZIktQsCyDYW2Uti6jOboKJT24wcLhb7c8ug3kpAMh4KkGVMIJwupFNYn6RIQC4BGYWHxjYrwVdLjQs5x+7EcrwpxcGFZ+NpUjheE5O7B8FIhhLfVp0BZOBiEZNwwLQFO6HNJQo2sCFnVIAuJbMvZFJAUJl0EbaEFjUWI0jZvjjy5vzpWITymKbYklELHe7SyKaOQZ2sL9pgFUeUrE79IeQNst0xBSIkQ/AlGqAgJThFmmZiQZCH76UOgCSkXIu0IQ9aOwSasFWZFqEJ4XBRKziw3p+gohSzp0ShqoiydLKRnwuSjJqH0M8UewHP5akIunJRqeHEYpxOqxjQb7ArX7n1ujFkBvgGnPSGkDWgWZldKFWJ85ugpBIrnZ6WQkn3cU0gtwnh+8mSrkPaEbMQpwnUVj25UN9h/jVkyf6MXhFmqOAQgdgwEDGfEu4SkCrcEiRCeC3PDJvTzsU/rhTS+kIuOCYs+DcK8gkSYd3iZEIsTwhKQ5FSEBTB/zNgRUruQWGWVgbowr1cX0tBCoKQ+USjA+BJgjbAUmYVar6dBPYQUCh1XmOW0C+9H1JBCDI9aW5ajwvA8MJYQtuOX13BEiCMKaTsfuwh5wyBC353l/BYhCAOPC+WG04RYI9QHXsIPEYI+8EuETwZ+gNA9Y8SfnGv8A4ifD3j8+00tAAAAAElFTkSuQmCC",
                         2205, [103.10003, 86.59523, 72.1242, 61.98604], [0.59301, 0.57086, 0.65904, 0.70347], 27175344)
            elif (record == "SRR3581728"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581728", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDK/wAy1e5hAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACoklEQVRoge3XO3rDIAwAYAZX5/KQK7SzJt3/CI0fvCRBBNiJ288a2oQioT+2CXXujjvuuOMN8fV9/fjpTfz0h2sOQPvcaXaP5ccVAswzCe1V52ly8zy1t3NC2K9Mi9BN0zRf5Bqa+4Ym4fy8hBe5hucIF9tlhGScCOaZz3g8rrPT9Avx6FZOin5hwyX9aBAZvy/+sNDYqRTi4c1sweu2HDVkkFUIYuJpQraQtok3oP+EUHYIylCxGimdypHPCsVKipAlhQFVqORrQgrFDg3ekdahNpQneSEMCbfEsY1AhkGoXVYpxH2qUSgf2CgUBYaCr6QLRYtM6D8EIcStphiqCQ9+IHuFeVImTP+E2+RYkvb7uSzUtqqBALYS7EJIHgeQamBJReH6OhNiWUjZ74OiKIz3ivZsySRduFWJ+eiFfF13rhDz92tTUUivhEAV4TJOcRPxd7wuRKfeMUPB2/crr8LtRh0UEoIQoribXbhv1d14IPqEy6zwxYyvhDEfdi2VhDgo1M4munD7FZ4ivmbW3yooCMmHUUhyr2oKuY/vLTAh7Zdlaca/bBJCNjEV0qlCSDIRTML4EnXhs4wU+uIuKZO+9/CyEF1XQMh8vsqElM5ZokWYGsIHlIm40A8rwvShds2ncEgX0oXEetj3iZoQ0gk2oQ9NmK+mnWgrEduKRfK1WAcWYW4YFrLVGs+oFaH/16ws5IfXqlCKuoVNxJpQ7UBpB8F/K1eESr1G4XbuQfXQ3ymk/F1JCGsinC/EdQDkrFoEFyRrdgjpFh4kBHVWKULGEcL03HyWkPgW8SKWylGYJnYJ+cApQlbKItymAw0L9YGDhTz1RVAQEku8rJA3ahCimvhPhJXEW3gBoeHrAtS8W3gdIfYBm4XIa71N6CtAyPgFF3ryDVu0/agAAAAASUVORK5CYII=",
                         5171, [200.58209, 168.47183, 140.31831, 120.59442], [0.60632, 0.6174, 0.7058, 0.71168],
                         32757267)
            elif (record == "SRR3581726"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581726", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/zJgayrdcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAChklEQVRoge3XTZakIAwAYBZOzuWirjD7rHL/I4x/kBAJAiVWWWP6vX4t8pMPRWjnnnjiiScuiD9/vz+oteGnJ7c4qKby6F5uGDtl0imgRjiMw6QcuiXTJaqEk25w46tXLn0CCCtqj8M4I28VtcJpKf6ycHjd8kuDn06hc9BXCaFDn4/w2ugjVBti1f54ctRtzoXxVUKdi7rb2qkpxLYe34j8kvkBIRwJIXfbbHYjIbUIYS/0vTRN2FvxXwhza42adraE0F9fJOQtEC4XnnwWMDY7nsg5l8yYcKKQtlsN/WUGmn4S5cjwAiHnWnz6yQjPPc/thevDI55Iul545vFmHihe2UHohzlDuG+fEuJa1Fm4YY6EwhQJ07klZigv3FVvj136hlCPaQqTDzFqDqHZrlI3oRjK7+6iOCUUnzstTCQXjgwLLiy2nZCC8P3XFPzhLy8krhIlDkIYd5Cc/tB84R8IQXbY/jAtIaxC3MpN4XS9vWw+MfRp7nIClELMCzHOqPJhxhMvhaHcC2ETTg5ICOcCXk7zBVG4dGrqpZAQgV+SjBB9WdV/31QgXAdhYfjzUIjcPp56ksKlP6dXrxDGwzULQQnFkXBhkRBSNKRIxhLSoRBtoR8ZuaxKKCFZIQeqGmkhaSFPCCjhWrezELiPJiEcCCGI3LbNsXDrzBTK3mqF6sEVCimqAeywhVLk5N1qYaLWkZC/1EqIok46vl1IxIsHbKENrBDKDEFdFwvB+e94sRBDWnLMWqHooEhoXKuTUGJsCL+KhZzWW0IKL94FQplaPuLqtpDrZYRGQZWQXyhLSKrp3YSih9OF6uQXj5YBfk5YtBCjnvEHhZmGdxAWGG8vFF0s8Q8yf+SoozbOtAAAAABJRU5ErkJggg==",
                         2259, [100.04268, 84.02731, 69.98541, 60.14789], [0.56944, 0.56926, 0.64864, 0.66299],
                         28691694)
            elif (record == "SRR3581724"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581724", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/zJgayrdcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACjklEQVRoge3YQWKEIAwAQA/bvMvDfqH3XJr/P6FaJYQQVDRSbc2lLULIuAhuu+6JJ554okF8fF4qvlyz/fbNNQLQaCOjsRx99+7eb59yTojjwlf/6vrep5ozAshqw5oUfffq3r1POSeELTQay9FPyKuGhakVjqv0dkJUvRYyvIZ9ZngYHWvyjePCK0W+b9L/FZLu9xPZ+EsExN8MIbJFXCwJrbPzYMB6l9UgvvPGMTcKKVwVHQvCrP14dVlJO3IsCsfA+Sp3pFyIUxd/oUNC4rWVCyEVhtnaCdFFSLFwVNdsITQTuiQEJnSUEbUQgVvTjq2ElW/EnCTuE2hcZOGQnmDY3WhJWF/BSnFJwj35U6EuPBFOMoLrC5MzhhaEYAihpZCKQjG/9UqikxSEs0kLyRbCSUJSDXMx0WEJZRXRkAnJEtJvCiHWiuwgyt4W5SCxl4BaE0zC9E9T+NNyjlCVNNeKYaO1Jh2W2tQfbyFUn8c4AQQhThufnpQXMzoL0wQOL80lIQmhUY0UgjAcFU6zIWc4IER+xIpCsoRhbiGUhlkIMl2NkJLj89DXAkqEMU+YefwB8a5yOfPt5S9EBWFIWC1EJyHxsbcknC6BLAeQuFtRSPHfhzHNRmHSfb8QYhI1GawJp4EoGmyhFu0Twt638HWhKMUSygZDiLmosVAkSSdjjSplSZgU5SWck0Pl2Qjh8TCEab28NPcJDdE+IVUK06osIdeTAxsLY7btvPhl96AwrOHThWB02iaUc9pCK4RQN5wklCPXI+x5HkJsKtz6IYa6PIR2g69QnFhbgXHgPYR8DtcKMe4mFxcWehVCznQ7IW4Rlgc+wgsINy3TewvxzwvXjbAwarsQdaqGQo38BkSeB6npL8ZnAAAAAElFTkSuQmCC",
                         2376, [102.79822, 86.34173, 71.91307, 61.80458], [0.59023, 0.60503, 0.69304, 0.72041],
                         29368794)
            elif (record == "SRR3581720"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581720", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/zJgayrdcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACXUlEQVRoge3YS5qDIAwAYBZMzuWiV5hZZ5X7H2F8FEzCo6BCqzWLfi0GzK/4oMbccccdd3SIn9/Pj7+tHd99cEsDqCLZDsZOH6eKKuFgzcMMrUppFEBYkT1Ya4ahUSmNok5o7WN42Fa1tIkq4ThL7fRxqgiEgLG0JU55pyEtrJq1Z4i0EDpX0iggI1QbThpfIVSPfN9wfeFFbjlfKsTlC3avpkVQTDi31L3OFcU7nj+QEx5OrFnGHBWdhUcOGL3Vh2154bHHHFAIC68CVcQ60fcLiQ4+iWpSPIX04uIMhO53TBhZzieEaBoISQuX3QBmjbw8mCeCHy3sVyXEbsL8xSCF4CZCpPDx7FYJqYWQ5M9p+BdCsXX0ZYUom2ASJ4TUR0i6NTbvSHbJCVUTQU4Ihwj53UDvavo5bifeHJ5OvhW1EMNcvmqYp0dKiItw2aQGqgh+XaiagAvRV61H8EWAO4VJIT8p4IcWRzAh3LGKIi1ci3ruAFkNkYlXIUQlJCgW7pirXBQXukATfT6tcwyQpz67B3WvQhGvhJtfbYANDnJnqgQvlE8/1gQi1c0If2vyB6BU6E4xLuvFjYuCjFABVyGuvbFAGIxXLPT5MHO3CXnFcmeqgilNXEdzjwJhKNomDHKqhFgi9Pcc9lb2WhgR9RcSSGG0gkg5/YSy534hhTuJCaGXkEwiq1zo/vX5VCEksrIB6xp6j9C9O7YVprK6CFE3fIyQ2PNtjzDe0EyIVUK3MLqccP7zBZZBQXS8iBCILZ5lx4sIl0T2eSphCTHT7xpCyPQrF6IeqpswTP4HJqZIVQdanDAAAAAASUVORK5CYII=",
                         5170, [251.0959, 210.89912, 175.65553, 150.96446], [0.58855, 0.56243, 0.64534, 0.70871],
                         26162316)
            elif (record == "SRR3581721"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581721", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/zJgayrdcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACYElEQVRoge2XQZKsIAxAWfhzLhd9hT/rbCb3P8KoIBASlRZUtEx3dQkJkEcwoY155ZVXXjlB/v1vSX5+q0539eYqAlg6Q9ebz/jTqpQT9l1n+r6r4MsxUk5ouuFj+uJpjpIKhP34fXIMxxA2fUqpdIbPp/FMU0zYutBLeHt5AOEGAVGFenGtbBISnuLHYbKVKz0hC+Wdju4uwluVkNhZ0NRZhMrIRgQ4oQgNLhEit2uXkFiuBEo9JZUQRPa5MBvB+u6OhKHigSh+o7Zxwo1cTxHC1NL0Vj0RWj0Iw2cQjrpFwuuSq3SanTdGKB0HTogrhKdGMXr1pC+GHSlLSKGBzJITDowrhGdGMVpLXTnq+pLQWoKc1ffULxuo9EU5P5MQQyOygz2EmkMlol6fEsJ0zcFBazATOBPbCFEAYq8p+A1YIETDrwJVwikLk1sOw6MIYiBElRCDnSQcX8ZMwiovpkoIG4QUCBmDO5LAxpYQStcyoRKYuOk7MejVGhf7nBJSZCcJaZVw+KXQdwCh95QR4i7CRBu1lW1zXWw5ubd5wsYlS80nxffCkjcrhJIolxD5hsq9zSacx9n3CLkOcd5PTIrBPGqdUCHKJaT6hIn7YENgHQBJCNMfpeDf8YR7juk0iUt36VoxoS3PnNA+HUiY7Gd1QmCEijv26YaEIrtfTBjb7yWM75FEIrsvEELjhM46nmMPIZ5E6G6ElQh5a53Q5btDCcnILLgtQPO1qJBQ7ahMSP7G+z2hztQc4YLVFqBPEzcixGxCNysf+BRCHK+Y6sAbEGYcU33ct4Sc4ExCGcU/r9TpAunojzYAAAAASUVORK5CYII=",
                         3182, [137.87104, 115.7999, 96.44845, 82.89114], [0.55642, 0.57593, 0.65784, 0.72142],
                         29325971)
            elif (record == "SRR3581717"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581717", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCBghG+O6sJAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACR0lEQVRoge3YQXaDIBAGYBfpnMtFrtCuZzX3P0KJig4zAwUTUKz/62sSRJjPoCYZhjt37txpkK/v8+dn745HH9zsQEHf53N4vP71FcKCzo9hHMdKhdQKFAlHJ3yOlUqplHKheyO7SpHQ2dwqvbjwMTzGWrXUiRKi1avjAEkh+Seivdc4IYUttG5pXkyVpITYupgqMYTot2DrYqrkPwvVJajTXF9IMaG+jXQQQN0WFdLphaibriW0NMY9HAwhRTacLO8I0W8wxmie6GG2qju/0PhFJSYEvcRgCNtii3FuOEioPbEi9G3OdV1rnpYwvf7SwiYnIlcZBzUsAlm7LG8uee7hhJQSUhUhoDke+3Ro3INBLTzgZYquTAh5QjnfWxHjLTIIhXLKUAjkT0zjLAqENMsIDhVOE9NmsKYkIfRvsyGkQDhleThIuLwsEbKitBAMoY8ak6iCUC4XL5xaaZ3ZvO5pA8i+HoO8a0IYdC/75T8SqyTcptue6mJEZVy4FraSGgvFVUSuOC6EcJnlCREo3FYsXL8r4rArIMtDvmk735dqU0IwhVq0S4iD7JMbVnB4yBJCEgN4IRpCQ7RHuF2idwmX7wBiMv+CTRX2wOmTFxf6qj8rdNtwvq3sAU7zmMK12pgQ2AFYhIHhg0I/MpbJokKzAl3OLATRUEUY6ZUl5HOG4ySA/FNZC2GsVxuhbDiLEPxE7wrthpMIXzPBJYXk1xaKa0sHQswBspnEjlcRxnfsQJizTM39+hHiXz5I7ZcvRDlWM6E2/gJvGP8EWBtPkQAAAABJRU5ErkJggg==",
                         9864, [338.52372, 284.33102, 236.81615, 203.52801], [0.58289, 0.57122, 0.65372, 0.70073],
                         37024502)
            elif (record == "SRR3581719"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581719", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/zJgayrdcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACP0lEQVRoge2YQZKEIAxFWTg5F4u+wsw6q9z/CAMqGEK0REXF9ld1laYD/EcQ6Tbm1atXr07Qz+/99be14dWTu1pQkNtZ8zHG1rJSSSWEtuvcx9ayUkmEBckO0VpbyUklQRGhK6H9fGp5qaMiQtv5p9DW8lJHRYRN7jQZIV1io6JywnAv4s2K5gjhKcV8PCEQCZKJEM82U0VfTIjZ8m1BmIcUQgpxJf3m0vYOjRDNS3hXKYQe5AsJyTRBiDIAgrBPaJgQUEYIOSGZuGWeRVjyZ8Ka7lBGPMtoGjzsAiGNhFkfu3TMjIVOlAJwQn9FvpCLhAcXUXSX10CVyIrrULEnCGkF4bGIYiTtVEj5Sk7ducVHY+vMOFxMmC0KvQZZuzRCZYRAcClhf0tJJBsyrfTUyYzxlDBKSTyeUPYHgbBfmMPlmYRI2nDlmvqeJ6TAoQ2Z2hOEKDIvIATfBTIDqdkeC/oVgzMPRmpvythNSDxfDFpICJwQ+FduHt3e6C6GJQeKmySAbA6GS36K2EEItPk40kNxwjjtYYDJyuhfKUy8yQinYxrgZkLopxnNFkFOyF7YQigyBKE/VueEMTsilRK6wx3SPkLSCIUDhZC1GlqEGnNChaiYEMeRDyNM7zQxQuCESQ/HEeo5OwhpHaF/+DEhTBmOJyxbp8BdbSSkuL2eRFhSxZRjB6EM3IUQQvpeQj1wA8KY/lDCcfNF8ZJvgBDX4LGRRMOHEC40fAYhLDRsgHD8gTOLt9SuiDAlOJUwS/8H+d4LcX0uLQwAAAAASUVORK5CYII=",
                         5547, [251.31921, 211.08668, 175.81175, 151.09871], [0.58505, 0.56309, 0.64725, 0.69828],
                         28045149)
            elif (record == "SRR3581716"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581716", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCytCqgAYiRAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACaklEQVRoge3YS5KEIAwGYBZOzuXCK8w+m8n9jzBtC0JC5KFo05apmoWI8H+thTjGPPXUU09dUD+/XdVf09E+/eNqhVojVAwwTcM0TlObNCcUkNaqNm7U+P4bmqQ5ozaEWD7C9OaNbeKcUKoQpDB5T4e7C8eh64e0gXAYexei1ihINStPb/XCoNbIG2pWnk+W9pZbhYC+kXoSKqk3H6kQsXZWhNCXMJ6bxwmyfqdQmZs1hWullrN7YbQmmDn0xgFR9EzDtwsJQlUUnAmJNYoh8WDOuiIeRk4eol9Ryd+cWDif71xIeeHaIQ5eLrz2lU/AQqM4HQndMWWEGLbKfgcz15UQRnvIlJD3hUfoW8Qk51YQlNJCsEJcD3hfLiS7Q4KEUNs0HCr16cgL3QsiJyQupGUDlBCqXyJHSnkX8NVFEfp8kBGCKqSEEJsLZXyf1D4vFBMpEFJSyM4uP9y2cG4AfHVB07LEVOCT2pdwWoixMNyHx8L5+SYj+tlBjf8RGpYUrvMsMdCFbCeckbqQnBBPFC5p1ihZoe8YCN3eRZwNjpPCtu8NqBLahTwjXBeLjwmD1QrEXLAM71MIIRUJY1GhkJoJ+YaFuBgN+hR7hIqoVKif2iN0Q8gRYbkFStnTeI0QbdtOYTC6mEy1MSFdJ4T9L/95iHDN2EqgCl9d4SIhVQvdljaYk8+WAF4sJKN9p2SLpepcSHYvUQUE5tgttFuus4XswsJy/Y8K8UphzU0E1/+oUG84S4ilvPXLBtiV/QvLbuI8sltB+Zx3Eb7nEBfeSgjahV8jxEe4tRe7kTB5YbmQCy4Uun8WBV3/AVJAwDIb6ZHsAAAAAElFTkSuQmCC",
                         9656, [362.48896, 304.45978, 253.58117, 217.93645], [0.58251, 0.58352, 0.66981, 0.71258],
                         33847589)
            elif (record == "SRR3581715"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581715", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD+zADl3MYdAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACoklEQVRoge2YS3qrMAyFGVCtK4NuoXeskfa/hMvLVJaOXzikkC9nkBIjWfqRsJ0Ow0cfffTRC/T1c339axzf9dcPt1rCeJzA2PgYxvnjVqIUoYCxxzh8zx+3EglCGRK1fYzXriH7IXKEmxGu7Th+Pw7XEE34XBEIMQEaQgk3gPUENx7v0kSzNFnk1U/YtdIQbpbIAsRMCtg2EUpTtBrZ/P38TYSIBq0pKUI6nRDgJFc9OJ1zx4SSJux9KVxK8YyeEMaMR9Qm3UHIyWh9MoS+SdoIga3vATqfkHVKEZMP4HMZ7Lb8ex91tB+TPCEP/donnyfUM4JHKCimISRtbG2nOc1ZM0FIw9MIKSYUfccFqCJkZWxN7RglCJcBGK1ZakVeCVnfWr5Fb5YPGjeeKrxP3EaYH+9UVEgoJxBKglAWxvWyQCi6D/KES6kXQlfYzdW+NQdVQzg38rRzMCbU6el0QWkc4VbAHKGJ1i7TVQlCXp+E67LNLcosWJQJKdhDQobR2uUIo9U+IpQ+wglJP8MyobE+kzCUb3uq9miXI2RtGBOK4kOE0Z2OUi6ZMyQM2Sx/VN+Y3UG5hKQShJH76YSkFjzJEIZDleobT7juJ9RIGClPeOR1lCQhh4RWqPWCsoRq8TSEYgwPEPLTCfff19u3CxCSMyiLGgnT6ZQIo2PqRQgl+sbitc3BVYQ8oLuvIFRpHCMMi0CWkMkRNRLCo3lZUk2IFFKkaxNKP+HsWCAERK2E22bcxkh3Igz7aDsh9xOGY85LCLmFcPfQvm9ESDcjjB0rtO8AdyOsfRN/p94vOwjtwKmEXEeoHGLPI4R44CzCuiIScPwQ3osQOb4VISHH2xDyQcB3Isw63oCwiEhZv3pCtpO9jLCAWHC7BeGi8H+DWf8BquvUmwSMHJYAAAAASUVORK5CYII=",
                         7260, [220.78941, 185.44426, 154.45446, 132.74352], [0.62543, 0.60792, 0.70166, 0.71268],
                         41781463)
            elif (record == "SRR3581714"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581714", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCBghG+O6sJAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACjElEQVRoge3YS5KcMAwAUC+IzsUiV8heK93/CAHaH1mW8Q+TgbSqpmoa25IeDYYZY77xjW9844b49efnB/Uu/NcntzaAGiYvq/ltzDqrlznRJFyXZWMu05qZEk3Cg/g8ITbMXpZ1fZqQWoS77kVCSA89caeBvLDp8p0WTduEFv+jEP2IGBiPnoQThORHxMAFpTpWDXehCNGNjOY+LwV16Ye7oKyw6THSUaruDI6f562suHaYcDR5UoondF9p9FBKnlB5YeU1kBdCOjIYuhB4p6AIc01UChWHbYNmCHlCKyQgxyJMK+abKAnRl0mFCLafa+9EUYq8kNgEWTEvLDVn12nC4wjcKyQ3Qdz70C3c/mYil+EmoSzlhPtR8kJRMn+rlJrbtqibhSBvbCaMflWa0aK0S7hv/24hRZ/RdAghApzW83XjIU14waaqCckoQuSrZHvoelEat+Ni5e1Cij4bLoSMMLq03Q4zKqTolGO3kL2RkC50cEzPQWjmmL//7M/OMyH7p5NNXyek7pdDCMkLwq1CUYjbDEAmFF1tevf2YC/B/ZGREeI1Qn6hq0JXZ58oZyTC8HWrwv35QPZNB+KsipAgZIP0bA0L4UMLvrIQS0I2anjijJBl6xD6N82QnWfcc4oeEmFw5IXpyWgX+t2uDejmHytRFebDgaTQrWEjGP4WOc0/TXjUAU14AvQgwFgYZbAEkJdIuxCV62FISJVCWTv0jNFHKWoXAl9YGXEb3UK6Rcg31RZheJ8YEcoDU4TxyqoAl5Sv7BHijxbiBUL9wCxhw15jhW73e6HwU0n08B4hhpeTdwqJXi4EZeG7hNrCxwix7IOThfVClKnuEpaJOvBBwhIxA3ySkGX4xF+HIOynVDoARgAAAABJRU5ErkJggg==",
                         6316, [238.97891, 200.72188, 167.17902, 143.67945], [0.6087, 0.58488, 0.67093, 0.70435],
                         33582097)
            elif (record == "SRR3581713"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581713", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCytCqgAYiRAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACoklEQVRoge3YTZKsIAwAYBZOzuWirzCzZpX7H2FEEQgJyq/t9JiqVzUikHyCPKuVeuKJJ564IL6+7x8/tQPf/XCzAwr6TvP0mtU8qpRBATq/7zyZf/OoUgZFiXBZPmPsmgiwbrr8QDmxHFOLUM40XJjIK8eyS+dqIaJoKSqgJooSTOaYmV51mWKhriigJoYncBEJ7WsJIC9tv2BC7W50zrQIw1Q2MZ4I26tgwv26++K+S4gpIbvRGMCEa/FECPzzo7kKYCfcKCFyobmkQp7z7whNIpLKgrdWl5NtylQV2cdEUohXCjWSNqEcFnJ5QtsthKjTSVPnkFie9GF4mRCPhDZXfBgpdx6FLXu7UF6mcB0qJKsJfza+TYhDheBTSkJURAinQjMd7u3C9qXHD+4dmRDlGxUB/pwMlsqVGAjN3+whqEi4XID2y83zhW2YI9SqMZgw/K9vvQIn1HnC9IY2plJh8yKaMuxGDd+3IDMX6ngG/3ckjMsjwm2R4QIhUqGb0ibIECKZLS0EhGh+817KQvdsabYRQgdcFjvqQYXAj12+oV3JsM6mxwnBH3jHQn0i9PWdCbcVpEIcJ7RzYlqILEShbwC3oWUhhncXIZmVC3VHof9GCqfkQhcJoXsCXqjjnl6YnpIKK48aOBVGFQjlBKNyhG7CUqGdo+R3ceU/qRqE5g3S50Jguz5T6E6A/kKkVwVCYoiEXlQpLHwhsYdwHXgsNGXGolxheG95TmVC2AbSnFVCoA1MKIjqhIU/u63Tu9emXohXCf24nNjr6iHUFwrzifuXmP9aubnQ/EokdDoAhl9ircK4YYgQyMizgK5CuaG3MNHrXwvj+CyhNPCjhCANfIS3EeoM4cHAzxAeDcwXUsGdhHA4sEEYNQwTmrFAu/8CgoBWUK9VWMcAAAAASUVORK5CYII=",
                         7069, [274.16865, 230.27825, 191.7962, 164.83631], [0.61227, 0.61843, 0.7085, 0.71015],
                         32761627)
            elif (record == "SRR3581712"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581712", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD+zADl3MYdAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACqUlEQVRoge2XS3brIAyGPUi1rgyyhd6xRtr/Em6IDZaQZMDYMenJ39MBoNdnQI6n6auvvvrqDfr5HV//9jpe/XCrBS3G9+kx3e4nVdIo0lOIlYaubvfbdH/+DyGjcMJKQ19hD6cxCKGe0Jx1FPbw+TeCTEJjDsAjNO9nIBxjC5+EqkKQhPO6T2id3tvjeUofj+7qjhDoDcum5gEowzhsOr0X6DMJW95cmpDIJCSH0D29Z8rqHr5tBSGNRmj1Qk+KMKCIoj+dMMNxCfOdTYRqvl9YMjCah68aQtgg1HvbKwQsmZQJ2boiJEVIHiGap7dTQOU2cgAhMwCfkBZCGaBTgVBm0uFbCHWBJiFahMEVDiekPJNxaC1C+YosE2L0gnkMFxLO8UHaqJxyZo2QX7qMEJdhvrGr4ctYpduhGMPoA68RgKw69+c+yDZZHUm4ijD9CNSEr6W5AWGyUf7MJ1DEPdeX7jrCtXqRaiXEUB9ODqFsn+kplQiBmPKQJK37REtHyVPBEp8RgkEIoxOGY4UsrCwpUTHCLCf34eVCgZCEXMLudz6rOX9mgpC2CGVziQ3KCDcEYYqInHDG1M2ogTCV/CbC2PA0IcaFgQhxx3WMITcIXwNihLhNuPb/QwlxSm/mFoEAEYTEFmi+gSmXUQ0UCNMvog5CUAY1hBykkRAdQskQCXGyVusJd35GJUKWM0YEyesSMrstQkXUSmh9fFQRkkdIYoQslSxnfkoFQjqOsOIDPQuBVYQ8lTCYHxKcTzgfo9DcLyDEMqEm2k3YdFR3EUqDNxOittpSqgv6COkthNhDyHMOS7hi1hMuUambEPOJ0wiZa0n84xp7Ce2Jiwldx79CCK7jBxBWXcTPJqzYRQvwTxFuuX0Eobbd3jyRU0YopgB/4mRCsZH/AZc8L5afF+evAAAAAElFTkSuQmCC",
                         3337, [109.48768, 91.9603, 76.59271, 65.82643], [0.59685, 0.58897, 0.67847, 0.70651], 38727212)
            elif (record == "SRR3581711"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581711", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCTcyYUg6nkAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACoklEQVRoge2XTXrjIAyGvXB1Lha5Qmetle5/hHEwYCEEBgKZ2JOv7fPE6PclgOmyfPXVV1+9QT+/n68/vYH/enKrBQ2+q1kf5vGY1sscUYOvWbc/M6uTWWohXMyyLg8zqZNJAsIG73X7ef5eSXlCZYNuq9TYpXol5QkVw2qe69RMbGeCEsLw2LR8P1gJIeUMVxXdnRCIxOviPyBEb8HBtUbnq1OecFu+OLYUlh6nqUjYdN2pKIXRI+puo1UilJYXJfK9izDlcIQwgxDZI4zNXiorCSkYxp41Ip+WveU/uYayCSF6w/sJ06GXW8gRQkTYO7f8cAGdMEqt7IvcLGPl9Cu7bR8YRUj8syC0j5RxD26YDLlwzZDGVxL2HgoFQtAJk74TaPDj0nORpxf5nDWESrYaMcI9YWSShNrWF18rgludkCE8BqlESL4hd6x2X+BYH1nCI3kFIfmM6Xs8qrcdWQ2E0E9ItYTgK5cI0bZyEKanAyOE0H0NYfdrg2V3CUMiRkh2G+DClg3PEECermXCUMBOxfYZTglxGCFRDOCy2lae+wdRzkGcAXZCYoTKwSsJadFnLSXsPEzzhBQIifbOTwmdPUeIRJxwL5YlRE6o+FSKtxET+g7OCI8Q8HZGKF1REvqQlDCUoz5CXsfdxEqEe8nYY7/CccLgqBL6FBGhTMkIuS2d2TOB74qFRv0dK45SuTbsNJ0RAiup5a8ixH5CXrPYQdoO7J/EgCCk46oeW5sIIYqsJqQcIcVPrxGiWPU9hGFDtuzEUYSueJ5QIWomzHkV5Su9TCgHPoUQRhHqA59D6E+/exFCuKeES8N1CLGOkNxFCUXgnQjlW/xWhDbxrQkLgRcgrDhqQI27DiGeARbjrkB4hlgOqyeMCd5KaO+J3PUvXC6jHbuEM88AAAAASUVORK5CYII=",
                         6134, [225.87168, 189.71293, 158.00979, 135.79909], [0.61559, 0.58185, 0.66759, 0.6973],
                         34507004)
            elif (record == "SRR3581709"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581709", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD+mQAiEG8MAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACiklEQVRoge3YS5KEIAwGYBc9OZeLvsLMOqvc/wjjC4HwI6BiS5epqa5uDSQfPmu67oknnnjigvj5vX/87R346cXNDuL83Fffvbr3u1ovdUI4P7cffF1fq5NaUSIcjuBg7Ct1UimoSDiepeNfSxEIGWUtMfH65oTibxCcN8Vwk3n3w+2mqSgSNhn3EnKFOeU6ISczqEbx64QZrxa6l3HU4bKhcGnkdGnGcwkIy9oAFe4vTA5yAyS3K0QnPUreECb7KYy0cGgmSIkLwWqAFYoKBRQ7GHpGDgocFAYWgltrCYlVJXBIoTB2tYQ7ioXnXoiTkL0OOcgJi6oXEortmGdEFYBQUPbhoLC+LhCkdNtC3R8QMjpW0++5mJ7iSIioUtnCWTV/yooMG0drKAnhGeepKZkhlFA49uELzRw41+wlk4KFw5wUNLQz1juenpDWDtczDwjFCnlcLDGXLzje5IwfH5ZLChSKFu5/ORzmYNu+LSW0nCRkH90RoZiehawLCAUJJSJkOU8ortD0RGLOqfHL2BClhLJMkStcDhJhobiT1RTy9GX6VIeZ8oTrRcC+UAqFxQ8ONhAlFHfHKpwa8Vt0HstGyO4UyylANt0rYNfDXTUgtLeJIiKZ50wodO6EKpgSQm/ZlVDtLRQS41faDeF60w6F/i8gXNeA00KOC1mcSApJyg6ibAglJlTtTF9ovxBMCYXzOhYK6QThXDIlBKLLhE6h3UK5VlhwIapCdxcSzooHObcHp+ZdhbJDqCH7haw31BBSqdB98lILwlhWLJzKxEeFeMNdhMv96euEBAY2I+RHGBv8VUKKD2xAOL+Fb1+OjQvZfePMB7YkZPSflG2dzferbQA/KLT5ZsQ/HkMAZjsHAp8AAAAASUVORK5CYII=",
                         3766, [134.50222, 112.97038, 94.09178, 80.86574], [0.63248, 0.6271, 0.71889, 0.73161],
                         35577557)
            elif (record == "SRR3581710"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581710", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCSkyZLPzA/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACMElEQVRoge2ZQYKDIAxFXTg5lwuvMLPOKvc/wigaJQkoWLHF+hedign8JwiUaZpHjx49ukA/v5+vv6OJ7364yYKM2L5v2qbtSlkpJMoJbpu+6dpSVgopi7AbGIePqgSEGdGOsLI+zCJ0eLWN0lzCvqttpskbpTWKHsLaBV9IuKyPqrxWDYRqyedLwKu9lNFXEuL8N2s797miGCHenpCqnGTRFsUIoUrCwNwBNyO0b9aNCWk6vQgREt/Ay5ydJUm4gNRKiLqA/Pmfl8EgITY1EALql+52hGbBHllm04DvIEzYBuY0aYyDIKQtQuIbGe0laP80wXaLOgoUM8km4fwdpo5VVRJBEULTklHox6ooAVoGgvUXIqQIIXFIuv0EKUu2S5d3R2T5UV4VlpAMIcEGoR9+kgzh3DB4AaZJMXDd5DD1oh1jFCBkGSNEijDnfxsx6Vd+rp5AdMsuIa17LlEdM6G4ihOK8FMIjaU0Qj/HNwU6+EXCE4ZriHC8JNdLw+BjV9ZMCiFIy/mEr885pikmHJsB/ogTQhnC6dbYNjaHhX61yhJjjV/VU9WES6hH6BY26TqXEF00mKA98TQ55IEgXM65DKGxMySCTygYQFx5RMcI18w0AdfpnnKIMACm7NC4gbmAkNaajxKu5z5xB9aOC0BdUIYwHLUDOIX7bcrWNgA1UGnCWNQXE/JWEHkyqYcQ0wjXaV8m3oYwmlgBYcowhVBePYS4g7edl04oCa4ktNH/FEiEHtV1HeoAAAAASUVORK5CYII=",
                         8728, [282.92207, 237.63039, 197.91971, 170.09906], [0.56187, 0.55823, 0.63899, 0.67909],
                         39198836)
            elif (record == "SRR3581708"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581708", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCTcyYUg6nkAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACb0lEQVRoge2XTZKEIAyFWfTkXC76CjPrrHL/I4y2oIGEX5XGKl/VVE2FR5IPFGljHj169KiDfn7H11/rxG8vbrGgxjyZt3lNF3VylQjLva/pZab5716qIZyWPZw3clihEoOQUDM5vd/zHppx9xBQC4aElEox+FMaIQyQ0oRjnzSgNV9HOLjqCFX34NJ6ngFDQoy7R9dDuMoRhvE7SOs5SjjH8fKOzpbWc4wQvkNYdUmWGp8QKgi1r7vWtEJILq6kuFjigpXySuveNBukwQgzxxsbloRLz6MT5oryr4FcjHJCNF0J2bt3jJACwm2ruhFGjpG9TrYoEez/CkROSIYShFRSrEH6OwZpQj5pHt4evxzhnJaWRU0ThtWOSV8yYKeLSrgHPs06d55wGac04cmbGFZas1M5ITFCpXGfkJKEtFtOVNC+fTpXQthKoz8JJCFuCKE1JMRP9iRhUO6IxEPhCNe1RqOvKtthSYihVRKSkpMP+SkOSbRkC3/CEH1uDhHaHdQI6XxCUcqmJyeUFuO/vBlC3jKQJ62Vswi3FBFCYLWUmlBMCHy0HyHgnAJZ2j0hFBHy9jwGCDoH4qP1hK2oSw7ghHst2yIjhK8RAtb8qMkQukSw9oAkJAjtB1AjRO+K00Job3athMBq+sW2biWhdbBZ64zN6hEKolpCdIEmxDyhJmvoRwiqq5lQ7UAj/Fj9gCBU8jUQ6q6knJvX9KslADkhXE/IDrv+hNSFMOZKCVyho4TYlxBrCd3ZcIAwDIxBCO7w9Se2EOqBrxOKb9xtCIteRFDm3YewBPHmhHlEDfBWhOkreHRWJaFP0JcwtP8D4Y1mi1aej98AAAAASUVORK5CYII=",
                         7451, [271.5758, 228.10049, 189.98236, 163.27743], [0.5837, 0.58063, 0.66539, 0.71431],
                         34861716)
            elif (record == "SRR3581707"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581707", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCSkyZLPzA/AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACaUlEQVRoge2YQZqDIAyFWTg5l4teYWadVe5/hLEqkISg4CiWTt+iX8XAez+g1jr30UcffdRAX9+vr5+jHe+e3GJRRe3j4R5uGK+Kco2ghnB0w/QxXBbmElURPsbhiXhVlmtUReiGYZzXsScBYXnxcwnH/nYplhdPN5n+7jSkCdGq6liQEFZdlx3IIIzH6kyf2iLEt1jODUJ4G0LFwQnR9S+D0Deky9ul3p+QLEKUX/qWSUj+C7YPdLYgTwj/ihBaxdkrqH9+lRKiayIDgHJH+7MeMAoIG21X0Fm0NVDk2pn16b23hNCfakSYZFHWU6TItUuIe4R0NqG1Qo7vtvTZPMcQI8Qk5p8TyGo3CfH5szueqnpLzipHGFopDSM7CUJrOti6+unKE85263iZbJXKPH3i4MwxCRqjkXFibUJV6+sMQmpHCIWE4CORJOAGjHDZgrBBCIwQTyO0ngbHCCGt5Zsc0BcbW3/x4YTPEMr4iJQVLBeNWpbsb8hIOHdLCHngWkIwig5Ib5d12hab6GMszJo5JVQ3IdY9HFrhBSGFamlcShV7JVbLmImPjBMbIERihHr4lDAd0u+F1PkIIQuxQ4j7hIIB/EKI1LcScn+fAUVsQThFB0koGVZCOoXQrCom1BE4oQwhKoDiU3mTUBMVE7Jzxwlnn/VaVGagCckihB1Cg6iaMG6ko4TxPxHjiDvdRBi2a9XNFML/IClTjlAWzLZtCFXXQsCTCHXDKxHGF7A/EOJLEqILryfwV0K74WZC8jOPwaUbwqKbKURC5dkDIRYQ5vu9ByFs9CsnRD1UM8L1jaMWsCtCXf4LCRULoyw8CHoAAAAASUVORK5CYII=",
                         8015, [285.84655, 240.08669, 199.96554, 171.85732], [0.58496, 0.55396, 0.6304, 0.69057],
                         35628361)
            elif (record == "SRR3581706"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581706", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD+mQAiEG8MAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACdklEQVRoge2YTRqcIAyGWdicy8VcoV1n09z/CPUPSAJRwMFq6zcbMb+vAvKMc69evXp1gX78vL1+/W6N/NsPt1RAFc7D6D7Ojb166aMqwnEYFsxHqYrQDTPi2KmVTqojHIdxfBohVa3D6fdvE34+004zfLo100U7hHhdFz21Q1i1Qu8rm7BuD7qtgAhN05WNdNNEqEDCsGoPuq/+S0IMFgw30T1WZYSA7rEik5BbXsJCQUOMudWX1twnxOB2roxP0xDTjxA6ELZk6UdIivBkoTVnS4xZOGdIKxQTfmUltrwP86uc6yjMtWikDCFFCzK3+uaS8jahvUKbCdHHlxBm3nSDmgjBLJxLFkpMk26Lu5iQJxHvoJ4wPao4QUh7hBgsFLOdJ+TT3mnCZYCgSUESMnOOEKmQkIIl9+VolU7CzhN+ylGyZ89BwEbSYldYrJFD+l1NCPPVYpgXj+om9geLQ4jPtaQIkebtJk+Im3fI3odwa2aeiHM/W01RRxCuRsRiwumJYV9CcRTS7fvsWzNIYtoYhOQndKYl1LMuKiGkrxESv5a1thFro4SQOCElrlcT8ijQxSzCtO01HtcMwAlRuxYTkmgozXaMxiGyhLBCqVb4Q3XiTXlC+hJhqBzvVBASJ9y+e7pYBk0RgsMjQr2uawiJBZwj5Cf5WMwG5AtDEPKW0knfTBiXSjkh7BFitkozIfvknCYsP7aBL8RrthDmb2QJyRqXEIKILZBPCk8hNPwMQTwoiZo3JgTDz5D/rlmEJEc3IER2efw/BIQI3cN9CaVj4u2s4Hj5JMJ19z54hWnUgwhz7oeADyQ0/1P5EiHqVJcTxjx/AJa2C2sQCibuAAAAAElFTkSuQmCC",
                         3677, [117.19988, 98.4379, 81.98783, 70.46318], [0.59962, 0.58772, 0.66503, 0.70639], 39864995)
            elif (record == "SRR3581705"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581705", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCZzP+FRvQ1AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACMUlEQVRoge2YQZaDIAyGWXRyLhdeYWadVe5/hLEKGEIUwWIL9X/dICH8Xyjg05hbt27dukA/v5+vv9KB7y7uYUFG7Dg+xmEcq3mpI8oJfhgzDJWM1BIQZkQPE+M4VLJSSfmEz19LyiJ8/knN0D3hY6jlpY7y/qUtqn9C6p0QIsKs+7EB7RCK561qIhSLRr7ncjNVpBCi67ncTBVtE/ZyBH0xIfVCSF9LCL0QgkJIrgPfYOikMHrSNaEH6YgwvMO3CdF0QQhpwvYQOSHRNiG5jhe/t6UrlvNlUx2fTZi0lDd9smJna+otA7ptphNCFUKRD2yD1T1dA5ZAMxcR0gYhScKz/55wepvTvlqEhJFt2mipX18Y4ex/yq3sNo3wJRtSENoWrQunlFssFauGEsssL/a94riIEM1pSf82PSPUNgaIqkyLw21Gzo8Sogm6ir/HsYHycHYnwWKLhEMeFo6xbYhj+aIkCQltl4svJGTJ5VSWENhEGiEfwz0phKHjFCHxbAilp3hE6JsAS8sTLqefdAPHCcWaHCVcrkYovDeWDBgbWJeUFRPCCJZh9qwS+kPeI2UT4pmrcR4IAaHf2TY9m0nUICIEHrA0/KW6us4mJEA1KsXGUoWEYUsRJwRGiEGARwgrVkJIBYTAXgkjphThelZidHgqhJKogFCP2tUcLuYsIHTF/TBCCt2dItQfVCPEI3wQsPVKqA/shXB7YAOERxB3xrVA+IzbxQR9WEOEPMWsf8bbeBjl55s7AAAAAElFTkSuQmCC",
                         9327, [477.80943, 401.31912, 334.25424, 287.26969], [0.57236, 0.55377, 0.63491, 0.66895],
                         24803475)
            elif (record == "SRR3581704"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581704", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCXmZnsxbRDAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACMklEQVRoge2XTYKDIAyFWTg5lwuvMF1nlfsfYYqKhiRMhRFbGN+qxYS8jx9B527dunXrAn19f74epYnvHtzDoozYaXKTc2MtK3UEhMeDRze4cRiqmamiLMLpidc3oZ/CvgnHwXW+Soex9zdNkyJJmHN6NCEigXQTNidNiG/xcY5QN0FXhIBG238mbHBD5hIa4R8uyeKVJmzxKnCQkMITrO5oKXhiVwZimlBddirpzJEkwzT1RAidEeq0nRD2xiShOR41xAkhHabzUEUzQnxubwhtNiFdRAjADBgVVUtoAJRvFSBGCLS8wkxCCg+uOPOJEVoLNvYAe4O2R4xws28TQiVCq7+YUEdQItqwl0FIIQSzAF7JHDFhSz4W0xoTogh9NyGY/bE6VsVol/Kd1hohbT910h7KTK2sEIcKwu2FoksiCzlNsr/5Q2CtMxuzBpXnsNAwSdvHhD8eDEJKEZIgzDmnUmIrLBTCQ4SwWuChYcICoZ9qgzC0GoREcbyoWwrI+4GY0J9gmnD3ZxMqIvkfXhGG+00x4ZYYLwoX7/eFkVvUhBgxHCWUVW1CX7uMj11YQBZb/mnC8PE2bw0+ygahQVRCCH6qsYxw7104WC0gaW3xeAkhraujjHDpwCI0yCI7cwC/WdUjDMNchMgy42q/AF5PaEe9QjuFEGXD5xASuzH9gdBuqEaIxwGB2BHeJWEI75OQHWxRYgOEhzYiGHl9EVp57RD6XMwHzCaMCa4k5D0s+gFy4MeE8vV98AAAAABJRU5ErkJggg==",
                         7801, [397.20466, 333.618, 277.86673, 238.8083], [0.5733, 0.55647, 0.63784, 0.6972], 24955209)
            elif (record == "SRR3581703"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581703", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDK/wAy1e5hAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACY0lEQVRoge2ZQZKEMAhFXTicy4VXmFmz4v5HGBM1AiFqbKOmyz9VU9UIgSeYtNVN8+rVq1cX6Of3+fo7Gnj3zd0twP2+bdf07l9dItzv2zVt03VtsVqKCLIIXQ+bugghIkTLbVLfDj0c/mpSTEgr3p0jrKuFw5CSQloj9DtN3xet6GzlEdaoNGHOKfIYYWx6CeuSVXOaUNtrkEVIjyKED+Otmg1CTHuXVg6h3S/LliAcxtdYorBynv1dhPAwQsiZG4MwjqcVQno6oeGrtk1aJXTOiPlFfqQcQmPGHAs3kod5EmF8cjXpL5Fx4ZzQj7BvIBiE3uIvXLObhixmxtSzEjuDIBzemaYRvZ0QBCHqy9KyVLRN6D6sEJIe6lKi5QXVvKnSsp+QuPSSgwVKEJqraULtxMsDIL5PrBHSBuEss6ajApUI53RzFislkGwbECNE7vcAQrXcdGJnElKakJd8F6HINE3nUgBYKV3bVGUYnJH7we2EOhNxQtdQsHLyqIiQpN8RQn/pnFfheKz8R28eR9UihFAfmIQg+n+E0Pm75MfBRK18X2SEMFUbEy5B0wkXEWqiA4To7vFhwrC6TsUJx1RWOZxQMIxxeAah8836bYMLSBEuz9QWIfj2M0LJcBrhODtZv21EhMiXxeWCwNLlDA7u+d8gNIjyCckTZo4psg1gOfdYMlWBSRg2n7KEMnCnwh1hoTLbCiADwisJs5oIAusDQm0oSohZgBzkOKFtuJ1wfjWrjnD3mE4HF4Y830YY1g5n9JcRQhz4XYQGYD2E+BImAOsh3EZcjdtPKAmuJBRLeP0D/Gxyb/4TUcEAAAAASUVORK5CYII=",
                         10723, [548.14924, 460.39856, 383.46085, 329.55955], [0.59109, 0.56821, 0.65286, 0.69539],
                         24856659)
            elif (record == "SRR3581702"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581702", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD//2a0pA13AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACYklEQVRoge2XS5bcIAxFPahoXR5kC8lYo7f/JSTYppCEsMG/NnXqDXy6QPB0+fcwfPXVV1/doF9/nq+/exv+9OBWi7g+9jUOv8OnL4HrY8fXaxjH12W5XKMWwoA4DuNFmVwksoTsRUWFKRw6m0MCdAH8uElhgXa3SpsIuzxpioRrpF0JRUK+O5UTxHkRfRShd7cXCbMztgd5OTuEcxS6JHQOj2cRtrwgPWkWmr8Fwrz8Dh0kJD0tiIVPIjzmaZLeJuRDdnvUMqrOfJukP5AQMmkKhPQwwux9tRrMTvOY9P/K6W/M2DrudkKSKWaeOjsSFdloZIQoEGL+3kaY/D1PlH7lhJCEtEFIdxJGH2/dmKcVRIVNnHLCaaE6hBwJrd0VQmBId7OdGEtIWBZqHqsIoWQsQ4khpOEMsVeIcLzQ29lOoilI6Z5D+K45hdC/zmdCjs45odimcpaPEpqaU7YkoAZqOe2DDc2JOYRqtwEpwjkomgghOxvabmLTm+pYprTssHVCld4GoUy5jXC6W/bxiW1E1gqJcLFysqknxFFCHvaIUu+ZFdKhvXgVCNPz0hKKWFK1jYTTKto3iSuElBHSEUJdW0+IRMinELKqcgnZtL+YkKfYY4Qsuz2XkEkP4C7CQtS6YjQlT5cQwo210XRJVhBaolZCUCFqVSSvZU3I2oWRK3ZxE2EpaosQBUI5uWtGBHO6uoQO0c8Tuhn4hHGGH0j4dnIIoX/1SUjRiQ4S+gVPIpSeHRByHR6L58tHElLaPdQbYdUyJaddP4RcQVhu9yGEVG7XA+EmosvXFSHiPwRR/wBGUHoHgZtnsQAAAABJRU5ErkJggg==",
                         6172, [298.17449, 250.44111, 208.58962, 179.26916], [0.59028, 0.56948, 0.65681, 0.69812],
                         26301511)
            elif (record == "SRR3581701"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581701", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD//2a0pA13AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACg0lEQVRoge2XwbqsIAiAW8zluVrMK9yzZsX7P8KttELAUktPzh0W840Fwi+INgxf+cpXvtJA/vxNl58M3UdI7mIA1Vjim+U1vt7jMJYZd0E4vl4zZplxF4QT4nsYxzJbILwzlEoypXB8v8tsqQfCuUqL92EXhNMWnBI4lhl3QXhFaJLf8QyN/PweYaPaAUUIbRw36+Ga0DmuX0JNCQNXDrh+5UKj3aEIwQ3re1f7H021y7IQUvhgdkW1tyMowkqLSpKQVsJjh3jV8ZMIzWxeDqc24TabI0T2ZhkB7a1OtqLjcFKruy4hEA/fJgxV1BSxVm/vX+NZnPCODnBAuKARPyb1eTIcHGbmLdeKWa/bOrxyTgILmjnivgLCKTJA1W2dWSQM8w5oKRuE6AOITJ0iPC2+cizCmdEREgKqXuTNTA+8urVfMcP9hNstYp7dVw6JMhWE618ZDH+C7KVJCJmE5S0nm3D/K8IOwpsV12YCOvBoXjUhQEw7Uc4JwRNqCZ0KwnmwZ8Co6MCclnu9WRg3EDIsk5BihOL7w0WTRAhyhWhbSUVIiO63kJDihPxkSEjiTrhmHWzCuRsz82m4lDTFCM31zCKkGGE4SiEkH3OgIAP37YoTkt/gtQhxCOsmnPOAUHx/bIThEoD7xw7e4E7hT9dzQiwChDsIKYUQ1yuPeMsy/lhCSCGkOKG1aPcRbqZ8kmxC2prHxxISDuKBIjSIMgl9qWTQTVt8jQuuElILQpeJjG9G2q9f4T3s6YSYCAg7ofBZQmg/uJdwPUdTkyhm7okwEfHzCa2IH06IEa3/lVBM3AVhTMsW07AbQjwHhAPDzyA8MuyA8AzxxC6dMCRoSaiV/wG7itspXwwk2wAAAABJRU5ErkJggg==",
                         6073, [221.65494, 186.17122, 155.05994, 133.26389], [0.61579, 0.63093, 0.72356, 0.69477],
                         34813777)
            elif (record == "SRR3581700"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581700", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDo6EaTIBzcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACdklEQVRoge3YSZaEIAwAUBd2zuXCK3Svs8r9j9AOCGRAhRKnV9n0kw6QTyFa1TTf+MY3vnFC/PzeP/5KO169uLsDMCO5a/qm7SpVUisI9+e2XTso22q11IkcYde1A+9hQsgR9n3bdcNWfVQAUUb2sENvvUlRN4ESGkkhxpOm74+r6OhA3aSFOR/p7QJ10wB8kdB68r1MaBT/LqF1aqaFUL2e40MJYU2Y85y8S1hCepNw+LiQt5ApRJctkh8QxobEtFAtxxnx2b0PAgOrQr0cZ0TWNzkVo2XZgeOfaYveS5j1jqxWA5QQtoRyiOphCZNVbAkBJ57cus2VQv2O3KSFOlcIx4u5yRBCHaEYT41P1py8PIqTxblkCMkWjl3BnO2zAGQD+seRnz9XKP5DsZBoVUh1hHym5TI8eI1ihJCSQsgU4izE5sgAvmbLpZMCO+3jLHGxrIsUUpaQZR8VQOLzmMafjhfw71eGkO1iCusiRysRHvtE1DWN1RC4mwJNYdxJCZHnlQvxw3cNUwiREKfSYFUIq8IgyhTOg6H5zTIzZP3gZiYZnBiEaAlBiQqEMO0fPm+xkMS1LCUIQQkhTnALdojQ3SGlMuRCP05S6DIoFOPyqwhpzoViYegoJsMNIcx/WYMh1KJcIXoh5sCW37yipeGTLRX4rWcIx+PtDGEiawMYQdx7g10BamAAbQsN0WnCaCJL6K8uFxIksvYJDRPxq3UhnCBMZa2Gn+kzId1U6B5c6OcpFy4H7r2Ey711iFA21BXiLmAYugH2ja1EaDdcLIzyece3CCHZ8QHCXTfis4VYBnyQcOwsfsCTkeqWJeSCU4XxEFP8A7Z/fBMicHQ/AAAAAElFTkSuQmCC",
                         7277, [330.65621, 277.72299, 231.31239, 198.79789], [0.59633, 0.57959, 0.66835, 0.7046],
                         27964107)
            elif (record == "SRR3581699"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581699", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDo6EaTIBzcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACSElEQVRoge3ZTZaDIAwAYBZOzuWiV5hZZ5X7H2HU8pNgUESq8Grem7Yg0nyCaB1jnnjiiScuiJ/f3KC/7KatxLFDAQSIHznIdWM0w/xSEEDUg3AYzTgOQ8muk5CwcjofiPGckGrnUz9er2Ih9SE0JWOIy2s/wsMrDeDytgixekItxHcJ+TQF+waXZ1Q7ksL3iILd3lf4pOcPO0ICZWCbD3CUOfuUkLwQ2Z6X5Hc+PGV6ByFE0WguCSH0shhxIe0Lw8j2IgQm9KqkMMxdNNSbEFZCdiImhD3c9wQhrYXoW1kNQ60Wo2bjgBDhO4T4vkr0I6QNIYlW4CopNLk+3+PhWbtCXzk3gniU240sIXAh9iScbtRKhO8/RRgVQ9x2KDKFIIRCK/tLnZdwm5DIP7AQKUeAJDBaapKQfGHtn2duupltYRqYFoot2Sds9cEOQjdMaOu1UoaQr74s1/V81gPiHk9HJaGbWiSvL8gLSubrquuFJEtJYfh1wnNFXtA4SlVKiGXzN+TpgMVCMHKksoS2QVhd9LG2WwqEnuUvb8XCZcdQEaFSQvttYTD7EYL7bB/RKZkDJoQqBM4KQ1QSvjfChpB9m6dqQmhGSJoQk0KQQrZbBAk93C+EldD1t85cfJs/AKxL1lI0ORZaxuVC3BWSf8Aqb9zdjqALEQw/evcJ9QoURdS2uvRFDzJJMam7Fcoe1CSdMPv2vFdh9v+H1IybFk7Xbds+j9ih0D/wy1l1Er/bWxdGXW1EKuOjQin4vDDO9DCwI+F6ov4D3dlKtjo92bQAAAAASUVORK5CYII=",
                         6042, [274.04462, 230.17408, 191.70944, 164.76174], [0.53267, 0.57507, 0.65831, 0.55078],
                         28014618)
            elif (record == "SRR3581698"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581698", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDo6EaTIBzcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACXUlEQVRoge3YQZaDIAwAUBdOzsXCK8yss8r9jzAqIoQExRYs9JnxdZ40YL5QtR2GJ5544okb4ue3/fh7teOnT252APJ91JJcmHEyo6lWS52IhXSQu+CMGStWUyMoIh0JjRnGwUxV6ykecEU4TbNw7GwOk8J49a5h5r/h64W9XWmSQsK7S6kTM1AXwiNsMlA2KUKbJdp7CO3akRLK9h7iqlBJbzxAmZVH2G5oK5JbwL4mhNS+UMwXIa8Z1o2kkOzrnI1DwyGEy2QxDCWFBB0L0TeQ3TQh2Wxs+n4hCg+F64d0Tph3j4Rt3xHPhOsVZt2OhFi/UEjunPQ7FtImWK4+mhDvE1JyZ2tK1KAXLoXKWgzfSYxeJuzgFFwxQPlc8Br8JMvyuJCuCS+snnREt2jYb7zom+Q55eXRfhKEkC27i0Is820YiJ0okkJt1URCVy7EQmAlXxMCit/jXoqoJNofLVwr6MLt4WsvDj3BpwErOV9oaygi1EpC9w981Uo3L/QzV1KI9p5SUUjbGfT1a0IcsIbQDgoiKT9cxeHxFSG6lEi417cIwWdAlBxU/KowOnJmwD56fKxQiEkhBEJm2IT7tesNIb0jXCcf2bDunW3MsIqwRCnkBicUoqtCGhJZ+ULQhK4C9Edyz1EO5HulhVRAmMo6kQVC/9udUsGBcF2BZ0IpuknIpooLie8FQpYA5Bdxg0IIH62+UsghmUKesJYY3vXaE2IBId4rxEvAIkK94dPC+UF5z4e+hHnLNBwaw2N+ixCUfv0IMUOY7teDMGMSQevWkfB8Fg969SGMs/8B1N9jXZKN6BgAAAAASUVORK5CYII=",
                         7394, [374.35162, 314.4234, 261.87976, 225.06855], [0.58316, 0.54918, 0.63214, 0.67906],
                         25097184)
            elif (record == "SRR3581697"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581697", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDo6EaTIBzcAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACQklEQVRoge2YTZqDIAyGWTg5lwuvMF1nlfsfYQBRCAlWbLXQ8VvQpzSE7+VPrDG3bt26dYF+ftvX42jDTw/ubgHuj50mM7miL9UQjmZwRWci3B87jcNgi7OsnKQaQjMMo5/HngQ5IWpRQW4Kx7E7QuIVpMd5DaM9aWzRk6CKsEf9A0K6CXtXmbDmJtCyvowQZVWZsOom0Ii0WSFJiPyzJ2mei4T07YRy9fYgzXO/hMqeE7cXA9uEMkVLkoQ5C/ROSJBXZDDkYUqE1AEhiQpu2hESKIQ0lzYYzcWC/XtfHhSMEO0qDhOoEKIyHteo4nSTxlPPdpP6IXhGePVpKs/C8ouAnIGMkDYI7RYOhDzF6VIJmQdar57SHjFCT4AlQvocoegxI1xC4AkhBYIiIV1IGPtXeuR/lAEn5E8/TkjNEEJkAGXr84UbTUlCZvkpIbHwdyl35LO7WQlPCWXlGWYPNgi55TrCd70KA7efEs5daYO62gM+S5AFA7NcSWjL7H50TLwrCOldbZg8hRDWRicRBg81T+JciwkAaWkhpCJh9AeoEa7ri09KHeE8xkcB+TGS5AmEkHSluEkJIXqK7ZBlP0QIMyGaI4KYXXeUWgMWIQg5A7BvLxBSdka9TEjxB5+VpLL2bRIu28N1FN5QdEJNS4pwez6bsBS1DchAOCFtdsKBTF7REmGCdZwQmyXkIMcJ9YoPE8Ly6oVrP90Q4i7CJBwwbfgthFBs2AHhnmWqAXZE6B9sm3dwFbCaEPNUlxHyHE5/38fJFpMUBdwAAAAASUVORK5CYII=",
                         7461, [380.57572, 319.65112, 266.23386, 228.81062], [0.56268, 0.54015, 0.61982, 0.6727],
                         24910430)
            elif (record == "SRR3581696"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581696", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDT0zLQxEywAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACZUlEQVRoge3YS2KDIBAGYBbpnMtFrtCuZzX3P0LxwWNgULBA0PqvKuExn0Y0VerJkydPOuTre/z8nB346ZObHSrpPKmXek2NKmkVwvy+GjdNU6tKWqVEOC3CqVUpbQIlwvdbC9+vZsU0SSREqZfJcg0vJwy2GtzrfcGdBiJh0d56gWjgI7xSMG5KC0HoPXwwbrqXUKpZEKL5pHU99SPVnBZSyavAIAkta9u/FcIgwmQV0j3Ha6atLSGkwYVieRyj/4a0cL4/MTF515QIwV6W5QInhWQ7JyZvF2EvTAjjHVI/DEMhzchdYffnhSR0TeC9cEnC2eKEuvykEJURYpW68xMLIV8IgZAWIewJO+013iLxdWFCnM+A2yfirqFQRxSS6igkYNclXNEvb63V2wmjrk64ypJCaiKUX3TJ/ZMhS0hOKBTuhCxxRyas9Qoe3GTbtJ5QKCYSUkpIhULwJ0NVJSQLXQHC14bdbvtC/9NjIfpC3YEvezJB9XZ2LgxOg2/eE1oS8sOUkHVfHyt/DatV2auzVYoJoWsBc9brCmltqPFTEdzy9hi3ZgByK6M/al8YTHdKiOLdkc8KS3CHvpCWtws4IQQIgN2FbnK+1Pq8QlbakZAZjDASlQtB6lMgNAXztYCdvywhN6yHFYR0Tmj6AwUbpb7n2JEvlMo5EFJFIZ4SLjMgn1ZYRChH7z3zA/NIGIuKheKZPQqYheaB3pO9WAgdhMHIvJhJwRtZLCT7BRpUiHaq80LsKiz4mkItodwwitDuUXcUBgNvJ4R7C0EYeBkh5gjTA/OFXDCWEHYGXkBof7C6rr9PJT/HA3lILAAAAABJRU5ErkJggg==",
                         6065, [328.27115, 275.71974, 229.6439, 197.36394], [0.57565, 0.54563, 0.62748, 0.67891],
                         23475960)
            elif (record == "SRR3581695"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581695", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDT0zLQxEywAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACQklEQVRoge3WS3aEIBAFUAam1uWgt5CMa5La/xLSAvKtQug0ConvnHxaAeuKjSh1586dOyfk43P8fH2/2PHqm1sdwPq2y6oeSq29SumUVIhcI5t1WZ4/a79iuoQo+VxqvKplujmEJqH2rR3L6ZAmoX5K/7RQrzTLo2tB7w60PaUT5gkUhC1vkZHzn4WEZ9fSJ4wQ47+zRxRmK9CskYT58VlzC+cPFYR4fjlvDegXAyPUMi3EC8pKA693JTgUjvCcik8StyOJG8vC7cCUQkiFm0USko40+omRagDmRCokUUgjCYUHiVvrYyEYwlhCZllpEMYWoqIQrhAC5t8tafMIeeHxISswiRv2E8qjGRlQLsynysyzJKT4kyjcgweVNQXkpdmc4vZR7hDsv/2OhBWi71gjNBfG37x2wwqwfCqvJYCYEmgf5UAI2CoUa2sIM0O2artHZL4Xvj7YzkMsDG49xItjvRD1AXFBOwz4nmn9bkrtO6tG6A1mwvytd6dR+dOVQtQVJFeuB1Lwb3Qp+2nbeJgJgbKQikI7SLvQrKqQNXqPEK2QvJArJqk5FLp1KD7bLGRubrMwG8Ve2ZcGzIUOhJiLThbqjlgnJOZCcIIQhFZHsmCsUJjuOXJgk5ARNQulVsWALHTvbxAu47ri4MKAxQpFnwdt7+FRhXtzYIRUvEgMUumBvkJsF4YdXxHiqEJTnds5vS7kD1wsxP3Ou03WPMKqL+I2Mib95hFihVDuN4OwYhKB6zaREP2LrgE4kzAcQucHbIwBvbmCoWIAAAAASUVORK5CYII=",
                         4661, [221.76119, 186.26046, 155.13427, 133.32777], [0.57942, 0.5425, 0.62347, 0.67164],
                         26706614)
            elif (record == "SRR3581694"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581694", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDLyzJA6iYhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACfklEQVRoge2YS5aEIAxFHdhZl4PaQvc4o+x/Ca0ikGAQEfBTxzeoUj4vuYKgdt2rV69enaCf35r6q+pWrAbXC6iBaZb6oftMP610PeHQ99NPM//rCbt+RPzqMRzHbxi+egzHAezaEmJ9T4CM1p9P65UG63tePzGYqAVhC9OjapLMS3iqxmTq3zO3IhwBV9mUpQezaZFFBblhgyxCdQ8Ip4AhvHoxdQxZhARKxWpjII0w4thM4BLII9Qqxv3UlFp8MqZBV/OHOU8Ch4Q2K0EYZAOxKRYhXEodIUQJAVvfn0sS4Bkoj1CpWBNqniTbVpQ05ITA0pF9OKGoShA6iusJ5wRMLJNN0IoTkig/TmijyVDlChY/8lhL7hrhWAD+mJmpCZIgBDtJV4Tj64a6rBUqWMoZ4XLp04S+Mkk47RMQJaROiVWswJD4wMUI/Uro926UFYEn2n7OWiXUrmaxgkgCaw/hcmx2PJXQD2yC0JYjhhZF2iScjpV0fAHgAmUYNEJ2a83zPkrohHWf5+T42OvtCUFJhxOSQuhWL1wR0g7CuvM08FsIwWeRIHStVEKyjT2hm4tNCdmjXxBqRehu/01C5IToPuyAQsjUjpB9WQKFkDYI2WNOkLNOaOfA6YTy5W+TUKQDbC+JEroRvREhurM0oVt84oSc6HJCGcxmIKKVEUJwvo+wdLugIkLKIoyctyIk77VJqMk3wBMI8RAf8KzYW9J8ug4SJwwL7kTI0pCEdEPCfExrymMeIdQL6hKS2LV3Ch5GuGqwLWSvz88ghDxCHhmeQai2iYu7PoMQZc+UuDOInrcljLWKSOuYSygJbkYYz/gJhJjkg62ODyBU2v4DIaGMcwUJ9x4AAAAASUVORK5CYII=",
                         4320, [239.38747, 201.06504, 167.46484, 143.92509], [0.568, 0.58862, 0.67159, 0.71334],
                         22930187)
            elif (record == "SRR3581693"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581693", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDLyzJA6iYhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACgElEQVRoge3YS3LDIAwAUBapzuVFrtCutdL9j1An5ieQCMQWiTPRojPmqwcMdurcN77xjW9MiJ/f94+/Zzu+enG7gwbaXhZ3dderWS42MSJcLhe3LFaZGAWMCN19DxejVIxiTHjbQ3exysUmhoTbKf1k4f2mWf+cKaAhxHlpGAaQJgTCmYmYxccLV6ACwVcIwWBIXahVWAYcT9SFaoVljFzsgJ1DnlbYmZ4g9M8vEnbPKTety95MSOrNXoUsrLtLQlIqrCK7XYRJh15mwim/QYrS6cKUgDSploWY3quFyAYMWwfPCoUaYWNJEqIy2b5YZ2czhdse0kRdQj9IW5heJU3h0C/HR1ENGJOJ5SRkU+4K4FYg55cLMRuUt5onxFixbYwsJPbUEkLaWFg/OjejKCTwIxxJvA+IbB6MFdgppDiIKMQkJMiXjbfbSoDKjHZGNZ5/hDTTbiGRsmx1KhOFVAqx7FYQVGGecjiCIK3a1uw4ob/WJCGF8j5hthj1oefdvdADBSEZCcv9cEkYFpXPeSvbXpzAFkMQ5rUh/YYQmXDsP45srEKYkiqEKZ067YYwffGhIIyhC2P7p4WYfcnn+fsLRhDyV8oDYcpwrxDdUPglyQ9CMVnkJKGUTiaMKyALKa/tEFbth4BhzHwMPlmRgZBO1stUGPditnA9BVAImWEbAA8S1m3aAYcI7x15QSUURMNCdOENOSZETShmoAlhgpDikR8TZh+a7y/Me/bw4tECSUj8qSWkSUIUW6lBScjmfEaIU4Qgt2oI0TcPPd9dqLTSgV4YL/cdQrnATIg9QFA7fopQ73gCYdcxPbcQHwNB73cG4eNNFIHDQiyHmiesjP/JpnlThGN6EwAAAABJRU5ErkJggg==",
                         6036, [267.23711, 224.45635, 186.9472, 160.66891], [0.59317, 0.59285, 0.67985, 0.70448],
                         28699725)
            elif (record == "SRR3581692"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581692", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/2ULgAcEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACYUlEQVRoge3XS5qDIAwAYBdOzuWiV5ius8r9jzDWEcgLC7ZY6Wc2bTFgflSow3DFFVdccUD8/J4+7ve9PT89uaUBVJM9DbdhnBqV0iiqhOM0DtPUqpRGUSWcpnGceiNWCW+3GXkbmxXTJGqfw8d1bFRKo/j6lQaIULagl9ZxWGH8DepAD4G2KS8EfaCHcB65WahaVxgaeg9hhQ+gL6Qehc6y+cVCCk1WSOvHOYRVm1kS4kmFYJsqhWvRgPBMCC2ETwf0hLlO3mYmhRFihDg0ErrXg6vAEEGUx0uaEXasKKSwSRwpBHRH5NfCnlMI+RY9f7cTRklIW0Ia2gjliEGWVoelKnVSJST+XQvBE9KWsOohfx7kCimV7Ql5FfOzRfHO9IR0LuH6SwvlSYXjcTTe046QyoXYQqhHLBJSVuhf71Ih8ZR3hRUu1bDzlAjj+mKESEaIy/xtCsMQzj5VG+ZUXIgpQ5adFYKbqoSr74NCEmXnhMh/yOlAlKkvCHF4NXT9wIVLO6mMWLYcQQhJpSphCCtEJdy7NbKZ0fUDn0kuFOWkBvCEKRmwTkgIMn+ncBkAuTBekH9hqGu3UF/gfUK2oNfFY5C4s7sVYaoCRQbotR74ZGyISoXiGbU5rwspH7Er8uXp7UJ2DOqFEN8xM0JVQYlQGt4vxDpgEoauO4Thxj1GWPuqnRW6FWSEfsObhSj/DZUFre8AeeEG8GghxSe8HAgh3TWdT+hn5XndCTNZ2ZgTw5ngK4UQVsDwn6EjIRYJSfxP+UIhZDtewl6E+Y4dCEuWGvD61QpRj3SYEPcBuxb+ARJmxih63GjUAAAAAElFTkSuQmCC",
                         8371, [399.35305, 335.42246, 279.36964, 240.09996], [0.60103, 0.59363, 0.68289, 0.7157],
                         26634565)
            elif (record == "SRR3581691"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581691", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/XV2Znjo4AAAACXBIWXMAAA7EAAAOxAGVKw4bAAACdUlEQVRoge3XQXaEIAwAUBY253IxV2jXWeX+R+joCCYhKKjo4DPvdUEUkq8WHeeeeOKJJ06In9/vj7+tE6++uLkBVHBy17uXc32tXupEkbDvuvGvqSgSuu59D+8t7G91D40DnWtSiIkjhvD1anKnQTOPZY/vF0dSSMmb21ZAJJxuHTUpxDgFEWQaP8I6ATvnG3vHW6iylwp37m7W7niq0LpDwJN79+9MIfk87isXBVlCqiwcIGcJQVf6lIPVUxKrYZRCK3miUK8I44j4dY/3vWQ0IJy6OVJIIQk4Jy8UjoW0MPcxNdobMZ/sihBdDaFecbpfooG4m+T7Iz5ztHgh+YmmkKIDe1/EvhTKMb6/QTYKjTsghTQZbSFEQrXYliBVauwGRR32mM2nsTH737MbF0JcEJI+cMADC4aQRFdyEKahGnwSceO0RRgezlrC0BXMGdTTxADyhZQhDEcOEEbtMyG5sOlooWhvuOhYKNQXdkqh+Lf1b5DyYDvUohCzhf6ETCGlhCSFsFXI2hUNGEIwhcDbAy0Up+4VotsS6kXAiwGpQA4whdyQJRy+JlJCecV3CMn/7lbCCGgLRXvlwsG4LGTfBUUwX3ooAVKIKaGqOTeDfKCE4UUd1kNr+SxhCdGfPc6rKCQXPxOlQr5auZDXVMI0cCrEZimEFGpRqXB+pRwrVB3E7cD8XT4lLKGxXrEwlCkQwpKQPb8rQvndUU0YyhwrXACySyCEKAzXCn0hUXOTUCeqCMF8T60K6QihnThaSCimZvi8EMTE+wj9hHmdrxfKqWsBqYl3ERrAdoRZm+n9hda8doS4xkN7bqlQCs4UktO/9v8BrKeNqSJU5WcAAAAASUVORK5CYII=",
                         4490, [171.9858, 144.45339, 120.31362, 103.4017], [0.58525, 0.58992, 0.6767, 0.71036],
                         33172562)
            elif (record == "SRR3581690"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581690", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDM/2ULgAcEAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACTUlEQVRoge2WS5aEIAxFGdhZl4PaQs8zyv6X0P6QBCIFakqp9g3qaID4Lp9Qzj169OjRB/Tze3/R3oFXT26xqKJv17uXe73MvJgIagj7rnN9b2XFSFWEblrD3siKkeoIxzV0nZUXG+3Ypd9MOFWa4acp1e3SFgWEV1sw1iZhk+SoxBJC/04tbl9UYhSTLIRJvAVpRQX+NSGaOzpbD+Gs+R3uT4hpSLsY2iVM7QEqhCPIjQihoqtOuEQBQ78iwjDAVgcJKRDSsIlhflII0V1GmH6HNtrT4zU4Z4QD47pUFxFqOZVaSKI5jEmNT6HdhAa3v173khiP1BBSjpB8A4ZYhfVCQTgy0belHQzPwJrfE+K6VNuEFGLoDotQFBLvhtnWCjizB1nC2TEjnJ9JJaSIUDnV9RqSvCGU+2aNCWeAFPrGPa8nFPaX/GxhSHETEy57T5kNUgjHcqMTIpsEp+7lem0QzhUegsdklMpQRDhm2yAkA8LYkidcFwY0QsoTglNbCwiRd6czCPmMJYRs2ygLM3teXXPCcJCwkpB4f21uDxP6WQufEhbLCDEhSt6NCSHeYucS0gmE4WrcdSPCmAB5WgwtESGR8h1GiAqhQvRhwjEBCEJx9031/AaE2pfzAu+KDdQJNclE5oR0hJAPzDrQ7Ax/XyShyHAmoVoB8vJJtwkzgGH5JaFkOJNQDj1MSPItR+jLqzFhNLREcBahHrgLIUYHuAHCwivf7+tvJRwzz6dnLX0NEWIB4fa4LyHMjGuBcLr96wGrCSXBZwnj3n8+HjP31AjHJQAAAABJRU5ErkJggg==",
                         5655, [265.07498, 222.64035, 185.43467, 159.36899], [0.58389, 0.57138, 0.65647, 0.70323],
                         27107480)
            elif (record == "SRR3581689"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581689", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDK/wAy1e5hAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACUklEQVRoge2YS3aDMAxFGVCti0G20I41qfa/hGLARpbFR8QOmPLSc5KALL0rBIQ2zaNHjx59QF/fl9fP79GVZzd3r4As0V376tqukJVCMhG2Xesoi5kpIvMx7DlLeSkjI6H768o4KaWEEMInTKP7Ca1tSFNCQr8HG6l+RvvXq7ClzDIRVikKRH4Dyg+Va5EQ7kMoxvRuhLBEiLcnpGR8K9X/JYQ7E5Lfjif4yS4H8hCeK3wzWiXE5kKEpkefkwnhUIjJhfIouEpoa9+mdnhNCW2/O8yEO7pukBwKHL/yImlB2yTZCS3ZNyUq+aMD6abYn6EEpJZJI6Qpdd4zUZr12VnfTYRa+yEkRX/R0QlREuYYV9kxXxjc+1AA05bG9qKBJtRmeiakMVwnJEFo+2+VLlgghKHvwUxqmW3i69UrIbHBcK9+xbmE7isNgxjGJrXMCYfzR9szlkBG6Bj77n2akOfxhEMdtyvpgeRwu4E9GWjBgTCSllQQilwHlJTihBQIRSVJ2F8rL06IIRHsJkT+JTch5SacE0FUh2g6Y4QbvgR4ipGQX06Rd2ibcAoP2bIRhmIjIc4uFgmJr4gI+zUBEclESMQJ6S3C6c4sigkLjJCXgnkJhGZgtF4S7Sbk8WnMptDnwt2EscWUMA7IRhh+wJn4wMe7hSrhMmBdhKAQqg40O8PxvyKhCyU23r5m7GAFcAbCRmwoQkjKvXodkOaWqEz7Cf3F50OE+xAh+MIMhPqG7IR61I0IF6I2CeUN7iaEoC2shhAPAtZDuIm4vq4GwpTxD4LN1cAc5IlkAAAAAElFTkSuQmCC",
                         2004, [102.51069, 86.10022, 71.71192, 61.63171], [0.56331, 0.56107, 0.63956, 0.67169],
                         24840129)
            elif (record == "SRR3581688"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581688", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDLyzJA6iYhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACZ0lEQVRoge3XTZKsIAwAYBc9OZcLrzD7bF7uf4QnNkgCQcB/HFM1NYoY8qGi3XVvvPHGGyfEz+/949/aE6+e3OKgir7D0A2HFXJUQI2w7z7jX2MBhOWdB0NsLaqExtcfVMhhUSXsP0+/Sz99kysNXl3CsQH0KCHGTUkhdi3SlVffXxTaTtjkA+pqBpybzhRCtpkVtm4ERUhjyF52l3YXJhLyz8ZzhbsvstFIQVXdHkKbzE8bKEJ0BzYOF0ZaiH572xC3FbJyytNp1/t6oZaRj1Tz7GtdzxeK1bNAmLjMauqbCHkKPSM0LuRvgiAjgP3n27VBU0WoQvJCnjMUUmqw+qAFod0j1k7KoKmLmhWSHzYWjtO7vzAsPxZSnVCpTwoJxrNTQjxc6Cq0LHSbQTXJ98c3m1jKAIUQzeShKgQr3Pj6ncbh2xTctGgrNcVgpwv5rKA8YLrOE2C+GoCEkKbbQxWSfqA+jIL8digkV1VaCLEQuNCLxhTsLv+mnSMpTPwYKI5vJmRpBbBAyBrQLvLgz5dCqhPy7gcIwQoR2EjKmP4k85DhdN69hS6hvXReSHNVKSFNy0ZSKEuuFq78VRML5VNJwIvIC2kS4ryLlwnBvsV4EpmRIiGWCH2Ha4XuYRElq0I+FIIc02c4RVj+5jDfEjTdmzKJ24GEMBrTTGtOCJuF5NuwK4uckN+/y0L3QXKGEKqEuCSkrJAvRjmhIqoVsv51Qjf/a4WAYYMi1ERnCO2ZQY7HCJWK1wnTDdcKg8wNCKeD/NRHCqFCqFV8dyG6T6sSYZC4FaE4dTnUitsSZhacJoWyn+z+H7LibbD+BF/mAAAAAElFTkSuQmCC",
                         808, [42.25187, 35.48797, 29.55753, 25.40277], [0.58663, 0.62192, 0.70614, 0.7097], 24299126)
            elif (record == "SRR3581686"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581686", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/XV2Znjo4AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA80lEQVRoge2WQRKCMAxFWWDPxSV0nVXvfwQRGCxDYyMhLS3/rTToz3/qFLsOAAAy8HjWyssnX1L6w1XifGzaD5lrGBI3HPrcPezAd1g/dzCkyLStXymVrmAMDOvnDoatK8KwfmBYP6cYXvpAHg2j/0z/DCF9EytgKAwhfRMrYCgMIX0TK04xHM9j0ldRl+DmJ9wuYJgFGCrDGzf8nFb64+o4825GxMFQAgytgSEMk0wZ3xDWNhy7RJ680rx9IVnuGDBcL4TvSeTJK8EQhvIda0grhkGm2+T73bNwPLVfHnNr99fi5bdFGEN+1a9QGMIQhgUM3yRciRndA7haAAAAAElFTkSuQmCC",
                         37, [1.96096, 1.64704, 1.3718, 1.17897], [0.28474, 0.32297, 0.37193, 0.36663], 23975035)
            elif (record == "SRR3581684"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581684", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/AACDUTRoAAAACXBIWXMAAA7EAAAOxAGVKw4bAAABf0lEQVRoge2XzZbDIAiFXWR4rizyCrNnxfs/wjQTrRbRyQ82OuXuhObCRw/mxDmTyWR6g76+r4kuPt9UKhMiFRdFzW7SNeyNcJrdoukHRKDpp6B5Uv0PuyRcZkW7Hgl197A/wmnRJaSH3GlG3Bm7U0ZYF+6M3akrhIAoRKXYnTLCmnokzKqT1yk3osxvjW5BkHLtlVU1wqo6JMyrBsItAWLLRTdpMkBG2FRGODphfqUABsItDoeuHCDhqjHCpvoQwrTuY+0iIbqDhJD5+SLo01d6PScjHI8w9Bu+HJKFSwPJJmaL+od9nZCn9GWE4xPGdwCGc40QgecL8u+BnHA9MMK222iERlhSN4TwWwxiG/TaEpAofDGRrgs/sfB8/K2fEgZ7PHZ1HZYRjkkIieHGlnTNOtpDCDwQWncyYeIAoXih1ZPkRjg84Wr4/PLkXbOOCoDCEDgf8wsjYOfojy7TNjmCpF0j/CTCp2eJELMBlAg5Q5WQE8WzQEm1pBH+N8Ifem7z4S17MDIAAAAASUVORK5CYII=",
                         136, [7.29959, 6.13104, 5.10647, 4.38868], [0.40269, 0.44825, 0.51374, 0.50863], 23673665)
            elif (record == "SRR3581687"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581687", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDK/wAy1e5hAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACo0lEQVRoge3YTZaDIAwAYBadnMtFrzD7bCb3P8JUikhCooBgf57Z9KkE8imi1rkrrrjiihPi57c4/sqbvklUngvAEWe4e0zu5m5TU+pnCB+4aZpuTbmfIXSz0LUJCfuWMii8cGpK/SBh2yV0RA671jIkbvfHFL3fW1LhdUI4aRgixHOGkkHnDPMQvuhOhJHCZH7MwpNOpixi5LBz3+E5+P1CksKhA7MiBg4E20IcMVy+c6zwobCERxee/BlgCo8NtFnEjBomzNJfIPSo0L8XIjtYNLB5u3YQHv8Y8KiDQvMuApRHThU+U6uFyvtVlTDLp0FCSFSWUF3jFA1vhekB2ZpIlgyqMOYdEdJSROyfxFLTJExKUl4gVKGcOm79jjvwvKJ9of6Ko+5ay0hLUoVyVxCKvUOFsUtQzm289rwvVI8fEVLedWXYwvUWUIT6xN0QIp/W2VvTfJVUoe8SjwtBES59akLjsmK6AWlj4n+N5ELaEs6jNX4cL9eC9oT+tXUdhAw16xhZY1a8JhS3/9Iu/GDjVawT8om3L6QkfxWiIiR4hZCSNn4jOA0hq+85s58tohDDIfnmuywyphC0QxVCLBT6swH+foJNIcSJaQgh7X5PiGKVqAxiXWwJIUwkL9SqyYWUCmkVosiOe1QhdRHyGvhgYQOS3z5CZJkFwnoi0baQbcU6ieIpt4Q4SFh9J1J8jSgQpoGsQYoKG+yk7wl53x2FgB2FNFBIXFj+t9gsRNGDMFlC3tzJ1QOQNbCEtOTWCkuJfYVpBvAGh4VxSizPxlIh9RJCoxBF6wIhah8qViSdipKLhQEEcseO0Nq2hMk6HrC1wjXahPaO7kKW+c3CoouYZ72v0Cq02ncJ30k4527OVUMoTO8rXD6I0BRulvwJwrz5Px8Amw6nzcOUAAAAAElFTkSuQmCC",
                         1623, [65.75298, 55.22689, 45.99786, 39.53216], [0.59614, 0.60255, 0.69007, 0.6561], 31363775)
            elif (record == "SRR3581685"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581685", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDK/wAy1e5hAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACTklEQVRoge3YXZKDIAwAYB+6OZcPvcLuc55y/yMsVvkJBA0qFhwzO04bQPJVLG6H4Yknnnjigvj5bT7+do/89oerDaCCzu/38JoOXUWRcDR/41ipklpRdg1HIzSHrqJIaNaouYSvWrXUibJVOgnHhoUo5LJCqeE1XUBzaDZQyAFJ2bWGhgNQSNKthMK6g6ww29Bw6ISYa+ggdMKlE91IGGUXWIdCuL8QpW9H6laY7gxAghD6FcoYMSkKxd4thXC5SCsk25D0bimMEKIUpZi+hYmG/EX0N+mqsOj/qqvjkBDlhhOqOt7B9UiFEArJPJuhy/KOFYXshDC4YnwO109g9gPbI60vEtI8nXBzXib0xcSpbATPmEl9M1AnpKGKMHoE9kJXNGxNGZSbbA3EhbbnutC1bN4fmohKWt4FLPFDDTPBOgSlEGQh8UW9fX9oIt5/lrebwmBMqRD1wjO2xpzQp4ViBrZw14QgCMmy+TlF4Qm3ZDSVBc9pcC+RjwqFoSERkiS07LQS5EKoJCTH8gsKk1F5IfmP3lq40IZQCcbCw+s0rn8WohPiHiGmokIhhdXsYsXlRUJb1nQAoRqWSIWCSCtk/aVeWiHZn7ZYAUkJ8ZSsmHkA/y45VQj7hWS/RPxpdwuRdWhECGcKeYfThDQk60snC+YRhVmgnwcaFtpzhgPVQvZ77QVCt2kWCjEn5O+yws+04TNXU0KwJxVNBUKME1WE0VBNzN3puFBOVBMqiX4b5+NuIyS3tm4qzI/rQajY80Ea1pEQ9/i6Eoan+MQ/3Y4hndGHboMAAAAASUVORK5CYII=",
                         7290, [370.87055, 311.4996, 259.44455, 222.97565], [0.57016, 0.56626, 0.64917, 0.6949],
                         24976435)
            elif (record == "SRR3581683"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581683", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMALU5xZsz6cAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACcElEQVRoge3WTXaEIAwAYBc253LRK7TrrHL/I7T+AEkIDjjGKVPT99qRIYFPwDoMd9xxxx0XxMfX34/vo4mvvrnVAS2dp/FzGienmXgFNfSdcdM0ek3FKQgbOk/DOP/qK9qFva/h7q6d5p/OhNAiHD/nVZwcp+MQQIrUtGt7CLqF3tH0//hIGEJ0GsqsC95CyIVeiwhmXeLClreP6mENocc4y1DWcrFGvF6IZw9ltDKhz73dFcb9espZKQjToSCXA2IKwzhJeMbINoDf0MuF6CqE2FrosDWKlAPzeKFwLcq3zENhyxqHRFNI4VMcu6FyKUAL10spzE8qz+lMSFoIllA8nloettAktJ+CjWEIaUDGWj5inmXMrGq4YlZsgQuElAkxy8pnVjdcMSsXkqOQlFATtbD6PzPbiZYQt+JY6FMbIA+RKLPM95GQtLD6iRDqGqebC9cPzwjV/NQ4lAslgSeBm9B8AlQPIyebykAmlFesbe0fhGKfljftA2H8DoezhGqBwgZNBFQrKieThHFJ1+/XiqA3mVCUhGFGkN3Z2oBMKHdciGUUJaSFUBTCnMCFuGXx+ntCZEtnbJ4GIUqhPHOxEX5fKkSP7eawhvg9JiEwIS5zBmT1oUoIYuDnhXwGSUjswRM7AN8+KWMTqnrLS7SuXyGkp4XhrkqhBJK4Tqm4I7TuGGZ30EsIW28yhCSv1gB+wYS64UQhxb9HhNQqFKFADcL8GsvCeLAPCEE6Ximk7EUjCUMXVao3IaughDEOCGPvPoQq9RbGCv9ACPCmQtgeX6gS30cYu7+9UCd2IKwilvPeQQi7efVC1MUuE+bGHxE7dA+/NAy2AAAAAElFTkSuQmCC",
                         2688, [123.60851, 103.8206, 86.47102, 74.3162], [0.58487, 0.54967, 0.63143, 0.68338], 27631607)
            elif (record == "SRR3581682"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581682", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMALU5xZsz6cAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACmUlEQVRoge3ZSXaDMAwAUBZU52LRK7Rrbar7H6FMxpIs44HBIS96r6+NB0UfYyBp133iE5/4xA3x9dMqfv+MRqutPhofW8C8trLoh/57OJrkpLhGOPTjz9EkJwVR2JYnxJ1R/dD1dfWcH2QQ84S0M2pcw9cWGutqzMR43ygcKgs6J5jAFpq7UyfZOQ7jWTrUFHZaJIXW+pQILwldwF742iBbCLrtyUJyQmCJQQ+8XVjyfn4s7QunX08UjtdKdLNCIWKuELs7I9gmMkTnONZVawiJCac+cpNuE5obDhJC0cs2H1FQKFFjoU0RQuMYiEnkVy4pxBZCa8fRVUJqIjQyC6FxCER5u0IQQiTwI3XKiy6mUSFttIQQvBBSQnLC8MZ5l3B9glxqnnvM05i1LYQlSZZwG6lTthKGO2u6XOwIZaGkhGu/KbyGqBKvJ9HcCk4Y3MR5E5ULwcq62fGgSIUuibxw2YvBiE6VVy4EWv4yk2Lep8n8CIXoSzlByM/hJsKgJCUkcT9TxfgXcSHv9WkhLgzaDwbo+rUQ1xHIZwlHlTB6YsDVQogI5SKmhNtDEFQJsTseWw5dPizLtSfEpBCBpWsj9Bfk9R1FRbg1MyHbdyiErt8U+jRSqFL6sdaDbQ2wQEhCCJMY2QqAKXTb1otyhbjOPyic6l5PVFuIFAbr58JtjZnQEN0rnN4HUAjFKYeqkDuFYvghoUui3oxyhKJhW+5XEvIkltCOiFAWdZbwINESmhU0FtY/gj9BSPNo80uydxHi1FD5EA6WkOSr9kIyv9VK4/yl7+2Ey3rzDK8uXOdlb8XpgVrmf4bQ/N9qRBgcnWcIcz8tQjjxMUKsBL6ZMD7xAcJ5cuLOCJFpRULUmYqE+suRMiFLOcc/kGnqydM03jkAAAAASUVORK5CYII=",
                         1495, [76.15458, 63.96335, 53.27436, 45.78583], [0.56769, 0.58373, 0.66967, 0.72055], 24944249)
            elif (record == "SRR3581681"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581681", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACpklEQVRoge3YS5asIAwG4BrYWZeD2kLfcUbZ/xIuKEKAHxTf9jF9+iGPmA+q5FR/Pm+88cYbJ8TP7/3j39qJVy8uCkaN0pCg67tv3/W7FHNIIAy1CPvOfNsfd43Nwk9nvj73FSIMtQl7y+t3qmf/gEJpeh8644nRtAEFIS/P8P0aofmxZ1BUTdZ9gHC6JkrHbgxi3BxVk3UfJ2Rq2dwlUcgXC9NlKD8m0IKBmg2wJGx6+S4Ikw8ljB51+XqX1xl1XCqkVOj2QHRVDULYERo5NEn6MHXXOX1bZHcKwtCc37QiBD2+LbyELxS69Kkwq6ZQBWVDx/mul/W4LKe4X4Xc62K4k87orpSQoLDwqMmHflTRVwilJAwFDEPiauBO+cGokd08neFBQmF/tmwWgofstgDC4VI1SzYmdRghC+yxYfoi4bRTQMh7Ce2NpmdmcitSQlV0VWjmVIWihGyFVBIK3NwVYW+0o3DoHgeg+iKh+eMMoc0RCUP5o5CpQShqAGVDU6GMj+ljhZQLWfdJVHRJyPqiJlTTbTdZoV5BIJwytH1KrgnD2SeRUHzTucJQzkFC8kKmeD910SuFKvJxvE04HVrjSkJhXIEV+r+xkHzVQQgqXyds/F+OPba0CgmTCqwRlaOqmBVyk3BaUldc64fhKScSwgpgOZQIowyuPn2U6JJbha2H/7ywAnSg4eDTQr/LSqiLr60gEEYL0iqkmlDiq7JQmoS+e42QWoWJY7VwenMmNcfCVLRYqMa/QijkPYS44XIh+UOMniD0hS4HutfWY4QMP39UQrwwvud9hcRgTFXokiY13FYoq4XJPW8shIPmhSHuLsSDGoCPEfIiIBVn3l+4bBP/vhBN/FNCOPExQp4HUmXiciGnqU4TzhMrFZ8mhPmXCcHw/5/uk6yUXYM7AAAAAElFTkSuQmCC",
                         5387, [258.91413, 217.46576, 181.12482, 155.66495], [0.60962, 0.61549, 0.70859, 0.71971],
                         26437263)
            elif (record == "SRR3581680"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581680", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACpklEQVRoge2YQdqcIAyGWdicy4VXaNfZNPc/QgXBCSECIji/ffwWMxoDfK8BxtGYV69evbpBv3531Z+/MpIEbtSIGwYoIzRimGNNs1nsxzARliNDNU+TmedpWP/wdUKzws3zMqx7oGRSHhKmE7qL5pVxaq0hFjO+T2hL6D5bdOQV2GE9oTKhe2hZpmVu22kApXv03yy8EmKcZFLmEJeZx0PXJl7Taj72GmYZLwYlvpWqhlTULyip1ZmXlBLSfuHj5emEGAfcKVmGUM+UUN6XwgVUYsmKHfQQkSekPUcMf5EQzGhC2Fc55QlxC1UTJpN+i6IIkFEmelfCT+cJobd4mnC7Z8mU8FE5vnYvehKy3Z+ke2/RkXNCNCJrb4XMn3IzXLafM/vCVgnjIS6pktAeUjhE0UFEiMHfEaFv7gjBJd9LyLuOCe1JltDaBVuTH0cYeu9BSOcICbY1rhMC9liPkjB+QHOneUJihHZCWNPImwvvgnBb4+nuZbd40Laq03I2MEcI1YTojoMvSFKjGODKeExI6g50SsgM1hKGwyZCWzROaJtt3abFdhG4Rhh+l44JwdupJ2TF1gjJZ0jCpEu2MC5MUzoijLdWhnWVkFJCpu6EUCQMDpCNptkpEfI/KHcSxq4iwo8jqQbC/XFPXq0mbEXsQOiLUyDEi4TNRWwijO3A1nA0YetuKmxE3cZnBUIoECpEJwmxCRByhBSffZuwrYgQWvIxfzLh6Ur2IqTbCM9Wshsh3kCI5tR7O0aIzyGEVkL/rHyFUAbGECopBfmW9AjC/e1JPR9I++2EeqA3oc+tfIID+27gWYSfvzd1hERPIzzKyhCiaPh/EdKTCbGWUG/4Ej6DEDIN6wlRdnUXYXkh6oDfIJROKgmLiDnHtxIWnGfGlkj/AORHwewEXDUEAAAAAElFTkSuQmCC",
                         4696, [215.17725, 180.73052, 150.52844, 129.36936], [0.60868, 0.62168, 0.71652, 0.72619],
                         27730456)
            elif (record == "SRR3581678"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581678", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAy/84xeGNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACUElEQVRoge2YS5KkMAxEWdA6F4u6QvdaK93/CMPPH8kJYQOmgCEXVY1CtvJhW+Xopnn16tWrE/Tze339bR347ZebLSpJ7ppP8/nUslJJwvm5bdc2XVfLSSVRCWFP1zafrpaX/WIQKyIcNugAeVkxiCWEKMlr3KXXJSRGQREdQEleQ6dpu6MMHa48QgFJd9HzCVFP6QH/P0KQdRdZlkEv4a2U9JQ5eCHCojtyIi4iJP5Gx4HdPlvSw6TvaIVwV7Vtol2vVQZxOucCIcitL7TLlpSsN2FCeSbhuFll/L4UYVZRZ3edkJsVQnHpO7xuEyK0LtxRTf0ZQhmGCiZkSH6CcgjF7zGdKwmhjHiECPuWC+InCG0cw0wRoaj41EoVIc2xlFBOIXQHKfyEoaJmpXIJp0daJGTceI+Vm7//pqi0zVL2NCHHaaIJleyUPrnqKvpDJxJ1N0to7PmMOdc31K2EptxOmQ0Xex3/XCCcFnj4pJBhCAMRm+frEDK8dZH3N/WOhFCivHJCN5kuulmUbLhhYiLvArgJEUQo/j+FmwnH/KNWktQC0RGEnBJ9k1DXcoRRqXVC3/qPJRR0PdokMrUWCXmJUDGQetpFSBUJRVmjlJDOIJw+SnmczeDXFqPJTmQN2DmDkONx2ZKoiZtpnYPZvLES7IQ7QGVCNS5XtEIomhfUmkey7j21CcsQFcj8c4oJkbzFcwlLTiL5SlHN6xNyNl84PbSPcCFQizB3ESmcLdWlHkNI6cCHEYKBzyIkMPA2hPx4wqxFROPuQzjdIjlK/QfHQTw1XgXgKgAAAABJRU5ErkJggg==",
                         6447, [354.56367, 297.80321, 248.03699, 213.17159], [0.57314, 0.54835, 0.63303, 0.67234],
                         23104081)
            elif (record == "SRR3581679"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581679", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAfv+hd7twAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACcElEQVRoge3XS5KDIBAGYBeZ/1xZ5Aoz6171/Y8wykOhaSKI77KnKmUI4P+Jr+m6p5566qkd6uf3/PW3dODRB7e4uKLv6919ho9rFVN53/fr1b3fr82ybFKoEXbDGna3Fg5r2P9dqVAlNGfp5ZawRmjuNJ/PZmm2qF4obqZ0SI7tKhXWPD2uUI/w8GqOc10hSGlU2s4lRNqUiwNNqLVxKlR67VWakPSu6lMO8njgm/CItVRS54VKwKSNvwir3gTKanZCpKmzr1ysBYzHIysEat91iio5hZQebcJ+fHglcl7I2h2ouaRQ0aT7DJso+EQavCOMbJBbQFI62haoZ0FTyeVI5ldCK0J2k6Wdh6ZR2P/ar2hWyKadZIS2EofMgWFuoBjis3JUI2Ef2p8JBUIyX3NC3kQY3wdsGjZS81tGyNM28XhgZoTshPxduO6VKPJzIEROyLHQBCZPEPEghEEpk6q/NJaYUAqpy4WxmW3qtYW2O63hS/J7IcdCygwCIQwlhW6SZUL1Fbe6IHZlUYGNwoSaMA5ltwA/W4uw4amBaXKZPxBykVAcdiecRMuEbBtahD6x3JeljReXv/UJYoUQ4fByIa0tdHPBP6cmYQQID0NeyKEwGl4lxAKhj4lpdiHkMWJS4yw0K+RVhBy/zpYUJki/RfG07tuc0Ox1VpiKaoU2wvx/BRkh54UuTwqcQDsKa8/TSIgGoWjYRhiOK61xQDBWF2o1RaQ9hLRACD8priCMxtUIaQWh3rCNsOpCHPcU7vP0Qrq9sHwR4feE6Bo+v7CUmN7/byZEOvBeQgX4CM8jpIXAWwlVYLWQ5FR7CRXiPzIN0z8bafYfAAAAAElFTkSuQmCC",
                         6535, [341.29367, 286.65754, 238.75388, 205.19337], [0.60362, 0.58127, 0.67065, 0.70583],
                         24330029)
            elif (record == "SRR3581676"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581676", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACiklEQVRoge3ZS3qEIAwAYBc253LhFdp1Vrn/EeoDhhACEhVr/cymFQPkd2g603bdG2+88cYF8fV9//jZO/GvH251gCG3H7qxG8dmtbQJwvrcoe+7YWhVSauwCLt+Uo5Do0qOB6A2aBIOs7E/p5wGUSekwgrzSzgd1fNKOjmOC8exH4ep3dw1VCGRIJWEd4/nC6VlDniF/yoqhXhJMU0itqzv1p4mRH61XOSFdz+tSt8EISQ3mBOmKxyM7QUNe2KaCwIzXUBBaHs3V1fUVgJonSK3WJpLcyC/ng8ipUJyXzYLMoY8Vn6D8PFtWwif9LRwYMJlr7IQrhOGjZJakiD/AkCVEDJC7NoIxYqh1jCytalRSGXh2c1UrOifYRBChZDCLJkshcslKY9iHThdCKgLwSIEg5BKQrXHHoxkJ1fNXEKXPXniF0i9kMpCqjoxVfFpL7KVc6G7QaqQjxSFZBOmC+wJdhLKQlJT1kGJQL+yqDwWArGQS05pyiPaE4sQ2f6yID/OhGJXNgdKQgCTkB2dVkJXoi9khmlC4EKQQpTr/YkQuRCjW0xImKa4ae5D0IaQrcO8eaGy114hcSHFtwh5FTzFdyg+AKwsKeRPyiA8TGR7yqeWCn1V7naY5YV8CZf8adU7he7OfmheSKIG392CEKuEUas2C/2vKTT996Zj7SErBEUYlTMJoUKYiozCGYef9xxmId8z3izxpcLlm4jcRLj+dKh/wzpbGJcDFNqrZjhPuCYY+6pbEzVhfLUhhKuEadIWkDV/abIIxcBNhIBup8PCzEArIVYLXb6Y+Rgh5GbeX1h5TJWJzxKCMvFZQm3iK7yNEHcC/4+w4kUEdZ5ViHKp64SwfMDBkPoLvOGy0d2F9DwAAAAASUVORK5CYII=",
                         3704, [182.48995, 153.27598, 127.66186, 109.71703], [0.60019, 0.59369, 0.68584, 0.7064],
                         25790353)
            elif (record == "SRR3581672"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581672", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAy/84xeGNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACY0lEQVRoge3YUXKEIAwGYB62/7m8RPucp9z/CF1cEQhBja6KjpnObssEyLcouHXuiSeeeOKA+PltP/7Wdjz7w10cMOS+OvfyL9cKpuW53ct13fvlWmERuu4tbHgNQVqjSdj4Gm4Xtn6VqhaTsPWdZruw7SDHXLYCslVJukhQYfFxJyHrQi6EdEg5OwQXFh83EsIqVM+WlsMsvNxaVoRl65lCy7eA4hpbLuQhX45wQFjuDEiNVcinCA1HVbEEnlIWrbg/DThFqK1BLXRhOgA+aZqQtR3o6wHx7mwXjlp4GADx5UShciwZhLJAIBP6N/Y/JwrHR6yo0m6NWhWycGajUL1rN0Y+UeAk95O2GRZVhK1+gZDqQsIOQjDyP/sJEIXqpLI8hM8lz4UQvmnkhcX243YTQn63GYTJF4I5IfnNY7Gw//0IYRiE5YisC+VlmjT09xUbhFwXDsnktkcYvSr0BXy2U62adOF9xUiFnOXlwr4htIqSEuJGXT9cNqwoKU5HFWHaMlSsCkXNI3h/4XglLBaS6B+ekwlpVRC5K4Vxl1trxTiInGsQIqliRpgVJYRxmJXC1ad/HEQVclaaIqQZYfjoNwr1/9JNy5KJM2Gon0KJcS5kGYi9NMPYXYrswuHgJGcJzAlDBYowdCV/0MwI+StC/hwrJiFXhaIC4jJiwrywFBmFwxxg4yJmE2lCBaYI6QAhrRIiDKqZWhOikjUrpG8IZcMOwmrWZISZsFGoN5wtTB/bbynk9NpK57yLEFn+xYRkFOZPWbcR1jveRIh6xwsIhxNuwjfVzyDMBUcKwzkQU/8B+8xrhbdmjg4AAAAASUVORK5CYII=",
                         4796, [220.34883, 185.07421, 154.14625, 132.47863], [0.58508, 0.5831, 0.67176, 0.70652],
                         27656275)
            elif (record == "SRR3581639"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581639", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAy/84xeGNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACcklEQVRoge2YXXaEIAyF58FmXT64hfY5T9n/EgoqEkKwoCLY4+05nTEGcj/5UefzefXq1asb9PXdv36ONmx9cbMFBbnDOEzjMNayUklUkDsOg/1XzUsVAWFBthlDM5K1vFQRlBHaITR/3QrjUBmhnaVdT1KMQ0AlhGaTmT7TdJWfywWoxJKEWnbvyiN0h0XrsxNphGQkIu5Tye5J+njFsSRh2R7bQPp4abEkYcmjQANdQah00ZESa45nuJhOSN0T6uOF7MjFVEJ4IiFkEqKSfJOU95yUC+Mvyvam5ym8fO+MMC4ZuViPY+Oz54CQzCUDhdDGGxEqJaOQ3yckIWUT0i2Embt96ILcfVoxLgltAiUIKciuJH0v3A8BuZsYxP6AE9LCQZAgRKhAKAZNeWhSnjLgFKGdjzoh3UC4Fia2gWYQEickmcoIgZjCPtmJ0NJZie7W/snO1mXGamuf6hJe8GS6WQa5yDwh2hm7rn0MmweEWEJIaQ5+RtYrFfjeQRbyhLSOnlZy8wdL6g4ht9wDoZuSswHKI2SmQCSDg2pLiOIUuvtakhA8Ie4SCsstCGV3wKiW79K0JARuak3e9uejhGe3GjZwsrvFA6umEvpWCUJ+AQ8RhvWOEaLvFv0J4SFyYzIwJAw8bYSSqAEh6YRJeRshYegJgqN2hKyPpT/3/NIXod3FysDAoUSErlgakAHdQkjz/C/97RRcJYWQwqM9QuL39WqE8/pWf6X7kxCeQUgrYT4ibC9gyGseIcTbCIHy95zNF11AKAPVCJWsNKDzJWoeIdQDbQlBafgSPotQa/gSdkOIBwH/EyHsNXwAoXsjZ6S/QpmeS7pIefUAAAAASUVORK5CYII=",
                         5700, [270.97539, 227.59619, 189.56234, 162.91645], [0.59013, 0.58948, 0.67576, 0.70254],
                         26728235)
            elif (record == "SRR3581591"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581591", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACf0lEQVRoge3YSXLsIAwGYBb9/nN50Vd4WWsT7n+EgM0gQB5oPGBXqypVaYIlfW2D7Sj1jW984xsnxL//XcWvNPjzabarv1wpSBqEODoTg3qr17BHL4eEbNHiqByv4aUG89NrtAuHQRnezYTIhdIkH++3vVCHvRraPaSzhUKol1LYq7TfUzgnzEjLQrPT2BPZaeQWGwZYI+w86oQ4vJ/94/HCYsW5wRlhzV2kkzCY8rz0JWy8biyGpMF0ZJoDYe7x0SakKPS3fti12ZWwqaauFV5w22j7Vq0lE+plYVO59ShPmLQXzn7PxeHIhbhaKG4KK7MQyGV7olDLQnf1UtHCniGs9HWhrhGaW8eM0PwFJwp1OZS0k3zy70LCPpEIzcRJqEWhTmYfFJ7DXm7KZvIHMR2PKuZmQuuALNTu1B68m7pu2Oub0HV+4QbDBiGLonIIUnsG5c3a9KMQsXJWMhViXuhJFCeeL0zzufRjA9POvyYEayoXogchknxgQoq/Fv9x8P0hdEaBQPExD37NUch+kpA9aSIpxYX6cyGxedcIWQokCTFVButCKIkopFKo24XNmylYirT/QugFZTNOiDCRCQvRyULEFKA0YWgxtAbe4jYhtQtJfRR+9XFhltAJWakVYdoTkk8XCCkyKE3rq7iTwEpJJc8R2jVeKfU5EWumxXwHgtCDxq/peKH927gHVAGxIBQ7KNsZJ/hL+Vih2SHsCqGPhKxmWm0ByEB0hnBcLygmrQoZpHehV1KFMFRqFMoDRwjjkZsCfj5uJay4TOHn85qPErpS7inmucKs5nOE4fHxfkLaBJw98ClCzB74EKEEvI9wy0JcOPAOQlLhldrFH3Ifxj328Z9fAAAAAElFTkSuQmCC",
                         7317, [270.48952, 227.18811, 189.22245, 162.62434], [0.59145, 0.58368, 0.66919, 0.71119],
                         34372243)
            elif (record == "SRR3581388"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581388", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCY/2b5PNDSAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACrElEQVRoge3XS3LDIAwAUC9SncuLXKF7NtX9j9CAwZZA/BTs2BlrptMJBqFXMKHTdMcdd9xxQPz8fiz+dp/hw39bMHtkfczTc5pm5WgzsJJ2IXRlnR+P18/cXc0SRjlODkChTZiiTzjZNZxnTUHDtxVgmm+A0K7h86mqSCnMDmoWdk3rdqn2PZRKqoewF/PpRCFmUwjx1kmDOmFuEAqVSxjQzauJqKTG3ZMrD04nBIN8qlVIqsL0WMiVh61CPFRIC/CnPdBTXyrayPkuIXQTAzkxpEOBNAFvTzqDeKikQpN2eidCOvvesAL8xFgWAhduSEEoLqsg7DlbGyJkF4TuUySMiuFCtMXBli7qi+KGTDsOFoZ0mBciaYorpEJ0Qgzt6dqkGDhcSGryn0gBIAiRCV8foCJc2sJuRiMs9lChXQKzTU9qglQorIEkNGF4SWh/QZg1IxxxUXZfy2abvkGYVs0FmBVCIoSM0PcZ8S1iJ/V/qXguJly2XkbojxZByCtPhFgUwpDvyVSI9JEJa7FhpXXxQugWYkU44IUke6kk9KWVhWbr2CyMJ42FfLKhQkBfOxHSCtdiykLWmQnR3XD2E66HdUWIZqvibSF56i4HJMYLQ05BGCrAjBCjRKsQWYZUCDw/WcFEiAC5G1BjgErIOvQKgT2tCW2L66wlloTIPwnhU7itXhOuN3H+lPQuCtWLOEToBlaF/FLYLhTfifbAo4TrPybR07qQd9cISRlvCKEmTEWHCbdr2DcKYZAQDxDqXsRLCY2v2SiE4dqkF5q4YSfhi9e3Xf1IIDl0QrlhvNDd+jt8QcjnPKtweRWg48wJe+s6QlyEjYtoe3phVMNphdHIFqE88vzCtkX8fqE08BZeSgjSwMsIjRL4TUIZeB1hdZuWB7YLueBIYUr8B67RphdCqF84AAAAAElFTkSuQmCC",
                         7732, [407.31566, 342.11038, 284.93994, 244.88726], [0.61121, 0.62997, 0.72331, 0.72999],
                         24120483)
            elif (record == "SRR3581499"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581499", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAy/84xeGNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACb0lEQVRoge2ZS26FMAxFM6BeF4O3hXbskfe/hBLydxwgQOAFcaWqwnFsn/zVKvXq1atXF+jn9/v1t7fj3YO7WYAVzqP6qGFsVEkrEW73HcZBjdNPX6ohHEc16InsSlBD+Plovs7mEIhSAy5597hKM0KS/Yw6PGkmwBrCDtUxIeYm6ebrl1CkkWyPIpTuhY4JhUI5i/HLCLFJQadLusjvJjw3cHbNqdsJq15P68oKl6EXCOHMckwqTL9RdGMqHgs5oWaJY4K3sp6Y/j5NfITdUQG5SShHiMabiJnIW8WQeDohz2TKwXMJY9syYT63h8XXkPkknRC8DbNeiSXUxCdMJYTzDiDQge8n1FRuS2ZF1xBCSjgTkEhIoBoQmvypQVdjCMOwIuuXlkEOElYJaYFwsggBdsoFyQhNApgJqUgIbFQQIkJ+csWEhuAKQhddIpwTTQ12OqWkCSEEjzVCsjKkrCQvZNn2yJ+ONibLE0qh/Cy0XvZa8yGqCKk5ITFCjFr8EMeE0ooqEoZoduPlhIWYcku9dCJ7TnJCW2I0nhJhsHiEhBBCONhFiOqYIATZTJjkXCXE2PFCQv+2zQjdSw1ZDWHBFgldj28gBA9SJHSLqoIwKco6Q5xoD+HOjbhE6B6LOaGUMyJMGSD5OkA4++MlhKwcci+vxoRTm17rVf+fil6gUU5OWJYtEf1t2ZhQ73DxrwNlwSmE5LdmW8I5ifTmXyGMQA4QckMLwoLTOiGeQCgbWhHidkLvj10RVkyizeRusKcRYnYPPIyQ4z2PUOjYDSHuBHwWIZQ7dkC4ZZmK/fohxF189YQpwZWE5hEVc/4Duw/FCcSM8pwAAAAASUVORK5CYII=",
                         7307, [364.04284, 305.76491, 254.66819, 218.87068], [0.60976, 0.60638, 0.69785, 0.72165],
                         25504210)
            elif (record == "SRR3581383"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581383", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMAAy/84xeGNAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACcklEQVRoge3WS5qDIAwAYBadnMtFrzCzzir3P8JYKAhJkEfFqp/ZFSLJr1Q05o477rhjh/j5PX789V747ZtbHdSSPJmneT5HtTIoCOtzH9NjRj6G9TIkoEU4Wd40qpchAU3C1wadLi00r116kE0KWJnXKJzfNGcTUpNw/8DcRL+w8sK9InuYgTaDWh4XNp2P4yO7xebO5aCSTKcVUr2QJR7sf5lrBzShtnOPJQQ5pD0pN35Ooaz9qRBUoXIrN4iK17tyd5uEKloR4ighllLUplk36Mf7hW4Ea0/U6ih/WygHAHuhgN+ItnG2Hkgh5YWA6on6SfBK8ntR+cAKQvckySM0IaFy9K0IN/+c04WQjIiaFAnnOYI14TLmN2BWiHYCNzWKltzPqDqA3rXvmZzQZtQKMSOk7YWipXdpWkkxXEh5IRjkQjLugrxw033qFuQD2CSkpSmxHJloNhLyPBMGNxFGB4Qo5YXLG00rWSuEtGW7KOEOQkrbT266LQC0vFKVbpYRVYhpYiIkv0W/K6S3kJaRpGYsTJqqE/oYJ7RLYLQsJnOhAfccO4Ths0QIgaLIC/1U7+EfNSHuWaswNTAhm41+jxdSRsh6wDCCccmCMLym+oU+H01b+DaFMBRjPYQDymfQ690CJaEU9QobH2LSlSoEIcRECOS/rAYLyfh/LTYAoSxM3wQ2Lcmw04YPDBJSjzBqQxMKnyrEXYUt+9QXimumHUggawfyA5sL9aySUBzhabUDCZf/Sz0QbuGxhJmsonCuhBcXsponEGIdj4ivcDEhxE/vZMKqbQrKddcSatedR4iXFxaJsHZZvRD5WvsJRfI/zfToRZxqxRsAAAAASUVORK5CYII=",
                         7563, [249.86393, 209.86437, 174.7937, 150.22377], [0.60671, 0.60281, 0.69057, 0.73275],
                         38460577)
            elif (record == "SRR3581352"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581352", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCOgm513YCZAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA6klEQVRoge2YMRaDIBAFtzCey8IrpLfJ3v8I8clLIpAYQlgF30ylsCx/kEoRAIAduFxrRW9/tzj6cL+gU86qcSwcw5A8w6FsCFMyv+FQNoUleYbSlU1hSeYtPb1hN5RNYUnmLW2I0xv2qv3RGWzBsH0wbB8M2wfD9tGZyT2GpvNMWN3iYWDog2GNYOiDYY1g6GNl2Kv3qyHeeClJ+x0R9dKHSCT0mnErpnlx0h6/g6FguNULQ8GwBBgKhlu9djHUqHkYahVrlSmoSdnd7+Vel6E3Xd3Qs+RRmbBLBIYYCoafemGIYTIY1m94B5kStIKyXxu+AAAAAElFTkSuQmCC",
                         25, [1.2345, 1.03688, 0.8636, 0.74221], [0.26705, 0.21661, 0.25825, 0.31728], 25732016)
            elif (record == "SRR3581356"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581356", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMC9d0Dm7cNnAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAu0lEQVRoge3YMQ6CQBBG4S2Qc23BFbS2mvsfwcTCZCUbl3EG/PF9HcksmYcUhlIAYAeX68+62bd3OPrhfjKb49CyhO+Rx1VYo7fI5PsNa/QaiVyFZYpeI5HvLT194VSj10jke0uVnL1wNqNQHIX6KNRHob7/KLwfvUQqCvVRqI9CfRTqMwrlUaiPQn0U6tuhcMufit6sNZ8imqvVkXb2edlb4DX6dmYjCkdmKezPUkjhCApHZinszwYVPgDiwwUXTCk9PgAAAABJRU5ErkJggg==",
                         13, [0.62284, 0.52314, 0.43571, 0.37447], [0.19334, 0.19339, 0.21455, 0.24533], 26520999)
            elif (record == "SRR3581347"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581347", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDDjGB0pJ6DAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAA60lEQVRoge2WQQ7CIBBFu9Cei0WvoGs2zv2PYBRUpEgYbEvR91YNnfkzr0kThgEAYAOOpxxnkUu2YN8U+I8idu1vvDBGV96f4cHo6vszNEZX35/hNOnq+zP8/f/wDwyVYNg/GJYESPj8XdoKYFgSgGFbMCwJwLAtGJYEYNgWDEsCdm1420m9lPjWe5/MDd2LUeadlYQztGCYHuhbbTwdw1owzIFheqBvtfF0DGvBMAeG6YG+1cbT+zJ83jFf8e5oFAkLwgB3JA/DeXB0cQ0isnVvBUpdDAcMMcxujmFSCsPESAwxxPDz5ksYXgEIEPu09fnVHAAAAABJRU5ErkJggg==",
                         24, [1.24297, 1.04398, 0.86952, 0.7473], [0.27802, 0.22622, 0.27595, 0.32558], 24534514)
            elif (record == "SRR3581346"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581346", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCXmZnsxbRDAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACsklEQVRoge3aS3rjIAwAYBYZncuLXmFmrZXuf4S6OGA9ACNCMnYTreIHsn6gYH9fQ/jEJz7xiRfEn7+O+Oe5+QTh7w6Y38Oz47aEWwjLaHOaWMqTYrmFZVmZQwF4AeE6fMsyOoZAVxDefrtw+fXCuNLcvsYan1GIU7O9nxD86WF2H/lLaAUZoTs/0UC3NMJfQTNWoUhI/18oC3o8nRxEOINwLvEdhe51Y0xYf+F/ttC/e+g/5c5WtWO4tJANnBGmHGMdVn+kEtKrhGYTnShccyM7eFgIrZLUhfXZlH6pSznJnm7021zM8yhkzxLCvie0hJaR0ps27MoThHuqglBVUspXF5I+frmQopDEcUjLwLYJqEqCPtcQmtf6kwjXyxSTb/epSoI+VxCm/bEptJdQ/nALwfRRqAgpCmETlr4cxLnJQpbO+yJhZ0FoC6khJHGgqz0W2n13ipBEqvxI9jDIQkrC0h8ZmcUq/d6KupdmRhfbQlKNZgpTygSOA5uEZhDBCuUud34h7KftFCwL8f4zfpooYVoxIAsLM7so9K01DiHl02hKwbaQft6YtJCQ3ekTeoypJU/OBqskjFNVloJ3NXsvUEIQwri7CiF2CPNU9ghz3/iFwLPgdq4u/NlOmQj3SXNPD4dCGhZSUMkzKR6hEcoOCHlWsxT8lj4htYTAskchht4gnqIszCtMtxCKQpgn9HxJKSHKgjuF7IaGUIqGhaB6d4awGiLJkZCOhHgsxP1h5xciaSHVhGTGmRyDKIS4v8d7hKBPgayjKCwchz1DVYiybSdwvjAvvy6h3WazMN2i27YDtgWN9ETvF/LFTQpFHb1ClqEmJNW2HSLpXKGs42FhcUc+9KmyridEjzAtY2cVlndkDO1/iSk2upzQ3P9Gwn21K5XcL5SCsrAu6ha2It/6DZcpXc+VILPFAAAAAElFTkSuQmCC",
                         4493, [96.83866, 81.33621, 67.74402, 58.22156], [0.57834, 0.58028, 0.65599, 0.66457], 58953949)
            elif (record == "SRR3581345"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581345", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMCZ/wBcL36IAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACZUlEQVRoge2YTZqDIAyGWTg5lwuvMLPOKvc/wijlNwQFRpxi/RZ9CoTkeymiVqlHjx49ukBf3++vn9aJ/724pQKqCJ7maZmXpZuZLqoinKdp/ehlpZOqCFfERS1zJyudVEeof8Kpl5c+qt6l83wXQiBM+qZZLdvHUKIawhEFlAHB3MBo+mBCeghHUUoIr/ZtCFOQVxvuQiiAPISDSSKkzMCY2kDYQ83QhOkDmkiIalRC4SH7doSYdn00YdW78TXC/eGYEF5dAiHJA38V8DZKUfsKpkhbzBHq3O7ITAnBDDRY2BEjsm44+G4K8tEyoU2K66GzQ0icsMZFVsySLRyef0d11sW3ScQXdOdZ2yfTtUPoRk7Zr6yQdQNBv7BxI+htDtmvaSwnRHUpIbBKEuH6lfsO5+gD3s3ikfqtPSLc9nSGEINFULX/OGbEK5n0EHilYBe6MN+BgSm+XrovIVxjSgl53XolR5epTN4rCW5CQmMaXbp8iUNCM9CT0FrUhBgQIJvm26cS4umE3L0j9P0yIUUzagmlfZESQpqsUNvS+H9FojQvixgQgkAYlk4Jo9BKwjBZckaUa5sYEXpPYNpmQVEm9P7gmJD9KJWELFkxICO0xYBZ2PIzO8gIUSIM75bgR8sJ/UN4O2F0kWUckPs1HZB/OraEUQaDY+9joOJd0kBYjkj+Lh3WjKslgO749oTunsU8Y9TkRC2EYlRWQP66rSKMAzQhXkBIqpbQnMNBmWZCe6L3JSSFYtQOoQ2Pa7YQyh1nE4IcdQToL6u3J2RTDwTZiXchzE8cgLBom45NiG2AAxGmiL+7faeQlVYb9AAAAABJRU5ErkJggg==",
                         4477, [224.91248, 188.90728, 157.33878, 135.2224], [0.5521, 0.55302, 0.63155, 0.66299],
                         25292910)
            elif (record == "SRR3581336"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3581336", "Klepikova",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMDMzJg85+yVAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACi0lEQVRoge3XS4KCMAwG4C6cnIuFV5h9Vrn/EQa1j6RpaxuKgmNWPMrffICAzn3rW9/61gvq53egaGTwAWr4bCDtcIo3Faotl8VdnFuMeXQC4XJxy7IyTQVnEK6Xb1nLFndAYaGh2zW8Xo1xZxDe71Lr7/CIQtXRpieNTYi2yfqKaGb8+jO05M1sIS84ghBmtqDCP0VYjXiHEPRR5uniYjViijAl1IQcBQUh8pX+idNjrX7UDCG7yepCNiYXyh6OKGQJVWHaSkAZkTJhf0MvElJDCGl7Gp6/MicIoXAUxqn7A2vTEF8W/ccOiC2tUwqjEOLINwNPRbkLwlUl2yuaRzWFaRo+oiG87VaPokqhOG+qLYyB6LaUFrK8ipByoUzoFAKKVLkzbtldiGE7shHPhPHEPJ0Z41KH0PjafSZE2YEQom7P78dWS5BmxrhUEcIeQhbk0ytCSD1kCY+eao9V/wK+C0FHxJy4y8cYhTwc8nvQr7CNk4VUiBBtMaH143CTEFV7PUJ+b7aE6MTvZn8h5CPgfpNBKWGWUJ/QucIwc1V4WwB+SCYsn/VeIe0nRLYvCpHSgIoQlLBEhFcJUQuJ9xenCRvJoRYif/4WhAUiKSHpgT5li5B/FYU3lBQCCKGoJAQhFAnzhGgTpm+G8PyWAOoSig1FYfYMBIMw3MsjQBBCdj2ZkIaFUBZ6UYRJIU/YS4gtYbFYiwPCsJULsSEkYPF6zDuEcZUJmQj9s5cLo6IpRJsQU9R+wpT+WHXZukyoCf2lPoUQjUIWdHBhab1bOHIRzyFMhcVRrYrDTyIsj/rXQgjD4TOF4Sf8qcLbl8dnC/lwOWe/UApeKMQxYX7gCYTPr2L6E3tWoSL+AXug3lcDHhimAAAAAElFTkSuQmCC",
                         5165, [268.79382, 225.76386, 188.03621, 161.60484], [0.57377, 0.55484, 0.63103, 0.6844],
                         24416101)
            elif (record == "SRR3724650"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724650", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACYklEQVRoge3YS3qEIAwAYBY252LhFdp1Ns39j1AfPMJLQMTBfmY1hSHkRwU7Qrzxxhtv3BBf38PHz+/ZkZ9e3NIAqvm2FLOY5DTLTtX0iCrhghNSTlO3anpE7TVchPM0dyqmS1ClcBLrJZSdqukQUCuUYiXKPtX0iDrhtNygclq3m+cE1V3D+wMbx8PwwtbyDoRA2Jj8kvj3wuYqhhPC1VUcCOkjQn/S/yaEPsJ4imTH1QHszoTgeG4W0ghCi6KIsHEzjQjV3/cJmYH8h6b9vH6wsLC8qJBUT1mK1mBCCIRBAxuGRekpTKEarhdCNB/Zy7QB3Vl7CfFokz0d8WL3Csh8LBWWPqBxIen1LMpRGOEjhagrwFNCDBojP1hkhGGO8+ELYU9/sTBou1mI3t+6AmJCp5zK8xp0o33mPygkR4h6SlUOJOtzhweN+xSA2vgcIbhvypAV8u0r+NbSdL3Qz7dzNAt9IRoHE9oEOeHaS+uFzAib/8FmpLjQhmlQJaaEe5ICIVvBiBDBLG1L8Nw5IeaECnUghFAYu1COsPm1F9lnJ51Xw0mhOQDXuwXsIt4lBJZAFWsqCoRuOSkhgCfUolqh2QGahDyBmzDtSwrNolshCitaXpDOCZuIaeEBUAvRF+r+hJD3lggTnYWh9lA+3qmvRLg9c26DLyQRiu4Rghq2jWdam7BIiFlhRHSPUE+0zXhemGgYQAhcGNyXQwoBqoVkp3mEsObdhozQmXNcIYq6Hy31C6adZXSh2tHKgepkMgf0A4RsYDbAH31CiH6i3kJnZC7SI8cX5u9TSAx8jBBD0x9opRqZJH6brAAAAABJRU5ErkJggg==",
                         18663, [612.15029, 514.15398, 428.23314, 368.03841], [0.54649, 0.55728, 0.63516, 0.68237],
                         38739023)
            elif (record == "SRR3724649"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724649", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACeElEQVRoge3XTXKrMAwAYBY8nSuLXOF1rZXuf4SS4h9ZksEGQwyDptMGV5b9YTBkGJ544oknToh///uPn60dv31yi4Nqkl/D+Pn1PmoyRwTUCMcPbhzHCXmdqBIOr0k3/dx3DSfh+3XzNRzGXq5SKE6sug/f/ew0hEaj1Va3hv0EmEILQ3cXghKaPfsLU2hdkJNQZIZjMEr0E3ppBlM45cnMIOx7MUktzWAu7KWF1oKhbtJCymYfH8UPuasKjfsoNwlLiMaVawoxl314GNtH7mFmCMG6NykrNO/kpmHs1Xpnz+4GGaFLj7VPFCqQa+C3nhZm75VdQnJ/MrU3hrzHwE1eCGWWmgWGzP3Ctu9zcq5+vfjaWkL7nWtNGJ955wnlNeE1fG31oNuFFEtqIdoVdoXa6NwA1E5IXEhfESYFoxBlW5olCjEhqtxSIbkKLfearJA3qzGzW48hBCkMd9vBQreTqJH+jjER6mmr6YX9SU+PhJC+IeT1mDC8J5rC+b8QGjDk6lQlBFY/Gfkk4edSmn/jkC4CT5rLzLUSobomtJAyQmwlhDWhd5YJY0KREMHXV0JqJAQ/eS30g8/t7Hznhcgm5T6KJ40QxjOohV6/k8hqyKHEHDJDMiEmBi8MFbFSSAcJw0lXQPuSWhEaom3C8m/efvqJin2mvDCdjnvT4ULfpa3QVa8kArH5bRXGHd0y7BeK4bBKSKvCBWAEYdfC+D4hhOlRB0L3BafqJRyWhJQeLQtFw2FCnbMcvN8eIeFJQogdi3jpE3WP0G5oLfQnsnQVfQeMBe4lBNn9AsK0az3wEfYjLLlMzX61wlRwphBXeJDreBmhJv4CX8pm9/pGKFoAAAAASUVORK5CYII=",
                         21767, [674.81964, 566.79088, 472.07383, 405.71662], [0.56953, 0.5799, 0.66273, 0.69552],
                         40986056)
            elif (record == "SRR3724651"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724651", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACdklEQVRoge3XTXaEIAwAYBfTnMvFXKH7rHL/IxSVv0BAQJgpPvP6OhUh4UOlzrI88cQTT3wgfn7/f1DrwG8vbmkAVXR+v5fX9muqqBIq37qug2YyKuqEqxK+10FTGRT1QnUhp4oqobKpu3R2IWC682v7ea0DpzMgIiGh+QuXWwQ9wtkDiIC3WGHugZwolDC4iFYYXd2rlbqmq6j7CPtVwtM+I0IQkj2DfSthUKlr+kzdjLDrRQzzQdlFLelzVjYSoj11NT3PGwiF9ABhy3J1lb8oNOl9lLAb1c0hHp8R0njhfsyF4Wwg+ajEl1tcIVG4N+AIIQbH20erUJqc8GhTUkidhdBZKO5TxUJcOgm9Fz9ZiEqIQRvPkBKKk7ONLulgoZc7yrdXJl9IwpOREQqzU21HI6BJKwvJnLlIhBKha5VKpuYgbCD+baKE5CXl/SRh49eMIwG6Sl6afTpA/o2ZEIYQtMODE77Qnk0K4Shn3m942dLYE+ixFJTSBfRMybWwUg4CZh5UKkS3Y54KW1+aY6EtZvLrtq1AgZAQyoVUJWx7dyoVHk8jv21cBicEtwSexgJrhNhR6L0iuWIceEyc9fDXpUxo0vhClWUqoW9wFykjREoKg1umVmj6+zWJpCMpdAosEpo3IkD/rFvBeCVCoUmn/5N+UOi2V00QhOie64TQS5kQHq+Oca9sUEZI/CgjtM+KJpgpcWEoKhWSE5q1KweaBYG+QmYAdtQidGHWrl7IajYJg4bbCc32OlzIhp6G+r6nkwIb2CKUG74upHCv+vdCPvQcqJcEg4F3EQKz3VUoD5xAWLKZSsCJhNgGvJEwP24GYUz8A8YBbeehoxelAAAAAElFTkSuQmCC",
                         10967, [494.99636, 415.75468, 346.27745, 297.60285], [0.59801, 0.58326, 0.6652, 0.69894],
                         28152120)
            elif (record == "SRR3724652"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724652", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACWUlEQVRoge3YS3qEIAwAYBY253IxV2jXWeX+R6ijPAIECwqMUvN97YwggR/Fxyj1xBNPPNEhvr6vHz9HG356crODCvadZvV6/7tXlAjnaVLzPDUbS5OAIuFrWo7g3GosbaJIuB5CNfIxfONGOksxKrnllSYtBOw4jIaRFhJ2HEbDoJQQxhGiXDGKECIh6M8k/WYRC/U2Di+kgYTBpWYw4Rv4/4SkPzoJIfH9UGCc/mLCs8T45i4KcfvoJWTdlL0GCLkKhSe7yww+qvjKfjyXSykLhYpGUVcYNb+EkPh3zG0njU4QkiQk1UjoJ9QLkAsLOhUfm22hW9z7wrpEwEBoFzzvO+xz59UHhUJNXIToUvYShvkyhZjMFtfYwmVxk0sZC9EIE9kPRfh8qLd5N8LSgNQ0C5OxnCROSJ8RYrDtj0Dqs0hInhDtfrGQeggpElJdobuvX0G4XvtKhMIJHQnJdLMjrHmpCUfPhbjWCMJw8Spz6ZGErHm+EFW1CLvS+bUw0WVQsBxqYEJ/dPy0+1OIpruKT8JbOvS3yQrXP1G45YA1nb1agpmfIJ8nRPmut9XVEhL7yhOC3jbFOUJiRwnM/BiR39zuKSkqCoElID+hk0WRFjIDmFnZE9r5E4RB3cEX0zWBfkQkaQRpIW+lh2DaoJcgzCfml4Re5dEfh3mf/gh2gGSHiHwVgT2triB0PyoLpgIhBgUthWXrkdg75gkh9RHqWxYWCu3N/IxQLqgvFPfa0ZkHMb/PCwvlvVIBZkrQNryNEDOBiYaDCCXgQELAvYb5Ql/QUSisxF//vpekTAuApQAAAABJRU5ErkJggg==",
                         12348, [490.94948, 412.35565, 343.44644, 295.16978], [0.54514, 0.54451, 0.62085, 0.66775],
                         31958404)
            elif (record == "SRR3724663"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724663", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACV0lEQVRoge3YTZaDIAwAYBadnMuFV5hZZ5X7H2FEkL8ExR+otOa9ea0gkE8R6Sj1xBNPPNEgfn7vH39HG7774hYH7Tj3NahRjWO1XOrEHuGgXvNfVwG7hPoeTsauYpdwfOl7ONTKpU4wIaycPGhhZ5OUCwnzJ88rzUcLu4xvECbELxC6Y2ycSqXICwFb51IniAvRfsHWuVQJeITdhyQkW4Pt06kQa8I9O9b7Rl7IKvoMDeRCnD6Q6BbTFE+2Xxfe4SbiyfZ5oa649iau/SzLN8pe5cLLLwtJVRDmtvghnF+E/Iq+kdwyXFMhJsdmrhwUyhUY1JtPaiaEtLdSYWY2ysn5PfWmECoI4+6WKxlu8PmAK0Ihu+nGmkKYFkrDbSdkI/m5gkGZ0CzbH8/OTRRww2WEaE+5kCgLKcxUGDHZkATfxZcZFQspEZ75qWjbsvSN0C514E6Js9EF/uGcVxfTibBEql1CbCOERehfwfxhtdtkm/fVQvdSqSN0g+ga6cGIhKY6LwTfHKwCC4VwZv8WCoNulgFMsV/ctoS0Q6iPckK6RgjLBNwQIvEHgwl91l4TTS5BOPdcJsRDwiDl9AZFQp9LfFEhKHD1odCJEMPatPc1oevuMDASOiIDJumYi7ohJC+k3cKoEvhZR4VuW7UtpFjo6jE6TEUHhBiOUxjg/k3AhCiOIgpRJQV1hPE4pUAzUF64AgyE0EgIYdNCoP95wkzlwmUxqC2MmxbwFiFEDY8I5YI3C2m56Spp+ClC3TOKDT9JKDfsQFiymErAjoS4wfMboV6FnPgP0BbKTCEotFgAAAAASUVORK5CYII=",
                         9063, [439.34988, 369.01639, 307.34965, 264.14695], [0.57333, 0.56108, 0.63868, 0.68628],
                         26211190)
            elif (record == "SRR3724668"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724668", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACRElEQVRoge3XS3qEIAwAYBY253IxV2jXWeX+R6g6AUkIFlQctWbTbxRJfuVV55544oknDoiv7/PHz9oHP/1yi4Mq2nZ99+pd36qURlEj7F03MluV0iagSjh8Q3e1b1glfHWjr29VS5uo+4ZddychYXJpmIIvNw7UK0VWCIbwkvEIrx+Ug2RvXCwggcD7N95XyL/pJsIBSGoiPsKLxf8UEv95hGcMTK6YQuQbafMzBe9qMtLjCy0Ja/7raBaYu2F9AOOAdjIhQHKp6lB5TmGMgjRnbq6kRxVnsj8p5ImkhKga5Y/NRn2lQnIs3JeosntNvGKky1trYab3VaGzB2GUP63GGLe5psNoCCUPr43eU/hQoezOZ4aogo1CioSwKMRGQpHJEBqTf62QfLe2kFoIdSb+HVVg5cwtBtZKSLGQGdZ68gkhzhX+LZwaFAmRu1wQ7kgE3d2Uh2vAeUDJlCAvDNML/fpkvQwlJMgK8SDhuCCERFZKVd/0MtDszlH8uO82K6TQZB+eE0NIVJQIk6H8vgBOTJ3NwvBut7HGvY53dC1UNQyfU5QTP+WFsYGx8zKM8d0aIboNMT0f1zqnAi0kJXxn/luoRaVCedM48pcKQ07+UmLrs8PfRymULz08v5Nw5WBNhXLrWxaGFf0QIe4sXADOQhRCadhXSLXTEebzWCKUv84g5INBsY53GnRq/ZbZioR+8WkuhFqh73Sz0L6wvzB6sAQYOpU5Tyy0W2UiyqRyXkCIJcL8g3cQzjvWNqEUHCg0kL+jfZ2ejaLHYAAAAABJRU5ErkJggg==",
                         8161, [342.80229, 287.92465, 239.80924, 206.10038], [0.54442, 0.54186, 0.61786, 0.66783],
                         30249969)
            elif (record == "SRR3724737"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724737", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACRUlEQVRoge3ZwWKDIAwGYA8uz+XBV9jOOeX9H2FTAYH8OFCxxZrDWjVCPkFqu6574oknnrggvr7fP372nvjqi5sdVJDbD904/WkrpCB36PpuGPpqtVQJKhIOi7KpKBKO/cQbatVSJ8rGsG9vCMuE/dCPwzhWK6ZKFAmbjLTwLnSJIcLxm7aDJIbYbXqEbcQf8AOE0Y34AcJlm9XgthlQyNPL/YX6Bm0z7i+ULeEtHmqgcNoBBveCAL83lBXB+vxNoc6vHEiYKgIe0NdjW3j5IBKrPSkhPAC+RmAhW2Gi9WqhnyFLhWonFsoVQluNPzN1l5SaSLA4t5PYTocXCm3zkRDeM/h0OCXnNiehrHnvIDQ9qWooJURrPfEqdEcTQq4hFA56Ms3LPA8NNkeYSg3Wf7dQSqaw5HfxVMTFeiXQUjZYv4EjLRQlXF6QUELhKb9WxXNi7oaX7pZVR/S80YPKJwmZJMjn7nBAoRiWN6N466T17oWpkZC8xuPM84VxSaYDJxROCQU1kiV0AYSWf1DoTe+lQbfYRCWoi6qE5DbZa44oTC0Q+seI9j6/zWsWe81uCYMSkdBcA18oqr1dQp2TGVM/oTBRAShH1jQjJFFC0F6xkPZ8kSKTP5/ofZivFWwADSj+/CA7i88WCrqp/wubD025wvXJChnOFPqzP1/opvcBoV1dKwvdCpAPJJNOR4V8jRBnbfCcMOhzhzCx49VCO+gNCjkLuPYc1XAXISVPvIkQAdsR/nsjQt4OIceNXSbkzv1jysQvIgfB+JKfQ78AAAAASUVORK5CYII=",
                         8086, [278.76043, 234.13496, 195.00841, 167.59699], [0.56644, 0.5552, 0.63354, 0.67874],
                         36857670)
            elif (record == "SRR3724739"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724739", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACe0lEQVRoge3XS7akIAwAUAevsy4HtYWeZ9LZ/xLaDwgkAUmB1sNTGVhH5JOLiNY0feMb3/jGDfHn78jxr3z505NbHZC9gqLkZ55+1sNYQbkLgKJonqbXehgqwCRc7+FyGCpMwteyRtfDUJEXEoqieRXOowuPW6cIl03mNY+20wjhAVOEQ0ZWCJRdv2NFSYg353JNCEck7HsT8bRGv1ZxCIc/v1yovI2UaM5BOvz5cqHrMs1v2sW4RIjut7cQi+dbmWzWnENWSL2FvDdtJ7tLSO6nuzDprk6o3Wlb3ClMR9K6l5+QzW9l4OOmwp6bqSLcziEpUxJsG1YX4uSF2NZ9aSQpJPnqKgjrtuJfJlRGzAsrc9OF5C4c41XOl2kkd05MqM+31l9dTvcJxQ06hJhUSbOBgrBM9N2eCSmt3hC6EKMNCBQhKwHWXI7iK6LflvV1IYXtmyoX7nNLbjiazoSw1cDw/1wTgl/zgGQTtmzZLqeSELZtg4jXkUIqLL4pWrpANiFcJSRyGSzfO1glJNwrVAipJMROwlUXCyk8KK7//dfrjMKkqqseCSntISP03YnOqmLrKRYSF5JByFKS706DkEIGLULY7lqFMIm9QtRqb4DnwlD2hvCtZUp5YR7oHwxMEt32fy5k706T8OjuEFqIED3lbwvDs5IXYpRVfNUqVOarXkhMGGdgEyY9eGFIS+kfC0IKKfj1bxD6gfLCAjAWsgIhDGkdE6DO4IkQrELw1VVTZyEXVQtDfE7oXyKXC5OmFiG0CvWC7sK0qUGYTs2jhHt11vA5Qv8xzRs+RkjpR+bzhJBt+BChBhxHWPFCVIEDCfEtn12IvLMPCv8Dg16KQPRwqOYAAAAASUVORK5CYII=",
                         9843, [267.69908, 224.84437, 187.27038, 160.94666], [0.5881, 0.56137, 0.6404, 0.68175],
                         46720327)
            elif (record == "SRR3724741"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724741", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACUElEQVRoge3XS4KDIAwAUBadnMtFrzD7rHL/Iwxa+SWBAq2Kjlm0lTGEhwqOMXfccccdO8TP7/hBvYlHT25tALWcPZmHeT7tx4miSfiYzDQj7cd5ovUaWtx0C8eKdqF9CK8iRNHymBcZKzzTSgOUFRLuOI7t4j8L4RaeJGh0IX6Yby9hBoK5P+wcTZuZEopwPc7Stw3gRS8mBPFotL2QaF0OJhTLwsergSZ8NVxJyPpcG0YX1tIHE8rRZPfrWiGpQlzp0DzEYi29GUwo0yCsvQC6kFbhV6+inXTiDctXRJc1G4Wy7UAhrN1DKAOyZvadSx2csrfsKiQuJP8N7herKZeeaJhaDfcLo/P2EvJK6zEtG5Zb3HhNObw19NdNfz/YVyMMPewoRHZsaoR87VlOUDYBE20AgO5yvhF+k5gThkJFoV9w/dNbFNqJM2HatJEcJxS3she+siuFVBbS94WgCedhZIQYDWbJn2/o+Q7NC6MS4BNzQgRlQjtYgSQm7NW/q4P+waA4MxXO44IGIdpethamm3nSHbFgQr+TeCGsMxILk7euaBLB97qxcBk4JqCAZ4HJGVLohxQLXX/g01HrXRESpAnYBYS8UAB7hGiCqFuYPBWtQVmhBLLhwPKdCP1UhA5AivqEvf+GxjXTYgWgFxIa1iCEiqhX2PY8uvM1YXp0oDD5Y6vQFVJN9UL3bG0vlOdcSojqa0ExIJqZj4R6w7eFfmus5EWb7DWF5O4tDB0ML0xS3wTw7DMI09RyFBKvIYRCYr0QeVfDCMuJJxAqxD/nORzPMkU7vwAAAABJRU5ErkJggg==",
                         15382, [343.41181, 288.4366, 240.23564, 206.46684], [0.56742, 0.56505, 0.64516, 0.68708],
                         56914490)
            elif (record == "SRR3724768"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724768", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACp0lEQVRoge2YQWKEIAxFWdicy4VXaNfZNPc/Qh1FSUIyisJU2/nd1BBIHkLACeGtt9566wX6+LyUvi3j19HRfntyLaFlhIIBuj4MYRjqZHNSVt6Aez099V0X+tAdyqi2LBogy9M0ehrh+vHvCiLMbQ6h4emqnxkvINhNaHp66sJ1FmkbwmHohv5PE15I9GcIvUJ4grCotrZXlg5GOxmJOtjKeHXC2QAlhMqzGWHJ1SIpyzkR6haHMJuLdoRG9G0VEIKJnb/tZpUH8MDk5YVwNjzy1sNNNoyxhNUaoYHMnbMlRUjPCOmmhKITAVUgbLURzdogBdkHniRM6/CKhLoMWFcNyCaBThDCVL5zx+X5WHH35RGC9OEuoYgQDEKwHOMz1t6PLiEB91FRZXokCaVvRkjjrrUJyYx1VjqlZYeNhNE8HidWNiieJKFaAImQovdTwrqI2aTzXOdjnKeovTSDJgScG3cSQitCteIeASA18BR5LzUGrv9i+piY339OiDYhRcKaVZUcQlrTFi/BJGQOcV7SZl5USIihmo4Ryk5lhPAKwmkq0SWk1b5NCNIhzgu5hBhtDiHN1/TTh/80V5wwpb9EXhKDQNpFE3KHFWmLUE/sGrIWIUrClL8inKJVJcRkMwljTAxn9IihCIk1LbtBEmZ3mEiIZYRCHqGe0EOEuJdQpgPIvRoSnlumPKYaMDbxpSQJp5d/Y8IlA6Rcq4MiXPvUJYzD1SOUGWwQcsPqWplwuqMW/2qMW4QGWE5IQRtaEVJpxQFiN+kThPgiQjhKaDMVENqGNoRlG5Gmz5PbECLruJ+QHXVXJwTT6YniBTOddFcntJ1c0VIf0jlwF8J9iPAvCLVuQ4g7AJ90fBWhOf4+ws2X6PUrJZQEDqEanbun6uikvhGa6weKjbZ/8nuFrgAAAABJRU5ErkJggg==",
                         3749, [348.29947, 292.54182, 243.65483, 209.40541], [0.56362, 0.5712, 0.65794, 0.71026],
                         13676907)
            elif (record == "SRR3724778"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724778", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACRklEQVRoge2YQdarIAyFHfiyLgdu4c0zyv6X8KPEmCAoFqjW4+05bQXMzQcIate9evXq1Rf0739dUeV4RWrSY4RNwmarH7qxG8eGDlcTDn3vvvvKUaEj+U+00/Ab6ifEoXJQIBk5uJxw6IehMSHutGyv3n2G2pPUzUwZucsJ3SIzVr8Mb0XYRo8nhJfw5/V8QrKEV2+IDfR4wnmSLnOTXsJf1Ev4+9KE68YBF2ZUWR5wS4hcj7GTTlqUhygRsXwuTQjDef/l6+CAEMrSgTkEBpYYadlOzyI0kcFTHBKWpAMJwpKYuzKBAWfnhXCuU4Q8diV34kBTlO2NoCtos/gEb5n4MUITAoWERc8aM5t+cmE1Iwyc2HkhJNk4OLulEZYYEsYJp5LPA+8Yoj3MIkwsNfFiMzZztCSh7EfVBAeE2FEWoVyxUQ+dt4SOELrpi7UZA0Iw4ybzyRLaAWBo5JpIflJqlukEYfXXCYGVT16wnJ1J5zNCyiek6oQQI0RaCW06ilBO8v8MYXBDoAlV56UI696+eT80R3FxA5RcfMG8N9KGkCP6X02oOy9FWH4pqi62XhmE69rDhMB5xQjXDlmOYRMyTGVqXDxR1VRfYoYme4RwSEiaEDThNmQjQpkI1uwDwjUtqdeExEFPEhYi+l63hJBPmCgQQqpBWLbaqIw661aJELZEpwnxMzBN1Y4wRnSKMFKZS6g5nkboNgg+bXF5GqGcFnjmE1qCuxGuxkHGNyfMfx2UzPjGhHjqVfv1hFN7OEUYb+T1ByyihGJlGEDdAAAAAElFTkSuQmCC",
                         3270, [265.9299, 223.35841, 186.03274, 159.88299], [0.49657, 0.52846, 0.60521, 0.64686],
                         15624490)
            elif (record == "SRR3724774"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724774", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACOUlEQVRoge3YXZKDIAwAYB7cnMsHr7D7nKfc/wirCEJCpGClFcfszI5SfvIVCrbGPPHEE098IH5+rx9/Rxt++80tDqqoO4xmWv71FTXCcRjMOA7NcmkTNUIzzH/j1CqVRlElHNd57CqAsLyynULTuxC1Wi6mqcOdJhFWrdqrBSplqVCr1UugUrYrhA4nE1ArJCHpWqjlvCdE6nC5VgnpNkLShdChEEqF9r5LId5dSPcXqjnDfYTwCH2stS4qxMxrZCMpvrwQ2V2Uq3xCg1WIsvLlhSy7eK+U6TEhhKZZ4RWeTIUQwiXyilyIW9N06a4F7YV+lanfB6J04pdnIW6XCLxiKkTj4EbWNF6YH/y98JOQ/w7Dp2pJCvylmIAqIX1CSLFwdyT+xSDslmniUjg/4CxrOis8ea9BvqyCkKxQHYttExQllSROXEj+8CgT8gV/MEAsK9f9Oty8+FD7hYilFxvk8Q5vCs/YckCsiUhIVqiN8koYba21Qlffl5wD3BX67ECeAUvpqgBFSOHzmwghLwxhzjr8IU7AhA8SyWBDhbd5meNEiFvyonkQhh5aC6MOjwl5hVIhfk0I7gZIhh8KC4SRaO/+pZCMNs+lsRy87imkWOhq4HaYNRdq81wKtAYudBlA3LmSDtiqHxFC3LAybOeqcLvLCrELoTQRv8sJvb+xkDUsjfXwZk2PCPWCRsIqouuzM2HFXrMOxE/oOwlJ9tCNEAuByf7YjbBoEkFp148QC4T77XoQpsR/bsPRrqdEi24AAAAASUVORK5CYII=",
                         3161, [301.05144, 252.85751, 210.60221, 180.99884], [0.55598, 0.53252, 0.61167, 0.67529],
                         13341635)
            elif (record == "SRR3724785"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724785", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACYklEQVRoge3YXXKEIAwHcB62/3P5sFdon/PS3P8I9QNdkqCioGLHTGd2ViXkB4hunXviiSeeOCG+vmuKn9+i6a4e3EiAcjO8Gvdy73eBWo6JfGHT+lyTX8lRAc5O8ermsMkv5aAoIOxWafdXaeQLe15ThZBiB/OF7Sbzbtrt5sqg8YP0GVCBVXp+mJrJf9h9E8x1CpermhOyFbZANgdriOWq9Fm/EBHBzAmxr65igW1Cj+hWpJ7euwpZf6ehVbrw6ptzWQjlwHbhyhAeH9qwfHZB2B+K5KpcqGsWQtKnopN4LyHNC6k6oX+eYZOQlTB4iSGuVNjVvFBCqpA90KcKXgdghGftrb5fKSRzlRB+1qbfVsbqwTwrNAPov5u+sgPy0TsKxdIyw7si5FVhZNP1GciVDpAYTF+MEJrfBuJlGkZI+4QsL8kJkUXeb4gLVbdiCfNGIcPNCMmt7eGpIebECPuvQVlMdlMQwsAAJYoKeZx2nZRcOeGUBbKraTaGsnxFZlfgsNEOIceF7OK/TvKEothJiKkw8oIyQnbDiMHmLCoMsiMs4LM4P6XJEgsIg9SmKhwgVJ1tFoIQXrAuDHNaIfd3TTYQs0KMXy4S9sgCwqFLKiQUF6wKiYOICU1fu4Xhu4upaJoYU07Q6pZC61LltCWDwg1YGVaFkUErKITItFfIZwh3vrvx+MCJmaoS2reok4XqQHmhPZkUKCQcd4s6haRr2COMH7hc6J+19xF2d0M6D59mqs8qhb4JOP0//9Ct7yDsWiVvqbGK7yA01/xHISUBMd+0emEa8dbCBOJiw3sK/wDFU7EpcrX7/QAAAABJRU5ErkJggg==",
                         3549, [313.68713, 263.47041, 219.44158, 188.5957], [0.57175, 0.59136, 0.68278, 0.70627],
                         14375884)
            elif (record == "SRR3724782"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724782", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACPElEQVRoge2YS3bDIAxFGbhalwfZQjvWSPtfQv0hNvolQI0TUr9JDliW3jUgJwnh0qVLl07Q1/f766f2xlc/3GxBQewwhiGEsZWVRqKC2HEItxmzL5UQTis4hHFs5KSVigjnXXq7tbLSSCWEQ+jwHAJhfvC0fLexe8KiXduDgARSyZp2oYuwf12E/es/Et7HeLaVA4TGnE/Y44vR8uwRInRIaHr2CIk6PJAW4QR4FiEcm8+yl0uIcf5YR5VN2r1JpQP7Z8SZhCJh3t8nXjfQMFP+1xKqSnHXPgH1CJW9OT9vKmTXPZ8Q1RSz47jwCOPs/PEKQmRjXAql3cHoFNweJvPK96I1Yn5UsLVMHWn4+btIES5DSs+OPkd83+1rDMq4Q6gDTyOMldOzYxStJ4zXbULiFwBL/jV2BB5hUkeGBLkZgSA5XY8I6f5CdwhpvRDDCQ9YzjWhqBMYIWlCkPdA9KKMk0kIrQmTzmETYjpNMkRu7cSUNA6ScJlYQe2exAirj2RCqOyvBaRpUYrfRCI4CS0npN2Rsc65SkwwA7vb+IE5hGmKuPZbg1CECqMJITj2lAUkHSEIwSTkXaqGEIPcKeWEyNJagGshaQc4IcIeuh1J3qVqCLdnizWESwKwCCWgsgPL9zV4QmgQVRCaQfWEfOQTLt8x04lWhDxvBSEKQuIjn9CdOJiQwI56KGAcH0gIlDTh9yd0oh7pHs5qfgwhbf1B1OyAEHMAwb3xInwDwpxtagF2RIh1gB0RasRf2CPZDmLbE0EAAAAASUVORK5CYII=",
                         2848, [291.83641, 245.11767, 204.15578, 175.45856], [0.58058, 0.55927, 0.64483, 0.69077],
                         12400117)
            elif (record == "SRR3724786"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724786", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACpUlEQVRoge3YS5qDIAwAYBZOzuWiV5h9Vrn/EcZaA0lA5KUd+zWrQjHkV0Rb577xjW9844L4+b1fUOnAd5/c4gDTJswMnt3DPR4nVnNGkG3j/thpnp7Km0WN0M3T5B7zecXEgf0pjoVixDzNs5v6Jy0P7E9hRQdCN8+XCu0FaElhciSEfsS07DPLzdg/aXlkb5qigBrhG+IMYWhj1HN9nCLknIjc0ztJR/RPnhByBxL32LeC1rkaDlHl1V1QSKVwqxD5E4/oXypyyqpDOoSUSuH+ubBqyWaEtH3xgo0TNtxSqryo1qLpKCfU1O5oSEM9QoxTbB1BiG6gEAYIaxb6kZBo+zRKCA1pyApFK5EMlCXcZOmk/1CoWpBIpoRwU6FPQRivWDJCcBkhDhcWplFjEkJ29QmRL+FgYclWqKZKCCk0oqqs8DmiQEhjhBAJ16RgroSeiuRBJIVxOiffqZ2C2FFr1zlClO21ofZ/sPdqLBSvIXnhVn/iTLyygBYO+HWxK0Qz5vUJQzG6ZikUhzp7fg6EdIVwbVF4iocp/b4vOlJCXZfGlAqxSyifT/askxeKvaNaqN/LwwS8CPeFPnZWfFnYFxK7ipRQXRZYL62YG/z3e0Lx7bLIWZio3gqjU9UolAVEQn5wSeEyVgr91qCFLOIHeL0QbGUVAbFQ3yeOd2rxfGoTEuj2dcJwXFKIeaHsOBCaNo/GYmHTMgUrEm3Y6uHCQo17QmUYKNQTtwvtmTIn0E609vcIM7UPEYa9fkeYkMVC1VEnzNU+QAgUC3UFDUJtOEOI5UI6FGaAtxPi9nNIp8kA7yAECn9hLZukMX2K0L+yf6SQk6oDP0+I9xOWPS4AvZBn+SzhMzM/mu8nLCAmD7uXMKfcO6xWqAVxx4nCMPyVxv0BDgnA/3SLiKoAAAAASUVORK5CYII=",
                         2758, [239.45946, 201.1255, 167.51519, 143.96837], [0.578, 0.4996, 0.57892, 0.64871], 14634825)
            elif (record == "SRR3724787"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724787", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACjklEQVRoge3XTZqzIAwAYBdOzuVirjD7bL7c/whfrfwkISACZaZ9zGaqEpO3iHSW5Y477rhjQnz9vDj+vbpAIeZ8hTSnTIht/d6WbWbFAUK4MHbdduTaX5QHFq9OFj6mb13ahWa3QMUOCFurlcvmokdIZikAKnaQF2YvpIVVyVLmvgibhSi7PQqdCCErLPapCuvMfOr6vb9mttpb60KiFPya8NFIbeq1IJLCQ0ZKqLp5ibC8LtojFe6HSqj7zs9w9Sso+ZKGCvmtMkJZTxennD8/uTosYW1uxc3556yQ+MmkG56D7EJtl5Zw2CTWClGdFN3wHAwL9XHB2EetrbUk7JbyfrXQ1RFCPSYREvj3oD0R5o5rPBdBiHr0xVAP4HVhskr9JIMpBEOYbkchVe/QDTFfmHacDuTC3sdUC9Wr9aoQlBDjugM3QGRbZdlNYRcmCZcCqoVHRTwXkhL60e4H0p8Vup838SMfROJACcnfHNkf3YMhxGNbHCkE3f0QIUmhfgSWghCYUCf1COO9jkNgbXOhe/zKQgrbkSmkGqH7cTxMqI6fv0p922JEIoQToX8KMKbTnpURkijX/EqtEPpoEyIToiEEygqRl2tejqGfnDAGBoADxUdsirBxEo9+MN52tJCYcB8nhFAnRPXOHyQEOBWSEoqXkinkx/hc4s8dzxaGNwD1ComvKKOjWEcLqUvozvwhIWIixA5hBFQKcbAwAep2uoXpLUcKpUOZmoXC0C9kF29hEiAdHUJ+4oXCmDdZmDlxCycIfYKoeQt/TwjWmEIAhn8I3kRojimE/06ye/wHCF2CqvkpQjBS30RYSXxnYR3RSvwoIViJnyQ0ge8jPNn1Cct544QkDkcK01n8D4etqmWde7k3AAAAAElFTkSuQmCC",
                         3417, [258.29332, 216.94434, 180.69053, 155.29171], [0.59912, 0.57552, 0.66211, 0.70524],
                         16809588)
            elif (record == "SRR3724798"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724798", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACOklEQVRoge3YQZaDIAwAUBadnMtFrzCzzir3P8JAFUgwCFQdYWreG18VDPmC1o4xd9xxxx1/EF/f/cfPuydefXGrAxr6PibzcJuxghr6Tg8zTXYzVrQIjROawYTQJJyccDqplJMCCOs729kbb5E2CZ9Pi7SboaJJOGSshP9OfAvHD/oAYfKF+AHCpleA/gNuoWl8c+0uNGEq6lNY+6uvStglsfxEfF0DB+xbmJuqirdNmvtpQkyPFJOdF7mxK4oqCjEeKSY7L8TYbkLncmGf0B1BwJjswmXKx7a/1uFAoU3RgRCk0F73WZYK7XzYP/EPi/lOzQpdQ0x2iFC/6rD91E+ExIRy/dp+tvV9oVZba+gXiqJQGyQVpkVRbCEpXGSbwiXJQcLMUiAIubVBhJCk0LUslTUL8SShkoaNn2kGvuOT6EI+wraQwinGk3dHXojh46qdQn3ggUIIqdDvoyE2VUpSPFwIaRpANMKtLeP3hcsRlkEmDbFPyJ6TK2G8BdjTYkvoFVGIHQhjbkqHYkIIRV8iBKVPbbATFaGrZikrXknfB1NhuHGikMKtuxKG3aIQ16XVxzwrrFaWB1hyhgXfheaXUCYUhuOEBDuFCFVC9pk1Q0GIRaFW/YFCWguTVcsCRY+1UBpA7F0q9GMmgyUlqEIy6YFThGqfsi0rxJxQDgX5AycJsQkIc9K8cAN4lbBpEpf+oAlJ7nUkxHahOLN/YcMkJumHEWK1UD1xAGHNJL4SjyvEkm/zvDGFv5FwzjKcEK+2AAAAAElFTkSuQmCC",
                         2663, [206.56552, 173.4974, 144.50406, 124.1918], [0.56415, 0.50344, 0.58536, 0.65409],
                         16380932)
            elif (record == "SRR3724806"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724806", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACgklEQVRoge2YS3aDMAxFGaRaF4NuoR1rpP0voQnFsq0PWCSGkMMbNUKfdzEYyjBcunTp0g76+nl//W4tPPrkNgsCubdxuHUz0k2A7bnjbRjHXka6ibA9d/w+ISFECG9nXMMQ4bA/IXkHsLWDIlyqfGqnAel2aRLLI2zfPoBED/ekPSs9CRuqfMKW6u1zt+g+Cf2fnrwk++6yYocTVs9jPTtECNaK70dIDmERNG4uaS/Hde77EU6TAaGIGVXlLwDOJHUjwgGE1Zp4hIUB7VDYo9TRJMRGwhduptVEQUgbCCEVTX+hzj2UUHoqCOcsNGZHCMkmVNGehGJJmRCnCGozYUIZG/YjnMy5hNMGQvoyA1A18w5sLFiQ0EiNq3hoLRNSigiLdQ0oQpDJ2rY+bf9Zkf8afa0RYoq/ghCPIeTmRIZbZEI0Uga5LKQJ80E0TlDKrCOJ8BWMJAlzz7SmJAlRNFggrDZfo5oHWa6cp2dQxZqQcJCuuBcRciNpAXRwJjSS4woQgksoLoOSENPB+w1fD6jnHEEIihAhTPjAwsxRlOdbzCYE+4kaFhSOBSH/zNbkKjcQ0grh/U5zCLEboVpSkkLZYH6JiROST0jUm5AdZWuHEkY+i6tWc5tmQn4Nf4qQ5pH1dV7ampITYkdCQ9li+Q4AGCTEHFsl3Hy9PkfITDNhqmkjrCa4hGzuCELk7bU7IWwgfBTMj7ythDLQg7BoFgS8X2PEU2tC6aiZUJtaJNQtbUIc3I8DS5qKT0FIvOmGVPe3CBcA9yYk9+OAA/d41tYdBNP7EUKIkM/JiQiLunUBn5PzEMLHE5o5rqYZH08odRGeihCs0pMQrm42jxQT8NSEf8d2EDbU3OmEAAAAAElFTkSuQmCC",
                         1590, [125.1826, 105.1427, 87.57218, 75.26257], [0.57936, 0.5918, 0.68108, 0.7099], 16139067)
            elif (record == "SRR3724814"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3724814", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACZ0lEQVRoge3YSWLrIAwAUC9SncuLXqF/rZXuf4RfG5AQswdinFqbJEQgPReTNNP0xBNPPPGG+PoZP/7tnXj1xW0OqmagPJ2n1/Sau/XSJ+pCyfjFzfPcsZku0SAEfroK547d9AjCaoZchEX4/erZzvkBWSGPB8L57kK3JYHHRfj6vuFJEwmJ3+CR+q06chSE7o1LhVjNqAWE/TuYLzxeZnccv7pZIQn1Dwgv3KbHS0ftjybEwytEQnKPdu1LhfHHdfi6vkJGCEq4ddnTIrqJNm/brHBhsfXThGge/oQQXQruaq9SumXR+Aw4U0jXC6P2wB6ugJDKR52bXMIK4W3CZKecEwmpXSg3mU4yA1aIUzeh/RwAKO07CtpDkMue6AlUMtnEkpCfJlY7GvYMoarQr02+MJ63R4jnCYONZXv1GkgU2SxUyTYxISQRUlxlbwCqUiRCNDiKNx9xf8AvkRtXqcsdpabDeg3GEJLZXcSDqhkRQkGI5E9fTjEQyJuEVBXifqG5lXwhmowGIVFYdrdP7yFPuFT8PSYxakcJbaoIST5qjNgTWkBOiB2EwTqmMnLba08lISaEqIVSYYvQZe4K72sLBeuYysRtU0oIu4Xcd0ZIJwnX/Y4lITdmdvFWofoXLyVMdU+69BEhrNdKCb2fKE2HcTgQT8oLPdFWYbrs6cJ8qYTQ9dwmLHT/HiGkywiIIqEyDCKkg0JQA6MKKRBis5D/agMKQX7riYSkX+WF2YFBhChLfaKQ7ihsJa570uarmuMLG4n8rR3vJ8QGH5AI+Sj8KGFh4iMcQGh/Ri0BITvvHkJ3PErqf/fna0Vxjy0PAAAAAElFTkSuQmCC",
                         1620, [137.75588, 115.70318, 96.36789, 82.82191], [0.57174, 0.48298, 0.5656, 0.62879],
                         14942736)
            elif (record == "SRR3725446"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3725446", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACJElEQVRoge3YTZaDIAwAYBZMzuXCK8w+m8n9jzBaLSYkKhWw0po3r2+kAvnkR61zd9xxxx0nxM/vpeKvaGvvvrhGAOa24Dvfd31fIJc6kS/svB8+fX4qlQIou4lhDIeP/FQqRQGhH31dfiqVIl84ztLuupO0gNB3rr/wMiwxSy8et7D9uIWtByARWuXRcbuXAehbhXGheVITsSqMBq1dIdlCaFWo80wWXnghsvc/sIUGsV2hSvQThETBuC3kL/utCkkJwRCCM4WPb9GdFDu/rfDshlzD8ksQwlR7VZj/q05aiAmlv46EwZUgpMcfrArtu2f54E/LoIksC2AGUEIiJRwqGCe6qWDt+aB4gBDqPYClxw2g9k0pHGuNQny/kPVj9Qk5wvHwUkLrfpYsBCWcSmwhVhEa24gTOwYZxE2hmN+xEE8XjmsiOn6mPestYcgP5CjtCpFYOKPNGkI1rTB0F/6Nel1GwBRi2JoOCos+3cTZL3Nl6I/CujG2jylntISL6JCw6DCCIRTbwa5QGHaFIrQQo+4KDObcHIoCx650GKMXhIYoUbiM8Xx+Bm1+KlOdURSozpBCacgWsgrIb1nFhBDlsHJRTxDSPDuO4R4rTQrNDHQ6wPehukI6IAxvZ2OHZAk3gAsIXVRQScgrJsazTdOULqRThS8RSwntglrC1Hn6vPJLSx8m5D21JsQUIOspyuFThOsVGxCmEDfqpQul4EyhXor/FUqqcXLh2YAAAAAASUVORK5CYII=",
                         4527, [369.72904, 310.54082, 258.646, 222.28934], [0.55488, 0.54601, 0.63004, 0.67982],
                         15557944)
            elif (record == "SRR3725458"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3725458", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACNElEQVRoge2XN3LEMAxFVdA4l4q9gns0xv2PYAUmgFBakRKp0R8XZsR/DKC26169evXqAv38VqW/rLPdvbiKAM/OYPrOdJ9PBi9ldJ6wH/i6/ryTUgI6PYUxA2N/3kohZSDszWc8qLXqPKEZ//onEw5JxozpplZlOKWV6yVsXzohXG2jmGAgRLX+KQKk9glxrXGRENfLVQnXGmmBUFaqnSpRnElSn0SPIlSSSqOELP8TRf9i0nWUNoWobIZQwgAtbGLthBgXyOfBdL9iQuD1Ysq6vnxiQgh7BAkhUkzIR4kpKyecK1JCaoMQEEWFJKT9hORHdaJnLrtfSLtcrDUP4dQJ7/iag0sJ9dczv0AgoGiNH3lBGHclhRBdC484V0ASq5SGm+YDpYT0JSGFK1wBoXeQ2ObHllYIQSMkN4xHvI/QehRmQsUxwrEwHtb0bl9H6MwMAed7s0YICiH5S+wBBSEpKakU4bScbEbrboo03kXn0gHtIMRAJAntJ86VhCSfWhvAOiXkhFiUkHISxrshbg52IQc6S4cI6TRhhlc/ytkc0UZeIqRg3CJDPMUmIdMSYYZtBP9LdZOQ25kXphwh7088QxwBDDGTYFPB204JwzpbQuYpGyHZmsNg+whV+ZHICDlDVsK0y5a4K06IYRXqICR7Oo4AggsUx/yC0OfDsoRqn21Cd7wTQuKlVUK94nbCsOksZvWEu9+N0B/YyPoJd+4ipAOfRagAtkOIOwBXBjZAqCD+A98rpy+M3GTIAAAAAElFTkSuQmCC",
                         3101, [261.80988, 219.89795, 183.15056, 157.40594], [0.54509, 0.5453, 0.62856, 0.67127],
                         15050156)
            elif (record == "SRR3725471"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3725471", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACY0lEQVRoge3YS3qEIAwAYBc253LRK3SfTXP/I1RHgSREEcUH1izmcxBDflF0pmneeOONN06Ir59bxW/RbFefXCtwb4K2a76Hj7sG0N4MXds2XdeWKOaQ2C8ciN2j57AZpvDRczjgni2800oDVtv+q/RGAWi0/QOh0VhXYNi0MA8QsqvwmUJ2n5kYW2itSXeNlJCqFxJB2DQ0tvDmC6wob1kI2DemUlwcxvWkheg3Iw2QObHR9XzlVQvx4KK8IABDSCuFVy64xjsJL2dgIfrNBSE/U6A7ni2UxUR7eXkfArn2RSHOpPj0w+bUkMXowXl5QMFQlVBOEuq924UQpxj7qTGOjjBvhMtC0kLRF0ELKU4x5SlR9/oIBbDbjFWzUoh8rxAaOQuVngi3wpQRTlewF1LjJHCWMPo55xogVBULxe22QQi2UNdSJPpXKnOcYLCEtChkfQ3hlNkSfhpwt0kG+Ie1Hwd92QihSNXJ+z0Cg4ivJpFw7AFzQkDrX4JNNHRp5SwKYW+US8VqoRNp4ZTOeqyMvUCPVUAoM05fXWFJIW4Soi2ko4TqxmFCciWRmmiSd6kUIqSEdIKQ5oXES/Ph9g+nJiWkpDA6aWNS5K/xO4FC6DPCNHIMDCDkK2au0DhpXDhOLpaYRSn0GcsIDVGWsMB1Cloo319UIUpIFQhZEjmYSYuEeKRQ9M8N4D/ElVB+u17oTnme0B1nmnKEuuEwYdaf5RT+BtsrtBsKCz9PJcj4veHOfBjl7sL+EMoQ+getf8mqQMiPTAUbqR6h3WsmrAOrEeJG4KOEsHDgeiHqVGcJDeIfwwX9pz7oT1YAAAAASUVORK5CYII=",
                         5530, [455.93437, 382.94594, 318.95142, 274.11791], [0.55721, 0.58085, 0.66513, 0.70248],
                         15411612)
            elif (record == "SRR3725482"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3725482", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACRklEQVRoge3XSXaDMAwAUC+ozsWiV2jXWun+R2ggHjQxmASCKdr04UHWB2zSEO644447Doivn/PH79aJn765q4MqxnZ9+A6h36uUnaJG2Hfdg9ntVss+oYXlGu3ggdiaEIwQUw8GE13X9+0JUTbMCQfdtYVNnjRVwiYDSG3ELNT0VuM/Cil14OHF7BK3sK1Ap80RovjbUrjHP00I0XQ0EJ4QpoRE5yBW1WB+gobmhDg3FHCtkGL7KXairAH9Qc+wltj4ISGsGybK854R790uXFlNVWwRzu8b+0wed8QX4i5CtQ4grsgNSgj5RbXnphaO+3Kd8C0ff/2GpewVwscFIMnpIqNsHG2HClGslNLzZ2G1pITEhHp0hZAOFVKp1AiHIlh3KQpIpYu9qCYvCdOL9Aahtz4GcQCC3VvlqwzpKgu9wsUSVcLXv/1TwmfzmJ/sF1sIcVYoKs6TkczAI4WUDZQrssVkIWkhmqG5YjxeSGqp9BCiEL2HIIRohcQ3rhHGfAtCel0Y9xaxh1Uq5IVtECIrzAgL0BGiEBJs/f023isuLP9eR3C50SiFz2lcmIa6wvg6MiEDekdSTieXqQxYFpaQJQb223FaSGwfqevSsiCknPmtwnThCPPGyG9SFArD68LcmTNXycq6WiivvJgQSsOi0KaUQhabhJRTBW06n9AfNRvcgduF6SW+sNBv2E2Iq4GQRvOJlxOWs/6KwpRUTLyOMJ0PeFHhkPn5eUEAMbEB4arDFJx57QhxG7Ah4bLRBTYl1IP/AE5ATLP9pDkiAAAAAElFTkSuQmCC",
                         5401, [471.25784, 395.81635, 329.67104, 283.33072], [0.5875, 0.56147, 0.64195, 0.69871],
                         14562665)
            elif (record == "SRR3725493"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3725493", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACTUlEQVRoge3XQbKDIAwAUBb+nIuFV/j7bH7uf4SPChggUBW06JiZzlhFyGsQrFJvvPHGGxfEz29X8de0t2//uFJQbQfjqEY16AapnBTVQq0GpXWDTE4KqK+hHgbdMbFeOJdwHBrkck7UC7XBaf1koVlkul5pGszSrgPw+UIShXB1IqcFkCx8TmEnIQrnnyMkWQjxSaHNTWKrUCx0JwFYupoVRtPUN+pwCWoqxKS4HQTPFYWrjxIK6e0TTrun0Pr64NmZXGE9xqjltFkIGyLkhJm9pX18eNx5FpMQ/THGLUksYvoesHzvVei/JukRF7IlqX8h8WNy8xSSGZkRQgfC4ksVBIvLatgiBMMTGtryf0eY7nc1QlNvulYo9heMn9aTC2m3kDJCUqcIzQYU5o52ODcO3FwY97gKXQLzHpxmg+w4LyRZiEVhU2LSoR2YJcBT5HctR4IQo4ZMSOyUIPSXG+mklFx1ysI1C/AZI+vOTetVs1OIqlkkQ7FxcNkUy0KUhKtotzAYrep/lN0BkvSDuWKeFy9oI0T/ZIpC11utcNJlhPMICu1p+ykKA8OSIBSEDCgIw+Yf/ngWYq4SF647g61dTgjL61lwIhVStZDN6oNCcq/O0WC+Bmn468jXu73CtMuyEI8CfR/RYBLtIUIxgy8KzQ1mUdordH1WCt2zdK6QllV6u9C+zrNhQiGF3zoQ2mE2C+0CyXo6LpRPNBdKbUpA/5O4UW4ixG1A8EL/CnIX4cYignDnXYTbiNKNjxKCdONthHgQeB+h7Zk3/QeUXhB8QgtvegAAAABJRU5ErkJggg==",
                         8497, [540.03614, 453.58425, 377.78528, 324.68177], [0.57149, 0.57826, 0.66307, 0.70013],
                         19992544)
            elif (record == "SRR3725503"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3725503", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACXklEQVRoge3XS3qEIAwAYBc253IxV2jXWeX+RygzgoSQ4SHSgc6kX78q8sgPinZZPvGJT3ziD+Lre/z4Odvw1ZNbHFRRd93W27ZuvVLpFDXCbTW/W69MekWNcNmWdT6iFBImKq/m57Z2zKZDQI3Q3KXb41adKUCKUkKzyWzLbDtNlXDKiIVVW88E8Q5CIRpMiM09KMKjU2jvvjna5zshxBE2nTcQYnMPsdAVeCG0jnI+ugrJLSe8ThjeYoCAWN9DLMTjkjuq7fayCIVkhPt5+SY4ldCcgH10GoV0XEJ7VNzf1REJbU5A+Zw8Q5RzoTvK9tYrmoS4cIUvdyU0gpCEkGqEBOXCjl9y6X2auCQvDMoedf9SaLZ6vTjViOe3A1PC8N/5nDCcsFz6+TC3utqLz0q5zPYCO+U+pai6mUKK2maFZEuwSqOFFNq1Az99yiCUEoaJo1S/QBj2Yrcvn4C2LMXC+5eAyDMpNPXQCfEioezFPkmhEOPNIi30688ulgltdwSW2goEKSQppCjHQOimnAnxeI+BItzbKsmTp+9tIB74RBx3BC/ww3mh3A6TQv6FKYiUFiJrAvHAp4Vss+FCPI78ikbCwAAuf10IfsACoTK1VYFMSLrwPmBYA/a/p4UMoAspqNAkBFUIsJ/EM3kIMS+kEYVBRgtGw7DP/mOlFMMowvs3hipUYNcKQ4AmfDJwLfC+TQpTuRBbhIncnw2M54QoV+1fCXnDU0JRMI4wdJwW0tBCvEKIowqB2MusRagXDCB0nf5ToXt6UDScQFjwQgS13TxCzAGT7WYRQlD9F+z5MLM35weJAAAAAElFTkSuQmCC",
                         5497, [420.80719, 353.44212, 294.37801, 252.99867], [0.57133, 0.50687, 0.58447, 0.66234],
                         16598462)
            elif (record == "SRR3725527"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3725527", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACUUlEQVRoge3YOXaEMAwAUAqic1HMFdKrie5/hLDZSLYQi5cBHkrDeNUfY8Okad544403KsTP76XiL+to3/5ytcDkEbr207Vd8jClAjB1hAHXdcmJFAug5CG6pr0yMZPw02bIpUxkEfZ/dxeCUdd+hlXs8qRTIHRhKCIsn0mZAHy8kHRhKLqvkJ4gRKtyRQgUlF5ZaL+zEIWWqVMkTH+mFAv7aTAIUev0Ci8U/Wlp1D5EiP4ao8rdQpwrcuaWJxgBIsxRIV5wLSGrUD95SweataNhTivG8NqgXBZMXeErQmVncAgthjg/ohWh0hIbeUOUDa7aJcSpZZg4sdqwIizApopwPgxtobjFsgmpqStc5lGPD369KgQUwnFs8L3kmLWE4HeUnwfzCo0d21QSulyXkmhSLiRLSJcQilcuiA5tbSORJUS/cT2Qv670XUnZsPN7QwEhNmKmeWZKFE7NNSGMvxd1IRURBiPuEoo0FCHZQtoS5jROOeAyIhPiqpB8fnBQiHNfU5h1FUUCgZB4k1Uh8CGmD5ZwKdKFymwlhX06LqUjQjSEDGgI3UmVZEMulOeGN9C20C8KE9JpoRwtTQiqEIQQ+ZyuxTA5E0pDqjCoA3ZAHAqKhXMGLqUlNX/pgP5WOiWMFYaQTm/Ivr87kGUGEStKZ7yCCsJzj0aRVWDSJonTgdrCQ7+GYW4PfM4zQqwjRK2RGa55slAvyC0EtdGmEFE+vy4slD23w53TGPS8vnDvIq59N08RgtLxNkLcI1zveAPh9iJqj+8TQimoKaTo/0T/cbr9AWs8azcAAAAASUVORK5CYII=",
                         2423, [177.43177, 149.02754, 124.12338, 106.67594], [0.55216, 0.55547, 0.63824, 0.68238],
                         17351910)
            elif (record == "SRR3725516"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3725516", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACbklEQVRoge3YS4KDIAwAUBadnMtFrzD7rHL/IwyK/EKgxEornWY2FQHzEMHRmG984xvfeEH8/F4/6GjDdw9ud5Ci7m0xN3O/D8tlTGiEy80syzIqk1GhEZpVeF8GZTIoQCVcrNAyp4pCiI3K1mZn6XRCzAv4cRp2kbmty81UoRJOGf9ByB7EmYWAUuFHCaWN4eOFFsiFqg3yWjGlEDWVe4WqTkcHaipPKVTMqNWCRaEk3AvEpfflkWUH6W/kVWUh9QgBzLsifyFJVMWbilqIybZxHSFVTmxB/cK1BG0XFGoVDc+L9ujl2zVRuItlTiQIqS6ETYi13k4MnTBkYnNCXlMppLOFFUpbSFy4H5fPHMlCqgrT+qcIax8Tmkt2vtQnSZW3xgnzsnUeykI8Xwi1TpqfUahbiCTcRIXw+Tc5qL1JNIcvSw+0QiDpxu4T93RheSETUs2S8j9Cq5BzauDCgHG1t6lPLSEOEebvJ6739DL2Lzmg7CwIQnwgDCGk4vkhieO0fSVpCfdyO65xLruLx7N6YShqCsmXoDkaqTDtZe89ZuBnzpuEB28iPBK66yC4giiEUuhTyoTJLVcK05NSrT6fzdnnIAv98ugf/IYw1IhCCgtxbB2EDNESwjNCqgnd7YqJsXRgByTCzOBHpiYkhdCP3QEhcSHfvYGEOEdYdjlKSJkQM6Ac8TwCKxgiDGOHRh2CMP5D1iPkBVwoiPRC1vRJYfh+UAdy0EWFqSoXihlMJ4RkH+VCyo8mFW6dshw+RQhrPVd9PmHXdrHVc1di15xBiH3ASrvPEEKj3QzCx9NUbqYV5oKXCt0iknwb+wPNFDFNf6VPiwAAAABJRU5ErkJggg==",
                         2995, [200.00702, 167.98882, 139.91602, 120.24868], [0.586, 0.56124, 0.64449, 0.70134],
                         19027286)
            elif (record == "SRR3725538"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3725538", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACcUlEQVRoge2XTZqkIAyGWTg5FwuvML3OKvc/wkiDmPBnUOlWp75FPQWE5HsBKcuYjz766KMf0J+/99fX0Ym/vbhqUUfsPJvZTHaUlUFKCQnrsdZMxtpppJ0B6iGcraO048yMEPQQLls4uY9HqYtwOaDWPO2UQkrUIpzsNNun3TRdhI/U/0CYPIhp+/EqEOKvGBmmFuE7dpPqhHiH3cTTGQqEa8ctCKU7PJKhTniLJ1K4A+xPALcn5PaOGCoSYhw6kPFicXvZb7dGdyeEKqH2xBYJKQ4ps5wRtEclIWtovZGKsO3ilIjnzutwKFwaW8Q+IYUECsJD518p5hmwSOg7wYUuDdwGdlO7SXuE6zc051V+cDbPhqhIGDx4Z9FJbjxP7Uq2CGn9RtcQUmGL5EtigZDOELpoHeF+MoXyO22tIhzJxYSckBKbzYJNQriAUNwiSZZwMNh19l1HEhIj9IZCeMF4Vvw7REGIimT1IrIgd+9bLPlKEIajmUCIowjhDCE1CV2zRgjb8akT8nRhVgchRkIqJtMI2LzMkq8TuqlASD2Ei010IbyrRYjur5PXSUJ+jRQIV9ORhhOiJFzHOWHcNN/mK+rjWQZRmeKCkljZs4T8pYsTbjRdhBQJgTLCde0qhPFIcAtXEoJYvhohyI6ckP9L4D7jme4gPLKJfpmREaIkZAsIRwhxl7Dk3fcNIkzvTc6YEdIuIdUJG94vJiQtoSzkCdOOexKSJJStNmG5Q0XY8t4srBPwN9uU6RWE9ExC7CLErcwLCSEkfT+hmPgqwhAOYuJLCAFctuLEBxAqLlMoznsOIR7i6yfENNmPEeab+A9AiDxxtYSwlAAAAABJRU5ErkJggg==",
                         7781, [590.16889, 495.69148, 412.85593, 354.8227], [0.58348, 0.52052, 0.59997, 0.67322],
                         16752683)
            elif (record == "SRR3725561"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3725561", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACVElEQVRoge3XS2KEIAwAUBc25/IS7Tqr3P8I7YxACP+PMGrNToSYxwA6y/LEE088MSG+vs8fP60DPz25xUEVfddtWZdlG1XKoHCFhPG+27ps27qOLGdA1Aj/fr67C6/4G8LtVym4opTwkicNkPMjJlfp/Kg56sPhC/tzHhlDhdid/IDoX1L/UqhyQnfuI2KssDt5f3jlpQMDbeQLVQPgCc6cOmFw2cWFhCd4cUhhbuN4ny97hojwdSeTcEJIYa6gcwohfXeMEPWdoUS15OqE6XVaJ6RZwuQzRHnvZaXm3/ueDlnCrbS3kC1Mz3Nb6BJD8+5Vo4dkhcHGWUKSadT6o6SQ6wNVE5o9hKHOwcagEHaheXEUKpLFyverqjG9FcgWojXrr9Fy3nEJbqsPCqlaSI6Q/K4iF6mOBcK6D4tIuDuehfIsQadTVCjTofhJ9sGvU2yy0K7e2u/RPhkh8s4GtO+aZFQmhEOE++NRXPPjCoRgG/YL/n+sb+oDGuuE7nMrAvT3vnq8LIkrRU9IjhADQjTF+0J1GREijzAtTT4i/Ubfs0FCCI4Q80IWkXNthJwhLoRmIZAr5DesnVzPtl0O8Fu5R0icQQjJEzZtxLhQJ9fnA+n1ZEDWPKuaRYackLglLDSPo9AxXBrvYdKk8pAfKDr4Qmk4UAgtQmAHlgplh+FCq0ODEISjWUg9Qj+lI4w8eK4Q3YYzCfHeQt29VxhuGCbER2gCdPfbCnV3uL1QDLyAsPCo0Scgf49dR4gFPoiOu4swPu4KwvwyhcS4ciG6qeYJva6/0UKPXypXknYAAAAASUVORK5CYII=",
                         4808, [403.32355, 338.75735, 282.14723, 242.48712], [0.59322, 0.55156, 0.63463, 0.69544],
                         15147332)
            elif (record == "SRR3725550"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR3725550", "Klepikova_Stress",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMBlzGawS1VhAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACiElEQVRoge2XTYKDIAyFWXRyLhe9wsw6q9z/CGNRfhICBZSOOmZVIDzeBxGtMXfccccdH4iv7+PHT+/Ev97c6qCG3Mdknub5HOZlTLQQTo+HmcxjmJcxIQkBC8kWbxpnZkSAJCQsZFu+aZybEdFEaKv0bEUKkqhEaG+aSxOeMoBEmQZCbLlmjxtHJ8TNCkXC7fKbY/suFwjpAITJVd8jIQkpjOBm+a2RXIQ9EgcnZPawQ4JSQvTiOyNCxxRmr/hFmYs8Ie1O2PFMfYgQOjY/DeCEzm1ZmxNKr1XLVhHu8mIE7CAkQdi+1xoh+RFPiM3Cy8R4HglCJ+57tEWYvdlSe52qhOhGljHoJhT2mIzfPvQJmkB8bFxC86T0qYTkRpZf/TdOLJ4S2iaBQ8gRZiRUT4rEUEKoIfQ5WqUEwnkbMJZQ60rbpCwhklMHSnIqg4nLl09COLeTe4QRElGcLTyhUQkV9yMJ+b1om8wzyCepSMhN0fxE84MNpagSBrl9CNeiR9Y28dHaDmlbIUTdOKVV8pqUJYS9CYmdACe0VmzRgHjkY0JnKRDyVFQIqYqQErEWQlzfBoIQuPqrxGIAmWVsCZYIUc5Ge6o5Qow3rJ+Q8oRrY7U9/9d2C/rnLCF044zQ7xjfoHlRWtgyhNGC6ebsQbjK+17y/v0XFQAnDKkRu9CLCNkKCiH5KcBmbidEnTAKn4BGdGiEqI0GQqwnbLpr1uxFQCPUyDoIKUsYfL8lzGQVA2JCwdRA6Ex0ERa8FxfeTki8VSTUO45ASP+BEC9NCOtCcDJCbCKMPm0vSOhEL08IbOL1CPF8hHVXTVhZeLgIofIpdCZCfAuo8Z2J8N0hluedgtDeHnHqL1szosl5b+TlAAAAAElFTkSuQmCC",
                         5536, [417.14362, 350.36503, 291.81514, 250.79605], [0.60439, 0.54508, 0.62868, 0.69034],
                         16863035)
            elif (record == "SRR847501"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR847501", "Pollen_Loraine_Lab",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/AACDUTRoAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAe0lEQVRoge3RwQ2AMAzF0B7KXjmwAiuw/whIsEGUtFjyG+BXbsaQpAWOa5P71fvG3q/9Cut3o34yqalwRvlkljfMivrJJAuT5lk+mdV1w/+wkM9CPgv5LOSzkM9CPgv5LOSzkM9CPgv5LOSzkM9CPgv5LOSzkM9CvjWFD/gntDRLwchVAAAAAElFTkSuQmCC",
                         1, [0.05265, 0.04422, 0.03683, 0.03166], [0.09074, 0.10234, 0.11727, 0.13273], 24133008)
            elif (record == "SRR847502"):
                dumpJSON(200, "AT2G24270", 1, 2, 10326917, 10330049, "SRR847502", "Pollen_Loraine_Lab",
                         "iVBORw0KGgoAAAANSUhEUgAAAcIAAAAyBAMAAAA908bbAAAAFVBMVEX/////AABkzGX//wAAAADAwMD/AACDUTRoAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAQUlEQVRoge3UQREAIAwDsD2GL0zg3woqxo5doqDtoxEAD6wzWPe4NXZ3gGqZ3Qmqafi/+Q3nPw0AAAAAAAAAQJsLgZBJsofrHUAAAAAASUVORK5CYII=",
                         0, [0, 0, 0, 0], [0, 0, 0, 0], 22714097)


# The main program
if __name__ == '__main__':
    main()
