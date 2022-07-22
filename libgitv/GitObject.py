#This file is the GitObject class.
#To initialize a GitObject, it needs the repo info and also other data
#Two important functions - serialize() and deserialize()
from datetime import datetime
import zlib
import os
import re
import sys
import hashlib  # SHA-1 function used extensively by Git

from libgitv.GitRepository import GitRepository

def ref_resolve():
    pass

# Forward declaration of constructor dictionaries for superclass to use
# to filled after the superclass declaration
GIT_OBJECT_CONSTRUCTORS = {}

class GitObject:
    repo = None

    def __init__(self, repo, data = None) -> None:
        self.repo = repo
        if data is not None:
            self.deserialize(data)

    def serialize(self):
        """
        This function will be implemented by subclasses.
        """
        # raise Exception("Unimplemented!")
        pass

    def deserialize(self):
        raise Exception("Unimplemented!")

    """
    The storage format: header + ASCII number + size of the object in bytes + null(0x00) + contents of the object
    """
    def object_read(repo,sha): #sha is the way the path is hashed
        """
        Read object from Git repo
        Return a GitObject
        """

        path = repo.file("objects", sha[:2],sha[2:])
        with open(path, 'rb') as f:
            #first get the raw data from depressing the file
            raw = zlib.decompress(f.read()) #type(raw) is String

            #read object type
            objectTypeIdx = raw.find(b' ')     #find the last occurance of type info
            fmt = raw[0:objectTypeIdx]

            #read and validate object size
            sizeIdx = raw.find(b'\x00', objectTypeIdx)
            size = int(raw[objectTypeIdx:sizeIdx].decode("ascii"))
            if size != len(raw)-sizeIdx-1:
                raise Exception("Malformed object {0}: bad length".format(sha))
            
            #pick constructor
            if fmt in GIT_OBJECT_CONSTRUCTORS:
                c=GIT_OBJECT_CONSTRUCTORS[fmt]
            else:
                raise Exception("Unknow type {0} for object {1}".format(fmt.decode("ascii"),sha))
            
            return c(repo,raw[sizeIdx+1:]) #return the content

        
    def object_write(obj, written = True):
        data = obj.serialize()  
        result = obj.format + b' ' + str(len(data)).encode()+b'\x00'+data
        sha = hashlib.sha1(result).hexdigest()
        if written:
            #compute the path
            path=obj.repo.file("objects", sha[0:2], sha[2:], mkdir=written)
            with open(path, 'wb') as f:
                f.write(zlib.compress(result))
        return sha

    def object_resolve(repo, name):
        candidates = list()
        hashRE = re.compile(r"^[0-9A-Fa-f]{4,40}$")

        if not name.strip():
            return None  # Abort for empty strings
        
        if name == 'HEAD':  # Head is non ambiguous
            return [ref_resolve(repo, 'HEAD')]
        
        if hashRE.match(name):
            if len(name) == 40:
                return [name.lower()]  # A complete hash
            prefix = name.lower()[0:2]
            path = repo.dir('objects', prefix, mkdir=False)
            if path:
                rem = name[2:]
                for f in os.listdir(path):
                    if f.startswith(rem):
                        candidates.append(prefix + f)
        
        # Resolve reference names
        if len(candidates) == 0:
            # Search for branches with name
            refObj = ref_resolve(repo, f'refs/heads/{name}')
            if refObj:
                return [refObj]
            # Search for tags with name
            refObj = ref_resolve(repo, f'refs/tags/{name}')
            if refObj:
                return [refObj]
        
        return candidates

    def object_find(repo, name, format=None, follow=True):
        sha = GitObject.object_resolve(repo, name)

        if not sha:
            raise Exception('No such reference {0}.'.format(name))
        if len(sha) > 1:
            raise Exception("Ambiguous reference {0}: Candidates are:\n - {1}.".format(name,  "\n - ".join(sha)))

        sha = sha[0]

        if not format:
            return sha

        while True:
            obj = GitObject.object_read(repo, sha)

            if obj.format == format:
                return sha

            if not follow:
                return None

            # Follow tags
            if obj.format == b'tag':
                sha = obj.kvlm[b'object'].decode("ascii")
            elif obj.format == b'commit' and format == b'tree':
                sha = obj.kvlm[b'tree'].decode("ascii")
            else:
                return None

# Import subclasses
from libgitv.GitBlob import GitBlob
from libgitv.GitTree import GitTree
from libgitv.GitCommit import GitCommit

# Load subclass constructors into dictionary
GIT_OBJECT_CONSTRUCTORS[b'commit'] = GitCommit
GIT_OBJECT_CONSTRUCTORS[b'tree'] = GitTree
# GIT_OBJECT_CONSTRUCTORS[b'tag'] = GitTag  # Uncomment when class implemented
GIT_OBJECT_CONSTRUCTORS[b'blob'] = GitBlob


from libgitv.GitRefs import ref_resolve

#cat-file command
#git cat-file TYPE OBJECT 
#cat-file is to print out the user content using a certain format

def cmd_cat_file(args):
    repo = GitRepository.repo_find()
    cat_file(repo, args.object, format = args.type.encode())

def cat_file(repo, obj, format = None):
    obj = GitObject.object_read(repo, GitObject.object_find(repo,obj,format=format))
    sys.stdout.buffer.write(obj.serialize())
        

#hash-object is basically the opposite of cat-file: 
#it reads a file, computes its hash as an object
#either storing it in the repository (if the -w flag is passed) or just printing its hash.
#git hash-object [-w] [-t Type] FILE 

def cmd_hash_object(args):
    if args.write:
        repo = GitRepository.repo_find()
    else: repo = None
    
    with open(args.path, "rb") as fd:
        #printing its hash
        sha = object_hash(fd,args.type.encode(),repo)
        print(sha)

def object_hash(fd, format=b'blob', repo=None, lf_ending=False):
    #type commit, tree, tag, blob
    #default: blob
    data = fd.read()
    if lf_ending:  # Scrub blobs to linux LF format for cross-platform consistency
        data = data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')

    if format in GIT_OBJECT_CONSTRUCTORS:
        obj = GIT_OBJECT_CONSTRUCTORS[format](repo, data)
    else:
        raise Exception("Unknown type %s!" % format)

    return obj.object_write(False)


def cmd_log(args):
    repo = GitRepository.repo_find()
    log_graph(repo, GitObject.object_find(repo, args.commit), set())

def log_graph(repo,sha,seen):
    if sha in seen:
        return 
    seen.add(sha)

    commit = GitObject.object_read(repo,sha)
    assert(commit.format==b'commit')
    if not b'parent' in commit.kvlm.keys():
        #no parent, the initial commit
        return
    
    parents = commit.kvlm[b'parent'] #key value list message
    if type(parents) != list:
        parents=[parents] #convert it to a list
    
    for p in parents:
        p = p.decode("ascii")
        # print("c_{0} -> c_{1};".format(sha,p))
        print('commit: {0}'.format(sha))
        arrAuthor = str(commit.kvlm[b'author'])[2:-1].split(' ')
        commitDate = datetime.fromtimestamp(int(arrAuthor[-2]))
        print('Author: {0} {1}\nDate: {2} {3}\n'.format(' '.join(arrAuthor[:-3]), arrAuthor[-3], commitDate.ctime(), arrAuthor[-1]))
        print('\t{0}'.format(str(commit.kvlm[b''])[2:-1].replace('\\n', '\n\t')))
        log_graph(repo,p,seen) #recursion


def cmd_rev_parse(args):
    format = None
    if args.type:
        format = args.type.encode()
    repo = GitRepository.repo_find()
    print(GitObject.object_find(repo, args.name, format, follow=True))