import collections
import os

from libgitv.GitRepository import GitRepository
from libgitv.GitCommit import GitCommit


def ref_resolve(repo, ref):
    with open(repo.file(ref), 'r') as fp:
        data = fp.read()[:-1]
    if data.startswith("ref: "):
        return ref_resolve(repo, data[5:])
    else:
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


def cmd_tag(args):
    repo = GitRepository.repo_find()

    if args.name:
        tag_create(args.name, args.object, type="object" if args.create_tag_object else "ref")
    else:
        refs = ref_list(repo)
        show_ref(repo, refs["tags"], with_hash=False)


def tag_create(name, object, type):
    if type=="ref":
        # TODO: Create ref
    elif type="object":
        # TODO: Create object tag
    else:
        raise('Unknown tag type')