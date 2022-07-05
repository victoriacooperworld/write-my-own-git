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
from libgitv.GitRepository import cmd_init
from libgitv.GitObject import cmd_cat_file, cmd_hash_object, cmd_log

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

argsp = argsubparsers.add_parser("cat-file", help = "Provide content of repository objects")
argsp.add_argument("type",
                   metavar="type",
                   choices=["blob", "commit", "tag", "tree"],
                   help="Specify the type.")
argsp.add_argument("object",
                   metavar = "object",
                   help = "The object to display.")

argsp = argsubparsers.add_parser(
    "hash-object",
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


argsp = argsubparsers.add_parser("log", help = "Display history of the given commit.")
argsp.add_argument("commit", default= "HEAD", nargs="?", help = "Commit to start at.")


# Placeholder functions
def cmd_add(args):
    pass
def cmd_checkout(args):
    pass
def cmd_commit(args):
    pass

def cmd_ls_tree(args):
    pass
def cmd_merge(args):
    pass
def cmd_rebase(args):
    pass
def cmd_rev_parse(args):
    pass
def cmd_rm(args):
    pass
def cmd_show_ref(args):
    pass
def cmd_tag(args):
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