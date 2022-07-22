import collections
import os
from libgitv.GitObject import GitObject

from libgitv.GitRepository import GitRepository
from libgitv.GitCommit import GitCommit


def ref_resolve(repo, ref):
    data = None
    try:
        with open(repo.file(ref), 'r') as fp:
            data = fp.read()[:-1]
        if data.startswith("ref: "):
            return ref_resolve(repo, data[5:])
        else:
            return data
    except:
        return data


def ref_list(repo, path=None):
    if not path:
        path = repo.dir("refs")
    ret = collections.OrderedDict()

    for f in sorted(os.listdir(path)):
        can = os.path.join(path, f)
        if os.path.isdir(can):
            ret[f] = ref_list(repo, can)
        else:
            ret[f] = ref_resolve(repo, can)
    
    return ret


def cmd_show_ref(args):
    repo = GitRepository.repo_find()
    refs = ref_list(repo)
    show_ref(repo, refs, prefix="refs")


def show_ref(repo, refs, with_hash=True, prefix=""):
    for k, v in refs.items():
        if type(v) == str:
            print("{0}{1}{2}".format(
                v + " " if with_hash else "",
                prefix + "/" if prefix else "",
                k))
        else:
            show_ref(repo, v, with_hash=with_hash, prefix="{0}{1}{2}".format(prefix, "/" if prefix else "", k))


class GitRefs():
    # TODO
    # Either just SHA, followed by \n
    # Or refs: <refs path>, followed by \n
    def create_sha_reference(sha):
        # TODO
        pass

    def create_ref_reference(path):
        # TODO
        pass
        


class GitTag(GitCommit):
    format = b'tag'

    def create(repo, object_id, name, msg=''):
        object = GitObject.object_read(repo, object_id)

        tagObject = GitTag(repo)
        tagObject.kvlm = collections.OrderedDict()
        tagObject.kvlm[b'object'] = object_id.encode('ascii') if isinstance(object_id, str) else object_id
        tagObject.kvlm[b'type'] = b'commit'
        tagObject.kvlm[b'tag'] = name.encode('ascii') if isinstance(name, str) else name

        # TODO: Read data from global config
        tagObject.kvlm[b'tagger'] = b'Victoria Niu <57949035+victoriacooperworld@users.noreply.github.com> 1656980047 -0700'

        tagObject.kvlm[b''] = msg.encode('ascii') if isinstance(msg, str) else msg
        tagObject.kvlm[b''] += b'\n'

        tagObject.format = GitTag.format
        return tagObject


def cmd_tag(args):
    repo = GitRepository.repo_find()
    object_id = GitObject.object_find(repo, args.object)

    if args.name:
        # TODO: Need to pass in args.msg optionally into tag_create
        tag_create(repo, args.name, object_id, type="annotated" if args.create_tag_object else "lightweight", msg = args.msg)
    else:
        refs = ref_list(repo)
        show_ref(repo, refs["tags"], with_hash=False)


def tag_create(repo, name, object_id, type, msg=''):
    if type=="lightweight":
        # Create lightweight -- plain ref to a commit
        # Create a file of given name at .git/refs/tags
        path = repo.file('refs', 'tags', name)
        with open(path, 'w') as f:
            # Write commit id into file
            f.write(object_id)
        
    elif type=="annotated": #git tag -a v1.0.0 -m "Releasing version v1.0.0"
        # Create new commit object with message (annotation)
        # TODO: Pass in args.msg into GitTag.create
        annotatedTag = GitTag.create(repo, object_id, name, msg)
        annotation_id = annotatedTag.object_write()
        
        # Create a file of given name at .git/refs/tags
        path = repo.file('refs', 'tags', name)
        with open(path, 'w') as f:
            # Write commit id into file
            f.write(annotation_id)
    else:
        raise('Unknown tag type')