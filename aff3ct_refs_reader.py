#!/usr/bin/env python3
import numpy as np

class aff3ctRefsReader:
	NoiseLegendsList = { "ebn0" : "Eb/N0", # Signal noise ration view from info bits
	                     "esn0" : "Es/N0", # SNR view from sent symbols
	                     "rop"  : "ROP",   # Received optical power
	                     "ep"   : "EP"     # Event probability
	                   }
	NoiseUnitsList   = { "ebn0" : "dB",
	                     "esn0" : "dB",
	                     "rop"  : "",
	                     "ep"   : ""
	                   }
	BferLegendsList  = {"be_rate" : "BER", # Bit error rate
	                    "fe_rate" : "FER", # Frame error rate
	                    "n_be"    : "BE",  # Number of bit errors
	                    "n_fe"    : "FE",  # Number of frame errors
	                    "n_fra"   : "FRA"  # Number of frame played
	                   }
	MiLegendsList    = {"n_trials" : "TRIALS", # number of frame played
	                    "mi"       : "MI",     # Mutual information average
	                    "mi_min"   : "MIN",    # minimum got MI
	                    "mi_max"   : "MAX"     # maximum got MI
	                   }
	TimeLegendsList  = { "sim_thr" : ["SIM_THR", "SIM_CTHR"], # simulation throughput
	                     "el_time" : "ET/RT"    # elapsed time
	                   }
	TimeUnitsList    = { "sim_thr" : "Mb/s",
	                     "el_time" : "hhmmss"
	                   }


	# aff3ctOutput must be a filename string object or
	# the content of a file stocked in a list object with one line of the file per line of the table
	# else raise a ValueError exception
	def __init__(self, aff3ctOutput):
		self.Metadata   = {'command': '', 'title': ''}
		self.SimuHeader = [] # simulation header
		self.Legend     = [] # keys of BferLegendsList or MiLegendsList
		self.NoiseType  = "" # key of NoiseLegendsList
		self.Trace      = {} # all trace informations with key as in Legend array
		                     #  and as value a list to represent the column of data

		if type(aff3ctOutput) is str: # then a filename has been given
			self.Metadata['filename'] = aff3ctOutput
			aff3ctOutput = self.__fileReader(aff3ctOutput)
		elif type(aff3ctOutput) is list: # then the file content has been given
			pass
		else:
			raise ValueError("Input is neither a str nor a list object")


		traceVersion = self.__detectTraceVersion(aff3ctOutput)
		if traceVersion == 0:
			self.__reader0(aff3ctOutput)
		elif traceVersion == 1:
			self.__reader1(aff3ctOutput)

	def legendKeyAvailable(self, key):
		return key in self.Trace and len(self.Trace[key]) != 0

	def getMetadataAsString(self):
		header = "[metadata]\n"
		for key in self.Metadata:
			header += key + "=" + self.Metadata[key] + "\n"

		header += "\n[trace]\n"

		return header

	def __fileReader(self, filename):
		# read all the lines from the given file
		aFile = open(filename, "r")
		lines = []
		for line in aFile:
			lines.append(line)
		aFile.close()

		return lines;

	def __checkLegend(self, legendTable, colName):

		for key in legendTable:
			if type(legendTable[key]) is list:
				for i in range(len(legendTable[key])):
					if legendTable[key][i] == colName:
						return key

			elif legendTable[key] == colName:
				return key

		return ""

	def __getMatchingLegend(self, colName):

		key = self.__checkLegend(self.NoiseLegendsList, colName)
		if key != "":
			return key

		key = self.__checkLegend(self.BferLegendsList, colName)
		if key != "":
			return key

		key = self.__checkLegend(self.MiLegendsList, colName)
		if key != "":
			return key

		key = self.__checkLegend(self.TimeLegendsList, colName)
		if key != "":
			return key

		return colName

	def __fillLegend(self, line):
		line = line.replace("#", "")
		line = line.replace("||", "|")
		line = line.split('|')

		for i in range(len(line)):
			line[i] = self.__getMatchingLegend(line[i].strip())

		self.Legend = line

	def __findLine(self, stringArray, string):
		for i in range(len(stringArray)):
			if string in stringArray[i]:
				return i

		return -1

	def __getLegendIdx(self, colName):
		for i in range(len(self.Legend)):
			if self.Legend[i] == colName:
				return i
		return -1

	def __getVal(self, line):
		line = line.replace("#", "")
		line = line.replace("||", "|")
		line = line.split('|')

		valLine = []
		for i in range(len(line)):
			val = float(0.0)

			try:
				val = float(line[i])

				if "inf" in str(val):
					val = float(0.0)

			except ValueError:
				pass

			valLine.append(val)

		return valLine

	def __detectTraceVersion(self, aff3ctOutput):
		if aff3ctOutput[0].startswith("[metadata]"):
			return 1

		if aff3ctOutput[0].startswith("Run command:"):
			return 0

		return 0

	def __reader1(self, aff3ctOutput):
		startMeta  = False;
		startTrace = False;
		allTrace   = []

		for line in aff3ctOutput:
			if line.startswith("[metadata]"):
				startMeta = True;
				continue

			if line.startswith("[trace]"):
				startTrace = True;
				startMeta = False;
				continue

			if startMeta:
				vals = line.split('=', 1);
				if len(vals) == 2:
					self.Metadata[vals[0]] = vals[1].strip();

			elif startTrace:
				if line.startswith("#"):
					if len(line) > 3 and line[0] == '#' and line[2] == '*':
						entry = line.replace("# * ", "").replace("\n", "").split(" = ")
						if len(entry) == 1:
							entry[0] = entry[0].replace("-", "")
						self.SimuHeader.append(entry)

					elif len(line) > 7 and line[0] == '#' and line[5] == '*' and line[6] == '*':
						entry = line.replace("#    ** ", "").replace("\n", "").split(" = ")
						self.SimuHeader.append(entry)

					elif len(line) > 6 and line[0] == '#' and line[1] == ' ' and line[2] == ' ' and line[3] == ' ' and line[4] == ' ' and line[5] != ' ' and line[5] != '*':
						entry = line.replace("#    ", "*").replace("\n", "").split(" = ")
						if len(entry) == 1:
							entry[0] = entry[0].replace("-", "")
						self.SimuHeader.append(entry)

					elif len(line) > 20:
						if(   line.find(self.BferLegendsList["be_rate"]) != -1
						  and line.find(self.BferLegendsList["fe_rate"]) != -1
						  and line.find(self.BferLegendsList["n_fra"  ]) != -1):
							self.__fillLegend(line)

						elif( line.find(self.MiLegendsList["n_trials"]) != -1
						  and line.find(self.MiLegendsList["mi"      ]) != -1):
							self.__fillLegend(line)
				else:
					if len(self.Legend) != 0:
						d = self.__getVal(line)
						if len(d) == len(self.Legend):
							allTrace.append(d)


		allTrace = np.array(allTrace).transpose()


		# fill trace
		for i in range(len(self.Legend)):
			self.Trace[self.Legend[i]] = allTrace[i]


		# find the type of noise used in this simulation
		idx = -1
		for n in self.NoiseLegendsList:
			idx = self.__getLegendIdx(self.NoiseLegendsList[n])
			if idx != -1:
				self.NoiseType = n
				break

	def __reader0(self, aff3ctOutput):
		startMeta  = False;
		startTrace = False;
		allTrace   = []

		for line in aff3ctOutput:
			if line.startswith("#"):
				if len(line) > 3 and line[0] == '#' and line[2] == '*':
					entry = line.replace("# * ", "").replace("\n", "").split(" = ")
					if len(entry) == 1:
						entry[0] = entry[0].replace("-", "")
					self.SimuHeader.append(entry)

				elif len(line) > 7 and line[0] == '#' and line[5] == '*' and line[6] == '*':
					entry = line.replace("#    ** ", "").replace("\n", "").split(" = ")
					self.SimuHeader.append(entry)

				elif len(line) > 6 and line[0] == '#' and line[1] == ' ' and line[2] == ' ' and line[3] == ' ' and line[4] == ' ' and line[5] != ' ' and line[5] != '*':
					entry = line.replace("#    ", "*").replace("\n", "").split(" = ")
					if len(entry) == 1:
						entry[0] = entry[0].replace("-", "")
					self.SimuHeader.append(entry)

				elif len(line) > 20:
					if(   line.find(self.BferLegendsList["be_rate"]) != -1
					  and line.find(self.BferLegendsList["fe_rate"]) != -1
					  and line.find(self.BferLegendsList["n_fra"  ]) != -1):
						self.__fillLegend(line)

					elif( line.find(self.MiLegendsList["n_trials"]) != -1
					  and line.find(self.MiLegendsList["mi"      ]) != -1):
						self.__fillLegend(line)
			else:
				if len(self.Legend) != 0:
					d = self.__getVal(line)
					if len(d) == len(self.Legend):
						allTrace.append(d)


		allTrace = np.array(allTrace).transpose()


		# get the command to reproduce this trace
		idx = self.__findLine(aff3ctOutput, "Run command:")
		if idx != -1 and len(aff3ctOutput) >= idx +1:
			self.Metadata['command'] = str(aff3ctOutput[idx +1].strip())

		# get the curve name (if there is one)
		idx = self.__findLine(aff3ctOutput, "Curve name:")
		if idx != -1 and len(aff3ctOutput) >= idx +1:
			self.Metadata['title'] = str(aff3ctOutput[idx +1].strip())


		# fill trace
		for i in range(len(self.Legend)):
			self.Trace[self.Legend[i]] = allTrace[i]


		# find the type of noise used in this simulation
		idx = -1
		for n in self.NoiseLegendsList:
			idx = self.__getLegendIdx(self.NoiseLegendsList[n])
			if idx != -1:
				self.NoiseType = n
				break