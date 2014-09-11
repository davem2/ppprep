#!/usr/bin/env python

"""ppprep

Usage:
  ppprep [-abceipqv] <infile>
  ppprep [-abceipqv] <infile> <outfile>
  ppprep -h | --help
  ppprep ---version

Automates various tasks in the post-processing of books for pgdp.org using the ppgen post-processing tool.  Run ppprep as a first step on an unedited book text.

Examples:
  ppprep school.txt
  ppprep school-src.txt school2-src.txt

Options:
  -h --help            Show help.
  -a, --all            Perform all safe actions. (-bip) (default)
  -b, --boilerplate    Include HTML boilerplate code when processing illustrations 
  -c, --chapters       Convert chapter headings into ppgen style chapter headings.
  -e, --sections       Convert section headings into ppgen style section headings.
  -i, --illustrations  Convert [Illustration] tags into ppgen .il/.ca markup.
  -p, --pages          Convert page breaks into ppgen // 001.png style and Comment out [Blank Page] lines.
  -q, --quiet          Print less text.
  -v, --verbose        Print more text.
  --version            Show version.
"""  

from docopt import docopt
from PIL import Image
import glob
import re
import os
import sys
import logging


# Replace : [Blank Page]
# with    : // [Blank Page]
def processBlankPages( inBuf ):
	outBuf = []
	lineNum = 0
	
	logging.info("--- Processing blank pages")
	
	while lineNum < len(inBuf):
		m = re.match(r"^\[Blank Page]", inBuf[lineNum])
		if( m ):        
			outBuf.append("// [Blank Page]")
			logging.debug("Line " + str(lineNum) + ": convert " + inBuf[lineNum] + " ==> " + outBuf[-1])
			lineNum += 1
		
		else:
			outBuf.append(inBuf[lineNum])
			lineNum += 1

	return outBuf;
	
	
# Replace : -----File: 001.png---\sparkleshine\swankypup\Kipling\SeaRose\Scholar\------
# with    : // 001.png
def processPageNumbers( inBuf ):
	outBuf = []
	lineNum = 0
	
	logging.info("--- Processing page numbers")
	
	while lineNum < len(inBuf):
		m = re.match(r"^-----File: (\d\d\d\.png).*", inBuf[lineNum])
		if( m ):        
			outBuf.append("// " +  m.group(1))
			logging.debug("Line " + str(lineNum) + ": convert " + inBuf[lineNum] + " ==> " + outBuf[-1])
			lineNum += 1
		
		else:
			outBuf.append(inBuf[lineNum])
			lineNum += 1

	return outBuf;
	
	
def isLineBlank( line ):
	return re.match( r"^\s*$", line )
	
	
def isLineComment( line ):
	return re.match( r"^\/\/ *$", line )
	
	
def formatAsID( s ):
	s = re.sub(r" ", '_', s)        # Replace spaces with underscore    
	s = re.sub(r"[^\w\s]", '', s)   # Strip everything but alphanumeric and _
	s = s.lower()                   # Lowercase

	return s
	
	
def findPreviousNonEmptyLine( buf, startLine ):
	lineNum = startLine
	while lineNum < len(buf) and isLineBlank(buf[lineNum]):
		lineNum -= 1
	
	return lineNum
	
	
def findNextNonEmptyLine( buf, startLine ):
	lineNum = startLine
	while lineNum >= 0 and isLineBlank(buf[lineNum]):
		lineNum += 1
	
	return lineNum
	
	
def processHeadings( inBuf, doChapterHeadings, doSectionHeadings ):
	outBuf = []
	lineNum = 0 
	consecutiveEmptyLineCount = 0
	rewrapLevel = 0
	foundChapterHeadingStart = False

	logging.info("--- Processing headings")
	
	while lineNum < len(inBuf):
		# Chapter heading blocks are in the form:
			# (4 empty lines)
			# chapter name
			# can span more than one line
			# (1 empty line)
			# chapter description, opening quote, etc., 1 empty line seperating each
			# ...
			# (2 empty lines)

		# Section heading blocks are in the form
			# (2 empty lines)
			# section name
			# can span more than one line
			# (1 empty line)

		# Out-of-line formatting /# #/ /* */
		if( re.match(r"^\/\*$", inBuf[lineNum]) or re.match(r"^\/\#$", inBuf[lineNum]) ):
			rewrapLevel += 1
		elif( re.match(r"^\*\/$", inBuf[lineNum]) or re.match(r"^\#\/$", inBuf[lineNum]) ):
			rewrapLevel -= 1
			
		# Chapter heading
		if( doChapterHeadings and consecutiveEmptyLineCount == 4 and not isLineBlank(inBuf[lineNum]) and rewrapLevel == 0 ):
			inBlock = []
			outBlock = []
			foundChapterHeadingEnd = False;
			consecutiveEmptyLineCount = 0;
		
			# Copy chapter heading block to inBlock
			while( lineNum < len(inBuf) and not foundChapterHeadingEnd ):
				if( isLineBlank(inBuf[lineNum]) ):
					consecutiveEmptyLineCount += 1
					if( consecutiveEmptyLineCount == 2 ):
						foundChapterHeadingEnd = True
						consecutiveEmptyLineCount = 0
				else:
					consecutiveEmptyLineCount = 0
				
				if( foundChapterHeadingEnd ):
					# Remove trailing empty lines from chapter heading block
					inBlock = inBlock[:-1]
					# Rewind parser (to handle back to back chapter headings)
					lineNum = findPreviousNonEmptyLine(inBuf, lineNum) + 1
				else:
					inBlock.append(inBuf[lineNum])
					lineNum += 1
			
			# Remove the four consecutive blank lines that preceeds chapter heading
			outBuf = outBuf[:-4]
		
			# .sp 4
			# .h2 id=chapter_vi
			# CHAPTER VI.||chapter description etc..
			# .sp 2             
			chapterID = formatAsID(inBlock[0])
			chapterLine = ""
			for line in inBlock:
				chapterLine += line
				chapterLine += "|"
			chapterLine = chapterLine[:-1]
			
			logging.debug("Found chapter heading: " + chapterLine)

			outBlock.append("// ******** PPPREP GENERATED ****************************************") 
			outBlock.append(".sp 4")
			outBlock.append(".h2 id=" + chapterID )             
			outBlock.append(chapterLine)
			outBlock.append(".sp 2")

			# Write out original as a comment
			outBlock.append(".ig  // *** PPPREP BEGIN ORIGINAL ***********************************") 
			outBlock.append("") 
			outBlock.append("") 
			outBlock.append("") 
			outBlock.append("") 
			for line in inBlock:
				outBlock.append(line)
			outBlock.append(".ig- // *** END *****************************************************")
				
			# Write out chapter heading block
			for line in outBlock:
				outBuf.append(line)
			
			# Log action
			print(".h2 " + chapterLine)
				
		# Section heading
		elif( doSectionHeadings and consecutiveEmptyLineCount == 2 and not isLineBlank(inBuf[lineNum]) and rewrapLevel == 0 ):
			inBlock = []
			outBlock = []
			foundSectionHeadingEnd = False;
			consecutiveEmptyLineCount = 0;
		
			# Copy section heading block to inBlock
			while( lineNum < len(inBuf) and not foundSectionHeadingEnd ):
				if( isLineBlank(inBuf[lineNum]) ):
					foundSectionHeadingEnd = True
				else:
					inBlock.append(inBuf[lineNum])
					lineNum += 1
			
			# Remove two consecutive blank lines that preceed section heading
			outBuf = outBuf[:-2]
		
			# .sp 2
			# .h3 id=section_i
			# Section I.
			# .sp 1             
			sectionID = formatAsID(inBlock[0])
			sectionLine = ""
			for line in inBlock:
				sectionLine += line
				sectionLine += "|"
			sectionLine = sectionLine[:-1]
			
			logging.debug("Found section heading: " + sectionLine)

			outBlock.append("// ******** PPPREP GENERATED ****************************************") 
			outBlock.append(".sp 2")
			outBlock.append(".h3 id=" + sectionID )             
			outBlock.append(sectionLine)
			outBlock.append(".sp 1")

			# Write out original as a comment
			outBlock.append(".ig  // *** PPPREP BEGIN ORIGINAL ***********************************") 
			outBlock.append("") 
			outBlock.append("") 
			for line in inBlock:
				outBlock.append(line)
			outBlock.append(".ig- // *** END *****************************************************")
				
			# Write out chapter heading block
			for line in outBlock:
				outBuf.append(line)
			
			# Log action
			print("  .h3 " + sectionID)
		else:
			if( isLineBlank(inBuf[lineNum]) ):
				consecutiveEmptyLineCount += 1
			else:
				consecutiveEmptyLineCount = 0

			outBuf.append(inBuf[lineNum])
			lineNum += 1

	return outBuf;
	
	
def processIllustrations( inBuf, doBoilerplate ):
	# Build dictionary of images
	files = sorted(glob.glob("images/*"))
	
	logging.info("--- Processing illustrations")
	logging.info("------ Scanning /image folder")

	# Build dictionary of illustrations in images folder
	illustrations = {}
	for f in files:
		try:
			img = Image.open(f)
			img.load()
		except:
			logging.critical("Unable to load image: " + f)

		m = re.match(r"images/i_([^\.]+)", f)
		if( m ):        
			scanPageNum = m.group(1)
			anchorID = "i"+scanPageNum
			caption = ""    
			f = re.sub(r"images/", "", f)
			illustrations[scanPageNum] = ({'anchorID':anchorID, 'fileName':f, 'scanPageNum':scanPageNum, 'dimensions':img.size, 'caption':caption })
			logging.debug("Adding image '" + f + "' " + str(img.size))
		else:
			logging.warning("Skipping file '" + f + "' does not match expected naming convention")

	# Find and replace [Illustration: caption] markup
	outBuf = []
	lineNum = 0
	currentScanPage = 0
		
	logging.info("------ Processing [Illustration] tags")

	while lineNum < len(inBuf):
		# Keep track of active scanpage
		m = re.match(r"\/\/ (\d+)\.png", inBuf[lineNum])
		if( m ):
			currentScanPage = m.group(1)

		# Copy until next illustration block
		if( re.match(r"^\[Illustration", inBuf[lineNum]) ):
			inBlock = []
			outBlock = []
		
			# Copy illustration block
			inBlock.append(inBuf[lineNum])
			while( lineNum < len(inBuf)-1 and not re.search(r"]$", inBuf[lineNum]) ):
				lineNum += 1
				inBlock.append(inBuf[lineNum])
			
			lineNum += 1
			
			# Convert to ppgen illustration block
            # .il id=i_001 fn=i_001.jpg w=600 alt=''
            # .ca SOUTHAMPTON BAR IN THE OLDEN TIME.
			try:
				outBlock.append( ".il id=i" + currentScanPage + " fn=" +  illustrations[currentScanPage]['fileName'] + " w=" + str(illustrations[currentScanPage]['dimensions'][0]) + " alt=''" )
			except KeyError:
				logging.critical("No image file for illustration located on scan page " + currentScanPage + ".png");
			
			captionLine = ""
			for line in inBlock:
				line = re.sub(r"^\[Illustration: ", "", line)
				line = re.sub(r"^\[Illustration", "", line)
				line = re.sub(r"]$", "", line)
				captionLine += line
				captionLine += "<br/>"

			outBlock.append( ".ca " + captionLine );
			
			# Write out ppgen illustration block
			for line in outBlock:
				outBuf.append(line)
				
			if( doBoilerplate ):
				# Write out boilerplate code for HTML version as comment in case .il is not sufficient
				outBuf.append(".ig  // *** PPPREP BEGIN **************************************************************")
				outBuf.append("// ******** Alternative inline HTML version for use when .il .ca are insufficient *****") 
				outBuf.append(".if h")
				outBuf.append(".de .customCSS { clear:left; float:left; margin:4% 4% 4% 0; }")
				outBuf.append(".li")
				outBuf.append("<div class='customCSS'>")
				outBuf.append("<img src='" + illustrations[currentScanPage]['fileName'] + "' alt='' />")
				outBuf.append("</div>")
				outBuf.append(".li-")
				outBuf.append(".if-")
				outBuf.append(".if t")
				for line in inBlock:
					outBuf.append(line)
				outBuf.append(".if-")           
				outBuf.append(".ig- // *** END ***********************************************************************")
			
			logging.debug("Line " + str(lineNum) + ": ScanPage " + str(currentScanPage) + ": convert " + str(inBlock))

		else:
			outBuf.append(inBuf[lineNum])
			lineNum += 1
	
	return outBuf;
		
			
def loadFile(fn):
	inBuf = []
	encoding = ""
	
	if not os.path.isfile(fn):
		logging.critical("specified file {} not found" + format(fn))

	if encoding == "":
		try:
			wbuf = open(fn, "r", encoding='ascii').read()
			encoding = "ASCII" # we consider ASCII as a subset of Latin-1 for DP purposes
			inBuf = wbuf.split("\n")
		except Exception as e:
			pass

	if encoding == "":
		try:
			wbuf = open(fn, "rU", encoding='UTF-8').read()
			encoding = "utf_8"
			inBuf = wbuf.split("\n")
			# remove BOM on first line if present
			t = ":".join("{0:x}".format(ord(c)) for c in inBuf[0])
			if t[0:4] == 'feff':
				inBuf[0] = inBuf[0][1:]
		except:
			pass

	if encoding == "":
		try:
			wbuf = open(fn, "r", encoding='latin_1').read()
			encoding = "latin_1"
			inBuf = wbuf.split("\n")
		except Exception as e:
			pass

	if encoding == "":
		fatal("Cannot determine input file decoding")
	else:
		# self.info("input file is: {}".format(encoding))
		if encoding == "ASCII":
			encoding = "latin_1" # handle ASCII as Latin-1 for DP purposes

	for i in range(len(inBuf)):
		inBuf[i] = inBuf[i].rstrip()

	return inBuf;
	
	
def createOutputFileName( infile ):
	outfile = infile.split('.')[0] + "-src.txt"
	return outfile


def main():
	args = docopt(__doc__, version='ppprep 0.1')

	# Process required command line arguments
	outfile = createOutputFileName( args['<infile>'] )
	if( args['<outfile>'] ):
		outfile = args['<outfile>']
		
	infile = args['<infile>']

	# Open source file and represent as an array of lines
	inBuf = loadFile( infile )

	# Process optional command line arguments
	doBoilerplate = args['--boilerplate'];
	doChapterHeadings = args['--chapters'];
	doSectionHeadings = args['--sections'];
	doIllustrations = args['--illustrations'];
	doPages = args['--pages'];
	
	# Default to --all if no other processing options set
	if( not doChapterHeadings and \
		not doSectionHeadings and \
		not doIllustrations and \
		not doPages or \
		args['--all'] ):
		doIllustrations = True;
		doPages = True;
			
	# Configure logging
	logLevel = logging.INFO #default
	if( args['--verbose'] ):
		logLevel = logging.DEBUG
	elif( args['--quiet'] ):
		logLevel = logging.ERROR
		
	logging.basicConfig(format='%(levelname)s: %(message)s', level=logLevel)
			
	logging.debug(args)
			
	# Process source document
	logging.info("Processing '" + infile + "' to '" + outfile + "'")
	outBuf = []
	if( doPages or doIllustrations ): # Illustration process requires // 001.png format
		outBuf = processPageNumbers( inBuf )
		inBuf = outBuf
	if( doChapterHeadings or doSectionHeadings ):
		outBuf = processHeadings( inBuf, doChapterHeadings, doSectionHeadings )
		outBuf = processHeadings( inBuf, doChapterHeadings, doSectionHeadings )
		inBuf = outBuf
	if( doPages ):
		outBuf = processBlankPages( inBuf )
		inBuf = outBuf
	if( doIllustrations ):
		outBuf = processIllustrations( inBuf, doBoilerplate )
		inBuf = outBuf

	# Save file
	f = open(outfile,'w')
	for line in outBuf:
		f.write(line+'\n')
	f.close()
	
	return


if __name__ == "__main__":
	main()
