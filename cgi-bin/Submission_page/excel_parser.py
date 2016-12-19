from webbrowser import open_new_tab
from webbrowser import get
import openpyxl

f = open('submission_parse.html','w')
wb = openpyxl.load_workbook('bulk_template.xlsx')
sheet = wb.get_sheet_by_name('Data sheet')
all_rows = tuple(sheet.rows)

# Store string to be written into html file after all content is read.
total_XML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<title> Submitting your RNA-Seq data for eFP-Seq Browser</title>
<meta name="description" content="Submiting your RNA-Seq data for eFP-Seq Browser" />
<meta name="keyboard" content="eFP, RNA-Seq" />
<meta name="author" content="Michelle Chen" />
<link rel="stylesheet" type="text/css" href="style.css" />
<link rel="stylesheet" href="https://code.getmdl.io/1.1.3/material.green-pink.min.css/">
<script src="processing-api.min.js"></script>
<script src="http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js"></script>
<script src="XMLgenerator-v2.js"></script>

<!--Bootstrap -->
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>

<!-- This script is to ask the user if they are sure if they want to close the submission system or not -->
<script>
window.onbeforeunload = function() { return "You are about to the submission system. Are you sure?"}
</script>

<div>

    <header>
        <div>
            <h1 class="leftmargin">Alpha v0.0</h1>
            <div>
                <p class="leftmargin">
                <button class="mdl-button mdl-js-button mdl-button--raised mdl-js-ripple-effect leftmargin" data-toggle="modal" data-target="#myModal" data-upgraded=",MaterialButton,MaterialRipple">Submit<span class="mdl-button__ripple-container"><span class="mdl-ripple"></span></span></button>
          Or, upload XMl file:
                <button class="mdl-button mdl-js-button mdl-button--raised mdl-js-ripple-effect leftmargin" data-toggle="modal" data-target="#myModal" data-upgraded=",MaterialButton,MaterialRipple">Choose file<span class="mdl-button__ripple-container"><span class="mdl-ripple"></span></span></button>
                <a target="_blank" href=" Tutorial-Help.html"><button class="mdl-button mdl-js-button mdl-button--raised mdl-js-ripple-effect tutorialbotton leftmargin" data-toggle="modal" data-target="#myModal" data-upgraded=",MaterialButton,MaterialRipple">Tutorial/Help<span class="mdl-button__ripple-container"><span class="mdl-ripple"></span></span></button></a>
                </p>
            </div>
        </div>
    </header>
    
    <br>
    <body>
    <div class="SubmissionArea">
"""

# Iterate through each entry and corresponding cells.
for row in range(1, len(all_rows)):
    crow = all_rows[row] # Current entry
    total_XML += """
    <div class="Entries" name="Entries">
    <legend class="leftmargin"> Entry </legend>
        <form class="form">
            <fieldset>
                <table class="container">"""

    for x in range(1, 12):
        ccell = crow[x].value

# Prints alert to user if cell is empty. 
# Note: As of now, it's just printed, but this could be incorporated into the UI in the future (perhaps a popup?)
        if ccell is None:
            print("Input missing from Entry " + str(row) + ", column " + str(x))

# Stores content of each cell in a HTML wrapper
# form field is set to column index number (would need to be manually changed if template is changed)
        else:
            if x == 1:
                total_XML += """
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3" for="channel-species" title="The species of the organism (latin name with exception of human) that your RNA-Seq data is for.">Species</label>
                    <input class='channelspecies' name='channelspecies' data-help-text='species' value='""" + ccell + """'/>
                </div>
                </tr>"""

            elif x == 2:
                total_XML += """
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3" for="channel-title" title="Title of RNA-Seq coverage. For example: Aerial part of long-day-grown 4-leaf-stage seedling with mock (NaCl) treatment">Title</label></th>
                    <input class='channeltitle' name='channeltitle' data-help-text='title' value='""" + ccell + """'/>
                </div>
                </tr>"""

            elif x == 3: #how to validate BAM link?
                total_XML += """
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3" for="channel-bam_link" title="It is required for your your BAM files or RNA-Seq data files to have a .dl repository link for the eFP-Seq Browser to give you input.">RNA-Seq Data/BAM file Repsitory Link</label>
                    <input class='channelbamlink' name='channelbamlink' data-help-text='bam_link' value='""" + ccell + """'/>
                </div>
                </tr>"""

            elif x == 4:
                total_XML += """
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3" for="channel-publication_link" title="If your research has been published or referencing a research, it may be useful to link to the publication.">Publicaiton Link</label>
                    <input class='channelpublicationlink' name='channelpublicationlink' data-help-text='publication_link' value='""" + ccell + """'/>
                </div>
                </tr>"""

            elif x == 5 and ("ncbi" or "NCBI" in ccell):
                total_XML += """
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3" for="channel-publication_url" title="If your RNA-Seq data is available on NCBI's Sequence Read Archive, it may be useful to include this informaiton.">Sequence Reach Archive/NCBI Link</label>
                    <input class='channelpublicationurl' name='channelpublicationurl' data-help-text='publication_url' value='""" + ccell + """'/>
                </div>
                </tr>"""

            elif x == 6:
                total_XML += """
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3" for="channel-total_reads_mapped" title="The total amount of reads mapped in your RNA-Seq data.">Total Reads Mapped</label>
                    <input class='channeltotalreadsmapped' name='channeltotalreadsmapped' data-help-text='svgname' value='""" + str(ccell) + """'/>
                </div>
                </tr>"""

            elif x == 7 and ".svg" in ccell:
                total_XML += """
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3" for="channel-svgname" title="Admin use only: SVG Name. Ex: ath-rosettePlusRoot.svg">SVG Name</label>
                    <input class='channelsvgname' name='channelsvgname' data-help-text='total_reads_mapped' value='""" + ccell + """'/>
                </div>
                </tr>"""

            elif x == 8:
                total_XML += """
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3" for="channel-tissue" title="The tissue the RNA-Seq data is from.">Tissue</label>
                    <input class='channeltissue' name='channeltissue' data-help-text='tissue' value='""" + ccell + """'/>
                </div>
                </tr>"""

            elif x == 9:
                total_XML += """
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3" for="channel-controls" title="The BAM exp number of the controls in your RNA-Seq data.">Controls</label>
                    <input class='channelcontrols' name='channelcontrols' data-help-text='total_controls' value='""" + ccell + """'/>
                </div>
                </tr>
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3" for="channel-record_number" title="Record or run number. For example ERR274310 or SRR547531">Record number</label>
                    <input class='channelrecordnumber' name='channelrecordnumber' data-help-text='record_number' value='""" + ccell + """'/>
                </div>
                </tr>"""

            elif x == 10:
                replicates = ccell.split(", ")

# Checks to make sure they don't have over 5 replicates.
                if len(replicates) > 5:
                    print("Sorry, you have over 5 replicates in Entry " + str(row))

                else:
                    k = 1
                    for i in replicates: # Populate w/ each replicate.

                        if replicates.index(i) == 0:
                            total_XML += """
                <tr>            
                <div class='forminput row'>
                    <label class="col-sm-3">Replicate</label>
                    <input class='channelgroupwidtho' name='channelgroupwidtho' data-help-text='groupwidth' value='""" + i + """'/>
                </div>
                </tr>"""
                            k += 1
                        else:    
                            total_XML += """
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3">Replicate</label>
                    <input class='channelgroupwidth""" + str(k) + "' name='channelgroupwidth""" + str(k) + "' data-help-text='groupwidth' value='""" + i + """'/>
                </div>
                </tr>"""
                            k += 1

# Add in the remaining empty replicates, change 5 to whatever max # you want.
                    j = k
                    for x in range(len(replicates), 5):

                        total_XML += """
                <tr>
                <div class='forminput row'>
                    <label class="col-sm-3">Replicate</label>
                    <input class='channelgroupwidth""" + str(j) + "' name='channelgroupwidth""" + str(j) + """' data-help-text='groupwidth' value=''/>
                </div>
                </tr>"""
                        j += 1


            elif x == 11:
                 total_XML += """
                <tr>
                <div class='forminput row'>
                    <label for="channel-description" class="formtextarea col-sm-3" title="Description of your RNA-Seq submission data">Description</label>
                    <input class='channeldescription' name='channeldescription' data-help-text='description' value='""" + ccell + """'/>
                </div>
                </tr>"""

    total_XML += """
                </table>
            </fieldset>
        </form>
    </div>
"""


total_XML += """
    </div>
    </body>
    </br>
    <div id="Cloning" class="button_fixed">
        <p>
            <button id="CloneForm" class="mdl-button mdl-js-button mdl-button--raised mdl-js-ripple-effect leftmargin" data-upgraded=",MaterialButton,MaterialRipple">Add another entry<span class="mdl-button__ripple-container"><span class="mdl-ripple"></span></span></button>
            <button id="SubmitButton" class="mdl-button mdl-js-button mdl-button--raised mdl-js-ripple-effect leftmargin" data-upgraded=",MaterialButton,MaterialRipple">Generate XML<span class="mdl-button__ripple-container"><span class="mdl-ripple"></span></span></button>
        </p>
    </div>
    <div id="generated" style="display:none">
        <h2>bamdata.xml</h2>
        <a href="#" id="DownloadLink">Download XML</a>
        <textarea id="ResultXml" style="width: 100%; height: 30em" readonly="readonly"></textarea>
    </div>    
</div>

<!-- Floating help button -->
<a href="Tutorial-Help.html"><img src="Images/help2.png" style="position: fixed; bottom: 10px; right: 10px;" height="40" title="Tutorial on how the submission system works for the eFP-Seq Browser and what to put in each input field (including how to find it)."></a>
</html>"""

print (total_XML) # Testing purposes

f.write(total_XML)
f.close()

filename = "/Users/Alexander/Dropbox/School/CSB498/eFP-Seq Browser submission development/eFP-Seq-Browser/cgi-bin/Submission_page/submission_parse.html"
# get("firefox").open_new_tab(filename)
