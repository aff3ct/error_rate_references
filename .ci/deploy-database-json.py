#!/usr/bin/env python3

import os
import re
import json
import hashlib
import pathlib
import argparse

parser = argparse.ArgumentParser(prog='deploy-database-json', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--refs-path', action='store', dest='refsPath', type=str,  default="./",            help='Path to the reference files.')
parser.add_argument('--output',    action='store', dest='output',   type=str,  default="database.json", help='Path to the concatenated files.')
parser.add_argument('--nice-json', action='store', dest='niceJson', type=bool, default=False,           help='Beautiful JSON indentation.')

# supported file extensions (filename suffix)
extensions = ['.txt', '.perf', '.data', '.dat']

def getFileNames(currentPath, fileNames):
	if os.path.isdir(currentPath):
		files = os.listdir(currentPath)
		for f in files:
			if "~" in f or f.startswith("."):
				continue
			newCurrentPath = currentPath + "/" + f
			getFileNames(newCurrentPath, fileNames)
	elif os.path.isfile(currentPath):
		if pathlib.Path(currentPath).suffix in extensions:
			if args.refsPath == currentPath:
				basename = os.path.basename(args.refsPath)
				dirname = args.refsPath.replace(basename, '')
				args.refsPath = dirname
				fileNames.append(basename)
			else:
				shortenPath = currentPath.replace(args.refsPath + "/", "")
				shortenPath = shortenPath.replace(args.refsPath,       "")
				fileNames.append(shortenPath)
	else:
		print("# (WW) The path '", currentPath, "' does not exist.")

# read all the lines from the given file and set them in a list of string lines with striped \n \r
def readFileInTable(filename):
	aFile = open(filename, "r")
	lines = []
	for line in aFile:
		line = re.sub('\r','',line.rstrip('\n'))
		if len(line) > 0:
			lines.append(line)
	aFile.close()

	return lines;

def getHashFromFile(filename):
	BLOCKSIZE = 65536
	hasher = hashlib.sha1()
	with open(filename, 'rb') as afile:
	    buf = afile.read(BLOCKSIZE)
	    while len(buf) > 0:
	        hasher.update(buf)
	        buf = afile.read(BLOCKSIZE)
	return hasher.hexdigest()

args = parser.parse_args()
fileNames = []
getFileNames(args.refsPath, fileNames)

id = 0;
aList = [];
for fn in fileNames:
	hash = getHashFromFile(args.refsPath + "/" + fn)
	smallHash = hash[0:7]
	dict = {"id" : id, "filename" : fn, "hash" : hash, "shash" : smallHash}

	sfn = readFileInTable(args.refsPath + "/" + fn)

	ln = 0
	isTrace = False
	trace = ""
	metadata = {"ci": True}
	titleSec = ""
	dictHeaders = {}
	dictSec = {}
	for l in sfn:
		if ln == 0 and l != "[metadata]":
			break
		if l == "[trace]":
			isTrace = True
			ln = ln + 1
			continue

		if not isTrace:
			ls = l.split("=", 1)
			if len(ls) == 2:
				if ls[1] == "on":
					metadata[ls[0]] = True
				elif ls[1] == "off":
					metadata[ls[0]] = False
				else:
					metadata[ls[0]] = ls[1]
		else:
			if len(metadata) > 0:
				dict["metadata"] = metadata;
				metadata = {}
			trace += l + "\n";

			if l.startswith("# *"):
				if titleSec != "":
					dictHeaders[titleSec] = dictSec;
					dictSec = {}
				titleSec = l[4:].split(" -",1)[0]
			elif l.startswith("#    **"):
				cleanL = l[8:]
				splitL = cleanL.split(" = " , 1)
				if len(splitL) == 2:
					if (splitL[1] == "yes") or (splitL[1] == "on"):
						dictSec[splitL[0].rstrip()] = True;
					elif (splitL[1] == "no") or (splitL[1] == "off"):
						dictSec[splitL[0].rstrip()] = False;
					else:
						try:
							dictSec[splitL[0].rstrip()] = int(splitL[1]);
						except ValueError:
							try:
								dictSec[splitL[0].rstrip()] = float(splitL[1]);
							except ValueError:
								dictSec[splitL[0].rstrip()] = splitL[1];
			elif l.startswith("# The simulation is running..."):
				if titleSec != "":
					dictHeaders[titleSec] = dictSec
					dictSec = {}
					titleSec = ""
					dict["headers"] = dictHeaders


		ln = ln + 1

	if trace != "":
		dict["trace"] = trace
		aList.append(dict)

	id = id + 1

if args.niceJson:
	jsonList = json.dumps(aList, sort_keys=True, indent=4)
else:
	jsonList = json.dumps(aList)

f = open(args.output, "w")
f.write(jsonList)
f.close()