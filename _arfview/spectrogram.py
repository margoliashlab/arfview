import pyqtgraph as pg
import numpy as np
import scipy.signal
import libtfr
import h5py
from PySide import QtCore

class spectrogram(pg.PlotItem):
    """pyqtgraph.PlotItem that plots a spectrogram of the data in an arf dataset based on the
    settings in the settings panel"""
    
    selection_made = QtCore.Signal(pg.PlotItem)

    def __init__(self, dataset, t_step_ms=1, win_size=512, window_name='Hann', freq_min=0, 
                 freq_max=10000, *args, **kwargs):
        super(spectrogram, self).__init__(*args, **kwargs)
        self.dataset = dataset
        self.selection = None #contains pg.LinearRegionItem representing selection if not None
                #getting spectrogram settings
        sr = float(dataset.attrs['sampling_rate'])
        t_step = int(float(t_step_ms) * sr/1000.)  #time step in samples    

        if window_name == "Hann":
            window = scipy.signal.hann(win_size)
        elif window_name == "Bartlett":
            window = scipy.signal.bartlett(win_size)
        elif window_name == "Blackman":
            window = scipy.signal.blackman(win_size)
        elif window_name == "Boxcar":
            window = scipy.signal.boxcar(win_size)
        elif window_name == "Hamming":
            window = scipy.signal.hamming(win_size)
        elif window_name == "Parzen":
            window = scipy.signal.parzen(win_size)

        #computing and interpolating image
        Pxx = libtfr.stft(dataset,w=window,step=t_step)
        Pxx[Pxx==0] = np.min(Pxx[Pxx!=0]) #ensures that log won't give -inf
        spec = np.log(Pxx.T)
        res_factor = 1.0 #factor by which resolution is increased
        # spec = interpolate_spectrogram(spec, res_factor=res_factor)
        #making color lookup table
        pos = np.linspace(0,1,6)
        color = np.array([[0,0,255,255],[0,255,255,255],[0,255,0,255],
                          [255,255,0,255],[255,0,0,255],[100,0,0,255]], dtype=np.ubyte)
        color_map = pg.ColorMap(pos,color)
        lut = color_map.getLookupTable(0.0,1.0,256)
        self.img = pg.ImageItem(spec,lut=lut)
        #img.setLevels((-5, 10))

        self.addItem(self.img)
        image_scale = t_step/sr/res_factor
        self.img.setScale(image_scale)
        df = sr/float(win_size)
        plot_scale = df/res_factor/image_scale
        self.getAxis('left').setScale(plot_scale)
        xmax = float(dataset.size)/dataset.attrs['sampling_rate']
        self.setXRange(0, xmax)
        self.setYRange(freq_min/plot_scale, freq_max/plot_scale)
        self.setMouseEnabled(x=True, y=False)
        self.win_size = win_size #saving values for export selection function
        self.t_step = t_step 

 #       vb = self.getViewBox()
#        vb.sigXRangeChanged.connect(self.get)  

    @classmethod
    def fromSettingsPanel(cls, dataset, settings_panel, *args, **kwargs):
        '''Creates spectrogram using arguments specified by a 
        settings_panel object'''

        win_size_text = settings_panel.win_size.text()
        t_step_text = settings_panel.step.text()
        min_text = settings_panel.freq_min.text()
        max_text = settings_panel.freq_max.text()

        if win_size_text:
            win_size = int(float(win_size_text))
        else:
            win_size = settings_panel.defaults['win_size']
            settings_panel.win_size.setText(str(win_size))
        if t_step_text:
            t_step = int(float(t_step_text))
        else:
            t_step = settings_panel.defaults['step']
            settings_panel.win_size.setText(str(int(tstep*1000)))
        if min_text:
            freq_min = int(min_text)
        else:
            freq_min = settings_panel.defaults['freq_min']
            settings_panel.freq_min.setText(str(freq_min))
        if max_text:
            freq_max = int(max_text)
        else:
            freq_max = settings_panel.defaults['freq_max']
            settings_panel.freq_max.setText(str(freq_max))                                     

        window_name = settings_panel.window.currentText()                

        return cls(dataset, t_step_ms=t_step, window_name=window_name, 
                   win_size=win_size, freq_min=freq_min, 
                   freq_max=freq_max,*args, **kwargs)
        
    def removeSelection(self):
        '''Sets selection to None and removes it from display'''
        if self.selection is not None:
            self.removeItem(self.selection)
            self.selection = None

    def mouseDoubleClickEvent(self, event):
        '''Double click to select portions of spectrogram'''
        pos = event.scenePos()
        vb = self.getViewBox()
        x = vb.mapSceneToView(pos).x()
        if self.selection is None:
            self.selection = pg.LinearRegionItem([x, x])
            self.addItem(self.selection)
            self.selection_made.emit(self)
        else:
            bounds = list(self.selection.getRegion())
            idx_change = np.argmin(np.abs(x-np.array(self.selection.getRegion())))
            bounds[idx_change] = x
            self.selection.setRegion(bounds)
            
        