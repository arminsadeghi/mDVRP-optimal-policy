#!/bin/bash
costs=("1.0" "1.5" "2.0")
etas=("0.3" "0.5" "0.8" "1.0")

prefix_str=""
if [[ $1 ]]
then
    prefix_str="--prefix=$1"
fi

for a in ${etas[*]}; do
    for c in ${costs[*]}; do
        python main.py --multipass --cost-exponent=$c --eta=$a --gamma=0.95 --max-tasks=1000 --policy=hybrid $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
        python main.py --multipass --cost-exponent=$c --eta=$a --eta-first --gamma=0.95 --max-tasks=1000 --policy=hybrid $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
    done
done
