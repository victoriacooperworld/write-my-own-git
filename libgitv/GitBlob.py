from libgitv.GitObject import GitObject

#Blob is the class which stores users' content
class GitBlob(GitObject):
    format = b'blob'

    def create(repo, data):
        objBlob = GitBlob(repo, '')
        objBlob.blobdata = data
        
    def serialize(self):
        return self.blobdata
    
    def deserialize(self, data):
        self.blobdata = data