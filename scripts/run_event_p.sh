#!/bin/bash
etas=("1.0")
# lambs=("0.6" "0.7" "0.8" "0.85" "0.9" "0.95" "0.97")
# lambs=("0.95" "0.97")
seeds=("6983" "42" "520" "97" "29348" "935567")
tasks=3000
total_tasks=3500
policy="quad_wait_tsp"
cost_exponent=1.1

prefix_str=""
if [[ $1 ]]
then
    prefix_str="--prefix=$1"
    shift
fi


while (( "$#" )); do
    l=$1
    for s in ${seeds[*]}; do
        for a in ${etas[*]}; do
            python main.py --multipass --cost-exponent=$cost_exponent --eta=$a  --max-tasks=$tasks --total-tasks=$total_tasks --lambd=$l --seed=$s --policy=$policy $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
        done
    done
    echo working on $l
    python main.py --multipass --cost-exponent=$cost_exponent --eta=1.0 --max-tasks=$tasks --total-tasks=$total_tasks --lambd=$l --seed=21 --policy=$policy $prefix_str --service-time 1 --generator uniform > /dev/null 2>&1
    echo done
    shift
done
