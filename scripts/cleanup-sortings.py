#!/usr/bin/python

import json
from typing import List, Dict, Any
import kachery_p2p as kp

SORTINGS = '/home/jsoules/src/spikeforest_recordings/sortings.json'
STUDIES = '/home/jsoules/src/spikeforest_recordings/current-studysets.json'
DRY_RUN = True


def slurp(filename: str) -> str:
    as_one_string = ''
    with open(filename) as f:
        while True:
            line = f.readline().rstrip()
            if not line: break
            as_one_string += line
    return as_one_string

def load_sortings() -> List[Dict[str, Any]]:
    hydrated_sortings = json.loads(slurp(SORTINGS))
    return hydrated_sortings

def load_all_studies() -> List[Dict[str, Any]]:
    hydrated_studysets = json.loads(slurp(STUDIES))
    flattened_study_list = [study for studyset in hydrated_studysets['StudySets'] for study in studyset['studies']]
    return flattened_study_list

def main():
    sortings = load_sortings()
    all_studies = load_all_studies()

    for sorting in sortings:
#        print(f"Seeking study name {sorting['studyName']} and recording name {sorting['recordingName']}")
        relevant_studyset = [s for s in all_studies if s['name'] == sorting['studyName']][0]
        relevant_recording =  [r for r in relevant_studyset['recordings'] if r['name'] == sorting['recordingName']][0]
#        print(f"Found relevant studyset and recording: {json.dumps(relevant_studyset, indent=4)}\n{json.dumps(relevant_recording, indent=4)}")
        sorting.pop('recordingDirectory', None)
        sorting.pop('firingsTrue', None)
        sorting['recordingUri'] = relevant_recording['recordingUri']
        sorting['sortingTrueUri'] = relevant_recording['sortingTrueUri']


    if DRY_RUN:
        original_sortings = load_sortings()
        print(f"Checking time:\n\n")
        for s in sortings[0:2]:
            original = original_sortings.pop(0)
            print(f"\tOriginal version:\n")
            print(json.dumps(original, indent=4))
            print(f"\tbecame:\n")
            print(json.dumps(s, indent=4))
            print("\n\n")
    else:
        print(kp.store_text(json.dumps(sortings)))

if __name__ == "__main__":
    main()
