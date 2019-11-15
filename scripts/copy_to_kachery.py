from mountaintools import client as mt
import kachery as ka

mt.configDownloadFrom('spikeforest.public')
ka.set_config(
    preset='default_readwrite'
)

X = mt.loadObject(path='sha1://b678d798d67b6faa3c6240aca52f3857c9e4b877/analysis.json')
ka.store_object(X, basename='analysis.json')

X = ka.load_object('sha1://b678d798d67b6faa3c6240aca52f3857c9e4b877/analysis.json')

def get_sha1_part_of_sha1dir(path):
    if path.startswith('sha1dir://'):
        list0 = path.split('/')
        list1 = list0[2].split('.')
        return list1[0]
    else:
        return None

studies_to_include = ['paired_kampff']
fnames = ['geom.csv', 'params.json', 'raw.mda', 'firings_true.mda']
# fnames = ['geom.csv', 'params.json']
for studyset in X['StudySets']:
    print('STUDYSET: {}'.format(studyset['name']))
    for study in studyset['studies']:
        study_name = study['name']
        print('STUDY: {}'.format(study_name))
        if study_name in studies_to_include:
            for recording in study['recordings']:
                recname = recording['name']
                recdir = recording['directory']
                print('RECORDING: {}'.format(recname), recdir)
                sha1 = get_sha1_part_of_sha1dir(recdir)
                if sha1:
                   ff = mt.realizeFile('sha1://' + sha1)
                   print('Storing directory index file: {} for sha1={}'.format(ff, sha1))
                   ka.store_file(ff)
                for fname in fnames:
                    print('Realizing file: {}'.format(recdir + '/' + fname))
                    ff = mt.realizeFile(path=recdir + '/' + fname)
                    print('Storing file: {}'.format(ff))
                    ka.store_file(ff)