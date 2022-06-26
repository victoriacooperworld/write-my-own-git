import argparse  # Parse command line arguments
import collections  # Provide auxiliary data structures
import configparser  # Read/Write configuration files in Microsoft INI format
import hashlib  # SHA-1 function used extensively by Git
import os  # Provide filesystem abstraction routines
import re  # Regular expressions
import sys  # Provide access to command-line arguments 
import zlib  # Git compresses everything using zlib


argparser = argparse.ArgumentParser(description="Content tracker")
argsubparsers = argparser.add_subparsers(title="Commands", dest="command")
argsubparsers.required = True

argsp = argsubparsers.add_parser("version", help="Prints the version")

# Placeholder functions
def cmd_add(args):
    pass
def cmd_cat_file(args):
    pass
def cmd_checkout(args):
    pass
def cmd_commit(args):
    pass
def cmd_hash_object(args):
    pass
def cmd_init(args):
    pass
def cmd_log(args):
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