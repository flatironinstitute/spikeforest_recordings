#!/usr/bin/env python


from os.path import basename
import numpy as np
import json
from spikeforest2_utils import AutoRecordingExtractor, MdaRecordingExtractor, MdaSortingExtractor
import hither
import kachery as ka
import os

studyset_name = 'PAIRED_ENGLISH'
study_name = 'paired_english'
path_from = '/mnt/ceph/users/jjun/groundtruth/paired_english'
path_to = '/mnt/home/jjun/src/spikeforest_recordings/recordings/PAIRED_ENGLISH/paired_english'


def register_recording_test(*, recdir, output_fname, label, to):
    print(f'''
        recdir: {recdir}
        output_fname: {output_fname}
        label: {label}
        to: {to}
    ''')


def register_recording(*, recdir, output_fname, label, to):
    with ka.config(to=to):
        raw_path = ka.store_file(recdir + '/raw.mda')
        obj = dict(
            raw=raw_path,
            params=ka.load_object(recdir + '/params.json'),
            geom=np.genfromtxt(ka.load_file(recdir + '/geom.csv'), delimiter=',').tolist()
        )
        obj['self_reference'] = ka.store_object(obj, basename='{}.json'.format(label))
        with open(output_fname, 'w') as f:
            json.dump(obj, f, indent=4)


def register_groundtruth(*, recdir, output_fname, label, to):
    with ka.config(to=to):
        raw_path = ka.store_file(recdir + '/raw.mda')
        obj = dict(
            firings=raw_path
        )
        obj['self_reference'] = ka.store_object(obj, basename='{}.json'.format(label))
        with open(output_fname, 'w') as f:
            json.dump(obj, f, indent=4)

ka.set_config(
    fr='default_readwrite',
    to='default_readwrite'
)

list_rec = [str(f) for f in os.listdir(path_from) if os.path.isdir(os.path.join(path_from, f))]

print('# files: {}'.format(len(list_rec)))
study_obj = dict(
    name=study_name,
    studySetName=studyset_name,
    recordings=[]
)
for rec1 in list_rec:
    print(f'Uploading {rec1}')
    path_rec1 = os.path.join(path_from, rec1)
    rec = MdaRecordingExtractor(recording_directory=path_rec1)
    sorting = MdaSortingExtractor(firings_file=path_rec1 + '/firings_true.mda')
    if False:
        register_recording(
            recdir = path_rec1, 
            output_fname = os.path.join(path_to, rec1+'.json'),
            label = rec1,
            to = 'default_readwrite'
        )
    if False:
        register_groundtruth(
            recdir = path_rec1, 
            output_fname = os.path.join(path_to, rec1+'.firings_true.json'),
            label = rec1+'.firings_true',
            to = 'default_readwrite'
        )
    recording_obj = dict(
        name=rec1,
        studyName=study_name,
        studySetName=studyset_name,
        directory=ka.store_dir(path_rec1),
        firingsTrue=ka.store_file(os.path.join(path_to, rec1+'.firings_true.json'), basename='firings_true.json'),
        sampleRateHz=rec.get_sampling_frequency(),
        numChannels=len(rec.get_channel_ids()),
        durationSec=rec.get_num_frames() / rec.get_sampling_frequency(),
        numTrueUnits=len(sorting.get_unit_ids()),
        spikeSign=-1 # TODO: get this from params.json
    )
    study_obj['recordings'].append(recording_obj)

study_obj['self_reference'] = ka.store_object(study_obj)
with open(os.path.join(path_to, studyset_name, study_name, study_name + '.json'), 'w') as f:
    json.dump(study_obj, f, indent=4)

studyset_obj = dict(
    name=studyset_name,
    info=dict(
        label=studyset_name,
        electrode_type='[electrode_type]',
        doi='[doi]',
        ground_truth='[ground_truth]',
        organism='[organism]',
        source='[source]',
        labels=["in-vivo"]
    ),
    description='[description]',
    studies=[
        study_obj
    ]
)

studyset_obj['self_reference'] = ka.store_object(studyset_obj)
with open(os.path.join(path_to, studyset_name, studyset_name + '.json'), 'w') as f:
    json.dump(studyset_obj, f, indent=4)
