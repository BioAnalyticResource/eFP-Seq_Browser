#!/bin/bash 

# Outputs the mpileup of a given region into the subdirectory specified on line 25. Look for 113 files with > 0 KB file size as an indicator for successful data retrieval for the given locus.

# Priyank Purohit, February 1, 2016.

match_regex='/iplant/home/araport/rnaseq_bam/[a-zA-Z]*/([A-Z0-9a-z]*)/accepted_hits.bam' # This regex matches to the link paths in the txt file to get the TISSUE and RECORD.

for i in $(cat TEMP_iplant_path_to_bam_files.txt); do # Iterate over the paths in the txt file
	BAM_PATH="$(echo $i | grep -v 'bai$' | grep -P $match_regex)" # ignore the BAI file paths, match the regex above

	if [[ $BAM_PATH == *".bam"* ]] # If the match contains the .bam extension, proceed:
	then
		#echo ">>> "${i:32:-18}
		
		arr=(${i//\// })

		tissue=(${arr[-3]})
		record=(${arr[-2]})

		filename="/mnt/RNASeqData/"$tissue"/"$record"/accepted_hits.bam"

		echo $filename # this is the BAM file in the mnt directory that we will try to get data from

		samtools mpileup -r Chr2:10327050-10329941 $filename > data_retrieval_test/$tissue$record
	fi
done
