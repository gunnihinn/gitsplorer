#!/usr/bin/env python

from __future__ import with_statement

import argparse
import errno
import os
import sys

from fuse import FUSE, FuseOSError, Operations


class Gitsplorer(Operations):
    def __init__(self, root):
        self.root = root

    def _full_path(self, partial):
        partial = partial.lstrip("/")
        path = os.path.join(self.root, partial)
        return path

    # Filesystem
    def access(self, path, mode):
        return

    def chmod(self, path, mode):
        return 0

    def chown(self, path, uid, gid):
        return 0

    def getattr(self, path, fh=None):
        print('getattr', path)
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return {
            'st_atime': st.st_atime,
            'st_ctime': st.st_ctime,
            'st_gid': st.st_gid,
            'st_mode': st.st_mode,
            'st_mtime': st.st_mtime,
            'st_nlink': st.st_nlink,
            'st_size': st.st_size,
            'st_uid': st.st_uid,
        }

    def readdir(self, path, fh):
        print('readdir', path)
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    def readlink(self, path):
        pathname = os.readlink(self._full_path(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def mknod(self, path, mode, dev):
        return 0

    def rmdir(self, path):
        return 0

    def mkdir(self, path, mode):
        return 0

    def statfs(self, path):
        print('statfs', path)
        full_path = self._full_path(path)
        stv = os.statvfs(full_path)
        return {
            'f_bavail': st.f_bavail,
            'f_bfree': st.f_bfree,
            'f_blocks': st.f_blocks,
            'f_bsize': st.f_bsize,
            'f_favail': st.f_favail,
            'f_ffree': st.f_ffree,
            'f_files': st.f_files,
            'f_flag': st.f_flag,
            'f_frsize': st.f_frsize,
            'f_namemax': st.f_namemax,
        }

    def unlink(self, path):
        return 0

    def symlink(self, name, target):
        return 0

    def rename(self, old, new):
        return 0

    def link(self, target, name):
        return 0

    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)

    # Files
    def open(self, path, flags):
        print('open', path)
        full_path = self._full_path(path)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        return 0

    def read(self, path, length, offset, fh):
        print('read', path)
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        return len(buf)

    def truncate(self, path, length, fh=None):
        return 0

    def flush(self, path, fh):
        return 0

    def release(self, path, fh):
        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return 0


def main(mountpoint, root):
    FUSE(Gitsplorer(root), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', help="Root of filesystem to mount")
    parser.add_argument('mountpoint', help="Mount point of filesystem")
    args = parser.parse_args()
    main(args.mountpoint, args.root)
