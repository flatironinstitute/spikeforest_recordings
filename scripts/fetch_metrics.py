#!/usr/bin/python

import argparse
import json
from spikeextractors import RecordingExtractor, SortingExtractor
from spikecomparison import GroundTruthComparison
import spiketoolkit as st
from typing import Any, cast, Dict, List, Set, Tuple, TypedDict, Union

import hither2 as hi
import kachery_p2p as kp
import labbox_ephys as le

class ArgsDict(TypedDict):
    verbose: int
    test: int
    sortingsfile: str
    recordingset: str

args: Union[ArgsDict, None] = None

RECORDING_URI_KEY = 'recordingUri'
GROUND_TRUTH_URI_KEY = 'sortingTrueUri'
SORTING_FIRINGS_URI_KEY = 'firings'
QUALITY_METRICS = [
    "num_spikes",
    "firing_rate",
    "presence_ratio",
    "isi_violation",
    "amplitude_cutoff",
    "snr",
    "max_drift",
    "cumulative_drift",
    "silhouette_score",
    "isolation_distance",
    "l_ratio",
    "nn_hit_rate",
    "nn_miss_rate",
    "d_prime"
]

def init_args():
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('--test', '-t', action='count', default=0,
        help="If non-zero, this will set a maximum number of iterations before quitting, " +
        "to give a usable sample without processing the entire data set.")
    parser.add_argument('--sortingsfile', '-s', action='store',
        default='/home/jsoules/src/spikeforest_recordings/sortings.json',
        help="The full path for the JSON file which contains the sortings. The sortings file content " +
            "should be equivalent to the output of an API call to SpikeForest.")
    parser.add_argument('--recordingset', '-r', action='store', default='',
        help='If set, will limit processing to the set of recordings named in the variable (e.g. "paired_kampff").')
    args = cast(ArgsDict, parser.parse_args())

def print_per_verbose(lvl: int, msg: str):
    if args['verbose'] < lvl: return
    tabs = max(0, lvl - 1)
    print("\t" * tabs + msg)

def slurp(filename: str) -> str:
    as_one_string = ''
    with open(filename) as f:
        while True:
            line = f.readline().rstrip()
            if not line: break
            as_one_string += line
    return as_one_string

def load_sortings() -> List[Dict[str, Any]]:
    hydrated_sortings = json.loads(slurp(args['sortingsfile']))
    return hydrated_sortings

def compute_quality_metrics(recording: RecordingExtractor, sorting: SortingExtractor) -> str:
    return st.validation.compute_quality_metrics(
        sorting, recording,
        metric_names=QUALITY_METRICS, as_dataframe=True).to_dict()

def compare_with_ground_truth(sorting: SortingExtractor, gt_sorting: SortingExtractor):
    ground_truth_comparison = GroundTruthComparison(gt_sorting, sorting)

    return {"best_match_21": ground_truth_comparison.best_match_21.to_list(),
            "best_match_12": ground_truth_comparison.best_match_12.to_list(),
            "agreement_scores": ground_truth_comparison.agreement_scores.to_dict()}

@hi.function(
    'compute_quality_metrics_hi', '0.1.0',
    kachery_support=True
)
def compute_quality_metrics_hi(recording_uri, gt_uri, firings_uri):
    # gt_uri is not needed, but including it lets this method and the ground truth comparison use the same consistent kwargs parameters.
    print_per_verbose(1, f"Computing quality metrics for recording {recording_uri} and sorting {firings_uri}. Fetching Extractors...")
    print_per_verbose(2, f"Execting le.LabboxEphysRecordingExtractor({recording_uri})")
    recording = le.LabboxEphysRecordingExtractor(recording_uri)
    sample_rate = recording.get_sampling_frequency()
    print_per_verbose(2, f"Found sample rate {sample_rate}.")
    sorting_object = {
        'sorting_format': 'mda',
        'data': {
            'firings': firings_uri,
            'samplerate': sample_rate
        }
    }
    print_per_verbose(2, f"(Comparison evaluation) Executing le.labboxEphysSortingExtractor({json.dumps(sorting_object)})")
    sorting = le.LabboxEphysSortingExtractor(sorting_object)
    print_per_verbose(2, f"Executing quality metrics")
    return compute_quality_metrics(recording, sorting)

@hi.function(
    'compute_ground_truth_comparison_hi', '0.1.0',
    kachery_support=True
)
def compute_ground_truth_comparison_hi(recording_uri, gt_uri, firings_uri):
    print_per_verbose(1, f"Computing ground truth comparison for ground truth {gt_uri} and sorting {firings_uri} (recording {recording_uri})")
    print_per_verbose(3, f'Fetching sample rate from {recording_uri}')
    recording = le.LabboxEphysRecordingExtractor(recording_uri)
    sample_rate = recording.get_sampling_frequency()
    print_per_verbose(3, f'Got sample rate {sample_rate}')
    print_per_verbose(2, f"Building sorting object for ground truth {gt_uri}")
    gt_firings = kp.load_object(gt_uri)['firings']
    print_per_verbose(2, f"Got ground truth firings {gt_firings}")
    gt_sorting_obj = {
        'sorting_format': 'mda',
        'data': {
            'firings': gt_firings,
            'samplerate': sample_rate
        }
    }
    gt_sorting = le.LabboxEphysSortingExtractor(gt_sorting_obj)
    print_per_verbose(2, f"Building sorting object for sorting with firings {firings_uri}")
    sorting_obj = {
        'sorting_format': 'mda',
        'data': {
            'firings': firings_uri,
            'samplerate': sample_rate
        }
    }
    sorting = le.LabboxEphysSortingExtractor(sorting_obj)
    print_per_verbose(2, f"Executing ground-truth comparison")
    return compare_with_ground_truth(sorting, gt_sorting)

def process_sorting_record(sorting_record):
    try:
        params = {
            'recording_uri': sorting_record[RECORDING_URI_KEY],
            'gt_uri': sorting_record[GROUND_TRUTH_URI_KEY],
            'firings_uri': sorting_record[SORTING_FIRINGS_URI_KEY]
        }
        quality_metric = hi.Job(compute_quality_metrics_hi, params).wait().return_value
        gt_comp = hi.Job(compute_ground_truth_comparison_hi, params).wait().return_value
        return (quality_metric, gt_comp)
    except KeyError:
        print(f"One of sorting/recording/gt-sorting keys missing from {json.dumps(sorting_record)}. Skipping...")
    return (None, None)

def make_comparison_entry(sorting_record, quality_metric, gt_comparison):
    return {
        'studyName': sorting_record['studyName'],
        'recordingName': sorting_record['recordingName'],
        'sorterName': sorting_record['sorterName'],
        'quality_metric': quality_metric,
        'ground_truth_comparison': gt_comparison
    }

def main():
    init_args()
    if args['test'] != 0: print(f"\tRunning in TEST MODE--Execution will stop after processing {args['test']} sortings!\n")
    count = 0
    sortings = load_sortings()
    comparisons = []

    if args['recordingset'] is not None and args['recordingset'] != '':
        sortings = [s for s in sortings if s['studyName'] == args['recordingset']]

    for sorting_record in sortings:
        (quality_metric, ground_truth_comparison) = process_sorting_record(sorting_record)
        if quality_metric is None or ground_truth_comparison is None: continue
        
        comparisons.append(make_comparison_entry(sorting_record, quality_metric, ground_truth_comparison))
        count += 1
        if args['test'] != 0 and count >= args['test']: break
    print(f"Results:\n{json.dumps(comparisons, indent=4)}")

if __name__ == "__main__":
    main()
