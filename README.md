# spikeforest_recordings

Ephys recordings and ground truth information for the SpikeForest project for benchmarking spike sorting algorithms.

See the live website: https://spikeforest.flatironinstitute.org

## Structure of the recordings

This repository contains (pointers to) the ephys recordings used by SpikeForest.

Directory structure is as follows:

```
recordings/
    STUDY_SET_1/
        STUDY_1_1/
            RECORDING_1_1_1.json
            RECORDING_1_1_1.firings_true.json
            RECORDING_1_1_2.json
            RECORDING_1_1_2.firings_true.json
            ...
        STUDY_1_2/
            ...
    STUDY_SET_2/
        ...
```

As can be seen, each study set consists of multiple studies, and each study in turn contains one or more recordings.

The structure of a recording JSON file is for example:

```json
{
    "raw": "sha1dir://615aa23efde8898aa89002613e20ad59dcde42f9.hybrid_janelia/drift_siprobe/rec_16c_600s_11/raw.mda",
    "params": {
        "samplerate": 30000,
        "spike_sign": -1,
        "scale_factor": 1
    },
    "geom": [[43.0,80.0], [11.0, 80.0], ...],
    "self_reference": "sha1://8c655b5fa8fa15ef0f2d7cdccec1b14468ea622a/HYBRID_JANELIA/hybrid_drift_siprobe/rec_16c_600s_11.json"
}
```

The "raw" field is a [kachery](https://github.com/flatironinstitute/kachery)-pointer to the raw timeseries data in .mda format. The "params" contains the samplerate and other optional parameters.
The "geom" contains the electrode locations. Finally "self_reference" is a convenience kachery-pointer that refers to the object itself (of course without the self_reference - that would be practically impossible).

The structure of a ground-truth sorting is for example:

```json
{
    "firings": "sha1dir://615aa23efde8898aa89002613e20ad59dcde42f9.hybrid_janelia/drift_siprobe/rec_16c_600s_11/firings_true.mda",
    "self_reference": "sha1://a660baf2c4cd0cd56cc45b9dbf4da92a9742ce8d/HYBRID_JANELIA/hybrid_drift_siprobe/rec_16c_600s_11.firings_true.json"
}
```

Here "firings" points to the spike times and labels in .mda format.

To retrieve any of these data, use the kachery Python API or command-line tools.

## Generating the recordings (internal)

The script used to generate these recordings is found in [scripts/prepare_recordings.py](scripts/prepare_recordings.py)

## Authors

Jeremy Magland