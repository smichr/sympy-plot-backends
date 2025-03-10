from sympy.core.symbol import symbols
from sympy.matrices.dense import Matrix
from sympy.core.containers import Tuple
from sympy.functions.elementary.trigonometric import cos
from sympy.functions.elementary.miscellaneous import sqrt
from sympy.geometry import Plane
from sympy.vector import CoordSys3D
from sympy.external import import_module
from spb.vectors import _preprocess, _series, plot_vector
from spb.utils import _plot_sympify, _split_vector
from spb.series import (
    Vector2DSeries,
    Vector3DSeries,
    SliceVector3DSeries,
    ContourSeries,
)
from spb.backends.utils import get_seeds_points
from pytest import raises

np = import_module('numpy', catch=(RuntimeError,))


def pw(*args):
    """_preprocess wrapper. Only need it to sympify the arguments before
    calling _preprocess."""
    args = _plot_sympify(args)
    return _preprocess(*args)


def test_preprocess():
    # verify that the preprocessing is correctly applied to the
    # input arguments

    x, y, z = symbols("x:z")
    N = CoordSys3D("N")
    v1 = x * N.i + y * N.j + z * N.k
    v2 = z * N.i + x * N.j + y * N.k
    m1 = v1.to_matrix(N)
    m2 = v2.to_matrix(N)
    l1 = list(m1)
    l2 = list(m2)

    # passing in vectors
    r = pw(v1)[0]
    assert r[0] == v1
    assert r[1] == str(v1)

    r = pw(v1, (x, -5, 5), "test")[0]
    assert r == [v1, Tuple(x, -5, 5), "test"]

    r = pw((v1, (x, -5, 5), "test"))[0]
    assert r == [v1, Tuple(x, -5, 5), "test"]

    r = pw((v1, (x, -5, 5), "v1"), (v2, (x, -5, 5), (y, -2, 2)))
    assert r[0] == [v1, Tuple(x, -5, 5), "v1"]
    assert r[1] == [v2, Tuple(x, -5, 5), Tuple(y, -2, 2), str(v2)]

    r = pw(v1, v2, (x, -5, 5), (y, -2, 2), (z, -3, 3))
    assert r[0] == [v1, Tuple(x, -5, 5), Tuple(y, -2, 2), Tuple(z, -3, 3), str(v1)]
    assert r[1] == [v2, Tuple(x, -5, 5), Tuple(y, -2, 2), Tuple(z, -3, 3), str(v2)]

    # passing in matrices
    r = pw(m1, (x, -5, 5), "test")[0]
    assert r == [m1, Tuple(x, -5, 5), "test"]

    r = pw(m1, m2, (x, -5, 5), (y, -2, 2), (z, -3, 3))
    assert r[0] == [m1, Tuple(x, -5, 5), Tuple(y, -2, 2), Tuple(z, -3, 3), str(m1)]
    assert r[1] == [m2, Tuple(x, -5, 5), Tuple(y, -2, 2), Tuple(z, -3, 3), str(m2)]

    # passing in lists
    r = pw(l1, (x, -5, 5), "test")[0]
    assert r == [tuple(l1), Tuple(x, -5, 5), "test"]

    r = pw(l1, l2, (x, -5, 5), (y, -2, 2), (z, -3, 3))
    assert r[0] == [
        tuple(l1),
        Tuple(x, -5, 5),
        Tuple(y, -2, 2),
        Tuple(z, -3, 3),
        str(tuple(l1)),
    ]
    assert r[1] == [
        tuple(l2),
        Tuple(x, -5, 5),
        Tuple(y, -2, 2),
        Tuple(z, -3, 3),
        str(tuple(l2)),
    ]


def test_split_vector():
    # verify that the correct components of a vector are retrieved, no matter
    # the type of the input vector (list, matrix, symbolic vector)

    x, y, z = symbols("x:z")
    N = CoordSys3D("N")
    v1 = x * N.i + y * N.j + z * N.k
    v2 = z * N.i + x * N.j + y * N.k
    m1 = v1.to_matrix(N)
    m2 = v2.to_matrix(N)
    l1 = list(m1)
    l2 = list(m2)

    ranges_in = [Tuple(x, -5, 5)]
    ranges_out = [Tuple(x, -5, 5), Tuple(y, -10, 10), Tuple(z, -10, 10)]

    def do_test(expr_in, expr_out):
        exprs, ranges = _split_vector(expr_in, ranges_in)
        assert exprs == expr_out
        assert all([r in ranges_out for r in ranges])

    do_test(v1, (x, y, z))
    do_test(m1, (x, y, z))
    do_test(l1, (x, y, z))
    do_test(v2, (z, x, y))
    do_test(m2, (z, x, y))
    do_test(l2, (z, x, y))

    # too few or too many elements
    raises(ValueError, lambda: _split_vector([x], ranges_in))
    raises(ValueError, lambda: _split_vector([x, x, x, x], ranges_in))


def test_series():
    # verify that the correct data series are created from the provided
    # input vectors and keyword arguments

    x, y, z = symbols("x:z")
    N = CoordSys3D("N")
    v1 = x * N.i + y * N.j
    v2 = z * N.i + x * N.j + y * N.k
    m1 = v1.to_matrix(N)
    m2 = v2.to_matrix(N)

    # Tests for 2D vectors
    args = pw(v1, "test")[0]
    _, _, s = _series(args[0], *args[1:-1], label=args[-1])
    assert isinstance(s, Vector2DSeries)
    # auto generate ranges
    t1 = (s.exprs[0], s.ranges[0][1], s.ranges[0][2])
    t2 = (s.exprs[1], s.ranges[1][1], s.ranges[1][2])
    assert (t1 == (x, -10.0, 10.0))
    assert (t2 == (y, -10.0, 10.0))

    args = pw(v1, (x, -5, 5), "test")[0]
    _, _, s = _series(args[0], *args[1:-1], label=args[-1])
    assert isinstance(s, Vector2DSeries)
    assert (s.exprs[0], s.ranges[0][1], s.ranges[0][2]) == (x, -5.0, 5.0)
    # auto generate range
    assert (s.exprs[1], s.ranges[1][1], s.ranges[1][2]) == (y, -10.0, 10.0)

    # vector doesn't contain free symbols, and not all ranges were provided.
    # raise error because the missing range could be any symbol.
    args = pw([1, 2], (x, -5, 5), "test")[0]
    raises(ValueError, lambda: _series(args[0], *args[1:-1], label=args[-1]))

    # too many free symbols in the 2D vector
    args = pw([x + y, z], (x, -5, 5), "test")[0]
    raises(ValueError, lambda: _series(args[0], *args[1:-1], label=args[-1]))

    # Tests for 3D vectors
    args = pw(v2, "test")[0]
    _, _, s = _series(args[0], *args[1:-1], label=args[-1])
    assert isinstance(s, Vector3DSeries)
    # auto generate ranges
    t1 = (s.exprs[0], s.ranges[0][1], s.ranges[0][2])
    t2 = (s.exprs[1], s.ranges[1][1], s.ranges[1][2])
    t3 = (s.exprs[2], s.ranges[2][1], s.ranges[2][2])
    assert t1 == (z, -10.0, 10.0)
    assert t2 == (x, -10.0, 10.0)
    assert t3 == (y, -10.0, 10.0)

    args = pw(v2, (x, -5, 5), "test")[0]
    _, _, s = _series(args[0], *args[1:-1], label=args[-1])
    assert isinstance(s, Vector3DSeries)
    t1 = (s.exprs[0], s.ranges[0][1], s.ranges[0][2])
    t2 = (s.exprs[1], s.ranges[1][1], s.ranges[1][2])
    t3 = (s.exprs[2], s.ranges[2][1], s.ranges[2][2])
    assert t1 == (z, -5.0, 5.0)
    assert t2 == (x, -10.0, 10.0)
    assert t3 == (y, -10.0, 10.0)

    # vector doesn't contain free symbols, and not all ranges were provided.
    # raise error because the missing range could be any symbol.
    args = pw(Matrix([1, 2, 3]), (x, -5, 5), "test")[0]
    raises(ValueError, lambda: _series(args[0], *args[1:-1], label=args[-1]))

    # too many free symbols in the 3D vector
    a = symbols("a")
    args = pw(Matrix([x + y, z, a + x]), (x, -5, 5), "test")[0]
    raises(ValueError, lambda: _series(args[0], *args[1:-1], label=args[-1]))

    # Test for 3D vector slices
    # Single slicing plane
    _, _, s = _series(
        v2,
        Tuple(x, -5, 5),
        Tuple(y, -4, 4),
        Tuple(z, -3, 3),
        label="test",
        slice=Plane((1, 2, 3), (1, 0, 0)),
        n1=5,
        n2=6,
        n3=7,
    )
    assert isinstance(s, (tuple, list))
    assert len(s) == 1
    assert isinstance(s[0], SliceVector3DSeries)
    assert s[0].is_slice
    xx, yy, zz, uu, vv, ww = s[0].get_data()
    assert all([t.shape == (6, 7) for t in [xx, yy, zz, uu, vv, ww]])
    # normal vector of the plane is directed along x-axis. Same value for each
    # x-coordinate.
    assert np.all(xx == 1)
    assert (np.min(yy.flatten()) == -4) and (np.max(yy.flatten()) == 4)
    assert (np.min(zz.flatten()) == -3) and (np.max(zz.flatten()) == 3)

    # multiple slicing planes
    _, _, s = _series(
        v2,
        Tuple(x, -5, 5),
        Tuple(y, -4, 4),
        Tuple(z, -3, 3),
        label="test",
        slice=[
            Plane((1, 2, 3), (1, 0, 0)),
            Plane((1, 2, 3), (0, 1, 0)),
            Plane((1, 2, 3), (0, 0, 1)),
        ],
        n1=5,
        n2=6,
        n3=7,
    )
    assert isinstance(s, (tuple, list))
    assert len(s) == 3
    assert all([isinstance(t, SliceVector3DSeries) for t in s])
    xx1, yy1, zz1, uu1, vv1, ww1 = s[0].get_data()
    xx2, yy2, zz2, uu2, vv2, ww2 = s[1].get_data()
    xx3, yy3, zz3, uu3, vv3, ww3 = s[2].get_data()
    assert all([t.shape == (6, 7) for t in [xx1, yy1, zz1, uu1, vv1, ww1]])
    assert all([t.shape == (7, 5) for t in [xx2, yy2, zz2, uu2, vv2, ww2]])
    assert all([t.shape == (6, 5) for t in [xx3, yy3, zz3, uu3, vv3, ww3]])
    assert np.all(xx1 == 1)
    assert (np.min(yy1.flatten()) == -4) and (np.max(yy1.flatten()) == 4)
    assert (np.min(zz1.flatten()) == -3) and (np.max(zz1.flatten()) == 3)
    assert np.all(yy2 == 2)
    assert (np.min(xx2.flatten()) == -5) and (np.max(xx2.flatten()) == 5)
    assert (np.min(zz2.flatten()) == -3) and (np.max(zz2.flatten()) == 3)
    assert np.all(zz3 == 3)
    assert (np.min(xx3.flatten()) == -5) and (np.max(xx3.flatten()) == 5)
    assert (np.min(yy3.flatten()) == -4) and (np.max(yy3.flatten()) == 4)

    # slicing expression (surface)
    _, _, s = _series(
        v2,
        Tuple(x, -5, 5),
        Tuple(y, -4, 4),
        Tuple(z, -3, 3),
        label="test",
        slice=cos(x ** 2 + y ** 2),
        n1=5,
        n2=6,
        n3=7,
    )
    assert isinstance(s, (tuple, list))
    assert len(s) == 1
    assert isinstance(s[0], SliceVector3DSeries)
    assert s[0].is_slice
    xx, yy, zz, uu, vv, ww = s[0].get_data()
    assert all([t.shape == (6, 5) for t in [xx, yy, zz, uu, vv, ww]])
    # normal vector of the plane is directed along x-axis. Same value for each
    # x-coordinate.
    assert (np.min(xx.flatten()) == -5) and (np.max(xx.flatten()) == 5)
    assert (np.min(yy.flatten()) == -4) and (np.max(yy.flatten()) == 4)

    # must fail because slice is not an Expr or a Plane or a list of Planes
    raises(
        ValueError,
        lambda: _series(
            v2,
            Tuple(x, -5, 5),
            Tuple(y, -4, 4),
            Tuple(z, -3, 3),
            label="test",
            n1=5,
            n2=6,
            n3=7,
            slice=[-1],
        ),
    )
    raises(
        ValueError,
        lambda: _series(
            v2,
            Tuple(x, -5, 5),
            Tuple(y, -4, 4),
            Tuple(z, -3, 3),
            label="test",
            n1=5,
            n2=6,
            n3=7,
            slice=0,
        ),
    )
    raises(
        ValueError,
        lambda: _series(
            v2,
            Tuple(x, -5, 5),
            Tuple(y, -4, 4),
            Tuple(z, -3, 3),
            label="test",
            n1=5,
            n2=6,
            n3=7,
            slice="test",
        ),
    )


def test_plot_vector():
    # verify that `plot_vector()` generates the correct data series

    x, y, z = symbols("x:z")
    N = CoordSys3D("N")
    v1 = x * N.i + y * N.j
    v2 = z * N.i + x * N.j + y * N.k

    # this will stop inside plot_vector, because we are mixing 2D and 3D vectors
    raises(ValueError, lambda: plot_vector(v1, v2))
    # this will stop inside _series, because 3 ranges have been provided
    # for a 2D vector plot (v1)
    raises(ValueError, lambda: plot_vector(v1, v2, (x, -5, 5), (y, -2, 2), (z, -3, 3)))

    # scalar is not one of [None,True,False,Expr]
    raises(ValueError, lambda: plot_vector(v1, scalar="s"))

    # single 2D vector field with magnitude scalar field: contour series should
    # have the same range as the vector series
    p = plot_vector(v1, (x, -5, 5), (y, -2, 2), show=False)
    assert len(p.series) == 2
    assert isinstance(p.series[0], ContourSeries)
    assert isinstance(p.series[1], Vector2DSeries)
    assert p.series[0].start_x == -5
    assert p.series[0].end_x == 5
    assert p.series[0].start_y == -2
    assert p.series[0].end_y == 2

    # multiple 2D vector field with magnitude scalar field: contour series
    # should cover the entire ranges of the vector fields
    p = plot_vector(
        (v1, (x, -5, -3), (y, -2, 2)),
        (v1, (x, -1, 1), (y, -4, -3)),
        (v1, (x, 2, 6), (y, 3, 5)),
        scalar=sqrt(x ** 2 + y ** 2),
        show=False,
    )
    assert len(p.series) == 4
    assert isinstance(p.series[0], ContourSeries)
    assert all([isinstance(s, Vector2DSeries) for s in p.series[1:]])
    assert p.series[0].start_x == -5
    assert p.series[0].end_x == 6
    assert p.series[0].start_y == -4
    assert p.series[0].end_y == 5


def test_vector_data():
    # verify that vector data series generates data with the correct shape

    x, y, z = symbols("x:z")

    s = Vector2DSeries(x, y, (x, -5, 5), (y, -3, 3), "test", n1=10, n2=15)
    xx, yy, uu, vv = s.get_data()
    assert xx.shape == uu.shape == (15, 10)
    assert yy.shape == vv.shape == (15, 10)

    # at least one vector component is a scalar
    s = Vector2DSeries(1, y, (x, -5, 5), (y, -3, 3), "test", n1=10, n2=15)
    xx, yy, uu, vv = s.get_data()
    assert xx.shape == uu.shape == (15, 10)
    assert yy.shape == vv.shape == (15, 10)

    s = Vector3DSeries(
        x, y, z, (x, -5, 5), (y, -3, 3), (z, -2, 2), "test", n1=10, n2=15, n3=20
    )
    xx, yy, zz, uu, vv, ww = s.get_data()
    assert xx.shape == uu.shape == (15, 10, 20)
    assert yy.shape == vv.shape == (15, 10, 20)
    assert zz.shape == ww.shape == (15, 10, 20)

    # at least one vector component is a scalar
    s = Vector3DSeries(
        x, 1, z, (x, -5, 5), (y, -3, 3), (z, -2, 2), "test", n1=10, n2=15, n3=20
    )
    xx, yy, zz, uu, vv, ww = s.get_data()
    assert xx.shape == uu.shape == (15, 10, 20)
    assert yy.shape == vv.shape == (15, 10, 20)
    assert zz.shape == ww.shape == (15, 10, 20)


def test_get_seeds_points():
    # verify that spb.backends.utils.get_seeds_points returns the correct
    # data type based on the parameters

    vtk = import_module('vtk', catch=(RuntimeError,))

    x, y, z = symbols("x:z")
    s = Vector3DSeries(z, y, x, (x, -5, 5), (y, -3, 3), (z, -2, 2))
    xx, yy, zz, uu, vv, ww = s.get_data()

    #
    # Case 1: search boundary points where the vector is pointing inward the
    # domain
    #
    d = get_seeds_points(xx, yy, zz, uu, vv, ww, True,
        **dict(starts=None))
    assert isinstance(d, np.ndarray)
    assert len(d.shape) == 2 and (d.shape[1] == 3)

    d = get_seeds_points(xx, yy, zz, uu, vv, ww, False,
        **dict(starts=None))
    assert isinstance(d, vtk.vtkPolyData)

    #
    # Case 2: user-provided starting points
    #
    xx2 = np.linspace(-5, 5, 10)
    yy2 = np.linspace(-3, 3, 10)
    zz2 = np.linspace(-2, 2, 10)
    d = get_seeds_points(xx, yy, zz, uu, vv, ww, True,
        **dict(starts={
            "x": xx2,
            "y": yy2,
            "z": zz2
        }))
    assert isinstance(d, np.ndarray)
    assert len(d.shape) == 2 and (d.shape == (10, 3))
    assert np.all(d[:, 0] == xx2)
    assert np.all(d[:, 1] == yy2)
    assert np.all(d[:, 2] == zz2)

    d = get_seeds_points(xx, yy, zz, uu, vv, ww, False,
        **dict(starts={
            "x": xx2,
            "y": yy2,
            "z": zz2
        }))
    assert isinstance(d, vtk.vtkPolyData)

    #
    # Case 3: generate random locations
    #
    d = get_seeds_points(xx, yy, zz, uu, vv, ww, True,
        **dict(starts=True, npoints=10))
    assert isinstance(d, np.ndarray)
    assert len(d.shape) == 2 and (d.shape == (10, 3))

    d = get_seeds_points(xx, yy, zz, uu, vv, ww, False,
        **dict(starts=True, npoints=10))
    assert isinstance(d, vtk.vtkPointSource)
