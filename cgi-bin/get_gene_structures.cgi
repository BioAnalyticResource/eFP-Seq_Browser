#!/usr/bin/python3
import base64
import cgi
import json
import urllib.request
from PIL import Image, ImageDraw

print("Access-Control-Allow-Origin: *")
print("Content-Type: application/json\n")  # HTML is following

# ----- CONSTANTS -----
EXON_IMG_WIDTH = 450
EXON_IMG_HEIGHT = 8

# ----- VARIABLES -----
exon_and_CDS = {"start": [], "end": []}
mRNA = {"start": [], "end": []}

expression_score = []
variants = []
variant_count = 0

# ----- GET THE LOCUS OF INTEREST -----
gene_id = cgi.FieldStorage().getvalue("locus")

# ----- GETS MAPPING INFO FOR THE GENE ID -----
map_info = json.loads(
    urllib.request.urlopen(
        "https://bar.utoronto.ca/webservices/bar_araport/gene_structure_by_locus.php?locus="
        + gene_id
    ).read()
)

printout = ""
printout = printout + "{"
printout = printout + '"locus" : "' + gene_id + '", '
printout = (
    printout + '"locus_start" : "' + str(map_info["features"][0]["start"]) + '", '
)
printout = printout + '"locus_end" : "' + str(map_info["features"][0]["end"]) + '", '
printout = printout + '"splice_variants" : ['

# Get start/end of the LOCUS
start = int(map_info["features"][0]["start"])
end = int(map_info["features"][0]["end"])
strand = int(map_info["features"][0]["strand"])

i = 0
for subfeature in map_info["features"][0]["subfeatures"]:
    # Need a comma if it is not the first element
    if i == 0:
        printout = printout + "{"
    else:
        printout = printout + ", {"

    # To return a count of the number of variants returned by Araport
    variant_count = variant_count + 1

    # Extract variant
    variants.append(subfeature["subfeatures"])

    # Return all exons' coordinates
    printout = printout + '"exon_coordinates" : ['

    # Define the colours
    white = (255, 255, 255)
    black = (0, 0, 0)

    red = (220, 20, 60)
    orange = (255, 140, 0)
    blue = (0, 0, 255)
    # TO DO: Fix the green and dark green shades...
    green = (166, 220, 166)
    darkgreen = (0, 125, 0)

    # Generate gene structure image based on the information in map_info.
    # Create an image for gene structure
    exon_graph_image = Image.new("RGB", (EXON_IMG_WIDTH, EXON_IMG_HEIGHT), white)
    exongraph = ImageDraw.Draw(exon_graph_image)

    count = 0  # Need a comma if it is not the first element...
    for region in variants[i]:
        # We want to return regions marked as type = exons and type = CDS
        if region["type"] == "exon" or region["type"] == "CDS":
            exon_and_CDS["start"].append(int(region["start"]))
            exon_and_CDS["end"].append(int(region["end"]))
            if count == 0:
                printout = (
                    printout
                    + "{"
                    + '"exon_start" : '
                    + str(int(region["start"]))
                    + ', "exon_end" : '
                    + str(int(region["end"]))
                    + "}"
                )
            else:
                printout = (
                    printout
                    + ", {"
                    + '"exon_start" : '
                    + str(int(region["start"]))
                    + ', "exon_end" : '
                    + str(int(region["end"]))
                    + "}"
                )
            count = count + 1  # To add a comma only...
        # We want to graph all types of features in the gene structure image
        if region["type"] == "exon":
            exongraph.rectangle(
                (
                    (
                        int(
                            float(region["start"] - start)
                            / (end - start)
                            * EXON_IMG_WIDTH
                        ),
                        0,
                    ),
                    (
                        int(
                            float(region["end"] - start)
                            / (end - start)
                            * EXON_IMG_WIDTH
                        ),
                        EXON_IMG_HEIGHT,
                    ),
                ),
                darkgreen,
            )
        elif region["type"] == "CDS":
            exongraph.rectangle(
                (
                    (
                        int(
                            float(region["start"] - start)
                            / (end - start)
                            * EXON_IMG_WIDTH
                        ),
                        0,
                    ),
                    (
                        int(
                            float(region["end"] - start)
                            / (end - start)
                            * EXON_IMG_WIDTH
                        ),
                        EXON_IMG_HEIGHT,
                    ),
                ),
                darkgreen,
            )
        elif region["type"] == "five_prime_UTR":
            exongraph.rectangle(
                (
                    (
                        int(
                            float(region["start"] - start)
                            / (end - start)
                            * EXON_IMG_WIDTH
                        ),
                        0,
                    ),
                    (
                        int(
                            float(region["end"] - start)
                            / (end - start)
                            * EXON_IMG_WIDTH
                        ),
                        EXON_IMG_HEIGHT,
                    ),
                ),
                green,
            )
        elif region["type"] == "three_prime_UTR":
            exongraph.rectangle(
                (
                    (
                        int(
                            float(region["start"] - start)
                            / (end - start)
                            * EXON_IMG_WIDTH
                        ),
                        0,
                    ),
                    (
                        int(
                            float(region["end"] - start)
                            / (end - start)
                            * EXON_IMG_WIDTH
                        ),
                        EXON_IMG_HEIGHT,
                    ),
                ),
                green,
            )

    # Nucleotide padding
    nucleotidePadding = 100
    exongraph.rectangle(
        ((0, 0), ((EXON_IMG_WIDTH / nucleotidePadding), EXON_IMG_HEIGHT)), white
    )
    exongraph.rectangle(
        (
            ((EXON_IMG_WIDTH - (EXON_IMG_WIDTH / nucleotidePadding)), 0),
            (EXON_IMG_WIDTH, EXON_IMG_HEIGHT),
        ),
        white,
    )

    # Line in the middle
    exongraph.rectangle(
        ((0, EXON_IMG_HEIGHT / 2), (EXON_IMG_WIDTH, EXON_IMG_HEIGHT / 2)), black
    )

    # Insert appropriate arrows to indicate direction of the gene
    if strand == -1:
        exongraph.polygon(
            (
                (0, EXON_IMG_HEIGHT / 2),
                (3, EXON_IMG_HEIGHT - (EXON_IMG_HEIGHT - 1)),
                (3, EXON_IMG_HEIGHT - 1),
            ),
            black,
        )
    elif strand == +1:
        exongraph.polygon(
            (
                (EXON_IMG_WIDTH, EXON_IMG_HEIGHT / 2),
                (EXON_IMG_WIDTH - 3, EXON_IMG_HEIGHT - (EXON_IMG_HEIGHT - 1)),
                (EXON_IMG_WIDTH - 3, EXON_IMG_HEIGHT - 1),
            ),
            black,
        )

    f = open("get_exon_base64_exongraph.png", "wb")
    exon_graph_image.save(f)
    f.close()

    printout = (
        printout
        + "], "
        + '"start" : '
        + str(start)
        + ", "
        + '"end" : '
        + str(end)
        + ", "
        + '"gene_structure" : '
    )
    printout = printout + '"'

    with open("get_exon_base64_exongraph.png", "rb") as fl:
        printout = printout + base64.b64encode(fl.read()).decode("utf-8")
    printout = printout + '"'
    fl.close()

    i = i + 1
    printout = printout + "}"

printout = printout + "]" + ', "variant_count" : "' + str(variant_count) + '"' + "}"
print(printout.replace("\n", " "))
