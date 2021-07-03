from spb.defaults import cfg
from spb.backends.base_backend import Plot
from bokeh.plotting import figure, show
from bokeh.io import output_notebook
import bokeh.palettes as bp
from bokeh.io import curdoc
from bokeh.models import (
    LinearColorMapper, ColumnDataSource, MultiLine, ColorBar, Segment
)
from bokeh.models.tickers import FixedTicker
from bokeh.io import export_png, export_svg
import itertools
import colorcet as cc
import os
import numpy as np
from mergedeep import merge
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from spb.backends.utils import convert_colormap

def get_contour_data(X, Y, Z, get_source=True):
    """ Uses Matplotlib contours to create a data source to plot contour levels.

    Credit to: https://stackoverflow.com/a/37633519/2329968
    """
    cs = plt.contour(X, Y, Z, [0.])
    xs = []
    ys = []
    for isolevel in cs.collections:
        for path in isolevel.get_paths():
            v = path.vertices
            x = v[:, 0]
            y = v[:, 1]
            xs.append(x.tolist())
            ys.append(y.tolist())
    data = {'xs': xs, 'ys': ys}
    if not get_source:
        return data
    return ColumnDataSource(data=data)

def compute_streamlines(x, y, u, v, density=1.0):
    ''' Return streamlines of a vector flow.

    * x and y are 1d arrays defining an *evenly spaced* grid.
    * u and v are 2d arrays (shape [y,x]) giving velocities.
    * density controls the closeness of the streamlines.

    Credit: https://docs.bokeh.org/en/latest/docs/gallery/quiver.html
    '''

    # TODO: is it possible to further optimize this function?

    ## Set up some constants - size of the grid used.
    NGX = len(x)
    NGY = len(y)

    ## Constants used to convert between grid index coords and user coords.
    DX = x[1]-x[0]
    DY = y[1]-y[0]
    XOFF = x[0]
    YOFF = y[0]

    ## Now rescale velocity onto axes-coordinates
    u = u / (x[-1]-x[0])
    v = v / (y[-1]-y[0])
    speed = np.sqrt(u*u+v*v)
    ## s (path length) will now be in axes-coordinates, but we must
    ## rescale u for integrations.
    u *= NGX
    v *= NGY
    ## Now u and v in grid-coordinates.

    NBX = int(30*density)
    NBY = int(30*density)

    blank = np.zeros((NBY,NBX))

    bx_spacing = NGX/float(NBX-1)
    by_spacing = NGY/float(NBY-1)

    def blank_pos(xi, yi):
        return int((xi / bx_spacing) + 0.5), \
               int((yi / by_spacing) + 0.5)

    def value_at(a, xi, yi):
        if type(xi) == np.ndarray:
            x = xi.astype(int)
            y = yi.astype(int)
        else:
            x = int(xi)
            y = int(yi)
        a00 = a[y,x]
        a01 = a[y,x+1]
        a10 = a[y+1,x]
        a11 = a[y+1,x+1]
        xt = xi - x
        yt = yi - y
        a0 = a00*(1-xt) + a01*xt
        a1 = a10*(1-xt) + a11*xt
        return a0*(1-yt) + a1*yt

    def rk4_integrate(x0, y0):
        ## This function does RK4 forward and back trajectories from
        ## the initial conditions, with the odd 'blank array'
        ## termination conditions. TODO tidy the integration loops.

        def f(xi, yi):
            dt_ds = 1./value_at(speed, xi, yi)
            ui = value_at(u, xi, yi)
            vi = value_at(v, xi, yi)
            return ui*dt_ds, vi*dt_ds

        def g(xi, yi):
            dt_ds = 1./value_at(speed, xi, yi)
            ui = value_at(u, xi, yi)
            vi = value_at(v, xi, yi)
            return -ui*dt_ds, -vi*dt_ds

        check = lambda xi, yi: xi>=0 and xi<NGX-1 and yi>=0 and yi<NGY-1

        bx_changes = []
        by_changes = []

        ## Integrator function
        def rk4(x0, y0, f):
            ds = 0.01 #min(1./NGX, 1./NGY, 0.01)
            stotal = 0
            xi = x0
            yi = y0
            xb, yb = blank_pos(xi, yi)
            xf_traj = []
            yf_traj = []
            while check(xi, yi):
                # Time step. First save the point.
                xf_traj.append(xi)
                yf_traj.append(yi)
                # Next, advance one using RK4
                try:
                    k1x, k1y = f(xi, yi)
                    k2x, k2y = f(xi + .5*ds*k1x, yi + .5*ds*k1y)
                    k3x, k3y = f(xi + .5*ds*k2x, yi + .5*ds*k2y)
                    k4x, k4y = f(xi + ds*k3x, yi + ds*k3y)
                except IndexError:
                    # Out of the domain on one of the intermediate steps
                    break
                xi += ds*(k1x+2*k2x+2*k3x+k4x) / 6.
                yi += ds*(k1y+2*k2y+2*k3y+k4y) / 6.
                # Final position might be out of the domain
                if not check(xi, yi): break
                stotal += ds
                # Next, if s gets to thres, check blank.
                new_xb, new_yb = blank_pos(xi, yi)
                if new_xb != xb or new_yb != yb:
                    # New square, so check and colour. Quit if required.
                    if blank[new_yb,new_xb] == 0:
                        blank[new_yb,new_xb] = 1
                        bx_changes.append(new_xb)
                        by_changes.append(new_yb)
                        xb = new_xb
                        yb = new_yb
                    else:
                        break
                if stotal > 2:
                    break
            return stotal, xf_traj, yf_traj

        integrator = rk4

        sf, xf_traj, yf_traj = integrator(x0, y0, f)
        sb, xb_traj, yb_traj = integrator(x0, y0, g)
        stotal = sf + sb
        x_traj = xb_traj[::-1] + xf_traj[1:]
        y_traj = yb_traj[::-1] + yf_traj[1:]

        ## Tests to check length of traj. Remember, s in units of axes.
        if len(x_traj) < 1: return None
        if stotal > .2:
            initxb, inityb = blank_pos(x0, y0)
            blank[inityb, initxb] = 1
            return x_traj, y_traj
        else:
            for xb, yb in zip(bx_changes, by_changes):
                blank[yb, xb] = 0
            return None

    ## A quick function for integrating trajectories if blank==0.
    trajectories = []
    def traj(xb, yb):
        if xb < 0 or xb >= NBX or yb < 0 or yb >= NBY:
            return
        if blank[yb, xb] == 0:
            t = rk4_integrate(xb*bx_spacing, yb*by_spacing)
            if t is not None:
                trajectories.append(t)

    ## Now we build up the trajectory set. I've found it best to look
    ## for blank==0 along the edges first, and work inwards.
    for indent in range((max(NBX,NBY))//2):
        for xi in range(max(NBX,NBY)-2*indent):
            traj(xi+indent, indent)
            traj(xi+indent, NBY-1-indent)
            traj(indent, xi+indent)
            traj(NBX-1-indent, xi+indent)

    xs = [np.array(t[0])*DX+XOFF for t in trajectories]
    ys = [np.array(t[1])*DY+YOFF for t in trajectories]

    return xs, ys


class BokehBackend(Plot):
    """ A backend for plotting SymPy's symbolic expressions using Bokeh.
    Note: this implementation only implements 2D plots.

    Keyword Arguments
    =================

        colorbar_kw : dict
            A dictionary with keyword arguments to customize the colorbar.

        line_kw : dict
            A dictionary of keywords/values which is passed to Plotly's scatter
            functions to customize the appearance. Default to:
            ``line_kw = dict(line_width = 2)``
            Refer to this documentation page:
            https://docs.bokeh.org/en/latest/docs/reference/plotting.html?highlight=line#bokeh.plotting.Figure.line

        quiver_kw : dict
            A dictionary with keyword arguments to customize the quivers.
            Default to:
                ```dict(
                        scale = 1,
                        pivot = "mid",      # can be "mid", "tip" or "tail"
                        arrow_heads = True,  # show/hide arrow
                        line_width = 1
                    )
                ```

        stream_kw : dict
            A dictionary with keyword arguments to customize the streamlines.
            Default to: ``dict(line_width=2, line_alpha=0.8)``

        theme : str
            Set the theme. Default to "dark_minimal". Find more Bokeh themes at
            the following page:
            https://docs.bokeh.org/en/latest/docs/reference/themes.html

    Export
    ======

    In order to export the plots you will need to install the packages listed
    in the following page:
    https://docs.bokeh.org/en/latest/docs/user_guide/export.html

    At the time of writing this backend, geckodriver is not available to pip.
    Do a quick search on the web to find the appropriate installer.
    """

    _library = "bokeh"

    colorloop = bp.Category10[10]
    
    # to be used in parametric plots
    colormaps = [
        cc.fire, cc.isolum, cc.rainbow, cc.blues, cc.bmy, cc.colorwheel, cc.bgy
    ]

    # to be used in complex-parametric plots
    cyclic_colormaps = [
        cm.hsv, cm.twilight, cc.cyclic_mygbm_30_95_c78_s25 
    ]

    # TODO: better selection of discrete color maps for contour plots
    # DO I need this or can I just use colormaps?
    contour_colormaps = [
        bp.Plasma10, bp.Blues9, bp.Greys10
    ]

    quivers_colormaps = [
        cc.bmy, cc.bgy, cc.isolum, cc.fire
    ]

    def __new__(cls, *args, **kwargs):
        # Since Plot has its __new__ method, this will prevent infinite
        # recursion
        return object.__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self._get_mode() == 0:
            output_notebook(
                hide_banner=True
            )
        
        self._handles = dict()
        self._init_cyclers()

        curdoc().theme = kwargs.get("theme", cfg["bokeh"]["theme"])
        TOOLTIPS = [
            ("x", "$x"),
            ("y", "$y")
        ]

        if all([s.is_parametric for s in self.series]):
            # with parametric plots, also visualize the parameter
            TOOLTIPS += [("u", "@us")]
        if any([s.is_complex and s.is_domain_coloring for s in self.series]):
            # with complex domain coloring, shows the magnitude and phase
            # in the tooltip
            TOOLTIPS += [
                ("Abs", "@abs"),
                ("Arg", "@arg")
            ]

        sizing_mode = cfg["bokeh"]["sizing_mode"]
        if any(s.is_complex and s.is_domain_coloring for s in self.series):
            # for complex domain coloring
            sizing_mode = None

        self._fig = figure(
            title = self.title,
            x_axis_label = self.xlabel if self.xlabel else "x",
            y_axis_label = self.ylabel if self.ylabel else "y",
            sizing_mode = "fixed" if self.size else sizing_mode,
            width = int(self.size[0]) if self.size else 600,
            height = int(self.size[1]) if self.size else 400,
            x_axis_type = self.xscale,
            y_axis_type = self.yscale,
            x_range = self.xlim,
            y_range = self.ylim,
            tools = "pan,wheel_zoom,box_zoom,reset,hover,save",
            tooltips = TOOLTIPS,
            match_aspect = True if self.aspect == "equal" else False
        )
        self._fig.axis.visible = self.grid
        self._fig.grid.visible = self.grid
        
        self._process_series(self._series)
    
    def _init_cyclers(self):
        super()._init_cyclers()
        contour_colormaps = [convert_colormap(cm, self._library) for cm
                in self.contour_colormaps]
        self._ccm = itertools.cycle(contour_colormaps)
        quivers_colormaps = [convert_colormap(cm, self._library) for cm
                in self.quivers_colormaps]
        self._qcm = itertools.cycle(quivers_colormaps)

    def _process_series(self, series):
        self._init_cyclers()
        # clear figure. need to clear both the renderers as well as the
        # colorbars which are added to the right side.
        self._fig.renderers = []
        self._fig.right = []
        
        for i, s in enumerate(series):
            if s.is_2Dline:
                if s.is_parametric and self._use_cm:
                    x, y, param = s.get_data()
                    # Bokeh is not able to deal with None values. 
                    # Need to replace them with np.nan.
                    y = [t if (t is not None) else np.nan for t in y]
                    colormap = (next(self._cm) if not s.is_complex 
                            else next(self._cyccm))
                    ds, line, cb = self._create_gradient_line(x, y, param,
                            colormap, s.label)
                    self._fig.add_glyph(ds, line)
                    if self.legend:
                        self._handles[i] = cb
                        self._fig.add_layout(cb, "right")
                else:
                    if s.is_parametric:
                        x, y, param = s.get_data()
                        y = [t if (t is not None) else np.nan for t in y]
                        source = {"xs": x, "ys": y, "us": param}
                    else:
                        x, y = s.get_data()
                        x, y, modified = self._detect_poles(x, y)
                        if modified:
                            self._fig.y_range.start = self.ylim[0]
                            self._fig.y_range.end = self.ylim[1]
                        y = [t if (t is not None) else np.nan for t in y]
                        source = {"xs": x, "ys": y}

                    lkw = dict(
                        line_width = 2, legend_label = s.label,
                        color=next(self._cl)
                    )
                    line_kw = self._kwargs.get("line_kw", dict())
                    if not s.is_point:
                        self._fig.line("xs", "ys", source=source, 
                            **merge({}, lkw, line_kw))
                    else:
                        self._fig.dot("xs", "ys", source=source,
                            **merge({"size": 20}, lkw, line_kw))

            elif s.is_contour:
                x, y, z = s.get_data()
                x, y, zz = [t.flatten() for t in [x, y, z]]
                minx, miny, minz = min(x), min(y), min(zz)
                maxx, maxy, maxz = max(x), max(y), max(zz)

                cm = next(self._ccm)
                self._fig.image(image=[z], x=minx, y=miny,
                        dw=abs(maxx - minx), dh=abs(maxy - miny),
                        palette=cm)
                
                colormapper = LinearColorMapper(palette=cm, low=minz, high=maxz)
                # default options
                cbkw = dict(width = 8)
                # user defined options
                colorbar_kw = self._kwargs.get("colorbar_kw", dict())
                colorbar = ColorBar(color_mapper=colormapper, title=s.label,
                    **merge({}, cbkw, colorbar_kw))
                self._fig.add_layout(colorbar, 'right')
                self._handles[i] = colorbar

            elif s.is_implicit:
                points = s.get_data()
                # TODO: add color to the legend
                if len(points) == 2:
                    # interval math plotting
                    x, y, pixels = self._get_pixels(s, points[0])
                    x, y = x.flatten(), y.flatten()
                    cm = ["#00000000", next(self._cl)]
                    self._fig.image(image=[pixels], x=min(x), y=min(y),
                        dw=abs(max(x) - min(x)), dh=abs(max(y) - min(y)),
                        palette=cm, legend_label=s.label)
                else:
                    x, y, z, ones, plot_type = points
                    if plot_type == "contour":
                        source = get_contour_data(x, y, z)
                        lkw = dict(
                            line_color = next(self._cl),
                            line_width = 2,
                            source = source,
                            legend_label = s.label
                        )
                        line_kw = self._kwargs.get("line_kw", dict())
                        self._fig.multi_line('xs', 'ys', 
                            **merge({}, lkw, line_kw))
                    else:
                        cm = ["#00000000", next(self._cl)]
                        self._fig.image(image=[ones], x=min(x), y=min(y),
                            dw=abs(max(x) - min(x)), dh=abs(max(y) - min(y)),
                            palette=cm, legend_label=s.label)

            elif s.is_2Dvector:
                streamlines = self._kwargs.get("streamlines", False)
                if streamlines:
                    x, y, u, v = s.get_data()
                    sqk = dict(color=next(self._cl), line_width=2, line_alpha=0.8)
                    stream_kw = self._kwargs.get("stream_kw", dict())
                    density = stream_kw.pop("density", 2)
                    xs, ys = compute_streamlines(x[0, :], y[:, 0], u, v, density=density)
                    self._fig.multi_line(xs, ys, **merge({}, sqk, stream_kw))
                else:
                    x, y, u, v = s.get_data()
                    quiver_kw = self._kwargs.get("quiver_kw", dict())
                    data, quiver_kw = self._get_quivers_data(x, y, u, v, **quiver_kw)
                    mag = data["magnitude"]
                    
                    color_mapper = LinearColorMapper(palette=next(self._qcm), 
                        low=min(mag), high=max(mag))
                    is_contour = (True if ("scalar" not in self._kwargs.keys()) else
                        (False if not self._kwargs["scalar"] else True))
                    line_color = ({'field': 'magnitude', 'transform': color_mapper}
                        if not is_contour else next(self._cl))
                    source = ColumnDataSource(data=data)
                    # default quivers options
                    qkw = dict(line_color=line_color, line_width=1, name=s.label)
                    glyph = Segment(x0="x0", y0="y0", x1="x1", y1="y1",
                        **merge({}, qkw, quiver_kw))
                    self._fig.add_glyph(source, glyph)

            elif s.is_complex and s.is_domain_coloring:
                x, y, magn_angle, img, colors = s.get_data()
                img = self._get_img(img)

                source = ColumnDataSource({
                    "image": [img],
                    "abs": [magn_angle[:, :, 0]],
                    "arg": [magn_angle[:, :, 1]]
                })

                self._fig.image_rgba(source=source, x=x.min(), y=y.min(),
                        dw=x.max() - x.min(), dh=y.max() - y.min())
                
                if colors is not None:
                    # chroma/phase-colorbar
                    cm1 = LinearColorMapper(palette=[tuple(c) for c in colors], 
                            low=-self.pi, high=self.pi)
                    ticks = [-self.pi, -self.pi/2 , 0, self.pi/2, self.pi]
                    labels = ["-π", "-π / 2", "0", "π / 2", "π"]
                    colorbar1 = ColorBar(color_mapper=cm1, title="Argument",
                        ticker = FixedTicker(ticks = ticks),
                        major_label_overrides = {k: v for k, v in zip(ticks, labels)})
                    self._fig.add_layout(colorbar1, 'right')

                if s.coloring == "f":
                    # lightness/magnitude-colorbar
                    cm2 = LinearColorMapper(palette=bp.gray(100), low=0, high=1)
                    colorbar2 = ColorBar(color_mapper=cm2, title="Magnitude",
                        ticker = FixedTicker(ticks = [0, 1]),
                        major_label_overrides = {0: "0", 1: "∞"})
                    self._fig.add_layout(colorbar2, 'right')

            else:
                raise NotImplementedError(
                    "{} is not supported by {}\n".format(type(s), type(self).__name__) +
                    "Bokeh only supports 2D plots."
                )

        if len(self._fig.legend) > 0:
            self._fig.legend.visible = self.legend
            # interactive legend
            self._fig.legend.click_policy = "hide"
            self._fig.add_layout(self._fig.legend[0], 'right')
    
    def _get_img(self, img):
        new_img = np.zeros(img.shape[:2], dtype=np.uint32)
        pixel = new_img.view(dtype=np.uint8).reshape((*img.shape[:2], 4))
        for i in range(img.shape[1]):
            for j in range(img.shape[0]):
                pixel[j, i] = [*img[j, i], 255]
        return new_img

    def _get_segments(self, x, y, u):
        # MultiLine works with line segments, not with line points! :|
        xs = [x[i-1:i+1] for i in range(1, len(x))]
        ys = [y[i-1:i+1] for i in range(1, len(y))]
        # TODO: let n be the number of points. Then, the number of segments will
        # be (n - 1). Therefore, we remove one parameter. If n is sufficiently
        # high, there shouldn't be any noticeable problem in the visualization.
        us = u[:-1]
        return xs, ys, us

    def _create_gradient_line(self, x, y, u, colormap, name):
        xs, ys, us = self._get_segments(x, y, u)
        color_mapper = LinearColorMapper(palette = colormap, 
            low = min(us), high = max(us))
        data_source = ColumnDataSource(dict(xs = xs, ys = ys, us = us))

        lkw = dict(
            line_width = 2, name = name,
            line_color = {'field': 'us', 'transform': color_mapper}
        )
        line_kw = self._kwargs.get("line_kw", dict())
        glyph = MultiLine(xs="xs", ys="ys", **merge({}, lkw, line_kw))
        # default options
        cbkw = dict(width = 8)
        # user defined options
        colorbar_kw = self._kwargs.get("colorbar_kw", dict())
        colorbar = ColorBar(color_mapper=color_mapper, title=name,
            **merge({}, cbkw, colorbar_kw))
        return data_source, glyph, colorbar

    def _update_interactive(self, params):
        rend = self.fig.renderers
        
        for i, s in enumerate(self.series):
            if s.is_interactive:
                self.series[i].update_data(params)
                
                if s.is_2Dline and s.is_parametric and self._use_cm:
                    x, y, param = self.series[i].get_data()
                    xs, ys, us = self._get_segments(x, y, param)
                    rend[i].data_source.data.update(
                        {'xs': xs, 'ys': ys, 'us': us})
                    if i in self._handles.keys():
                        cb = self._handles[i]
                        cb.color_mapper.update(low = min(us), high = max(us))

                elif s.is_2Dline:
                    if s.is_parametric:
                        x, y, param = self.series[i].get_data()
                        source = {"xs": x, "ys": y, "us": param}
                    else:
                        x, y = self.series[i].get_data()
                        x, y, _ = self._detect_poles(x, y)
                        source = {"xs": x, "ys": y}
                    rend[i].data_source.data.update(source)

                elif s.is_contour:
                    x, y, z = s.get_data()
                    cb = self._handles[i]
                    rend[i].data_source.data.update({"image": [z]})
                    zz = z.flatten()
                    # TODO: as of Bokeh 2.3.2, the following line going to update
                    # the values of the color mapper, but the redraw is not 
                    # applied, hence there is an error in the visualization.
                    # Keep track of the following issue:
                    # https://github.com/bokeh/bokeh/issues/11116
                    cb.color_mapper.update(low = min(zz), high=max(zz))
                
                elif s.is_implicit:
                    points = s.get_data()
                    if len(points) == 2:
                        raise NotImplementedError
                    else:
                        x, y, z, ones, plot_type = points
                        if plot_type == "contour":
                            data = get_contour_data(x, y, z, False)
                            # TODO: for some unkown reason, this is not updating!
                            rend[i].data_source.data.update(data)
                        else:
                            source = {"image": [ones]}
                            rend[i].data_source.data.update(source)

                elif s.is_2Dvector:
                    x, y, u, v = s.get_data()
                    streamlines = self._kwargs.get("streamlines", False)
                    if streamlines:
                        sqk = dict(color=next(self._cl), line_width=2, 
                            line_alpha=0.8)
                        stream_kw = self._kwargs.get("stream_kw", dict())
                        density = stream_kw.pop("density", 2)
                        xs, ys = compute_streamlines(x[0, :], y[:, 0], u, v, 
                            density=density)
                        rend[i].data_source.data.update({'xs': xs, 'ys': ys})
                    else:
                        quiver_kw = self._kwargs.get("quiver_kw", dict())
                        data, quiver_kw = self._get_quivers_data(x, y, u, v, 
                            **quiver_kw)
                        mag = data["magnitude"]
                        color_mapper = LinearColorMapper(
                            palette=self.quivers_colormaps[i], 
                            low=min(mag), high=max(mag))
                        line_color = quiver_kw.get("line_color",
                            {'field': 'magnitude', 'transform': color_mapper})
                        rend[i].data_source.data.update(data)
                        rend[i].glyph.line_color = line_color

                elif s.is_complex and s.is_domain_coloring:
                    # TODO: for some unkown reason, domain_coloring and 
                    # interactive plot don't like each other...
                    x, y, magn_angle, img, _ = s.get_data()
                    img = self._get_img(img)
                    source = {
                        "image": [img],
                        "abs": [magn_angle[:, :, 0]],
                        "arg": [magn_angle[:, :, 1]]
                    }
                    rend[i].data_source.data.update(source)

    def save(self, path, **kwargs):
        self._process_series(self._series)
        ext = os.path.splitext(path)[1]
        if ext == ".svg":
            self._fig.output_backend = "svg"
            export_svg(self.fig, filename=path)
        else:
            if ext == "":
                path += ".png"
            self._fig.output_backend = "canvas"
            export_png(self._fig, filename=path)
    
    def show(self):
        self._process_series(self._series)
        show(self._fig)
    
    def _get_quivers_data(self, xs, ys, u, v, **quiver_kw):
        """ Compute the segments coordinates to plot quivers.
        
        Parameters
        ==========
            xs : np.ndarray
                A 2D numpy array representing the discretization in the
                x-coordinate
            
            ys : np.ndarray
                A 2D numpy array representing the discretization in the
                y-coordinate
            
            u : np.ndarray
                A 2D numpy array representing the x-component of the vector
            
            v : np.ndarray
                A 2D numpy array representing the x-component of the vector
            
            kwargs : dict, optional
                An optional
        
        Returns
        =======
            data: dict
                A dictionary suitable to create a data source to be used with
                Bokeh's Segment.
            
            quiver_kw : dict
                A dictionary containing keywords to customize the appearance
                of Bokeh's Segment glyph
        """
        scale = quiver_kw.pop("scale", 1.0)
        pivot = quiver_kw.pop("pivot", "mid")
        arrow_heads = quiver_kw.pop("arrow_heads", True)
        
        xs, ys, u, v = [t.flatten() for t in [xs, ys, u, v]]
        
        magnitude = np.sqrt(u**2 + v**2)
        rads = np.arctan2(v, u)
        lens = magnitude / max(magnitude) * scale

        # Compute segments and arrowheads
        # Compute offset depending on pivot option
        xoffsets = np.cos(rads) * lens / 2.
        yoffsets = np.sin(rads) * lens / 2.
        if pivot == 'mid':
            nxoff, pxoff = xoffsets, xoffsets
            nyoff, pyoff = yoffsets, yoffsets
        elif pivot == 'tip':
            nxoff, pxoff = 0, xoffsets*2
            nyoff, pyoff = 0, yoffsets*2
        elif pivot == 'tail':
            nxoff, pxoff = xoffsets*2, 0
            nyoff, pyoff = yoffsets*2, 0
        x0s, x1s = (xs + nxoff, xs - pxoff)
        y0s, y1s = (ys + nyoff, ys - pyoff)

        if arrow_heads:
            arrow_len = (lens/4.)
            xa1s = x0s - np.cos(rads+np.pi/4)*arrow_len
            ya1s = y0s - np.sin(rads+np.pi/4)*arrow_len
            xa2s = x0s - np.cos(rads-np.pi/4)*arrow_len
            ya2s = y0s - np.sin(rads-np.pi/4)*arrow_len
            x0s = np.tile(x0s, 3)
            x1s = np.concatenate([x1s, xa1s, xa2s])
            y0s = np.tile(y0s, 3)
            y1s = np.concatenate([y1s, ya1s, ya2s])

        data = {'x0': x0s, 'x1': x1s, 'y0': y0s, 'y1': y1s,
            'magnitude': np.tile(magnitude, 3)}

        return data, quiver_kw

BB = BokehBackend
