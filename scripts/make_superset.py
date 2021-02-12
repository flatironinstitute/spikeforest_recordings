#!/usr/bin/python

import json
from os import getcwd, listdir, chdir, system
from os.path import exists, isdir, isfile, join, split

import kachery_p2p as kp

VERBOSE = True
VERY_VERBOSE = False
DRY_RUN = True

required_keys = [ 'name', 'description', 'studies' ]
superset = { 'StudySets': [] }


def check_file_relevance(filename: str, directory_tail: str):
    # the study json files are always called [last part of directory path].json.
    # anything that doesn't match that pattern is not a file we care about.
    if filename[-5:] != '.json': return False
    if (filename[:-5] != directory_tail):
        if VERY_VERBOSE: print(f"\t *** Omitting file {filename} which does not match {directory_tail}.")
        return False
    lowercase_letters = [c for c in filename[:-5] if c.islower()]
    if len(lowercase_letters) > 0:
        return False
    return True


def slurp(filename: str) -> str:
    as_one_string = ''
    with open(filename) as f:
        while True:
            line = f.readline().rstrip()
            if not line: break
            as_one_string += line
    return as_one_string


def process_file(fname: str, cwd: str):
    hydrated_file = json.loads(slurp(fname))
    for key in required_keys:
        if not key in hydrated_file:
            print(f'File {fname} is missing required key {key}')
            return None
    if VERY_VERBOSE:
        print(f"Updated study file {fname} to the following:\n{hydrated_file}")
    return hydrated_file


def main():
    cwd = getcwd()
    dirs = [join(cwd, d) for d in listdir(cwd) if isdir(join(cwd, d))]
    files = [f for f in listdir(cwd) if isfile(join(cwd, f))]
    directory_tail = split(cwd)[1]

    for f in files:
        if not check_file_relevance(f, directory_tail): continue
        print(f'Handling file: {f}')
        result = process_file(f, cwd)
        if result != None:
            superset['StudySets'].append(result)

    for d in dirs:
        # traverse any subdirectories (depth-first search). (We don't anticipate cycles or stack explosion in the intended use case.)
        print(f"\t\tcd to {d}")
        chdir(d)
        main()


if __name__ == "__main__":
    main()
    if VERY_VERBOSE:
        print(json.dumps(superset, indent=4))
    if len(superset['StudySets']) > 0 and not DRY_RUN:
        print(kp.store_object(superset, basename='studysets.json'))
