## Constraints
* Make constraints work for using the minimum up down times based on behaviour in the previous day.

## Sanity checks
* The minimum up/down equations only work if there is only one unit built

## Traces
* Remove region from traces in arma_traces.py file

## Denki series
* Make link for initial state based on previous day, and minimum upd/down time from previous day.
* Check that correct traces are being chosen. Try look_ahead_intervals longer than a day. 
* Add functionality to resolve failed days
