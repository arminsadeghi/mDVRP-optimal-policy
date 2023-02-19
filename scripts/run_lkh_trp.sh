#!/bin/bash
etas=("0.05" "0.2")
# lambs=("0.804634695848085" "0.965561635017702" "1.126488574187319" "1.287415513356936" "1.4483424525265531" )
lambs=("0.5" "0.6" "0.7" "0.8" "0.9")
seeds=("6983" "42" "520" "97" "29348" "935567" "7")
tasks=3000
total_tasks=3500
policy="lkh_cont_trp"
cost_exponents=("1.5")
service_time=1

prefix_str=""
if [[ $1 ]]
then
    prefix_str="--prefix=$1"
    shift
fi


for l in ${lambs[*]}; do
    echo working on $l
    for s in ${seeds[*]}; do
        echo       ... and seed $s
        for ce in ${cost_exponents[*]}; do
            for a in ${etas[*]}; do
                python main.py --multipass --cost-exponent=$ce --eta=$a --eta-first --max-tasks=$tasks --total-tasks=$total_tasks --lambd=$l --seed=$s --policy=lkh_batch_trp $prefix_str --service-time=$service_time --generator uniform  > /dev/null 2>&1 &
            done
        done
        python main.py --multipass --cost-exponent=2.0 --eta=1.0 --max-tasks=$tasks --total-tasks=$total_tasks --lambd=$l --seed=$s --policy=lkh_cont_trp $prefix_str --service-time=$service_time --generator uniform  > /dev/null 2>&1 &
    done
    wait
done
