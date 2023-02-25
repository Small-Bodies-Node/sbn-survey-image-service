#!/usr/bin/env python3
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
from typing import List
import argparse
from argparse import ArgumentParser
import subprocess


class colors:
    """Terminal color codes."""

    reset = "\033[00m"
    black = "\033[30m"
    red = "\033[31m"
    green = "\033[32m"
    yellow = "\033[33m"
    blue = "\033[34m"
    magenta = "\033[35m"
    cyan = "\033[36m"
    white = "\033[37m"


def start_service(args: argparse.Namespace) -> None:
    if status_service(args) > 0:
        return


def restart_service(args: argparse.Namespace) -> None:
    if status_service(args) == 0:
        return


def check_venv() -> None:
    """Raise warning if not running in a python virtual environment."""
    if os.getenv("VIRTUAL_ENV") is None:
        raise UserWarning("Not in a python virtual environment.")


def status_service(args: argparse.Namespace) -> int:
    """Returns number of running sbnsis-service (gunicorn) processes."""

    check_venv()

    processes: List[str] = subprocess.check_output(["ps", "-ef"]).decode().splitlines()
    venv: str = os.getenv("VIRTUAL_ENV")
    gunicorn_processes: List[str] = [
        process for process in processes if f"{venv}/bin/sbnsis-service" in process
    ]

    n: int = len(gunicorn_processes)
    if n == 0:
        print(
            "No sbnsis-service is running from this project's virtual environment at the moment."
        )
        return 0

    ppid: str
    for process in gunicorn_processes:
        ppid = process.split()[2]
        if ppid != "1":
            break

    print(
        f"""sbnsis-service is running with {n} processes.
Parent PID: {ppid}"""
    )

    return n


def stop_service(args: argparse.Namespace) -> None:
    pass


def parse_arguments() -> ArgumentParser:
    parser: ArgumentParser = ArgumentParser(description="SBN Survey Image Service")
    subparsers: argparse._SubParsersAction = parser.add_subparsers(
        help="sub-command help"
    )

    # start #########
    start_parser: ArgumentParser = subparsers.add_parser(
        "start", help="start the service"
    )
    start_parser.set_defaults(func=start_service)
    start_parser.add_argument(
        "--dev", action="store_true", help="run in development mode"
    )
    start_parser.add_argument(
        "--no-daemon",
        dest="daemon",
        action="store_false",
        help="do not run in daemon mode (implied with --dev)",
    )

    # restart #######
    restart_parser: ArgumentParser = subparsers.add_parser(
        "restart", help="restart the service"
    )
    restart_parser.set_defaults(func=restart_service)

    # status ########
    status_parser: ArgumentParser = subparsers.add_parser(
        "status", help="get service status"
    )
    status_parser.set_defaults(func=status_service)

    # stop ##########
    stop_parser: ArgumentParser = subparsers.add_parser("stop", help="stop the service")
    stop_parser.set_defaults(func=stop_service)

    return parser


if __name__ == "__main__":
    parser: ArgumentParser = parse_arguments()
    args: argparse.Namespace = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_usage()
