# zort : ZTF Object Reader Tool

## Getting Started

The ZTF Object Reader Tool, ```zort```, is set of functions to organize and 
access the ZTF Public Data Release lightcurves across multiple filters. 

### ZTF Public Data Release Lightcurves

The ZTF Public Data Release Lightcurves are generated through spatially 
cross-matching individual epoch photometric catalogs. Catalogs are 
pre-filtered to be (1) the same ZTF observation field ID, (2) the same CCD 
readout channel, and (3) the same photometric filter. Spatially coincidence
observations in these catalogs are all labelled as objects and saved to a 
common ascii file along with the observation data for each epoch of the object. 
These files are consolidated such that all objects sharing a common ZTF 
observation field ID reside in the same file.

```zort``` refers to these files with extension ```*.txt``` as 
**lightcurve files**.

### Features

```zort``` provides facilitates the reading and inspection of lightcurves in 
the ZTF Public Data Release. The features of ```zort``` include:
- Instant access to lightcurves by (1) ZTF Object ID or (2) sky location 
specified through right ascension and declination, after initial search 
- Consolidating g-band and R-band lightcurves of a object that are otherwise 
labelled as two separate objects 
- Plotting lightcurves in multiple colors for visual inspection

### Installation

```bash
git clone https://github.com/MichaelMedford/zort.git
cd zort
python setup.py install
```

### Terminology
- **lightcurve file**: Files included in the ZTF Public Data Release containing 
epoch photometry for spatially coincidence observations
- **object**: A collection of spatially coincident 
observations in a single color. Objects include IDs, sky locations (in right 
ascension and declination) and filter colors (g-band and R-band).
- **lightcurve**: Observation epochs of an object. Lightcurve observations 
include dates, magnitudes and magnitude errors.
- **rcid map**: Information on the organization of the lightcurve files 
required for faster object access.
- **sibling**: A spatially coincident source in a different filter color.

### Initialization

```zort``` requires that the location of the lightcurve files be saved as 
an environemnt variable **ZTF_LC_DATA**. You will most likely want to set this 
location as an environment variable in your ~/.bashrc file or ~/.cshrc.

```zort``` creates two additional data products per lightcurve file 
(```*.txt```) in order to make object discovery and multiple filter 
consolidation faster. Object files (```*.objects```) contain all of the 
metadata for each object in a lightcurve file. RCID map files 
(```*.rcid_map```) contain lightcurve file metadata that facilitates faster 
matching of multiple colors for individual objects. ```zort``` requires that 
each lightcurve file has a corresponding object file and RCID map file.

To generate object files and RCID map files either run:
```bash
python {initializeFile}
```
or
```bash
python {initializeFile} --parallel --n-procs=$N_PROCS
``` 

## Requirements
* Python 3.7

## Authors
* Michael Medford <MichaelMedford@berkeley.edu>
