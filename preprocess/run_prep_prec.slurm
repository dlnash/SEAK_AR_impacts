#!/bin/bash
#SBATCH --account=cwp140
#SBATCH --partition=compute
#SBATCH -N 1 # Ensure that all cores are on one machine
#SBATCH --nodes=1 # specifies how many nodes to use (each node has 24 cores)
#SBATCH --mem=40G
#SBATCH -t 05:00:00 # Runtime in HH:MM:SS
#SBATCH -o slurm_out/prec/output_%a # File to which STDOUT will be written
#SBATCH -e slurm_out/prec/output_err%a # File to which STDERR will be written
#SBATCH --job-name=preprocess_GEFS_prec
#SBATCH --mail-type=ALL # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=dnash@ucsd.edu # Email to which notifications will be sent
#SBATCH --qos=unlim
#SBATCH --array=1-6%10

# Activate Anaconda work environment
source /home/${USER}/.bashrc
source activate SEAK-impacts 
 
linevar=`sed $SLURM_ARRAY_TASK_ID'q;d' calls_prec.txt`
eval $linevar