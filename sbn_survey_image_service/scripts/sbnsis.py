#!/usr/bin/env python3
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import time
import signal
import argparse
import subprocess
from argparse import ArgumentParser
from sqlalchemy import MetaData

from sbn_survey_image_service import models
from sbn_survey_image_service.config.env import ENV, env_example
from sbn_survey_image_service.services.database_provider import (
    db_engine,
    data_provider_session,
)


class ServiceException(Exception):
    pass


class Colors:
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


def print_color(string: str, color: Colors = Colors.green, **kwargs: dict) -> None:
    print(color + string + Colors.reset, **kwargs)


def ellipsis(n: int) -> None:
    for _ in range(n):
        time.sleep(1)
        print_color(".", end="", flush=True)
    print()


class SBNSISService:
    def __init__(self):
        parser: ArgumentParser = self.argument_parser()
        self.args: argparse.Namespace = parser.parse_args()

        if hasattr(self.args, "func"):
            try:
                print_color("#" * 72 + "\n")
                self.args.func()  # run requested function
                print_color("\n" + "#" * 72)
            except ServiceException as e:
                print_color(str(e), color=Colors.red)
                print_color("\n" + "#" * 72)
                exit(1)
        else:
            parser.print_usage()

    def _check_venv(self) -> None:
        """Raise warning if not running in a python virtual environment."""
        if os.getenv("VIRTUAL_ENV") is None:
            raise ServiceException("Not in a python virtual environment.")

    def _get_gunicorn_processes(self) -> tuple[int, int]:
        """Return number of running processes for this virtual environment and the parent PID."""
        all_processes: list[str] = (
            subprocess.check_output(["ps", "-ef"]).decode().splitlines()
        )
        venv: str = os.getenv("VIRTUAL_ENV")
        processes: list[str] = [
            process for process in all_processes if f"{venv}/bin/gunicorn" in process
        ]

        ppid: int = 0
        for process in processes:
            ppid = int(process.split()[2])
            if ppid != 1:
                break

        return len(processes), ppid

    def start(self) -> None:
        if self.status(quiet=True)[0] > 0:
            return

        if self.args.dev:
            print_color("Running in development mode.")
            self.start_dev()
        else:
            print_color("Starting service in production mode.")
            self.start_production()

    def start_dev(self) -> None:
        cmd: list[str] = [
            "nodemon",
            "-w",
            "sbn_survey_image_service/**",
            "-e",
            "py,yaml",
            "--exec",
            "python3",
            "-m",
            "sbn_survey_image_service.app",
        ]

        env: dict[str, str] = os.environ.copy()
        env["IS_PRODUCTION"] = "FALSE"
        try:
            subprocess.check_call(cmd, env=env)
        except KeyboardInterrupt:
            pass

    def start_production(self) -> None:
        cmd: list[str] = [
            "gunicorn",
            "sbn_survey_image_service.app:app",
            "--workers",
            str(ENV.LIVE_GUNICORN_INSTANCES),
            "--worker-class",
            "uvicorn.workers.UvicornWorker",
            "--bind",
            f"{ENV.API_HOST}:{ENV.API_PORT}",
            "--access-logfile",
            ENV.SBNSIS_LOG_FILE,
            "--error-logfile",
            ENV.SBNSIS_LOG_FILE,
        ]

        env: dict[str, str] = os.environ.copy()
        env["IS_PRODUCTION"] = "TRUE"
        if self.args.daemon:
            env["IS_DAEMON"] = "TRUE"
            cmd += ["--daemon"]
        else:
            env["IS_DAEMON"] = "FALSE"

        try:
            subprocess.check_call(cmd, env=env)
        except KeyboardInterrupt:
            pass

        if self.args.daemon:
            ellipsis(3)
            self.status()

    def restart(self) -> None:
        n: int
        ppid: int
        n, ppid = self.status()

        if n == 0:
            return

        print_color("\nRestarting service")

        print_color("  - Starting new service", end="", flush=True)
        os.kill(ppid, signal.SIGUSR2)
        ellipsis(1)

        print_color("  - Stopping old service workers", end="", flush=True)
        os.kill(ppid, signal.SIGWINCH)
        ellipsis(10)

        print_color("  - Stopping old service parent process", end="", flush=True)
        os.kill(ppid, signal.SIGQUIT)
        ellipsis(1)

        print()
        self.status()

    def stop(self) -> None:
        """Stop instances running in this virtual environment."""

        self._check_venv()

        n: int
        ppid: int
        n, ppid = self.status()

        if n == 0:
            return

        print_color("\nStopping service", end="", flush=True)
        os.kill(ppid, signal.SIGTERM)
        ellipsis(10)

        if self.status(quiet=True)[0] == 0:
            print_color("Service stopped.")
        else:
            raise ServiceException("Processes still running!")

        print()
        self.rotate_logs()

    def status(self, quiet=False) -> tuple[int, int]:
        """Returns number of running processes and parent PID."""

        self._check_venv()

        n: int
        ppid: int
        n, ppid = self._get_gunicorn_processes()

        if n == 0:
            if not quiet:
                print_color(
                    "No sbnsis-service running from this project's virtual environment."
                )
            return 0, 0

        print_color(
            f"sbnsis-service is running with {n - 1} workers.\nParent PID: {ppid}"
        )

        return n, ppid

    def rotate_logs(self) -> None:
        print_color("Rotating logs.")
        subprocess.check_call(
            [
                "/usr/sbin/logrotate",
                "--force",
                "--state",
                "logrotate.state",
                "logrotate.config",
            ],
            cwd="logging",
        )

    def env_file(self) -> None:
        if os.path.exists(".env") and not self.args.print:
            raise ServiceException("Politely refusing to overwrite .env.")

        if self.args.print:
            print(env_example)
        else:
            with open(".env", "w") as outf:
                outf.write(env_example)
                outf.write("\n")
            print_color("Wrote new .env file.")

    def create_tables(self) -> None:
        session: Session
        with data_provider_session() as session:
            current: MetaData = MetaData()
            current.reflect(db_engine)
            models.Base.metadata.create_all(db_engine)
            updated: MetaData = MetaData()
            updated.reflect(db_engine)

        new: set[str] = set(updated.tables.keys()) - set(current.tables.keys())
        s: str = "" if len(new) == 1 else "s"
        print_color(f"Created {len(new)} database table{s}")
        for name in new:
            print_color(f" - {name}")

    def verify_tables(self) -> None:
        """Verify SBN SIS tables."""

        metadata: MetaData = MetaData()
        metadata.reflect(db_engine)

        missing: bool = False
        name: str
        for name in models.Base.metadata.tables.keys():
            if name not in metadata.tables.keys():
                missing = True
                print_color("{} is missing from database".format(name), Colors.red)

        if not missing:
            print_color("All tables verified")

    def argument_parser(self) -> ArgumentParser:
        parser: ArgumentParser = ArgumentParser(description="SBN Survey Image Service")
        subparsers = parser.add_subparsers(help="sub-command help")

        # start #########
        start_parser: ArgumentParser = subparsers.add_parser(
            "start", help="start the service"
        )
        start_parser.set_defaults(func=self.start)
        start_parser.add_argument(
            "--dev", action="store_true", help="run in development mode"
        )
        start_parser.add_argument(
            "--no-daemon",
            dest="daemon",
            action="store_false",
            help="do not daemonize in production mode",
        )
        start_parser.set_defaults(func=self.start)

        # restart #######
        restart_parser: ArgumentParser = subparsers.add_parser(
            "restart", help="restart the service"
        )
        restart_parser.set_defaults(func=self.restart)

        # status ########
        status_parser: ArgumentParser = subparsers.add_parser(
            "status", help="get service status"
        )
        status_parser.set_defaults(func=self.status)

        # stop ##########
        stop_parser: ArgumentParser = subparsers.add_parser(
            "stop", help="stop the service"
        )
        stop_parser.set_defaults(func=self.stop)

        # rotate-logs ##########
        rotate_logs_parser: ArgumentParser = subparsers.add_parser(
            "rotate-logs", help="force rotate logs"
        )
        rotate_logs_parser.set_defaults(func=self.rotate_logs)

        # env ##########
        env_parser: ArgumentParser = subparsers.add_parser(
            "env", help="create a new .env file"
        )
        env_parser.add_argument(
            "--print",
            action="store_true",
            help="print the defaults, but do not save to .env",
        )
        env_parser.set_defaults(func=self.env_file)

        # verify-tables ###############
        verify_tables_parser: ArgumentParser = subparsers.add_parser(
            "verify-tables", help="verify database tables"
        )
        verify_tables_parser.set_defaults(func=self.verify_tables)

        # create-tables ###############
        create_tables_parser: ArgumentParser = subparsers.add_parser(
            "create-tables", help="create database tables, as needed"
        )
        create_tables_parser.set_defaults(func=self.create_tables)

        return parser


def __main__():
    SBNSISService()
