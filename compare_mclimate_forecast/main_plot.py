"""
Create plots from saved diagnostics.
Load + visualize
load nc
→ plot
"""

import argparse
import yaml

from io_utils import load_processed_datasets
from summaries import load_summary_csv
from plotter import create_mclimate_figure

# ---------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------

parser = argparse.ArgumentParser()

parser.add_argument(
    "--init-date",
    required=True,
)

parser.add_argument(
    "--domain",
    default="San-Mateo",
)

parser.add_argument(
    "--source",
    default="reforecast",
)

args = parser.parse_args()

init_date = args.init_date
domain_name = args.domain
source = args.source


# ---------------------------------------------------------
# Domain config
# ---------------------------------------------------------

with open(
    "config/domain.yaml",
    "r",
) as f:

    config = yaml.safe_load(f)

domain_cfg = (
    config["domains"][domain_name]
)


# ---------------------------------------------------------
# Load processed datasets
# ---------------------------------------------------------

fc, final_ds = (
    load_processed_datasets(
        init_date=init_date,
        source=source,
    )
)

df = load_summary_csv(
    domain_name=domain_name,
    init_date=init_date,
)

# ---------------------------------------------------------
# Create plots
# ---------------------------------------------------------

create_mclimate_figure(
    ds=final_ds,
    fc=fc,
    df=df,
    domain_name=domain_name,
    domain_cfg=domain_cfg,
    init_date=init_date,
    lead_time=108,
    panel_labels=True,
)