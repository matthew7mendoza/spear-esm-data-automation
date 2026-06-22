"""This script gets spear climate dataset from the laboratory and save details"""

import xarray as xr
import fsspec

DATA_URL = "ftp://nomads.gfdl.noaa.gov/2/GFDL-LARGE-ENSEMBLES/CMIP/NOAA-GFDL/GFDL-SPEAR-MED/historical/r10i1p1f1/Amon/tas/gr3/v20210201/tas_Amon_GFDL-SPEAR-MED_historical_r10i1p1f1_gr3_192101-201412.nc"

try:
    with fsspec.open(DATA_URL, "rb") as f:
        ds = xr.open_dataset(f, engine="h5netcdf")
        
        print("Success")
        
        output_filename = "spear_metadata_summary.txt"
        with open(output_filename, "w", encoding="utf-8") as text_file:
            text_file.write(str(ds))
            
        print(f"Saved to {output_filename}")

except Exception as e:
    print(f"Error: {str(e).replace('.', '')}")