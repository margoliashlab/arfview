''' general utilities for the program '''
import h5py
import time
def is_simple_event(dataset):
    if dataset.attrs['datatype'] >= 1000 and dataset.dtype.names is None:
        return True
    else:
        return False

def is_complex_event(dataset):
    if dataset.attrs['datatype'] >= 1000 and dataset.dtype.names is not None \
    and set(('name', 'start', 'stop')).issubset(dataset.dtype.names):
        return True
    else:
        return False

def replace_dataset(dataset, parent, **kwargs):
    '''replaces data in "dataset" with dataset created with keyword arguments kwargs
    passed to the create_dataset method of the parent of "dataset"'''
    name = dataset.name.split('/')[-1]
    k = 0
    temp_name = '_'.join([name, 'temp', str(k)])
    while temp_name in parent.keys():
        k+=1
        temp_name = '_'.join([name, 'temp', str(k)])

    try:
        new_dset = parent.create_dataset(temp_name,**kwargs)
        for key,value in dataset.attrs.items():
            new_dset.attrs.create(key,value)
    except:
        del parent[temp_name]

    del parent[name]
    while name in parent.keys():
        pass
    parent[name] = parent[temp_name]
    del parent[temp_name]
    
    return parent[name]

    



















