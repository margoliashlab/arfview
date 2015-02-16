from PySide import QtGui, QtCore
import pyqtgraph.dockarea as pgd
import pyqtgraph as pg

class settingsPanel(QtGui.QWidget):
    def __init__(self):
        super(settingsPanel, self).__init__()       
        self.defaults = {'psth_bin':10,
                         'isi_bin':10,
                         'win_size':512,
                         'step':1,
                         'freq_min':0,
                         'freq_max':10000}
        self.initUI() 
    def initUI(self):
        
        layout = QtGui.QVBoxLayout()
        self.oscillogram_check=QtGui.QCheckBox("Oscillogram")
        self.oscillogram_check.setCheckState(QtCore.Qt.CheckState.Checked)
        self.raster_check=QtGui.QCheckBox("Raster")
        self.raster_check.setCheckState(QtCore.Qt.CheckState.Checked)
        self.label_check=QtGui.QCheckBox("Label")
        self.label_check.setCheckState(QtCore.Qt.CheckState.Checked)
        self.psth_check=QtGui.QCheckBox("PSTH")
        self.psth_bin_size = QtGui.QLineEdit(str(self.defaults['psth_bin']))
        self.isi_check=QtGui.QCheckBox("ISI")
        self.isi_bin_size = QtGui.QLineEdit(str(self.defaults['isi_bin']))
        self.spectrogram_check=QtGui.QCheckBox("Spectrogram")
        self.spectrogram_box = self.create_spectrogram_box()

        psth_settings_layout = QtGui.QHBoxLayout()
        psth_settings_layout.addWidget(self.psth_check)
        psth_settings_layout.addWidget(QtGui.QLabel("Bin Size: "))
        self.psth_bin_size.setMaximumWidth(50)
        psth_settings_layout.addWidget(self.psth_bin_size)
        psth_settings_layout.addWidget(QtGui.QLabel('ms'))
        psth_settings_layout.addStretch()
        psth_settings_layout.setContentsMargins(0,0,0,0)
        
        isi_settings_layout = QtGui.QHBoxLayout()
        isi_settings_layout.addWidget(self.isi_check)
        isi_settings_layout.addSpacing(18)
        isi_settings_layout.addWidget(QtGui.QLabel("Bin Size: "))
        self.isi_bin_size.setMaximumWidth(50)
        isi_settings_layout.addWidget(self.isi_bin_size)
        isi_settings_layout.addWidget(QtGui.QLabel('ms'))
        isi_settings_layout.addStretch()
        isi_settings_layout.setContentsMargins(0,0,0,0)
        
        layout.addWidget(self.oscillogram_check)
        layout.addWidget(self.raster_check)
        layout.addWidget(self.label_check)
        layout.addLayout(psth_settings_layout)
        layout.addLayout(isi_settings_layout)
        layout.addWidget(self.spectrogram_check)
        layout.addWidget(self.spectrogram_box)
        layout.addStretch()

        self.setLayout(layout)
        

    def create_spectrogram_box(self):
        #self.spectrogram_check.setCheckState(QtCore.Qt.CheckState.Checked)
        self.win_size = QtGui.QLineEdit(str(self.defaults['win_size']))
        self.step = QtGui.QLineEdit(str(self.defaults['step']))
        self.window = QtGui.QComboBox()        
        self.window.addItem("Bartlett")
        self.window.addItem("Blackman")
        self.window.addItem("Boxcar")
        self.window.addItem("Hamming")
        self.window.addItem("Hann")
        self.window.addItem("Parzen")
        self.window.setCurrentIndex(4)

        range_layout = QtGui.QHBoxLayout()
        self.freq_min = QtGui.QLineEdit(str(self.defaults['freq_min']))
        self.freq_max = QtGui.QLineEdit(str(self.defaults['freq_max']))
        range_layout.addWidget(QtGui.QLabel("Frequency Range:"), 0)
        range_layout.addWidget(self.freq_min, 1)
        range_layout.addWidget(QtGui.QLabel(" - "), 2)
        range_layout.addWidget(self.freq_max, 3)
        range_layout.addWidget(QtGui.QLabel("Hz"), 4)

        group_box = QtGui.QGroupBox("Spectrogram Settings")
        layout = QtGui.QGridLayout()
        ledge = 0
        uedge = 0
        layout.addWidget(QtGui.QLabel("Window Size:"), uedge, ledge)
        layout.addWidget(self.win_size, uedge, ledge+1)
        layout.addWidget(QtGui.QLabel("samples"), uedge, ledge+2)
        layout.addWidget(QtGui.QLabel("Time Step:"), uedge+1, ledge)
        layout.addWidget(self.step, uedge+1, ledge+1)
        layout.addWidget(QtGui.QLabel("ms"), uedge+1, ledge+2)
        layout.addWidget(QtGui.QLabel("Window"), uedge+2, ledge)
        layout.addWidget(self.window, uedge+2, ledge+1)
        layout.addLayout(range_layout, uedge+3, ledge,1,3)
        layout.setColumnStretch(1,30)
        group_box.setLayout(layout)
    
        return group_box
