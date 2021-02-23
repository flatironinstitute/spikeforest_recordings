import json
from os import getcwd, listdir, chdir, system
from os.path import exists, isdir, isfile, join
import pathlib
import random
from shutil import copyfile
from typing import Any

import kachery_p2p as kp
import kachery as ka

VERBOSE = True
DRY_RUN = True
FORCE = False
COMPLETED_DIRECTORIES = ['LONG_DRIFT', 'MANUAL_FRANKLAB', 'SYNTH_MAGLAND']

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


def trim_dir_annotation(sha1dir: str):
    # Handle cases where sha1dir is annotated, e.g. sha1dir://abcdef.patched/...
    # if the '.patched' annotation is not removed, ka.get_file_hash throws an exception.
    sha1dir_components = sha1dir.split('/')
    sha1dir_components[2] = sha1dir_components[2].split('.')[0] # remove any dot & anything after
    return '/'.join(sha1dir_components) # return reformed string


def reup_file(object: Any):
    thekey = recording_key if recording_key['key_field'] in object else sorting_key
    if VERBOSE: print(f"Executing: object['{thekey['key_field']}'] = kp.store_file(kp.load_file(object['{thekey['key_field']}']), basename={thekey['basename']})")
    if DRY_RUN: return

    # Turns out that kachery doesn't handle big files without manifests all that well. Which was the point of this exercise.
    # So let's take advantage of being on the same filesystem to do a little magic.
    raw = object[thekey["key_field"]]
    print(f'Got raw: {raw}')
    if ('sha1dir' in raw):
        key_field = object[thekey['key_field']]
        sha1dir = key_field.split('/')[2]
        print(f'Got dir: {sha1dir}')
        kp.load_file(f'sha1://{sha1dir}')
        print(f"Fetching hash for file: {key_field}")
        reformed_field = trim_dir_annotation(f"{key_field}")
        if VERBOSE: print(f"(using reformed field {reformed_field})")
        try:
            sha1 = ka.get_file_hash(reformed_field)
        except:
            if FORCE:
                print(f"\t** Trimmed lookup didn't work, falling back to kp.load_file({key_field})")
                kp.load_file(key_field)
                sha1 = ka.get_file_hash(key_field)
            else:
                print(f"Error on ka.get_file_hash({reformed_field}) -- aborting")
                exit()
    else:
        #sha1 = '/'.join(raw.split('/')[2:])
        sha1 = raw.split('/')[2]
    print(f'Got sha1: {sha1}')
    src_path  = f'/mnt/ceph/users/magland/kachery-storage/sha1/{sha1[0]}{sha1[1]}/{sha1[2]}{sha1[3]}/{sha1[4]}{sha1[5]}/{sha1}'
    dest_path = f'/mnt/ceph/users/jsoules/kachery-storage/sha1/{sha1[0]}{sha1[1]}/{sha1[2]}{sha1[3]}/{sha1[4]}{sha1[5]}/{sha1}'
    if VERBOSE: print(f"Executing: shutil.copyfile({src_path}, {dest_path})")
    if not exists(dest_path):
        pathlib.Path('/'.join(dest_path.split('/')[:-1])).mkdir(parents=True, exist_ok=True)
        copyfile(src_path, dest_path)
        print("\tCompleted copy operation.")
    object[thekey['key_field']] = kp.store_file(kp.load_file(object[thekey['key_field']]), basename=f"{thekey['basename']}")


def self_tag(myobject: Any, filename: str):
    myobject.pop('self_reference', None) # delete the self_reference key if it exists
    if DRY_RUN:
        new_ref = str(random.randrange(100000, 9999990)) + ' (pretend)'
    else:
        if VERBOSE: print(f'kachery-storing object {filename}.')
        new_ref = kp.store_object(myobject, basename=filename)
    myobject['self_reference'] = new_ref

    if VERBOSE: print(f'Persist object {myobject} with self-reference {new_ref}')
    if not DRY_RUN:
        with open(filename, 'w') as f:
            f.write(json.dumps(myobject, indent=4))


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
            print(f"\t\t*** File {f} has both 'raw' and 'firings' keys--investigate this!")
            continue

        print(f'Handling file: {f}')
        reup_file(hydrated_object)
        self_tag(hydrated_object, f)

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
