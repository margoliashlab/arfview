"""an alpha version of the plotter"""

from __future__ import absolute_import, division, \
    print_function
from PySide import QtGui, QtCore
from PySide.QtGui import QApplication, QCursor
import signal
import sys
import pyqtgraph as pg
import pyqtgraph.dockarea as pgd
import h5py
import numpy as np
from scipy.io import wavfile
import os.path
import tempfile
from _arfview.datatree import DataTreeView, createtemparf, named_types
import _arfview.utils as utils
QtCore.qInstallMsgHandler(lambda *args: None)  # suppresses PySide 1.2.1 bug
from scipy.interpolate import interp2d
import scipy.signal
from _arfview.labelPlot import labelPlot
from _arfview.treeToolBar import treeToolBar
from _arfview.settingsPanel import settingsPanel
from _arfview.rasterPlot import rasterPlot
from _arfview.downsamplePlot import downsamplePlot
from _arfview.spectrogram import spectrogram
from _arfview.plotScrollArea import plotScrollArea
from treemodel import *
from _arfview.exportPlotWindow import exportPlotWindow
import argparse
import arf
import libtfr
import subprocess
import lbl
import time


class MainWindow(QtGui.QMainWindow):
    '''the main window of the program'''
    def __init__(self, file_names):
        super(MainWindow, self).__init__()
        self.file_names = file_names
        self.current_file = None
        self.open_files = []    # TODO replace current_file with list
        self.plotchecked = False
        self.initUI()

    #setting up context manager to make sure files get closed
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        for file in self.tree_model.files:
            file.close()

    def initUI(self):
        """"Assembles the basic Gui layout, status bar, menubar
        toolbar etc."""
        # status bar
        self.statusBar().showMessage('Ready')

        # actions
        soundAction = QtGui.QAction(QtGui.QIcon.fromTheme(
            'media-playback-start'), 'Play Sound', self)
        soundAction.setShortcut('Ctrl+S')
        soundAction.setStatusTip('Play data as sound')
        soundAction.triggered.connect(self.playSound)
        exitAction = QtGui.\
            QAction(QtGui.QIcon.fromTheme('window-close'),
                    'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(QtGui.qApp.quit)
        openAction = QtGui.\
            QAction(QtGui.QIcon.fromTheme('document-open'), 'Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open an arf file')
        openAction.triggered.connect(self.showDialog)

        newAction = QtGui.QAction('New', self)
        newAction.setStatusTip('Create new file')
        newAction.triggered.connect(self.new)

        exportAction = QtGui.QAction(QtGui.QIcon.fromTheme('document-save-as'),
                                    'Export Checked Data', self)
        exportAction.setShortcut('Ctrl+e')
        exportAction.setStatusTip('Export dataset as wav')
        exportAction.triggered.connect(self.export)

        exportSelectionAction = QtGui.QAction('Export Selection', self)
        exportSelectionAction.setVisible(False)
        exportSelectionAction.setStatusTip('')
        exportSelectionAction.triggered.connect(self.export_selection)
        self.exportSelectionAction = exportSelectionAction
        self.spec_selected = None

        exportPlotAction = QtGui.QAction('Export Plot', self)
        exportPlotAction.setStatusTip('Export Plot')
        exportPlotAction.triggered.connect(self.exportPlot)

        plotcheckedAction = QtGui.QAction(QtGui.QIcon.fromTheme('face-smile'),
                                          'Plot Checked', self)
        plotcheckedAction.setShortcut('Ctrl+k')
        plotcheckedAction.setStatusTip('plot checked')
        plotcheckedAction.triggered.connect(self.toggleplotchecked)
        self.plotcheckedAction = plotcheckedAction

        refreshAction = QtGui.QAction(QtGui.QIcon.fromTheme('view-refresh'),
                                      'Refresh Data View', self)
        refreshAction.setShortcut('Ctrl+r')
        refreshAction.setStatusTip('Refresh Data View')
        refreshAction.triggered.connect(self.refresh_data_view)

        labelAction = QtGui.QAction(QtGui.QIcon.fromTheme('insert-object'),
                                      'Add Labels', self)
        labelAction.setVisible(False)
        labelAction.setShortcut('Ctrl+l')
        labelAction.setStatusTip('Add label entry to current group')
        labelAction.triggered.connect(self.add_label)
        self.labelAction = labelAction

        deleteLabelAction = QtGui.QAction('Delete Label', self)
        deleteLabelAction.setVisible(False)
        deleteLabelAction.setShortcut('Ctrl+d')
        deleteLabelAction.setStatusTip('Add label entry to current group')
        self.deleteLabelAction = deleteLabelAction

        # addPlotAction = QtGui.QAction('Add Plot', self)
        # addPlotAction.setVisible(False)
        # addPlotAction.setStatusTip('Add checked datasets to current plot')
        # addPlotAction.triggered.connect(self.add_plot)
        # self.addPlotAction = addPlotAction

        # menubar
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(exportAction)
        fileMenu.addAction(plotcheckedAction)
        fileMenu.addAction(refreshAction)

        # toolbar
        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.addAction(exitAction)
        self.toolbar.addAction(openAction)
        self.toolbar.addAction(newAction)
        self.toolbar.addAction(soundAction)
        self.toolbar.addAction(exportAction)
        self.toolbar.addAction(exportPlotAction)
        self.toolbar.addAction(exportSelectionAction)
        self.toolbar.addAction(plotcheckedAction)
        self.toolbar.addAction(refreshAction)
        self.toolbar.addAction(labelAction)
        self.toolbar.addAction(deleteLabelAction)
        #self.toolbar.addAction(addPlotAction)

        # tree model
        self.tree_model = TreeModel(self.file_names)

        # tree view
        self.tree_view = ArfTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.pressed.connect(self.selectEntry)
        if self.current_file:
            self.populateTree()

        # tree_toolbar
        self.tree_toolbar = treeToolBar(self.tree_model)

        #attribute table
        self.attr_table = QtGui.QTableWidget(10, 2)
        self.attr_table.setHorizontalHeaderLabels(('key','value'))

        #plot region
        self.plot_scroll_area = plotScrollArea(parent=self)
        self.data_layout = pg.GraphicsLayoutWidget()
        self.plot_scroll_area.setWidget(self.data_layout)
        self.plot_scroll_area.setWidgetResizable(True)
        self.subplots=[]

        #settings panel
        self.settings_panel = settingsPanel()

        #error message
        self.error_message = QtGui.QErrorMessage(parent=self)
        self.error_message.setFixedSize(500,200)
        # final steps
        self.area = pgd.DockArea()
        tree_dock = pgd.Dock("Tree", size=(250, 100))
        data_dock = pgd.Dock("Data", size=(400, 100))
        attr_table_dock = pgd.Dock("Attributes", size=(200, 50))
        settings_dock = pgd.Dock('Settings', size=(150,1))
        self.area.addDock(tree_dock, 'left')
        self.area.addDock(data_dock, 'right')
        self.area.addDock(attr_table_dock, 'bottom', tree_dock)
        self.area.addDock(settings_dock, 'bottom', attr_table_dock)
        tree_dock.addWidget(self.tree_view)
        header = self.tree_view.header()
        header.resizeSection(0,150)
        header.resizeSection(1,100)
        header.resizeSection(2,150)
        tree_dock.addWidget(self.tree_toolbar)
        tree_dock.addAction(exitAction)
        data_dock.addWidget(self.plot_scroll_area)
        #data_dock.addWidget(self.data_layout)
        attr_table_dock.addWidget(self.attr_table)
        settings_dock.addWidget(self.settings_panel)
        self.settings_panel.show()

        self.setCentralWidget(self.area)
        self.setWindowTitle('arfview')
        self.resize(1300, 700)
        self.show()

    def toggleplotchecked(self):
        self.plotchecked = not self.plotchecked
        if self.plotchecked:
            self.plotcheckedAction.setIcon(QtGui.QIcon.fromTheme('face-cool'))
            self.plotcheckedAction.setStatusTip('click to turn check mode off')
            self.plotcheckedAction.setText('Check Mode Is On')
            self.plotcheckedAction.setIconText('Check Mode Is On')
            #self.addPlotAction.setVisible(True)
        else:
            self.plotcheckedAction.setIcon(QtGui.QIcon.fromTheme('face-smile'))
            self.plotcheckedAction.setStatusTip('Click to turn check mode on')
            self.plotcheckedAction.setText('Check Mode Is Off')
            self.plotcheckedAction.setIconText('Check Mode Is Off')
            #self.addPlotAction.setVisible(False)

    def new(self):
        fname, fileextension = QtGui.QFileDialog.\
                               getSaveFileName(self, 'Save file', '.', '*.arf')
        self.tree_model.insertFile(fname, mode='w')

    def exportPlot(self):
        exportWin = exportPlotWindow(self.data_layout.centralWidget)
        exportWin.exec_()

    def export(self):
        items = self.tree_model.getCheckedDatasets()
        if not items: return
        savedir, filename = os.path.split(items[0].file.filename)
        savepath =  os.path.join(savedir,os.path.splitext(filename)[0]
                                 + '_' + items[0].name.replace('/','_'))

        for i,item in enumerate(items):
            if 'datatype' in item.attrs.keys() and item.attrs['datatype'] < 1000:
                fname, fileextension = QtGui.QFileDialog.\
                                       getSaveFileName(self, 'Save data as',
                                                       savepath,
                                                       'wav (*.wav);;text (*.csv, *.dat)')

            elif 'datatype' in item.attrs.keys() and item.attrs.get('datatype')==2002:
                fname, fileextension = QtGui.QFileDialog.\
                                       getSaveFileName(self, 'Save data as',
                                                       savepath,
                                                       'lbl (*.lbl)')

            export(item, fileextension.split(' ')[0], fname)                
                

    def export_selection(self):
        fname, fileextension = QtGui.QFileDialog.\
                               getSaveFileName(self, 'Save data as',
                                               '',
                                               'wav (*.wav);;text (*.csv, *.dat)')
        bounds = np.array(self.spec_selected.selection.getRegion())
        bounds = np.array(bounds*self.spec_selected.dataset.attrs['sampling_rate'],
                          dtype = int)
        export(self.spec_selected.dataset, fileextension.split(' ')[0], fname, 
               start_idx=bounds[0], stop_idx=bounds[1])

    def playSound(self):
        indexes = self.tree_view.selectedIndexes()
        if len(indexes) == 1:
            dataset = self.tree_model.getEntry(indexes[0].internalPointer())
        playSound(dataset, self)

    def showDialog(self):
        extensions = '*.arf *.hdf5 *.h5 *.mat *.wav *.lbl'
        #added because not all of arfx compiles on OS X
        try:
            from arfx import pcmio
            extensions += ' *.pcm *.pcm_seq2'
        except ImportError:
            pass

        fname, fileextension = QtGui.QFileDialog.\
                               getOpenFileName(self, 'Open file', '.', extensions)
        if not fname: return
        ext = os.path.splitext(fname)[-1]
        if ext not in ('.arf','.hdf5','.h5','.mat'):
            if ext in ('.lbl', '.wav'):
                temp_h5f = createtemparf(fname)
            elif ext in ('.pcm', '.pcm_seq2'):
                # reversing value and key to access type number from datatype_name
                sampled_types = {value:key for key,value in named_types.items()
                                 if key > 0 and key < 1000}
                datatype_name,ok = QtGui.QInputDialog.getItem(self, "",
                                                              "Select datatype of file",
                                                              sampled_types.keys())
                if not ok: return
                temp_h5f = createtemparf(fname, datatype=sampled_types[datatype_name])

            fname = temp_h5f.file.filename
        self.tree_model.insertFile(fname)

    def plot_checked_datasets(self):
        checked_datasets = self.tree_model.getCheckedDatasets()
        self.plot_dataset_list(checked_datasets, self.data_layout)

    def refresh_data_view(self):
        if self.plotchecked:
            self.plot_checked_datasets()
        else:
            datasets = []
            entries = [self.tree_model.getEntry(idx.internalPointer()) for idx
                       in self.tree_view.selectedIndexes()]
            for entry in entries:
                if type(entry) == h5py.Dataset:
                    datasets.append(entry)
                else:
                    datasets.extend([x for x in entry.itervalues() if type(x) == h5py.Dataset])

            self.plot_dataset_list(datasets, self.data_layout)
        
        self.exportSelectionAction.setVisible(False)
        self.spec_selected = None

    def add_plot(self):
        checked_datasets = self.tree_view.all_checked_dataset_elements()
        if len(checked_datasets) > 0 and self.plotchecked:
            new_layout = self.data_layout.addLayout(row=len(self.subplots),col=0)
            self.plot_dataset_list(checked_datasets, new_layout)


    def selectEntry(self):
        if not self.plotchecked:
            self.refresh_data_view()

        indexes = self.tree_view.selectedIndexes()
        if len(indexes) == 1:
            self.labelAction.setVisible(True)
            node = indexes[0].internalPointer()
            entry = self.tree_model.getEntry(node)
            self.populateAttrTable(entry)
        else:
            self.labelAction.setVisible(False)

    def spectrogramSelection(self, spec_selected):
        '''Slot that handles selection made on spectrogram'''
        self.spec_selected = spec_selected
        for pl in self.subplots:
            if isinstance(pl, spectrogram) and pl is not spec_selected:
                pl.removeSelection()
            self.exportSelectionAction.setVisible(True)

    def populateAttrTable(self, item):
        """Populate QTableWidget with attribute values of hdf5 item ITEM"""
        self.attr_table.setRowCount(len(item.attrs.keys()))
        for row, (key, value) in enumerate(item.attrs.iteritems()):
            attribute = QtGui.QTableWidgetItem(str(key))
            attribute_value = QtGui.QTableWidgetItem(str(value))
            attribute.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            attribute_value.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.attr_table.setItem(row, 0, attribute)
            self.attr_table.setItem(row, 1, attribute_value)

    def add_label(self):
        indexes = self.tree_view.selectedIndexes()
        if len(indexes) == 1:
            node = indexes[0].internalPointer()
            entry = self.tree_model.getEntry(node)
        if isinstance(entry, h5py.Group):
            lbl_parent = entry
            parentIndex = indexes[0]
        elif isinstance(entry, h5py.Dataset):
            lbl_parent = entry.parent
            parentIndex = indexes[0].parent()

        self.tree_model.insertLabel(parentIndex)
        self.refresh_data_view()

    def label_selected(self):
        self.deleteLabelAction.setVisible(True)

    def label_unselected(self):
        self.deleteLabelAction.setVisible(False)

    def keyPressEvent(self, event):
        '''implements select next entry shortcut'''
        if (event.key()==QtCore.Qt.Key_F and 
            event.modifiers() == QtCore.Qt.ControlModifier):
            self.tree_view.select_next_entry()
            self.selectEntry()
            event.accept()

        elif (event.key()==QtCore.Qt.Key_F and 
              event.modifiers() == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier)):
            self.tree_view.select_entry_in_next_parent()
            self.selectEntry()
            event.accept()

    def plot_dataset_list(self, dataset_list, data_layout, append=False):
        ''' plots a list of datasets to a data layout'''
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        data_layout.clear()
        if not append:
            self.subplots = []
        toes = []
        t = time.time()
        unplotable = []
        for dataset in dataset_list:
            if 'datatype' not in dataset.attrs.keys():
                unplotable.append(''.join([dataset.file.filename, dataset.name]))
                continue

            '''sampled data'''
            if dataset.attrs.get('datatype') < 1000: # sampled data
                if (self.settings_panel.oscillogram_check.checkState()
                    ==QtCore.Qt.Checked):

                    pl = downsamplePlot(dataset,
                                        name=str(len(self.subplots)))
                    pl.setLabel('left', dataset.name.split('/')[-1])
                    data_layout.addItem(pl,row=len(self.subplots), col=0)
                    # max_default_range = 20
                    # xmax = min(dataset.size/float(dataset.attrs['sampling_rate']),
                    #            maxb_default_range)
                    # xrange = pl.dataItems[0].dataBounds(0)
                    # yrange = pl.dataItems[0].dataBounds(1)
                    # pl.setXRange(*xrange,padding=0)
                    # pl.setYRange(*yrange,padding=0)
                    self.subplots.append(pl)
                    pl.showGrid(x=True, y=True)
                ''' simple events '''
            elif utils.is_simple_event(dataset):
                if dataset.attrs.get('units') == 'ms':
                    data = dataset.value / 1000.
                elif dataset.attrs.get('units') == 'samples':
                    data = dataset.value / dataset.attrs['sampling_rate']
                else:
                    data = dataset.value
                if (self.settings_panel.raster_check.checkState()==QtCore.Qt.Checked or
                    self.settings_panel.psth_check.checkState()==QtCore.Qt.Checked or
                    self.settings_panel.isi_check.checkState()==QtCore.Qt.Checked):
                    toes.append(data)
                continue

                ''' complex event '''
            elif utils.is_complex_event(dataset):
                if (self.settings_panel.label_check.checkState()
                    ==QtCore.Qt.Checked):
                    pl = labelPlot(dataset.file,dataset.name, name=str(len(self.subplots)))
                    pl.setLabel('left', dataset.name.split('/')[-1])
                    data_layout.addItem(pl, row=len(self.subplots), col=0)
                    #pl.showLabel('left', show=False)
                    pl.sigLabelSelected.connect(self.label_selected)
                    pl.sigNoLabelSelected.connect(self.label_unselected)
                    self.deleteLabelAction.triggered.connect(pl.delete_selected_labels)
                    self.subplots.append(pl)

            else:
                unplotable.append(''.join([dataset.file.filename, dataset.name]))
                continue

            '''adding spectrograms'''
            if dataset.attrs.get('datatype') in (0,1,23): # show spectrogram
                if (self.settings_panel.spectrogram_check.checkState()
                    ==QtCore.Qt.Checked):
                    pl = spectrogram(dataset, self.settings_panel)
                    pl.selection_made.connect(self.spectrogramSelection)
                    data_layout.addItem(pl, row=len(self.subplots), col=0)
                    self.subplots.append(pl)

 #end for loop
        if toes:
            if self.settings_panel.raster_check.checkState()==QtCore.Qt.Checked:
                pl= rasterPlot(toes)
                data_layout.addItem(pl, row=len(self.subplots), col=0)
                pl.showLabel('left', show=False)
                self.subplots.append(pl)

            if self.settings_panel.psth_check.checkState()==QtCore.Qt.Checked:
                all_toes = np.zeros(sum(len(t) for t in toes))
                k=0
                for t in toes:
                    all_toes[k:k+len(t)] = t
                    k += len(t)
                if self.settings_panel.psth_bin_size.text():
                    bin_size = float(self.settings_panel.psth_bin_size.text())/1000.
                else:
                    bin_size = .01
                bins = np.arange(all_toes.min(),all_toes.max()+bin_size,bin_size)
                y,x = np.histogram(all_toes,bins=bins)
                psth = pg.PlotCurveItem(x, y, stepMode=True,
                                        fillLevel=0, brush=(0, 0, 255, 80))

                pl = data_layout.addPlot(row=len(self.subplots), col=0)
                pl.addItem(psth)
                pl.setMouseEnabled(y=False)
                self.subplots.append(pl)

        if self.settings_panel.isi_check.checkState()==QtCore.Qt.Checked:
            isis = np.zeros(sum(len(t)-1 for t in toes))
            k=0
            for t in toes:
                isis[k:k+len(t)-1] = np.diff(t)
                k += len(t)-1
            if self.settings_panel.psth_bin_size.text():
                bin_size = float(self.settings_panel.psth_bin_size.text())/1000.
            else:
                bin_size = .01
            bins = np.arange(isis.min(),isis.max()+bin_size,bin_size)
            y,x = np.histogram(isis,bins=bins,normed=True)
            isi_hist = pg.PlotCurveItem(x, y, stepMode=True,
                                    fillLevel=0, brush=(0, 0, 255, 80))

            pl = data_layout.addPlot(row=len(self.subplots), col=0)
            pl.addItem(isi_hist)
            pl.setMouseEnabled(y=False)
            self.subplots.append(pl)

        '''linking x axes'''
        minPlotHeight = 100
        masterXLink = None
        for pl in self.subplots:
            if not masterXLink:
                masterXLink = pl
            pl.setXLink(masterXLink)
            pl.setMinimumHeight(minPlotHeight)

        if any(isinstance(pl, spectrogram) for pl in self.subplots):
            self.exportSelectionAction.setVisible(True)
        else:
            self.exportSelectionAction.setVisible(False)

        spacing = 5
        self.data_layout.centralWidget.layout.setSpacing(spacing)
        self.data_layout.setMinimumHeight(len(self.subplots)*(minPlotHeight+spacing))
        QApplication.restoreOverrideCursor()
        if unplotable:
            self.error_message.showMessage("Could not plot the following datasets: %s" %('\n'.join(unplotable)),
            "plot_error")

## Make all plots clickable
lastClicked = []

def clicked(plot, points):
    global lastClicked
    for p in lastClicked:
        p.resetPen()
    for p in points:
        p.setPen('b', width=2)
    lastClicked = points


def export(dataset, export_format='wav', savepath=None, start_idx=None, stop_idx=None):
    if not savepath:
        savepath = os.path.basename(dataset.name)
    if export_format == 'wav':
        data = np.int16(dataset[start_idx:stop_idx] / 
                        max(abs(dataset[start_idx:stop_idx])) * (2**15 - 1))
        wavfile.write(savepath + '.wav', dataset.attrs['sampling_rate'], data)
    if export_format == 'text':
        np.savetxt(savepath + '.csv', dataset)
    if export_format == 'lbl':
        lbl.write(savepath + '.lbl', dataset[start_idx:stop_idx])

def playSound(data, mainWin):
    tfile = tempfile.mktemp() + '_' + data.name.replace('/', '_') + '.wav'
    normed_data = np.int16(data/np.max(np.abs(data.value)) * 32767)
    wavfile.write(tfile, data.attrs['sampling_rate'],
                  normed_data)
    # can't access PATH environment variable with frozen app,
    # so hardcoding most likely sox paths
    paths = ['/usr/local/bin', '/opt/local/bin', '/usr/bin']
    for p in paths:
        play_path = ''.join([p, '/play'])
        if os.path.exists(play_path):
            subprocess.Popen([play_path, tfile])
            break

def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    sys.stderr.write('\r')
    QtGui.QApplication.quit()

def interpolate_spectrogram(spec, res_factor):
    """Interpolates spectrogram for plotting"""
    x = np.arange(spec.shape[1])
    y = np.arange(spec.shape[0])
    f = interp2d(x, y, spec, copy=False, kind = 'quintic')
    xnew = np.arange(0,spec.shape[1],1./res_factor)
    ynew = np.arange(0,spec.shape[0],1./res_factor)
    new_spec = f(xnew,ynew)

    return new_spec

def main():
    p = argparse.ArgumentParser(prog='arfview')
    p.add_argument('file_names', nargs='*',default=[])
    options = p.parse_args()
    signal.signal(signal.SIGINT, sigint_handler)
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('arfview')
    timer = QtCore.QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.
    with MainWindow(options.file_names) as mainWin:
        sys.exit(app.exec_())

if __name__=='__main__':
    main()
