#This file is the GitObject class.
#To initialize a GitObject, it needs the repo info and also other data
#Two important functions - serializ() and deserialize()
from multiprocessing.sharedctypes import SynchronizedString
from zipapp import get_interpreter
import zlib
import GitRepository
import sys
class GitObject:
    repo = None

    def __init__(self, repo, data = None) -> None:
        self.repo = repo
        self.data = data

    def serialize(self):
        """
        This function will be implemented by subclasses.
        """
        raise Exception("Unimplemented!")

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

        path = repo.file("object", sha[:2],sha[2:])
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
            if fmt==b'commit':
                c=GitCommit
            elif fmt == b'tree':
                c=GitTree
            elif fmt == b'tag':
                c=GitTag
            elif fmt == b'blob':
                c=GitBlob
            else:
                raise Exception("Unknow type {0} for object {1}".format(fmt.decode("ascii"),sha))
            
            return c(repo,raw[sizeIdx+1:]) #return the content

        def object_find(repo, name, fmt=None, follow=True):
            return name


#cat-file command
#git cat-file TYPE OBJECT 
#cat-file is to print out the user content using a certain format

def cmd_cat_file(args):
    repo = repo.find()
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

    if format == b'commit':
        obj = GitCommit(repo, data)
    elif format == b'tree':
        obj = GitTree(repo, data)
    elif format == b'tag':
        obj = GitTag(repo, data)
    elif format == b'blob':
        obj = GitBlob(repo, data)
    else:
        raise Exception("Unknown type %s!" % format)

    return GitObject.object_write(obj,repo)

    
    
