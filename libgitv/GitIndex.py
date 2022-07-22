import hashlib
import struct
from queue import SimpleQueue  # Queue data structrue
import os
import posixpath
from libgitv.GitObject import GitObject
from libgitv.GitRepository import GitRepository


class GitIndexEntry(object):
    ctime_s = None
    ctime_n = None
    """The last time a file's metadata changed.  This is a tuple (seconds, nanoseconds)"""

    mtime_s = None
    mtime_n = None
    """The last time a file's data changed.  This is a tuple (seconds, nanoseconds)"""

    dev = None
    """The ID of device containing this file"""
    ino = None
    """The file's inode number"""
    mode = None
    """The object type, either b1000 (regular), b1010 (symlink), b1110 (gitlink). """
    """The object permissions, an integer."""
    uid = None
    """User ID of owner"""
    gid = None
    """Group ID of ownner (according to stat 2.  Isn'th)"""
    size = None
    """Size of this object, in bytes"""
    sha1 = None
    """The object's hash as a hex string"""
    flags = None
    """Length of the name if < 0xFFF (yes, three Fs), -1 otherwise"""
    path = None


    def __init__(self, fields):
        self.ctime_s, self.ctime_n, self.mtime_s, self.mtime_n, self.dev, self.ino, self.mode, self.uid, self.gid, self.size, self.sha1, self.flags, self.path = fields
    

        


class GitIndex(GitObject):
  format = b'DIRC'

  def read_index(repo):
    path = repo.file('index')
    with open(path, 'rb') as f:
        data = f.read()
        # Verify hash
        assert hashlib.sha1(data[:-20]).digest() == data[-20:], 'Invalid index checksum'
        # Read headers
        signature, version, num_entries = struct.unpack('!4sLL', data[:12])
        assert signature == b'DIRC', 'Invalid index signature {}'.format(signature)
        assert version == 2, 'Unknown index version {}'. format(version)
        data = data[12:-20]
        entries = []
        i = 0
        ctr = 0
        while i + 62 < len(data) and ctr < num_entries:
            fields_end = i + 62
            path_end = data.find(b'\x00', fields_end)
            fields = struct.unpack('!LLLLLLLLLL20sH', data[i:fields_end])
            path = data[fields_end:path_end]
            entry = GitIndexEntry((*fields, path.decode()))
            entries.append(entry)
            entry_len = ((62 + len(path) + 8) // 8) * 8
            i += entry_len
            ctr += 1
        assert len(entries) == num_entries

        objIndex = GitIndex(repo)
        objIndex.entries = entries
        return objIndex

def cmd_ls_files(args):
    repo = GitRepository.repo_find()
    objIndex = GitIndex.read_index(repo)
    for entry in objIndex.entries:
        print(entry.path)

def cmd_add(args):
    repo = GitRepository.repo_find()
    repoRoot = os.path.join(repo.gitdir, '..')  # Obtain repo's root path
    toVisit = SimpleQueue()
    if os.path.isfile(args.path):
        toVisit.put(args.path)
    elif os.path.isdir(args.path):
        for root, dirs, files in os.walk(args.path, topdown=True):
            if '.git' in root:
                continue
            for tmpF in files:
                # TODO: Check if git ignore excludes the file
                path = os.path.join(root, tmpF)
                path = os.path.relpath(path, repoRoot)
                path = path.replace(os.sep, posixpath.sep)
                toVisit.put(path)

    while not toVisit.empty():
        path = toVisit.get()
        print(path)
        # TODO: Detect change. If changed, update index
    pass