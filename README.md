# mDVRP

## A study of allocation and scheduling for the Dynamic Vehicle Routing Problem

<p align="center">
  <img src="./docs/montreal_six.gif">
</p>

The optimal policy for the mDVRP problem for any arrival rate.  Task generation is controlled by selecting a generator function in *scripts/generators*.  The policy followed is selected from *scripts/policies*.

## Preliminaries

This application makes use of the LKH-3.x solver which must be compiled before running the main program.  Full source and build files are found in thirdParty/lkh.

Python 3.8 or later is recommended.

## How to run:

To run the application, run
```bash
$ python main.py \<args\>
```

where \<args\> specifies the main parameters for each simulation run.  

For exmaple, to simulate servicing 1000 tasks, each with an arrival rate of 0.8 and a 1s mean service time, in a uniform 1x1 environment, using the TSP solver
```bash
$ python main.py --show-sim --max-tasks 1000 --policy lkh_batch_tsp --lambd 0.8 --service-tim 1 --generator uniform
```

There is a configuration file, *config.py*, that allows access to some additional settings.  Please note that the simulation is significanly faster if animation is disabled (remove '--show-sim' from the above).




