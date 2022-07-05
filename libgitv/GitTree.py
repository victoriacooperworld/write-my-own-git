import os  # Provide filesystem abstraction routines

from libgitv.GitRepository import GitRepository
from libgitv.GitObject import GitObject


# Tree Leaf - A singular record
class GitTreeLeaf(object):
    def __init__(self, mode, path, sha):
        self.mode = mode
        self.path = path
        self.sha = sha


# Tree - Describes content of work tree, associating blobs to paths.
class GitTree(GitObject):
    format=b'tree'

    def deserialize(self, data):
        self.items = GitTree.parse(data)


    def serialize(self):
        ret = b''
        for item in obj.items:
            ret += item.mode + b' ' + item.path + b'\x00'
            sha = int(item.sha, 16)
            ret += sha.to_bytes(20, byteorder="big")
        return ret
        
    
    def parse_one(raw, start=0):
        # Find the space terminator of the mode
        x = raw.find(b' ', start)
        assert(x-start in (5,6))
        
        # Read mode
        mode = raw[start:x]
        
        # Find NULL terminator of path, then read path
        y = raw.find(b'\x00', x)
        path = raw[x+1:y]
        
        # Read SHA and convert to hex string
        sha = hex(int.from_bytes(raw[y+1:y+21], "big"))[2:]  # Remove '0x' added by hex()
        
        return y+21, GitTreeLeaf(mode, path, sha)
    
    
    def parse(raw):
        pos = 0
        max = len(raw)
        ret = list()
        while pos < max:
            pos, data = GitTree.parse_one(raw, pos)
            ret.append(data)
        return ret
    
    
    def checkout(repo, tree, path):
        for item in tree.items:
            obj = GitObject.object_read(repo, item.sha)
            dest = os.path.join(path, item.path)

            if obj.format == b'tree':
                os.mkdir(dest)
                GitTree.checkout(repo, obj, dest)  # Recurse into subtrees
            elif obj.format == b'blob':
                with open(dest, 'wb') as f:
                    f.write(obj.blobdata)  # Write blob objects of tree
        

def cmd_ls_tree(args):
    repo = GitRepository.repo_find()
    obj = GitObject.object_read(repo, GitObject.object_find(repo, args.object, format=b'tree'))

    for item in obj.items:
        print("{0} {1} {2}\t{3}".format(
            "0" * (6 - len(item.mode)) + item.mode.decode("ascii"),
            # Git's ls-tree displays the type
            # of the object pointed to.  We can do that too :)
            GitObject.object_read(repo, item.sha).format.decode("ascii"),
            item.sha,
            item.path.decode("ascii")))


def cmd_checkout(args):
    repo = GitRepository.repo_find()
    obj = GitObject.object_read(repo, GitObject.object_find(repo, args.commit))

    # If the object is a commit, we grab its tree
    if obj.format == b'commit':
        obj = GitObject.object_read(repo, obj.kvlm[b'tree'].decode("ascii"))

    # Verify that path is an empty directory
    if os.path.exists(args.path):
        if not os.path.isdir(args.path):
            raise Exception("Not a directory {0}!".format(args.path))
        if os.listdir(args.path):
            raise Exception("Not empty {0}!".format(args.path))
    else:
        os.makedirs(args.path)

    GitTree.checkout(repo, obj, os.path.realpath(args.path).encode())