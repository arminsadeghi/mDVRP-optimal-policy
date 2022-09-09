#!/bin/bash
etas=("0.3" "0.5" "0.8" "1.0")

prefix_str=""
if [[ $1 ]]
then
    prefix_str="--prefix=$1"
fi

for a in ${etas[*]}; do
    python main.py --multipass --cost-exponent=-2.0 --eta=$a --max-tasks=1000 --policy=tsp $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
done
