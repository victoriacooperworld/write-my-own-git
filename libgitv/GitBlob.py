from libgitv.GitObject import GitObject

#Blob is the class which stores users' content
class GitBlob(GitObject):
    format = b'blob'
    
    def __init__(self) -> None:
        self.blobdata = None
        
    def serialize(self):
        return self.blobdata
    
    def deserialize(self, data):
        self.blobdata = data