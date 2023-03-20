#include "LKH.h"
#include "Segment.h"
#include <math.h>
#include <assert.h>
#include <stdio.h>

GainType Penalty_TRP() {
  static Node *StartRoute = 0;
  Node *N, *NextN, *CurrentRoute;
  ;
  GainType P = 0, DistanceSum;
  int Forward = SUCC(Depot)->Id != Depot->Id + DimensionSaved;

  if (!StartRoute)
    StartRoute = Depot;
  if (StartRoute->Id > DimensionSaved)
    StartRoute -= DimensionSaved;
  N = StartRoute;
  do {
    CurrentRoute = N;
    DistanceSum = 0;
    do {
      NextN = Forward ? SUCC(N) : PREDD(N);
      if (N->Id <= Dim || N->DepotId) {
        if (NextN->DepotId == 0) {
          DistanceSum += (C(N, NextN) - N->Pi - NextN->Pi) / Precision;
          GainType service_time = 0;
          GainType existing_wait = 0;
          if (NextN->Id <= Dim) {
            service_time = NextN->ServiceTime;
            existing_wait = NextN->Demand;
          } else {
            assert(NextN->FixedTo1->Id <= Dim);
            service_time = NextN->FixedTo1->ServiceTime;
            existing_wait = NextN->FixedTo1->Demand;
          }
          DistanceSum += service_time / Precision;

          // TODO: RiskThreshold has been repurposed to allow passing in the cost exponent (way better than hard coding it)
          //       but at some point, should be given it's own variable (but that requires rework all the way up to the
          //       python interface.  That's going to have to wait...
          double exponent = RiskThreshold != 0 ? (RiskThreshold / 10.0) : 1.0;
          GainType oldP = P;
          P += pow(DistanceSum + existing_wait / Precision, exponent);
          if( P < oldP ) {
            printf("ERROR -- WRAPPED P: %lld, OLD_P: %lld, Exponent: %f\n", P, oldP, exponent );
            assert( P >= oldP );
          }

          if (P > CurrentPenalty || (P == CurrentPenalty && CurrentGain <= 0)) {
            StartRoute = CurrentRoute;
            return CurrentPenalty + (CurrentGain > 0);
          }
          if (DistanceSum > DistanceLimit &&
              ((P += DistanceSum - DistanceLimit) > CurrentPenalty ||
               (P == CurrentPenalty && CurrentGain <= 0))) {
            StartRoute = CurrentRoute;
            return CurrentPenalty + (CurrentGain > 0);
          }
        }
      }
      N = Forward ? SUCC(NextN) : PREDD(NextN);
    } while ((N = NextN)->DepotId == 0);
  } while (N != StartRoute);
  return P;
}
