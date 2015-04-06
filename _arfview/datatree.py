'''
datatree.py

This file contains aspects of arf model and it's associated view DataTreeView

'''
import tempfile
import os.path
from PySide import QtGui
from PySide.QtCore import Qt
from datetime import datetime
from dateutil import tz
import h5py
import lbl
import arf
import ewave

named_types = {0 : 'UNDEFINED', 1 : 'ACOUSTIC', 2 : 'EXTRAC_HP', 3 : 'EXTRAC_LF',
               4 : 'EXTRAC_EEG', 5 : 'INTRAC_CC', 6 : 'INTRAC_VC',
               23 : 'EXTRAC_RAW',
               1000 : 'EVENT',
               1001 : 'SPIKET',
               1002 : 'BEHAVET',
               2000 : 'INTERVAL',
               2001 : 'STIMI',
               2002 : 'COMPONENTL'}

def get_str_type(h5Object):
    if type(h5Object) == h5py.Dataset and 'datatype' in h5Object.attrs.keys():
        if h5Object.attrs['datatype'] in named_types.keys():
            return named_types[h5Object.attrs['datatype']]
        else: return str(h5Object.attrs['datatype'])
    if type(h5Object) == h5py.Group:
        return ('entry')


def get_str_time(entry):
    if 'timestamp' not in entry.attrs.keys():
        return('')
    time = datetime.fromtimestamp(entry.attrs['timestamp'][0] + entry.attrs['timestamp'][1] * 1e-6,
                                  tz.tzutc()).astimezone(tz.tzlocal())
    return time.strftime('%Y-%m-%d, %H:%M:%S:%f')

def createtemparf(filename, datatype=0):
    root, ext = os.path.splitext(filename)
    arffile = arf.open_file(tempfile.mktemp())
    if ext == '.lbl':
        lbl_rec = lbl.read(filename)
        print(lbl_rec)
        dset = arf.create_dataset(arffile, os.path.split(filename)[-1],
                                  lbl_rec, units=['','s','s'], datatype=2002)
        dset.attrs['units'] = 's'
    elif ext == '.wav':
        wavfile = ewave.open(filename)        
        arf.create_dataset(arffile, os.path.split(filename)[-1], wavfile.read(),
                           sampling_rate=wavfile.sampling_rate, datatype=1)
    elif ext =='.pcm':
        from arfx import pcmio
        pcmfile = pcmio.open(filename)
        arf.create_dataset(arffile, os.path.split(filename)[-1], pcmfile.read(),
                           sampling_rate=pcmfile.sampling_rate, datatype=datatype)
    elif ext == '.pcm_seq2':
        from arfx import io
        pcmseqfile = io.open(filename)
        dataset_basename = os.path.split(filename)[-1]
        for i in xrange(pcmseqfile.nentries):
            dataset_name = '_'.join([dataset_basename, str(i)])
            arf.create_dataset(arffile, dataset_name, pcmseqfile.read(),
                               sampling_rate=pcmseqfile.sampling_rate, 
                               timestamp=pcmseqfile.timestamp, datatype=datatype)
            pcmseqfile.entry += 1
            

    return arffile['/']
    

class Model():
    '''A data object for the data model,
    self.data must be an arf type entry or dataset

    This function was created due to PySide segfaulting on adding hdf5 objects as data
    it essentiall provides a python object wrapper for h5py objects and has some functions
    for converting other data types to this model'''
    def __init__(self, data):
        if type(data) in [h5py.Dataset, h5py.Group]:
            self.data = data
        else:
            raise TypeError     # TODO create and arf type with the data
    def __call__(self):
        return self.data


class DataTreeItem(QtGui.QTreeWidgetItem):
    ''' an item in a data tree'''
    def __init__(self, data, *args, **kwargs):
        super(DataTreeItem, self).__init__(*args, **kwargs)
        self.setData(0, Qt.UserRole, Model(data))

    def getData(self):
        ''' use this to access the arf data in a DataTreeItem '''
        return self.data(0, Qt.UserRole)()


class DataTreeView(QtGui.QTreeWidget):
    ''' a tree for storing data, both in hdf5 and other formats '''
    def __init__(self, *args, **kwargs):
        super(DataTreeView, self).__init__(*args, **kwargs)
        self.setColumnCount(4)
        self.setHeaderLabels(('Name', 'Type', 'Time', 'File'))

    def add(self, data, parent_node=None):
        '''creates a DataTreeItem from data and returns it'''
        # assuming arf for now
        str_type = get_str_type(data)
        if type(data) == h5py.Group:
            str_time = get_str_time(data)
        else: str_time = ''
        fname = data.file.filename
        tree_node = DataTreeItem(data, [data.name, str_type, str_time, fname])
        tree_node.setData(0, Qt.UserRole, Model(data))
        if type(data) == h5py.Dataset:
            tree_node.setCheckState(0, Qt.CheckState.Unchecked)
        if parent_node is not None:
            parent_node.addChild(tree_node)
        else:
            self.addTopLevelItem(tree_node)
        return tree_node

    def recursivePopulateTree(self, node_data, parent_node=None):
        node = self.add(node_data, parent_node)
        if type(node_data) == h5py.Group:
            sorted_childs = sorted(node_data.values(), cmp=lambda x,y: cmp(x.name, y.name))
            #sorted_childs = [node_data[k] for k in arf.keys_by_creation(node_data)] 
            [self.recursivePopulateTree(children, node) for children in sorted_childs]

    def all_dataset_elements(self):
        ''' returns all the elements in the tree'''
        elements = []
        roots = [self.topLevelItem(i) for i in range(self.topLevelItemCount())]
        for r in roots:
            entries = [r.child(i) for i in range(r.childCount())]
            topleveldatasets = [x for x in entries if type(x.getData()) == h5py.Dataset]
            elements.extend(topleveldatasets)
            for entry in entries:
                datasets = [entry.child(i) for i in range(entry.childCount())]
                elements.extend(datasets)
        return elements

    def all_checked_dataset_elements(self):
        dataset_items = self.all_dataset_elements()
        return [x.getData() for x in dataset_items if x.checkState(0) == Qt.Checked]

