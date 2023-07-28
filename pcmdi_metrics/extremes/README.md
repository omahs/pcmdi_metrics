# PMP Extremes Metrics

TODO: THere is a bug in the return value calculation (lib/return_value.py) that is causing DJF to be all nans.

## Inputs

The Extremes Driver works on daily gridded climate data. This package expects input netcdf files to be cf-compliant and on regular latitude/longitude grids. X and Y dimensions must be named "lon" and "lat", and the time dimension must be named "time". The input variables must be called "tasmax", "tasmin", or "pr". Input files must contain lat, lon, and time bounds.

A reference (observation) input is not required, but it is necessary to create Taylor Diagrams. Reference data sets must follow the above rules for variable names and bounds.

If land sea masks are scaled from 0-1, they will be rescaled to 0-100 on-the-fly. The mask variable in the file must be called "sftlf". If land/sea masks are not provided, there is an option to generate them on-the-fly using pcmdi_utils. 

A yearly covariate time series can be provided to calculate the return value for non-stationary data. The covariate time dimension must either 1) be exactly the same length in years as the input data, or 2) overlap in years with the input data time dimension. It is recommended that a log transformation be applied to nonlinear covariates such as recent carbon dioxide values. Covariate data must be provided as a netcdf file with time bounds.

See the "Other Parameters" table for options to select a year range, convert units, and control regridding.

## Run

To run the extremes metrics, use the following command format in a PMP environment:  
```extremes_driver.py -p parameter_file --other_params```

## Outputs
The outputs will be written to a single directory. This directory will be created by the driver if it does not already exist. Otherwise, the output directory should be empty before the driver starts. The name of the output directory is controlled by the `metrics_output_path` and `case_id` parameters. 

This script will produce metrics JSONs, netcdf files, and figures (optional) containing block max/min values for temperature and/or precipitation. A metadata file called "output.json" will be generated with more detailed information about the files in the output bundle.

Data is masked to be over land only (50<=sftlf<=100). Antarctica is excluded.

### Metrics
Metrics are produced to describe the time mean extrema values, along with spatial statistics comparing the mean model field to mean observed field.  
Model only: "mean", "std_xy"  
If reference dataset is available: "mean", "std_xy","std-obs_xy","pct_dif","bias_xy","cor_xy","mae_xy","rms_xy","rmsc_xy"  

## Regional Analysis

You can either use a region from a shapefile or provide coordinate pairs that define the region. Consult the parameters section for more information.

## Parameters

### Shapefile 

| Parameter   | Definition |
--------------|-------------
| shp_path    |  (str) path to shapefile.  |
| attribute      | (str) Attribute used to identify region (eg, column of attribute table). For example, "COUNTRY" in a shapefile of countries.  |
| region_name | (str) Unique feature value of the region that occurs in the attribute given by "--attribute". Must match only one geometry in the shapefile. An example is "NORTH_AMERICA" under the attribute "CONTINENTS". |

### Coordinates 
| Parameter   | Definition |
--------------|-------------
| coords      | (list) Coordinate lat/lon pair lists. The coordinate must be listed in consecutive order, as they would occur when walking the perimeter of the bounding shape. Does not need to be a box, but cannot have holes. For example [[lat1,lon1],[lat1,lon2],[lat2,lon2],[lat2,lon1]].  |
| region_name | (str) Name of region. Default is "custom". |

## Time series settings

| Parameter   | Definition |
--------------|-------------
| dec_mode | (str) Toggle how season containing December, January, and February is defined. "DJF" or "JFD". Default "DJF". |
| annual_strict | (bool) This only matters for Rx5day. If True, only use data from within a given year in the 5-day means. If False, the rolling mean will include the last 4 days of the prior year. Default False. |
| drop_incomplete_djf | (bool) If True, don't include data from the first January/February and last December in the analysis. Default False. |

## Other parameters
| Parameter   | Definition |
--------------|-------------
| case_id |  (str) Will be appended to the metrics_output_path if present. | 
| model_list | (list) List of model names.  | 
| realization | (list) List of realizations. | 
| vars | (list) List of variables: "pr", "tasmax", and/or "tasmin". | 
| filename_template | (str) The template for the model file name. May contain placeholders %(variable), %(model), %(model_version), or %(realization) | 
| test_data_path  |  (str) The template for the directory containing the model file. May contain placeholders %(variable), %(model), %(model_version), or %(realization) | 
| sftlf_filename_template | (str) The template for the model land/sea mask file. May contain placeholders %(model), %(model_version), or %(realization) | 
| generate_sftlf | (bool) If true, generate a land/sea mask on the fly when the model or reference land/sea mask is not found. If false, skip datasets when land/sea mask is not found. | 
| reference_data_path | (str) The full path of the reference data file. | 
| reference_data_set  | (str) The short name of the reference datas set for labeling output files. | 
| reference_sftlf_template | (str) The full path of the reference data set land/sea mask. | 
| metrics_output_path  | (str) The directory to write output files to. | 
| plots | (bool) True to save world map figures of mean metrics. |
| debug | (bool) True to use debug mode. | 
| msyear | (int) Start year for model data set. |
| meyear | (int) End year for model data set. |
| osyear | (int) Start year for reference data set. |
| oeyear | (int) End year for model data set. |
| regrid | (bool) Set to False to skip regridding if all datasets are on the same grid. Default True. |  
| ModUnitsAdjust | (tuple) Provide information for units conversion. Uses format (flag (bool), operation (str), value (float), new units (str)). Operation can be "add", "subtract", "multiply", or "divide". For example, use (True, 'multiply', 86400, 'mm/day') to convert kg/m2/s to mm/day.|
| ObsUnitsAdjust | (tuple) Similar to ModUnitsAdjust, but for reference dataset. |  


## References

Michael Wehner, Peter Gleckler, Jiwoo Lee, 2020: Characterization of long period return values of extreme daily temperature and precipitation in the CMIP6 models: Part 1, model evaluation, Weather and Climate Extremes, 30, 100283, https://doi.org/10.1016/j.wace.2020.100283.