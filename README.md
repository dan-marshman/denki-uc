# Denki-UC
A stochastic unit commitment model in python - still in development

# Installation
Clone and install using
```
$ git clone https://github.com/dan-marshman/denki-uc
$ cd denki-uc
$ python setup.py install
```
Test the package using
```
$ python main.py
```
This will run a test set of input data, contained in '/examples/test1'. Results files are written as .csv files in the directory 'denki-outputs' by default.

# Basic Usage
This module runs a unit commitment simulation by calling an instance of a ucModel from uc_model.py, which takes two arguments
1. The name of your simulation - a string, and;
2. The path to the data directory to be used for the simulation, (the path may be relative or absolute).
'path_to_inputs' should contain all input data (e.g. electricity demand, generating unit data, etc), and a 'settings.csv', which controls how the model behaves.
```
import denkiuc.uc_model as uc

yourModel = uc.ucModel(name=model_name, path_to_inputs=some_path)
```
Generating an instance of ucModel will build the model, but not yet solve it - as solving can take a long time depending on the model complexity, and to allow some input parameters to be altered prior to solve, if desired.  To solve the model, use the 'solve()' method, i.e.
```
yourModel.solve()
```
This will solve the UC optimisation problem (assuming the input data is such that the model is feasible), and write outputs 'outputs_folder\your_model_name\results', where the outputs_folder is specified in the 'settings.csv' file within 'settings.csv'.
## Overview of input files
Within the 'examples' folder are example input data collections.
### settings.csv
This contains a number of parameters, which control how the simulation behaves.  For example, UC constraints may be turned on or off, and the penalty on unserved load/reserves/inertia may be set.
The example file specifies the type of each parameters (e.g. string, integer, boolean, etc), and also gives a short description. Only the 'Value' column should be changed.
### demand.csv
Electricity demand (MW) in each interval. The interval column is used to specify the set of all intervals, and should be consecutive, but need not start at 0 or 1. 
### wind.csv and solarPV.csv
Traces for wind and solar units, specified as a fraction of capacity (i.e. between 0 and 1) in each interval.  Intervals should be consistent with those in demand.csv
### unit_data.csv
The Unit column is used to create the set of units.  Remaining fields specify a number of (mostly self-explanatory) fields for each unit - though some may not be relevant, and are set to 0 or 1 (.e.g. thermal efficiency is not relevant to wind/solarPV units).  The Technology specifies the types of technologies which a unit is.  Therefore a Unit with Technology set to 'Wind' would be treated as a wind unit (even if called Coal!).
### initial_state.csv
This specifies the initial state of the system, immediately prior to the first interval.  For thermal units, it specifies their initial commitment status, and current operating point (e.g. megawatts of power being generated). Storage units have their storage level specified (as a fraction of total storage capacity).
# Detailed documentation
Coming soon
