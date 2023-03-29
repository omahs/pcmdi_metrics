#!/usr/bin/env python

import glob
import json
import os
from re import split
from collections import OrderedDict

import cdms2
import cdutil
import numpy as np
import xcdat as xc

from pcmdi_metrics import resources
from pcmdi_metrics.io import load_regions_specs, region_subset
from pcmdi_metrics.mean_climate.lib import (
    compute_metrics,
    create_mean_climate_parser,
    load_and_regrid,
    mean_climate_metrics_to_json,
)
from pcmdi_metrics.variability_mode.lib import tree


parser = create_mean_climate_parser()
parameter = parser.get_parameter(argparse_vals_only=False)

# parameters
case_id = parameter.case_id
test_data_set = parameter.test_data_set
realization = parameter.realization
vars = parameter.vars
reference_data_set = parameter.reference_data_set
target_grid = parameter.target_grid
regrid_tool = parameter.regrid_tool
regrid_tool_ocn = parameter.regrid_tool_ocn
save_test_clims = parameter.save_test_clims
test_clims_interpolated_output = parameter.test_clims_interpolated_output
filename_template = parameter.filename_template
sftlf_filename_template = parameter.sftlf_filename_template
generate_sftlf = parameter.generate_sftlf
regions_specs = parameter.regions_specs
regions = parameter.regions
test_data_path = parameter.test_data_path
reference_data_path = parameter.reference_data_path
metrics_output_path = parameter.metrics_output_path
diagnostics_output_path = parameter.diagnostics_output_path
debug = parameter.debug
cmec = parameter.cmec

if metrics_output_path is not None:
    metrics_output_path = parameter.metrics_output_path.replace('%(case_id)', case_id)

if diagnostics_output_path is None:
    diagnostics_output_path = metrics_output_path.replace('metrics_results', 'diagnostic_results')    
    
diagnostics_output_path = diagnostics_output_path.replace('%(case_id)', case_id)

find_all_realizations = False
if realization is None:
    realization = ""
    realizations = [realization]
elif isinstance(realization, str):
    if realization.lower() in ["all", "*"]:
        find_all_realizations = True
    else:
        realizations = [realization]

if debug:
    print('regions_specs (before loading internally defined):', regions_specs)

if regions_specs is None or not bool(regions_specs):
    regions_specs = load_regions_specs()

default_regions = ['global', 'NHEX', 'SHEX', 'TROPICS']
print(
    'case_id: ', case_id, '\n',
    'test_data_set:', test_data_set, '\n',
    'realization:', realization, '\n',
    'vars:', vars, '\n',
    'reference_data_set:', reference_data_set, '\n',
    'target_grid:', target_grid, '\n',
    'regrid_tool:', regrid_tool, '\n',
    'regrid_tool_ocn:', regrid_tool_ocn, '\n',
    'save_test_clims:', save_test_clims, '\n',
    'test_clims_interpolated_output:', test_clims_interpolated_output, '\n',
    'filename_template:', filename_template, '\n',
    'sftlf_filename_template:', sftlf_filename_template, '\n',
    'generate_sftlf:', generate_sftlf, '\n',
    'regions_specs:', regions_specs, '\n',
    'regions:', regions, '\n',
    'test_data_path:', test_data_path, '\n',
    'reference_data_path:', reference_data_path, '\n',
    'metrics_output_path:', metrics_output_path, '\n',
    'diagnostics_output_path:', diagnostics_output_path, '\n',
    'debug:', debug, '\n')

print('--- prepare mean climate metrics calculation ---')

# generate target grid
if target_grid == "2.5x2.5":
    # target grid for regridding
    t_grid = xc.create_uniform_grid(-88.875, 88.625, 2.5, 0, 357.5, 2.5)
    if debug:
        print('type(t_grid):', type(t_grid))  # Expected type is 'xarray.core.dataset.Dataset'
        print('t_grid:', t_grid)
    # identical target grid in cdms2 to use generateLandSeaMask function that is yet to exist in xcdat
    t_grid_cdms2 = cdms2.createUniformGrid(-88.875, 72, 2.5, 0, 144, 2.5)
    # generate land sea mask for the target grid
    sft = cdutil.generateLandSeaMask(t_grid_cdms2)
    if debug:
        print('sft:', sft)
        print('sft.getAxisList():', sft.getAxisList())
    # add sft to target grid dataset
    t_grid['sftlf'] = (['lat', 'lon'], np.array(sft))
    if debug:
        print('t_grid (after sftlf added):', t_grid)
        t_grid.to_netcdf('target_grid.nc')

# load obs catalogue json
egg_pth = resources.resource_path()
obs_file_name = "obs_info_dictionary.json"
obs_file_path = os.path.join(egg_pth, obs_file_name)
with open(obs_file_path) as fo:
    obs_dict = json.loads(fo.read())
# if debug:
    # print('obs_dict:', json.dumps(obs_dict, indent=4, sort_keys=True))

print('--- start mean climate metrics calculation ---')

# -------------
# variable loop
# -------------
for var in vars:

    if '_' in var or '-' in var:
        varname = split('_|-', var)[0]
        level = float(split('_|-', var)[1])
    else:
        varname = var
        level = None

    if varname not in list(regions.keys()):
        regions[varname] = default_regions

    print('varname:', varname)
    print('level:', level)

    # set dictionary for .json record
    result_dict = tree()

    # ----------------
    # observation loop
    # ----------------
    if "all" in reference_data_set:
        reference_data_set = [x for x in list(obs_dict[varname].keys()) if (x == "default" or "alternate" in x)]
        print("reference_data_set (all): ", reference_data_set)

    for ref in reference_data_set:
        print('ref:', ref)
        # identify data to load (annual cycle (AC) data is loading in)
        ref_dataset_name = obs_dict[varname][ref]
        ref_data_full_path = os.path.join(
            reference_data_path,
            obs_dict[varname][ref_dataset_name]["template"])
        print('ref_data_full_path:', ref_data_full_path)
        # load data and regrid
        ds_ref = load_and_regrid(ref_data_full_path, varname, level, t_grid, decode_times=False, regrid_tool=regrid_tool, debug=debug)
        ds_ref_dict = OrderedDict()

        # ----------
        # model loop
        # ----------
        for model in test_data_set:

            if find_all_realizations:
                test_data_full_path = os.path.join(
                    test_data_path,
                    filename_template).replace('%(variable)', varname).replace('%(model)', model).replace('%(model_version)', model).replace('%(realization)', '*')
                ncfiles = glob.glob(test_data_full_path)
                realizations = []
                for ncfile in ncfiles:
                    realizations.append(ncfile.split('/')[-1].split('.')[3])
                print('=================================')
                print('model, runs:', model, realizations)

            for run in realizations:
                # identify data to load (annual cycle (AC) data is loading in)
                test_data_full_path = os.path.join(
                    test_data_path,
                    filename_template).replace('%(variable)', varname).replace('%(model)', model).replace('%(model_version)', model).replace('%(realization)', run)
                if os.path.exists(test_data_full_path):
                    print('-----------------------')
                    print('model, run:', model, run)
                    print('test_data (model in this case) full_path:', test_data_full_path)
                    try:
                        ds_test_dict = OrderedDict()

                        # load data and regrid
                        ds_test = load_and_regrid(test_data_full_path, varname, level, t_grid, decode_times=True, regrid_tool=regrid_tool, debug=debug)
                        print('load and regrid done')

                        # -----------
                        # region loop
                        # -----------
                        for region in regions[varname]:
                            print('region:', region)

                            # land/sea mask -- conduct masking only for variable data array, not entire data
                            if ('land' in region.split('_')) or ('ocean' in region.split('_')):
                                ds_test_tmp = ds_test.copy(deep=True)
                                ds_ref_tmp = ds_ref.copy(deep=True)
                                if 'land' in region.split('_'):
                                    ds_test_tmp[varname] = ds_test[varname].where(t_grid['sftlf'] != 0.)
                                    ds_ref_tmp[varname] = ds_ref[varname].where(t_grid['sftlf'] != 0.)
                                elif 'ocean' in region.split('_'):
                                    ds_test_tmp[varname] = ds_test[varname].where(t_grid['sftlf'] == 0.)
                                    ds_ref_tmp[varname] = ds_ref[varname].where(t_grid['sftlf'] == 0.)
                                    print('mask done')
                            else:
                                ds_test_tmp = ds_test
                                ds_ref_tmp = ds_ref

                            # spatial subset
                            if region.lower() in ['global', 'land', 'ocean']:
                                ds_test_dict[region] = ds_test_tmp
                                if region not in list(ds_ref_dict.keys()):
                                    ds_ref_dict[region] = ds_ref_tmp
                            else:
                                ds_test_tmp = region_subset(ds_test_tmp, regions_specs, region=region)
                                ds_test_dict[region] = ds_test_tmp
                                if region not in list(ds_ref_dict.keys()):
                                    ds_ref_dict[region] = region_subset(ds_ref_tmp, regions_specs, region=region)
                                print('spatial subset done')
                                
                            if save_test_clims and ref == reference_data_set[0]:
                                test_clims_dir = os.path.join(
                                    diagnostics_output_path, var, 'interpolated_model_clims')
                                os.makedirs(test_clims_dir, exist_ok=True)
                                test_clims_file = os.path.join(
                                    test_clims_dir,
                                    '_'.join([var, model, run, 'interpolated', regrid_tool, region, 'AC', case_id + '.nc']))
                                ds_test_dict[region].to_netcdf(test_clims_file)

                            if debug:
                                print('ds_test_tmp:', ds_test_tmp)
                                ds_test_dict[region].to_netcdf('_'.join([var, 'model', model, run, region + '.nc']))
                                if model == test_data_set[0] and run == realizations[0]:
                                    ds_ref_dict[region].to_netcdf('_'.join([var, 'ref', region + '.nc']))

                            # compute metrics
                            print('compute metrics start')
                            result_dict["RESULTS"][model][ref][run][region] = compute_metrics(varname, ds_test_dict[region], ds_ref_dict[region], debug=debug)

                        # write individual JSON
                        # --- single simulation, obs (need to accumulate later) / single variable
                        json_filename_tmp = "_".join([model, var, target_grid, regrid_tool, "metrics", ref])
                        mean_climate_metrics_to_json(
                            os.path.join(metrics_output_path, var),
                            json_filename_tmp,
                            result_dict,
                            model=model,
                            run=run,
                            cmec_flag=cmec,
                            debug=debug
                        )
 
                    except Exception as e:
                        print('error occured for ', model, run)
                        print(e)

    # write collective JSON --- all models / all obs / single variable
    json_filename = "_".join([var, target_grid, regrid_tool, "metrics"])
    mean_climate_metrics_to_json(
        metrics_output_path,
        json_filename,
        result_dict,
        cmec_flag=cmec,
    )
    print('pmp mean clim driver completed')