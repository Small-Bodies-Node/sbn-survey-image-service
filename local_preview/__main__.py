import argparse
import signal
import tempfile
from pathlib import Path

from werkzeug.serving import make_server

from .create_app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run actual survey preview renderers locally, without the production database."
    )
    parser.add_argument("--port", type=int, default=5010)
    parser.add_argument(
        "--cache-dir", type=Path, help="Session directory; the caller owns its cleanup"
    )
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")

    def interrupt(_signal, _frame) -> None:
        raise KeyboardInterrupt

    # Leave the TemporaryDirectory context on both Ctrl+C and supervisor shutdown.
    signal.signal(signal.SIGTERM, interrupt)

    def serve(cache: Path) -> None:
        print(
            f"Local preview renderer: http://127.0.0.1:{args.port}/ (cache: {cache})",
            flush=True,
        )
        with make_server(
            "127.0.0.1", args.port, create_app(cache), threaded=True
        ) as server:
            server.serve_forever()

    if args.cache_dir:
        serve(args.cache_dir.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="catch-local-images-") as directory:
            serve(Path(directory))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
