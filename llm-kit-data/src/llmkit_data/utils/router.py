import httpx
import uvicorn
import logging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import json

logger = logging.getLogger("uvicorn")

class RouterApp:
    def __init__(self, worker_info_map: dict[str, list], host: str = "0.0.0.0", port: int = 8000, timeout: int = 1000):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.app = FastAPI()
        self.active_responses = {
            model : {f"http://{host}:{port}": 0 for host, port in worker_info}
            for model, worker_info in worker_info_map.items()
        }
        self.default_model = list(worker_info_map.keys())[0]
        self._setup_routes()

    async def stream_proxy_response(self, response: httpx.Response, model: str, worker_url: str):
        try:
            async for chunk in response.aiter_bytes():
                yield chunk
        finally:
            self.active_responses[model][worker_url] -= 1

    def is_serious_error(self, error: httpx.HTTPError) -> bool:
        """
        Determine if the error is serious enough to remove the worker.
        """
        if isinstance(
            error,
            (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError),
        ):
            return True
        return False

    def _setup_routes(self):
        @self.app.api_route(
            "/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )
        async def route_to_worker(full_path: str, request: Request):
            # Extract headers to forward
            headers_to_forward = dict(request.headers)
            # Parse model name
            try:
                model = headers_to_forward["model"]
            except Exception as err:
                model = self.default_model
            headers_to_forward.pop("host", None)
            headers_to_forward.pop("model", None)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    request_body = await request.body()

                    # Get worker url and update response counter
                    active_responses = self.active_responses[model]
                    worker_url = min(active_responses, key=active_responses.get)
                    active_responses[worker_url] += 1
                    target_url = f"{worker_url}{request.url.path}"

                    # Forward to worker
                    response = await client.request(
                        request.method,
                        target_url,
                        headers=headers_to_forward,
                        params=request.query_params,
                        content=request_body,
                        timeout=self.timeout,
                    )

                    response.raise_for_status()

                    return StreamingResponse(
                        self.stream_proxy_response(response, model, worker_url),
                        status_code=response.status_code,
                        headers=response.headers,
                    )

                except httpx.HTTPError as e:
                    active_responses[worker_url] -= 1
                    if self.is_serious_error(e):
                        # Remove worker
                        active_responses.pop(worker_url, None)
                        logger.error(
                            f"Removed worker {worker_url} due to serious error: {e}"
                        )
                    return {"error": f"Error communicating with worker: {e}"}, 502
                except Exception as e:
                    active_responses[worker_url] -= 1
                    return {"error": f"Unexpected error: {e}"}, 500

    def run(self):
        # TODO uvicorn's logger is in warning level
        logger.warning(f"Router is starting on port {self.port}")
        logger.warning(f"Model list: {self.active_responses.keys()}")
        for model, active_responses in self.active_responses.items():
            logger.warning(f"- Model name: {model}")
            logger.warning(f"- Forwarding requests to workers: {active_responses.keys()}")
        uvicorn.run(self.app, host=self.host, port=self.port)
