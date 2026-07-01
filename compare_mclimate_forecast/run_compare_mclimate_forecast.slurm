#!/bin/bash
#SBATCH --account=cwp140
#SBATCH --partition=shared-128
#SBATCH --job-name=mclimate_csv
#SBATCH --output=logs/mclimate_%A_%a.out
#SBATCH --error=logs/mclimate_%A_%a.err

#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G

#SBATCH --array=0-365

# ---------------------------------------------------------
# Config
# ---------------------------------------------------------

DATES_FILE="dates_2000_2019.txt"

DAYS_PER_TASK=20

START=$(( SLURM_ARRAY_TASK_ID * DAYS_PER_TASK + 1 ))
END=$(( START + DAYS_PER_TASK - 1 ))

echo "Processing lines ${START}-${END}"

# ---------------------------------------------------------
# Loop over dates
# ---------------------------------------------------------

for LINE in $(seq $START $END)
do

    DATE=$(sed -n "${LINE}p" ${DATES_FILE})

    # Skip if empty
    if [ -z "$DATE" ]; then
        continue
    fi

    echo "Running ${DATE}"

    /home/dnash/miniconda3/envs/SEAK-impacts/bin/python main.py \
        --init-date ${DATE} \
        --domain NPAC \
        --source reforecast \
        --server aware

done