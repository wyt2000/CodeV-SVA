import uvicorn
from contextlib import asynccontextmanager
import concurrent.futures
import resource
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from Executor import syntax_check, coverage_check, equality_check, equality_check_opt, correctness_verify, testbench_generate, yosys_parse, correctness_verify_impl_only, majority_vote
import asyncio
import argparse
import yaml
import os
import uuid
import traceback
from datetime import datetime
import shutil
import Utils

def process_request(task):
    # resource.setrlimit(
    #     resource.RLIMIT_AS,
    #     (MEMORY_LIMIT, MEMORY_LIMIT)
    # )
    task_data, task_type = task
    work_dir = os.path.join(os.getcwd(), 'logs', f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}")
    os.makedirs(work_dir, exist_ok=True)
    result = None
    if task_type == "/syntax":
        result = syntax_check(task_data, work_dir)
    elif task_type == "/cov":
        result = coverage_check(task_data, work_dir)
    elif task_type == "/verify":
        result = correctness_verify(task_data, work_dir)
    elif task_type == "/verify_impl_only":
        result = correctness_verify_impl_only(task_data, work_dir)
    elif task_type == "/equal":
        result = equality_check(task_data, work_dir)
    elif task_type == "/equal_opt":
        result = equality_check_opt(task_data, work_dir)
    elif task_type == "/testbench":
        result = testbench_generate(task_data, work_dir) 
    elif task_type == "/svparse":
        result = yosys_parse(task_data, work_dir) 
    elif task_type == "/mvote":
        result = majority_vote(task_data, work_dir) 
    shutil.rmtree(work_dir, ignore_errors=True)
    return result

async def worker():
    while True:
        task, response_future = await task_queue.get()

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, process_request, task)
            response_future.set_result(result)
        except Exception as e:
            response_future.set_exception(e)
        finally:
            task_queue.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    for _ in range(MAX_CONCURRENT_TASKS):
        asyncio.create_task(worker())
    yield
    executor.shutdown(wait=True)

app = FastAPI(lifespan=lifespan)

@app.post("/syntax")
@app.post("/cov")
@app.post("/verify")
@app.post("/equal")
@app.post("/equal_opt")
@app.post("/testbench")
@app.post("/verify_impl_only")
@app.post("/svparse")
@app.post("/mvote")
async def handle_request(request: Request):
    if task_queue.full():
        return JSONResponse(content={"error": "Task queue is full, please try again later"}, status_code=503)

    body = await request.json()
    task_type = request.url.path

    response_future = asyncio.Future()
    await task_queue.put(((body, task_type), response_future))

    try:
        results = await response_future
        return results
        # else:
        #     futures = []
        #     for code in code_list:
        #         response_future = asyncio.Future()
        #         await task_queue.put((code, response_future))
        #         futures.append(response_future)
        #     results = []
        #     for future in futures:
        #         result = await future 
        #         results.append(result)
        #     return results
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(content={"error": str(e), "traceback": tb}, status_code=500)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Config file path",
    )
    args = parser.parse_args()
    with open(args.config) as f:
        config = yaml.safe_load(f)
    config = config['verifier']
    Utils.config_global = config

    MAX_CONCURRENT_TASKS = config['max_workers']
    QUEUE_MAX_SIZE       = config['queue_max_size']
    MEMORY_LIMIT         = config['memory_limit'] * (1000 ** 3)
    TIME_LIMIT           = config['time_limit']

    task_queue = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=MAX_CONCURRENT_TASKS)
    uvicorn.run(app, host=config['host'], port=config['port'])
