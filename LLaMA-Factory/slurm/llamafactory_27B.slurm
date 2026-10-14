#!/bin/bash

#- Job parameters

# (TODO)
# Please modify job name
#SBATCH -J llamafactory

#- Resources

# (TODO)
# Please modify your requirements

#SBATCH -p r8nv-gpu-hw-80g        # Submit to 'nv-gpu' Partitiion
#SBATCH --nodes=2                    # Request N nodes
#SBATCH --gres=gpu:8                 # Request M GPU per node
#SBATCH --ntasks-per-node=1          # Request P tasks per node
#SBATCH --cpus-per-task=96
#SBATCH --qos=gpu-normal                 # Request QOS Type
#SBATCH --constraint="IB&A100_80G"

export USER_GPUS_PER_NODE=8
export USER_NGPUS=$(($USER_GPUS_PER_NODE * $SLURM_NNODES))
nodelist_h_format=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | \
    awk -v gpu=$USER_GPUS_PER_NODE '{printf ((NR>1?",":"")$0":%s"), gpu}')

export MASTER_ADDR=$(scontrol show hostnames "$SLURM_JOB_NODELIST" | head -n 1)
export MASTER_PORT=$(expr 50000 + $(echo -n "$SLURM_JOBID" | tail -c 4))
export WORLD_SIZE=${USER_NGPUS}
export FORCE_TORCHRUN=1
export NPROC_PER_NODE=${USER_GPUS_PER_NODE}

export NCCL_IB_DISABLE=0
export NCCL_P2P_DISABLE=0
export NCCL_IB_CUDA_SUPPORT=1
export NCCL_NET_GDR_LEVEL=2
export NCCL_IB_HCA="mlx5_0,mlx5_1,mlx5_2,mlx5_3"

echo "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX "
echo "Nodelist:=        " $SLURM_JOB_NODELIST
echo "Nodelistname:=    " $nodelist_h_format
echo "Number of nodes (NNODES):= " $SLURM_NNODES
echo "Ntasks per node:= " $SLURM_NTASKS_PER_NODE
echo "Ntasks of jobs:=  " $SLURM_NTASKS
echo "NGPUs of jobs:=   " $USER_NGPUS
echo "MASTER_ADDR:=     " $MASTER_ADDR
echo "MASTER_PORT:=     " $MASTER_PORT
echo "WORLD_SIZE:=      " $WORLD_SIZE
echo "NPROC_PER_NODE:=  " $NPROC_PER_NODE
echo "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX "

# set constraint for RTX8000 to meet my cuda

#- Log information

echo "Job start at $(date "+%Y-%m-%d %H:%M:%S")"
echo "Job run at:"
echo "$(hostnamectl)"

#- Load environments
source /tools/module_env.sh
module list                       # list modules loaded

##- CUDA
module load cuda-cudnn/12.4-9.1.1

ulimit -l unlimited  # 锁定内存 (对 NCCL/RDMA 通信很重要)
ulimit -v unlimited  # 虚拟内存 (解决 mmap failed)
ulimit -n 65535
ulimit -u 4125556
ulimit -s unlimited  # 栈大小 (解决 mmap failed / Segmentation fault)
ulimit -a

echo "=============== srun begins =================="
srun --kill-on-bad-exit=1 bash -lc '
  THIS_UP_IB_DEV=$(ibdev2netdev | grep Up | grep ib | awk "{print \$1}" | paste -sd "," -)
  if [[ -n ${THIS_UP_IB_DEV} ]]; then
    export NCCL_IB_HCA=${THIS_UP_IB_DEV}
  fi

  node_msg="
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Task run on: $(hostname -s);
GPU devices: $(nvidia-smi);
InfiniBand devices: $(ibdev2netdev);
NCCL_IB_HCA=${NCCL_IB_HCA};
Task run on: $(hostname -s), PID: ${SLURM_TASK_PID};
USE GPU ${CUDA_VISIBLE_DEVICES} of this node (GPUs_PER_Node, not PER_Task);
GlobalID : ${SLURM_PROCID} of ${SLURM_NTASKS};
NodeID   : ${SLURM_NODEID} of ${SLURM_NNODES};
LocalID  : ${SLURM_LOCALID} of ${SLURM_NTASKS_PER_NODE};
GPUs_PER_Task = ${USER_NGPUS} / ${SLURM_NTASKS} = $((${USER_NGPUS}/${SLURM_NTASKS}));
MASTER_ADDR   = ${MASTER_ADDR};
MASTER_PORT   = ${MASTER_PORT};
WORLD_SIZE    = ${WORLD_SIZE};
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
"
  echo "${node_msg}"

  ulimit -l unlimited
  ulimit -v unlimited
  ulimit -n 65535
  ulimit -u 4125556
  ulimit -s unlimited

  source /tools/module_env.sh
  module load cuda-cudnn/12.4-9.1.1

  export JOB_LOCAL_DIR=/tmp/${USER}/llamafactory_${SLURM_JOB_ID}_${SLURM_NODEID}
  export TMPDIR=${JOB_LOCAL_DIR}/tmp
  export HF_HOME=${JOB_LOCAL_DIR}/hf
  export HF_DATASETS_CACHE=${HF_HOME}/datasets
  export HF_HUB_CACHE=${HF_HOME}/hub
  export TRANSFORMERS_CACHE=${HF_HOME}/transformers
  export TRITON_CACHE_DIR=${JOB_LOCAL_DIR}/triton
  export TORCH_EXTENSIONS_DIR=${JOB_LOCAL_DIR}/torch_extensions
  mkdir -p "${TMPDIR}" "${HF_DATASETS_CACHE}" "${HF_HUB_CACHE}" "${TRANSFORMERS_CACHE}" \
    "${TRITON_CACHE_DIR}" "${TORCH_EXTENSIONS_DIR}"

  cd "${LLAMA_FACTORY_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
  . .venv/bin/activate

  echo "Training config summary:"

  echo "${LD_LIBRARY_PATH}"
  export LD_LIBRARY_PATH=$(echo "${LD_LIBRARY_PATH}" | tr ":" "\n" \
    | grep -v "/tools/cluster-software/cuda-cudnn/cuda-12.4.1-9.1.1/lib64" \
    | paste -sd ":" -)
  echo "${LD_LIBRARY_PATH}"

  export NODE_RANK=${SLURM_NODEID}
  export NNODES=${SLURM_NNODES}

  export WANDB_MODE=offline
  llamafactory-cli train examples/train_full/sft_qwen3p5_27B_0514.yaml

  slurm-gpu-atop-log-stats "${SLURM_JOB_ID}" "${CUDA_VISIBLE_DEVICES}"
'

#- End
echo "Job end at $(date "+%Y-%m-%d %H:%M:%S")"
