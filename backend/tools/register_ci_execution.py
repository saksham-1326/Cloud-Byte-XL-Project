"""Trusted local registration; never infers the latest deployment."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app import get_db_connection
from backend.ci_callbacks import register_execution, CallbackError
import psycopg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repository', required=True)
    parser.add_argument('--run-id', type=int, required=True)
    parser.add_argument('--attempt', type=int, required=True)
    parser.add_argument('--commit-sha', required=True)
    parser.add_argument('--deployment-id', type=int, required=True)
    args = parser.parse_args()
    try:
        register_execution(get_db_connection, args.repository, args.run_id,
                           args.attempt, args.commit_sha, args.deployment_id)
    except CallbackError as error:
        print('Registration rejected: ' + error.code)
        return 1
    except psycopg.Error:
        print('Registration failed; verify database availability, schema, and explicit association.')
        return 1
    print('Explicit workflow/deployment association committed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
