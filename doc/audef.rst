The Software Definitions File
=============================


The astro-update definitions file is a json dictionary in which each monitored software package is a key in the json dictionary,
with sub-keys providing needed information about the software.  For example the entries for ``HEASoft``
in the file ``astroupdate_defs_MASTER.json`` are::

    "heasoft": {
            "release_pattern": "[a-z,A-Z]+\\s{1}\\d{1,2},\\s{1}\\d{4}",
            "description": "Multi-Mission High Energy Analysis software",
            "release_url": "http://heasarc.gsfc.nasa.gov/docs/software/lheasoft/release_notes.html",
            "author": "HEASARC",
            "pattern": "\\d+\\.{0,1}\\d+",
            "release_marker": "RELEASE NOTES FOR HEASOFT",
            "ad_version": "6.20",
            "download_url": "http://heasarc.gsfc.nasa.gov/docs/software/lheasoft/download.html",
            "name": "HEASoft",
            "author_page": "http://heasarc.gsfc.nasa.gov/docs/software/lheasoft/",
            "pattern_marker": "RELEASE NOTES FOR HEASOFT",
            "pattern_description": "one or more digits followed by zeror or 1 period followed by one or more digits",
            "version_url": "http://heasarc.gsfc.nasa.gov/docs/software/lheasoft/release_notes.html",
            "release_description": "(Full month name) (1-2 digit day of month), (4 digit year)",
            "home_url": "http://heasarc.gsfc.nasa.gov/docs/software/lheasoft/",
            "ad_release_date": "01/18/17"
        }


The individual fields have the following meanings:


==================== 	=======================================================================      ========================================================
Element         		Sample Value                                   								 Meaning
==================== 	=======================================================================      ========================================================
release_pattern 		``[a-z,A-Z]+\\s{1}\\d{1,2},\\s{1}\\d{4}``								     regular expression used to retrieve the **release date**.  The release date is the (approximate) date of the release of the listed version of the software.
description 			Multi-Mission High Energy Analysis software 								 Brief description of the software
release_url             http://heasarc.gsfc.nasa.gov/docs/software/lheasoft/release_notes.html       url to parse for **release date**.
author: 				HEASARC 																	 astroupdate software author
pattern: 				``\\d+\\.{0,1}\\d+``  														 regular expression used to retrieve the **version string**
release_marker: 		RELEASE NOTES FOR HEASOFT													 text marker which helps identify the **release date string**
ad_version: 			6.20																		 Software version string
download_url            http://heasarc.gsfc.nasa.gov/docs/software/lheasoft/download.html            the url from which you can download the software
name: 					HEASoft																		 name of the software package
author_page:            http://heasarc.gsfc.nasa.gov/docs/software/lheasoft/						 url which contains information about the author of the software
pattern_marker: 		RELEASE NOTES FOR HEASOFT													 text marker which helps identify the **version**
pattern_description: 	one or more digits followed by zero or 1 period followed by digits			 description of the version pattern
version_url:            http://heasarc.gsfc.nasa.gov/docs/software/lheasoft/release_notes.html       url containing the version pattern
release_description: 	(Full month name) (1-2 digit day of month), (4 digit year)					 description of the release date
home_url: 				http://heasarc.gsfc.nasa.gov/docs/software/lheasoft/						 homepage of the software website
ad_release_date: 		01/18/17																	 release data in astro-update format
==================== 	=======================================================================      ========================================================
