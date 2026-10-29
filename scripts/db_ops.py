"""SQLite consistent backup / guarded restore; stop all application workers before restoring."""
import argparse
import hashlib
import sqlite3
import shutil
from pathlib import Path


def checksum(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def backup(source,dest):
    if not source.is_file():raise FileNotFoundError(source)
    dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():raise FileExistsError('Destination already exists')
    with sqlite3.connect(f'file:{source}?mode=ro',uri=True) as src,sqlite3.connect(dest) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('Backup integrity check failed')
    return checksum(dest)


def restore(source,dest,force=False):
    if not force:raise RuntimeError('Restore requires --force, and all application processes must be stopped')
    if not source.is_file():raise FileNotFoundError(source)
    with sqlite3.connect(f'file:{source}?mode=ro',uri=True) as c:
        if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise RuntimeError('Backup integrity check failed')
    if dest.exists():raise FileExistsError('Refusing to overwrite existing database; move it aside manually first')
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,dest)
    return checksum(dest)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['backup','restore'])
    parser.add_argument('source',type=Path)
    parser.add_argument('destination',type=Path)
    parser.add_argument('--force',action='store_true')
    opts=parser.parse_args()
    print('sha256:',backup(opts.source,opts.destination) if opts.operation=='backup' else restore(opts.source,opts.destination,opts.force))
