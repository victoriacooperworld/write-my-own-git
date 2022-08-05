import hashlib
import struct
import os
import posixpath
import re
import stat

import collections

from libgitv.util.TextDecorator import TextDecorator
from libgitv.GitObject import GitObject, object_hash
from libgitv.GitRepository import GitRepository
from libgitv.GitBlob import GitBlob
import libgitv.util.StringHelpers as StringHelper


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
    # path = None


    def __init__(self, fields):
        self.ctime_s, self.ctime_n, self.mtime_s, self.mtime_n, self.dev, self.ino, self.mode, self.uid, self.gid, self.size, self.sha1, self.flags = fields
    
    def create_from_file(repo, path):
        # ctime_s, ctime_n, mtime_s, mtime_n, dev, ino, mode, uid, gid, size, sha1, flags, path
        pathStat = os.stat(path)
        dev = pathStat.st_dev * 0
        ino = pathStat.st_ino * 0
        sha1 = object_hash(open(path, 'rb'), repo=repo, bin=True)
        flags = len(path)
        if flags >= 0xFFF: flags = 0xFFF
        fields = (int(pathStat.st_ctime), (pathStat.st_ctime_ns % 1000000000),
            int(pathStat.st_mtime), (pathStat.st_mtime_ns % 1000000000), dev, ino,
            pathStat.st_mode, pathStat.st_uid, pathStat.st_gid, pathStat.st_size, sha1, flags)
        print(fields)
        objIndex = GitIndexEntry(fields)
        return objIndex

    def serialize(entry):
        buff = struct.pack('!LLLLLLLLLL20sH', entry.ctime_s, entry.ctime_n, entry.mtime_s, entry.mtime_n, entry.dev, entry.ino, entry.mode, entry.uid, entry.gid, entry.size, entry.sha1, entry.flags)
        # buff += entry.path + b'\x00'
        return buff

        


class GitIndex(GitObject):
    format = b'DIRC'
    entries = collections.defaultdict(GitIndexEntry)
    
    def read_index(repo):
        path = repo.file('index')
        with open(path, 'rb') as f:
            data = f.read()
            print(data)
            # Verify hash
            assert hashlib.sha1(data[:-20]).digest() == data[-20:], 'Invalid index checksum'
            # Read headers
            signature, version, num_entries = struct.unpack('!4sLL', data[:12])
            assert signature == b'DIRC', 'Invalid index signature {}'.format(signature)
            assert version == 2, 'Unknown index version {}'. format(version)
            data = data[12:-20]
            entries = collections.defaultdict(GitIndexEntry)
            i = 0
            ctr = 0
            while i + 62 < len(data) and ctr < num_entries:
                fields_end = i + 62
                path_end = data.find(b'\x00', fields_end)
                fields = struct.unpack('!LLLLLLLLLL20sH', data[i:fields_end])
                path = data[fields_end:path_end]
                entry = GitIndexEntry(fields)
                # entries.append(entry)
                entries[str(path)[2:-1]] = entry
                entry_len = ((62 + len(path) + 8) // 8) * 8
                i += entry_len
                ctr += 1
            assert len(entries) == num_entries

            objIndex = GitIndex(repo)
            objIndex.entries = entries
            return objIndex

    def write_index(index):
        path = index.repo.file('index')
        with open(path, 'rb') as f:
            # Write header: signature, version, num_entries
            buff = struct.pack('!4sLL', index.format, 2, len(index.entries))
            # f.write(buff)

            # For each index entry: write index entry
            for entry_path in index.entries:
                buff += index.entries[entry_path].serialize() + StringHelper.toBytes(entry_path) + b'\x00'

            # Write hash digest of index
            sha1 = hashlib.sha1(buff).digest()
            buff += sha1
            print(buff)
            # f.write(buff)
        pass


    def getIgnoreList(index):
        fIgnore = os.path.join(index.repo.gitdir, '../.gitignore')
        if not os.path.exists(fIgnore):
            return []
        liIgnore = []
        for ignPattern in open(fIgnore, 'r'):
            if ignPattern == '\n':
                continue
            bIgnore = not ignPattern.startswith('!')
            if not bIgnore:
                ignPattern = ignPattern.replace('!', '', 1)
            # TODO: Support more complex gitignore patterns
            ignPattern = ignPattern.replace('.', '\.').replace('*', '.*').replace('\n', '')
            ignRegex = re.compile(ignPattern)
            liIgnore.append((ignRegex, bIgnore))
        return liIgnore


    def getChangedFiles(index, targetPath=None):
        repoRoot = os.path.abspath(os.path.join(index.repo.gitdir, '..'))  # Obtain repo's root path
        if targetPath is None:
            targetPath = repoRoot
        toVisit = []
        if os.path.isfile(targetPath):
            toVisit.append(targetPath)
        elif os.path.isdir(targetPath):
            for root, dirs, files in os.walk(targetPath, topdown=True):
                if '.git' in root:
                    continue
                files.sort()
                for tmpF in files:
                    path = os.path.join(root, tmpF)
                    path = os.path.relpath(path, repoRoot)
                    path = path.replace(os.sep, posixpath.sep)
                    toVisit.append(path)

        # Filter down list using gitignore
        liIgnore = index.getIgnoreList()
        liIgnore.reverse()
        i = len(toVisit)-1
        while i >= 0:
            for reIgnore in liIgnore:
                if reIgnore[0].match(toVisit[i]):
                    if reIgnore[1]:
                        toVisit.pop(i)
                    break

            i -= 1
        return toVisit
    
    
    def getStatus(index, targetPath=None):
        toVisit = index.getChangedFiles(targetPath)  # type: list

        liIndex = index.entries  # type: dict

        modified = []
        added = []

        for path in toVisit:
            if path in liIndex:
                sha1Index = liIndex[path].sha1.hex()
                sha1Visit = object_hash(open(path, 'rb'), repo=index.repo)
                if (sha1Index != sha1Visit) and (sha1Index != (object_hash(open(path, 'rb'), repo=index.repo, lf_ending=True))):
                    modified.append((path, 'm'))
            else:
                added.append(path)
        
        for path in liIndex.keys():
            if path not in toVisit:
                modified.append((path, 'd'))
            
        return modified, added


def cmd_ls_files(args):
    repo = GitRepository.repo_find()
    objIndex = GitIndex.read_index(repo)
    for entry in objIndex.entries:
        print(entry.path)


def cmd_status(args):
    repo = GitRepository.repo_find()
    objIndex = GitIndex.read_index(repo)
    modified, added = objIndex.getStatus(args.path)

    if len(modified) > 0:
        print('Changes not staged for commit:')
        print('  (use "git add <file>..." to update what will be committed)')
        print('  (use "git restore <file>..." to discard changes in working directory)'+TextDecorator.FAIL)
        for entry in modified:
            op ='modified' if entry[1]=='m' else 'deleted'
            print(f'\t{op}:\t{entry[0]}')
        print(TextDecorator.ENDC)
    if len(added) > 0:
        print('Untracked files')
        print('  (use "git add <file>..." to include in what will be committed)'+TextDecorator.FAIL)
        for entry in added:
            print('\t' + entry)
        print(TextDecorator.ENDC)


def cmd_add(args):
    repo = GitRepository.repo_find()
    objIndex = GitIndex.read_index(repo) #entries:
    modified, added = objIndex.getStatus(args.path)
    entries = objIndex.entries
    
    for i in modified:
        path = i[0]
        if i[1] == 'm':
            objBlob = GitBlob.create(repo, open(path, 'rb').read())
            sha1 = objBlob.object_write(True, bin=True)
            entries[path].sha1 = sha1
        elif i[1] == 'd':
            #delete the index
            entries.pop(path)
    for path in added:
        objBlob = GitBlob.create(repo, open(path, 'rb').read())
        sha1 = objBlob.object_write(True, bin=True)
        entries[path] = GitIndexEntry.create_from_file(repo, path)
        entries[path].sha1 = sha1

    print('Updating')
    # Write updated index into index file 
    objIndex.write_index()
    