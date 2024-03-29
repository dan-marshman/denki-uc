# Denki-UC
A stochastic unit commitment optimisation model, written in python. 

Currently in development.

## Contents
- [Denki-UC](#denki-uc)
  * [Overview](#overview)
  * [Installation](#installation)
  * [Getting started](#getting-started)
    + [Dependencies](#dependencies)
    + [Overview of input files](#overview-of-input-files)
  * [Contributing](#contributing)
  * [Authors & Contributors](#authors---contributors)
  * [License](#license)
    + [Citing this software](#citing-this-software)
  * [Detailed documentation](#detailed-documentation)


## Overview
The unit commitment problem describes the problem of deciding when to turn generating stations on and off, to meet electricity demand.  With increasing variability from renewable generation, these decisions become more complex.

For example, Denki-UC can be be used to study:
* The impact of wind, solar and demand uncertainty on unit commitment decisions.
* Evolution of electricity prices, and market performance in different power systems.
* Impacts on ancillary services - e.g. reserves and inertia, from growing renewables.
* While the model is based on a unit commitment function, it can be used to study generation expansion problems (include with unit commitment constraints, subject to tractability).

For the unit commitment formulation and examples of the package's usage, see the following:
1. [Marshman, D., Brear, M., Jeppesen, M. and Ring, B., 2020. *Performance of wholesale electricity markets with high wind penetration.* Energy Economics, 89, p.104803.](https://www.sciencedirect.com/science/article/pii/S0140988320301432)
2. [Marshman, D., 2018. *Performance of electricity markets & power plant investments in the transition to a low-carbon power system*. Doctoral thesis.](https://minerva-access.unimelb.edu.au/bitstream/handle/11343/222168/Revised%20Thesis.pdf?sequence=1&isAllowed=y)

## Installation
Clone this repo, and then install using
```
$ git clone https://github.com/dan-marshman/denki-uc
$ cd denki-uc
$ python setup.py install
```
Test the package using
```
$ python main.py
```
This will run a test set of input data, viewed in '/examples/test1'. Results files will be written as .csv files in the directory 'denki-outputs' by default.

## Getting started
The module runs a unit commitment simulation by calling a run_opt_problem(name, path) from uc_model.py, which takes two required arguments, and an optional third.
1. The name of your simulation (a string e.g. "MyModel")
2. The path to the input data directory (e.g. 'path\to\inputs')
3. (optional) The path to save the outputs (e.g., 'path\to\outputs')

For example to run an example model (test1), in a python script, execute:
```
import denkiuc.uc_model as uc
import denkiuc.denki_paths
import os

dk_paths = denkiuc.denki_paths.dk_paths
path_to_test1 = os.path.join(<denki_path>, 'test1')
uc.run_opt_problem(name='test1', prob_path=path_to_test1, outputs_path=<your_ouptputs_path>)
```
replacing *<denki_path>* with the path where you cloned the repo, and *<your_ouptputs_path>* to a desired results directory.
This will solve the UC optimisation problem, and write outputs to 'outputs_folder\MyModel\results', with this path being specified in your settings.csv file.
### Overview of the input files
A minimal set of input data is described in this section.Within the 'examples' folder are example input data collections.  
#### settings.csv
This contains a number of parameters, which control how the simulation behaves.  For example, UC constraints may be turned on or off, and the penalty on unserved load/reserves/inertia may be set.
The example file specifies the type of each parameters (e.g. string, integer, boolean, etc), and also gives a short description. Only the 'Value' column should be changed.
#### demand.csv
Electricity demand (MW) in each interval. The interval column is used to specify the set of all intervals, and should be consecutive, but need not start at 0 or 1. 
#### wind.csv and solarPV.csv
Traces for wind and solar units, specified as a fraction of capacity (i.e. between 0 and 1) in each interval.  Intervals should be consistent with those in demand.csv
#### unit_data.csv
The Unit column is used to create the set of units.  Remaining fields specify a number of (mostly self-explanatory) fields for each unit - though some may not be relevant, and are set to 0 or 1 (.e.g. thermal efficiency is not relevant to wind/solarPV units).  The Technology specifies the types of technologies which a unit is.  Therefore a Unit with Technology set to 'Wind' would be treated as a wind unit (even if called Coal!).
#### initial_state.csv
This specifies the initial state of the system, immediately prior to the first interval.  For thermal units, it specifies their initial commitment status, and current operating point (e.g. megawatts of power being generated). Storage units have their storage level specified (as a fraction of total storage capacity).
## Dependencies
* [pandas](https://github.com/pandas-dev/pandas)
* [PuLP](https://github.com/coin-or/pulp)
* [NumPy](https://numpy.org/)
## Contributing
Please see the open issues if you are interested in contributing. As we are in a state of development, there is plenty to do. We are happy to ackowledge all contributors.
## Authors & Contributors
* Daniel Marshman - daniel.marshman@protonmail.com
# License
This may be used in accordance with the GPL3.0 license, but please see the next subsection for citation details if publishing results from use of the model.  

If you are publishing based on results generated from this model, we ask that you cite the following paper:

[Marshman, D., Brear, M., Jeppesen, M. and Ring, B., 2020. *Performance of wholesale electricity markets with high wind penetration.* Energy Economics, 89, p.104803.](https://www.sciencedirect.com/science/article/pii/S0140988320301432)
## Detailed documentation
Coming soon.  In the meantime, see chapter 3 of Daniel Marshman's [thesis](https://minerva-access.unimelb.edu.au/bitstream/handle/11343/222168/Revised%20Thesis.pdf?sequence=1&isAllowed=y)
