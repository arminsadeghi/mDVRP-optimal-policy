#!/bin/bash
etas=("0.05" "0.2")
# lambs=("0.6" "0.7" "0.8" "0.85" "0.9" "0.95" "0.97")
# given a 30 minute service time
lambs=('0.0002777777777777778' '0.0003333333333333333' '0.00038888888888888887' '0.00044444444444444447' '0.0005')
seeds=("6983" "42" "520" "97" "29348" "935567" "7")
tasks=3000
total_tasks=3500
initial_tasks=5
policy="lkh_batch_trp_time"
sectors=("1")
cost_exponent=("1.5")
data_source='data/montreal_nord-2017_2019-2500-1.clustered.csv'
max_initial_wait=1000
service_time=1800
tick_time=15

prefix_str=""
if [[ $1 ]]
then
    prefix_str="--prefix=$1"
    shift
fi


# while (( "$#" )); do
    # l=$1
    for l in ${lambs[*]}; do
        echo working on $l...
        for ce in ${cost_exponent[*]}; do
            for s in ${seeds[*]}; do
                for a in ${etas[*]}; do
                    python main.py --multipass --tick-time $tick_time --cost-exponent=$ce --eta=$a --eta-first --max-tasks=$tasks --total-tasks=$total_tasks --initial-tasks $initial_tasks --max-initial-wait $max_initial_wait  --lambd=$l --seed=$s --policy=$policy $prefix_str --service-time $service_time --generator data_loader --data-source $data_source  > /dev/null 2>&1 &
                done
            done
            wait
        done
    done
    # shift
# done














