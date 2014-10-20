import pyqtgraph as pg
import numpy as np

# class rasterTick(pg.GraphItem):
#     def __init__(self, toe, trial_number):
#         super(rasterTick,self).__init__()
#         x = (toe, toe)
#         y = (trial_number - .5, trial_number + .5)
#         self.setData(x, y)

class rasterPlot(pg.PlotItem):
    """Plots a raster plot from a list of array-like objects containing event times.
    All the tick marks together are a single object.  This is accomplished using a pyqtgraph.GraphItem,
    which is used to plot graph theory graphs"""
    def __init__(self, toes, *args, **kwargs):
        super(rasterPlot, self).__init__(*args,**kwargs)
        # if not isinstance(toes, list) or toes.ndim > 1:
        #     raise ValueError('Event times must be given as ndarray of dimension 2 or less')

        n_toes = sum(len(t) for t in toes)
        pos = np.zeros((n_toes*2,2)) #array of vertex positions
        k=0
        for trial_idx, trial_toes in enumerate(toes):
            pos[k:k+len(trial_toes)*2,0] = trial_toes.repeat(2)
            pos[k:k+len(trial_toes)*2:2,1] = 1 + trial_idx - .5
            pos[k+1:k+len(trial_toes)*2:2,1] = 1 + trial_idx + .5
            k+=len(trial_toes)*2

        adj = np.arange(n_toes*2).reshape(n_toes,2) #connections of graph
        self.graph_item = pg.GraphItem(pos=pos,adj=adj,size=0)
        self.addItem(self.graph_item)
        self.setMouseEnabled(y=False)
    # def add_trial(self, toes):
    #     self.ntrials += 1
    #     for idx, t in enumerate(toes):
    #         self.plot([t,t], [self.ntrials-.5, self.ntrials+.5])
       
        

