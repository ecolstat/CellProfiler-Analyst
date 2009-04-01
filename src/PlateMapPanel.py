from DataModel import *
from DBConnect import DBConnect
from Properties import Properties
import wx
import numpy as np
import pylab

abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
alphabet = [c for c in abc] + [c+c for c in abc]

# Well Shapes
ROUNDED_RECT = 'rounded_rect'
CIRCLE       = 'circle'
RECT         = 'rect'

all_well_shapes = ['rounded_rect', 'circle', 'rect']

class PlateMapPanel(wx.Panel):
    '''
    A Panel that displays a plate layout with wells that are colored by their
    data (in the range [0,1]).  The panel provides mechanisms for selection,
    color mapping, setting row & column labels, and reshaping the layout.
    '''
    
    def __init__(self, parent, data, shape=None, colormap='jet', 
                 wellshape=ROUNDED_RECT, **kwargs):
        wx.Panel.__init__(self, parent, **kwargs)
        self.hideLabels = False
        self.SetColorMap(colormap)
        self.wellshape = wellshape
        self.SetData(data, shape)
        self.selection = set([])
        self.row_labels = ['%2s'%c for c in alphabet[:self.data.shape[0]]]
        self.col_labels = ['%02d'%i for i in range(1,self.data.shape[1]+1)]
        self.Bind(wx.EVT_PAINT, self.OnPaint)
       
    
    def SetData(self, data, shape=None, range=None):
        '''
        data: An iterable containing numeric values. It's shape will be used
              to layout the plate unless overridden by the shape parameter
        shape: If passed, this will be used to reshape the data. (rows,cols)
        range: 2-tuple containing the min and max values that the data should
               be normalized to. Otherwise the min and max will be taken from
               the data (ignoring NaNs). 
        '''
        self.data = np.array(data).astype('float')
        
        if shape is not None:
            self.data = self.data.reshape(shape)

        self.range = range
        if self.range is None:
            self.range = (np.nanmin(self.data), np.nanmax(self.data))
        
        if self.range[0] == self.range[1]:
            self.data_normalized = self.data - self.range[0] + 0.5
        else:
            self.data_normalized = (self.data-self.range[0]) / (self.range[1]-self.range[0])
        
        self.Refresh()
        
    
    def SetColLabels(self, labels):
        assert len(labels) >= self.data.shape[1]
        self.col_labels = ['%2s'%c for c in labels]
        self.Refresh()
        
    
    def SetRowLabels(self, labels):
        assert len(labels) >= self.data.shape[0]
        self.row_labels = ['%2s'%c for c in labels]
        self.Refresh()
        
    
    def SetWellShape(self, wellshape):
        '''
        wellshape in PlatMapPanel.ROUNDED_RECT,
                     PlatMapPanel.CIRCLE,
                     PlatMapPanel.RECT
        '''
        self.wellshape = wellshape
        self.Refresh()
        
        
    def SetColorMap(self, map):
        ''' map: the name of a matplotlib.colors.LinearSegmentedColormap instance '''
        self.colormap = pylab.cm.get_cmap(map)
        self.Refresh()
        
    
    def SelectWell(self, well):
        ''' well: 2-tuple of integers indexing a well position (row,col)'''
        self.selection = set([well])
        self.Refresh()
        
        
    def ToggleSelected(self, well):
        ''' well: 2-tuple of integers indexing a well position (row,col)'''
        if well in self.selection:
            self.selection.remove(well)
        else:
            self.selection.add(well)
        self.Refresh()
        

    def GetWellAtCoord(self, x, y, format='tuple'):
        '''
        format: 'A01' or 'tuple'
        returns a 2 tuple of integers indexing a well position 
                or -1 if there is no well at the given position.
        '''
        r = min(self.Size[0]/(self.data.shape[1]+1.)/2.,
                self.Size[1]/(self.data.shape[0]+1.)/2.) - 0.5
        i = int((x-2-self.xo)/(r*2+1))
        j = int((y-2-self.yo)/(r*2+1))
        if 0<i<=self.data.shape[1] and 0<j<=self.data.shape[0]:
            if format=='A01':
                return '%s%02d'%(abc[j-1],i)
            elif format=='tuple':
                return (j-1,i-1)
        else:
            return -1


    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.Clear()
        dc.BeginDrawing()
        
        w_win, h_win = (float(self.Size[0]), float(self.Size[1]))
        cols_data, rows_data = (self.data.shape[1], self.data.shape[0])
        
        # calculate the well radius
        r = min(w_win/(cols_data+1.)/2.,
                h_win/(rows_data+1.)/2.) - 0.5
                
        # calculate start position to draw at so image is centered.
        w_data, h_data = ((cols_data+1)*2.*(r+0.5), (rows_data+1)*2.*(r+0.5))
        self.xo, self.yo = (0., 0.)
        if w_win/h_win < w_data/h_data:
            self.yo = (h_win-h_data)/2
        else:
            self.xo = (w_win-w_data)/2
            
        # Set font size to fit
        font = dc.GetFont()
        if r>6:
            font.SetPixelSize((r-2,(r-2)*2))
        else:
            font.SetPixelSize((3,6))
        dc.SetFont(font)
            

        py = self.yo
        i=0
        for y in range(rows_data+1):
            px = self.xo
            for x in range(cols_data+1):
                # Draw column headers
                if y==0 and x!=0:
                    dc.DrawText(self.col_labels[x-1], px+1, py+1)
                # Draw row headers
                elif y!=0 and x==0:
                    dc.DrawText(self.row_labels[y-1], px+1, py+1)
                # Draw wells
                elif y>0 and x>0:
                    if (y-1, x-1) in self.selection:
                        dc.SetPen(wx.Pen("BLACK",5))
                    else:
                        dc.SetPen(wx.Pen("BLACK",0.5))
                    color = np.array(self.colormap(self.data_normalized[y-1][x-1])[:3]) * 255
                    if np.isnan(self.data[y-1][x-1]):
                        dc.SetBrush(wx.Brush(color, style=wx.TRANSPARENT))
                    else:
                        dc.SetBrush(wx.Brush(color))
                    if self.wellshape == ROUNDED_RECT:
                        dc.DrawRoundedRectangle(px+1, py+1, r*2, r*2, r*0.75)
                    elif self.wellshape == CIRCLE:
                        dc.DrawCircle(px+r+1, py+r+1, r)
                    elif self.wellshape == RECT:
                        dc.DrawRectangle(px+1, py+1, r*2, r*2)
                    if np.isnan(self.data[y-1][x-1]):
                        dc.SetPen(wx.Pen("GRAY",1))
                        dc.DrawLine(px+3, py+3, px+r*2-2, py+r*2-2)
                        dc.DrawLine(px+3, py+r*2-2, px+r*2-2, py+3)    
                    i+=1
                px += 2*r+1
            py += 2*r+1
        dc.EndDrawing()
        return dc
            


if __name__ == "__main__":
    app = wx.PySimpleApp()
    
    # test plate map panel
    data = np.arange(384.) 
#    data = np.ones(384)
    data[100:102] = np.nan
    frame = wx.Frame(None, size=(600.,430.))
    p = PlateMapPanel(frame, data, shape=(16,24), wellshape='rect')
    frame.Show()
    
    app.MainLoop()
    
    
    