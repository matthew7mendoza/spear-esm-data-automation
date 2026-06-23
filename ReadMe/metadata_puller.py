import random
import s3fs
import xarray as xr

s3 = s3fs.S3FileSystem(anon=True)
bucket_path = "noaa-gfdl-spear-large-ensembles-pds/SPEAR/GFDL-LARGE-ENSEMBLES/CMIP/NOAA-GFDL/GFDL-SPEAR-MED"

try:
    all_files = s3.glob(f"{bucket_path}/**/*.nc")
    sampled_files = random.sample(all_files, min(10, len(all_files)))

    for index, file_path in enumerate(sampled_files, 1):
        url = f"s3://{file_path}"
        try:
            dataset = xr.open_dataset(
                url, engine="h5netcdf", storage_options={"anon": True}
            )
            
            with open(f"meta_{index}.txt", "w", encoding="utf-8") as f:
                f.write(f"URL: {url}\n\n")
                
                f.write("--- GLOBAL ATTRIBUTES ---\n")
                for key, value in dataset.attrs.items():
                    f.write(f"{key}: {value}\n")
                
                f.write("\n--- DATA VARIABLES AND METADATA ---\n")
                for var_name in dataset.variables:
                    f.write(f"\nVariable: {var_name}\n")
                    f.write(f"Dimensions: {dataset[var_name].dims}\n")
                    f.write(f"DataType: {dataset[var_name].dtype}\n")
                    for attr_key, attr_val in dataset[var_name].attrs.items():
                        f.write(f"  {attr_key}: {attr_val}\n")
                        
            print(f"[{index}/10] Saved meta_{index}.txt")
        except Exception as e:
            print(f"[{index}/10] Failed ({type(e).__name__})")

except Exception as e:
    print(f"Execution failed: {e}")