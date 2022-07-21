import argparse  # Parse command line arguments
import collections  # Provide auxiliary data structures
import configparser  # Read/Write configuration files in Microsoft INI format
import hashlib  # SHA-1 function used extensively by Git
import os  # Provide filesystem abstraction routines
import re  # Regular expressions
import sys  # Provide access to command-line arguments 
import zlib  # Git compresses everything using zlib
import libgitv
# Import cmd handler functions from gitv library files
from libgitv.GitRepository import GitRepository, cmd_init
from libgitv.GitObject import cmd_cat_file, cmd_hash_object, cmd_log, cmd_rev_parse
from libgitv.GitTree import cmd_ls_tree, cmd_checkout
from libgitv.GitRefs import cmd_show_ref, cmd_tag
from libgitv.GitIndex import cmd_ls_files 

argparser = argparse.ArgumentParser(description="Content tracker")
argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True


# Version command prints the version 
argsp = argsubparsers.add_parser("version", help="Prints the version")


# Init command initializes a new empty repository
argsp = argsubparsers.add_parser("init", help="Initialize a new, empty repository.")
argsp.add_argument("path",
   metavar="directory",
   nargs="?",
   default=".",
   help="Where to create the repository.")


# cat-file prints the content of an object
argsp = argsubparsers.add_parser("cat-file", help = "Provide content of repository objects")
argsp.add_argument("type",
   metavar="type",
   choices=["blob", "commit", "tag", "tree"],
   help="Specify the type.")
argsp.add_argument("object",
   metavar = "object",
   help = "The object to display.")


# hash-object computes the object-id hash of an object
argsp = argsubparsers.add_parser("hash-object",
    help="Compute object ID and optionally creates a blob from a file")

argsp.add_argument("-t",
   metavar="type",
   dest="type",
   choices=["blob", "commit", "tag", "tree"],
   default="blob",
   help="Specify the type")

argsp.add_argument("-w",
   dest="write",
   action="store_true",
   help="Actually write the object into the database")

argsp.add_argument("path",
   help="Read object from <file>")


# log prints commit history of a given commit (defaulting to HEAD)
argsp = argsubparsers.add_parser("log", help = "Display history of the given commit.")
argsp.add_argument("commit", default= "HEAD", nargs="?", help = "Commit to start at.")


# ls-tree pretty prints a tree object
argsp = argsubparsers.add_parser("ls-tree", help="Pretty-print a tree object.")
argsp.add_argument("object", help="The object to show.")


# checkout a commit / branch / tag
argsp = argsubparsers.add_parser("checkout", help="Checkout a commit inside of a directory.")
argsp.add_argument("commit",  help="The commit or tree to checkout.")
argsp.add_argument("path", help="The EMPTY directory to checkout on.")


# show-ref lists references
argsp = argsubparsers.add_parser("show-ref", help="List references.")


# tag creates a new tag or lists existing tags
argsp = argsubparsers.add_parser("tag", help="List and create tags")
argsp.add_argument("-a", action="store_true", dest="create_tag_object", help="Whether to create a tag object")
argsp.add_argument("name", nargs="?", help="The new tag's name")
argsp.add_argument("object", default="HEAD", nargs="?", help="The object the new tag will point to")
argsp.add_argument("-m", action="store_true", dest="create_tag_object", help="Follows the message.")
argsp.add_argument("msg", default= "", nargs="?", help= "The message for this annotated tag.")
# TODO: Add optional argument for message. Variable will be called msg


argsp = argsubparsers.add_parser("rev-parse", help="Parse revision (or other objects) identifiers")
argsp.add_argument("--gitv-type",
    metavar="type",
    dest="type",
    choices=["blob", "commit", "tag", "tree"],
    default=None,
    help="Specify the expected type")
argsp.add_argument("name", help="The name to parse")


argsp = argsubparsers.add_parser("ls-files", help="Show information about files in the index and the working tree")



# Placeholder functions
def cmd_add(args):
    pass
def cmd_commit(args):
    pass
def cmd_merge(args):
    pass
def cmd_rebase(args):
    pass
def cmd_rm(args):
    pass

def cmd_version(args):
    print("0.0.1")


commandDict = {
    "add": cmd_add,
    "cat-file": cmd_cat_file,
    "checkout": cmd_checkout,
    "commit": cmd_commit,
    "hash-object": cmd_hash_object,
    "init": cmd_init,
    "log": cmd_log,
    "ls-tree": cmd_ls_tree,
    "ls-files": cmd_ls_files,
    "merge": cmd_merge,
    "rebase": cmd_rebase,
    "rev-parse": cmd_rev_parse,
    "rm": cmd_rm,
    "show-ref": cmd_show_ref,
    "tag": cmd_tag,
    
    "version": cmd_version
}


def main(argv=sys.argv[1:]):
    args = argparser.parse_args(argv)
    
    if 'command' in args and args.command in commandDict:
        func = commandDict[args.command]
        func(args)
    else:
        print('Unknown command. Please use ./gitv -h for more info on how to use gitv')