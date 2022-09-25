# LKH-3

A lightly modified copy of the [LKH-3](http://webhotel4.ruc.dk/~keld/research/LKH-3/) included here for convenience.  For reference, please see the following report:

 > K. Helsgaun,
 > An Extension of the Lin-Kernighan-Helsgaun TSP Solver for Constrained Traveling Salesman and Vehicle Routing Problems.
 > Technical Report, Roskilde University, 2017.


Please note that the code is distributed for academic and non-commercial use. The author reserves all rights to the code.

## Modifications

Penalty_TRP.cpp function has been modified to support our cost function, raising each of the waiting times by a fixed exponent (1.5):

```c++
  double service_time = 0;
  int existing_wait = 0;
  if (NextN->Id <= Dim) {
    service_time = NextN->ServiceTime;
    existing_wait = NextN->Demand;
  } else {
    assert(NextN->FixedTo1->Id <= Dim);
    service_time = NextN->FixedTo1->ServiceTime;
    existing_wait = NextN->FixedTo1->Demand;
  }
  DistanceSum += service_time / Precision;
  P += pow(DistanceSum + existing_wait / Precision, 1.5);
```
