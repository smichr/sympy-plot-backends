from sympy import latex
from sympy.core.symbol import symbols
from sympy.core.containers import Tuple
from sympy.core.numbers import I, pi
from sympy.functions.elementary.trigonometric import sin, cos, tan
from sympy.functions.elementary.exponential import log
from sympy.functions.elementary.miscellaneous import sqrt
from sympy.functions.elementary.complexes import re, im, arg
from sympy.functions.elementary.integers import frac
from sympy.geometry import Plane, Circle, Point
from sympy.concrete.summations import Sum
from sympy.core.singleton import S
from sympy.external import import_module
from sympy.vector import CoordSys3D, gradient

from spb.series import (
    LineOver1DRangeSeries, Parametric2DLineSeries, Parametric3DLineSeries,
    SurfaceOver2DRangeSeries, ContourSeries, ParametricSurfaceSeries,
    InteractiveSeries,
    ImplicitSeries, Implicit3DSeries,
    Vector2DSeries, Vector3DSeries, SliceVector3DSeries,
    ComplexSurfaceSeries, ComplexDomainColoringSeries,
    ComplexInteractiveBaseSeries,
    ComplexSurfaceInteractiveSeries, ComplexDomainColoringInteractiveSeries,
    ComplexPointSeries, ComplexPointInteractiveSeries,
    GeometrySeries, GeometryInteractiveSeries,
    PlaneSeries, PlaneInteractiveSeries,
    List2DSeries, AbsArgLineSeries,
    LineInteractiveSeries, AbsArgLineInteractiveSeries,
    Parametric2DLineInteractiveSeries, Parametric3DLineInteractiveSeries,
    ParametricSurfaceInteractiveSeries, SurfaceInteractiveSeries,
    Vector2DInteractiveSeries, Vector3DInteractiveSeries,
    SliceVector3DInteractiveSeries, ContourInteractiveSeries
)
from pytest import raises
np = import_module('numpy', catch=(RuntimeError,))

# NOTE:
#
# These tests are meant to verify that the data series generates the expected
# numerical data.
#
# If your issue is related to the processing and generation of *Series
# objects, consider adding tests to test_functions.py.
# If your issue il related to the preprocessing and generation of a
# Vector series or a Complex Series, consider adding tests to
# test_build_series.
# If your issue is related to a particular keyword affecting a backend
# behaviour, consider adding tests to test_backends.py
#


def test_adaptive():
    # verify that adaptive-related keywords produces the expected results

    from adaptive.learner.learner1D import curvature_loss_function
    x, y = symbols("x, y")

    # use default adaptive options: adaptive_goal=0.01, loss_fn=None
    s1 = LineOver1DRangeSeries(sin(x), (x, -10, 10), "", adaptive=True)
    x1, _ = s1.get_data()
    # use a different goal: set a number
    s2 = LineOver1DRangeSeries(sin(x), (x, -10, 10), "", adaptive=True,
        adaptive_goal=0.001)
    x2, _ = s2.get_data()
    # use a different goal: set a function
    s3 = LineOver1DRangeSeries(sin(x), (x, -10, 10), "", adaptive=True,
        adaptive_goal=lambda l: l.npoints >= 100)
    x3, _ = s3.get_data()
    # use a different loss function
    s4 = LineOver1DRangeSeries(sin(x), (x, -10, 10), "", adaptive=True,
        adaptive_goal=0.01, loss_fn=curvature_loss_function())
    x4, _ = s4.get_data()
    assert len(x1) < len(x2)
    assert len(x3) >= 100
    # using the same adaptive_goal value, curvature_loss_function produces
    # less points than default_loss
    assert len(x1) > len(x4)

    s1 = Parametric2DLineSeries(cos(x), sin(x), (x, 0, 2*pi),
        adaptive=True)
    x1, _, _, = s1.get_data()
    s2 = Parametric2DLineSeries(cos(x), sin(x), (x, 0, 2*pi),
        adaptive=True, adaptive_goal=0.001)
    x2, _, _ = s2.get_data()
    s3 = Parametric2DLineSeries(cos(x), sin(x), (x, 0, 2*pi),
        adaptive=True, adaptive_goal=0.01, loss_fn=curvature_loss_function())
    x3, _, _ = s3.get_data()
    assert len(x1) < len(x2)
    assert len(x1) > len(x3)

    s1 = Parametric3DLineSeries(cos(x), sin(x), x, (x, 0, 2*pi),
        adaptive=True)
    x1, _, _, _ = s1.get_data()
    s2 = Parametric3DLineSeries(cos(x), sin(x), x, (x, 0, 2*pi),
        adaptive=True, adaptive_goal=0.001)
    x2, _, _, _ = s2.get_data()
    s3 = Parametric3DLineSeries(cos(x), sin(x), x, (x, 0, 2*pi),
        adaptive=True, adaptive_goal=0.01, loss_fn=curvature_loss_function())
    x3, _, _, _ = s3.get_data()
    assert len(x1) < len(x2)
    assert len(x1) > len(x3)

    # the more refined the goal, the greater the number of points
    s1 = SurfaceOver2DRangeSeries(cos(x**2 + y**2), (x, -3, 3), (y, -3, 3),
        adaptive=True, adaptive_goal=0.5)
    x1, _, _ = s1.get_data()
    n1 = x1.shape[0] * x1.shape[1]
    s2 = SurfaceOver2DRangeSeries(cos(x**2 + y**2), (x, -3, 3), (y, -3, 3),
        adaptive=True, adaptive_goal=0.1)
    x2, _, _ = s2.get_data()
    n2 = x2.shape[0] * x2.shape[1]
    assert n1 < n2


def test_adaptive_zerodivisionerror():
    x, y = symbols("x, y")

    # adaptive should be able to catch ZeroDivisionError
    s1 = LineOver1DRangeSeries(1 / x, (x, -10, 10), "", adaptive=True)
    x1, y1 = s1.get_data()

    s1 = Parametric2DLineSeries(cos(x), 1 / x, (x, -10, 10), "",
        adaptive=True)
    x1, y1, p1 = s1.get_data()

    s1 = Parametric3DLineSeries(cos(x), x, 1 / x, (x, -10, 10), "",
        adaptive=True)
    x1, y1, z1, p1 = s1.get_data()


def test_detect_poles():
    x, u = symbols("x, u")

    s1 = LineOver1DRangeSeries(tan(x), (x, -pi, pi),
        adaptive=False, n=1000, detect_poles=False)
    xx1, yy1 = s1.get_data()
    s2 = LineOver1DRangeSeries(tan(x), (x, -pi, pi),
        adaptive=False, n=1000, detect_poles=True, eps=0.01)
    xx2, yy2 = s2.get_data()
    # eps is too small: doesn't detect any poles
    s3 = LineOver1DRangeSeries(tan(x), (x, -pi, pi),
        adaptive=False, n=1000, detect_poles=True, eps=1e-06)
    xx3, yy3 = s3.get_data()

    assert np.allclose(xx1, xx2) and np.allclose(xx1, xx3)
    assert not np.any(np.isnan(yy1))
    assert not np.any(np.isnan(yy3))
    assert np.any(np.isnan(yy2))

    s1 = LineOver1DRangeSeries(frac(x), (x, -10, 10),
        adaptive=False, n=1000, detect_poles=False)
    xx1, yy1 = s1.get_data()
    s2 = LineOver1DRangeSeries(frac(x), (x, -10, 10),
        adaptive=False, n=1000, detect_poles=True, eps=0.05)
    xx2, yy2 = s2.get_data()
    xx3, yy3 = s3.get_data()

    assert np.allclose(xx1, xx2)
    assert not np.any(np.isnan(yy1))
    assert np.any(np.isnan(yy2))

    s1 = LineInteractiveSeries([tan(x)], [(x, -pi, pi)],
        adaptive=False, n=1000, detect_poles=False)
    xx1, yy1 = s1.get_data()
    s2 = LineInteractiveSeries([tan(x)], [(x, -pi, pi)],
        adaptive=False, n=1000, detect_poles=True, eps=0.01)
    xx2, yy2 = s2.get_data()
    # eps is too small: doesn't detect any poles
    s3 = LineInteractiveSeries([tan(x)], [(x, -pi, pi)],
        adaptive=False, n=1000, detect_poles=True, eps=1e-06)
    xx3, yy3 = s3.get_data()

    assert np.allclose(xx1, xx2) and np.allclose(xx1, xx3)
    assert not np.any(np.isnan(yy1))
    assert not np.any(np.isnan(yy3))
    assert np.any(np.isnan(yy2))


def test_list2dseries():
    xx = np.linspace(-3, 3, 10)
    yy1 = np.cos(xx)
    yy2 = np.linspace(-3, 3, 20)

    # same number of elements: everything is fine
    s = List2DSeries(xx, yy1)
    # different number of elements: error
    raises(ValueError, lambda: List2DSeries(xx, yy2))


def test_interactive_instance():
    # test that the correct data series is produced when instantiating
    # InteractiveSeries
    x, y, z, u, v = symbols("x, y, z, u, v")

    s = InteractiveSeries([u * cos(x)], [(x, -5, 5)], params={u: 1},
        absarg=False)
    assert isinstance(s, LineInteractiveSeries)
    assert not isinstance(s, AbsArgLineInteractiveSeries)

    s = InteractiveSeries([u * cos(x)], [(x, -5, 5)], params={u: 1},
        absarg=True)
    assert isinstance(s, AbsArgLineInteractiveSeries)

    s = InteractiveSeries([u * cos(x), u * sin(x)], [(x, -5, 5)],
        params={u: 1}, absarg=False)
    assert isinstance(s, Parametric2DLineInteractiveSeries)

    s = InteractiveSeries([u * cos(x), u * sin(x), x], [(x, -5, 5)],
        params={u: 1}, absarg=False)
    assert isinstance(s, Parametric3DLineInteractiveSeries)

    s = InteractiveSeries([u * cos(x * y)], [(x, -5, 5), (y, -5, 5)],
        params={u: 1}, threed=True)
    assert isinstance(s, SurfaceInteractiveSeries)

    s = InteractiveSeries([u * cos(x * y)], [(x, -5, 5), (y, -5, 5)],
        params={u: 1}, threed=False)
    assert isinstance(s, ContourInteractiveSeries)

    s = InteractiveSeries([u * cos(v * x), v * sin(u), u + v],
        [(u, -5, 5), (v, -5, 5)],
        params={x: 1})
    assert isinstance(s, ParametricSurfaceInteractiveSeries)

    s = InteractiveSeries([u * cos(y), u * sin(x)], [(x, -5, 5), (y, -5, 5)],
        params={u: 1})
    assert isinstance(s, Vector2DInteractiveSeries)

    s = InteractiveSeries([u * cos(y), u * sin(x), z],
        [(x, -5, 5), (y, -5, 5), (z, -5, 5)], params={u: 1}, slice=None)
    assert isinstance(s, Vector3DInteractiveSeries)

    s = InteractiveSeries([u * cos(y), u * sin(x), z],
        [(x, -5, 5), (y, -5, 5), (z, -5, 5)], params={u: 1},
        slice=Plane((0, 0, 0), (0, 1, 0)))
    assert isinstance(s, SliceVector3DInteractiveSeries)

    s = InteractiveSeries([Plane((u * x, y, 0), (0, 1, 0))],
        [(x, -5, 5), (y, -5, 5), (z, -5, 5)], params={u: 1})
    assert isinstance(s, PlaneInteractiveSeries)

    s = InteractiveSeries([Circle(Point(0, 0), u * 5)], [], params={u: 1})
    assert isinstance(s, GeometryInteractiveSeries)

    s = ComplexInteractiveBaseSeries(sqrt(z), (z, -5 - 5j, 5 + 5j),
        absarg=False)
    assert isinstance(s, ComplexSurfaceInteractiveSeries)

    s = ComplexInteractiveBaseSeries(sqrt(z), (z, -5 - 5j, 5 + 5j),
        absarg=True)
    assert isinstance(s, ComplexDomainColoringInteractiveSeries)


def test_lin_log_scale():
    # Verify that data series create the correct spacing in the data.
    x, y, z = symbols("x, y, z")

    s = LineOver1DRangeSeries(x, (x, 1, 10), adaptive=False, n=50, xscale="linear")
    xx, _ = s.get_data()
    assert np.isclose(xx[1] - xx[0], xx[-1] - xx[-2])

    s = LineOver1DRangeSeries(x, (x, 1, 10), adaptive=False, n=50, xscale="log")
    xx, _ = s.get_data()
    assert not np.isclose(xx[1] - xx[0], xx[-1] - xx[-2])

    s = Parametric2DLineSeries(
        cos(x), sin(x), (x, pi / 2, 1.5 * pi), adaptive=False, n=50, xscale="linear"
    )
    _, _, param = s.get_data()
    assert np.isclose(param[1] - param[0], param[-1] - param[-2])

    s = Parametric2DLineSeries(
        cos(x), sin(x), (x, pi / 2, 1.5 * pi), adaptive=False, n=50, xscale="log"
    )
    _, _, param = s.get_data()
    assert not np.isclose(param[1] - param[0], param[-1] - param[-2])

    s = Parametric3DLineSeries(
        cos(x), sin(x), x, (x, pi / 2, 1.5 * pi), adaptive=False, n=50, xscale="linear"
    )
    _, _, _, param = s.get_data()
    assert np.isclose(param[1] - param[0], param[-1] - param[-2])

    s = Parametric3DLineSeries(
        cos(x), sin(x), x, (x, pi / 2, 1.5 * pi), adaptive=False, n=50, xscale="log"
    )
    _, _, _, param = s.get_data()
    assert not np.isclose(param[1] - param[0], param[-1] - param[-2])

    s = SurfaceOver2DRangeSeries(
        cos(x ** 2 + y ** 2),
        (x, 1, 5),
        (y, 1, 5),
        n=10,
        xscale="linear",
        yscale="linear",
    )
    xx, yy, _ = s.get_data()
    assert np.isclose(xx[0, 1] - xx[0, 0], xx[0, -1] - xx[0, -2])
    assert np.isclose(yy[1, 0] - yy[0, 0], yy[-1, 0] - yy[-2, 0])

    s = SurfaceOver2DRangeSeries(
        cos(x ** 2 + y ** 2), (x, 1, 5), (y, 1, 5), n=10, xscale="log", yscale="log"
    )
    xx, yy, _ = s.get_data()
    assert not np.isclose(xx[0, 1] - xx[0, 0], xx[0, -1] - xx[0, -2])
    assert not np.isclose(yy[1, 0] - yy[0, 0], yy[-1, 0] - yy[-2, 0])

    s = ImplicitSeries(
        cos(x ** 2 + y ** 2) > 0, (x, 1, 5), (y, 1, 5),
        n=10, xscale="linear", yscale="linear", adaptive=False
    )
    xx, yy, _, _ = s.get_data()
    assert np.isclose(xx[1] - xx[0], xx[-1] - xx[-2])
    assert np.isclose(yy[1] - yy[0], yy[-1] - yy[-2])

    s = ImplicitSeries(
        cos(x ** 2 + y ** 2) > 0, (x, 1, 5), (y, 1, 5),
        n=10, xscale="log", yscale="log", adaptive=False
    )
    xx, yy, _, _ = s.get_data()
    assert not np.isclose(xx[1] - xx[0], xx[-1] - xx[-2])
    assert not np.isclose(yy[1] - yy[0], yy[-1] - yy[-2])

    s = InteractiveSeries([log(x)], [(x, 1e-05, 1e05)], n=10, xscale="linear")
    xx, yy = s.get_data()
    assert np.isclose(xx[1] - xx[0], xx[-1] - xx[-2])

    s = InteractiveSeries([log(x)], [(x, 1e-05, 1e05)], n=10, xscale="log")
    xx, yy = s.get_data()
    assert not np.isclose(xx[1] - xx[0], xx[-1] - xx[-2])

    s = AbsArgLineSeries(cos(x), (x, 1e-05, 1e05), n=10,
        xscale="linear", adaptive=False)
    xx, yy, _ = s.get_data()
    assert np.isclose(xx[1] - xx[0], xx[-1] - xx[-2])

    s = AbsArgLineSeries(cos(x), (x, 1e-05, 1e05), n=10,
        xscale="log", adaptive=False)
    xx, yy, _ = s.get_data()
    assert not np.isclose(xx[1] - xx[0], xx[-1] - xx[-2])

    s = Vector3DSeries(
        x, y, z, (x, 1, 1e05), (y, 1, 1e05), (z, 1, 1e05),
        xscale="linear", yscale="linear", zscale="linear"
    )
    xx, yy, zz, _, _, _ = s.get_data()
    assert np.isclose(
        xx[0, :, 0][1] - xx[0, :, 0][0], xx[0, :, 0][-1] - xx[0, :, 0][-2]
    )
    assert np.isclose(
        yy[:, 0, 0][1] - yy[:, 0, 0][0], yy[:, 0, 0][-1] - yy[:, 0, 0][-2]
    )
    assert np.isclose(
        zz[0, 0, :][1] - zz[0, 0, :][0], zz[0, 0, :][-1] - zz[0, 0, :][-2]
    )

    s = Vector3DSeries(
        x, y, z, (x, 1, 1e05), (y, 1, 1e05), (z, 1, 1e05),
        xscale="log", yscale="log", zscale="log"
    )
    xx, yy, zz, _, _, _ = s.get_data()
    assert not np.isclose(
        xx[0, :, 0][1] - xx[0, :, 0][0], xx[0, :, 0][-1] - xx[0, :, 0][-2]
    )
    assert not np.isclose(
        yy[:, 0, 0][1] - yy[:, 0, 0][0], yy[:, 0, 0][-1] - yy[:, 0, 0][-2]
    )
    assert not np.isclose(
        zz[0, 0, :][1] - zz[0, 0, :][0], zz[0, 0, :][-1] - zz[0, 0, :][-2]
    )


def test_rendering_kw():
    # verify that each series exposes the `rendering_kw` attribute
    u, v, x, y, z = symbols("u, v, x:z")

    s = List2DSeries([1, 2, 3], [4, 5, 6])
    assert isinstance(s.rendering_kw, dict)

    s = LineOver1DRangeSeries(1, (x, -5, 5))
    assert isinstance(s.rendering_kw, dict)

    s = AbsArgLineSeries(1, (x, -5, 5))
    assert isinstance(s.rendering_kw, dict)

    s = Parametric2DLineSeries(sin(x), cos(x), (x, 0, pi))
    assert isinstance(s.rendering_kw, dict)

    s = Parametric3DLineSeries(cos(x), sin(x), x, (x, 0, 2 * pi))
    assert isinstance(s.rendering_kw, dict)

    s = SurfaceOver2DRangeSeries(x + y, (x, -2, 2), (y, -3, 3))
    assert isinstance(s.rendering_kw, dict)

    s = Implicit3DSeries(
        x**2 + y**3 - z**2, (x, -2, 2), (y, -3, 3), (z, -4, 4))
    assert isinstance(s.rendering_kw, dict)

    s = ContourSeries(x + y, (x, -2, 2), (y, -3, 3))
    assert isinstance(s.rendering_kw, dict)

    s = ParametricSurfaceSeries(1, x, y, (x, 0, 1), (y, 0, 1))
    assert isinstance(s.rendering_kw, dict)

    s = ComplexPointSeries(x + I * y)
    assert isinstance(s.rendering_kw, dict)

    s = ComplexSurfaceSeries(1, (x, -5 - 2 * I, 5 + 2 * I))
    assert isinstance(s.rendering_kw, dict)

    s = ComplexDomainColoringSeries(1, (x, -5 - 2 * I, 5 + 2 * I))
    assert isinstance(s.rendering_kw, dict)

    s = Vector2DSeries(-y, x, (x, -3, 3), (y, -4, 4))
    assert isinstance(s.rendering_kw, dict)

    s = Vector3DSeries(z, -y, x, (x, -3, 3), (y, -4, 4), (z, -5, 5))
    assert isinstance(s.rendering_kw, dict)

    s = SliceVector3DSeries(
        Plane((-1, 0, 0), (1, 0, 0)),
        z, -y, x,
        (x, -3, 3), (y, -2, 2), (z, -1, 1))
    assert isinstance(s.rendering_kw, dict)

    s = PlaneSeries(Plane((0, 0, 0), (1, 1, 1)),
        (x, -5, 4), (y, -3, 2), (z, -6, 7))
    assert isinstance(s.rendering_kw, dict)

    s = GeometrySeries(Circle(Point(0, 0), 5))
    assert isinstance(s.rendering_kw, dict)

    s = LineInteractiveSeries([u * cos(x)], [(x, -5, 5)], params={u: 1})
    assert isinstance(s.rendering_kw, dict)

    s = AbsArgLineInteractiveSeries([u * cos(x)], [(x, -5, 5)], params={u: 1})
    assert isinstance(s.rendering_kw, dict)

    s = Parametric2DLineInteractiveSeries(
        [u * cos(x), u * sin(x)], [(x, -5, 5)], params={u: 1})
    assert isinstance(s.rendering_kw, dict)

    s = Parametric3DLineInteractiveSeries(
        [u * cos(x), u * sin(x), x], [(x, -5, 5)], params={u: 1})
    assert isinstance(s.rendering_kw, dict)

    s = SurfaceInteractiveSeries(
        [u * cos(x * y)], [(x, -5, 5), (y, -5, 5)], params={u: 1})
    assert isinstance(s.rendering_kw, dict)

    s = ContourInteractiveSeries(
        [u * cos(x * y)], [(x, -5, 5), (y, -5, 5)], params={u: 1})
    assert isinstance(s.rendering_kw, dict)

    s = ParametricSurfaceInteractiveSeries(
        [u * cos(v * x), v * sin(u), u + v], [(u, -5, 5), (v, -5, 5)],
        params={x: 1})
    assert isinstance(s.rendering_kw, dict)

    s = Vector2DInteractiveSeries(
        [u * cos(y), u * sin(x)], [(x, -5, 5), (y, -5, 5)], params={u: 1})
    assert isinstance(s.rendering_kw, dict)

    s = Vector3DInteractiveSeries(
        [u * cos(y), u * sin(x), z], [(x, -5, 5), (y, -5, 5), (z, -5, 5)],
        params={u: 1})
    assert isinstance(s.rendering_kw, dict)

    s = SliceVector3DInteractiveSeries([u * cos(y), u * sin(x), z],
        [(x, -5, 5), (y, -5, 5), (z, -5, 5)], params={u: 1},
        slice=Plane((0, 0, 0), (0, 1, 0)))
    assert isinstance(s.rendering_kw, dict)

    s = PlaneInteractiveSeries([Plane((u * x, y, 0), (0, 1, 0))],
        [(x, -5, 5), (y, -5, 5), (z, -5, 5)], params={u: 1})
    assert isinstance(s.rendering_kw, dict)

    s = GeometryInteractiveSeries(
        [Circle(Point(0, 0), u * 5)], [], params={u: 1})
    assert isinstance(s.rendering_kw, dict)

    s = ComplexPointInteractiveSeries([1 + 2 * I * u, 3 + 4 * I],
        params={u: 1})
    assert isinstance(s.rendering_kw, dict)

    s = ComplexSurfaceInteractiveSeries(sqrt(z), (z, -5 - 5j, 5 + 5j))
    assert isinstance(s.rendering_kw, dict)

    s = ComplexDomainColoringInteractiveSeries(
        sqrt(z), (z, -5 - 5j, 5 + 5j))
    assert isinstance(s.rendering_kw, dict)


def test_use_quiver_solid_color():
    u, x, y = symbols("u, x, y")

    # verify that the attribute `use_quiver_solid_color` is present

    s = Vector2DSeries(-y, x, (x, -3, 3), (y, -4, 4))
    assert isinstance(s.rendering_kw, dict)
    assert hasattr(s, "use_quiver_solid_color")
    assert s.use_quiver_solid_color

    s = Vector2DInteractiveSeries(
        [u * cos(y), u * sin(x)], [(x, -5, 5), (y, -5, 5)], params={u: 1})
    assert isinstance(s.rendering_kw, dict)
    assert hasattr(s, "use_quiver_solid_color")
    assert s.use_quiver_solid_color


def test_data_shape():
    # Verify that the series produces the correct data shape when the input
    # expression is a number.
    u, x, y, z = symbols("u, x:z")

    # scalar expression: it should return a numpy ones array
    s = LineOver1DRangeSeries(1, (x, -5, 5))
    xx, yy = s.get_data()
    assert len(xx) == len(yy)
    assert np.all(yy == 1)

    s = LineOver1DRangeSeries(1, (x, -5, 5), adaptive=False, n=10)
    xx, yy = s.get_data()
    assert len(xx) == len(yy) == 10
    assert np.all(yy == 1)

    s = AbsArgLineSeries(1, (x, -5, 5))
    xx, _abs, _arg = s.get_data()
    assert len(xx) == len(_abs) == len(_arg)
    assert np.all(_abs == 1)

    s = AbsArgLineSeries(1, (x, -5, 5), adaptive=False, n=10)
    xx, _abs, _arg = s.get_data()
    assert len(xx) == len(_abs) == len(_arg) == 10
    assert np.all(_abs == 1)

    s = Parametric2DLineSeries(sin(x), 1, (x, 0, pi))
    xx, yy, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(param))
    assert np.all(yy == 1)

    s = Parametric2DLineSeries(1, sin(x), (x, 0, pi))
    xx, yy, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(param))
    assert np.all(xx == 1)

    s = Parametric2DLineSeries(sin(x), 1, (x, 0, pi), adaptive=False)
    xx, yy, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(param))
    assert np.all(yy == 1)

    s = Parametric2DLineSeries(1, sin(x), (x, 0, pi), adaptive=False)
    xx, yy, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(param))
    assert np.all(xx == 1)

    s = Parametric3DLineSeries(cos(x), sin(x), 1, (x, 0, 2 * pi))
    xx, yy, zz, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(zz)) and (len(xx) == len(param))
    assert np.all(zz == 1)

    s = Parametric3DLineSeries(cos(x), 1, x, (x, 0, 2 * pi))
    xx, yy, zz, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(zz)) and (len(xx) == len(param))
    assert np.all(yy == 1)

    s = Parametric3DLineSeries(1, sin(x), x, (x, 0, 2 * pi))
    xx, yy, zz, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(zz)) and (len(xx) == len(param))
    assert np.all(xx == 1)

    s = SurfaceOver2DRangeSeries(1, (x, -2, 2), (y, -3, 3))
    xx, yy, zz = s.get_data()
    assert (xx.shape == yy.shape) and (xx.shape == zz.shape)
    assert np.all(zz == 1)

    s = Implicit3DSeries(x**2 + y**3 - z**2,
        (x, -2, 2), (y, -3, 3), (z, -4, 4),
        n1=5, n2=8, n3=10)
    xx, yy, zz, f = s.get_data()
    assert f.shape == xx.shape == yy.shape == zz.shape == (5, 8, 10)

    s = ParametricSurfaceSeries(1, x, y, (x, 0, 1), (y, 0, 1))
    xx, yy, zz, uu, vv = s.get_data()
    assert xx.shape == yy.shape == zz.shape == uu.shape == vv.shape
    assert np.all(xx == 1)

    s = ParametricSurfaceSeries(1, 1, y, (x, 0, 1), (y, 0, 1))
    xx, yy, zz, uu, vv = s.get_data()
    assert xx.shape == yy.shape == zz.shape == uu.shape == vv.shape
    assert np.all(yy == 1)

    s = ParametricSurfaceSeries(x, 1, 1, (x, 0, 1), (y, 0, 1))
    xx, yy, zz, uu, vv = s.get_data()
    assert xx.shape == yy.shape == zz.shape == uu.shape == vv.shape
    assert np.all(zz == 1)

    s = AbsArgLineSeries(1, (x, -5, 5), modules=None)
    xx, yy, aa = s.get_data()
    assert (xx.shape == yy.shape) and (xx.shape == aa.shape)
    assert np.all(aa == 0)

    s = AbsArgLineSeries(1, (x, -5, 5), modules="mpmath")
    xx, yy, aa = s.get_data()
    assert (xx.shape == yy.shape) and (xx.shape == aa.shape)
    assert np.all(aa == 0)

    s = ComplexSurfaceSeries(1, (x, -5 - 2 * I, 5 + 2 * I),
        n1=10, n2=10, modules=None)
    xx, yy, zz = s.get_data()
    assert (xx.shape == yy.shape) and (xx.shape == zz.shape)
    assert np.all(zz == 1)

    s = ComplexSurfaceSeries(1, (x, -5 - 2 * I, 5 + 2 * I),
        n1=10, n2=10, modules="mpmath")
    xx, yy, zz = s.get_data()
    assert (xx.shape == yy.shape) and (xx.shape == zz.shape)
    assert np.all(zz == 1)

    s = ComplexDomainColoringSeries(1, (x, -5 - 2 * I, 5 + 2 * I),
        n1=10, n2=10, modules=None)
    rr, ii, mag, arg, colors, _ = s.get_data()
    assert (rr.shape == ii.shape) and (rr.shape[:2] == colors.shape[:2])
    assert (rr.shape == mag.shape) and (rr.shape == arg.shape)

    s = ComplexDomainColoringSeries(1, (x, -5 - 2 * I, 5 + 2 * I),
        n1=10, n2=10, modules="mpmath")
    rr, ii, mag, arg, colors, _ = s.get_data()
    assert (rr.shape == ii.shape) and (rr.shape[:2] == colors.shape[:2])
    assert (rr.shape == mag.shape) and (rr.shape == arg.shape)

    # Corresponds to LineOver1DRangeSeries
    s = InteractiveSeries([S.One], [Tuple(x, -5, 5)])
    s.params = dict()
    xx, yy = s.get_data()
    assert len(xx) == len(yy)
    assert np.all(yy == 1)

    # Corresponds to Parametric2DLineSeries
    s = InteractiveSeries([S.One, sin(x)], [Tuple(x, 0, pi)])
    s.params = dict()
    xx, yy, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(param))
    assert np.all(xx == 1)

    s = InteractiveSeries([sin(x), S.One], [Tuple(x, 0, pi)])
    s.params = dict()
    xx, yy, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(param))
    assert np.all(yy == 1)

    # Corresponds to Parametric3DLineSeries
    s = InteractiveSeries([cos(x), sin(x), S.One], [(x, 0, 2 * pi)])
    s.params = dict()
    xx, yy, zz, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(param)) and (len(xx) == len(zz))
    assert np.all(zz == 1)

    s = InteractiveSeries([S.One, sin(x), x], [(x, 0, 2 * pi)])
    s.params = dict()
    xx, yy, zz, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(param)) and (len(xx) == len(zz))
    assert np.all(xx == 1)

    s = InteractiveSeries([cos(x), S.One, x], [(x, 0, 2 * pi)])
    s.params = dict()
    xx, yy, zz, param = s.get_data()
    assert (len(xx) == len(yy)) and (len(xx) == len(param)) and (len(xx) == len(zz))
    assert np.all(yy == 1)

    # Corresponds to SurfaceOver2DRangeSeries
    s = InteractiveSeries([S.One], [(x, -2, 2), (y, -3, 3)])
    s.params = dict()
    xx, yy, zz = s.get_data()
    assert (xx.shape == yy.shape) and (xx.shape == zz.shape)
    assert np.all(zz == 1)

    # Corresponds to ParametricSurfaceSeries
    s = InteractiveSeries([S.One, x, y], [(x, 0, 1), (y, 0, 1)])
    s.params = dict()
    xx, yy, zz, uu, vv = s.get_data()
    assert xx.shape == yy.shape == zz.shape == uu.shape == vv.shape
    assert np.all(xx == 1)

    s = InteractiveSeries([x, S.One, y], [(x, 0, 1), (y, 0, 1)])
    s.params = dict()
    xx, yy, zz, uu, vv = s.get_data()
    assert xx.shape == yy.shape == zz.shape == uu.shape == vv.shape
    assert np.all(yy == 1)

    s = InteractiveSeries([x, y, S.One], [(x, 0, 1), (y, 0, 1)])
    s.params = dict()
    xx, yy, zz, uu, vv = s.get_data()
    assert xx.shape == yy.shape == zz.shape == uu.shape == vv.shape
    assert np.all(zz == 1)

    s = ComplexSurfaceInteractiveSeries(S.One, (x, -5-2j, 5+2j), modules=None)
    s.params = dict()
    xx, yy, zz = s.get_data()
    assert (xx.shape == yy.shape) and (xx.shape == zz.shape)
    assert np.all(zz == 1)

def test_only_integers():
    x, y, u, v = symbols("x, y, u, v")

    s = LineOver1DRangeSeries(sin(x), (x, -5.5, 4.5), "",
        adaptive=False, only_integers=True)
    xx, _ = s.get_data()
    assert len(xx) == 10
    assert xx[0] == -5 and xx[-1] == 4

    s = AbsArgLineSeries(sqrt(x), (x, -5.5, 4.5), "",
        adaptive=False, only_integers=True)
    xx, _, _ = s.get_data()
    assert len(xx) == 10
    assert xx[0] == -5 and xx[-1] == 4

    s = Parametric2DLineSeries(cos(x), sin(x), (x, 0, 2 * pi), "",
        adaptive=False, only_integers=True)
    _, _, p = s.get_data()
    assert len(p) == 7
    assert p[0] == 0 and p[-1] == 6

    s = Parametric3DLineSeries(cos(x), sin(x), x, (x, 0, 2 * pi), "",
        adaptive=False, only_integers=True)
    _, _, _, p = s.get_data()
    assert len(p) == 7
    assert p[0] == 0 and p[-1] == 6

    s = SurfaceOver2DRangeSeries(cos(x**2 + y**2), (x, -5.5, 5.5),
        (y, -3.5, 3.5), "",
        adaptive=False, only_integers=True)
    xx, yy, _ = s.get_data()
    assert xx.shape == yy.shape == (7, 11)
    assert np.allclose(xx[:, 0] - (-5) * np.ones(7), 0)
    assert np.allclose(xx[0, :] - np.linspace(-5, 5, 11), 0)
    assert np.allclose(yy[:, 0] - np.linspace(-3, 3, 7), 0)
    assert np.allclose(yy[0, :] - (-3) * np.ones(11), 0)

    r = 2 + sin(7 * u + 5 * v)
    expr = (
        r * cos(u) * sin(v),
        r * sin(u) * sin(v),
        r * cos(v)
    )
    s = ParametricSurfaceSeries(*expr, (u, 0, 2 * pi), (v, 0, pi), "",
        adaptive=False, only_integers=True)
    xx, yy, zz, uu, vv = s.get_data()
    assert xx.shape == yy.shape == zz.shape == uu.shape == vv.shape == (4, 7)

    s = ComplexSurfaceSeries(sqrt(x), (x, -3.5 - 2.5j, 3.5 + 2.5j), "",
        adaptive=False, only_integers=True)
    xx, yy, zz = s.get_data()
    assert xx.shape == yy.shape == zz.shape == (5, 7)
    assert xx[0, 0] == -3 and xx[-1, -1] == 3
    assert yy[0, 0] == -2 and yy[-1, -1] == 2

    s = ComplexDomainColoringSeries(sqrt(x), (x, -3.5 - 2.5j, 3.5 + 2.5j), "",
        adaptive=False, only_integers=True)
    xx, yy, zz, aa, _, _ = s.get_data()
    assert xx.shape == yy.shape == zz.shape == aa.shape == (5, 7)
    assert xx[0, 0] == -3 and xx[-1, -1] == 3
    assert yy[0, 0] == -2 and yy[-1, -1] == 2

    # only_integers also works with scalar expressions
    s = LineOver1DRangeSeries(1, (x, -5.5, 4.5), "",
        adaptive=False, only_integers=True)
    xx, _ = s.get_data()
    assert len(xx) == 10
    assert xx[0] == -5 and xx[-1] == 4

    s = Parametric2DLineSeries(cos(x), 1, (x, 0, 2 * pi), "",
        adaptive=False, only_integers=True)
    _, _, p = s.get_data()
    assert len(p) == 7
    assert p[0] == 0 and p[-1] == 6

    s = SurfaceOver2DRangeSeries(1, (x, -5.5, 5.5), (y, -3.5, 3.5), "",
        adaptive=False, only_integers=True)
    xx, yy, _ = s.get_data()
    assert xx.shape == yy.shape == (7, 11)
    assert np.allclose(xx[:, 0] - (-5) * np.ones(7), 0)
    assert np.allclose(xx[0, :] - np.linspace(-5, 5, 11), 0)
    assert np.allclose(yy[:, 0] - np.linspace(-3, 3, 7), 0)
    assert np.allclose(yy[0, :] - (-3) * np.ones(11), 0)

    r = 2 + sin(7 * u + 5 * v)
    expr = (
        r * cos(u) * sin(v),
        1,
        r * cos(v)
    )
    s = ParametricSurfaceSeries(*expr, (u, 0, 2 * pi), (v, 0, pi), "",
        adaptive=False, only_integers=True)
    xx, yy, zz, uu, vv = s.get_data()
    assert xx.shape == yy.shape == zz.shape == uu.shape == vv.shape == (4, 7)

    s = ComplexSurfaceSeries(1, (x, -3.5 - 2.5j, 3.5 + 2.5j), "",
        adaptive=False, only_integers=True)
    xx, yy, zz = s.get_data()
    assert xx.shape == yy.shape == zz.shape == (5, 7)
    assert xx[0, 0] == -3 and xx[-1, -1] == 3
    assert yy[0, 0] == -2 and yy[-1, -1] == 2

    s = ComplexDomainColoringSeries(1, (x, -3.5 - 2.5j, 3.5 + 2.5j), "",
        adaptive=False, only_integers=True)
    xx, yy, zz, aa, _, _ = s.get_data()
    assert xx.shape == yy.shape == zz.shape == aa.shape == (5, 7)
    assert xx[0, 0] == -3 and xx[-1, -1] == 3
    assert yy[0, 0] == -2 and yy[-1, -1] == 2

    s = Vector2DSeries(-y, x, (x, -3.5, 3.5), (y, -4.5, 4.5), "",
        only_integers=True)
    xx, yy, uu, vv = s.get_data()
    assert xx.shape == yy.shape == uu.shape == vv.shape == (9, 7)
    assert xx[0, 0] == -3 and xx[-1, -1] == 3
    assert yy[0, 0] == -4 and yy[-1, -1] == 4

    # only_integers also works with Interactive series
    s = LineInteractiveSeries([sin(x * y)], [(x, -5.5, 4.5)], "",
        params={y: 1}, only_integers=True)
    xx, _ = s.get_data()
    assert len(xx) == 10
    assert xx[0] == -5 and xx[-1] == 4

    s = AbsArgLineInteractiveSeries([sqrt(x * y)], [(x, -5.5, 4.5)], "",
        params={y: 1}, only_integers=True)
    xx, _, _ = s.get_data()
    assert len(xx) == 10
    assert xx[0] == -5 and xx[-1] == 4

    s = SurfaceInteractiveSeries(
        [u * sin(x * y)], [(x, -5.5, 4.5), (y, -6.5, 6.5)],
        "", params={u: 1}, only_integers=True)
    xx, yy, zz = s.get_data()
    assert xx.shape == yy.shape == zz.shape == (13, 10)
    assert xx[0, 0] == -5 and xx[-1, -1] == 4
    assert yy[0, 0] == -6 and yy[-1, -1] == 6

    s = ComplexSurfaceInteractiveSeries(
        u * sqrt(x), (x, -3.5 - 2.5j, 3.5 + 2.5j), "",
        params={u: 1}, only_integers=True)
    xx, yy, zz = s.get_data()
    assert xx.shape == yy.shape == zz.shape == (5, 7)
    assert xx[0, 0] == -3 and xx[-1, -1] == 3
    assert yy[0, 0] == -2 and yy[-1, -1] == 2

    s = Vector2DInteractiveSeries([-u * y, x], [(x, -3.5, 3.5), (y, -4.5, 4.5)],
        "", params={u: 1}, only_integers=True)
    xx, yy, uu, vv = s.get_data()
    assert xx.shape == yy.shape == uu.shape == vv.shape == (9, 7)
    assert xx[0, 0] == -3 and xx[-1, -1] == 3
    assert yy[0, 0] == -4 and yy[-1, -1] == 4


def test_is_point_is_filled():
    # verify that `is_point` and `is_filled` are attributes and that they
    # they receive the correct values

    x, u = symbols("x, u")

    s = LineOver1DRangeSeries(cos(x), (x, -5, 5), "",
        is_point=False, is_filled=True)
    assert (not s.is_point) and s.is_filled
    s = LineOver1DRangeSeries(cos(x), (x, -5, 5), "",
        is_point=True, is_filled=False)
    assert s.is_point and (not s.is_filled)

    s = AbsArgLineSeries(cos(x), (x, -5, 5), "",
        is_point=False, is_filled=True)
    assert (not s.is_point) and s.is_filled
    s = AbsArgLineSeries(cos(x), (x, -5, 5), "",
        is_point=True, is_filled=False)
    assert s.is_point and (not s.is_filled)

    s = List2DSeries([0, 1, 2], [3, 4, 5],
        is_point=False, is_filled=True)
    assert (not s.is_point) and s.is_filled
    s = List2DSeries([0, 1, 2], [3, 4, 5],
        is_point=True, is_filled=False)
    assert s.is_point and (not s.is_filled)

    s = Parametric2DLineSeries(cos(x), sin(x), (x, -5, 5),
        is_point=False, is_filled=True)
    assert (not s.is_point) and s.is_filled
    s = Parametric2DLineSeries(cos(x), sin(x), (x, -5, 5),
        is_point=True, is_filled=False)
    assert s.is_point and (not s.is_filled)

    s = Parametric3DLineSeries(cos(x), sin(x), x, (x, -5, 5),
        is_point=False, is_filled=True)
    assert (not s.is_point) and s.is_filled
    s = Parametric3DLineSeries(cos(x), sin(x), x, (x, -5, 5),
        is_point=True, is_filled=False)
    assert s.is_point and (not s.is_filled)

    s = ComplexPointSeries([1 + 2 * I, 3 + 4 * I],
        is_point=False, is_filled=True)
    assert (not s.is_point) and s.is_filled
    s = ComplexPointSeries([1 + 2 * I, 3 + 4 * I],
        is_point=True, is_filled=False)
    assert s.is_point and (not s.is_filled)

    s = LineInteractiveSeries([u * cos(x)], [(x, -5, 5)], "",
        params={u: 1}, is_point=False, is_filled=True)
    assert (not s.is_point) and s.is_filled
    s = LineInteractiveSeries([u * cos(x)], [(x, -5, 5)], "",
        params={u: 1}, is_point=True, is_filled=False)
    assert s.is_point and (not s.is_filled)

    s = AbsArgLineInteractiveSeries([u * cos(x)], [(x, -5, 5)], "",
        params={u: 1}, is_point=False, is_filled=True)
    assert (not s.is_point) and s.is_filled
    s = AbsArgLineInteractiveSeries([u * cos(x)], [(x, -5, 5)], "",
        params={u: 1}, is_point=True, is_filled=False)
    assert s.is_point and (not s.is_filled)

    s = Parametric2DLineInteractiveSeries([u * cos(x), sin(x)],
        [(x, -5, 5)], "", params={u: 1}, is_point=False, is_filled=True)
    assert (not s.is_point) and s.is_filled
    s = Parametric2DLineInteractiveSeries([u * cos(x), sin(x)],
        [(x, -5, 5)], "", params={u: 1}, is_point=True, is_filled=False)
    assert s.is_point and (not s.is_filled)

    s = Parametric3DLineInteractiveSeries([u * cos(x), sin(x), x],
        [(x, -5, 5)], "", params={u: 1}, is_point=False, is_filled=True)
    assert (not s.is_point) and s.is_filled
    s = Parametric3DLineInteractiveSeries([u * cos(x), sin(x), x],
        [(x, -5, 5)], "", params={u: 1}, is_point=True, is_filled=False)
    assert s.is_point and (not s.is_filled)

    s = ComplexPointInteractiveSeries([1 + 2 * I, 3 + 4 * I],
        is_point=False, is_filled=True)
    assert (not s.is_point) and s.is_filled
    s = ComplexPointInteractiveSeries([1 + 2 * I, 3 + 4 * I],
        is_point=True, is_filled=False)
    assert s.is_point and (not s.is_filled)

def test_geometry_is_filled():
    # verify that GeometrySeries exposes the is_filled attribute
    x = symbols("x")

    s = GeometrySeries(Circle(Point(0, 0), 5), is_filled=False)
    assert not s.is_filled

    s = GeometrySeries(Circle(Point(0, 0), 5), is_filled=True)
    assert s.is_filled

    s = GeometryInteractiveSeries([Circle(Point(x, 0), 5)], [],
        params={x: 1}, is_filled=False)
    assert not s.is_filled

    s = GeometryInteractiveSeries([Circle(Point(x, 0), 5)], [],
        params={x: 1}, is_filled=True)
    assert s.is_filled


def test_steps():
    x, u = symbols("x, u")

    def do_test(s1, s2):
        if not s1.is_parametric:
            xx1, _ = s1.get_data()
            xx2, _ = s2.get_data()
        elif s1.is_parametric and s1.is_2Dline:
            xx1, _, _ = s1.get_data()
            xx2, _, _ = s2.get_data()
        else:
            xx1, _, _, _ = s1.get_data()
            xx2, _, _, _ = s2.get_data()
        assert len(xx1) != len(xx2)

    s1 = LineOver1DRangeSeries(cos(x), (x, -5, 5), "",
        adaptive=False, n=40, steps=False)
    s2 = LineOver1DRangeSeries(cos(x), (x, -5, 5), "",
        adaptive=False, n=40, steps=True)
    do_test(s1, s2)

    s1 = AbsArgLineSeries(cos(x), (x, -5, 5), "",
        adaptive=False, n=40, steps=False)
    s2 = AbsArgLineSeries(cos(x), (x, -5, 5), "",
        adaptive=False, n=40, steps=True)
    do_test(s1, s2)

    s1 = List2DSeries([0, 1, 2], [3, 4, 5],
        adaptive=False, n=40, steps=False)
    s2 = List2DSeries([0, 1, 2], [3, 4, 5],
        adaptive=False, n=40, steps=True)
    do_test(s1, s2)

    s1 = Parametric2DLineSeries(cos(x), sin(x), (x, -5, 5),
        adaptive=False, n=40, steps=False)
    s2 = Parametric2DLineSeries(cos(x), sin(x), (x, -5, 5),
        adaptive=False, n=40, steps=True)
    do_test(s1, s2)

    s1 = Parametric3DLineSeries(cos(x), sin(x), x, (x, -5, 5),
        adaptive=False, n=40, steps=False)
    s2 = Parametric3DLineSeries(cos(x), sin(x), x, (x, -5, 5),
        adaptive=False, n=40, steps=True)
    do_test(s1, s2)

    s1 = ComplexPointSeries([1 + 2 * I, 3 + 4 * I],
        adaptive=False, n=40, steps=False)
    s2 = ComplexPointSeries([1 + 2 * I, 3 + 4 * I],
        adaptive=False, n=40, steps=True)
    do_test(s1, s2)

    s1 = LineInteractiveSeries([u * cos(x)], [(x, -5, 5)], "",
        params={u: 1}, n1=40, steps=False)
    s2 = LineInteractiveSeries([u * cos(x)], [(x, -5, 5)], "",
        params={u: 1}, n1=40, steps=True)
    do_test(s1, s2)

    s1 = AbsArgLineInteractiveSeries([u * cos(x)], [(x, -5, 5)], "",
        params={u: 1}, n1=40, steps=False)
    s2 = AbsArgLineInteractiveSeries([u * cos(x)], [(x, -5, 5)], "",
        params={u: 1}, n1=40, steps=True)
    do_test(s1, s2)

    s1 = Parametric2DLineInteractiveSeries([u * cos(x), sin(x)],
        [(x, -5, 5)], "", params={u: 1}, n1=40, steps=False)
    s2 = Parametric2DLineInteractiveSeries([u * cos(x), sin(x)],
        [(x, -5, 5)], "", params={u: 1}, n1=40, steps=True)
    do_test(s1, s2)

    s1 = Parametric3DLineInteractiveSeries([u * cos(x), sin(x), x],
        [(x, -5, 5)], "", params={u: 1}, n1=40, steps=False)
    s2 = Parametric3DLineInteractiveSeries([u * cos(x), sin(x), x],
        [(x, -5, 5)], "", params={u: 1}, n1=40, steps=True)
    do_test(s1, s2)

    s1 = ComplexPointInteractiveSeries([1 + 2 * I, 3 + 4 * I],
        n1=40, steps=False)
    s2 = ComplexPointInteractiveSeries([1 + 2 * I, 3 + 4 * I],
        n1=40, steps=True)
    do_test(s1, s2)


def test_interactive():
    u, x, y, z = symbols("u, x:z")

    # verify that InteractiveSeries produces the same numerical data as their
    # corresponding non-interactive series.
    def do_test(data1, data2):
        assert len(data1) == len(data2)
        for d1, d2 in zip(data1, data2):
            assert np.allclose(d1, d2)

    s1 = InteractiveSeries([u * cos(x)], [(x, -5, 5)], "", params={u: 1}, n1=50)
    s2 = LineOver1DRangeSeries(cos(x), (x, -5, 5), "", adaptive=False, n=50)
    do_test(s1.get_data(), s2.get_data())

    s1 = InteractiveSeries([u * cos(x)], [(x, -5, 5)], "",
        params={u: 1}, n1=50, absarg=True)
    s2 = AbsArgLineSeries(cos(x), (x, -5, 5), "", adaptive=False, n=50)
    do_test(s1.get_data(), s2.get_data())

    s1 = InteractiveSeries(
        [u * cos(x), u * sin(x)], [(x, -5, 5)], "", params={u: 1}, n1=50)
    s2 = Parametric2DLineSeries(cos(x), sin(x), (x, -5, 5), "",
        adaptive=False, n=50)
    do_test(s1.get_data(), s2.get_data())

    s1 = InteractiveSeries(
        [u * cos(x), u * sin(x), u * x], [(x, -5, 5)], "",
        params={u: 1}, n1=50)
    s2 = Parametric3DLineSeries(cos(x), sin(x), x, (x, -5, 5), "",
        adaptive=False, n=50)
    do_test(s1.get_data(), s2.get_data())

    s1 = InteractiveSeries([cos(x ** 2 + y ** 2)], [(x, -3, 3), (y, -3, 3)],
        "", params={u: 1}, n1=50, n2=50,
    )
    s2 = SurfaceOver2DRangeSeries(
        cos(x ** 2 + y ** 2), (x, -3, 3), (y, -3, 3), "",
        adaptive=False, n1=50, n2=50)
    do_test(s1.get_data(), s2.get_data())

    s1 = InteractiveSeries(
        [cos(x + y), sin(x + y), x - y], [(x, -3, 3), (y, -3, 3)], "",
        params={u: 1}, n1=50, n2=50,)
    s2 = ParametricSurfaceSeries(
        cos(x + y), sin(x + y), x - y, (x, -3, 3), (y, -3, 3), "",
        adaptive=False, n1=50, n2=50,)
    do_test(s1.get_data(), s2.get_data())

    s1 = InteractiveSeries(
        [-u * y, u * x], [(x, -3, 3), (y, -2, 2)], "",
        params={u: 1}, n1=15, n2=15)
    s2 = Vector2DSeries(-y, x, (x, -3, 3), (y, -2, 2), "", n1=15, n2=15)
    do_test(s1.get_data(), s2.get_data())

    s1 = InteractiveSeries(
        [u * z, -u * y, u * x],
        [(x, -3, 3), (y, -2, 2), (z, -1, 1)], "",
        params={u: 1}, n1=15, n2=15, n3=15,)
    s2 = Vector3DSeries(
        z, -y, x, (x, -3, 3), (y, -2, 2), (z, -1, 1), "", n1=15, n2=15, n3=15)
    do_test(s1.get_data(), s2.get_data())

    s1 = InteractiveSeries(
        [u * z, -u * y, u * x],
        [(x, -3, 3), (y, -2, 2), (z, -1, 1)], "",
        params={u: 1}, slice=Plane((-1, 0, 0), (1, 0, 0)),
        n1=15, n2=15, n3=15,)
    s2 = SliceVector3DSeries(
        Plane((-1, 0, 0), (1, 0, 0)),
        z, -y, x,
        (x, -3, 3), (y, -2, 2), (z, -1, 1), "",
        n1=15, n2=15, n3=15)
    do_test(s1.get_data(), s2.get_data())

    ### Test InteractiveSeries and ComplexInteractiveSeries with complex
    ### functions

    # complex function evaluated over a real line with numpy
    s1 = InteractiveSeries(
        [(z ** 2 + 1) / (z ** 2 - 1)], [(z, -3, 3)], "",
        n1=50, modules=None, absarg=True)
    s2 = AbsArgLineSeries(
        (z ** 2 + 1) / (z ** 2 - 1), (z, -3, 3), "", adaptive=False,
        n=50, modules=None)
    do_test(s1.get_data(), s2.get_data())

    # complex function evaluated over a real line with mpmath
    s1 = InteractiveSeries(
        [(z ** 2 + 1) / (z ** 2 - 1)], [(z, -3, 3)], "",
        n1=11, modules="mpmath", absarg=True)
    s2 = AbsArgLineSeries(
        (z ** 2 + 1) / (z ** 2 - 1), (z, -3, 3), "", adaptive=False,
        n=11, modules="mpmath")
    do_test(s1.get_data(), s2.get_data())

    # real part of a complex function evaluated over a real line with numpy
    expr = re((z ** 2 + 1) / (z ** 2 - 1))
    s1 = InteractiveSeries([expr], [(z, -3, 3)], "", n1=50, modules=None)
    s2 = LineOver1DRangeSeries(expr, (z, -3, 3), "",
        adaptive=False, n=50, modules=None)
    do_test(s1.get_data(), s2.get_data())

    # real part of a complex function evaluated over a real line with mpmath
    expr = re((z ** 2 + 1) / (z ** 2 - 1))
    s1 = InteractiveSeries([expr], [(z, -3, 3)], "",
        n1=50, modules="mpmath")
    s2 = LineOver1DRangeSeries(expr, (z, -3, 3), "",
        adaptive=False, n=50, modules="mpmath")
    do_test(s1.get_data(), s2.get_data())

    # surface over a complex domain
    s1 = ComplexSurfaceInteractiveSeries(
        u * (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I), "",
        n1=20, n2=20, params = {u: 1}, modules=None)
    s2 = ComplexSurfaceSeries(
        (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I), "",
        n1=20, n2=20, modules=None)
    do_test(s1.get_data(), s2.get_data())

    s1 = ComplexSurfaceInteractiveSeries(
        u * (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I), "",
        n1=20, n2=20, params = {u: 1}, modules="mpmath")
    s2 = ComplexSurfaceSeries(
        (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I), "",
        n1=20, n2=20, modules="mpmath")
    do_test(s1.get_data(), s2.get_data())

    # domain coloring or 3D
    s1 = ComplexDomainColoringInteractiveSeries(
        u * (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I), "",
        n1=20, n2=20, params = {u: 1}, modules=None)
    s2 = ComplexDomainColoringSeries(
        (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I), "",
        n1=20, n2=20, modules=None)
    do_test(s1.get_data(), s2.get_data())

    s1 = ComplexDomainColoringInteractiveSeries(
        u * (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I), "",
        n1=20, n2=20, params = {u: 1}, modules="mpmath")
    s2 = ComplexDomainColoringSeries(
        (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I), "",
        n1=20, n2=20, modules="mpmath")
    do_test(s1.get_data(), s2.get_data())


def test_mpmath():
    # test that the argument of complex functions evaluated with mpmath
    # might be different than the one computed with Numpy (different
    # behaviour at branch cuts)
    z, u = symbols("z, u")

    s1 = LineOver1DRangeSeries(im(sqrt(-z)), (z, 1e-03, 5),
        adaptive=True, modules=None)
    s2 = LineOver1DRangeSeries(im(sqrt(-z)), (z, 1e-03, 5),
        adaptive=True, modules="mpmath")
    xx1, yy1 = s1.get_data()
    xx2, yy2 = s2.get_data()
    assert np.all(yy1 < 0)
    assert np.all(yy2 > 0)

    s1 = LineOver1DRangeSeries(im(sqrt(-z)), (z, -5, 5),
        adaptive=False, n=20, modules=None)
    s2 = LineOver1DRangeSeries(im(sqrt(-z)), (z, -5, 5),
        adaptive=False, n=20, modules="mpmath")
    xx1, yy1 = s1.get_data()
    xx2, yy2 = s2.get_data()
    assert np.allclose(xx1, xx2)
    assert not np.allclose(yy1, yy2)

    s1 = LineInteractiveSeries([im(sqrt(-z))], [(z, -5, 5)],
        adaptive=False, n=21, modules=None)
    s2 = LineInteractiveSeries([im(sqrt(-z))], [(z, -5, 5)],
        adaptive=False, n=21, modules="mpmath")
    xx1, yy1 = s1.get_data()
    xx2, yy2 = s2.get_data()
    assert np.allclose(xx1, xx2)
    assert not np.allclose(yy1, yy2)

    # here, there will be different values at x+0j for positive x
    s1 = ComplexSurfaceSeries(arg(sqrt(-z)), (z, -3 - 3j, 3 + 3j),
        n1=21, n2=21, modules=None)
    s2 = ComplexSurfaceSeries(arg(sqrt(-z)), (z, -3 - 3j, 3 + 3j),
        n1=21, n2=21, modules="mpmath")
    xx1, yy1, zz1 = s1.get_data()
    xx2, yy2, zz2 = s2.get_data()
    assert np.allclose(xx1, xx2)
    assert np.allclose(yy1, yy2)
    assert not np.allclose(zz1, zz2)

    s1 = ComplexDomainColoringSeries(arg(sqrt(-z)), (z, -3 - 3j, 3 + 3j),
        n1=21, n2=21, coloring="a", modules=None)
    s2 = ComplexDomainColoringSeries(arg(sqrt(-z)), (z, -3 - 3j, 3 + 3j),
        n1=21, n2=21, coloring="a", modules="mpmath")
    xx1, yy1, _, aa1, ii1, _ = s1.get_data()
    xx2, yy2, _, aa2, ii2, _ = s2.get_data()
    assert np.allclose(xx1, xx2)
    assert np.allclose(yy1, yy2)
    assert not np.allclose(aa1, aa2)
    assert not np.allclose(ii1, ii2)


def test_str():
    u, x, y, z = symbols("u, x:z")

    s = LineOver1DRangeSeries(cos(x), (x, -4, 3), "test")
    assert str(s) == "cartesian line: cos(x) for x over (-4.0, 3.0)"

    s = LineInteractiveSeries([cos(u * x)], [(x, -4, 3)], "test",
        params={u: 1})
    assert str(s) == "interactive cartesian line: cos(u*x) with ranges (x, -4.0, 3.0) and parameters (u,)"

    s = AbsArgLineSeries(sqrt(x), (x, -5 + 2j, 5 + 2j), "test")
    assert str(s) == "cartesian abs-arg line: sqrt(x) for x over ((-5+2j), (5+2j))"

    s = AbsArgLineInteractiveSeries([cos(u * x)], [(x, -4, 3)], "test",
        params={u: 1})
    assert str(s) == "interactive cartesian abs-arg line: cos(u*x) with ranges (x, (-4+0j), (3+0j)) and parameters (u,)"

    s = Parametric2DLineSeries(cos(x), sin(x), (x, -4, 3), "test")
    assert str(s) == "parametric cartesian line: (cos(x), sin(x)) for x over (-4.0, 3.0)"

    s = Parametric2DLineInteractiveSeries([cos(u * x), sin(x)], [(x, -4, 3)],
        "test", params={u: 1})
    assert str(s) == "interactive parametric cartesian line: (cos(u*x), sin(x)) with ranges (x, -4.0, 3.0) and parameters (u,)"

    s = Parametric3DLineSeries(cos(x), sin(x), x, (x, -4, 3), "test")
    assert str(s) == "3D parametric cartesian line: (cos(x), sin(x), x) for x over (-4.0, 3.0)"

    s = Parametric3DLineInteractiveSeries([cos(u*x), sin(x), x], [(x, -4, 3)], "test", params={u: 1})
    assert str(s) == "interactive 3D parametric cartesian line: (cos(u*x), sin(x), x) with ranges (x, -4.0, 3.0) and parameters (u,)"

    s = SurfaceOver2DRangeSeries(cos(x * y), (x, -4, 3), (y, -2, 5), "test")
    assert str(s) == "cartesian surface: cos(x*y) for x over (-4.0, 3.0) and y over (-2.0, 5.0)"

    s = SurfaceInteractiveSeries([cos(u * x * y)], [(x, -4, 3), (y, -2, 5)], "test", params={u: 1})
    assert str(s) == "interactive cartesian surface: cos(u*x*y) with ranges (x, -4.0, 3.0), (y, -2.0, 5.0) and parameters (u,)"

    s = ContourSeries(cos(x * y), (x, -4, 3), (y, -2, 5), "test")
    assert str(s) == "contour: cos(x*y) for x over (-4.0, 3.0) and y over (-2.0, 5.0)"

    s = ContourInteractiveSeries([cos(u * x * y)], [(x, -4, 3), (y, -2, 5)], "test", params={u: 1})
    assert str(s) == "interactive contour: cos(u*x*y) with ranges (x, -4.0, 3.0), (y, -2.0, 5.0) and parameters (u,)"

    s = ParametricSurfaceSeries(cos(x * y), sin(x * y), x * y,
        (x, -4, 3), (y, -2, 5), "test")
    assert str(s) == "parametric cartesian surface: (cos(x*y), sin(x*y), x*y) for x over (-4.0, 3.0) and y over (-2.0, 5.0)"

    s = ParametricSurfaceInteractiveSeries([cos(u * x * y), sin(x * y), x * y],
        [(x, -4, 3), (y, -2, 5)], "test", params={u: 1})
    assert str(s) == "interactive parametric cartesian surface: (cos(u*x*y), sin(x*y), x*y) with ranges (x, -4.0, 3.0), (y, -2.0, 5.0) and parameters (u,)"

    s = ImplicitSeries(x < y, (x, -5, 4), (y, -3, 2), "test")
    assert str(s) == "Implicit expression: x < y for x over (-5.0, 4.0) and y over (-3.0, 2.0)"

    s = ComplexPointSeries(2 + 3 * I, "test")
    assert str(s) == "complex points: (2 + 3*I,)"

    s = ComplexPointSeries([2 + 3 * I, 4 * I], "test")
    assert str(s) == "complex points: (2 + 3*I, 4*I)"

    s = ComplexPointInteractiveSeries([2 + 3 * I * y], "test", params={y: 1})
    assert str(s) == "interactive complex points: (3*I*y + 2,) with parameters (y,)"

    s = ComplexPointInteractiveSeries([2 + 3 * I, 4 * I * y], "test",
        params={y: 1})
    assert str(s) == "interactive complex points: (2 + 3*I, 4*I*y) with parameters (y,)"

    s = ComplexSurfaceSeries(sqrt(z), (z, -2-3j, 4+5j), "test", threed=False)
    assert str(s) == "complex contour: sqrt(z) for re(z) over (-2.0, 4.0) and im(z) over (-3.0, 5.0)"

    s = ComplexSurfaceSeries(sqrt(z), (z, -2-3j, 4+5j), "test", threed=True)
    assert str(s) == "complex cartesian surface: sqrt(z) for re(z) over (-2.0, 4.0) and im(z) over (-3.0, 5.0)"

    s = ComplexDomainColoringSeries(sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=False)
    assert str(s) == "complex domain coloring: sqrt(z) for re(z) over (-2.0, 4.0) and im(z) over (-3.0, 5.0)"

    s = ComplexDomainColoringSeries(sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=True)
    assert str(s) == "complex 3D domain coloring: sqrt(z) for re(z) over (-2.0, 4.0) and im(z) over (-3.0, 5.0)"

    s = ComplexSurfaceInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=False, params={x: 1})
    assert str(s) == "interactive complex contour for expression: x*sqrt(z) over (z, (-2-3j), (4+5j)) and parameters (x,)"

    s = ComplexSurfaceInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=True, params={x: 1})
    assert str(s) == "interactive complex cartesian surface for expression: x*sqrt(z) over (z, (-2-3j), (4+5j)) and parameters (x,)"

    s = ComplexDomainColoringInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j),
        "test", params={x: 1}, threed=False)
    assert str(s) == "interactive complex domain coloring for expression: x*sqrt(z) over (z, (-2-3j), (4+5j)) and parameters (x,)"

    s = ComplexDomainColoringInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j),
        "test", params={x: 1}, threed=True)
    assert str(s) == "interactive complex 3D domain coloring for expression: x*sqrt(z) over (z, (-2-3j), (4+5j)) and parameters (x,)"

    s = Vector2DSeries(-y, x, (x, -5, 4), (y, -3, 2), "test")
    assert str(s) == "2D vector series: [-y, x] over (x, -5.0, 4.0), (y, -3.0, 2.0)"

    s = Vector3DSeries(z, y, x, (x, -5, 4), (y, -3, 2), (z, -6, 7), "test")
    assert str(s) == "3D vector series: [z, y, x] over (x, -5.0, 4.0), (y, -3.0, 2.0), (z, -6.0, 7.0)"

    s = Vector2DInteractiveSeries([-y, x * z], [(x, -5, 4), (y, -3, 2)],
        "test", params={z: 1})
    assert str(s) == "interactive 2D vector series: (-y, x*z) with ranges (x, -5.0, 4.0), (y, -3.0, 2.0) and parameters (z,)"

    s = Vector3DInteractiveSeries([-y, x * z, x], [(x, -5, 4), (y, -3, 2)],
        "test", params={z: 1})
    assert str(s) == "interactive 3D vector series: (-y, x*z, x) with ranges (x, -5.0, 4.0), (y, -3.0, 2.0) and parameters (z,)"

    s = SliceVector3DSeries(Plane((0, 0, 0), (1, 0, 0)), z, y, x,
        (x, -5, 4), (y, -3, 2), (z, -6, 7), "test")
    assert str(s) == "sliced 3D vector series: [z, y, x] over (x, -5.0, 4.0), (y, -3.0, 2.0), (z, -6.0, 7.0) at plane series: Plane(Point3D(0, 0, 0), (1, 0, 0)) over (x, -5, 4), (y, -3, 2), (z, -6, 7)"

    s = SliceVector3DInteractiveSeries(
        [u * z, u * y, x],
        [(x, -5, 4), (y, -3, 2), (z, -6, 7)], "test",
        slice=Plane((0, 0, 0), (1, 0, 0)), params={u: 1})
    assert str(s) == "sliced interactive 3D vector series: (u*z, u*y, x) with ranges (x, 0.0, 0.0), (y, -3.0, 2.0), (z, -6.0, 7.0) and parameters (u,) at plane series: Plane(Point3D(0, 0, 0), (1, 0, 0)) over (x, -5, 4), (y, -3, 2), (z, -6, 7)"

    s = PlaneSeries(Plane((0, 0, 0), (1, 1, 1)),
        (x, -5, 4), (y, -3, 2), (z, -6, 7), "test")
    assert str(s) == "plane series: Plane(Point3D(0, 0, 0), (1, 1, 1)) over (x, -5, 4), (y, -3, 2), (z, -6, 7)"

    s = PlaneInteractiveSeries([Plane((z, 0, 0), (1, 1, 1))],
        [(x, -5, 4), (y, -3, 2), (z, -6, 7)], "test", params={z: 1})
    assert str(s) == "interactive plane series: Plane(Point3D(z, 0, 0), (1, 1, 1)) over (x, -5, 4), (y, -3, 2), (z, -6, 7) with parameters [z]"

    s = GeometrySeries(Circle(Point(0, 0), 5))
    assert str(s) == "geometry entity: Circle(Point2D(0, 0), 5)"

    s = GeometryInteractiveSeries([Circle(Point(x, 0), 5)], [], params={x: 1})
    assert str(s) == "interactive geometry entity: Circle(Point2D(x, 0), 5) with parameters (x,)"

    s = Implicit3DSeries(x**2 + y**3 - z**2, (x, -2, 2), (y, -3, 3), (z, -4, 4))
    assert str(s) == "implicit surface series: x**2 + y**3 - z**2 for x over (-2.0, 2.0) and y over (-3.0, 3.0) and z over (-4.0, 4.0)"


def test_use_cm():
    # verify that series who are supposed to expose `use_cm`, actually
    # produces the correct result.

    u, x, y, z = symbols("u, x:z")

    s = AbsArgLineSeries(sqrt(x), (x, -5 + 2j, 5 + 2j), "test", use_cm=True)
    assert s.use_cm
    s = AbsArgLineSeries(sqrt(x), (x, -5 + 2j, 5 + 2j), "test", use_cm=False)
    assert not s.use_cm

    s = AbsArgLineInteractiveSeries([cos(u * x)], [(x, -4, 3)], "test",
        params={u: 1}, use_cm=True)
    assert s.use_cm
    s = AbsArgLineInteractiveSeries([cos(u * x)], [(x, -4, 3)], "test",
        params={u: 1}, use_cm=False)
    assert not s.use_cm

    s = Parametric2DLineSeries(cos(x), sin(x), (x, -4, 3), "test", use_cm=True)
    assert s.use_cm
    s = Parametric2DLineSeries(cos(x), sin(x), (x, -4, 3), "test", use_cm=False)
    assert not s.use_cm

    s = Parametric2DLineInteractiveSeries([cos(u * x), sin(x)], [(x, -4, 3)],
        "test", params={u: 1}, use_cm=True)
    assert s.use_cm
    s = Parametric2DLineInteractiveSeries([cos(u * x), sin(x)], [(x, -4, 3)],
        "test", params={u: 1}, use_cm=False)
    assert not s.use_cm

    s = Parametric3DLineSeries(cos(x), sin(x), x, (x, -4, 3), "test",
        use_cm=True)
    assert s.use_cm
    s = Parametric3DLineSeries(cos(x), sin(x), x, (x, -4, 3), "test",
        use_cm=False)
    assert not s.use_cm

    s = Parametric3DLineInteractiveSeries([cos(u*x), sin(x), x], [(x, -4, 3)],
        "test", params={u: 1}, use_cm=True)
    assert s.use_cm
    s = Parametric3DLineInteractiveSeries([cos(u*x), sin(x), x], [(x, -4, 3)],
        "test", params={u: 1}, use_cm=False)
    assert not s.use_cm

    s = SurfaceOver2DRangeSeries(cos(x * y), (x, -4, 3), (y, -2, 5), "test",
        use_cm=True)
    assert s.use_cm
    s = SurfaceOver2DRangeSeries(cos(x * y), (x, -4, 3), (y, -2, 5), "test",
        use_cm=False)
    assert not s.use_cm

    s = SurfaceInteractiveSeries([cos(u * x * y)], [(x, -4, 3), (y, -2, 5)],
        "test", params={u: 1}, use_cm=True)
    assert s.use_cm
    s = SurfaceInteractiveSeries([cos(u * x * y)], [(x, -4, 3), (y, -2, 5)],
        "test", params={u: 1}, use_cm=False)
    assert not s.use_cm

    s = ParametricSurfaceSeries(cos(x * y), sin(x * y), x * y,
        (x, -4, 3), (y, -2, 5), "test", use_cm=True)
    assert s.use_cm
    s = ParametricSurfaceSeries(cos(x * y), sin(x * y), x * y,
        (x, -4, 3), (y, -2, 5), "test", use_cm=False)
    assert not s.use_cm

    s = ParametricSurfaceInteractiveSeries([cos(u * x * y), sin(x * y), x * y],
        [(x, -4, 3), (y, -2, 5)], "test", params={u: 1}, use_cm=True)
    assert s.use_cm
    s = ParametricSurfaceInteractiveSeries([cos(u * x * y), sin(x * y), x * y],
        [(x, -4, 3), (y, -2, 5)], "test", params={u: 1}, use_cm=False)
    assert not s.use_cm

    s = ComplexSurfaceSeries(sqrt(z), (z, -2-3j, 4+5j), "test", threed=False,
        use_cm=True)
    assert s.use_cm
    s = ComplexSurfaceSeries(sqrt(z), (z, -2-3j, 4+5j), "test", threed=False,
        use_cm=False)
    assert not s.use_cm

    s = ComplexSurfaceSeries(sqrt(z), (z, -2-3j, 4+5j), "test", threed=True,
        use_cm=True)
    assert s.use_cm
    s = ComplexSurfaceSeries(sqrt(z), (z, -2-3j, 4+5j), "test", threed=True,
        use_cm=False)
    assert not s.use_cm

    s = ComplexDomainColoringSeries(sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=False, use_cm=True)
    assert s.use_cm
    s = ComplexDomainColoringSeries(sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=False, use_cm=False)
    assert not s.use_cm

    s = ComplexDomainColoringSeries(sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=True, use_cm=True)
    assert s.use_cm
    s = ComplexDomainColoringSeries(sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=True, use_cm=False)
    assert not s.use_cm

    s = ComplexSurfaceInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=False, params={x: 1}, use_cm=True)
    assert s.use_cm
    s = ComplexSurfaceInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=False, params={x: 1}, use_cm=False)
    assert not s.use_cm

    s = ComplexSurfaceInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=True, params={x: 1}, use_cm=True)
    assert s.use_cm
    s = ComplexSurfaceInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j), "test",
        threed=True, params={x: 1}, use_cm=False)
    assert not s.use_cm

    s = ComplexDomainColoringInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j),
        "test", params={x: 1}, threed=False, use_cm=True)
    assert s.use_cm
    s = ComplexDomainColoringInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j),
        "test", params={x: 1}, threed=False, use_cm=False)
    assert not s.use_cm

    s = ComplexDomainColoringInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j),
        "test", params={x: 1}, threed=True, use_cm=True)
    assert s.use_cm
    s = ComplexDomainColoringInteractiveSeries(x * sqrt(z), (z, -2-3j, 4+5j),
        "test", params={x: 1}, threed=True, use_cm=False)
    assert not s.use_cm

    s = Vector2DSeries(-y, x, (x, -5, 4), (y, -3, 2), "test", use_cm=True)
    assert s.use_cm
    s = Vector2DSeries(-y, x, (x, -5, 4), (y, -3, 2), "test", use_cm=False)
    assert not s.use_cm

    s = Vector3DSeries(z, y, x, (x, -5, 4), (y, -3, 2), (z, -6, 7), "test",
        use_cm=True)
    assert s.use_cm
    s = Vector3DSeries(z, y, x, (x, -5, 4), (y, -3, 2), (z, -6, 7), "test",
        use_cm=False)
    assert not s.use_cm

    s = Vector2DInteractiveSeries([-y, x * z], [(x, -5, 4), (y, -3, 2)],
        "test", params={z: 1}, use_cm=True)
    assert s.use_cm
    s = Vector2DInteractiveSeries([-y, x * z], [(x, -5, 4), (y, -3, 2)],
        "test", params={z: 1}, use_cm=False)
    assert not s.use_cm

    s = Vector3DInteractiveSeries([-y, x * z, x], [(x, -5, 4), (y, -3, 2)],
        "test", params={z: 1}, use_cm=True)
    assert s.use_cm
    s = Vector3DInteractiveSeries([-y, x * z, x], [(x, -5, 4), (y, -3, 2)],
        "test", params={z: 1}, use_cm=False)
    assert not s.use_cm

    s = SliceVector3DSeries(Plane((0, 0, 0), (1, 0, 0)), z, y, x,
        (x, -5, 4), (y, -3, 2), (z, -6, 7), "test", use_cm=True)
    assert s.use_cm
    s = SliceVector3DSeries(Plane((0, 0, 0), (1, 0, 0)), z, y, x,
        (x, -5, 4), (y, -3, 2), (z, -6, 7), "test", use_cm=False)
    assert not s.use_cm

    s = SliceVector3DInteractiveSeries(
        [u * z, u * y, x],
        [(x, -5, 4), (y, -3, 2), (z, -6, 7)], "test",
        slice=Plane((0, 0, 0), (1, 0, 0)), params={u: 1}, use_cm=True)
    assert s.use_cm
    s = SliceVector3DInteractiveSeries(
        [u * z, u * y, x],
        [(x, -5, 4), (y, -3, 2), (z, -6, 7)], "test",
        slice=Plane((0, 0, 0), (1, 0, 0)), params={u: 1}, use_cm=False)
    assert not s.use_cm

    s = PlaneSeries(Plane((0, 0, 0), (1, 1, 1)),
        (x, -5, 4), (y, -3, 2), (z, -6, 7), "test", use_cm=True)
    assert s.use_cm
    s = PlaneSeries(Plane((0, 0, 0), (1, 1, 1)),
        (x, -5, 4), (y, -3, 2), (z, -6, 7), "test", use_cm=False)
    assert not s.use_cm

    s = PlaneInteractiveSeries([Plane((z, 0, 0), (1, 1, 1))],
        [(x, -5, 4), (y, -3, 2), (z, -6, 7)], "test", params={z: 1}, use_cm=True)
    assert s.use_cm
    s = PlaneInteractiveSeries([Plane((z, 0, 0), (1, 1, 1))],
        [(x, -5, 4), (y, -3, 2), (z, -6, 7)], "test", params={z: 1}, use_cm=False)
    assert not s.use_cm

    s = GeometrySeries(Circle(Point(0, 0), 5), use_cm=True)
    assert s.use_cm
    s = GeometrySeries(Circle(Point(0, 0), 5), use_cm=False)
    assert not s.use_cm

    s = GeometryInteractiveSeries([Circle(Point(x, 0), 5)], [], params={x: 1},
        use_cm=True)
    assert s.use_cm
    s = GeometryInteractiveSeries([Circle(Point(x, 0), 5)], [], params={x: 1},
        use_cm=False)
    assert not s.use_cm


def test_sums():
    # test that data series are able to deal with sums
    x, y, u = symbols("x, y, u")

    def do_test(data1, data2):
        assert len(data1) == len(data2)
        for d1, d2 in zip(data1, data2):
            assert np.allclose(d1, d2)

    s = LineOver1DRangeSeries(Sum(1 / x ** y, (x, 1, 1000)), (y, 2, 10),
        adaptive=False, only_integers=True)
    xx, yy = s.get_data()

    s1 = LineOver1DRangeSeries(Sum(1 / x, (x, 1, y)), (y, 2, 10),
        adaptive=False, only_integers=True)
    xx1, yy1 = s1.get_data()

    s2 = LineInteractiveSeries([Sum(u / x, (x, 1, y))], [(y, 2, 10)],
        params={u: 1}, only_integers=True)
    xx2, yy2 = s2.get_data()
    xx1 = xx1.astype(float)
    xx2 = xx2.astype(float)
    do_test([xx1, yy1], [xx2, yy2])

    s = LineOver1DRangeSeries(Sum(1 / x, (x, 1, y)), (y, 2, 10),
        adaptive=True)
    raises(TypeError, lambda: s.get_data())


def test_absargline():
    # verify that AbsArgLineSeries produces the correct results
    x, u = symbols("x, u")

    s1 = AbsArgLineSeries(sqrt(x), (x, -5, 5), adaptive=False, n=10)
    s2 = AbsArgLineInteractiveSeries([sqrt(u * x)], [(x, -5, 5)],
        n1=10, params={u: 1})
    data1 = s1.get_data()
    data2 = s2.get_data()
    assert len(data1) == len(data2)
    for d1, d2 in zip(data1, data2):
        assert np.allclose(d1, d2)
    # there shouldn't be nan values
    assert np.invert(np.isnan(data1[1])).all()
    assert np.invert(np.isnan(data1[2])).all()

    s3 = AbsArgLineSeries(sqrt(x), (x, -5, 5), adaptive=True)
    data3 = s3.get_data()
    assert np.invert(np.isnan(data3[1])).all()
    assert np.invert(np.isnan(data3[2])).all()


def test_apply_transforms():
    # verify that transformation functions get applied to the output
    # of data series
    x, y, z, u, v = symbols("x:z, u, v")

    s1 = LineOver1DRangeSeries(cos(x), (x, -2*pi, 2*pi), adaptive=False, n=10)
    s2 = LineOver1DRangeSeries(cos(x), (x, -2*pi, 2*pi), adaptive=False, n=10,
        tx=np.rad2deg)
    s3 = LineOver1DRangeSeries(cos(x), (x, -2*pi, 2*pi), adaptive=False, n=10,
        ty=np.rad2deg)
    s4 = LineOver1DRangeSeries(cos(x), (x, -2*pi, 2*pi), adaptive=False, n=10,
        tx=np.rad2deg, ty=np.rad2deg)

    x1, y1 = s1.get_data()
    x2, y2 = s2.get_data()
    x3, y3 = s3.get_data()
    x4, y4 = s4.get_data()
    assert np.isclose(x1[0], -2*np.pi) and np.isclose(x1[-1], 2*np.pi)
    assert (y1.min() < -0.9) and (y1.max() > 0.9)
    assert np.isclose(x2[0], -360) and np.isclose(x2[-1], 360)
    assert (y2.min() < -0.9) and (y2.max() > 0.9)
    assert np.isclose(x3[0], -2*np.pi) and np.isclose(x3[-1], 2*np.pi)
    assert (y3.min() < -52) and (y3.max() > 52)
    assert np.isclose(x4[0], -360) and np.isclose(x4[-1], 360)
    assert (y4.min() < -52) and (y4.max() > 52)

    xx = np.linspace(-2*np.pi, 2*np.pi, 10)
    yy = np.cos(xx)
    s1 = List2DSeries(xx, yy)
    s2 = List2DSeries(xx, yy, tx=np.rad2deg, ty=np.rad2deg)
    x1, y1 = s1.get_data()
    x2, y2 = s2.get_data()
    assert np.isclose(x1[0], -2*np.pi) and np.isclose(x1[-1], 2*np.pi)
    assert (y1.min() < -0.9) and (y1.max() > 0.9)
    assert np.isclose(x2[0], -360) and np.isclose(x2[-1], 360)
    assert (y2.min() < -52) and (y2.max() > 52)

    s1 = AbsArgLineSeries(cos(x) + sin(I * x), (x, -2*pi, 2*pi),
        n=10, adaptive=False)
    s2 = AbsArgLineSeries(cos(x) + sin(I * x), (x, -2*pi, 2*pi),
        n=10, adaptive=False,
        tx=np.rad2deg, ty=lambda x: 2*x, tz=lambda x: 3*x)
    x1, y1, a1 = s1.get_data()
    x2, y2, a2 = s2.get_data()
    assert np.allclose(x1, np.deg2rad(x2))
    assert np.allclose(y1, y2 / 2)
    assert np.allclose(a1, a2 / 3)

    s1 = Parametric2DLineSeries(
        sin(x), cos(x), (x, -pi, pi), adaptive=False, n=10)
    s2 = Parametric2DLineSeries(
        sin(x), cos(x), (x, -pi, pi), adaptive=False, n=10,
        tx=np.rad2deg, ty=np.rad2deg, tz=np.rad2deg)
    x1, y1, a1 = s1.get_data()
    x2, y2, a2 = s2.get_data()
    assert np.allclose(x1, x2)
    assert np.allclose(y1, y2)
    assert np.allclose(a1, np.deg2rad(a2))

    s1 =  Parametric3DLineSeries(
        sin(x), cos(x), x, (x, -pi, pi), adaptive=False, n=10)
    s2 = Parametric3DLineSeries(
        sin(x), cos(x), x, (x, -pi, pi), adaptive=False, n=10, tz=np.rad2deg)
    x1, y1, z1, a1 = s1.get_data()
    x2, y2, z2, a2 = s2.get_data()
    assert np.allclose(x1, x2)
    assert np.allclose(y1, y2)
    assert np.allclose(z1, z2)
    assert np.allclose(a1, np.deg2rad(a2))

    s1 = SurfaceOver2DRangeSeries(
        cos(x**2 + y**2), (x, -2*pi, 2*pi), (y, -2*pi, 2*pi),
        adaptive=False, n1=10, n2=10)
    s2 = SurfaceOver2DRangeSeries(
        cos(x**2 + y**2), (x, -2*pi, 2*pi), (y, -2*pi, 2*pi),
        adaptive=False, n1=10, n2=10,
        tx=np.rad2deg, ty=lambda x: 2*x, tz=lambda x: 3*x)
    x1, y1, z1 = s1.get_data()
    x2, y2, z2 = s2.get_data()
    assert np.allclose(x1, np.deg2rad(x2))
    assert np.allclose(y1, y2 / 2)
    assert np.allclose(z1, z2 / 3)

    s1 = LineInteractiveSeries([y * cos(x)], [(x, -2*pi, 2*pi)],
        adaptive=False, n=10, params={y: 1})
    s2 = LineInteractiveSeries([y * cos(x)], [(x, -2*pi, 2*pi)],
        adaptive=False, n=10, params={y: 1}, tx=np.rad2deg, ty=lambda x: 2*x)
    x1, y1 = s1.get_data()
    x2, y2 = s2.get_data()
    assert np.allclose(x1, np.deg2rad(x2))
    assert np.allclose(y1, y2 / 2)

    s1 = AbsArgLineInteractiveSeries([y * cos(x)], [(x, -2*pi, 2*pi)],
        adaptive=False, n=10, params={y: 1})
    s2 = AbsArgLineInteractiveSeries([y * cos(x)], [(x, -2*pi, 2*pi)],
        adaptive=False, n=10, params={y: 1},
        tx=np.rad2deg, ty=lambda x: 2*x, tz=lambda x: 3*x)
    x1, y1, a1 = s1.get_data()
    x2, y2, a2 = s2.get_data()
    assert np.allclose(x1, np.deg2rad(x2))
    assert np.allclose(y1, y2 / 2)
    assert np.allclose(a1, a2 / 3)

    s1 = Parametric2DLineInteractiveSeries(
        [y * sin(x), cos(x)], [(x, -pi, pi)], params={y: 1},
        adaptive=False, n=10)
    s2 = Parametric2DLineInteractiveSeries(
        [y * sin(x), cos(x)], [(x, -pi, pi)], params={y: 1},
        adaptive=False, n=10,
        tx=np.rad2deg, ty=np.rad2deg, tz=np.rad2deg)
    x1, y1, a1 = s1.get_data()
    x2, y2, a2 = s2.get_data()
    assert np.allclose(x1, x2)
    assert np.allclose(y1, y2)
    assert np.allclose(a1, np.deg2rad(a2))

    s1 = Parametric3DLineInteractiveSeries(
        [sin(x), y * cos(x), x], [(x, -pi, pi)], params={y: 1},
        adaptive=False, n=10)
    s2 = Parametric3DLineInteractiveSeries(
        [sin(x), y * cos(x), x], [(x, -pi, pi)], params={y: 1},
        adaptive=False, n=10, tz=np.rad2deg)
    x1, y1, z1, a1 = s1.get_data()
    x2, y2, z2, a2 = s2.get_data()
    assert np.allclose(x1, x2)
    assert np.allclose(y1, y2)
    assert np.allclose(z1, z2)
    assert np.allclose(a1, np.deg2rad(a2))

    s1 = SurfaceInteractiveSeries(
        [u * cos(x * y)], [(x, -5, 5), (y, -5, 5)], params={u: 1}, n1=10, n2=10)
    s2 = SurfaceInteractiveSeries(
        [u * cos(x * y)], [(x, -5, 5), (y, -5, 5)], params={u: 1}, n1=10, n2=10,
        tx=np.rad2deg, ty=lambda x: 2*x, tz=lambda x: 3*x)
    x1, y1, z1 = s1.get_data()
    x2, y2, z2 = s2.get_data()
    assert np.allclose(x1, np.deg2rad(x2))
    assert np.allclose(y1, y2 / 2)
    assert np.allclose(z1, z2 / 3)

    s1 = Vector2DSeries(sin(y), cos(x), (x, -pi, pi), (y, -pi, pi), n1=5, n2=5)
    s2 = Vector2DSeries(sin(y), cos(x), (x, -pi, pi), (y, -pi, pi), n1=5, n2=5,
        tx=np.rad2deg, ty=lambda x: 2*x)
    x1, y1, u1, v1 = s1.get_data()
    x2, y2, u2, v2 = s2.get_data()
    assert np.allclose(x1, np.deg2rad(x2))
    assert np.allclose(y1, y2 / 2)
    assert np.allclose(u1, np.deg2rad(u2))
    assert np.allclose(v1, v2 / 2)

    s1 = Vector2DInteractiveSeries(
        [u * sin(y), cos(u * x)], [(x, -pi, pi), (y, -pi, pi)], n1=5, n2=5,
        params={u: 1})
    s2 = Vector2DInteractiveSeries(
        [u * sin(y), cos(u * x)], [(x, -pi, pi), (y, -pi, pi)], n1=5, n2=5,
        tx=np.rad2deg, ty=lambda x: 2*x, params={u: 1})
    x1, y1, u1, v1 = s1.get_data()
    x2, y2, u2, v2 = s2.get_data()
    assert np.allclose(x1, np.deg2rad(x2))
    assert np.allclose(y1, y2 / 2)
    assert np.allclose(u1, np.deg2rad(u2))
    assert np.allclose(v1, v2 / 2)

    s1 = Vector3DSeries(
        x, y, z, (x, -1, 1), (y, -1, 1), (z, -1, 1), n1=5, n2=5, n3=5)
    s2 = Vector3DSeries(
        x, y, z, (x, -1, 1), (y, -1, 1), (z, -1, 1), n1=5, n2=5, n3=5,
        tx=np.rad2deg, ty=lambda x: 2*x, tz=lambda x: 3*x)
    x1, y1, z1, u1, v1, w1 = s1.get_data()
    x2, y2, z2, u2, v2, w2 = s2.get_data()
    assert np.allclose(x1, np.deg2rad(x2))
    assert np.allclose(y1, y2 / 2)
    assert np.allclose(z1, z2 / 3)
    assert np.allclose(u1, np.deg2rad(u2))
    assert np.allclose(v1, v2 / 2)
    assert np.allclose(w1, w2 / 3)

    s1 = Vector3DInteractiveSeries(
        [u * x, u * y, u * z], [(x, -1, 1), (y, -1, 1), (z, -1, 1)],
        n1=5, n2=5, n3=5, params={u: 1})
    s2 = Vector3DInteractiveSeries(
        [u * x, u * y, u * z], [(x, -1, 1), (y, -1, 1), (z, -1, 1)],
        n1=5, n2=5, n3=5, params={u: 1},
        tx=np.rad2deg, ty=lambda x: 2*x, tz=lambda x: 3*x)
    x1, y1, z1, u1, v1, w1 = s1.get_data()
    x2, y2, z2, u2, v2, w2 = s2.get_data()
    assert np.allclose(x1, np.deg2rad(x2))
    assert np.allclose(y1, y2 / 2)
    assert np.allclose(z1, z2 / 3)
    assert np.allclose(u1, np.deg2rad(u2))
    assert np.allclose(v1, v2 / 2)
    assert np.allclose(w1, w2 / 3)

    s1 = ComplexDomainColoringSeries(
        (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I),
        n1=10, n2=10, n3=10)
    s2 = ComplexDomainColoringSeries(
        (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I),
        n1=10, n2=10, n3=10, tz=lambda t: t/10)
    x1, y1, z1, a1, b1, c1 = s1.get_data()
    x2, y2, z2, a2, b2, c2 = s2.get_data()
    assert np.allclose(x1, x2)
    assert np.allclose(y1, y2)
    assert np.allclose(z1, z2 * 10)
    assert np.allclose(a1, a2)
    assert np.allclose(b1, b2)
    assert np.allclose(c1, c2)

    s1 = ComplexDomainColoringInteractiveSeries(
        (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I),
        n1=10, n2=10, n3=10)
    s2 = ComplexDomainColoringInteractiveSeries(
        (z ** 2 + 1) / (z ** 2 - 1), (z, -3 - 4 * I, 3 + 4 * I),
        n1=10, n2=10, n3=10, tz=lambda t: t/10)
    x1, y1, z1, a1, b1, c1 = s1.get_data()
    x2, y2, z2, a2, b2, c2 = s2.get_data()
    assert np.allclose(x1, x2)
    assert np.allclose(y1, y2)
    assert np.allclose(z1, z2 * 10)
    assert np.allclose(a1, a2)
    assert np.allclose(b1, b2)
    assert np.allclose(c1, c2)


def test_series_labels():
    # verify that series return the correct label, depending on the plot
    # type and input arguments. If the user set custom label on a data series,
    # it should returned un-modified.

    x, y, z, u, v = symbols("x, y, z, u, v")
    wrapper = "$%s$"

    expr = cos(x)
    s1 = LineOver1DRangeSeries(expr, (x, -2, 2), str(expr))
    s2 = LineOver1DRangeSeries(expr, (x, -2, 2), "test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = (cos(x), sin(x))
    s1 = Parametric2DLineSeries(*expr, (x, -2, 2), str(x), use_cm=True)
    s2 = Parametric2DLineSeries(*expr, (x, -2, 2), "test", use_cm=True)
    s3 = Parametric2DLineSeries(*expr, (x, -2, 2), str(x), use_cm=False)
    s4 = Parametric2DLineSeries(*expr, (x, -2, 2), "test", use_cm=False)
    assert s1.get_label(False) == "x"
    assert s1.get_label(True) == wrapper % "x"
    assert s2.get_label(False) == "x"
    assert s2.get_label(True) == wrapper % "x"
    assert s3.get_label(False) == str(expr)
    assert s3.get_label(True) == wrapper % latex(expr)
    assert s4.get_label(False) == "test"
    assert s4.get_label(True) == "test"

    expr = (cos(x), sin(x), x)
    s1 = Parametric3DLineSeries(*expr, (x, -2, 2), str(x), use_cm=True)
    s2 = Parametric3DLineSeries(*expr, (x, -2, 2), "test", use_cm=True)
    s3 = Parametric3DLineSeries(*expr, (x, -2, 2), str(x), use_cm=False)
    s4 = Parametric3DLineSeries(*expr, (x, -2, 2), "test", use_cm=False)
    assert s1.get_label(False) == "x"
    assert s1.get_label(True) == wrapper % "x"
    assert s2.get_label(False) == "x"
    assert s2.get_label(True) == wrapper % "x"
    assert s3.get_label(False) == str(expr)
    assert s3.get_label(True) == wrapper % latex(expr)
    assert s4.get_label(False) == "test"
    assert s4.get_label(True) == "test"

    expr = cos(x**2 + y**2)
    s1 = SurfaceOver2DRangeSeries(expr, (x, -2, 2), (y, -2, 2), str(expr))
    s2 = SurfaceOver2DRangeSeries(expr, (x, -2, 2), (y, -2, 2), "test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = (cos(x - y), sin(x + y), x - y)
    s1 = ParametricSurfaceSeries(*expr, (x, -2, 2), (y, -2, 2), str(expr))
    s2 = ParametricSurfaceSeries(*expr, (x, -2, 2), (y, -2, 2), "test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    # NOTE: don't really care about ImplicitSeries, as it doesn't currently
    # show any label on the chart

    expr = (-sin(y), cos(x))
    s1 = Vector2DSeries(*expr, (x, -2, 2), (y, -2, 2), str(expr))
    s2 = Vector2DSeries(*expr, (x, -2, 2), (y, -2, 2), "test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = (-sin(y), cos(x), cos(z))
    s1 = Vector3DSeries(*expr, (x, -2, 2), (y, -2, 2), (z, -2, 2), str(expr))
    s2 = Vector3DSeries(*expr, (x, -2, 2), (y, -2, 2), (z, -2, 2), "test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    s1 = SliceVector3DSeries(Plane((-1, 0, 0), (1, 0, 0)), *expr,
        (x, -2, 2), (y, -2, 2), (z, -2, 2), str(expr))
    s2 = SliceVector3DSeries(Plane((-1, 0, 0), (1, 0, 0)), *expr,
        (x, -2, 2), (y, -2, 2), (z, -2, 2), "test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    plane = Plane((-1, 0, 0), (1, 1, 0))
    s1 = PlaneSeries(plane, (x, -2, 2), (y, -2, 2), (z, -2, 2), str(plane))
    s2 = PlaneSeries(plane, (x, -2, 2), (y, -2, 2), (z, -2, 2), "test")
    assert s1.get_label(False) == str(plane)
    assert s1.get_label(True) == wrapper % latex(plane)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = Circle(Point(0, 0), 5)
    s1 = GeometrySeries(expr, label=str(expr))
    s2 = GeometrySeries(expr, label="test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    s1 = List2DSeries([0, 1, 2, 3], [0, 1, 2, 3], "test")
    assert s1.get_label(False) == "test"
    assert s1.get_label(True) == "test"

    s1 = ComplexPointSeries([1 + 2 * I, 3 + 4 * I], "test")
    assert s1.get_label(False) == "test"
    assert s1.get_label(True) == "test"

    expr = cos(x)
    s1 = AbsArgLineSeries(expr, (x, 1e-05, 1e05), str(expr))
    s2 = AbsArgLineSeries(expr, (x, 1e-05, 1e05), "test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = sqrt(x)
    s1 = ComplexSurfaceSeries(expr, (x, -3.5 - 2.5j, 3.5 + 2.5j), str(expr))
    s2 = ComplexSurfaceSeries(expr, (x, -3.5 - 2.5j, 3.5 + 2.5j), "test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = sqrt(x)
    s1 = ComplexDomainColoringSeries(expr, (x, -3.5 - 2.5j, 3.5 + 2.5j),
        str(expr))
    s2 = ComplexDomainColoringSeries(expr, (x, -3.5 - 2.5j, 3.5 + 2.5j),
        "test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = x**2 + y**3 - z**2
    s1 = Implicit3DSeries(expr, (x, -2, 2), (y, -3, 3), (z, -4, 4),
        str(expr))
    s2 = Implicit3DSeries(expr, (x, -2, 2), (y, -3, 3), (z, -4, 4),
        "test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"


def test_interactive_series_labels():
    # verify that interactive series return the correct label, depending on
    # the plot type and input arguments. If the user set custom label on a
    # data series, it should returned un-modified.

    x, y, z, u, v = symbols("x, y, z, u, v")
    wrapper = "$%s$"

    expr = u * cos(x)
    s1 = LineInteractiveSeries([expr], [(x, -2, 2)], str(expr), params={u: 1})
    s2 = LineInteractiveSeries([expr], [(x, -2, 2)], "test", params={u: 1})
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = (u * cos(x), u * sin(x))
    s1 = Parametric2DLineInteractiveSeries(expr, [(x, -2, 2)], str(x),
        params={u: 1}, use_cm=True)
    s2 = Parametric2DLineInteractiveSeries(expr, [(x, -2, 2)], "test",
        params={u: 1}, use_cm=True)
    s3 = Parametric2DLineInteractiveSeries(expr, [(x, -2, 2)], str(x),
        params={u: 1}, use_cm=False)
    s4 = Parametric2DLineInteractiveSeries(expr, [(x, -2, 2)], "test",
        params={u: 1}, use_cm=False)
    assert s1.get_label(False) == "x"
    assert s1.get_label(True) == wrapper % "x"
    assert s2.get_label(False) == "x"
    assert s2.get_label(True) == wrapper % "x"
    assert s3.get_label(False) == str(expr)
    assert s3.get_label(True) == wrapper % latex(expr)
    assert s4.get_label(False) == "test"
    assert s4.get_label(True) == "test"

    expr = (u * cos(x), u * sin(x), u * x)
    s1 = Parametric3DLineInteractiveSeries(expr, [(x, -2, 2)], str(x),
        params={u: 1}, use_cm=True)
    s2 = Parametric3DLineInteractiveSeries(expr, [(x, -2, 2)], "test",
        params={u: 1}, use_cm=True)
    s3 = Parametric3DLineInteractiveSeries(expr, [(x, -2, 2)], str(x),
        params={u: 1}, use_cm=False)
    s4 = Parametric3DLineInteractiveSeries(expr, [(x, -2, 2)], "test",
        params={u: 1}, use_cm=False)
    assert s1.get_label(False) == "x"
    assert s1.get_label(True) == wrapper % "x"
    assert s2.get_label(False) == "x"
    assert s2.get_label(True) == wrapper % "x"
    assert s3.get_label(False) == str(expr)
    assert s3.get_label(True) == wrapper % latex(expr)
    assert s4.get_label(False) == "test"
    assert s4.get_label(True) == "test"

    expr = cos(u * x**2 + y**2)
    s1 = SurfaceInteractiveSeries([expr], [(x, -2, 2), (y, -2, 2)], str(expr),
        params={u: 1})
    s2 = SurfaceInteractiveSeries([expr], [(x, -2, 2), (y, -2, 2)], "test",
        params={u: 1})
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = (u * cos(x - y), u * sin(x + y), u * x - y)
    s1 = ParametricSurfaceInteractiveSeries(expr, [(x, -2, 2), (y, -2, 2)],
        str(expr), params={u: 1})
    s2 = ParametricSurfaceInteractiveSeries(expr, [(x, -2, 2), (y, -2, 2)],
        "test", params={u: 1})
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    # # NOTE: don't really care about ImplicitSeries, as it doesn't currently
    # # show any label on the chart

    expr = (-u * sin(y), u * cos(x))
    s1 = Vector2DInteractiveSeries(expr, [(x, -2, 2), (y, -2, 2)], str(expr),
        params={u: 1})
    s2 = Vector2DInteractiveSeries(expr, [(x, -2, 2), (y, -2, 2)], "test",
        params={u: 1})
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = (-u * sin(y), u * cos(x), u * cos(z))
    s1 = Vector3DInteractiveSeries(expr, [(x, -2, 2), (y, -2, 2), (z, -2, 2)],
        str(expr), params={u: 1})
    s2 = Vector3DInteractiveSeries(expr, [(x, -2, 2), (y, -2, 2), (z, -2, 2)],
        "test", params={u: 1})
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    s1 = SliceVector3DInteractiveSeries(expr,
        [(x, -2, 2), (y, -2, 2), (z, -2, 2)], str(expr),
        slice=Plane((-1, 0, 0), (1, 0, 0)), params={u: 1})
    s2 = SliceVector3DInteractiveSeries(expr,
        [(x, -2, 2), (y, -2, 2), (z, -2, 2)], "test",
        slice=Plane((-1, 0, 0), (1, 0, 0)), params={u: 1})
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    plane = Plane((-1, 0, 0), (u * 1, u * 1, 0))
    s1 = PlaneInteractiveSeries([plane], [(x, -2, 2), (y, -2, 2), (z, -2, 2)],
        str(plane), params={u: 1})
    s2 = PlaneInteractiveSeries([plane], [(x, -2, 2), (y, -2, 2), (z, -2, 2)],
        "test", params={u: 1})
    assert s1.get_label(False) == str(plane)
    assert s1.get_label(True) == wrapper % latex(plane)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = Circle(Point(0, 0), 5 * u)
    s1 = GeometryInteractiveSeries([expr], [], params={u: 1}, label=str(expr))
    s2 = GeometryInteractiveSeries([expr], [], params={u: 1}, label="test")
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    # s1 = List2DSeries([0, 1, 2, 3], [0, 1, 2, 3], "test")
    # assert s1.get_label(False) == "test"
    # assert s1.get_label(True) == "test"

    s1 = ComplexPointInteractiveSeries([1 + u * 2 * I, 3 + 4 * I], "test",
        params={u: 1})
    assert s1.get_label(False) == "test"
    assert s1.get_label(True) == "test"

    expr = u * cos(x)
    s1 = AbsArgLineInteractiveSeries([expr], [(x, 1e-05, 1e05)], str(expr), params={u: 1})
    s2 = AbsArgLineInteractiveSeries([expr], [(x, 1e-05, 1e05)], "test", params={u: 1})
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = u * sqrt(x)
    s1 = ComplexSurfaceInteractiveSeries(expr, (x, -3.5 - 2.5j, 3.5 + 2.5j),
        str(expr), params={u: 1})
    s2 = ComplexSurfaceInteractiveSeries(expr, (x, -3.5 - 2.5j, 3.5 + 2.5j),
        "test", params={u: 1})
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"

    expr = u * sqrt(x)
    s1 = ComplexDomainColoringInteractiveSeries(expr,
        (x, -3.5 - 2.5j, 3.5 + 2.5j), str(expr), params={u: 1})
    s2 = ComplexDomainColoringInteractiveSeries(expr,
        (x, -3.5 - 2.5j, 3.5 + 2.5j), "test", params={u: 1})
    assert s1.get_label(False) == str(expr)
    assert s1.get_label(True) == wrapper % latex(expr)
    assert s2.get_label(False) == "test"
    assert s2.get_label(True) == "test"


def test_surface_use_cm():
    # verify that SurfaceOver2DRangeSeries/SurfaceInteractiveSeries and
    # ParametricSurfaceSeries, ParametricSurfaceInteractiveSeries get
    # the same value for use_cm

    x, y, u, v = symbols("x, y, u, v")

    # they read the same value from default settings
    s1 = SurfaceOver2DRangeSeries(cos(x**2 + y**2), (x, -2, 2), (y, -2, 2))
    s2 = SurfaceInteractiveSeries(
        [cos(u * x**2 + y**2)], [(x, -2, 2), (y, -2, 2)],
        params={u: 1})
    s3 = ParametricSurfaceSeries(u * cos(v), u * sin(v), u,
        (u, 0, 1), (v, 0 , 2*pi))
    s4 = SurfaceInteractiveSeries([x * u * cos(v), u * sin(v), u],
        [(u, 0, 1), (v, 0 , 2*pi)], params={x: 1})
    assert s1.use_cm == s2.use_cm == s3.use_cm == s4.use_cm

    # they get the same value
    s1 = SurfaceOver2DRangeSeries(cos(x**2 + y**2), (x, -2, 2), (y, -2, 2),
        use_cm=False)
    s2 = SurfaceInteractiveSeries(
        [cos(u * x**2 + y**2)], [(x, -2, 2), (y, -2, 2)],
        params={u: 1}, use_cm=False)
    s3 = ParametricSurfaceSeries(u * cos(v), u * sin(v), u,
        (u, 0, 1), (v, 0 , 2*pi), use_cm=False)
    s4 = SurfaceInteractiveSeries([x * u * cos(v), u * sin(v), u],
        [(u, 0, 1), (v, 0 , 2*pi)], params={x: 1}, use_cm=False)
    assert s1.use_cm == s2.use_cm == s3.use_cm == s4.use_cm == False

    # they get the same value
    s1 = SurfaceOver2DRangeSeries(cos(x**2 + y**2), (x, -2, 2), (y, -2, 2),
        use_cm=True)
    s2 = SurfaceInteractiveSeries(
        [cos(u * x**2 + y**2)], [(x, -2, 2), (y, -2, 2)],
        params={u: 1}, use_cm=True)
    s3 = ParametricSurfaceSeries(u * cos(v), u * sin(v), u,
        (u, 0, 1), (v, 0 , 2*pi), use_cm=True)
    s4 = SurfaceInteractiveSeries([x * u * cos(v), u * sin(v), u],
        [(u, 0, 1), (v, 0 , 2*pi)], params={x: 1}, use_cm=True)
    assert s1.use_cm == s2.use_cm == s3.use_cm == s4.use_cm == True


def test_sliced_vector_interactive_series():
    # verify that SliceVector3DInteractiveSeries using an instance of
    # SurfaceInteractiveSeries as a slice, produced the correct results,
    # ie both the vector series and the slice series updates their parameters.
    x, y, z, u, v, t = symbols("x, y, z, u, v, t")

    N = CoordSys3D("N")
    i, j, k = N.base_vectors()
    xn, yn, zn = N.base_scalars()
    expr = -xn**2 * tan(t)**2 + yn**2 + zn**2
    g = gradient(expr)
    m = g.magnitude()

    slice_series = ParametricSurfaceInteractiveSeries(
        [u / tan(t), u * cos(v), u * sin(v)],
        [(u, 0.0, 1.0), (v, 0.0, 2 * pi)], label="slice",
        params={t: 0.5},  n1=5, n2=5)
    slice_copy = ParametricSurfaceInteractiveSeries(
        [u / tan(t), u * cos(v), u * sin(v)],
        [(u, 0.0, 1.0), (v, 0.0, 2 * pi)], label="slice_copy",
        params={t: 0.5},  n1=5, n2=5)
    s = SliceVector3DInteractiveSeries(
        (g / m).to_matrix(N),
        [(xn, -5, 5), (yn, -5, 5), (zn, -5, 5)], label="vector",
        params={t: 0.5}, slice=slice_series)

    x1, y1, z1, _, _ = slice_copy.get_data()
    x3, y3, z3, _, _ = slice_series.get_data()
    x2, y2, z2, _, _, _ = s.get_data()
    assert np.allclose(x1, x2) and np.allclose(y1, y2) and np.allclose(z1, z2)
    assert np.allclose(x1, x3) and np.allclose(y1, y3) and np.allclose(z1, z3)

    # now update the parameter: slice shoud produce the same data as slice_copy
    v = 0.25
    slice_copy.params = {t: v}
    s.params = {t: v}
    x1, y1, z1, _, _ = slice_copy.get_data()
    x3, y3, z3, _, _ = slice_series.get_data()
    x2, y2, z2, _, _, _ = s.get_data()
    assert np.allclose(x1, x2) and np.allclose(y1, y2) and np.allclose(z1, z2)
    assert np.allclose(x1, x3) and np.allclose(y1, y3) and np.allclose(z1, z3)


def test_sliced_vector_series_slice_exprs():
    # given a vector field discretized in some domain, for example x,y,z,
    # the slice expression can be f(x, y) or f(y, z) or f(x, z) and the series
    # would return correct data.

    x, y, z = symbols("x, y, z")

    _slice_xy = cos(sqrt(x**2 + y**2))
    s = SliceVector3DSeries(
        _slice_xy, z, y, x, (x, -10, 10), (y, -5, 5), (z, -3, 3),
        n1=4, n2=8, n3=12)
    data = s.get_data()
    assert all(d.shape == (8, 4) for d in data)
    assert np.allclose(data[0][0, :], np.linspace(-10, 10, 4))
    assert np.allclose(data[1][:, 0], np.linspace(-5, 5, 8))

    _slice_yz = cos(sqrt(y**2 + z**2))
    s = SliceVector3DSeries(
        _slice_yz, z, y, x, (x, -10, 10), (y, -5, 5), (z, -3, 3),
        n1=4, n2=8, n3=12)
    data = s.get_data()
    assert all(d.shape == (12, 8) for d in data)
    assert np.allclose(data[1][0, :], np.linspace(-5, 5, 8))
    assert np.allclose(data[2][:, 0], np.linspace(-3, 3, 12))

    _slice_xz = cos(sqrt(x**2 + z**2))
    s = SliceVector3DSeries(
        _slice_xz, z, y, x, (x, -10, 10), (y, -5, 5), (z, -3, 3),
        n1=4, n2=8, n3=12)
    data = s.get_data()
    assert all(d.shape == (12, 4) for d in data)
    assert np.allclose(data[0][0, :], np.linspace(-10, 10, 4))
    assert np.allclose(data[2][:, 0], np.linspace(-3, 3, 12))


def test_sliced_vector_series_slice_instantiation():
    # verify that the sliced surface is instantiated correctly.

    x, y, z, t = symbols("x, y, z, t")

    _slice_xy = cos(sqrt(x**2 + y**2))
    s = SliceVector3DSeries(
        _slice_xy, z, y, x, (x, -10, 10), (y, -5, 5), (z, -3, 3),
        n1=4, n2=8, n3=12)
    assert isinstance(s.slice_surf_series, SurfaceOver2DRangeSeries)

    _slice_xy = cos(sqrt(x**2 + y**2)) * t
    s = SliceVector3DSeries(
        _slice_xy, z, y, x, (x, -10, 10), (y, -5, 5), (z, -3, 3),
        n1=4, n2=8, n3=12, params={t: 1})
    assert isinstance(s.slice_surf_series, SurfaceInteractiveSeries)


def test_is_polar_3d():
    # verify that SurfaceOver2DRangeSeries and SurfaceInteractiveSeries
    # are able to apply polar discretization

    x, y, t = symbols("x, y, t")
    expr = (x**2 - 1)**2
    s1 = SurfaceOver2DRangeSeries(expr, (x, 0, 1.5), (y, 0, 2 * pi),
        n=10, adaptive=False, is_polar=False)
    s2 = SurfaceOver2DRangeSeries(expr, (x, 0, 1.5), (y, 0, 2 * pi),
        n=10, adaptive=False, is_polar=True)
    x1, y1, z1 = s1.get_data()
    x2, y2, z2 = s2.get_data()
    x22, y22 = x1 * np.cos(y1), x1 * np.sin(y1)
    assert np.allclose(x2, x22)
    assert np.allclose(y2, y22)

    expr = (x**2 - t)**2
    s1 = SurfaceInteractiveSeries([expr], [(x, 0, 1.5), (y, 0, 2 * pi)],
        n=10, adaptive=False, is_polar=False, params={t: 1})
    s2 = SurfaceInteractiveSeries([expr], [(x, 0, 1.5), (y, 0, 2 * pi)],
        n=10, adaptive=False, is_polar=True, params={t: 1})
    x1, y1, z1 = s1.get_data()
    x2, y2, z2 = s2.get_data()
    x22, y22 = x1 * np.cos(y1), x1 * np.sin(y1)
    assert np.allclose(x2, x22)
    assert np.allclose(y2, y22)
