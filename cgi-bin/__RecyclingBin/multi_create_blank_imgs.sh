# This file creates blank images in the /img folder for the multi.cgi script to write to.
# This script also sets the correct write permission
# Priyank February 4, 2016

# This regex matches to the link paths in the txt file.
match_regex='/iplant/home/araport/rnaseq_bam/[a-zA-Z]*/([A-Z0-9a-z]*)/accepted_hits.bam'
# Iterate over the paths in the txt file
convert -size 450x50 xc:white img/img_0.jpg || { printf '%s\n' 'Failed to create original image' ; exit 1 ; }
for i in $(cat data/iplant_path_to_rnaseq_bam_files.txt); do
	# ignore the BAI file paths, match the regex above
	BAM_PATH="$(echo $i | grep -v 'bai$' | grep -P $match_regex)"
	if [[ $BAM_PATH == *".bam"* ]] # If the match contains the .bam extension, proceed:
	then
		BAM_LINK='http://s3.amazonaws.com/iplant-cdn'$BAM_PATH #add the correct prefix
		out_file_name=${BAM_LINK:66} # new unique BAM file name
		out_file_name=${out_file_name////_} #replace the / with _
		out_file_name=${out_file_name/bam/png} #replace the / with _
		echo '>>> '$out_file_name
		cp img/img_0.jpg "img/${out_file_name}" || { printf '%s\n' "Failed to copy to image img_${_num}.jpg" ; exit 2 ; }
		chmod 766 "img/${out_file_name}"
	fi
done