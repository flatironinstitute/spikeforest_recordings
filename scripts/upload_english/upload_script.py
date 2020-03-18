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


def register_recording_test(*, recdir, output_fname, label, to='default_readwrite'):
    print(f'''
        recdir: {recdir}
        output_fname: {output_fname}
        label: {label}
        to: {to}
    ''')


def register_recording(*, recdir, output_fname, label, to='default_readwrite'):
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


def register_groundtruth(*, recdir, output_fname, label, to='default_readwrite'):
    with ka.config(to=to):
        firings_path = ka.store_file(recdir + '/firings_true.mda')
        obj = dict(
            firings=firings_path
        )
        obj['self_reference'] = ka.store_object(obj, basename='{}.firings_true.json'.format(label))
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
    sorting = MdaSortingExtractor(firings_file=path_rec1 + '/firings_true.mda', 
        samplerate=rec.get_sampling_frequency())
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
    # update .json files
    register_recording(recdir=path_rec1, output_fname=os.path.join(path_to, rec1+'.json'), label=rec1)
    register_groundtruth(recdir=path_rec1, output_fname=os.path.join(path_to, rec1+'.firings_true.json'), label=rec1)

study_obj['self_reference'] = ka.store_object(study_obj)
with open(os.path.join(path_to, study_name + '.json'), 'w') as f:
    json.dump(study_obj, f, indent=4)

studyset_obj = dict(
    name=studyset_name,
    info=dict(
        label=studyset_name,
        electrode_type='silicon-probe',
        doi='10.1016/j.neuron.2017.09.033',
        ground_truth='Paired juxtacellular recording',
        organism='Mice',
        source='Daniel F. English, Virgina Tech',
        labels=["in-vivo paired recording"]
    ),
    description='''\
    # Silicon-juxtacellular hybrid probes
    This studyset consists of 29 paired recordings from Silicon-juxtacellular hybrid probes. \
    Juxtacellular electrodes are pulled from 1 mm OD 0.7 mm ID borosilicate glass and have impedances of 8-10 MOhm \
    when filled with 130 mM potassium acetate. These juxtacellular electrodes are glued to 32 channel silicon probes \
    (A1-32-Poly3, Neuronexus) using light-cure dental acrylic. Using the inter-site spacing of the silicon probe as \
    a visual distance guide, the tip of the juxtacellular is fixed at a distance of ~20 micrometers from the nearest silicon \
    probe recording site. The closest site is selected as a site in the middle (top to bottom) of an outer column of \
    recording sites. The close distance between the juxtacellular tip and the recording sites results in both devices \
    recording the same neuron at high probability. 
    
    #  Recording ground truth data in awake behaving mice
    Mice are placed in the head-fixed treadmill apparatus and the protective silicon elastomer is removed from the craniotomy, \
    the juxtacellular-silicon hybrid prove is inserted 0.1 mm into the brain, and the craniotomy is covered with silicon fluid to \
    prevent drying and improve stability. The probe is advanced into the brain at ~1-2 micrometers until action potentials are \
    observed on the juxtacellular electrode, at which point movement is ceased and data collection begins. 
    Electrical signals from the juxtacellular electrode are recorded and amplified through an analog microelectrode amplifier \
    (Cygnus IR-183), then digitized via an Intan RHD2000 system. Signals from the silicon probe are amplified and digitized \
    through the same RHD2000 system, which results in hardware synchronization of the two signals. By converting the digital \
    signals in the RHD2000 to analog voltage and outputting them to a digital microprocessor (CED Power1401), we calculated online \
    the juxtacellular spike triggered average of each channel of the extracellular electrode, and discard recordings in which the \
    triggered average does not contain a spike waveform on any channel.
    ''',
    studies=[
        study_obj
    ]
)

studyset_obj['self_reference'] = ka.store_object(studyset_obj)
with open(os.path.join(path_to, '../', studyset_name + '.json'), 'w') as f:
    json.dump(studyset_obj, f, indent=4)
