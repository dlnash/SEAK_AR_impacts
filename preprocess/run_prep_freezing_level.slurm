#!/bin/bash
#SBATCH --account=cwp140
#SBATCH --partition=shared
#SBATCH -N 1 # Ensure that all cores are on one machine
#SBATCH --mem=40G
#SBATCH -t 05:00:00 # Runtime in HH:MM:SS
#SBATCH -o slurm_out/freezing_level/output_%a # File to which STDOUT will be written
#SBATCH -e slurm_out/freezing_level/output_err%a # File to which STDERR will be written
#SBATCH --job-name=preprocess_GEFS_freezing_level
#SBATCH --mail-type=ALL # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=dnash@ucsd.edu # Email to which notifications will be sent
#SBATCH --array=39-1499%100 # runs jobs 39-1499, 100 at a time

# Activate Anaconda work environment
source /home/${USER}/.bashrc
source activate SEAK-impacts 
 
linevar=`sed $SLURM_ARRAY_TASK_ID'q;d' calls_freezing_level.txt`
eval $linevar