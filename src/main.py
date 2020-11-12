import logging
import asyncio
import argparse

from app import VSPCMetricsApp


def setup_logging(args):
    logging.basicConfig(
        format='%(asctime)s %(process)d %(levelname)s %(filename)s:%(lineno)d %(message)s',
        level=args.log_level,
    )
    # Silence asyncio and aiohttp loggers
    logging.getLogger("asyncio").setLevel(logging.ERROR)
    logging.getLogger("aiohttp").setLevel(logging.ERROR)


def setup_args():
    args = argparse.ArgumentParser(
        prog="vmware-vspc-exporter", description="vmware-vspc Prometheus Exporter"
    )
    args.add_argument(
        "--host",
        metavar="<exporter host>",
        type=str,
        default="0.0.0.0",
        help="The address to expose collected metrics from. Default is all interfaces.",
    )
    args.add_argument(
        "--port",
        metavar="<exporter port>",
        type=int,
        default=5050,
        help="The port to expose collected metrics from. Default is 5050",
    )
    args.add_argument(
        "--stats-interval",
        metavar="<time to next collection of metrics>",
        type=int,
        default=60,
        help="The interval to wait for the next collection of metrics",
    )
    args.add_argument(
        "--log-level", default="INFO", help="Log level",
    )
    args = args.parse_args()
    return args


def main():
    args = setup_args()
    loop = asyncio.get_event_loop()
    setup_logging(args)

    app = VSPCMetricsApp(
        metrics_host=args.host,
        metrics_port=args.port,
        stats_interval=args.stats_interval,
    )
    loop.run_until_complete(app.start())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(app.stop())
    loop.stop()
    loop.close()


if __name__ == "__main__":
    main()
