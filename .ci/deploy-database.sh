#!/bin/bash
# This script get all the text files contained in the $ROOT folder
# It concatenates all the text files in the $RESULT file
# To launch the script use "./deploy-database.sh $ROOT $RESULT"
# Each concatenated file begin by $startFile and end by $endFile
# The $ROOT sub folder are also parsed

set -x

if [ -z "$1" ]; then
  ROOT=./error_rate_references-master
else
  ROOT="$1"
fi

if [ -z "$2" ]; then
  OUTPUT='database.txt'
else
  OUTPUT="$2"
fi

startFile='Start_File'
endFile='End_File'

function directory
{
	for element in `ls $1`
	do
		if [ -d "$1/$element" ]
		then
			if [[ ( "$element" != "readers" ) ]] # skip the folder named "readers"
			then
				echo -e "$1/$element\n" >> $OUTPUT
				directory "$1/$element"
			fi
		else
			echo -e "$1/$element:\n" >> $OUTPUT
			echo -e "$startFile\n" >> $OUTPUT
			cat "$1/$element" >> $OUTPUT
			echo -e "$endFile\n" >> $OUTPUT
		fi
	done
}

echo -e "" > $OUTPUT
directory $ROOT