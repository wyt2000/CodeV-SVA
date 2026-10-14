import argparse

from llmkit_data.utils.router2 import RouterApp

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple Router Application")
    parser.add_argument(
        "--worker-urls",
        dest="worker_urls_str",
        type=str,
        required=True,
        help="Comma-separated list of worker URLs (e.g., http://localhost:8001,http://localhost:8002)",
    )
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Host for the router"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the router to listen on",
    )
    args = parser.parse_args()

    worker_urls = [url.strip() for url in args.worker_urls_str.split(",")]

    if not worker_urls:
        raise ValueError("At least one worker URL must be provided.")

    router_app = RouterApp(worker_urls, args.host, args.port)
    router_app.run()
