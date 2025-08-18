import glob
import re
import yaml

config_number = '2'

file_patterns = ["slurm_out/output_err{}".format(i) for i in range(1, 32)]

error_regex = re.compile(r"OSError: \[Errno -101\] NetCDF: HDF error: '([^']+)'")
date_regex = re.compile(r"/(\d{8})_")

errors_found = []
all_dates = []

for filename in file_patterns:
    try:
        with open(filename, 'r') as f:
            for line in f:
                match = error_regex.search(line)
                if match:
                    nc_file = match.group(1)
                    date_match = date_regex.search(nc_file)
                    if date_match:
                        date_str = date_match.group(1)
                    else:
                        date_str = "DATE_NOT_FOUND"
                    errors_found.append((filename, date_str))
                    all_dates.append(date_str)
    except FileNotFoundError:
        continue

# Create a unique sorted list
unique_dates = sorted(set(all_dates))

# Print results
if errors_found:
    print("Dates of NetCDF errors found:\n")
    for errfile, date_str in errors_found:
        print(f"In {errfile}: Date {date_str}")

    print("\nAll dates:")
    print(all_dates)

    print("\nUnique dates:")
    print(unique_dates)
else:
    print("No NetCDF HDF errors found in any output_err files.")

# ### manually add unique dates
# unique_dates = ['20040118', '20040819', '20041113', '20050129']
# print("\nUnique dates:")
# print(unique_dates)
# Load the YAML file
with open(f'/home/dnash/repos/SEAK_AR_impacts/downloads/GEFSv12_reforecast/config_{config_number}.yaml', 'r') as f:
    config_data = yaml.safe_load(f)

# Store matching jobs
matching_jobs = []

for job_name, job_info in config_data.items():
    init_date = str(job_info.get('date'))
    if init_date in unique_dates:
        matching_jobs.append(job_name)

# Print results
if matching_jobs:
    print("Jobs with init_date matching unique dates:\n")

    # Write to file
    output_file = "/home/dnash/repos/SEAK_AR_impacts/downloads/GEFSv12_reforecast/calls_missing.txt"
    with open(output_file, 'w') as out:
        for job_name in matching_jobs:
            out.write(f"python getGEFSv12_batch.py config_{config_number}.yaml '{job_name}'"+ '\n')
            
else:
    print("No jobs found with init_date matching unique dates.")

# Load the YAML file
with open(f'/home/dnash/repos/SEAK_AR_impacts/preprocess/GEFSv12_reforecast/config_{config_number}.yaml', 'r') as f:
    config_data = yaml.safe_load(f)

# Store matching jobs
matching_jobs = []

for job_name, job_info in config_data.items():
    init_date = str(job_info.get('date'))
    if init_date in unique_dates:
        matching_jobs.append(job_name)

# Print results
if matching_jobs:
    print("Jobs with init_date matching unique dates:\n")
    # Write to file
    output_file = "/home/dnash/repos/SEAK_AR_impacts/preprocess/GEFSv12_reforecast/calls_missing.txt"
    with open(output_file, 'w') as out:
        for job_name in matching_jobs:
            out.write(f"python preprocess_GEFSv12_reforecast.py config_{config_number}.yaml '{job_name}'"+ '\n')
else:
    print("No jobs found with init_date matching unique dates.")
    
     
