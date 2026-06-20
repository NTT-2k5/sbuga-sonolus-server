import argparse
import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from helpers.config_loader import set_config_path, get_config

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", default="config.yml")
parser.add_argument("-o", "--output", default="sbuga_sonolus_dump.sql")
args = parser.parse_args()

set_config_path(args.config)
psql = get_config()["psql"]

subprocess.run(
    [
        "pg_dump",
        "-h",
        psql["host"],
        "-p",
        str(psql["port"]),
        "-U",
        psql["user"],
        "-d",
        psql["database"],
        "-F",
        "c",
        "-f",
        args.output,
    ],
    env={**os.environ, "PGPASSWORD": psql["password"]},
    check=True,
)

print(f"dumped to {args.output}")
