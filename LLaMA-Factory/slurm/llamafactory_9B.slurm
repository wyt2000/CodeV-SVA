#!/bin/bash

#- Job parameters

# (TODO)
# Please modify job name
#SBATCH -J llamafactory

#- Resources

# (TODO)
# Please modify your requirements

#SBATCH -p r8nv-gpu-hw-80g        # Submit to 'nv-gpu' Partitiion
### #SBATCH -t 0-03:00:00                # Run for a maximum time of 0 days, 12 hours, 00 mins, 00 secs
#SBATCH --nodes=1                    # Request N nodes
#SBATCH --gres=gpu:4                 # Request M GPU per node
#SBATCH --ntasks-per-node=1          # Request P tasks per node
#SBATCH --cpus-per-task=64           # Request Q core per task; means that P*Q cores per node
#SBATCH --qos=gpu-normal                 # Request QOS Type
#SBATCH --constraint="IB&A100_80G"

#- Log information

echo "Job start at $(date "+%Y-%m-%d %H:%M:%S")"
echo "Job run at:"
echo "$(hostnamectl)"

#- Load environments
source /tools/module_env.sh
module list                       # list modules loaded

##- CUDA
module load cuda-cudnn/12.4-9.1.1

nvidia-smi --format=csv --query-gpu=name,driver_version,power.limit # gpu info

ulimit -u $(ulimit -H -u)
ulimit -n $(ulimit -H -n)
ulimit -s unlimited  # 栈大小 (解决 mmap failed / Segmentation fault)
ulimit -v unlimited  # 虚拟内存 (解决 mmap failed)
ulimit -l unlimited  # 锁定内存 (对 NCCL/RDMA 通信很重要)
ulimit -a

cd "${LLAMA_FACTORY_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
. .venv/bin/activate
echo $LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$(echo "$LD_LIBRARY_PATH" | tr ':' '\n' \
  | grep -v '/tools/cluster-software/cuda-cudnn/cuda-12.4.1-9.1.1/lib64' \
  | paste -sd ':' -)
echo $LD_LIBRARY_PATH

export WANDB_MODE=offline
llamafactory-cli train examples/train_full/sft_qwen3p5_9B_0407.yaml

#- End
echo "Job end at $(date "+%Y-%m-%d %H:%M:%S")"
