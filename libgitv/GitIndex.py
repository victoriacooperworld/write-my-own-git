import hashlib
import struct
from libgitv.GitObject import GitObject


class GitIndexEntry(object):
    ctime = None
    """The last time a file's metadata changed.  This is a tuple (seconds, nanoseconds)"""

    mtime = None
    """The last time a file's data changed.  This is a tuple (seconds, nanoseconds)"""

    dev = None
    """The ID of device containing this file"""
    ino = None
    """The file's inode number"""
    mode_type = None
    """The object type, either b1000 (regular), b1010 (symlink), b1110 (gitlink). """
    mode_perms = None
    """The object permissions, an integer."""
    uid = None
    """User ID of owner"""
    gid = None
    """Group ID of ownner (according to stat 2.  Isn'th)"""
    size = None
    """Size of this object, in bytes"""
    obj = None
    """The object's hash as a hex string"""
    flag_assume_valid = None
    flag_extended = None
    flag_stage = None
    flag_name_length = None
    """Length of the name if < 0xFFF (yes, three Fs), -1 otherwise"""

    name = None


class GitIndex(GitObject):
  format = b'DIRC'

  def read_index(repo):
    
    path = repo.file('index')
    with open(path, 'rb') as f:
      data = path.read()
      # Verify hash
      assert hashlib.sha1(data[:-20]).digest() == data[-20:0], 'Invalid index checksum'
      # Read headers
      signature, version, num_entries = struct.unpack('!4sLL', data[:12])
      assert signature == b'DIRC', 'Invalid index signature {}'.format(signature)
      assert version == 2, 'Unknown index version {}'. format(version)
      data = data[12:-20]
      entries = []
      i = 0
      while i + 62 < len(data):
        fields_end = i + 62
        fields = struct.unpack('!LLLLLLLLLL20sH', data[i:fields_end])
        path_end = data.index(b'\x00', fields_end)
        path = data[fields_end:path_end]
        entry = GitIndexEntry(*(fields + (path.decode(),)))
        entries.append(entry)
        entry_len = ((62 + len(path) + 8) // 8) * 8
        i += entry_len
    assert len(entries) == num_entries
    return entries

    pass
    """Read git index file and return list of IndexEntry objects."""
    '''try:
        data = read_file(os.path.join('.git', 'index'))
    except FileNotFoundError:
        return []
    digest = hashlib.sha1(data[:-20]).digest()
    assert digest == data[-20:], 'invalid index checksum'
    signature, version, num_entries = struct.unpack('!4sLL', data[:12])
    assert signature == b'DIRC', \
            'invalid index signature {}'.format(signature)
    assert version == 2, 'unknown index version {}'.format(version)
    entry_data = data[12:-20]
    entries = []
    i = 0
    while i + 62 < len(entry_data):
        fields_end = i + 62
        fields = struct.unpack('!LLLLLLLLLL20sH',
                               entry_data[i:fields_end])
        path_end = entry_data.index(b'\x00', fields_end)
        path = entry_data[fields_end:path_end]
        entry = IndexEntry(*(fields + (path.decode(),)))
        entries.append(entry)
        entry_len = ((62 + len(path) + 8) // 8) * 8
        i += entry_len
    assert len(entries) == num_entries
    return entries'''
