#!/bin/bash
costs=("1.0" "1.5"  "2.0")

prefix_str=""
if [[ $1 ]]
then
    prefix_str="--prefix=$1"
fi

# python main.py --multipass --cost-exponent=-3 --max-tasks=1000 --policy=weighted_tsp $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
# python main.py --multipass --cost-exponent=-2 --max-tasks=1000 --policy=batch_tsp $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
python main.py --multipass --cost-exponent=-1 --max-tasks=1000 --policy=tsp $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
for i in ${costs[*]}; do
    python main.py --multipass --cost-exponent=$i --max-tasks=1000 --policy=quad_wait_tsp $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
done
