# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/) and this project adheres to [Semantic Versioning](http://semver.org/).

To see tags and releases, please go to [Tags](https://github.com/BioAnalyticResource/eFP-Seq_Browser/tags) on [GitHub](https://github.com/BioAnalyticResource/eFP-Seq_Browser).

## [1.3.14] - 2022-06-09

**A brand new version of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) has dropped!**

Version 1.3.14 (dev version: p20220606) has now dropped which focuses primary on fixing bugs and optimizations.

**Optimization**:

-   Converted some images to webp
-   Converted single declaration variables to const
-   Decrease file sizes of SVGs
-   Removed unused variables
-   Removed redundant code
-   Removed depreciated code
-   Refactored some code
-   Updated meta-data
-   Updated service workers

**Security**:

-   Added Content Security Policy

**Update**:

-   Updated Bootstrap, Material Design, jQuery UI, html2canvas & mathJS packages
-   Update Google Analytics to GA4

**Actions**:

-   Removed daily scheduled action runs (only on push now)

**Documentation**:

-   Updated styling
-   Renamed some variables to keep code clean

**Bug fix**:

-   Fixed UI issue relating to tablet size screens
-   Fixed issues with incorrectly calling functions
-   Fixed issue with throw not throwing error correctly
-   Fixed issue of images having missing alt attributes
-   Fixed issues with service worker trying to cache itself
-   Fixed issue where colours of radio buttons were displaying incorrectly
-   Fixed missing ID in web manifest
-   Fixed missing main aria landmark
-   Fixed missing aria labels
-   Fixed missing closing tags
-   Fixed duplicate ID in HTML elements

## [1.3.13] - 2022-03-16

**A brand new version of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) has dropped!**

Version 1.3.13 (dev version: p20220316) has now dropped which focuses primary on fixing bugs with minor optimizations.

**UI/UX**:

-   Removed ambiguous wording (data found "here")

**Optimization**:

-   Added missing dynamic structured data
-   Updated meta-data

**Security**:

-   Added a step to verify locus input

**Update**:

-   Update packages

**Documentation**:

-   Prettified code
-   Improved readability of code

**Bug fix**:

-   Fixed issue relating to using hexadecimal and encoding
-   Fixed issue where eFP-Seq Browser was not working on Safari 10
-   Fixed issue where CSS was not working on Safari 3
-   Fixed issue where maskable icons were not matching appropriate sizes
-   Fixed duplicate alt for images
-   Fixed broken HTML tags
-   Fixed line ending issue for webservice

## [1.3.12] - 2021-11-18

**A brand new version of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) has dropped!**

Version 1.3.12 (dev version: p20211118) has now dropped and it allows users to submit their datasets which they made publicly available to us so we can make them community datasets. In addition are bug and security fixes, as well as optimizations.

**New feature**:

-   If a user would like to have their dataset publicly available as a community dataset, they can now submit it to us

**UI/UX**:

-   Updated logo from raster PNG to a vector SVG (this includes updating favicons)

**Optimization**:

-   Added display swap to Google Font

**Security**:

-   Fixed security issue regarding jQuery-UI's grunt vulnerability by updating all packages
-   Updated server security

**Update**:

-   Updated Bootstrap, mathJS and jQuery packages

**Documentation**:

-   Updated my author details to include Alexander Sullivan's personal website

**Bug fix**:

-   Fixed incorrect documentation
-   Fixed incorrect meta-data
-   Fixed issue where when closing navigation bar, it would adjust the table content to the left side of the page instead of it being centred
-   Fixed issue where the service working was trying to cache itself
-   Fixed issue where service worker was not able to find files

**Known issue**:

-   If the web service timeouts, the eFP-Seq Browser will load continuously
-   Loading circle is not centred

## [1.3.6] - 2021-09-20

**A brand new version of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) has dropped!**

Version 1.3.6 (dev version: p20210325) now makes the generation of data no longer requiring an SRA record number/ID to process data. Also includes UI/UX adjustments, offline service workers, optimization, and security & bug fixes.

**New feature:**

-   Add offline service worker for instance if a user loses connection mid-usage (this makes no change on loading new data but rather existing data)

**UI/UX:**

-   Added loading percent to the document's title
-   When the user clicks on "Generate XML" from the generate data form, it now moves the screen/document to the bottom of the page where the download button is
-   Removed duplicate arrows from help cards

**Optimization**:

-   Removed unnecessary code and unnecessary steps in logic
-   Added more GitHub workflows
-   Added cache-control
-   Updated what is cached and added preloading

**Security**:

-   Fixed incomplete URL substring sanitization issue

**Documentation**:

-   Added missing documentation

**Bug fix:**

-   Fixed issue where cookies were expiring on session end instead of a new version (also updated cookie name to be less vague)
-   Fixed issue where the eFP-Seq Browser required an SRA record number/ID to process data (no longer requires it)
-   Fixed issue where if a user adds multiple of the same SRA record number/ID, would fail to process consecutive SRA record numbers/IDs with the same record number/ID
-   Fixed issue where if no publication link or SRA record number was given, it would display a false link towards both of those within the "More details" of the table
-   Fixed issue where if the RNA-Seq map coverage/data visualization fails to load, would not display anything at all - now displays an error
-   Fixed issue where the loading screen was blocking interaction with the eFP-Seq Browser's table
-   Fixed issue where document's title was displaying the wrong name of the dataset if it was uploaded by the user
-   Fixed issue where inputs had no names and images had no alternative text (accessibility adjustments)
-   Fixed issue where creating new entries or resetting the entries within the generate data form was giving the incorrect entry number
-   Fixed incorrect link to GitHub page for the eFP-Seq Browser
-   Fixed broken bootstrap modals unable to close
-   Fixed web manifest not working correctly
-   Fixed missing meta-data and manifest
-   Fixed vagueness of version number and variable names
-   Fixed grammar
-   Fixed the mobile UI

**Known issue:**

-   If the web service timeouts, the eFP-Seq Browser will load continuously
-   Loading circle is not centred

## [1.3.5] - 2021-01-12

**A brand new version of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) has dropped!**

Version 1.3.5 (dev version: p20210112) includes bug fixes, optimization and general improvements to make the experience smoother for the user.

**UI:**

-   Updated styling to make the text more readable
-   Updated moving elements to move faster and without notice
-   Error message will display above whatever is in the body/content of the eFP-Seq Browser instead of replacing it

**Optimization:**

-   Added code scanner workflows

**Bug fix:**

-   Fixed issue where if no gene structure data was returned, prevent data from loading
-   Fixed issue where if it was not able to generate a variant visualization, it would present the incorrect variant visualization. Now presents an error instead
-   Fixed issue where if no RPKM was able to be calculated, it would prevent data from correctly loading
-   Fixed issue where if no record/SRA data was generated, would cause issues with displaying the lack of data
-   Fixed issue where some buttons sometimes did nothing when clicked
-   Fixed issue where clicking submit on generating data would sometimes not send data to be loaded
-   Fixed issue when uploading data or submitting data (from generating data) would keep the previous modal/window open instead of closing it
-   Fixed issue where, when generating data and selecting a tissue, tissue selection sometimes fills with something the user did not click
-   Fixed issue where the bulk template for generating data was not downloading
-   Fixed issue where there is a missing arrow key for the dataset and/or tissue selection
-   Fixed issue where if the web service returns an error relating to using SAMTools on the BAM files, may cause either continuous loading or failed to load RNA-seq mapping
-   Fixed issue where sorting arrows would not appear on Microsoft Edge
-   Fixed issue where user cannot download the table as an image on Microsoft Edge
-   Fixed misaligned navbar footer
-   Fixed bug where no tissue information was sent to the server to visual RNA-Seq data on user-generated data
-   Fixed potential cause of gtag (Googe login) issues

**Security:**

-   Fixed potential client-side cross-site scripting

**Update:**

-   Updated metadata
-   Updated packages including Bootstrap, ddslick, Google Material Icons, html2canvas, jQuery, jQuery UI, mathJS and tableToCSV
-   Replaced custom lazy loading with browser's built-in lazy loading for images

**Documentation:**

-   Added missing documentation
-   Reorganized files to make it easier to find files
-   Renamed files
-   Updated installation notes within README

**Known issue:**

-   If the web service timeouts, the eFP-Seq Browser will load continuously
-   Loading circle is not centred

## [1.3.4] - 2020-09-10

**A brand new version of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) has dropped!**

Version 1.3.4 (dev version: p20200910) includes mostly bug fixes but also, an optimization on lazy loading images.

**Optimization:**

-   Lazy loading has been added to all images

**Bug fixes:**

-   Fixed issue where Google Login/Authentication data and buttons would not load
-   Fixed issue where Google Login/Authentication and autofill data would not initialize
-   Fixed issue where OAuth would not load properly causing issues with accounts
-   Fixed issue where some styling would not appropriately change to loaded data
-   Fixed issue where if an %20 (space character) was in a shared link, would cause an issue retrieving that value
-   Fixed an issue where invalid locus or records would prevent anything from being loaded
-   Fixed an issue where if cannot find start base pair position, would prevent anything from being loaded
-   Fixed issue where SVG would not colour correctly
-   Fixed issue where elements could not find their data values
-   Added more fail-safes to prevent issues with displaying data

## [1.3.3] - 2020-06-09

**A brand new version of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) has dropped!**

Version 1.3.3 (dev version: p20200608) includes mostly bug fixes but also updated how eFP-Seq Browser's URL looks when loading data.

**New features:**

-   eFP-Seq Browser's URL automatically update with new data loaded
-   Tor browser support added
-   Added Google Tag Manager to start tracking issues with eFP-Seq Browser
-   Now sends errors in logic as an error to console to be tracked for bug reporting

**Optimization:**

-   Updated autocomplete call for speed and security

**Bug fixes:**

-   Fixed issue where if a BAM data was not reachable/unreadable, data would load continuously - Added a greyscaled error as a fail-safe for individual data points that fail on the front-end UI (created "status":"fail" for rnaSeqMapCoverage webservice)
-   Fixed bug where if a variant position was not detected, would not load data
-   Fixed issue where loading shared data that had overlapped data with public data, it would load the cached public data instead of shared data
-   Fixed bug where Google Identity login properties would not load
-   Fixed bug where if the container of all data point's information is not defined, causes errors in loading visualized data
-   Fixed bug where is expression information is not found, causes errors in loading visualized data
-   Fixed bug where is RPKM is not found or calculated, causes issues in loading visualized data and creating maximum scales
-   Fixed bug where if Google user information was not found, causes issues in loading datasets
-   Fixed bug where an error message would not be displayed for users
-   Fixed bug where if there is an inability to detect the user's browser, would cause errors for the eFP-Seq Browser
-   Fixed issue where colour SVGs would sometimes cause a JavaScript timeout due to how long it takes to initialize the process
-   Fixed visual issue where scrolling to select SVG/data point's highlight would disappear too fast for users to appropriately notice the select SVG/data point
-   Fixed UI issue where there would be a tiny empty box at the top of the loaded table
-   Fixed UI for warning to fill the whole body of the main container instead of just the top
-   Fixed issue where autocomplete would not initialize
-   Fixed grammar and spelling
-   Adjusted "status = 2" (recalculating r coefficient value) call as that is from the legacy version of the eFP-Seq Browser
-   Updated list of authors

## [1.3.2] - 2020-05-19

**A brand new version of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) has dropped!**

Version 1.3.2 (dev version: p20200519) includes new visual indicators for loading and optimization as well as security and bug fixes.

**New features:**

-   Added a visual indicator that data is loading (progress cursor)
-   Updated page title so it now displays what has been loaded (if anything)
-   Tracking BAR related cookies including the version number and whether a user has already accepted T&S/Cookie policy or not's display prompt
-   Added missing description-meta data (for SEOs)

**Optimization**

-   Removed junk files

**Security fix**

-   Updated jQuery version to address a security issue

**Bug fixes:**

-   Fixed issue where downloaded CSV takes the name of a selected dataset instead of loaded dataset
-   Fixed naming of CSV files to remove spaces and replace them with underscores
-   Fixed an issue where is a sample has 0 reads mapped, it would prevent completion of loading RNA-seq visualized data
-   Fixed the tooltip for the loading bar to more accurately display loading progress
-   Fixed issue if scripts cannot read if the sample is a cache datapoint, default to false
-   Fixed issue where the user was unable to login into Google Account has been fixed
-   Fixed more missing HTTPS links
-   Fixed issue where loading screen would disappear too early
-   Fixed issue where user cannot change absolute max
-   Fixed issue where absolute max may not initially display the absolute RPKM max for the current displayed dataset + locus
-   Removed the legacy version of the eFP-Seq Browser as it was no longer functional
-   Corrected the list of authors for the eFP-Seq Browser
-   Made code more human-readable
-   Updated documentation
-   Updated README

## [1.3.1] - 2019-08-12

**A brand new version of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) has dropped!**

Version 1.3 includes details of how to find the official publication of the eFP-Seq Browser as well as bug fixes

**New features:**

-   With the official publication of the eFP-Seq Browse published by The Plant Journal available at [https://doi.org/10.1111/tpj.14468](https://doi.org/10.1111/tpj.14468), this information can now be found on the eFP-Seq Browser's help section under citation

**Bug fixes:**

-   Fixed bug where relative RPKM median was calling itself instead of the median of the list of possible RPKM values
-   Added extra verification step to uploading data (this fixed the issue where uploading custom data would just suddenly stop)
-   Corrected grammar mistakes
-   Updated README

**Known issues:**

-   The IGB links do not work with Google Drive repositories (link to IGB will not appear for Google Drive files till this is fixed)
-   Download page as an image does not render SVGs in Microsoft Edge
-   Some sorting arrows may not display in Microsoft Edge

## [1.3.0] - 2019-06-25

**A brand new version of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) has dropped!**

Version 1.3 includes even more features, more quality of life changes and more bug fixes

**New features:**

-   Users can now generate a share link of their current session
-   Users can now compare multiple genes variants of a single sample

**Quality of Life changes:**

-   Updated description and details around read map method
-   Changed visibility of the gene variant dropdown selection to make it more clear that it is a selectable option
-   Added tooltips to r<sub>pb</sub> and PRKM to give more details of how to read that information

**Bug fixes:**

-   Change wording/phrasing to prevent confusion
-   Changed bamdata_amazon_links to bamdata_araport11 to prevent confusion with the name
-   Optimize data calling
-   Optimized and minified SVGs
-   Updated landing page to more accurately depict current UI
-   Updated help section with new features and updated old images with new UI elements
-   Fixed issue which preventing download table as CSV
-   Fixed issue with incorrect samples being displayed in the Klepikova data
-   Fixed issue with changing gene variants would either load slowly or not load at all
-   Fixed issue with giant arrows in Microsoft Edge
-   Fixed issue where incorrect RPKM and r<sub>pb</sub> would not change during switch variants
-   Fixed issue where relative RPKM would not display the correct information
-   If a sample has no control data, now uses the median of all samples instead of empty data
-   Replaced more http with https

**Known issues:**

-   The IGB links do not work with Google Drive repositories (link to IGB will not appear for Google Drive files till this is fixed)
-   Download page as an image does not render SVGs in Microsoft Edge
-   Some sorting arrows may not display in Microsoft Edge

## [1.2.0] - 2019-04-10

**A new version of the [eFP-Seq Browser](https://bar.utoronto.ca/eFP-Seq_Browser/) has dropped!**

Version 1.2 which includes the following new features, quality of life changes, and bug fixes:

**New features:**

-   Cookie policy and privacy policy has been added to the landing page when a user arrives Privacy Policy
-   You can now delete your account as a whole which will also delete your uploaded files permanently from the "Manage Account" modal
-   Filter eFP images from the RNA-table has been added
    ![FiltereFPImages](https://bar.utoronto.ca/~asullivan/RNA-Browser/cgi-bin/img/helpModal/0019_eFPImagesFilter.png)
-   Added Klepikova stress data and pollen data to the Klepikova data set
-   Switched from samtools' mpileup to bcftools mpileup (samtools mpileup is no longer supported)
-   RPKM calculations now exclude introns from its calculations

**Quality of Life changes:**

-   You can now press enter on the locus ID or y-axis scale input boxes to load a data set
-   You can now have no input for your read maps or insert 0 to have the eFP-Seq Browser find the read maps count for you
-   "araport.cyverse-cdn" is now an alternative option to Amazon's AWS
-   Switching between absolute and relative mode no longer requires loading the table again
-   Added a hover/tooltip to the loading bar to display how much of the page has been loaded (as a percentage)
-   Changed colour of buttons when enabled to more clearly indicate what can be clickable

**Bug fixes:**

-   Add extra verification and security steps to any aspect of the eFP-Seq Browser that involves a user's account
-   Spelling mistakes, grammar and styling has been corrected
-   Help images and landing page image now more accurately represents the current version of the eFP-Seq Browser
-   Simplified some of the cognitive complexity within the open source code and added more documentation
-   Updated readmap counts for the Klepikova data and updated BAM index files for all default data sets
-   Changed PCC to r<sub>pb</sub> to more accurately depict what it is
-   Fixed bug where if no XML is selected in "Manage Account", the user was still able to delete XMLs
-   Fixed bug where deleted XMLs would stay listed as an option to the user until next refresh
-   Fixed bug where the delete XMLs function would be called unnecessarily, even if the "Manage Account" feature was not opened
-   Fixed bug where downloading a file as an XML from the "Manage Account" modal would return nothing
-   Fixed bug where main (table and landing page) content would disappear at certain resolutions
-   Fixed bug where opening and closing the navbar would sometimes cause the main content to disappear
-   Fixed bug where the download table as CSV would return an undefined BAM filename
-   Fixed bug where submitting data from the generate data module would not do anything
-   Fixed bug where custom AWS data was not able to load/mount correctly
-   Fixed bug where the y-scale was fixed to either 1 or 0
-   Fixed bug in generating the Google drive link for accessing BAM files
-   Fixed bug where if the filename of the BAM file is just ".bam", would prevent the user from moving forward in generating data (security reasons)
-   Optimized the speed of loading images (and reduce bandwidth requirements for loading the eFP-Seq Browser)
-   Optimized memory usage and fixed memory leak problem

**Supplementary data**

-   The use of R functions and command-line tools to compute the correlation between SR34 gene structures and RNA-coverage from a pollen data set has been [added](https://github.com/BioAnalyticResource/eFP-Seq-Browser/tree/master/R)

**Updated License**

-   Updated license from GPLv3 to [GPLv2](https://github.com/BioAnalyticResource/eFP-Seq-Browser/blob/master/LICENSE.md)

**Known issues:**

-   The IGB links do not work with Google Drive repositories (link to IGB will not appear for Google Drive files till this is fixed)
-   Download page as an image does not render SVGs in Microsoft Edge

## [1.1.0] - 2018-11-29

**A new version of the eFP-Seq Browser has dropped!**

Version 1.1 which includes the following new features and bug fixes:

**New features:**

-   When clicking on an SVG in the eFP Overview, it will now bring the user to that RNA-table's row
-   Table sorting arrows now show a direction

**Bug fixes:**

-   Fixed issue where information will not reset on loading new datasets
-   Fixed browser compatibility issues where navbar and RNA-table does not appear side-by-side
-   Fixed issue where eFP Overview would not load in Microsoft Edge
-   Fixed issue on Microsoft Edge where if the user loads a dataset then refreshes the page, new data will not load unless all input fields have had their information re-entered
-   Fixed issue where loading private datasets would not load in the correct order
-   Fixed issue where navbar footer would randomly pop out if the screen is maximized
-   Fixed issue where if the user was not already logged in Google prior to loading the live version, they were not able to log in at all
-   Fixed issue where uploading data from the local computer to eFP-Seq Browser without uploading to private account would not work
-   Fixed spelling mistakes
-   Added details in the help section that correctly matches the current version of the eFP-Seq Browser
-   Help card arrows now show the correct direction arrow when opened (or closed)
-   UI more responsive to different window resolutions (fixing weird look on some resolutions)
-   Reduced cognitive complexity of the code
-   Updated metadata and favicon

**Known issues:**

-   After generating new data, scrolling up doesn't work unless the user scrolls down first
-   Does not work on Internet Explorer
-   Google Drive repos will not work with IGB
-   Download page as an image does not render SVGs in Microsoft Edge

## [1.0.0] - 2018-09-25

The official full release of the eFP-Seq Browser is here! You can visit and use it at https://bar.utoronto.ca/eFP-Seq_Browser/ .

Enjoy!
