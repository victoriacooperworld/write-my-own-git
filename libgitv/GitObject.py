#This file is the GitObject class.
#To initialize a GitObject, it needs the repo info and also other data
#Two important functions - serializ() and deserialize()
from multiprocessing.sharedctypes import SynchronizedString
from zipapp import get_interpreter
import zlib


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