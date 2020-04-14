#!/usr/bin/env python

import os
import kachery as ka
import json

studyset_name = 'LONG_STATIC'

def main():
    thisdir = os.path.dirname(os.path.realpath(__file__))
    studysets_obj_path = ka.load_text(thisdir + '/../../recordings/studysets')
    with ka.config(fr='default_readonly'):
        studysets_obj = ka.load_object(path=studysets_obj_path)
    # studysets_obj['StudySets']
    new_study_sets = []
    for ss in studysets_obj['StudySets']:
        if ss['name'] != studyset_name:
            new_study_sets.append(ss)
    studyset_obj_path = thisdir + f'/../../recordings/{studyset_name}/{studyset_name}.json'
    studyset_obj = ka.load_object(studyset_obj_path)
    assert studyset_obj is not None, f'Missing file: {studyset_obj_path}'
    new_study_sets.append(studyset_obj)
    studysets_obj['StudySets'] = new_study_sets
    with ka.config(fr='default_readwrite'):
        studysets_obj_path = ka.store_object(studysets_obj, basename='studysets.json')
    with open(thisdir + '/../../recordings/studysets', 'w') as f:
        f.write(studysets_obj_path)
    with open(os.path.join(thisdir, '../studysets.json'), 'w') as f:
        json.dump(studysets_obj, f, indent=4)

if __name__ == '__main__':
    main()
