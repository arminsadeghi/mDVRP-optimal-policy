#!/bin/bash
# etas=("1.0")
# etas=("0.2" "1")
# lambs=("0.804634695848085" "0.965561635017702" "1.126488574187319" "1.287415513356936" "1.4483424525265531" )
lambs=("0.5" "0.6" "0.7" "0.8" "0.9")
seeds=("6983" "42" "520" "97" "29348" "935567" "7")
tasks=3000
total_tasks=3500
policy="lkh_batch_tsp"
# sectors=("2" "4" "10")
sector=10
cost_exponent=-8.0
service_time=1
# centralized="--centralized"

prefix_str=""
if [[ $1 ]]
then
    prefix_str="--prefix=$1"
    shift
fi


# while (( "$#" )); do
#    l=$1
for l in ${lambs[*]}; do
    echo working on $l
    for s in ${seeds[*]}; do
        echo ....seed $s
        # python main.py --multipass --cost-exponent=$cost_exponent --eta=0.2 --sectors=$sector --max-tasks=$tasks --total-tasks=$total_tasks --lambd=$l --seed=$s --policy=$policy $prefix_str --service-time=$service_time --generator uniform  > /dev/null 2>&1 &
        # python main.py --multipass --cost-exponent=$cost_exponent --eta=0.2 --eta-first --sectors=$sector --max-tasks=$tasks --total-tasks=$total_tasks --lambd=$l --seed=$s --policy=$policy $prefix_str --service-time=$service_time --generator uniform  > /dev/null 2>&1 &
        python main.py --multipass --cost-exponent=$cost_exponent --eta=1.0 --sectors=$sector --centralized --max-tasks=$tasks --total-tasks=$total_tasks --lambd=$l --seed=$s --policy=$policy $prefix_str --service-time=$service_time --generator uniform > /dev/null 2>&1 &
    done
    wait
done
