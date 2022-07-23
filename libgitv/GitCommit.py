import collections  # Provide auxiliary data structures

from libgitv.GitObject import GitObject
import libgitv.util.StringHelpers as StringHelper


def kvlm_parse(raw):
    start = 0
    dict = collections.OrderedDict()
    
    while True:
        # Search for the next space and the next newline
        iSpace = raw.find(b' ', start)
        iNewline = raw.find(b'\n', start)
    
        # Space before newline indicates keyword
        
        # If newline appears first or no space at all, assume a blank line.
        # This indicates that the remainder of the data is the message
        if iSpace < 0 or iNewline < iSpace:
            assert(iNewline == start)
            dict[b''] = raw[start+1:]
            return dict
        
        # Otherwise, read as KV Pair
        key = raw[start:iSpace]
        
        # Find end of value (continuation lines begin w/ space)
        end = start
        while True:
            end = raw.find(b'\n', end+1)
            if raw[end+1] != ord(' '): break
            
        # Grab value and drop leading space
        value = raw[iSpace+1: end].replace(b'\n ', b'\n')
        
        if key in dict:
            if type(dict[key]) == list:
                dict[key].append(value)
            else:
                dict[key] = [dict[key], value]
        else:
            dict[key] = value
            
        start = end+1
    

def kvlm_serialize(kvlm):
    ret = b''
    
    # Output fields
    for key in kvlm.keys():
        if key == b'': continue
        val = kvlm[key]
        if type(val) != list:
            val = [val]
        
        for v in val:
            ret += key + b' ' + (v.replace(b'\n', b'\n ')) + b'\n'
    
    # Append message
    ret += b'\n' + kvlm[b'']
    
    return ret
    
    
class GitCommit(GitObject):
    format = b'commit'

    def create(repo, args):
        obj = GitCommit(repo)
        obj.kvlm = collections.OrderedDict()
        obj.kvlm[b'tree'] = StringHelper.toBytes(args['tree'])
        obj.kvlm[b'parent'] = StringHelper.toBytes(args['parent'])

        # TODO: Read data from global config
        obj.kvlm[b'author'] = b'Victoria Niu <57949035+victoriacooperworld@users.noreply.github.com> 1656980047 -0700'
        obj.kvlm[b'committer'] = b'Victoria Niu <57949035+victoriacooperworld@users.noreply.github.com> 1656980047 -0700'

        obj.kvlm[b''] = StringHelper.toBytes(args['msg'])
        obj.kvlm[b''] += b'\n'

        return obj

    def deserialize(self, data):
        self.kvlm = kvlm_parse(data)
        
    def serialize(self):
        return kvlm_serialize(self.kvlm)
        

