import glob
import json

ver = 'v20230324'

pin = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/%(MIP)/%(EXP)/' + ver + '/ts/'

MIPS = ['cmip6', 'cmip5']
# exps = ['historical', 'amip']
exps = ['amip']

mod_dic = {}

for mip in MIPS:
    mod_dic[mip] = {}
    for exp in exps:
        ptmp = pin.replace('%(MIP)', mip).replace('%(EXP)', exp)
        print('MIP: ', mip)
        print('exp: ', exp)
        print('dir: ', ptmp)

        lst = sorted(glob.glob(ptmp + '*.r1*.AC.' + ver + '.nc'))
        mods = []
        for li in lst:
            mod = li.split('.')[4]
            if mod not in mods:
                mods.append(mod)

        print(mods)
        mod_dic[mip][exp] = sorted(mods)

json.dump(mod_dic, open('all_mip_mods-' + ver + '.json', 'w'), indent=4, sort_keys=True)
