''' A parameters for arfview '''
import numpy as np
from PySide import QtGui


# time units: samples, s, ms
# window functions: hamming, hanning
plotpars = {
    'time-units': 's',
    'NFFT': 256,
    'window': np.hanning
    }


class ParameterWidget(QtGui.QWidget):
    pass

