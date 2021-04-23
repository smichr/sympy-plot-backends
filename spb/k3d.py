from spb.base_backend import MyBaseBackend
import k3d
import numpy as np
import warnings
from matplotlib.tri import Triangulation
from mayavi import mlab
from tvtk.api import tvtk

# TODO:
# 1. find a way to avoid using mlab since it is very slow to load
# 2. load the plot with menu minimized
# 3. how to clear the picture? The save command is going to add again the
#    objects, obtaining duplicates with different color maps.

class K3DBackend(MyBaseBackend):
    """ A backend for plotting SymPy's symbolic expressions using K3D-Jupyter.

    Keyword Arguments
    =================
        
        bg_color : int
            Packed RGB color of the plot background.
            Default to 0xFFFFFF (white).
        
        show_label : boolean
            Show/hide labels of the expressions. Default to False (labels not
            visible).
        
        use_cm : boolean
            If True, apply a color map to the meshes/surface. If False, solid
            colors will be used instead. Default to True.
        
        wireframe : boolean
            Visualize the wireframe lines instead of surface' colors.
            Default to False.
    """

    colormaps = [
        k3d.basic_color_maps.CoolWarm, k3d.basic_color_maps.Jet,
        k3d.basic_color_maps.BlackBodyRadiation, k3d.matplotlib_color_maps.Plasma,
        k3d.matplotlib_color_maps.Autumn, k3d.matplotlib_color_maps.Winter,
        k3d.paraview_color_maps.Nic_Edge, k3d.paraview_color_maps.Haze
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._get_mode() != 0:
            raise ValueError(
                    "Sorry, K3D backend only works within Jupyter Notebook")
        mlab.init_notebook()
        # this is necessary: suppose you do a plot with MayaviBackend. Then you
        # do a second plot with K3D. Without this line of code, the K3D data
        # will also be added to the previous Mayavi plot.
        mlab_fig = mlab.figure()

        self._fig = k3d.plot(
            grid_visible = self.axis,
            menu_visibility = True,
            background_color = self._kwargs.get("bg_color", 0xFFFFFF)
        )
        if (self.xscale == "log") or (self.yscale == "log"):
            warnings.warn("K3D-Jupyter doesn't support log scales. We will " +
                         "continue with linear scales.")
        self.plot_shown = False

    @staticmethod
    def _int_to_rgb(RGBint):
        """ Convert an integer number to an RGB tuple with components from 0 to
        255.

        https://stackoverflow.com/a/2262152/2329968
        """
        B =  RGBint & 255
        G = (RGBint >> 8) & 255
        R =   (RGBint >> 16) & 255
        return R, G, B
    
    @staticmethod
    def _rgb_to_int(RGB):
        """ Convert an RGB tuple to an integer number.

        https://stackoverflow.com/q/2262100/2329968
        """
        R, G, B = RGB
        return R * 256**2 + G * 256 + B
    
    def _convert_to_int(self, color):
        """ Convert the provided RGB tuple with values from 0 to 1 to an integer
        number.
        """
        color = [int(c * 255) for c in color]
        return self._rgb_to_int(color)

    def _process_series(self, series):
        # TODO: not working, it doesn't clear the previously drawn objects
        self._fig.object = []
        
        for s in series:
            if s.is_3Dline:
                x, y, z = s.get_data()
                vertices = np.vstack([x, y, z]).T.astype(np.float32)
                length = self._line_length(x, y, z, start=s.start, end=s.end)
                # keyword arguments for the line object
                a = dict(
                    width = 0.1,
                    name = s.label if self._kwargs.get("show_label", False) else None,
                    color = self._convert_to_int(next(self._iter_colorloop)),
                )
                if self._use_cm:
                    a["attribute"] = length,
                    a["color_map"] = next(self._iter_colormaps)
                    a["color_range"] = [s.start, s.end]
                line = k3d.line(vertices, **a)
                self._fig += line

            elif s.is_3Dsurface:
                x, y, z = s.get_data()
                x = x.astype(np.float32)
                y = y.astype(np.float32)
                z = z.astype(np.float32)
                # keyword arguments for the surface/mesh object
                a = dict(
                    name = s.label if self._kwargs.get("show_label", False) else None,
                    side = "double",
                    flat_shading = False,
                    wireframe = self._kwargs.get("wireframe", False),
                    color = self._convert_to_int(next(self._iter_colorloop)),
                )

                if s.is_parametric:
                    m = mlab.mesh(x, y, z)
                    actor = m.actor.actors[0]
                    polydata = tvtk.to_vtk(actor.mapper.input)
                    if self._use_cm:
                        a["color_map"] = next(self._iter_colormaps)
                        a["color_attribute"] = ["scalars", np.min(z), np.max(z)]
                    surf = k3d.vtk_poly_data(polydata, **a)
                else:
                    x = x.reshape(-1)
                    y = y.reshape(-1)
                    z = z.reshape(-1)
                    vertices = np.vstack([x, y, z])
                    indices = Triangulation(x, y).triangles.astype(np.uint32)
                    if self._use_cm:
                        a["color_map"] = next(self._iter_colormaps)
                        a["attribute"] = z
                    surf = k3d.mesh(vertices.T, indices, **a)
                    
                self._fig += surf
            else:
                raise ValueError(
                    "K3D-Jupyter only support 3D plots."
                )
        
        xl = self.xlabel if self.xlabel else "x"
        yl = self.ylabel if self.ylabel else "y"
        zl = self.zlabel if self.zlabel else "z"
        self._fig.axes = [xl, yl, zl]

        if self.title:
            self._fig += k3d.text2d(self.title, 
                 position=[0.025, 0.015], color=0, size=1, label_box=False)
    
    def show(self):
        self._process_series(self._series)
        self.plot_shown = True
        self._fig.display()
    
    def save(self, path, **kwargs):
        if not self.plot_shown:
            raise ValueError(
                "K3D-Jupyter requires the plot to be shown on the screen " + 
                "before saving it."
            )

        self._process_series(self._series)

        @self._fig.yield_screenshots
        def _func():
            self._fig.fetch_screenshot()
            screenshot = yield
            with open(path, 'wb') as f:
                f.write(screenshot)
        _func()

KB = K3DBackend