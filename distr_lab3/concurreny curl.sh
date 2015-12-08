#!/bin/bash

# Declare array
declare -a ARRAY
# Link filedescriptor 10 with stdin
exec 10<&0
# stdin replaced with a file supplied as a first argument
exec < $1
let count=0

while read LINE; do

    ARRAY[$count]=$LINE
    ((count++))
done

ELEMENTS=${#ARRAY[@]}

# echo each element in array
for (( i=0;i<$ELEMENTS;i++)); do

  curl -g --request POST ${ARRAY[${i}]}':63147' --data "comment=hej1"
  #curl -g --request POST ${ARRAY[${i}]}':63147' --data "comment=hej2"
  #curl --data "comment=hej1" ${ARRAY[${i}]}:63147
  #curl --data "comment=hej2" ${ARRAY[${i}]}:63147
  #curl --data "comment=hej3" ${ARRAY[${i}]}:63117
  #curl --data "comment=hej4" ${ARRAY[${i}]}:63117

done

#echo Number of elements: ${#ARRAY[@]}
# echo array's content
#echo ${ARRAY[@]}
# restore stdin from filedescriptor 10
# and close filedescriptor 10
exec 0<&10 10<&-
