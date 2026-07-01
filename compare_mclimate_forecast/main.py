"""
Main driver for AR hazard processing.
Compute + save
→ AR index
→ save nc
→ save csv
"""

import argparse
import yaml
import pandas as pd

from forecast_processor import process_all_variables
from ar_hazard_index import compute_AR_hazard_index
from io_utils import save_processed_datasets
from summaries import export_summary_csv


# ---------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------

parser = argparse.ArgumentParser()

parser.add_argument(
    "--init-date",
    required=True,
    help="Initialization date YYYYMMDD",
)

parser.add_argument(
    "--domain",
    default="San-Mateo",
)

parser.add_argument(
    "--source",
    default="reforecast",
)

parser.add_argument(
    "--server",
    default="aware",
)

args = parser.parse_args()

init_date = args.init_date
domain_name = args.domain
source = args.source
server = args.server


# ---------------------------------------------------------
# Config
# ---------------------------------------------------------

var_lst = [
    "qpf",
    "ivt",
    "freezing_level",
    "uv",
]

# ---------------------------------------------------------
# Load domain config
# ---------------------------------------------------------

with open("config/domain.yaml", "r") as f:
    config = yaml.safe_load(f)

domain_cfg = config["domains"][domain_name]

domain = {
    "lon_min": -179.5,
    "lon_max": -110.,
    "lat_min": 10.,
    "lat_max": 70.,
}


# ---------------------------------------------------------
# Process variables
# ---------------------------------------------------------

fc, final_ds = process_all_variables(
    init_date=init_date,
    var_lst=var_lst,
    domain=domain,
    source=source,
    server=server,
)


# ---------------------------------------------------------
# Compute AR hazard index
# ---------------------------------------------------------

final_ds = compute_AR_hazard_index(
    final_ds
)

# ---------------------------------------------------------
# Export netCDFs
# ---------------------------------------------------------
save_processed_datasets(
    fc,
    final_ds,
    init_date,
    source,
)

# ---------------------------------------------------------
# Export CSV
# ---------------------------------------------------------

export_summary_csv(
    final_ds,
    domain_name,
    domain_cfg,
    init_date,
    mode="max",
)