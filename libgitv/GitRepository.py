from configparser import ConfigParser  # Read/Write configuration files in Microsoft INI format
import os  # Provide filesystem abstraction routines


# Supported repositoryformatversions. Only 0 for now
SUPPORTED_REPO_FORMAT_VERS = (0,)
DEFAULT_CONFIG = {
    "core": [
        ("repositoryformatversion", "0"),
        ("filemode", "false"),
        ("bare", "false")
    ]
}


class GitRepository(object):
    worktree = None
    gitdir = None
    conf = None 
    
    def __init__(repo, path, force=False):
        repo.worktree = path
        repo.gitdir = os.path.join(path, ".git")
        
        if not (force or os.path.isdir(repo.gitdir)):
            raise Exception("Not a Git repository %s" % path)
            
        # Read configuration file in .git/config
        repo.conf = ConfigParser()
        cf = repo.file("config")
        
        if cf and os.path.exists(cf):
            repo.conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")
        
        if not force:
            vers = int(repo.conf.get("core", "repositoryformatversion"))
            if vers not in SUPPORTED_REPO_FORMAT_VERS:
                raise Exception("Unsupported repositoryformatversion %s" % vers)
    
    
    def path(repo, *path):
        return os.path.join(repo.gitdir, *path)
    
    
    def file(repo, *path, mkdir=False):
        if repo.dir(*path[:-1], mkdir=mkdir):
            return repo.path(*path)
    
    
    def dir(repo, *path, mkdir=False):
        path = repo.path(*path)
        
        if os.path.exists(path):
            if os.path.isdir(path):
                return path
            else:
                raise Exception("Not a directory: %s" % path)
        
        if mkdir:
            os.makedirs(path)
            return path
        else:
            return None
    
    
    def create(path):
        repo = GitRepository(path, True)
        
        # Make sure path exists and is empty
        if os.path.exists(repo.worktree):
            if not os.path.isdir(repo.worktree):
                raise Exception("%s is not a directory" % path)
            if os.listdir(repo.worktree):
                raise Exception("%s is not empty!" % path)
        else:
            os.makedirs(repo.worktree)
            
        assert(repo.dir("branches", mkdir=True))
        assert(repo.dir("objects", mkdir=True))
        assert(repo.dir("refs", "tags", mkdir=True))
        assert(repo.dir("refs", "heads", mkdir=True))
        
        # .git/description
        with open(repo.file("description"), "w") as f:
            f.write("Unnamed repository; edit this file 'description' to name the repository.\n")
        
        # .git/HEAD
        with open(repo.file("HEAD"), "w") as f:
            f.write("ref: refs/heads/master\n")
            
        # .git/config
        with open(repo.file("config"), "w") as f:
            config = GitRepository.default_config()
            config.write(f)
            
        return repo
    
    
    def default_config():
        ret = ConfigParser()
        
        # Fill in config virtual file with default config
        for tmpSection in DEFAULT_CONFIG:
            tmpData = DEFAULT_CONFIG[tmpSection]
            ret.add_section(tmpSection)
            for tmpEntry in tmpData:
                ret.set(tmpSection, tmpEntry[0], tmpEntry[1])
        
        # Return default config
        return ret
    
    
    def find(path=".", required=True):
        # Iteratively search for root of git directory
        # Look for .git folder under directories, starting from
        # current directory up to the root folder
        
        # Convert input path into a real path
        path = os.path.realpath(path)
        while True:
            # If .git folder directly under current directory, return as repository
            if os.path.isdir(os.path.join(path, ".git")):
                return GitRepository(path)
            
            # Obtain parent directory
            parent = os.path.realpath(os.path.join(path, ".."))
            
            if parent == path:  # If reached root directory
                if required:  # Raise exception if repo required
                    raise Exception("No git directory.")
                else:
                    return None
                    
            path = parent  # Go up to parent
    

def cmd_init(args):
    repo = GitRepository.create(args.path)
    print("Initialized empty Git repository in %s" % os.path.realpath(repo.gitdir))