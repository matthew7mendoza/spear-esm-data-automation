import xarray as xr

public_gfdl_url = "https://pavics.ouranos.ca/twitcher/ows/proxy/thredds/dodsC/datasets/simulations/bias_adjusted/cmip6/ouranos/ESPO-G/ESPO-G6-E5Lv1.0.0/day_ESPO-G6-E5L_v1.0.0_CMIP6_ScenarioMIP_NAM_CSIRO_ACCESS-ESM1-5_ssp370_r1i1p1f1_1950-2100.ncml"

try:
    ds = xr.open_dataset(public_gfdl_url, chunks=None, engine="netcdf4")

    with open("real_gfdl_headers.txt", "w") as file:
        file.write(str(ds))

    print(" GFDL metadata successfully written to file")
except Exception as e:
    print(f"The connection failed for some reason: {e}")