#!/usr/bin/python

import json
from os import getcwd, listdir, chdir, system
from os.path import exists, isdir, isfile, join, split
import random
from typing import Any, List

import kachery_p2p as kp

VERBOSE = True
VERY_VERBOSE = False
DRY_RUN = True
FORCE = False
COMPLETED_DIRECTORIES = []

recording_keys = { 'old': 'directory', 'new': 'recordingUri' }
sorting_keys   = { 'old': 'firingsTrue', 'new': 'sortingTrueUri' }
required_keys = [ 'name', 'studySetName', 'recordings' ]


def check_file_relevance(filename: str, directory_tail: str):
    # the study json files are always called [last part of directory path].json.
    # anything that doesn't match that pattern is not a file we care about.
    if filename[-5:] != '.json': return False
    if (filename[:-5] != directory_tail):
        if VERY_VERBOSE: print(f"\t *** Omitting file {filename} which does not match {directory_tail}.")
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


def fetch_self_reference(fname: str):
    hydrated_file = json.loads(slurp(fname))
    if 'self_reference' not in hydrated_file:
        raise Exception(f'self_reference key not present in {fname}')
    return hydrated_file['self_reference']


def process_file(fname: str, cwd: str):
    hydrated_file = json.loads(slurp(fname))
    for key in required_keys:
        if not key in hydrated_file:
            print(f'File {fname} is missing required key {key}')
            return False
    for x in hydrated_file['recordings']:
        for key in [recording_keys['old']] + [sorting_keys['old']]:
            if not key in x:
                print(f'Record with name {x["name"]} is missing required key {key}')
                return False
        name = x['name']
        recording_name = join(cwd, f'{name}.json')
        sorting_name   = join(cwd, f'{name}.firings_true.json')
        for f in [recording_name, sorting_name]:
            if not exists(f):
                print(f"ERROR: expected file {f} does not exist. Aborting processing of {fname}.")
                return False
        if VERBOSE:
            print(f"\tUpdating {fname} recording record {name} from {recording_name} and {sorting_name}")
        x.pop(recording_keys['old'], None) # purge old keys
        x.pop(sorting_keys['old'], None)
        x[recording_keys['new']] = fetch_self_reference(recording_name)
        x[sorting_keys['new']] = fetch_self_reference(sorting_name)
    if VERY_VERBOSE:
        print(f"Updated study file {fname} to the following:\n{hydrated_file}")
    self_tag(hydrated_file, fname)
    return True


def self_tag(myobject: Any, filename: str):
    myobject.pop('self_reference', None) # delete the self_reference key if it exists
    if DRY_RUN:
        new_ref = str(random.randrange(100000, 9999990)) + ' (pretend)'
    else:
        if VERBOSE: print(f'kachery-storing object {filename}.')
        new_ref = kp.store_object(myobject, basename=filename)
    myobject['self_reference'] = new_ref

    if VERBOSE: print(f'Persisting object with self-reference {new_ref}...')
    if VERY_VERBOSE: print(f'Persist object {myobject} with self-reference {new_ref}')
    if not DRY_RUN:
        with open(filename, 'w') as f:
            f.write(json.dumps(myobject, indent=4))


def main():
    cwd = getcwd()
    dirs = [join(cwd, d) for d in listdir(cwd) if isdir(join(cwd, d))]
    files = [f for f in listdir(cwd) if isfile(join(cwd, f))]
    directory_tail = split(cwd)[1]

    for f in files:
        if not check_file_relevance(f, directory_tail): continue
        print(f'Handling file: {f}')
        process_file(f, cwd)

    for d in dirs:
        # traverse any subdirectories (depth-first search). (We don't anticipate cycles or stack explosion in the intended use case.)
        skip = False
        for x in COMPLETED_DIRECTORIES:
            if x in d:
                print(f"\t****** Skipping manually-omitted directory ${x}")
                skip = True
        if skip: continue
 
        print(f"\t\tcd to {d}")
        chdir(d)
        main()


if __name__ == "__main__":
    main()
