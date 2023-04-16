import datetime
import os

mip = "obs"
dat = "TRMM"
var = "pr"
frq = "day"
ver = "v20221111"

modpath = "/p/user_pub/PCMDIobs/obs4MIPs/NASA-GSFC/TRMM-3B42v-7/day/pr/1x1/latest"
mod = "*.nc"

case_id = "{:v%Y%m%d}".format(datetime.datetime.now())
pmpdir = "/work/ahn6/pr/variability_across_timescales/power_spectrum/" + ver + "_test/"
results_dir = os.path.join(
    pmpdir, "%(output_type)", "%(mip)", "%(case_id)"
)

prd = [2001, 2019]  # analysis period
fac = 86400  # factor to make unit of [mm/day]
nperseg = 10 * 365 * 1  # length of segment in power spectra (~10yrs)
# length of overlap between segments in power spectra (~5yrs)
noverlap = 5 * 365 * 1