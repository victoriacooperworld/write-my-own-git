import collections  # Provide auxiliary data structures

from libgitv.GitObject import GitObject


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
    
    def deserialize(self, data):
        self.kvlm = kvlm_parse(data)
        
    def serialize(self):
        return kvlm_serialize(self.kvlm)
        

