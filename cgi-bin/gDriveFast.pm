package gDriveFast;
################################################################################
# This is the package for gDriveMountFast program
# Author: Asher
# Date: November 2016
################################################################################
use strict;
use warnings;
use WWW::Curl::Easy;
use JSON;


require Exporter;
our @ISA = qw(Exporter);
our @EXPORT = qw(verifyFolder buildFileSystem getPartialFileData getFileSize systemExit);

# Google API Key:
my $apiKey = "AIzaSyDxuD5HgK1H1xIvDqaKY0EMSIjc-9e7I_c";

# Check if folder is real
sub verifyFolder {
	my ($folderId) = @_;
	my $response_body;
	my $response_code;
	my $retcode;
	my $jsonData;
	my $folderURL;
	my $curl = WWW::Curl::Easy->new;
	my $json = JSON->new;

	$folderURL = "https://www.googleapis.com/drive/v3/files/" . $folderId . "?key=" . $apiKey;

	# Configure curl
	$curl->setopt(CURLOPT_URL, $folderURL);
	$curl->setopt(CURLOPT_WRITEDATA,\$response_body);

	# Run curl
	$retcode = $curl->perform;

	# check results
	if ($retcode == 0) {
		$response_code = $curl->getinfo(CURLINFO_HTTP_CODE);
		if ($response_code == 200) {
			$jsonData = $json->decode($response_body);

			# Now check if it is a google app folder
			unless ($jsonData->{"mimeType"} eq "application/vnd.google-apps.folder") {
				systemExit("The link provided does not look like a google drive folder.");
			}
		} else {
			systemExit("Error: Google drive folder response is not 200. It is: $response_code\n");
		}
	} else {
		systemExit("Error accessing Google drive folder.\n");
	}
}

# The the size of the bam and bam index files
sub getFileSize {
	my ($fileId) = @_;
	my $response_size;
	my $response_code;
	my $retcode;
	my $curl = WWW::Curl::Easy->new;

	my $fileURL = "https://www.googleapis.com/drive/v3/files/" . $fileId. "?key=" . $apiKey . "&alt=media";

	# Configure curl
	$curl->setopt(CURLOPT_URL, $fileURL);
	$curl->setopt(CURLOPT_NOBODY, 1);	# Just do HEAD request

	# Run curl
	$retcode = $curl->perform;

	# check results
	if ($retcode == 0) {
		$response_code = $curl->getinfo(CURLINFO_HTTP_CODE);
		if ($response_code == 200 || $response_code == 206) {
			$response_size = $curl->getinfo(CURLINFO_CONTENT_LENGTH_DOWNLOAD);
			systemExit("File size is unknown.\n") if ($response_size == -1);
		} else {
			systemExit("Error: Google drive file: $fileId response is not 200. It is: $response_code\n");
		}
	} else {
		systemExit("Error accessing Google drive folder.\n");
	}

	return $response_size;
}


# Get Partial File Data
sub getPartialFileData {
	my ($fileId, $offset, $buffer) = @_;
	my $response_body = "";
	my $response_code;
	my $retcode;
	my $curl = WWW::Curl::Easy->new;

	# sleep(2);
	my $fileURL = "https://www.googleapis.com/drive/v3/files/" . $fileId. "?key=" . $apiKey . "&alt=media";
	my $size = $buffer + $offset - 1;
	my $range = "$offset" . "-" . $size;

	# Configure curl
	$curl->setopt(CURLOPT_URL, $fileURL);
	$curl->setopt(CURLOPT_RANGE, $range);
	$curl->setopt(CURLOPT_WRITEDATA,\$response_body);

	# Run curl
	$retcode = $curl->perform;

	# check results
	if ($retcode == 0) {
		$response_code = $curl->getinfo(CURLINFO_HTTP_CODE);
		if ($response_code == 200 || $response_code == 206) {
			# Either full or partial data has been recieved.
			if ($response_body eq "") {
				systemExit("Error: No data from file.");
			}
			return $response_body;
		} else {
			systemExit("Error: Google drive folder response is not 200. It is: $response_code\n");
		}
	} else {
		systemExit("Error accessing Google drive folder.\n");
	}
}

# Build the file system
sub buildFileSystem {
	my ($files, $folderId, $bamName) = @_;
	my $folderListURL;
	my $response_body;
	my $response_code;
	my $retcode;
	my $jsonData;
	my $curl = WWW::Curl::Easy->new;
	my $json = JSON->new;
	my $fileName;
	my $fileSize;

	# Check if file is not deleted and in the parent folder
	# Note: Deleted file are retrieved if trashed = false is not set!
	$folderListURL = "https://www.googleapis.com/drive/v3/files?q=trashed%3Dfalse+and+'" . $folderId . "'+in+parents&key=". $apiKey;

	# Configure curl
	$curl->setopt(CURLOPT_URL, $folderListURL);
	$curl->setopt(CURLOPT_WRITEDATA,\$response_body);

	# Run curl
	$retcode = $curl->perform;

	# check results
	if ($retcode == 0) {
		$response_code = $curl->getinfo(CURLINFO_HTTP_CODE);
		if ($response_code == 200) {
			$jsonData = $json->decode($response_body);

			# Loop around this
			for (my $i = 0; $i < scalar(@{$jsonData->{"files"}}); $i++) {
				if ($jsonData->{"files"}[$i]{"kind"} eq "drive#file") {
					# It is a file, Add it
					$fileName = $jsonData->{"files"}[$i]{"name"};

					# Mounting accepts any filename with the same string as bamName
					next unless ($fileName eq $bamName || $fileName eq ($bamName . ".bai"));
					$fileSize = getFileSize($jsonData->{"files"}[$i]{"id"});

					# Adding
					$files->{$fileName}{'id'} = $jsonData->{"files"}[$i]{"id"};
					$files->{$fileName}{'type'} = 0100;
					$files->{$fileName}{'mode'} = 0400;
					$files->{$fileName}{'size'} = $fileSize;
					$files->{$fileName}{'ctime'} = time() - 1000;
				}
			}

			# Now check if it is a google app folder
			unless ($jsonData->{"kind"} eq "drive#fileList") {
				systemExit("Error: Could not list file in Google drive.");
			}
		} else {
			systemExit("Error: Google drive API response is not 200. It is: $response_code\n");
		}
	} else {
		systemExit("Error accessing Google drive folder.\n");
	}

}

# Graceful exit
sub systemExit {
	my ($message) = @_;
	$message = "Google Drive Mount Program: " . $message;
	print STDERR $message;
	exit(1);
}

1;
