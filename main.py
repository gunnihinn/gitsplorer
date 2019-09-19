#!/usr/bin/env python

import argparse
import errno
import os
import time
import stat
import sys

from fuse import FUSE, FuseOSError, Operations
import pygit2


class Stat:

    def __init__(self, obj, mode, size, nlink):
        self.obj = obj
        self.mode = mode
        self.nlink = nlink
        self.size = size


def get_object(repo, root, path):
    partial = os.path.normpath(path).lstrip('/')

    parts = []
    while True:
        head, tail = os.path.split(partial)

        if not head and not tail:
            break
        if tail:
            parts.append(tail)
        partial = head

    mode = 0o700
    size = 1 << 12
    while parts:
        part = parts.pop()
        for e in root:
            if e.name == part:
                root = repo.get(e.id)
                mode = e.filemode
                break
        else:
            raise FuseOSError(errno.ENOENT)

    if root.type == pygit2.GIT_OBJ_BLOB:
        size = root.size
        nlink = 1
        mode = mode | stat.S_IFREG
    else:
        nlink = len(root)
        mode = mode | stat.S_IFDIR

    return Stat(root, mode, size, nlink)


class Gitsplorer(Operations):

    def __init__(self, root, commit=None):
        self.root = root
        self.repo = pygit2.Repository(os.path.join(root, '.git'))
        self.time = int(time.time())
        self.uid = os.getuid()
        self.gid = os.getgid()

        if commit is None:
            self.commit = self.repo.head.peel()
        else:
            self.commit = self.repo.get(commit)
        assert isinstance(self.commit, pygit2.Commit)

    def _full_path(self, partial):
        partial = partial.lstrip("/")
        path = os.path.join(self.root, partial)
        return path

    def get_object(self, path):
        return get_object(self.repo, self.commit.tree, path)

    # Filesystem
    def access(self, path, mode):
        return

    def getattr(self, path, fh=None):
        st = self.get_object(path)

        return {
            'st_atime': self.time,
            'st_ctime': self.time,
            'st_mtime': self.time,
            'st_uid': self.uid,
            'st_gid': self.gid,
            'st_mode': st.mode,
            'st_nlink': st.nlink,
            'st_size': st.size,
        }

    def readdir(self, path, fh):
        stat = self.get_object(path)

        dirents = ['.', '..']
        if stat.obj.type == pygit2.GIT_OBJ_TREE:
            for e in stat.obj:
                dirents.append(e.name)

        for r in dirents:
            yield r

    # Files
    def open(self, path, flags):
        return 1

    def read(self, path, length, offset, fh):
        stat = self.get_object(path)
        return stat.obj.data[offset:offset+length]

    def release(self, path, fh):
        return


def main(mountpoint, root, commit=None):
    FUSE(Gitsplorer(root, commit=commit), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', help="Root of filesystem to mount", default='.')
    parser.add_argument('mountpoint', help="Mount point of filesystem")
    parser.add_argument('--commit')
    args = parser.parse_args()

    main(args.mountpoint, args.root, commit=args.commit)
