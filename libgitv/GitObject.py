#This file is the GitObject class.
#To initialize a GitObject, it needs the repo info and also other data
#Two important functions - serializ() and deserialize()
from multiprocessing.sharedctypes import SynchronizedString
from unittest import result
from zipapp import get_interpreter
import zlib
from libgitv.GitRepository import GitRepository
import sys
import hashlib  # SHA-1 function used extensively by Git

# Forward declaration of constructor dictionaries for superclass to use
# to filled after the superclass declaration
GIT_OBJECT_CONSTRUCTORS = {}

class GitObject:
    repo = None

    def __init__(self, repo, data = None) -> None:
        self.repo = repo
        if data != None:
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
            with open(path) as f:
                f.write(zlib.compress(result))
        return sha

    def object_find(repo, name, format=None, follow=True):
        return name

# Import subclasses
from libgitv.GitBlob import GitBlob
from libgitv.GitTree import GitTree
from libgitv.GitCommit import GitCommit

# Load subclass constructors into dictionary
GIT_OBJECT_CONSTRUCTORS[b'commit'] = GitCommit
GIT_OBJECT_CONSTRUCTORS[b'tree'] = GitTree
# GIT_OBJECT_CONSTRUCTORS[b'tag'] = GitTag  # Uncomment when class implemented
GIT_OBJECT_CONSTRUCTORS[b'blob'] = GitBlob


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
        repo = GitRepository(".") #??
    else: repo = None
    
    with open(args.path, "rb") as fd:
        #printing its hash
        sha = object_hash(fd,args.type.encode(),repo)
        print(sha)

def object_hash(fd, format, repo=None):
    #type commit, tree, tag, blob
    #default: blob
    data = fd.read()

    if format in GIT_OBJECT_CONSTRUCTORS:
        obj = GIT_OBJECT_CONSTRUCTORS[format](repo, data)
    else:
        raise Exception("Unknown type %s!" % format)

    return GitObject.object_write(obj,repo)


def cmd_log(args):
    repo = GitRepository.repo_find()
    print("LOG{")
    log_graph(repo, GitObject.object_find(repo, args.commit), set())
    print("}")

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
        print("c_{0} -> c_{1};".format(sha,p))
        log_graph(repo,p,seen) #recursion