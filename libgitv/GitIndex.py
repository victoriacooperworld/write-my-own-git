import hashlib
import struct
import os
import posixpath
import re

from libgitv.util.TextDecorator import TextDecorator
from libgitv.GitObject import GitObject, object_hash
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
        toVisit = index.getChangedFiles(targetPath)

        liIndex = index.entries
        szIndex, szVisit = len(liIndex), len(toVisit)
        i, j = 0, 0

        modified = []
        added = []

        while i < szIndex and j < szVisit:
            if liIndex[i].path == toVisit[j]:
                sha1Index = liIndex[i].sha1.hex()
                sha1Visit = object_hash(open(toVisit[j], 'rb'), repo=index.repo)
                # Check for modification. Check both native line ending and git LF line ending
                if (sha1Index != sha1Visit) and (sha1Index != (object_hash(open(toVisit[j], 'rb'), repo=index.repo, lf_ending=True))):
                    modified.append((liIndex[i].path, 'm'))
                i += 1
                j += 1
                pass
            elif liIndex[i].path < toVisit[j]:
                modified.append((liIndex[i].path, 'd'))
                i += 1
            else:
                added.append(toVisit[j])
                j += 1
        while i < szIndex:
            modified.append((liIndex[i].path, 'd'))
            i += 1
        while j < szVisit:
            added.append(toVisit[j])
            j += 1
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
    objIndex = GitIndex.read_index(repo)
    modified, added = objIndex.getStatus(args.path)
    
    # TODO: Update index by removing deleted entries, updating modified entries, and adding new entries