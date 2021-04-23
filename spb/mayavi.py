from spb.base_backend import MyBaseBackend
from mayavi import mlab
from IPython.core.display import display

# TODO
# 1. Implement save feature

class MayaviBackend(MyBaseBackend):
    """ A backend for plotting SymPy's symbolic expressions using Mayavi.

    Keyword Arguments
    =================

        bg_color : tuple
            A tuple of RGB values from 0 to 1 specifying the background color.
            Default to (0.22, 0.24, 0.29).
        
        use_cm : boolean
            If True, apply a color map to the meshes/surface. If False, solid
            colors will be used instead. Default to True.

    """
    # More colormaps at:
    # https://docs.enthought.com/mayavi/mayavi/mlab_changing_object_looks.html
    colormaps = ['jet', 'autumn', 'Spectral', 'CMRmap', 'YlGnBu',
          'spring', 'summer', 'coolwarm', 'viridis', 'winter']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._get_mode() == 0:
            mlab.init_notebook()
        
        size = (600, 400)
        if self.size:
            size = self.size
        self._fig = mlab.figure(
            size = size,
            bgcolor = self._kwargs.get("bg_color", (0.22, 0.24, 0.29))
        )
    
    def _process_series(self, series):
        mlab.clf(self._fig)

        cm = iter(self.colormaps)
        for i, s in enumerate(series):
            if s.is_3Dline:
                x, y, z = s.get_data()
                length = self._line_length(x, y, z, start=s.start, end=s.end)
                mlab.plot3d(x, y, z, length,
                    color = None if self._use_cm else next(self._iter_colorloop),
                    figure=self._fig,
                    tube_radius=0.05,
                    colormap=next(cm))
            elif s.is_3Dsurface:
                mlab.mesh(*s.get_data(),
                    color = None if self._use_cm else next(self._iter_colorloop),
                    figure = self._fig,
                    colormap = next(cm),
                    representation = "wireframe" if self._kwargs.get("wireframe", False) else "surface"
                )
            else:
                raise ValueError(
                    "Mayavi only support 3D plots."
                )
            
            if self.axis:
                mlab.axes(xlabel="", ylabel="", zlabel="",
                     x_axis_visibility=True, y_axis_visibility=True, z_axis_visibility=True)
                mlab.outline()
        
        xl = self.xlabel if self.xlabel else "x"
        yl = self.ylabel if self.ylabel else "y"
        zl = self.zlabel if self.zlabel else "z"
        mlab.orientation_axes(xlabel=xl, ylabel=yl, zlabel=zl)
        if self.title:
            mlab.title(self.title, figure=self._fig, size=0.5)

    def show(self):
        self._process_series(self._series)
        display(self._fig)
    
    def save(self, path, **kwargs):
        """ Save the current plot. Look at the following page to find out more
        keyword arguments to control the output file:
        https://docs.enthought.com/mayavi/mayavi/auto/mlab_figure.html#savefig


        Parameters
        ==========

            path : str
                File path with extension.
            
            kwargs : dict
                Optional backend-specific parameters.
        """
        mlab.savefig(
            path,
            figure = self._fig,
            size = kwargs.get("size", None),
            magnification = kwargs.get("magnification", "auto"),
        )
    
    def close(self):
        mlab.close(self._fig)

MB = MayaviBackend