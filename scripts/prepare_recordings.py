#!/usr/bin/env python

# pip install --upgrade kachery

import json
import argparse
import numpy as np
import kachery as ka
import os

def main():
    parser = argparse.ArgumentParser(
        description="Prepare SpikeForest recordings (i.e., populate this repository)")
    parser.add_argument('output_dir', help='The output directory (e.g., recordings)')
    parser.add_argument('--upload', action='store_true', help='Whether to upload the recording objects to kachery (password required)')
    # parser.add_argument('--verbose', action='store_true', help='Turn on verbose output')

    args = parser.parse_args()
    output_dir = args.output_dir

    if args.upload:
        ka.set_config(preset='default_readwrite')
    else:
        ka.set_config(preset='default_readonly')

    # Load a spikeforest analysis object
    X = ka.load_object('sha1://b678d798d67b6faa3c6240aca52f3857c9e4b877/analysis.json')

    # the output directory on the local machine
    basedir = output_dir
    if os.path.exists(basedir):
        raise Exception('Directory already exists: {}'.format(basedir))

    if not os.path.exists(basedir):
        os.mkdir(basedir)

    # download just one study for now
    studysets_to_include = ['PAIRED_BOYDEN', 'PAIRED_CRCNS_HC1', 'PAIRED_MEA64C_YGER', 'PAIRED_KAMPFF', 'PAIRED_MONOTRODE', 'SYNTH_MONOTRODE', 'SYNTH_MAGLAND', 'SYNTH_MEAREC_NEURONEXUS', 'SYNTH_MEAREC_TETRODE', 'SYNTH_MONOTRODE', 'SYNTH_VISAPY', 'HYBRID_JANELIA', 'MANUAL_FRANKLAB']

    # These are the files to download within each recording
    fnames = ['geom.csv', 'params.json', 'raw.mda', 'firings_true.mda']
    # fnames = ['geom.csv', 'params.json']
    for studyset in X['StudySets']:
        studyset_name = studyset['name']
        if studyset_name in studysets_to_include:
            print('STUDYSET: {}'.format(studyset['name']))
            studysetdir_local = os.path.join(basedir, studyset_name)
            if not os.path.exists(studysetdir_local):
                os.mkdir(studysetdir_local)
            for study in studyset['studies']:
                study_name = study['name']
                print('STUDY: {}/{}'.format(studyset_name, study_name))
                if True: # because I can't easily unindent in this editor :)
                    studydir_local = os.path.join(studysetdir_local, study_name)
                    if not os.path.exists(studydir_local):
                        os.mkdir(studydir_local)
                    for recording in study['recordings']:
                        recname = recording['name']
                        print('RECORDING: {}/{}/{}'.format(studyset_name, study_name, recname))
                        recdir = recording['directory']
                        recfile = os.path.join(studydir_local, recname + '.json')
                        obj = dict(
                            raw=recdir + '/raw.mda',
                            params=ka.load_object(recdir + '/params.json'),
                            geom=np.genfromtxt(ka.load_file(recdir + '/geom.csv'), delimiter=',').T
                        )
                        obj = _json_serialize(obj)
                        obj['self_reference'] = ka.store_object(obj, basename='{}/{}/{}.json'.format(studyset_name, study_name, recname))
                        with open(recfile, 'w') as f:
                            json.dump(obj, f, indent=4)
                        firings_true_file = os.path.join(studydir_local, recname + '.firings_true.json')
                        obj2 = dict(
                            firings=recdir + '/firings_true.mda'
                        )
                        obj2['self_reference'] = ka.store_object(obj2, basename='{}/{}/{}.firings_true.json'.format(studyset_name, study_name, recname))
                        with open(firings_true_file, 'w') as f:
                            json.dump(obj2, f, indent=4)

def _listify_ndarray(x):
    if x.ndim == 1:
        if np.issubdtype(x.dtype, np.integer):
            return [int(val) for val in x]
        else:
            return [float(val) for val in x]
    elif x.ndim == 2:
        ret = []
        for j in range(x.shape[1]):
            ret.append(_listify_ndarray(x[:, j]))
        return ret
    elif x.ndim == 3:
        ret = []
        for j in range(x.shape[2]):
            ret.append(_listify_ndarray(x[:, :, j]))
        return ret
    elif x.ndim == 4:
        ret = []
        for j in range(x.shape[3]):
            ret.append(_listify_ndarray(x[:, :, :, j]))
        return ret
    else:
        raise Exception('Cannot listify ndarray with {} dims.'.format(x.ndim))

def _json_serialize(x):
    if isinstance(x, np.ndarray):
        return _listify_ndarray(x)
    elif isinstance(x, np.integer):
        return int(x)
    elif isinstance(x, np.floating):
        return float(x)
    elif type(x) == dict:
        ret = dict()
        for key, val in x.items():
            ret[key] = _json_serialize(val)
        return ret
    elif type(x) == list:
        ret = []
        for i, val in enumerate(x):
            ret.append(_json_serialize(val))
        return ret
    else:
        return x

if __name__ == '__main__':
    main()
