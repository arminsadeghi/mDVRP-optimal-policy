#!/bin/bash
#
# Run this script first to generate data for the other simulations -- also runs the
# baseline full batch tsp
#
lambs=("0.3" "0.4" "0.5" "0.6" "0.7" "0.8" "0.9")
tasks=3000
total_tasks=3500

prefix_str=""
if [[ $1 ]]
then
    prefix_str="--prefix=$1"
fi

for l in ${lambs[*]}; do
    python main.py --multipass --cost-exponent=-2.0 --eta=1.0  --max-tasks=$tasks --total-tasks=$total_tasks --lambd=$l --policy=lkh_batch_tsp $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
done
