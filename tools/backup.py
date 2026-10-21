"""Consistent SQLite backup and non-destructive restore (standard library only)."""
import argparse
import os
import sqlite3
from contextlib import closing
from pathlib import Path


def copy_database(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file():
        raise ValueError('Source database does not exist.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation refuses to overwrite an existing desk or backup.
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    try:
        with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as src:
            tables = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'ideas', 'revisions', 'activity'} <= tables:
                raise ValueError('Source is not a StoryFlow database.')
            dst = sqlite3.connect(destination)
            try:
                src.backup(dst)
                if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise ValueError('Database integrity check failed.')
            finally:
                dst.close()
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['backup', 'restore'])
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path,
                        help='New file only; existing files are never overwritten.')
    args = parser.parse_args()
    try:
        output = copy_database(args.source, args.output)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f'{args.operation} failed: {error}\n')
    print(f'{args.operation.capitalize()} verified: {output}')


if __name__ == '__main__':
    main()
