#!/bin/bash
etas=("0.2" "0.5")
# lambs=("0.6" "0.7" "0.8" "0.85" "0.9" "0.95" "0.97")
lambs=("0.9")
seeds=("21" "6983" "42" "520" "97" "29348" "935567")

prefix_str=""
if [[ $1 ]]
then
    prefix_str="--prefix=$1"
fi

for s in ${seeds[*]}; do
    for l in ${lambs[*]}; do
        # python main.py --multipass --cost-exponent=-6.0 --eta=1.0  --max-tasks=1000 --initial-tasks=100 --policy=random_assgn_with_return  $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
        # python main.py --multipass --cost-exponent=-2.0 --eta=1.0  --max-tasks=10000 --total-tasks=20000 --initial-tasks=250 --lambd=$l --policy=lkh_batch_tsp $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
        # python main.py --multipass --cost-exponent=-2.0 --eta=1.0  --max-tasks=2000 --total-tasks=5000 --initial-tasks=250 --lambd=$l  --policy=batch_tsp $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
        for a in ${etas[*]}; do
           # python main.py --multipass --cost-exponent=-5.0 --eta=$a --max-tasks=10000 --total-tasks=20000 --initial-tasks=250 --lambd=$l  --policy=lkh_batch_tsp $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
           python main.py --multipass --cost-exponent=-5.0 --eta=$a --eta-first --max-tasks=10000 --total-tasks=20000 --initial-tasks=250 --lambd=$l --seed=$s --policy=lkh_batch_trp $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
           # python main.py --multipass --cost-exponent=-5.0 --eta=$a  --eta-first --max-tasks=10000 --total-tasks=20000 --initial-tasks=250 --lambd=$l --policy=lkh_batch_trp $prefix_str --service-time 1 --generator uniform  > /dev/null 2>&1 &
        done
    done
done