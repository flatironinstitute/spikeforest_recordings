#!/usr/bin/python

import json
from spikeextractors import RecordingExtractor, SortingExtractor
from spikecomparison import GroundTruthComparison
import spiketoolkit as st
from typing import Any, Dict, List, Set, Tuple

import kachery_p2p as kp
import labbox_ephys as le

VERBOSE = True
VERY_VERBOSE = True
ABBREVIATED_TEST = True
SORTINGS = '/home/jsoules/src/spikeforest_recordings/sortings.json'

RECORDING_URI_KEY = 'recordingUri'
GROUND_TRUTH_URI_KEY = 'sortingTrueUri'


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


def compute_quality_metrics(recording: RecordingExtractor, sorting: SortingExtractor) -> str:
    metric_names = [
        "num_spikes", "firing_rate", "presence_ratio",
        "isi_violation", "amplitude_cutoff", "snr", "max_drift",
        "cumulative_drift", "silhouette_score", "isolation_distance",
        "l_ratio", "nn_hit_rate", "nn_miss_rate","d_prime"]

    return st.validation.compute_quality_metrics(
        sorting, recording,
        metric_names=metric_names, as_dataframe=True).to_dict()

def compare_with_ground_truth(sorting: SortingExtractor, gt_sorting: SortingExtractor):
    ground_truth_comparison = GroundTruthComparison(gt_sorting, sorting)

    return {"best_match_21": ground_truth_comparison.best_match_21.to_list(),
            "best_match_12": ground_truth_comparison.best_match_12.to_list(),
            "agreement_scores": ground_truth_comparison.agreement_scores.to_dict()}

def compute_quality_metrics_json(recording: RecordingExtractor, sorting: SortingExtractor) -> str:
    metric_names = [
        "num_spikes", "firing_rate", "presence_ratio",
        "isi_violation", "amplitude_cutoff", "snr", "max_drift",
        "cumulative_drift", "silhouette_score", "isolation_distance",
        "l_ratio", "nn_hit_rate", "nn_miss_rate","d_prime"]

    return st.validation.compute_quality_metrics(
        sorting, recording,
        metric_names=metric_names, as_dataframe=True).to_json()

def compare_with_ground_truth_jsonstring(sorting: SortingExtractor, gt_sorting: SortingExtractor):
    ground_truth_comparison = GroundTruthComparison(gt_sorting, sorting)

    return json.dumps({"best_match_21": ground_truth_comparison.best_match_21.to_list(),
            "best_match_12": ground_truth_comparison.best_match_12.to_list(),
            "agreement_scores": ground_truth_comparison.agreement_scores.to_json()})

def get_unique_recordings_from_sortresult_list(sorting_entries: List[Dict[str, Any]]) -> Dict[str, str]:
    if VERY_VERBOSE: print(json.dumps(sorting_entries[0]))
    recording_set = set([a[RECORDING_URI_KEY] for a in sorting_entries])

    recording_uris_mapped_to_true_firings = {}
    for recording in recording_set:
        if VERBOSE: print(f"Checking recording {recording}")
        # We expect every recording (identified here by the URI) to be uniquely associated with a ground truth set.
        potential_gts = set([a[GROUND_TRUTH_URI_KEY] for a in sorting_entries if a[RECORDING_URI_KEY] == recording])
        if len(potential_gts) != 1:
            raise Exception
        # get an arbitrary element of the set--but since we've established it has one item, we're pretty sure which one it'll be
        recording_uris_mapped_to_true_firings[recording] = potential_gts.pop()
        if VERBOSE: print(f"Found corresponding ground-truth {recording_uris_mapped_to_true_firings[recording]}")
    return recording_uris_mapped_to_true_firings

def filter_sortresults_per_recording(sorting_entries: List[Dict[str, Any]], recordingFile: str) -> List[Dict[str, Any]]:
    filtered = [s for s in sorting_entries if s[RECORDING_URI_KEY] == recordingFile]
    return filtered

def get_recording_and_ground_truth(recording_uri: str, ground_truth_uri: str) -> Tuple[RecordingExtractor, SortingExtractor]:
    if VERBOSE: print(f"Fetching extractors for recording {recording_uri} and gt-sorting {ground_truth_uri}")
    if VERY_VERBOSE: print(f"Executing: le.LabboxEphysRecordingExtractor({recording_uri})")
    recording_extractor: RecordingExtractor = le.LabboxEphysRecordingExtractor(recording_uri)
    sample_rate = recording_extractor.get_sampling_frequency()
    if VERY_VERBOSE: print(f"Found sample rate {sample_rate}")
    firings_uri = kp.load_object(ground_truth_uri)['firings']
    sorting_obj = {
        'sorting_format': 'mda',
        'data': {
            'firings': firings_uri,
            'samplerate': sample_rate
        }
    }
    if VERY_VERBOSE: print(f"Executing: le.LabboxEphysSortingExtractor({json.dumps(sorting_obj)})")
    sorting_extractor: SortingExtractor = le.LabboxEphysSortingExtractor(sorting_obj)
    return (recording_extractor, sorting_extractor)

def evaluate_sorting_recording_pair(firings_file: str, recording_extr: RecordingExtractor, ground_truth: SortingExtractor) -> Tuple[Any, Any]:
    if VERY_VERBOSE: print(f"Loading sorting extractor for {firings_file} as the firings key")
    sorting_obj = {
        'sorting_format': 'mda',
        'data': {
            'firings': firings_file,
            'samplerate': recording_extr.get_sampling_frequency()
        }
    }
    if VERY_VERBOSE: print(f"Executing (for comparison evaluation): le.LabboxEphysSortingExtractor({json.dumps(sorting_obj)})")
    sorter_extractor = le.LabboxEphysSortingExtractor(sorting_obj)
    if VERY_VERBOSE: print(f"Executing quality metrics")
    quality_metrics = compute_quality_metrics(recording_extr, sorter_extractor)
    if VERY_VERBOSE: print(f"Executing ground-truth comparison")
    gt_comparison = compare_with_ground_truth(sorter_extractor, ground_truth)
    return (quality_metrics, gt_comparison)

def main():
    sortings = load_sortings()
    kampff_sortings = [s for s in sortings if s['studyName'] == 'paired_kampff']
    comparisons = []
    # returns dict whose keys are the unique recording URIs and whose values are the corresponding ground-truth sorting's URI.
    unique_recordings = get_unique_recordings_from_sortresult_list(kampff_sortings)
    for recording_uri in unique_recordings.keys():
        recording_extractor, ground_truth_sorting_extractor = get_recording_and_ground_truth(recording_uri, unique_recordings[recording_uri])
        sortings_for_this_recording = filter_sortresults_per_recording(kampff_sortings, recording_uri)
        for sorting_dict in sortings_for_this_recording:
            try:
                sorting_file = sorting_dict['firings']
            except KeyError:
                print(f"No 'firings' key for sorting_dict {json.dumps(sorting_dict)}. Skipping...")
                continue
            quality_metric, gt_comp = evaluate_sorting_recording_pair(sorting_file, recording_extractor, ground_truth_sorting_extractor)
            comparison = {
                'studyName': sorting_dict['studyName'],
                'recordingName': sorting_dict['recordingName'],
                'sorterName': sorting_dict['sorterName'],
                'quality_metric': quality_metric,
                'ground_truth_comparison': gt_comp
            }
            comparisons.append(comparison)
        if ABBREVIATED_TEST: break
    print(f"Results:\n{json.dumps(comparisons, indent=4)}")
    # This was for a different output format which we probably won't use
    # print("\tQuality metrics:\n" + "\n".join([json.dumps(qm, indent=4) for qm in ]))
    # print("\n\n\n")
    # print("\tGround Truth comparisons:\n" + "\n".join(json.dumps(comp, indent=4) for comp in all_ground_truth_comparisons))
    

if __name__ == "__main__":
    main()
