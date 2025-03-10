from sympy.core.containers import Tuple
from sympy.functions.elementary.miscellaneous import sqrt
from sympy.functions.elementary.complexes import re, im, arg
from sympy.core.expr import Expr
from sympy.core.symbol import Dummy, symbols
from sympy.core.numbers import I
from spb.defaults import cfg
import warnings

from spb.series import (
    LineOver1DRangeSeries,
    ComplexSurfaceBaseSeries,
    ComplexInteractiveBaseSeries,
    ComplexPointSeries,
    ComplexPointInteractiveSeries,
    _set_discretization_points,
    SurfaceOver2DRangeSeries,
    InteractiveSeries
)
from spb.vectors import plot_vector
from spb.utils import _plot_sympify, _check_arguments, _is_range
from spb.defaults import TWO_D_B, THREE_D_B

# NOTE:
# * `abs` refers to the absolute value;
# * `arg` refers to the argument;
# * `absarg` refers to the absolute value and argument, which will be used to
#   create "domain coloring" plots.


def _build_series(*args, interactive=False, **kwargs):
    series = []
    # apply the user-specified function to the expression
    #   keys: the user specified keyword arguments
    #   values: [function, label]
    # NOTE: the label is going to wrap the string representation of the
    # expression. This design choice precludes the ability of setting latex
    # labels, but this is not a problem as the user has the ability to set
    # a custom alias for the function to be plotted. The main motivation for
    # this choice is that whenever re() or im() is applied to an expression, it
    # might gets evaluated, resulting in a different expression (something
    # that the user might not recognize). This design prevents that.
    mapping = {
        "real": [lambda t: re(t), "Re(%s)"],
        "imag": [lambda t: im(t), "Im(%s)"],
        "abs": [lambda t: sqrt(re(t)**2 + im(t)**2), "Abs(%s)"],
        # NOTE: absarg is used to plot the absolute value colored by the
        # argument. The colorbar indicates the argument, hence the following
        # label is "Arg"
        "absarg": [lambda t: t, "Arg(%s)"],
        "arg": [lambda t: arg(t), "Arg(%s)"],
    }
    # option to be used with lambdify with complex functions
    kwargs.setdefault("modules", cfg["complex"]["modules"])

    if all([hasattr(a, "is_complex") and a.is_complex for a in args]):
        # args is a list of complex numbers
        cls = ComplexPointSeries if not interactive else ComplexPointInteractiveSeries
        for a in args:
            # series.append(cls([a], None, str(a), **kwargs))
            series.append(cls([a], str(a), **kwargs))
    elif (
        (len(args) > 0)
        and all([isinstance(a, (list, tuple, Tuple)) for a in args])
        and all([len(a) > 0 for a in args])
        and all([isinstance(a[0], (list, tuple, Tuple)) for a in args])
    ):
        # args is a list of tuples of the form (list, label) where list
        # contains complex points
        cls = ComplexPointSeries if not interactive else ComplexPointInteractiveSeries
        for a in args:
            series.append(cls(a[0], a[-1], **kwargs))
    elif (
        (len(args) > 0)
        and all([isinstance(a, (list, tuple, Tuple)) for a in args])
        and all([all([isinstance(t, Expr) and t.is_complex for t in a]) for a in args])
    ):
        # args is a list of lists
        cls = ComplexPointSeries if not interactive else ComplexPointInteractiveSeries
        for a in args:
            series.append(cls(a, "", **kwargs))
    else:
        new_args = []

        def add_series(argument):
            nexpr, npar = 1, 1
            if len([b for b in argument if _is_range(b)]) > 1:
                # function of two variables
                npar = 2
            new_args.append(_check_arguments([argument], nexpr, npar)[0])

        if all(isinstance(a, (list, tuple, Tuple)) for a in args):
            # deals with the case:
            # plot_complex((expr1, "name1"), (expr2, "name2"), range)
            # Modify the tuples (expr, "name") to (expr, range, "name")
            npar = len([b for b in args if _is_range(b)])
            tmp = []
            for i in range(len(args) - npar):
                a = args[i]
                tmp.append(a)
                if len(a) == 2 and isinstance(a[-1], str):
                    tmp[i] = (a[0], *args[len(args) - npar:], a[-1])

            # plotting multiple expressions
            for a in tmp:
                add_series(a)
        else:
            # plotting a single expression
            add_series(args)


        params = kwargs.get("params", dict())
        for a in new_args:
            expr, ranges, label = a[0], a[1:-1], a[-1]

            # From now on we are dealing with a function of one variable.
            # ranges need to contain complex numbers
            ranges = list(ranges)
            for i, r in enumerate(ranges):
                ranges[i] = (r[0], complex(r[1]), complex(r[2]))

            # there are expressions that are complex, but they do not represent
            # complex points, for example `exp(I * phi)`. If it is a complex
            # point, it won't have any free symbols.
            fs = expr.free_symbols
            fs = fs.difference(set(params.keys()))
            if expr.is_complex and (len(fs) == 0):
                # complex number with its own label
                cls = ComplexPointSeries if not interactive else ComplexPointInteractiveSeries
                series.append(cls([expr], label, **kwargs))

            else:
                # NOTE: as a design choice, a complex function will create one
                # or more data series, depending on the keyword arguments
                # (one for the real part, one for the imaginary part, etc.).
                # This is undoubtely inefficient as we must evaluate the same
                # expression multiple times. On the other hand, it allows to
                # maintain a one-to-one correspondance between Plot.series
                # and backend.data, making it easier to work with iplot
                # (backend._update_interactive).

                kw = kwargs.copy()
                absarg = kw.pop("absarg", True)
                real = kw.pop("real", False)
                imag = kw.pop("imag", False)
                _abs = kw.pop("abs", False)
                _arg = kw.pop("arg", False)

                if ranges[0][1].imag == ranges[0][2].imag:
                    # dealing with lines
                    def add_series(flag, key):
                        if flag:
                            kw2 = kw.copy()
                            kw2[key] = True
                            f, lbl_wrapper = mapping[key]
                            if not interactive:
                                series.append(LineOver1DRangeSeries(f(expr), *ranges, lbl_wrapper % label, **kw2))
                            else:
                                series.append(InteractiveSeries([f(expr)], ranges, lbl_wrapper % label, **kw2))

                else:
                    # 2D domain coloring or 3D plots
                    cls = ComplexSurfaceBaseSeries if not interactive else ComplexInteractiveBaseSeries
                    kw.setdefault("coloring", cfg["complex"]["coloring"])

                    def add_series(flag, key):
                        if flag:
                            kw2 = kw.copy()
                            kw2[key] = True
                            f, lbl_wrapper = mapping[key]
                            if key == "absarg":
                                lbl_wrapper = "%s"
                            series.append(cls(f(expr), *ranges, lbl_wrapper % label, **kw2))

                add_series(absarg, "absarg")
                add_series(real, "real")
                add_series(imag, "imag")
                add_series(_abs, "abs")
                add_series(_arg, "arg")

    return series


def _plot_complex(*args, show=True, **kwargs):
    """Create the series and setup the backend."""
    args = _plot_sympify(args)
    kwargs = _set_discretization_points(kwargs, ComplexSurfaceBaseSeries)

    series = _build_series(*args, **kwargs)
    if len(series) == 0:
        warnings.warn("No series found. Check your keyword arguments.")

    if any(s.is_3Dsurface for s in series):
        Backend = kwargs.pop("backend", THREE_D_B)
    else:
        Backend = kwargs.pop("backend", TWO_D_B)

    if all(
        isinstance(s, (SurfaceOver2DRangeSeries, InteractiveSeries)) for s in series
    ):
        # function of 2 variables
        if kwargs.get("xlabel", None) is None:
            if len(series) > 0:
                kwargs["xlabel"] = str(series[0].var_x)
        if kwargs.get("ylabel", None) is None:
            if len(series) > 0:
                kwargs["ylabel"] = str(series[0].var_y)
        # do not set anything for zlabel since it could be f(x,y) or
        # abs(f(x, y)) or something else
    elif all(not s.is_parametric for s in series):
        # when plotting real/imaginary or domain coloring/3D plots, the
        # horizontal axis is the real, the vertical axis is the imaginary
        if kwargs.get("xlabel", None) is None:
            kwargs["xlabel"] = "Re"
        if kwargs.get("ylabel", None) is None:
            kwargs["ylabel"] = "Im"
        if kwargs.get("zlabel", None) is None:
            kwargs["zlabel"] = "Abs"
    else:
        if kwargs.get("xlabel", None) is None:
            kwargs["xlabel"] = "Real"
        if kwargs.get("ylabel", None) is None:
            kwargs["ylabel"] = "Abs"

    if (kwargs.get("aspect", None) is None) and any(
        (s.is_complex and s.is_domain_coloring) or s.is_point for s in series
    ):
        # set aspect equal for 2D domain coloring or complex points
        kwargs.setdefault("aspect", "equal")

    p = Backend(*series, **kwargs)
    if show:
        p.show()
    return p


def plot_real_imag(*args, **kwargs):
    """Plot the real part, the imaginary parts, the absolute value and the
    argument of a complex function. By default, only the real and imaginary
    parts will be plotted. Use keyword argument to be more specific.
    By default, the aspect ratio of the plot is set to `aspect="equal"`.

    Depending on the provided expression, this function will produce different
    types of plots:

    1. line plot over the reals.
    2. surface plot over the complex plane if `threed=True`.
    3. contour plot over the complex plane if `threed=False`.

    Typical usage examples are in the followings:

    - Plotting a single expression with a single range.
        `plot_real_imag(expr, range, **kwargs)`
    - Plotting a single expression with the default range (-10, 10).
        `plot_real_imag(expr, **kwargs)`
    - Plotting multiple expressions with a single range.
        `plot_real_imag(expr1, expr2, ..., range, **kwargs)`
    - Plotting multiple expressions with multiple ranges.
        `plot_real_imag((expr1, range1), (expr2, range2), ..., **kwargs)`
    - Plotting multiple expressions with multiple ranges and custom labels.
        `plot_real_imag((expr1, range1, label1), (expr2, range2, label2), ..., **kwargs)`

    Parameters
    ==========
    args :
        expr : Expr
            Represent the complex function to be plotted.

        range : 3-element tuple
            Denotes the range of the variables. For example:

            * `(z, -5, 5)`: plot a line over the reals from point `-5` to
              `5`
            * `(z, -5 + 2*I, 5 + 2*I)`: plot a line from complex point
              `(-5 + 2*I)` to `(5 + 2 * I)`. Note the same imaginary part
              for the start/end point. Also note that we can specify the
              ranges by using standard Python complex numbers, for example
              `(z, -5+2j, 5+2j)`.
            * `(z, -5 - 3*I, 5 + 3*I)`: surface or contour plot of the
              complex function over the specified domain.

        label : str, optional
            The name of the complex function to be eventually shown on the
            legend. If none is provided, the string representation of the
            function will be used.

    abs : boolean, optional
        If True, plot the modulus of the complex function. Default to True.

    adaptive : bool, optional
        Attempt to create line plots by using an adaptive algorithm.
        Image and surface plots do not use an adaptive algorithm.
        Default to True.
        Use `adaptive_goal` and `loss_fn` to further customize the output.

    adaptive_goal : callable, int, float or None
        Controls the "smoothness" of the evaluation. Possible values:

        * `None` (default):  it will use the following goal:
          `lambda l: l.loss() < 0.01`
        * number (int or float). The lower the number, the more
          evaluation points. This number will be used in the following goal:
          `lambda l: l.loss() < number`
        * callable: a function requiring one input element, the learner. It
          must return a float number. Refer to [#fn0]_ for more information.

    arg : boolean, optional
        If True, plot the argument of the complex function. Default to True.

    aspect : (float, float) or str, optional
        Set the aspect ratio of the plot. The value depends on the backend
        being used. Read that backend's documentation to find out the
        possible values.

    backend : Plot, optional
        A subclass of `Plot`, which will perform the rendering.
        Default to `MatplotlibBackend`.

    detect_poles : boolean, optional
        Chose whether to detect and correctly plot poles. Defaulto to False.
        It only works with line plots. To improve detection, increase the
        number of discretization points if `adaptive=False` and/or change
        the value of `eps`.

    eps : float, optional
        An arbitrary small value used by the `detect_poles` algorithm.
        Default value to 0.1. Before changing this value, it is better to
        increase the number of discretization points.

    imag : boolean, optional
        If True, plot the imaginary part of the complex function.
        Default to True.

    line_kw : dict, optional
        A dictionary of keywords/values which is passed to the backend's
        function to customize the appearance of the lines. Refer to the
        plotting library (backend) manual for more informations.

    loss_fn : callable or None
        The loss function to be used by the `adaptive` learner.
        Possible values:

        * `None` (default): it will use the `default_loss` from the
          `adaptive` module.
        * callable : Refer to [#fn0]_ for more information. Specifically,
          look at `adaptive.learner.learner1D` to find more loss functions.

    modules : str, optional
        Specify the modules to be used for the numerical evaluation. Refer to
        `lambdify` to visualize the available options. Default to None,
        meaning Numpy/Scipy will be used. Note that other modules might
        produce different results, based on the way they deal with branch
        cuts.

    n1, n2 : int, optional
        Number of discretization points in the real/imaginary-directions,
        respectively, when `adaptive=False`. For line plots, default to 1000.
        For surface/contour plots (2D and 3D), default to 300.

    n : int, optional
        Set the same number of discretization points in all directions to be
        used when `adaptive=False`.

    real : boolean, optional
        If True, plot the real part of the complex function. Default to True.

    show : boolean, optional
        Default to True, in which case the plot will be shown on the screen.

    size : (float, float), optional
        A tuple in the form (width, height) to specify the size of
        the overall figure. The default value is set to `None`, meaning
        the size will be set by the backend.

    surface_kw : dict, optional
        A dictionary of keywords/values which is passed to the backend's
        function to customize the appearance of surfaces. Refer to the
        plotting library (backend) manual for more informations.

    threed : boolean, optional
        It only applies to a complex function over a complex range. If False,
        contour plots will be shown. If True, 3D surfaces will be shown.
        Default to False.

    use_cm : boolean, optional
        If False, surfaces will be rendered with a solid color.
        If True, a color map highlighting the elevation will be used.
        Default to True.

    use_latex : boolean, optional
        Turn on/off the rendering of latex labels. If the backend doesn't
        support latex, it will render the string representations instead.

    title : str, optional
        Title of the plot. It is set to the latex representation of
        the expression, if the plot has only one expression.

    xlabel : str, optional
        Label for the x-axis.

    ylabel : str, optional
        Label for the y-axis.

    zlabel : str, optional
        Label for the z-axis. Only available for 3D plots.

    xscale : 'linear' or 'log', optional
        Sets the scaling of the x-axis. Default to 'linear'.

    yscale : 'linear' or 'log', optional
        Sets the scaling of the y-axis. Default to 'linear'.

    xlim : (float, float), optional
        Denotes the x-axis limits, `(min, max)`.

    ylim : (float, float), optional
        Denotes the y-axis limits, `(min, max)`.

    zlim : (float, float), optional
        Denotes the z-axis limits, `(min, max)`. Only available for 3D plots.


    Examples
    ========

    .. plot::
       :context: reset
       :format: doctest
       :include-source: True

       >>> from sympy import I, symbols, exp, sqrt, cos, sin, pi, gamma
       >>> from spb import plot_real_imag
       >>> x, y, z = symbols('x, y, z')


    Plot the real and imaginary parts of a function over reals:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_real_imag(sqrt(x), (x, -3, 3))
       Plot object containing:
       [0]: cartesian line: (re(x)**2 + im(x)**2)**(1/4)*cos(atan2(im(x), re(x))/2) for x over (-3.0, 3.0)
       [1]: cartesian line: (re(x)**2 + im(x)**2)**(1/4)*sin(atan2(im(x), re(x))/2) for x over (-3.0, 3.0)

    Plot only the real part:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_real_imag(sqrt(x), (x, -3, 3), imag=False)
       Plot object containing:
       [0]: cartesian line: (re(x)**2 + im(x)**2)**(1/4)*cos(atan2(im(x), re(x))/2) for x over (-3.0, 3.0)

    Plot only the imaginary part:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_real_imag(sqrt(x), (x, -3, 3), real=False)
       Plot object containing:
       [0]: cartesian line: (re(x)**2 + im(x)**2)**(1/4)*sin(atan2(im(x), re(x))/2) for x over (-3.0, 3.0)

    Plot only the absolute value and argument:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_real_imag(sqrt(x), (x, -3, 3), real=False, imag=False, abs=True, arg=True)
       Plot object containing:
       [0]: cartesian line: sqrt(sqrt(re(x)**2 + im(x)**2)*sin(atan2(im(x), re(x))/2)**2 + sqrt(re(x)**2 + im(x)**2)*cos(atan2(im(x), re(x))/2)**2) for x over (-3.0, 3.0)
       [1]: cartesian line: arg(sqrt(x)) for x over (-3.0, 3.0)

    3D plot of the real and imaginary part of a function over a complex range:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_real_imag(sqrt(x), (x, -3-3j, 3+3j), n=100, threed=True)
       Plot object containing:
       [0]: cartesian surface: (re(x)**2 + im(x)**2)**(1/4)*cos(atan2(im(x), re(x))/2) for re(x) over (-3.0, 3.0) and im(x) over (-3.0, 3.0)
       [1]: cartesian surface: (re(x)**2 + im(x)**2)**(1/4)*sin(atan2(im(x), re(x))/2) for re(x) over (-3.0, 3.0) and im(x) over (-3.0, 3.0)

    3D plot of the absolute value of a function over a complex range:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_real_imag(sqrt(x), (x, -3-3j, 3+3j),
       ...     n=100, real=False, imag=False, abs=True, threed=True)
       Plot object containing:
       [0]: complex cartesian surface: sqrt(sqrt(re(x)**2 + im(x)**2)*sin(atan2(im(x), re(x))/2)**2 + sqrt(re(x)**2 + im(x)**2)*cos(atan2(im(x), re(x))/2)**2) for re(x) over (-3.0, 3.0) and im(x) over (-3.0, 3.0)

    References
    ==========

    .. [#fn0] https://github.com/python-adaptive/adaptive

    See Also
    ========

    plot_complex, plot_complex_list, plot_complex_vector

    """
    kwargs["absarg"] = False
    kwargs.setdefault("abs", False)
    kwargs.setdefault("arg", False)
    kwargs.setdefault("real", True)
    kwargs.setdefault("imag", True)
    return _plot_complex(*args, **kwargs)


def plot_complex(*args, **kwargs):
    """Plot the absolute value of a complex function colored by its argument.
    By default, the aspect ratio of the plot is set to `aspect="equal"`.

    Depending on the provided range, this function will produce different
    types of plots:

    1. Line plot over the reals.
    2. Image plot over the complex plane if `threed=False`. This is also
       known as Domain Coloring. Use the `coloring` keyword argument to
       select a different color scheme.
    3. If `threed=True`, plot a 3D surface of the absolute value over the
       complex plane, colored by its argument. Use the `coloring` keyword
       argument to select a different color scheme.

    Typical usage examples are in the followings:

    - Plotting a single expression with a single range.
        `plot_complex(expr, range, **kwargs)`
    - Plotting a single expression with the default range (-10, 10).
        `plot_complex(expr, **kwargs)`
    - Plotting multiple expressions with a single range.
        `plot_complex(expr1, expr2, ..., range, **kwargs)`
    - Plotting multiple expressions with multiple ranges.
        `plot_complex((expr1, range1), (expr2, range2), ..., **kwargs)`
    - Plotting multiple expressions with multiple ranges and custom labels.
        `plot_complex((expr1, range1, label1), (expr2, range2, label2), ..., **kwargs)`

    Parameters
    ==========
    args :
        expr : Expr
            Represent the complex function to be plotted.

        range : 3-element tuple
            Denotes the range of the variables. For example:

            * `(z, -5, 5)`: plot a line over the reals from point `-5` to
              `5`
            * `(z, -5 + 2*I, 5 + 2*I)`: plot a line from complex point
              `(-5 + 2*I)` to `(5 + 2 * I)`. Note the same imaginary part
              for the start/end point. Also note that we can specify the
              ranges by using standard Python complex numbers, for example
              `(z, -5+2j, 5+2j)`.
            * `(z, -5 - 3*I, 5 + 3*I)`: surface or contour plot of the
              complex function over the specified domain.

        label : str, optional
            The name of the complex function to be eventually shown on the
            legend. If none is provided, the string representation of the
            function will be used.

    adaptive : bool, optional
        Attempt to create line plots by using an adaptive algorithm.
        Image and surface plots do not use an adaptive algorithm.
        Default to True.
        Use `adaptive_goal` and `loss_fn` to further customize the output.

    adaptive_goal : callable, int, float or None
        Controls the "smoothness" of the evaluation. Possible values:

        * `None` (default):  it will use the following goal:
          `lambda l: l.loss() < 0.01`
        * number (int or float). The lower the number, the more
          evaluation points. This number will be used in the following goal:
          `lambda l: l.loss() < number`
        * callable: a function requiring one input element, the learner. It
          must return a float number. Refer to [#fn2]_ for more information.

    aspect : (float, float) or str, optional
        Set the aspect ratio of the plot. The value depends on the backend
        being used. Read that backend's documentation to find out the
        possible values.

    backend : Plot, optional
        A subclass of `Plot`, which will perform the rendering.
        Default to `MatplotlibBackend`.

    line_kw : dict, optional
        A dictionary of keywords/values which is passed to the backend's
        function to customize the appearance of lines. Refer to the
        plotting library (backend) manual for more informations.

    loss_fn : callable or None
        The loss function to be used by the `adaptive` learner.
        Possible values:

        * `None` (default): it will use the `default_loss` from the
          `adaptive` module.
        * callable : Refer to [#fn2]_ for more information. Specifically,
          look at `adaptive.learner.learner1D` to find more loss functions.

    modules : str, optional
        Specify the modules to be used for the numerical evaluation. Refer to
        `lambdify` to visualize the available options. Default to None,
        meaning Numpy/Scipy will be used. Note that other modules might
        produce different results, based on the way they deal with branch
        cuts.

    n1, n2 : int, optional
        Number of discretization points in the real/imaginary-directions,
        respectively, when `adaptive=False`. For line plots, default to 1000.
        For surface/contour plots (2D and 3D), default to 300.

    n : int, optional
        Set the same number of discretization points in all directions to be
        used when `adaptive=False`.

    show : boolean, optional
        Default to True, in which case the plot will be shown on the screen.

    size : (float, float), optional
        A tuple in the form (width, height) to specify the size of
        the overall figure. The default value is set to `None`, meaning
        the size will be set by the backend.

    threed : boolean, optional
        It only applies to a complex function over a complex range. If False,
        a 2D image plot will be shown. If True, 3D surfaces will be shown.
        Default to False.

    coloring : str or callable
        Choose between different domain coloring options. Default to `"a"`.
        Refer to [#fn1]_ for more information.

        - `"a"`: standard domain coloring using HSV, showing the argument
          of the complex function.
        - `"b"`: enhanced domain coloring using HSV, showing iso-modulus
          and is-phase lines.
        - `"c"`: enhanced domain coloring using HSV, showing iso-modulus
          lines.
        - `"d"`: enhanced domain coloring using HSV, showing iso-phase
          lines.
        - `"e"`: alternating black and white stripes corresponding to
          modulus.
        - `"f"`: alternating black and white stripes corresponding to
          phase.
        - `"g"`: alternating black and white stripes corresponding to
          real part.
        - `"h"`: alternating black and white stripes corresponding to
          imaginary part.
        - `"i"`: cartesian chessboard on the complex points space. The
          result will hide zeros.
        - `"j"`: polar Chessboard on the complex points space. The result
          will show conformality.

        The user can also provide a callable, `f(w)`, where `w` is an
        [n x m] Numpy array (provided by the plotting module) containing
        the results (complex numbers) of the evaluation of the complex
        function. The callable should return:

        - img : ndarray [n x m x 3]
            An array of RGB colors (0 <= R,G,B <= 255)
        - colorscale : ndarray [N x 3] or None
            An array with N RGB colors, (0 <= R,G,B <= 255).
            If `colorscale=None`, no color bar will be shown on the plot.

    phaseres : int
        Default value to 20. It controls the number of iso-phase and/or
        iso-modulus lines in domain coloring plots.

    title : str, optional
        Title of the plot. It is set to the latex representation of
        the expression, if the plot has only one expression.

    use_latex : boolean, optional
        Turn on/off the rendering of latex labels. If the backend doesn't
        support latex, it will render the string representations instead.

    xlabel : str, optional
        Label for the x-axis.

    ylabel : str, optional
        Label for the y-axis.

    zlabel : str, optional
        Label for the z-axis. Only available for 3D plots.

    xscale : 'linear' or 'log', optional
        Sets the scaling of the x-axis. Default to 'linear'.

    yscale : 'linear' or 'log', optional
        Sets the scaling of the y-axis. Default to 'linear'.

    xlim : (float, float), optional
        Denotes the x-axis limits, `(min, max)`.

    ylim : (float, float), optional
        Denotes the y-axis limits, `(min, max)`.

    zlim : (float, float), optional
        Denotes the z-axis limits, `(min, max)`. Only available for 3D plots.


    Examples
    ========

    .. plot::
       :context: reset
       :format: doctest
       :include-source: True

       >>> from sympy import I, symbols, exp, sqrt, cos, sin, pi, gamma
       >>> from spb import plot_complex
       >>> x, y, z = symbols('x, y, z')


    Plot the modulus of a complex function colored by its magnitude:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_complex((cos(x) + sin(I * x), "f"), (x, -2, 2))
       Plot object containing:
       [0]: absolute-argument line: cos(x) + I*sinh(x) for x over ((-2+0j), (2+0j))

    Domain coloring plot. Note that it might be necessary to increase the
    number of discretization points in order to get a smoother plot:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_complex(gamma(z), (z, -3 - 3*I, 3 + 3*I),
       ...     coloring="b", n=500, grid=False)
       Plot object containing:
       [0]: domain coloring: gamma(z) for re(z) over (-3.0, 3.0) and im(z) over (-3.0, 3.0)

    3D plot of the absolute value of a complex function colored by its
    argument:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_complex(gamma(z), (z, -3 - 3*I, 3 + 3*I), threed=True,
       ...     zlim=(-1, 6))
       Plot object containing:
       [0]: cartesian surface: gamma(z) for re(z) over (-3.0, 3.0) and im(z) over (-3.0, 3.0)


    References
    ==========

    .. [#fn1] Domain Coloring is based on Elias Wegert's book
       `"Visual Complex Functions" <https://www.springer.com/de/book/9783034801799>`_.
       The book provides the background to better understand the images.

    .. [#fn2] https://github.com/python-adaptive/adaptive

    See Also
    ========

    plot_real_imag, plot_complex_list, plot_complex_vector

    """
    kwargs["absarg"] = True
    kwargs["real"] = False
    kwargs["imag"] = False
    kwargs["abs"] = False
    kwargs["arg"] = False
    return _plot_complex(*args, **kwargs)


def plot_complex_list(*args, **kwargs):
    """Plot lists of complex points. By default, the aspect ratio of the plot
    is set to `aspect="equal"`.

    Typical usage examples are in the followings:

    - Plotting a single list of complex numbers.
        `plot_complex_list(l1, **kwargs)`
    - Plotting multiple lists of complex numbers.
        `plot_complex_list(l1, l2, **kwargs)`
    - Plotting multiple lists of complex numbers each one with a custom label.
        `plot_complex_list((l1, label1), (l2, label2), **kwargs)`


    Parameters
    ==========
    args :
        numbers : list, tuple
            A list of complex numbers.

        label : str
            The name associated to the list of the complex numbers to be
            eventually shown on the legend. Default to empty string.

    aspect : (float, float) or str, optional
        Set the aspect ratio of the plot. The value depends on the backend
        being used. Read that backend's documentation to find out the
        possible values.

    backend : Plot, optional
        A subclass of `Plot`, which will perform the rendering.
        Default to `MatplotlibBackend`.

    is_point : boolean
        If True, a scatter plot will be produced. Otherwise a line plot will
        be created. Default to True.

    is_filled : boolean, optional
        Default to True, which will render empty circular markers. It only
        works if `is_point=True`.
        If False, filled circular markers will be rendered.

    line_kw : dict, optional
        A dictionary of keywords/values which is passed to the backend's
        function to customize the appearance of lines. Refer to the
        plotting library (backend) manual for more informations.

    show : boolean
        Default to True, in which case the plot will be shown on the screen.

    size : (float, float), optional
        A tuple in the form (width, height) to specify the size of
        the overall figure. The default value is set to `None`, meaning
        the size will be set by the backend.

    title : str, optional
        Title of the plot. It is set to the latex representation of
        the expression, if the plot has only one expression.

    use_latex : boolean, optional
        Turn on/off the rendering of latex labels. If the backend doesn't
        support latex, it will render the string representations instead.

    xlabel : str, optional
        Label for the x-axis.

    ylabel : str, optional
        Label for the y-axis.

    xscale : 'linear' or 'log', optional
        Sets the scaling of the x-axis. Default to 'linear'.

    yscale : 'linear' or 'log', optional
        Sets the scaling of the y-axis. Default to 'linear'.

    xlim : (float, float), optional
        Denotes the x-axis limits, `(min, max)`.

    ylim : (float, float), optional
        Denotes the y-axis limits, `(min, max)`.


    Examples
    ========

    .. plot::
       :context: reset
       :format: doctest
       :include-source: True

       >>> from sympy import I, symbols, exp, sqrt, cos, sin, pi, gamma
       >>> from spb import plot_complex_list
       >>> x, y, z = symbols('x, y, z')

    Plot individual complex points:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_complex_list(3 + 2 * I, 4 * I, 2)
       Plot object containing:
       [0]: complex point (3 + 2*I,)
       [1]: complex point (4*I,)
       [2]: complex point (2,)

    Plot two lists of complex points and assign to them custom labels:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> expr1 = z * exp(2 * pi * I * z)
       >>> expr2 = 2 * expr1
       >>> n = 15
       >>> l1 = [expr1.subs(z, t / n) for t in range(n)]
       >>> l2 = [expr2.subs(z, t / n) for t in range(n)]
       >>> plot_complex_list((l1, "f1"), (l2, "f2"))
       Plot object containing:
       [0]: complex points (0.0, 0.0666666666666667*exp(0.133333333333333*I*pi), 0.133333333333333*exp(0.266666666666667*I*pi), 0.2*exp(0.4*I*pi), 0.266666666666667*exp(0.533333333333333*I*pi), 0.333333333333333*exp(0.666666666666667*I*pi), 0.4*exp(0.8*I*pi), 0.466666666666667*exp(0.933333333333333*I*pi), 0.533333333333333*exp(1.06666666666667*I*pi), 0.6*exp(1.2*I*pi), 0.666666666666667*exp(1.33333333333333*I*pi), 0.733333333333333*exp(1.46666666666667*I*pi), 0.8*exp(1.6*I*pi), 0.866666666666667*exp(1.73333333333333*I*pi), 0.933333333333333*exp(1.86666666666667*I*pi))
       [1]: complex points (0, 0.133333333333333*exp(0.133333333333333*I*pi), 0.266666666666667*exp(0.266666666666667*I*pi), 0.4*exp(0.4*I*pi), 0.533333333333333*exp(0.533333333333333*I*pi), 0.666666666666667*exp(0.666666666666667*I*pi), 0.8*exp(0.8*I*pi), 0.933333333333333*exp(0.933333333333333*I*pi), 1.06666666666667*exp(1.06666666666667*I*pi), 1.2*exp(1.2*I*pi), 1.33333333333333*exp(1.33333333333333*I*pi), 1.46666666666667*exp(1.46666666666667*I*pi), 1.6*exp(1.6*I*pi), 1.73333333333333*exp(1.73333333333333*I*pi), 1.86666666666667*exp(1.86666666666667*I*pi))

    See Also
    ========

    plot_real_imag, plot_complex, plot_complex_vector

    """
    kwargs["absarg"] = False
    kwargs["abs"] = False
    kwargs["arg"] = False
    kwargs["real"] = False
    kwargs["imag"] = False
    kwargs["threed"] = False
    return _plot_complex(*args, **kwargs)


def plot_complex_vector(*args, **kwargs):
    """Plot the vector field `[re(f), im(f)]` for a complex function `f`
    over the specified complex domain. By default, the aspect ratio of the
    plot is set to `aspect="equal"`.

    Typical usage examples are in the followings:

    - Plotting a vector field of a complex function.
        `plot_complex_vector(expr, range, **kwargs)`

    - Plotting multiple vector fields with different ranges and custom labels.
        `plot_complex_vector((expr1, range1, label1 [optional]), (expr2, range2, label2 [optional]), **kwargs)`

    Parameters
    ==========

    args :
        expr : Expr
            Represent the complex function.

        range : 3-element tuples
            Denotes the range of the variables. For example
            `(z, -5 - 3*I, 5 + 3*I)`. Note that we can specify the range
            by using standard Python complex numbers, for example
            `(z, -5-3j, 5+3j)`.

        label : str, optional
            The name of the complex expression to be eventually shown on the
            legend. If none is provided, the string representation of the
            expression will be used.

    aspect : (float, float) or str, optional
        Set the aspect ratio of the plot. The value depends on the backend
        being used. Read that backend's documentation to find out the
        possible values.

    backend : Plot, optional
        A subclass of `Plot`, which will perform the rendering.
        Default to `MatplotlibBackend`.

    contours_kw : dict
        A dictionary of keywords/values which is passed to the backend
        contour function to customize the appearance. Refer to the plotting
        library (backend) manual for more informations.

    n1, n2 : int
        Number of discretization points for the quivers or streamlines in the
        x/y-direction, respectively. Default to 25.

    n : int
        Set the same number of discretization points in all directions for
        the quivers or streamlines. It overrides `n1`, `n2`.
        Default to 25.

    nc : int
        Number of discretization points for the scalar contour plot.
        Default to 100.

    quiver_kw : dict
        A dictionary of keywords/values which is passed to the backend
        quivers-plotting function to customize the appearance. Refer to the
        plotting library (backend) manual for more informations.

    scalar : boolean, Expr, None or list/tuple of 2 elements
        Represents the scalar field to be plotted in the background of a 2D
        vector field plot. Can be:

        - `True`: plot the magnitude of the vector field. Only works when a
          single vector field is plotted.
        - `False`/`None`: do not plot any scalar field.
        - `Expr`: a symbolic expression representing the scalar field.
        - `list`/`tuple`: [scalar_expr, label], where the label will be
          shown on the colorbar.

        Remember: the scalar function must return real data.

        Default to True.

    show : boolean
        The default value is set to `True`. Set show to `False` and
        the function will not display the plot. The returned instance of
        the `Plot` class can then be used to save or display the plot
        by calling the `save()` and `show()` methods respectively.

    size : (float, float), optional
        A tuple in the form (width, height) to specify the size of
        the overall figure. The default value is set to `None`, meaning
        the size will be set by the backend.

    streamlines : boolean
        Whether to plot the vector field using streamlines (True) or quivers
        (False). Default to False.

    stream_kw : dict
        A dictionary of keywords/values which is passed to the backend
        streamlines-plotting function to customize the appearance. Refer to
        the plotting library (backend) manual for more informations.

    title : str, optional
        Title of the plot. It is set to the latex representation of
        the expression, if the plot has only one expression.

    use_latex : boolean, optional
        Turn on/off the rendering of latex labels. If the backend doesn't
        support latex, it will render the string representations instead.

    xlabel : str, optional
        Label for the x-axis.

    ylabel : str, optional
        Label for the y-axis.

    xscale : 'linear' or 'log', optional
        Sets the scaling of the x-axis. Default to 'linear'.

    yscale : 'linear' or 'log', optional
        Sets the scaling of the y-axis. Default to 'linear'.

    xlim : (float, float), optional
        Denotes the x-axis limits, `(min, max)`.

    ylim : (float, float), optional
        Denotes the y-axis limits, `(min, max)`.


    Examples
    ========

    .. plot::
       :context: reset
       :format: doctest
       :include-source: True

       >>> from sympy import I, symbols, exp, sqrt, cos, sin, pi, gamma
       >>> from spb import plot_complex_vector
       >>> z = symbols('z')

    Quivers plot with a contour plot in background representing the
    vector's magnitude (a scalar field).

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_complex_vector(z**2, (z, -5 - 5j, 5 + 5j),
       ...     quiver_kw=dict(color="orange"), grid=False)
       Plot object containing:
       [0]: contour: sqrt(((re(_x) - im(_y))**2 - (re(_y) + im(_x))**2)**2 + 4*(re(_x) - im(_y))**2*(re(_y) + im(_x))**2) for _x over (-5.0, 5.0) and _y over (-5.0, 5.0)
       [1]: 2D vector series: [(re(_x) - im(_y))**2 - (re(_y) + im(_x))**2, 2*(re(_x) - im(_y))*(re(_y) + im(_x))] over (_x, -5.0, 5.0), (_y, -5.0, 5.0)

    Only quiver plot.

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_complex_vector(z**2, (z, -5 - 5j, 5 + 5j), scalar=False)
       Plot object containing:
       [0]: 2D vector series: [(re(_x) - im(_y))**2 - (re(_y) + im(_x))**2, 2*(re(_x) - im(_y))*(re(_y) + im(_x))] over (_x, -5.0, 5.0), (_y, -5.0, 5.0)

    Only streamlines plot.

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_complex_vector(z**2, (z, -5 - 5j, 5 + 5j), scalar=False, streamlines=True)
       Plot object containing:
       [0]: 2D vector series: [(re(_x) - im(_y))**2 - (re(_y) + im(_x))**2, 2*(re(_x) - im(_y))*(re(_y) + im(_x))] over (_x, -5.0, 5.0), (_y, -5.0, 5.0)

    Quivers plot for multiple complex expressions:

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_complex_vector((z**2, (z, -5 - 5j, 5 + 0j)), (z**3, (z, -5 - 0j, 5 + 5j)))
       Plot object containing:
       [0]: 2D vector series: [(re(_x) - im(_y))**2 - (re(_y) + im(_x))**2, 2*(re(_x) - im(_y))*(re(_y) + im(_x))] over (_x, -5.0, 5.0), (_y, -5.0, 0.0)
       [1]: 2D vector series: [(re(_x) - im(_y))**3 - 3*(re(_x) - im(_y))*(re(_y) + im(_x))**2, 3*(re(_x) - im(_y))**2*(re(_y) + im(_x)) - (re(_y) + im(_x))**3] over (_x, -5.0, 5.0), (_y, 0.0, 5.0)

    See Also
    ========

    plot_real_imag, plot_complex, plot_complex_list

    """
    # for each argument, generate two series: one for the real part and
    # another for the imaginary part
    kwargs["absarg"] = False
    kwargs["abs"] = False
    kwargs["arg"] = False
    kwargs["real"] = True
    kwargs["imag"] = True
    kwargs["threed"] = False

    args = _plot_sympify(args)
    series = _build_series(*args, **kwargs)
    multiple_expr = len(series) > 2

    def get_label(i):
        _iterable = args[i] if multiple_expr else args
        for t in _iterable:
            if isinstance(t, str):
                return t
        return str(args[i][0] if multiple_expr else args[0])

    # create new arguments to be used by plot_vector
    new_args = []
    x, y = symbols("x, y", cls=Dummy)
    for i in range(int(len(series) / 2)):
        s1 = series[2 * i]
        s2 = series[2 * i + 1]
        expr1 = s1.expr
        expr2 = s2.expr
        free_symbols = list(expr1.free_symbols)
        if len(free_symbols) > 0:
            fs = free_symbols[0]
            expr1 = expr1.subs({fs: x + I * y})
            expr2 = expr2.subs({fs: x + I * y})
        r1 = (x, s1.start.real, s1.end.real)
        r2 = (y, s1.start.imag, s1.end.imag)
        label = get_label(i)
        new_args.append(((expr1, expr2), r1, r2, label))

    # substitute the complex variable in the scalar field
    scalar = kwargs.get("scalar", None)
    if scalar is not None:
        if isinstance(scalar, Expr):
            scalar = scalar.subs({fs: x + I * y})
        elif isinstance(scalar, (list, tuple)):
            scalar = list(scalar)
            scalar[0] = scalar[0].subs({fs: x + I * y})
        kwargs["scalar"] = scalar

    kwargs.setdefault("xlabel", "x")
    kwargs.setdefault("ylabel", "y")
    return plot_vector(*new_args, **kwargs)
