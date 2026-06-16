import xarray as xr
import s3fs
from fpdf import FPDF

# 1. Connect to S3 anonymously
fs = s3fs.S3FileSystem(anon=True)

# 2. Loop through the first 20 ensemble members (r1 to r20)
for i in range(1, 21):
    ensemble_member = f"r{i}i1p1f1"
    print(f"Processing {ensemble_member}...")
    
    # Dynamically inject the ensemble member into the S3 path
    s3_path = f's3://noaa-gfdl-spear-large-ensembles-pds/SPEAR/GFDL-LARGE-ENSEMBLES/CMIP/NOAA-GFDL/GFDL-SPEAR-MED/historical/{ensemble_member}/6hr/pr/gr3/v20210201/pr_6hr_GFDL-SPEAR-MED_historical_{ensemble_member}_gr3_192101010300-193012312100.nc'
    
    try:
        # Open the file without downloading the arrays or decoding time
        with fs.open(s3_path) as file_obj:
            ds = xr.open_dataset(file_obj, engine='h5netcdf', decode_times=False, decode_cf=False)
            
            # 3. Format the text for the PDF
            metadata_text = "--- GLOBAL METADATA ---\n"
            for key, value in ds.attrs.items():
                metadata_text += f"{key}: {value}\n"
                
            metadata_text += "\n--- VARIABLE METADATA (pr) ---\n"
            for key, value in ds['pr'].attrs.items():
                metadata_text += f"{key}: {value}\n"
                
            # 4. Generate the PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=10)
            
            # multi_cell handles line breaks automatically for long text blocks
            pdf.multi_cell(0, 5, metadata_text)
            
            # Save the file locally
            pdf_filename = f"metadata_{ensemble_member}.pdf"
            pdf.output(pdf_filename)
            
            print(f"Successfully saved {pdf_filename}")
            
    except Exception as e:
        print(f"Could not process {ensemble_member}. Error: {e}")

print("Batch processing complete!")