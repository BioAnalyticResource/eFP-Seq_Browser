#!/usr/bin/perl
################################################################################
# This program mount the Google Drive file system and run Sam Tools.
# Author: Asher
# Date: November, 2016
# Notice: Add Google API key before running
# To Start: perl gDriveMountFast.pl <google share folder id> <timestamp>
# To Stop: fusermount -u /mnt/gDrive/<folderid>_<timestamp> && rmdir mnt/gDrive/<folderid>_<timestamp>
################################################################################
use warnings;
use strict;
use Fuse;
use POSIX qw(ENOENT EISDIR EINVAL);

use lib '.';
use gDriveFast;

use Data::Dumper;

# The file system
my (%files) = (
	'.' => {
		type => 0040,
		mode => 0755,
		ctime => time()-1000
	}
);

# The following code is ispired from from Perl FUSE documentation
sub filename_fixup {
	my ($file) = shift;
	$file =~ s,^/,,;
	$file = '.' unless length($file);
	return $file;
}

# Size, name, permission etc.
sub e_getattr {
	my ($file) = filename_fixup(shift);
	$file =~ s,^/,,;
	$file = '.' unless length($file);
	return -ENOENT() unless exists($files{$file});

	my ($size) = exists($files{$file}{cont}) ? length($files{$file}{cont}) : 0;
	$size = $files{$file}{size} if exists $files{$file}{size};
	
	# Size for Google Drive files
	if ($files{$file}{type} == 0100) {
		$size = getFileSize($files{$file}{id});
	}

	# Fix folder size
	if ($files{$file}{type} == 0040) {
		$size = 4096;
	}

	my ($modes) = ($files{$file}{type}<<9) + $files{$file}{mode};
	my ($dev, $ino, $rdev, $blocks, $gid, $uid, $nlink, $blksize) = (0,0,0,1,0,0,1,1024);
	my ($atime, $ctime, $mtime);
	$atime = $ctime = $mtime = $files{$file}{ctime};
	
	# 2 possible types of return values:
	#return -ENOENT(); # or any other error you care to
	return ($dev,$ino,$modes,$nlink,$uid,$gid,$rdev,$size,$atime,$mtime,$ctime,$blksize,$blocks);
}

# This is used for browsing directories
sub e_getdir {
	# return as many text filenames as you like, followed by the retval.
	return (keys %files),0;
}

sub e_open {
	# VFS sanity check; it keeps all the necessary state, not much to do here.
    my $file = filename_fixup(shift);
    my ($flags, $fileinfo) = @_;
	
	return -ENOENT() unless exists($files{$file});
	return -EISDIR() if $files{$file}{type} & 0040;
    
    my $fh = [ rand() ];
    return (0, $fh);
}

# This is used by samtools mpileup program
sub e_read {
	# return an error numeric, or binary/text string.  (note: 0 means EOF, "0" will
	# give a byte (ascii "0") to the reading program)
	my ($file) = filename_fixup(shift);
	my ($buf, $off, $fh) = @_;
	return -ENOENT() unless exists($files{$file});
	
	# Read from Gooogle Drive file
	if(!exists($files{$file}{cont})) {
		# Get Data from partial cURL request
		my $context = getPartialFileData($files{$file}{id}, $off, $buf);
		return $context;
	}

	# We get size from cURL head request. This is content length
	return -EINVAL() if $off > $files{$file}{size};
	return 0 if $off == $files{$file}{size};
}

sub e_statfs { 
	return 255, 1, 1, 1, 1, 2 
}

sub main {
	my $folderId = "";
	my $folderURL = "";
	my $fileListURL = "";
	my $directory = "";
	my $timestamp = "";
	my $bamName = "";

	# Get folder ID from command line
	if (@ARGV) {
		$folderId	= shift(@ARGV);
		$timestamp	= shift(@ARGV);
		$bamName	= shift(@ARGV);

		# verify folder ID format
		systemExit("No folder ID provided\n") unless ($folderId);
		systemExit("No timestamp or random number provided\n") unless ($timestamp);		
		systemExit("No BAM filename was provided\n") unless ($bamName);
		systemExit("Error folder ID may not be in the correct format.\n") unless ($folderId =~ /^[a-zA-Z0-9_-]+$/);
		systemExit("Timestap or random number is not in correct format.\n") unless ($timestamp =~ /^\d+$/);

	} else {
		systemExit("Usage: perl gDriveMountFast.pl <gdrive folder ID> <timestamp or random number> <bam filename>\n");
	}
		
	# check if folder exists and readible
	verifyFolder($folderId);

	# Set up the directory
	$directory = $folderId . "_" . $timestamp;
	chdir "/mnt/gDrive/";
	system("mkdir", $directory);
	chdir "/mnt/";	# Must get out of gDrive directory to make sure umounts are clean (Just a double check)
	$directory = "/mnt/gDrive/" . $directory;
	# Now build 
	buildFileSystem(\%files, $folderId, $bamName);

	fork and exit;
	
	# Now mount with noexec, nodev, nosuid, etc.
	Fuse::main(
		mountpoint	=> $directory,
		mountopts	=> "ro,noexec,nodev,nosuid,noatime",
		getattr		=> "main::e_getattr",
		getdir		=> "main::e_getdir",
		open		=> "main::e_open",
		statfs		=> "main::e_statfs",
		read		=> "main::e_read",
		threaded	=> 0
	);

}

# Call main
main();

