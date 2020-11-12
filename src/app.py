import logging
import asyncio
from typing import Dict, Any

from aioprometheus import Service

from metrics import (
    METRICS,
    WaitingBytesInReceiveQueue,
    ActiveConnections,
)

logger = logging.getLogger(__name__)


class VSPCMetricsApp:

    def __init__(
        self,
        metrics_host: str = "127.0.0.1",
        metrics_port: int = 5050,
        stats_interval: int = 60,
    ):
        self.metrics_host = metrics_host
        self.metrics_port = metrics_port
        self.stats_interval = stats_interval
        self.msvr = Service()
        self.register_metrics()

    def register_metrics(self):
        for metric in METRICS.values():
            self.msvr.register(metric)

    async def start(self):
        """ Start the application """
        await self.msvr.start(addr=self.metrics_host, port=self.metrics_port)
        logger.debug("Serving prometheus metrics on: %s", self.msvr.metrics_url)

        self.stats_task = asyncio.ensure_future(self._updater_stats())

    async def stop(self):
        """ Stop the application """
        if self.stats_task:
            self.stats_task.cancel()
            try:
                await self.stats_task
            except asyncio.CancelledError:
                pass
            self.stats_task = None
        await self.msvr.stop()

    async def _updater_stats(self) -> None:
        """
        This long running coroutine task is responsible for fetching current
        statistics from local environment and then updating internal metrics.
        """
        while True:
            try:
                stats = await self._fetch_stats()
                self._process_stats(stats)
            except Exception as exc:
                logger.error(f"Error fetching stats: {exc}")
            await asyncio.sleep(self.stats_interval)

    async def _fetch_stats(self) -> Dict[Any, Any]:
        waiting_bytes = await self._get_waiting_bytes_in_queue()
        active_connections = await self._get_active_connections()
        return {
            WaitingBytesInReceiveQueue.name: {
                "label": "waiting_bytes",
                "value": waiting_bytes,
            },
            ActiveConnections.name: {
                "label": "active_connections",
                "value": active_connections,
            },
        }

    async def _run_command(
        self,
        program,
        *args,
        std_in=None,
        std_out=asyncio.subprocess.PIPE,
        std_err=asyncio.subprocess.PIPE,
    ):
        """Run command in subprocess."""
        process = await asyncio.create_subprocess_exec(
            program, *args, stdin=std_in, stdout=std_out, stderr=std_err
        )

        logger.debug(f"Started exec '{program}' with '{args}', pid={process.pid}")
        # Wait for the subprocess to finish
        stdout, stderr = await process.communicate()
        # Progress
        if process.returncode == 0:
            logger.debug(
                f"Done exec '{program}' with '{args}',"
                f" pid={process.pid}, result: {stdout.decode().strip()}"
            )
        else:
            logger.debug(
                f"Failed exec '{program}' with '{args}',"
                f" pid={process.pid}, result: {stdout.decode().strip()}"
            )
        result = stdout.decode().strip()
        return result

    async def _get_waiting_bytes_in_queue(self):
        cmd_tcp_connections = ["ss", "-nt"]
        cmd_filter_new_connections = ["grep", "-v", "-E", "ESTAB +0 +0"]
        cmd_waiting_bytes = ["awk", "BEGIN {sum=0} {sum=sum+$2} END {print sum}"]

        cmd_sequence = (
            cmd_tcp_connections,
            cmd_filter_new_connections,
            cmd_waiting_bytes,
        )
        for cmd in cmd_sequence:
            result = None
            result = await self._run_command(cmd[0], *cmd[1:], std_in=result)
        return int(result)

    async def _get_active_connections(self):
        cmd_active_tcp_connections = ["awk", "END {print NR}", "/proc/net/tcp"]
        active_connections = await self._run_command(
            cmd_active_tcp_connections[0],
            *cmd_active_tcp_connections[1:],
        )
        return int(active_connections)

    def _process_stats(self, stats: dict) -> None:
        """Process statistics into exported metrics."""
        for metric_name, collected_stats in stats.items():
            METRICS[metric_name].set({}, collected_stats["value"])
