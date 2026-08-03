#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
from simple_reader_nnr_ods import NNRsimplereader
from writeIODA import WriteIODA
import argparse
import glob

def expand_patterns(patterns):
    if not patterns or isinstance(patterns, str):
        return []
        
    expanded = []
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            expanded.extend(matches)
        else: 
            expanded.append(pattern)
    return expanded
   

# --- Configuration ---
nnr_base_path = Path('./')

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='script_offline_ods:')
    parser.add_argument('--ods', nargs='+', type=str, default='null',
                        help='AOD ODS filename(s) (default: none)')

    args = parser.parse_args();

    if args.ods:
       ods_files = expand_patterns(args.ods) if args.ods else []

    # pandas.date_range handles all the time math 
#   times = pd.date_range(start="2019-06-11 12:00:00", end="2019-06-11 12:00:00", freq="3h")

#   for t in times:
    for jj,t in enumerate(ods_files):
                
                # Build the file name and full path
#               filename = f"test.aod.obs.{t.strftime('%Y%m%d_%H')}00z.ods"
                        odsfile = t #nnr_base_path / filename
                
                        print(f"Checking: {odsfile}")
                
#               if odsfile.is_file():
#                   # Get just the name without the extension for the output file
#                   ioda_tmpl = f"IODA_{odsfile.stem}.nc4"
#                       ioda_tmpl = f"IODA_{odsfile.stem}.nc4"
                        ioda_tmpl = "test"+str(jj)+".nc4"
#                   
#                   try:
                        # Read
                        nnr = NNRsimplereader(odsfilename=str(odsfile), verbose=False)
                        print(nnr.nobs) 
                        # Write
                        ioda = WriteIODA(nnr=nnr, filename=ioda_tmpl, convert_log_to_linear=True, verbose=True)
                        ioda.write_ioda()
                        print(f"Success: {ioda_tmpl}\n")
                        
#                   except ValueError as e:
#                       print(f"Skipping {odsfile.name}: {e}\n")
#                   except Exception as e:
#                       print(f"Error processing {odsfile.name}: {e}\n")
#               else:
#                   print("File does not exist.\n")
