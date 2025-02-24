import json
from copy import deepcopy

from pcmdi_metrics.io.base import Base


def mean_climate_metrics_to_json(
    outdir, json_filename, result_dict,
    model=None, run=None,
    cmec_flag=False, debug=False
):
    # Open JSON
    JSON = Base(
        outdir, json_filename
    )
    # Dict for JSON
    json_dict = deepcopy(result_dict)
    if model is not None or run is not None:
        # Preserve only needed dict branch -- delete rest keys
        models_in_dict = list(json_dict["RESULTS"].keys())
        for m in models_in_dict:
            if m == model:
                for ref in list(json_dict["RESULTS"][m].keys()):
                    runs_in_model_dict = list(json_dict["RESULTS"][m][ref].keys())
                    for r in runs_in_model_dict:
                        if (r != run) and (run is not None):
                            del json_dict["RESULTS"][m][ref][r]
            else:
                del json_dict["RESULTS"][m]
    # Write selected dict to JSON
    JSON.write(
        json_dict,
        json_structure=[
            "model",
            "reference",
            "rip",
            "region",
            "statistic",
            "season",
        ],
        indent=4,
        separators=(",", ": "),
        mode="r+",
        sort_keys=False,
    )

    if debug:
        print('in mean_climate_metrics_to_json, model, run:', model, run)
        print('json_dict:', json.dumps(json_dict, sort_keys=True, indent=4))

    if cmec_flag:
        print("Writing cmec file")
        JSON.write_cmec(indent=4, separators=(",", ": "))
