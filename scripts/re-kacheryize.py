import json
from os import getcwd, listdir, chdir
from os.path import isdir, isfile, join
import random
from typing import Any

import kachery_p2p as kp

VERBOSE = True
DRY_RUN = True

recording_key = {'key_field': 'raw', 'basename': 'raw.mda'}
sorting_key = {'key_field': 'firings', 'basename': 'firings_true.mda'}


def slurp(filename: str) -> str:
    as_string = ''
    with open(filename) as f:
        while True:
            line = f.readline().rstrip()
            if not line: break
            as_string += line
    return as_string


def reup_file(object: Any):
    thekey = recording_key if recording_key['key_field'] in object else sorting_key
    if VERBOSE: print(f"Executing: object['{thekey['key_field']}'] = kp.store_file(kp.load_file(object['{thekey['key_field']}']), basename={thekey['basename']})")
    if DRY_RUN: return

    object[thekey['key_field']] = kp.store_file(kp.load_file(object[thekey['key_field']]), basename=f"{thekey['basename']}")


def self_tag(myobject: Any, filename: str):
    myobject.pop('self_reference', None) # delete the self_reference key if it exists

    if VERBOSE:
        print(f'Persist object {myobject} to {filename}')
        randomvalue = random.randrange(100000, 999999)
        print(f'Load {filename} to kachery, stipulate result to be {randomvalue}')
        myobject['self_reference'] = randomvalue
        print(f'Now re-overwrite {myobject} to {filename}')
    if DRY_RUN: return

    new_ref = kp.store_object(myobject)
    myobject['self_reference'] = new_ref
    with open(filename, 'w') as f:
        f.write(json.dumps(myobject, indent=4))
    # kp.store_object(myobject)


def main():
    cwd = getcwd()
    dirs = [join(cwd, d) for d in listdir(cwd) if isdir(join(cwd, d))]
    files = [f for f in listdir(cwd) if isfile(join(cwd, f))]

    for f in files:
        if f[-5:] != '.json': continue
        hydrated_object = json.loads(slurp(f))
        if not ('raw' in hydrated_object or 'firings' in hydrated_object):
            print(f'File {f} is neither sorting nor recording.')
            continue
        if ('raw' in hydrated_object and 'firings' in hydrated_object):
            print(f'*** File {f} has both "raw" and "firings" keys--investigate this!')
            continue

        print(f'Handling file: {f}')
        reup_file(hydrated_object)
        self_tag(hydrated_object, f)

    for d in dirs:
        # traverse any subdirectories (depth-first search). (We don't anticipate cycles or stack explosion in the intended use case.)
        print(f'Changing directory to {d}')
        chdir(d)
        main()


if __name__ == "__main__":
    main()
