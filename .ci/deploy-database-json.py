#!/usr/bin/env python3

import os
import re
import sys
import json
import hashlib
import pathlib
import argparse

parser = argparse.ArgumentParser(prog='deploy-database-json', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--refs-path', action='store', dest='refsPath', type=str,  default="./",            help='Set the path to the reference files.')
parser.add_argument('--output',    action='store', dest='output',   type=str,  default="database.json", help='Set the path to the concatenated files.')
parser.add_argument('--nice-json', action='store', dest='niceJson', type=bool, default=False,           help='Enable the beautiful JSON indentation.')
parser.add_argument('--hash-type', action='store', dest='hashType', type=str,  default="sha1",          help='Set the algorithm used for the hash ("sha1" or "md5").')

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

def getHashFromFile(filename, hashtype = "sha1"):
	if hashtype == "sha1":
		hasher = hashlib.sha1()
	elif hashtype == "md5":
		hasher = hashlib.md5()
	else:
		print("(EE) The hash type '" + hashtype + "' is not supported, supported types are 'sha1' and 'md5'.", file=sys.stderr)
		sys.exit(1);

	blocksize = 65536
	with open(filename, 'rb') as afile:
		buf = afile.read(blocksize)
		while len(buf) > 0:
			hasher.update(buf)
			buf = afile.read(blocksize)
	return hasher.hexdigest()

args = parser.parse_args()
fileNames = []
getFileNames(args.refsPath, fileNames)
hashList = []
shashList = []
bigDict = {};
for fn in fileNames:
	hash = getHashFromFile(args.refsPath + "/" + fn, args.hashType)
	smallHash = hash[0:7]

	if hash in hashList:
		print("(EE) The '"+ hash +"' hash is not unique :-(.", file=sys.stderr)
		sys.exit(1);
	else:
		hashList.append(hash);

	if smallHash in shashList:
		print("(EE) The '"+ smallHash +"' small hash is not unique :-(.", file=sys.stderr)
		sys.exit(1);
	else:
		shashList.append(smallHash);

	dict = {"filename" : fn, "hash" : {"type" : args.hashType, "value" : hash}}

	sfn = readFileInTable(args.refsPath + "/" + fn)

	ln = 0
	isTrace = False
	isLegend = False
	legends = []
	contents = {}
	trace = ""
	metadata = {"ci": True}
	titleSec = ""
	dictHeaders = {}
	dictSec = {}
	for l in sfn:
		if ln == 0 and l != "[metadata]":
			break

		trace += l + "\n";

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

			if l.startswith("# *"):
				if titleSec != "":
					dictHeaders[titleSec] = dictSec;
					dictSec = {}
				titleSec = l[4:].split(" -",1)[0]

			elif l.startswith("#    **"):
				cleanL = l[8:]
				splitL = cleanL.split(" = " , 1)
				if len(splitL) == 2:
					key = splitL[0].rstrip()
					val = splitL[1]
					if key in  ["Code rate", "Bit rate", "Multi-threading (t)"]:
						val = val.split(" ", 1)[0]
					if val in ["yes", "on"]:
						dictSec[key] = True;
					elif val in ["no", "off"]:
						dictSec[key] = False;
					else:
						try:
							dictSec[key] = int(val);
						except ValueError:
							try:
								dictSec[key] = float(val);
							except ValueError:
								dictSec[key] = val;

			elif l.startswith("# The simulation is running..."):
				if titleSec != "":
					dictHeaders[titleSec] = dictSec
					dictSec = {}
					titleSec = ""
					dict["headers"] = dictHeaders

			if not l.startswith("#"):
				if not isLegend:
					isLegend = True
					if ln > 3:
						leg = sfn[ln -3]
						leg = leg.replace("||", "|")
						leg = leg.replace("#", "")
						legends = leg.split("|")

				c = l
				c = c.replace("||", "|")
				cs = c.split("|")

				if len(cs) == len(legends):
					for x in range(len(cs)):
						key = legends[x].strip()
						val = cs[x].strip()
						try:
							li = [int(val)]
						except ValueError:
							try:
								li = [float(val)]
							except ValueError:
								li = [val]

						if key in contents:
							contents[key] = contents[key] + li
						else:
							contents[key] = li

		ln = ln + 1

	if trace != "" and len(contents):
		dict["trace"] = trace
		dict["contents"] = contents;
		bigDict[smallHash] = dict

if args.niceJson:
	jsonList = json.dumps(bigDict, sort_keys=True, indent=4)
else:
	jsonList = json.dumps(bigDict)

f = open(args.output, "w")
f.write(jsonList)
f.close()

sys.exit(0);