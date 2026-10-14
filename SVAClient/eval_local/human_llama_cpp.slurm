#!/bin/bash

#- Job parameters

# (TODO)
# Please modify job name

#- Resources

# (TODO)
# Please modify your requirements

#SBATCH -p r8nv-gpu-hw               # Submit to 'nv-gpu' Partitiion
#SBATCH -t 1-00:00:00                # Run for a maximum time of 0 days, 12 hours, 00 mins, 00 secs
#SBATCH --nodes=1                    # Request N nodes
#SBATCH --gres=gpu:8                 # Request M GPU per node
#SBATCH --ntasks-per-node=1          # Request P tasks per node
#SBATCH --cpus-per-task=64           # Request Q core per task; means that P*Q cores per node
#SBATCH --qos=gpu-normal             # Request QOS Type
### #SBATCH --constraint="IB&A100"
#SBATCH --nodelist=r8l40s-a08


###
### The system will alloc 8 or 16 cores per gpu by default.
### If you need more or less, use following:
### #SBATCH --cpus-per-task=K            # Request K cores
###
### 
### Without specifying the constraint, any available nodes that meet the requirement will be allocated
### You can specify the characteristics of the compute nodes, and even the names of the compute nodes
###
### #SBATCH --nodelist=r8l40s-a08
### #SBATCH --constraint="Volta|RTX8000" # Request GPU Type: Volta(V100 or V100S) or RTX8000
###

# set constraint for RTX8000 to meet my cuda

#- Log information

echo "Job start at $(date "+%Y-%m-%d %H:%M:%S")"
echo "Job run at:"
echo "$(hostnamectl)"

#- Load environments
source /tools/module_env.sh
module list                       # list modules loaded

##- Tools
module load cluster-tools/v1.0
module load slurm-tools/v1.0

##- language
module load python3/3.8.16

##- CUDA
module load module load cuda-cudnn/12.4-9.1.1

##- virtualenv
# source xxxxx/activate

echo $(module list)              # list modules loaded
echo $(which gcc)
echo $(which python)
echo $(which python3)

cluster-quota                    # nas quota

nvidia-smi --format=csv --query-gpu=name,driver_version,power.limit # gpu info

CUDA_VISIBLE_DEVICES = 8
#- Warning! Please not change your CUDA_VISIBLE_DEVICES
#- in `.bashrc`, `env.sh`, or your job script
echo "Use GPU ${CUDA_VISIBLE_DEVICES}"                              # which gpus
#- The CUDA_VISIBLE_DEVICES variable is assigned and specified by SLURM
# [EDIT HERE(TODO)]

unset http_proxy
unset https_proxy

# export GGML_CUDA_DISABLE_TENSOR_CORES=1
export EVAL_CONFIG_PATH=configs/nl2sva_human_local_llama_cpp_template_pass_at_k.yaml
export VERIFICATION_PATH=results/nl2sva_human_CodeV-SVA-14B-Q4-pass-at-k-verification.jsonl

expect eval_local/forward_eda.exp $LOGIN_USERNAME eda-00 $LOGIN_PASSWD 4422 # connect to eda server 
CUDA_VISIBLE_DEVICES="0" bash eval_local/start_llama_cpp_server.sh
python -m SVAClient.cli.main --task nl2sva_human --config $EVAL_CONFIG_PATH
python ../Scripts/nl2sva_pass_at_k.py --result-path $VERIFICATION_PATH --n 1

#- End
echo "Job end at $(date "+%Y-%m-%d %H:%M:%S")"
