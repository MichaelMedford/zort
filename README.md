# zort : ZTF Object Reader Tool

## Getting Started

The ZTF Object Reader Tool, ```zort```, is set of functions to organize and 
access the ZTF Public Data Release lightcurves across multiple colors. 

### ZTF Public Data Release Lightcurves

Instructions for downloading and extracting ZTF Public Data Release Lightcurves 
can be found at: https://www.ztf.caltech.edu/page/dr2#12c

The ZTF Public Data Release Lightcurves are generated through spatially 
cross-matching individual epoch photometric catalogs. Catalogs are 
pre-filtered to be (1) the same ZTF observation field ID, (2) the same CCD 
readout channel, and (3) the same photometric color. Spatially coincidence
observations in these catalogs are all labelled as objects and saved to a 
common ascii file along with the observation data for each epoch of the object. 
These files are consolidated such that all objects sharing a common ZTF 
observation field ID reside in the same file.

```zort``` refers to these files with extension ```*.txt``` as 
**lightcurve files**.

### Features

```zort``` provides facilitates the reading and inspection of lightcurves in 
the ZTF Public Data Release. The features of ```zort``` include:
- Seamless looping through ZTF lightcurves for custom filtering, where 
interesting objects can be saved and recovered by only their file location
- Consolidating g-band and R-band lightcurves of a single source that are 
otherwise labelled as two separate objects by pairing objects as "siblings"
- Plotting lightcurves in multiple colors for visual inspection

### Installation

Preferred method is through pip:

```
pip install zort
```

Latest version can also be installed from github:
```
git clone https://github.com/MichaelMedford/zort.git
cd zort
python setup.py install
```

### Terminology
- **lightcurve file**: Files included in the ZTF Public Data Release containing 
epoch photometry for spatially coincidence observations
- **object**: A collection of spatially coincident 
observations in a single color. Objects include IDs, sky locations (in right 
ascension and declination) and colors (g-band and R-band).
- **lightcurve**: Observation epochs of an object. Lightcurve observations 
include dates, magnitudes and magnitude errors.
- **radec_map**: Binary search trees for the objects in a lightcurve file. 
required for faster object access.
- **siblings**: A spatially coincident object in a different color 
originating from the same astrophysical source.

### Initialization

```zort``` requires two additional data products per lightcurve file 
(```*.txt```) in order to make object discovery and multiple color 
consolidation faster. Object files (```*.objects```) contain all of the 
metadata for each object in a lightcurve file. RCID map files 
(```*.radec_map```) contain binary search trees that facilitates faster 
matching of multiple colors for individual objects. ```zort``` requires that 
each lightcurve file has a corresponding object file and RCID map file.

To generate object files and RCID map files for a directory of lightcurve 
files, run
```
zort-initialize -lightcurve-file-directory=LIGHTCURVE_FILE_DIRECTORY -single
```
or if mpi4py is installed then launch multiple instances of 
```
zort-initialize -lightcurve-file-directory=LIGHTCURVE_FILE_DIRECTORY -parallel
```

If each lightcurve file does not have an object file and an RCID map then 
```zort``` will not be able to locate siblings

## Examples

### Extracting Lightcurves

```zort``` is designed to provide you with easy access to all of the 
lightcurves in a lightcurve file for applying filters and saving interesting 
objects. The preferred method for inspecting lightcurves is through a for-loop.

A filter is created that returns True for interesting objects. This filter 
can involve simply cuts on object properties or complicated model fitting to 
the full observation data in the object's lightcurve
```
def my_interesting_filter(obj):
    cond1 = obj.nepochs >= 20
    cond2 = min(obj.lightcurve.mag) <= 17.0
    if cond1 and cond2:
        return True
    else:
        return False
```

When a lightcurve file is looped over, it returns each object in the lightcurve
file. Interesting objects can be gathered into a list and saved to disk using the 
```save_objects``` function.
```
filename = 'lightcurve_file_example.txt'
interesting_objects = []

from zort.lightcurveFile import LightcurveFile
for obj in LightcurveFile(filename):
    if my_interesting_filter(obj):
        interesting_objects.append(obj)
       
from zort.object import save_objects
save_objects('objects.list', interesting_objects)
```

Objects and their lightcurves can be retrieved from a saved list by using the 
```load_objects``` function. Each object comes loaded with its metadata and 
lightcurve, easily previewed by printing the object and lightcurve attribute. 
```
from zort.object import load_objects
interesting_objects = load_objects('objects.list')
for obj in interesting_objects:
    print(obj)
    print(obj.lightcurve)
``` 

Objects can also be extracted in parallel by instantiating the LightcurveFile 
class with a rank and size. This could be done through mpi4py, or other 
parallelization packages. The LightcurveFile class simply needs to be told 
the rank of the parallel process and the total number, or size, of the parallel
processes. 
```
from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.rank
size = comm.size

filename = 'lightcurve_file_example.txt'
interesting_objects = []

from zort.lightcurveFile import LightcurveFile
for obj in LightcurveFile(filename, proc_rank=rank, proc_size=size):
    if my_interesting_filter(obj):
        interesting_objects.append(obj)
       
from zort.object import save_objects
save_objects('objects.%i.list' % rank, interesting_objects)
```

Setting the ```proc_rank``` and ```proc_size``` parameters will cause the 
iterator to uniquely send different objects to each parallel process without 
loading all of the objects into memory for each process. This allows for 
applying a filter to all of the objects in a lightcurve file without 
overloading memory.

### Matching multiple colors for an object

Each object is defined as a spatially coincidence series of observations that 
share a (1) ZTF observation field ID, (2) CCD readout channel, and (3) 
photometric filter. This labels multiple colors of the same astrophysical 
source as separate ZTF objects with separate object IDs. The ZTF Public Data 
Release does not provide any native support for pairing these objects as 
multiple colors of the same source.

```zort``` supports searching for and saving multiple colors for the same 
source. The ZTF Public Data Release contains observations in g-band 
(filterid=1) and R-band (filterid=2). Each object can therefore have one 
additional object that comes from the same astrophysical source but is in a 
different color. These matching objects are labelled as "siblings" and can 
be both discovered and saved with ```zort```.

The siblings for each object can be located by simply running an object's  
```locate_siblings``` method. Running

```
filename = 'field000245_ra357.03053to5.26702_dec-27.96964to-20.4773.txt'
buffer_position = 6852
obj = Object(filename, buffer_position)
obj.locate_siblings(printFlag=True)
```

results in
```
Locating siblings for ZTF Object 245101100000025
-- Object location: 4.74852, -26.23583 ...
** siblings file missing! **
-- Searching between buffers 17749819 and 18135260
---- Sibling found at 4.74851, -26.23581 !
---- Original Color: 1 | Sibling Color: 2
---- Sibling saved
```  

An object's siblings is itself another object and can be accessed through the 
siblings attribute.

```
print(obj)
Filename: field000245_ra357.03053to5.26702_dec-27.96964to-20.4773.txt
Buffer Position: 6852
Object ID: 245101100000025
Color: g
Ra/Dec: (4.74852, -26.23583)
22 Epochs passing quality cuts

print(obj.siblings)
Filename: field000245_ra357.03053to5.26702_dec-27.96964to-20.4773.txt
Buffer Position: 126136890
Object ID: 245201100000047
Color: r
Ra/Dec: (4.74851, -26.23581)
22 Epochs passing quality cuts
```

The default tolerance for matching two objects as siblings is 2.0". However 
this can be altered by setting the ```radius``` argument 
in ```obj.locate_siblings()```.  

### Plotting lightcurves

A lightcurve plot can be generated for any object using the 
```obj.plot_lightcurve()``` method.
![](https://raw.githubusercontent.com/MichaelMedford/zort/master/example_images/field000245_ra357.03053to5.26702_dec-27.96964to-20.4773.txt-6852-lc.png)

A lightcurve plot including an object's siblings 
cand be generated using the ```obj.plot_lightcurves()``` method.
![](https://raw.githubusercontent.com/MichaelMedford/zort/master/example_images/field000245_ra357.03053to5.26702_dec-27.96964to-20.4773.txt-6852-lc-with_siblings.png)

## Requirements
* python 3.6
* numpy
* scipy
* astropy
* matplotlib
* shapely

## Authors
* Michael Medford <MichaelMedford@berkeley.edu>

## Citation
[![DOI](https://zenodo.org/badge/200887248.svg)](https://zenodo.org/badge/latestdoi/200887248)
