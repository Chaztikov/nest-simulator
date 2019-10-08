# -*- coding: utf-8 -*-
#
# hl_api_topology.py
#
# This file is part of NEST.
#
# Copyright (C) 2004 The NEST Initiative
#
# NEST is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# NEST is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NEST.  If not, see <http://www.gnu.org/licenses/>.

"""
Functions relating to spatial properties of nodes
"""


import numpy as np

from ..ll_api import *
from .. import pynestkernel as kernel
from .hl_api_helper import *
from .hl_api_connections import GetConnections
from .hl_api_parallel_computing import NumProcesses, Rank
from .hl_api_types import GIDCollection

try:
    import matplotlib as mpl
    import matplotlib.path as mpath
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except ImportError:
    HAVE_MPL = False

__all__ = [
    'CreateMask',
    'Displacement',
    'Distance',
    'DumpLayerConnections',
    'DumpLayerNodes',
    'FindCenterElement',
    'FindNearestElement',
    'GetPosition',
    'GetTargetNodes',
    'GetTargetPositions',
    'PlotLayer',
    'PlotProbabilityParameter',
    'PlotTargets',
    'SelectNodesByMask',
]


def CreateMask(masktype, specs, anchor=None):
    """
    Create a spatial mask for connections.

    Masks are used when creating connections. A mask describes the area of
    the pool population that is searched for to connect for any given
    node in the driver population. Several mask types are available. Examples
    are the grid region, the rectangular, circular or doughnut region.

    The command ``CreateMask`` creates a Mask object which may be combined
    with other ``Mask`` objects using Boolean operators. The mask is specified
    in a dictionary.

    ``Mask`` objects can be passed to ``Connect`` in a connection dictionary with the key `'mask'`.


    Parameters
    ----------
    masktype : str, ['rectangular' | 'circular' | 'doughnut' | 'elliptical']
        for 2D masks, ['box' | 'spherical' | 'ellipsoidal] for 3D masks,
        ['grid'] only for grid-based layers in 2D
        The mask name corresponds to the geometrical shape of the mask. There
        are different types for 2- and 3-dimensional layers.
    specs : dict
        Dictionary specifying the parameters of the provided `masktype`,
        see **Mask types**.
    anchor : [tuple/list of floats | dict with the keys `'column'` and \
        `'row'` (for grid masks only)], optional, default: None
        By providing anchor coordinates, the location of the mask relative to
        the driver node can be changed. The list of coordinates has a length
        of 2 or 3 dependent on the number of dimensions.


    Returns
    -------
    out : ``Mask`` object


    See also
    --------
    Connect


    Notes
    -----
    - All angles must be given in degrees.


    **Mask types**

    Available mask types (`masktype`) and their corresponding parameter
    dictionaries:

    * 2D free and grid-based layers
        ::

            'rectangular' :
                {'lower_left'   : [float, float],
                 'upper_right'  : [float, float],
                 'azimuth_angle': float  # default:0.0}
            #or
            'circular' :
                {'radius' : float}
            #or
            'doughnut' :
                {'inner_radius' : float,
                 'outer_radius' : float}
            #or
            'elliptical' :
                {'major_axis' : float,
                 'minor_axis' : float,
                 'azimuth_angle' : float,   # default: 0.0,
                 'anchor' : [float, float], # default: [0.0, 0.0]}


    * 3D free and grid-based layers
        ::

            'box' :
                {'lower_left'  : [float, float, float],
                 'upper_right' : [float, float, float],
                 'azimuth_angle: float  # default: 0.0,
                 'polar_angle  : float  # defualt: 0.0}
            #or
            'spherical' :
                {'radius' : float}
            #or
            'ellipsoidal' :
                {'major_axis' : float,
                 'minor_axis' : float,
                 'polar_axis' : float
                 'azimuth_angle' : float,   # default: 0.0,
                 'polar_angle' : float,     # default: 0.0,
                 'anchor' : [float, float, float], # default: [0.0, 0.0, 0.0]}}


    * 2D grid-based layers only
        ::

            'grid' :
                {'rows' : float,
                 'columns' : float}

        By default the top-left corner of a grid mask, i.e., the grid
        mask element with grid index [0, 0], is aligned with the driver
        node. It can be changed by means of the 'anchor' parameter:
            ::

                'anchor' :
                    {'row' : float,
                     'column' : float}


    **Example**
        ::

            import nest

            # create a grid-based layer
            l = nest.Create('iaf_psc_alpha', positions=nest.spatial.grid(shape=[5, 5]))

            # create a circular mask
            m = nest.CreateMask('circular', {'radius': 0.2})

            # connectivity specifications
            conndict = {'rule': 'pairwise_bernoulli',
                        'p': 1.0,
                        'mask': m}

            # connect layer l with itself according to the specifications
            nest.Connect(l, l, conndict)

    """
    if anchor is None:
        return sli_func('CreateMask', {masktype: specs})
    else:
        return sli_func('CreateMask',
                        {masktype: specs, 'anchor': anchor})


def GetPosition(nodes):
    """
    Return the spatial locations of nodes.


    Parameters
    ----------
    nodes : GIDCollection
        GIDCollection of nodes we want the positions to


    Returns
    -------
    out : tuple or tuple of tuple(s)
        Tuple of position with 2- or 3-elements or list of positions


    See also
    --------
    Displacement : Get vector of lateral displacement between nodes.
    Distance : Get lateral distance between nodes.
    DumpLayerConnections : Write connectivity information to file.
    DumpLayerNodes : Write layer node positions to file.


    Notes
    -----
    * The functions ``GetPosition``, ``Displacement`` and ``Distance`` now
      only works for nodes local to the current MPI process, if used in a
      MPI-parallel simulation.


    **Example**
        ::

            import nest

            # Reset kernel
            nest.ResetKernel

            # create a layer
            l = nest.Create('iaf_psc_alpha', positions=nest.spatial.grid(shape=[5, 5]))

            # retrieve positions of all (local) nodes belonging to the layer
            pos = nest.GetPosition(l)

            # retrieve positions of the first node in the layer
            pos = nest.GetPosition(l[0])

            # retrieve positions of node 4
            pos = nest.GetPosition(l[4:5])

            # retrieve positions of a subset of nodes in the layer
            pos = nest.GetPosition(l[2:18])
    """
    if not isinstance(nodes, GIDCollection):
        raise TypeError("nodes must be a layer GIDCollection")

    return sli_func('GetPosition', nodes)


def Displacement(from_arg, to_arg):
    """
    Get vector of lateral displacement from node(s)/Position(s) `from_arg`
    to node(s) `to_arg`.

    Displacement is the shortest displacement, taking into account
    periodic boundary conditions where applicable. If explicit positions
    are given in the `from_arg` list, they are interpreted in the `to_arg`
    layer.

    * If one of `from_arg` or `to_arg` has length 1, and the other is longer,
      the displacement from/to the single item to all other items is given.
    * If `from_arg` and `to_arg` both have more than two elements, they have
      to be GIDCollections of the same length and the displacement for each
      pair is returned.


    Parameters
    ----------
    from_arg : GIDCollection or tuple/list with tuple(s)/list(s) of floats
        GIDCollection of GIDs or tuple/list of position(s)
    to_arg : GIDCollection
        GIDCollection of GIDs


    Returns
    -------
    out : tuple
        Displacement vectors between pairs of nodes in `from_arg` and `to_arg`


    See also
    --------
    Distance : Get lateral distances between nodes.
    DumpLayerConnections : Write connectivity information to file.
    GetPosition : Return the spatial locations of nodes.


    Notes
    -----
    * The functions ``GetPosition``, ``Displacement`` and ``Distance`` now
      only works for nodes local to the current MPI process, if used in a
      MPI-parallel simulation.


    **Example**
        ::

            import nest

            # create a layer
            l = nest.Create('iaf_psc_alpha', positions=nest.spatial.grid(shape=[5, 5]))

            # displacement between node 2 and 3
            print(nest.Displacement(l[1], l[2]))

            # displacment between the position (0.0., 0.0) and node 2
            print(nest.Displacement([(0.0, 0.0)], l[1:2]))
    """
    if not isinstance(to_arg, GIDCollection):
        raise TypeError("to_arg must be a GIDCollection")

    if isinstance(from_arg, np.ndarray):
        from_arg = (from_arg, )

    if (len(from_arg) > 1 and len(to_arg) > 1 and not
            len(from_arg) == len(to_arg)):
        raise ValueError("to_arg and from_arg must have same size unless one have size 1.")

    return sli_func('Displacement', from_arg, to_arg)


def Distance(from_arg, to_arg):
    """
    Get lateral distances from node(s)/position(s) from_arg to node(s) to_arg.

    The distance between two nodes is the length of its displacement.

    If explicit positions are given in the `from_arg` list, they are
    interpreted in the `to_arg` layer. Distance is the shortest distance,
    taking into account periodic boundary conditions where applicable.

    * If one of `from_arg` or `to_arg` has length 1, and the other is longer,
      the displacement from/to the single item to all other items is given.
    * If `from_arg` and `to_arg` both have more than two elements, they have
      to be lists of the same length and the distance for each pair is
      returned.


    Parameters
    ----------
    from_arg : GIDCollection or tuple/list with tuple(s)/list(s) of floats
        GIDCollection of GIDs or tuple/list of position(s)
    to_arg : GIDCollection
        GIDCollection of GIDs


    Returns
    -------
    out : tuple
        Distances between from and to


    See also
    --------
    Displacement : Get vector of lateral displacements between nodes.
    DumpLayerConnections : Write connectivity information to file.
    GetPosition : Return the spatial locations of nodes.


    Notes
    -----
    * The functions ``GetPosition``, ``Displacement`` and ``Distance`` now
      only works for nodes local to the current MPI process, if used in a
      MPI-parallel simulation.


    **Example**
        ::

            import nest

            # create a layer
            l = nest.Create('iaf_psc_alpha', positions=nest.spatial.grid(shape=[5, 5]))

            # distance between node 2 and 3
            print(nest.Distance(l[1], l[2]))

            # distance between the position (0.0., 0.0) and node 2
            print(nest.Distance([(0.0, 0.0)], l[1:2]))

    """
    if not isinstance(to_arg, GIDCollection):
        raise TypeError("to_arg must be a GIDCollection")

    if isinstance(from_arg, np.ndarray):
        from_arg = (from_arg, )

    if (len(from_arg) > 1 and len(to_arg) > 1 and not
            len(from_arg) == len(to_arg)):
        raise ValueError("to_arg and from_arg must have same size unless one have size 1.")

    return sli_func('Distance', from_arg, to_arg)


def FindNearestElement(layer, locations, find_all=False):
    """
    Return the node(s) closest to the location(s) in the given layer.

    This function works for fixed grid layer only.

    * If locations is a single 2-element array giving a grid location, return a
      list of GIDs of layer elements at the given location.
    * If locations is a list of coordinates, the function returns a list of
      lists with GIDs of the nodes at all locations.


    Parameters
    ----------
    layer : GIDCollection
        GIDCollection of layer GIDs
    locations : tuple(s)/list(s) of tuple(s)/list(s)
        2-element list with coordinates of a single position, or list of
        2-element list of positions
    find_all : bool, default: False
        If there are several nodes with same minimal distance, return only the
        first found, if `False`.
        If `True`, instead of returning a single GID, return a list of GIDs
        containing all nodes with minimal distance.


    Returns
    -------
    out : tuple of int(s)
        List of node GIDs


    See also
    --------
    FindCenterElement : Return GID(s) of node closest to center of layers.
    GetPosition : Return the spatial locations of nodes.


    Notes
    -----
    -


    **Example**
        ::

            import nest

            # create a layer
            l = nest.Create('iaf_psc_alpha', positions=nest.spatial.grid(shape=[5, 5]))

            # get GID of element closest to some location
            nest.FindNearestElement(l, [3.0, 4.0], True)
    """

    if not isinstance(layer, GIDCollection):
        raise TypeError("layer must be a GIDCollection")

    if not len(layer) > 0:
        raise ValueError("layer cannot be empty")

    if not is_iterable(locations):
        raise TypeError("locations must be coordinate array or list of coordinate arrays")

    # Ensure locations is sequence, keeps code below simpler
    if not is_iterable(locations[0]):
        locations = (locations, )

    result = []

    for loc in locations:
        d = Distance(np.array(loc), layer)

        if not find_all:
            dx = np.argmin(d)  # finds location of one minimum
            result.append(layer[dx].get('global_id'))
        else:
            mingids = list(layer[:1])
            minval = d[0]
            for idx in range(1, len(layer)):
                if d[idx] < minval:
                    mingids = [layer[idx].get('global_id')]
                    minval = d[idx]
                elif np.abs(d[idx] - minval) <= 1e-14 * minval:
                    mingids.append(layer[idx].get('global_id'))
            result.append(GIDCollection(mingids))

    return GIDCollection(result) if not find_all else result


def _rank_specific_filename(basename):
    """Returns file name decorated with rank."""

    if NumProcesses() == 1:
        return basename
    else:
        np = NumProcesses()
        np_digs = len(str(np - 1))  # for pretty formatting
        rk = Rank()
        dot = basename.find('.')
        if dot < 0:
            return '%s-%0*d' % (basename, np_digs, rk)
        else:
            return '%s-%0*d%s' % (basename[:dot], np_digs, rk, basename[dot:])


def DumpLayerNodes(layer, outname):
    """
    Write GID and position data of layer to file.

    Write GID and position data to layer file. For each node in a layer,
    a line with the following information is written:
        ::

            GID x-position y-position [z-position]

    If `layer` contains several GIDs, data for all layer will be written to a
    single file.


    Parameters
    ----------
    layer : GIDCollection
        GIDCollection of GIDs of a Topology layer
    outname : str
        Name of file to write to (existing files are overwritten)


    Returns
    -------
    out : None


    See also
    --------
    DumpLayerConnections : Write connectivity information to file.
    GetPosition : Return the spatial locations of nodes.


    Notes
    -----
    * If calling this function from a distributed simulation, this function
      will write to one file per MPI rank.
    * File names are formed by adding the MPI Rank into the file name before
      the file name suffix.
    * Each file stores data for nodes local to that file.


    **Example**
        ::

            import nest

            # create a layer
            l = nest.Create('iaf_psc_alpha', positions=nest.spatial.grid(shape=[5, 5]))

            # write layer node positions to file
            nest.DumpLayerNodes(l, 'positions.txt')

    """
    if not isinstance(layer, GIDCollection):
        raise TypeError("layer must be a GIDCollection")

    sli_func("""
             (w) file exch DumpLayerNodes close
             """,
             layer, _rank_specific_filename(outname))


def DumpLayerConnections(source_layer, target_layer, synapse_model, outname):
    """
    Write connectivity information to file.

    This function writes connection information to file for all outgoing
    connections from the given layers with the given synapse model.
    Data for all layers in the list is combined.

    For each connection, one line is stored, in the following format:
        ::

            source_gid target_gid weight delay dx dy [dz]

    where (dx, dy [, dz]) is the displacement from source to target node.
    If targets do not have positions (eg spike detectors outside any layer),
    NaN is written for each displacement coordinate.


    Parameters
    ----------
    source_layers : GIDCollection
        GIDCollection of GIDs of a Topology layer
    target_layers : GIDCollection
        GIDCollection of GIDs of a Topology layer
    synapse_model : str
        NEST synapse model
    outname : str
        Name of file to write to (will be overwritten if it exists)


    Returns
    -------
    out : None


    See also
    --------
    DumpLayerNodes : Write layer node positions to file.
    GetPosition : Return the spatial locations of nodes.
    nest.GetConnections : Return connection identifiers between
        sources and targets


    Notes
    -----
    * If calling this function from a distributed simulation, this function
      will write to one file per MPI rank.
    * File names are formed by inserting
      the MPI Rank into the file name before the file name suffix.
    * Each file stores data for local nodes.


    **Example**
        ::

            import nest

            # create a layer
            l = nest.Create('iaf_psc_alpha', positions=nest.spatial.grid(shape=[5, 5]))

            nest.ConnectLayers(l,l, {'rule': 'pairwise_bernoulli', 'p': 1.0}, {'synapse_model': 'static_synapse'})

            # write connectivity information to file
            nest.DumpLayerConnections(l, l, 'static_synapse', 'conns.txt')
    """
    if not isinstance(source_layer, GIDCollection):
        raise TypeError("source_layer must be a GIDCollection")
    if not isinstance(target_layer, GIDCollection):
        raise TypeError("target_layer must be a GIDCollection")

    sli_func("""
             /oname  Set
             cvlit /synmod Set
             /lyr_target Set
             /lyr_source Set
             oname (w) file lyr_source lyr_target synmod
             DumpLayerConnections close
             """,
             source_layer, target_layer, synapse_model,
             _rank_specific_filename(outname))


def FindCenterElement(layer):
    """
    Return GID(s) of node closest to center of layer.


    Parameters
    ----------
    layers : GIDCollection
        GIDCollection of layer GIDs


    Returns
    -------
    out : int
        The GID of the node closest to the center of the layer, as specified in
        the layer parameters. If several nodes are equally close to the center,
        an arbitrary one of them is returned.


    See also
    --------
    FindNearestElement : Return the node(s) closest to the location(s) in the
        given layer.
    GetPosition : Return the spatial locations of nodes.


    Notes
    -----
    -


    **Example**
        ::

            import nest

            # create a layer
            l = nest.Create('iaf_psc_alpha', positions=nest.spatial.grid(shape=[5, 5]))

            # get GID of the element closest to the center of the layer
            nest.FindCenterElement(l)
    """

    if not isinstance(layer, GIDCollection):
        raise TypeError("layer must be a GIDCollection")
    nearest_to_center = FindNearestElement(layer, layer.spatial['center'])[0]
    index = layer.index(nearest_to_center.get('global_id'))
    return layer[index:index+1]


def GetTargetNodes(sources, tgt_layer, syn_model=None):
    """
    Obtain targets of a list of sources in given target layer.


    Parameters
    ----------
    sources : tuple/list of int(s)
        List of GID(s) of source neurons
    tgt_layer : GIDCollection
        GIDCollection with GIDs of tgt_layer
    syn_model : [None | str], optional, default: None
        Return only target positions for a given synapse model.


    Returns
    -------
    out : tuple of list(s) of int(s)
        List of GIDs of target neurons fulfilling the given criteria.
        It is a list of lists, one list per source.

        For each neuron in `sources`, this function finds all target elements
        in `tgt_layer`. If `syn_model` is not given (default), all targets are
        returned, otherwise only targets of specific type.


    See also
    --------
    GetTargetPositions : Obtain positions of targets of a list of sources in a
        given target layer.
    nest.GetConnections : Return connection identifiers between
        sources and targets


    Notes
    -----
    * For distributed simulations, this function only returns targets on the
      local MPI process.


    **Example**
        ::

            import nest

            # create a layer
            l = nest.CreateLayer({'rows'      : 11,
                                'columns'   : 11,
                                'extent'    : [11.0, 11.0],
                                'elements'  : 'iaf_psc_alpha'})

            # connectivity specifications with a mask
            conndict = {'connection_type': 'divergent',
                        'mask': {'rectangular': {'lower_left' : [-2.0, -1.0],
                                                 'upper_right': [2.0, 1.0]}}}

            # connect layer l with itself according to the given
            # specifications
            nest.ConnectLayers(l, l, conndict)

            # get the GIDs of the targets of the source neuron with GID 5
            nest.GetTargetNodes([5], l)
    """
    if not isinstance(sources, GIDCollection):
        raise TypeError("sources must be a GIDCollection.")

    if not isinstance(tgt_layer, GIDCollection):
        raise TypeError("tgt_layer must be a GIDCollection")

    conns = GetConnections(sources, tgt_layer, synapse_model=syn_model)

    # Re-organize conns into one list per source, containing only target GIDs.
    src_tgt_map = dict((sgid, []) for sgid in sources.tolist())
    for src, tgt in zip(conns.source(), conns.target()):
        src_tgt_map[src].append(tgt)

    for src in src_tgt_map.keys():
        src_tgt_map[src] = GIDCollection(list(np.unique(src_tgt_map[src])))

    # convert dict to nested list in same order as sources
    return tuple(src_tgt_map[sgid] for sgid in sources.tolist())


def GetTargetPositions(sources, tgt_layer, syn_model=None):
    """
    Obtain positions of targets to a given GIDCollection of sources.


    Parameters
    ----------
    sources : GIDCollection
        GIDCollection with GID(s) of source neurons
    tgt_layer : GIDCollection
        GIDCollection of tgt_layer
    syn_type : [None | str], optional, default: None
        Return only target positions for a given synapse model.


    Returns
    -------
    out : list of list(s) of tuple(s) of floats
        Positions of target neurons fulfilling the given criteria as a nested
        list, containing one list of positions per node in sources.

        For each neuron in `sources`, this function finds all target elements
        in `tgt_layer`. If `syn_model` is not given (default), all targets are
        returned, otherwise only targets of specific type.


    See also
    --------
    GetTargetNodes : Obtain targets of a list of sources in a given target
        layer.


    Notes
    -----
    * For distributed simulations, this function only returns targets on the
      local MPI process.


    **Example**
        ::

            import nest

            # create a layer
            l = nest.CreateLayer({'rows'      : 11,
                                'columns'   : 11,
                                'extent'    : [11.0, 11.0],
                                'elements'  : 'iaf_psc_alpha'})

            # connectivity specifications with a mask
            conndict1 = {'connection_type': 'divergent',
                         'mask': {'rectangular': {'lower_left'  : [-2.0, -1.0],
                                                  'upper_right' : [2.0, 1.0]}}}

            # connect layer l with itself according to the given
            # specifications
            nest.ConnectLayers(l, l, conndict1)

            # get the positions of the targets of the source neuron with GID 5
            nest.GetTargetPositions(l[5:6], l)
    """
    if not isinstance(sources, GIDCollection):
        raise TypeError("sources must be a GIDCollection.")

    # Find positions to all nodes in target layer
    pos_all_tgts = GetPosition(tgt_layer)
    first_tgt_gid = tgt_layer[0].get('global_id')

    connections = GetConnections(sources, tgt_layer,
                                 synapse_model=syn_model)
    srcs = connections.get('source')
    tgts = connections.get('target')
    if isinstance(srcs, int):
        srcs = [srcs]
    if isinstance(tgts, int):
        tgts = [tgts]

    # Make dictionary where the keys are the source gids, which is mapped to a
    # list with the positions of the targets connected to the source.
    src_tgt_pos_map = dict((sgid, []) for sgid in sources.tolist())
    for i in range(len(connections)):
        tgt_indx = tgts[i] - first_tgt_gid
        src_tgt_pos_map[srcs[i]].append(pos_all_tgts[tgt_indx])

    # Turn dict into list in same order as sources
    return [src_tgt_pos_map[sgid] for sgid in sources.tolist()]


def SelectNodesByMask(layer, anchor, mask_obj):
    """
    Obtain the GIDs inside a masked area of a topology layer.

    The function finds and returns all the GIDs inside a given mask of a single
    layer. It works on both 2-dimensional and 3-dimensional masks and layers.
    All mask types are allowed, including combined masks.

    Parameters
    ----------
    layer : GIDCollection
        GIDCollection with GIDs of the layer to select nodes from.
    anchor : tuple/list of double
        List containing center position of the layer. This is the point from
        where we start to search.
    mask_obj: object
        Mask object specifying chosen area.

    Returns
    -------
    out : list of int(s)
        GID(s) of nodes/elements inside the mask.
    """

    if not isinstance(layer, GIDCollection):
        raise TypeError("layer must be a GIDCollection.")

    mask_datum = mask_obj._datum

    gid_list = sli_func('SelectNodesByMask',
                        layer, anchor, mask_datum)

    return GIDCollection(gid_list)


def _draw_extent(ax, xctr, yctr, xext, yext):
    """Draw extent and set aspect ration, limits"""

    # thin gray line indicating extent
    llx, lly = xctr - xext / 2.0, yctr - yext / 2.0
    urx, ury = llx + xext, lly + yext
    ax.add_patch(
        plt.Rectangle((llx, lly), xext, yext, fc='none', ec='0.5', lw=1,
                      zorder=1))

    # set limits slightly outside extent
    ax.set(aspect='equal',
           xlim=(llx - 0.05 * xext, urx + 0.05 * xext),
           ylim=(lly - 0.05 * yext, ury + 0.05 * yext),
           xticks=tuple(), yticks=tuple())


def _shifted_positions(pos, ext):
    """Get shifted positions corresponding to boundary conditions."""
    return [[pos[0] + ext[0], pos[1]],
            [pos[0] - ext[0], pos[1]],
            [pos[0], pos[1] + ext[1]],
            [pos[0], pos[1] - ext[1]],
            [pos[0] + ext[0], pos[1] - ext[1]],
            [pos[0] - ext[0], pos[1] + ext[1]],
            [pos[0] + ext[0], pos[1] + ext[1]],
            [pos[0] - ext[0], pos[1] - ext[1]]]


def PlotLayer(layer, fig=None, nodecolor='b', nodesize=20):
    """
    Plot all nodes in a layer.

    This function plots only top-level nodes, not the content of composite
    nodes.


    Parameters
    ----------
    layer : GIDCollection (Layer)
        GIDCollection with GIDs of layer to plot
    fig : [None | matplotlib.figure.Figure object], optional, default: None
        Matplotlib figure to plot to. If not given, a new figure is
        created.
    nodecolor : [None | any matplotlib color], optional, default: 'b'
        Color for nodes
    nodesize : float, optional, default: 20
        Marker size for nodes


    Returns
    -------
    out : `matplotlib.figure.Figure` object


    See also
    --------
    PlotProbabilityParameter : Create a plot of the connection probability and/or mask.
    PlotTargets : Plot all targets of a given source.
    matplotlib.figure.Figure : matplotlib Figure class


    Notes
    -----
    * Do not use this function in distributed simulations.


    **Example**
        ::

            import nest
            import matplotlib.pyplot as plt

            # create a layer
            l = nest.CreateLayer({'rows'      : 11,
                                'columns'   : 11,
                                'extent'    : [11.0, 11.0],
                                'elements'  : 'iaf_psc_alpha'})

            # plot layer with all its nodes
            nest.PlotLayer(l)
            plt.show()
    """

    if not HAVE_MPL:
        raise ImportError('Matplotlib could not be imported')

    if not isinstance(layer, GIDCollection):
        raise TypeError("layer must be a GIDCollection.")

    # get layer extent
    ext = layer.spatial['extent']

    if len(ext) == 2:
        # 2D layer

        # get layer extent and center, x and y
        xext, yext = ext
        xctr, yctr = layer.spatial['center']

        # extract position information, transpose to list of x and y pos
        xpos, ypos = zip(*GetPosition(layer))

        if fig is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
        else:
            ax = fig.gca()

        ax.scatter(xpos, ypos, s=nodesize, facecolor=nodecolor,
                   edgecolor='none')
        _draw_extent(ax, xctr, yctr, xext, yext)

    elif len(ext) == 3:
        # 3D layer
        from mpl_toolkits.mplot3d import Axes3D

        # extract position information, transpose to list of x,y,z pos
        pos = zip(*GetPosition(layer))

        if fig is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
        else:
            ax = fig.gca()

        ax.scatter3D(*pos, s=nodesize, facecolor=nodecolor, edgecolor='none')
        plt.draw_if_interactive()

    else:
        raise ValueError("unexpected dimension of layer")

    return fig


def PlotTargets(src_nrn, tgt_layer, syn_type=None, fig=None,
                mask=None, probability_parameter=None,
                src_color='red', src_size=50, tgt_color='blue', tgt_size=20,
                mask_color='yellow', probability_cmap='Greens'):
    """
    Plot all targets of source neuron `src_nrn` in a target layer `tgt_layer`.


    Parameters
    ----------
    src_nrn : GIDCollection
        GIDCollection of source neuron (as single-element GIDCollection)
    tgt_layer : GIDCollection
        GIDCollection of tgt_layer
    syn_type : [None | str], optional, default: None
        Show only targets connected to with a given synapse type
    fig : [None | matplotlib.figure.Figure object], optional, default: None
        Matplotlib figure to plot to. If not given, a new figure is created.
    mask : [None | dict], optional, default: None
        Draw mask with targets; see ``PlotProbabilityParameter`` for details.
    probability_parameter : [None | Parameter], optional, default: None
        Draw connection probability with targets; see ``PlotProbabilityParameter`` for details.
    src_color : [None | any matplotlib color], optional, default: 'red'
        Color used to mark source node position
    src_size : float, optional, default: 50
        Size of source marker (see scatter for details)
    tgt_color : [None | any matplotlib color], optional, default: 'blue'
        Color used to mark target node positions
    tgt_size : float, optional, default: 20
        Size of target markers (see scatter for details)
    mask_color : [None | any matplotlib color], optional, default: 'red'
        Color used for line marking mask
    kernel_color : [None | any matplotlib color], optional, default: 'red'
        Color used for lines marking kernel


    Returns
    -------
    out : matplotlib.figure.Figure object


    See also
    --------
    GetTargetNodes : Obtain targets of a list of sources in a given target
        layer.
    GetTargetPositions : Obtain positions of targets of a list of sources in a
        given target layer.
    probability_parameter : Add indication of connection probability and mask to axes.
    PlotLayer : Plot all nodes in a layer.
    matplotlib.pyplot.scatter : matplotlib scatter plot.


    Notes
    -----
    * Do not use this function in distributed simulations.


    **Example**
        ::

            import nest
            import matplotlib.pyplot as plt

            # create a layer
            l = nest.CreateLayer({'rows'      : 11,
                                'columns'   : 11,
                                'extent'    : [11.0, 11.0],
                                'elements'  : 'iaf_psc_alpha'})

            # connectivity specifications with a mask
            conndict = {'connection_type': 'divergent',
                         'mask': {'rectangular': {'lower_left'  : [-2.0, -1.0],
                                                  'upper_right' : [2.0, 1.0]}}}

            # connect layer l with itself according to the given
            # specifications
            nest.ConnectLayers(l, l, conndict)

            # plot the targets of the source neuron with GID 5
            nest.PlotTargets(l[4:5], l)
            plt.show()
    """

    if not HAVE_MPL:
        raise ImportError('Matplotlib could not be imported')

    if not isinstance(src_nrn, GIDCollection) or len(src_nrn) != 1:
        raise TypeError("src_nrn must be a single element GIDCollection.")
    if not isinstance(tgt_layer, GIDCollection):
        raise TypeError("tgt_layer must be a GIDCollection.")

    # get position of source
    srcpos = GetPosition(src_nrn)

    # get layer extent
    ext = tgt_layer.spatial['extent']

    if len(ext) == 2:
        # 2D layer

        # get layer extent and center, x and y
        xext, yext = ext
        xctr, yctr = tgt_layer.spatial['center']

        if fig is None:
            fig = plt.figure()
            ax = fig.add_subplot(111)
        else:
            ax = fig.gca()

        # get positions, reorganize to x and y vectors
        tgtpos = GetTargetPositions(src_nrn, tgt_layer, syn_type)
        if tgtpos:
            xpos, ypos = zip(*tgtpos[0])
            ax.scatter(xpos, ypos, s=tgt_size, facecolor=tgt_color,
                       edgecolor='none')

        ax.scatter(srcpos[:1], srcpos[1:], s=src_size, facecolor=src_color,
                   edgecolor='none',
                   alpha=0.4, zorder=-10)

        if mask is not None or probability_parameter is not None:
            edges = [xctr - xext, xctr + xext, yctr - yext, yctr + yext]
            PlotProbabilityParameter(src_nrn, probability_parameter, mask=mask, edges=edges, ax=ax,
                                     prob_cmap=probability_cmap, mask_color=mask_color)

        _draw_extent(ax, xctr, yctr, xext, yext)

    else:
        # 3D layer
        from mpl_toolkits.mplot3d import Axes3D

        if fig is None:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
        else:
            ax = fig.gca()

        # get positions, reorganize to x,y,z vectors
        tgtpos = GetTargetPositions(src_nrn, tgt_layer, syn_type)
        if tgtpos:
            xpos, ypos, zpos = zip(*tgtpos[0])
            ax.scatter3D(xpos, ypos, zpos, s=tgt_size, facecolor=tgt_color,
                         edgecolor='none')

        ax.scatter3D(srcpos[:1], srcpos[1:2], srcpos[2:], s=src_size,
                     facecolor=src_color, edgecolor='none',
                     alpha=0.4, zorder=-10)

    plt.draw_if_interactive()

    return fig


def _create_mask_patches(mask, periodic, extent, source_pos, face_color='yellow'):

    edge_color = 'black'
    alpha = 0.2
    line_width = 2
    mask_patches = []
    if 'anchor' in mask:
        offs = np.array(mask['anchor'])
    else:
        offs = np.array([0., 0.])

    if 'circular' in mask:
        r = mask['circular']['radius']

        patch = plt.Circle(source_pos + offs, radius=r,
                           fc=face_color, ec=edge_color, alpha=alpha, lw=line_width)
        mask_patches.append(patch)

        if periodic:
            for pos in _shifted_positions(source_pos + offs, extent):
                patch = plt.Circle(pos, radius=r,
                                   fc=face_color, ec=edge_color, alpha=alpha, lw=line_width)
                mask_patches.append(patch)
    elif 'doughnut' in mask:
        # Mmm... doughnut
        def make_doughnut_patch(pos, r_out, r_in, ec, fc, alpha):
            def make_circle(r):
                t = np.arange(0, np.pi * 2.0, 0.01)
                t = t.reshape((len(t), 1))
                x = r * np.cos(t)
                y = r * np.sin(t)
                return np.hstack((x, y))
            outside_verts = make_circle(r_out)[::-1]
            inside_verts = make_circle(r_in)
            codes = np.ones(len(inside_verts), dtype=mpath.Path.code_type) * mpath.Path.LINETO
            codes[0] = mpath.Path.MOVETO
            vertices = np.concatenate([outside_verts, inside_verts])
            vertices += pos
            all_codes = np.concatenate((codes, codes))
            path = mpath.Path(vertices, all_codes)
            return mpatches.PathPatch(path, fc=fc, ec=ec, alpha=alpha, lw=line_width)

        r_in = mask['doughnut']['inner_radius']
        r_out = mask['doughnut']['outer_radius']
        pos = source_pos + offs
        patch = make_doughnut_patch(pos, r_in, r_out, edge_color, face_color, alpha)
        mask_patches.append(patch)
        if periodic:
            for pos in _shifted_positions(source_pos + offs, extent):
                patch = make_doughnut_patch(pos, r_in, r_out, edge_color, face_color, alpha)
                mask_patches.append(patch)
    elif 'rectangular' in mask:
        ll = np.array(mask['rectangular']['lower_left'])
        ur = np.array(mask['rectangular']['upper_right'])
        pos = source_pos + ll + offs

        if 'azimuth_angle' in mask['rectangular']:
            angle = mask['rectangular']['azimuth_angle']
            angle_rad = angle * np.pi / 180
            cs = np.cos([angle_rad])[0]
            sn = np.sin([angle_rad])[0]
            pos = [pos[0] * cs - pos[1] * sn,
                   pos[0] * sn + pos[1] * cs]
        else:
            angle = 0.0

        patch = plt.Rectangle(pos, ur[0] - ll[0], ur[1] - ll[1], angle=angle,
                              fc=face_color, ec=edge_color, alpha=alpha, lw=line_width)
        mask_patches.append(patch)

        if periodic:
            for pos in _shifted_positions(source_pos + ll + offs, extent):
                patch = plt.Rectangle(pos, ur[0] - ll[0], ur[1] - ll[1],
                                      angle=angle, fc=face_color,
                                      ec=edge_color, alpha=alpha, lw=line_width)
                mask_patches.append(patch)
    elif 'elliptical' in mask:
        width = mask['elliptical']['major_axis']
        height = mask['elliptical']['minor_axis']
        if 'azimuth_angle' in mask['elliptical']:
            angle = mask['elliptical']['azimuth_angle']
        else:
            angle = 0.0
        if 'anchor' in mask['elliptical']:
            anchor = mask['elliptical']['anchor']
        else:
            anchor = np.array([0., 0.])
        patch = mpl.patches.Ellipse(source_pos + offs + anchor, width, height,
                                    angle=angle, fc=face_color,
                                    ec=edge_color, alpha=alpha, lw=line_width)
        mask_patches.append(patch)

        if periodic:
            for pos in _shifted_positions(source_pos + offs + anchor, extent):
                patch = mpl.patches.Ellipse(pos, width, height, angle=angle, fc=face_color,
                                            ec=edge_color, alpha=alpha, lw=line_width)
                mask_patches.append(patch)
    else:
        raise ValueError('Mask type cannot be plotted with this version of PyTopology.')
    return mask_patches


def PlotProbabilityParameter(source, parameter=None, mask=None, edges=[-0.5, 0.5, -0.5, 0.5], shape=[100, 100],
                             ax=None, prob_cmap='Greens', mask_color='yellow'):
    """
    Create a plot of the connection probability and/or mask.

    A probability plot is created based on a Parameter and a source. The
    Parameter should have a distance dependency. The source must be given
    as a GIDCollection with a single GID. Optionally a mask can also be
    plotted.

    Parameters
    ----------
    source : GIDCollection
        Single GID GIDCollection to use as source.
    parameter : Parameter object
        Parameter the probability is based on.
    mask : Dictionary
        Optional specification of a connection mask. Connections will only
        be made to nodes inside the mask. See CreateMask for options on
        how to specify the mask.
    edges : list/tuple
        List of four edges of the region to plot. The values are given as
        [x_min, x_max, y_min, y_max].
    shape : list/tuple
        Number of Parameter values to calculate in each direction.
    ax : matplotlib.axes.AxesSubplot,
        A matplotlib axes instance to plot in. If none is given,
        a new one is created.
    """
    if not HAVE_MPL:
        raise ImportError('Matplotlib could not be imported')

    if parameter is None and mask is None:
        raise ValueError('At least one of parameter or mask must be specified')
    if ax is None:
        fig, ax = plt.subplots()
    ax.set_xlim(*edges[:2])
    ax.set_ylim(*edges[2:])

    if parameter is not None:
        z = np.zeros(shape[::-1])
        for i, x in enumerate(np.linspace(*edges[:2], shape[0])):
            positions = [[x, y] for y in np.linspace(*edges[2:], shape[1])]
            values = parameter.apply(source, positions)
            z[:, i] = np.array(values)
        img = ax.imshow(np.minimum(np.maximum(z, 0.0), 1.0), extent=edges,
                        origin='lower', cmap=prob_cmap, vmin=0., vmax=1.)
        plt.colorbar(img, ax=ax)

    if mask is not None:
        source.set_spatial()
        periodic = source.spatial['edge_wrap']
        extent = source.spatial['extent']
        source_pos = GetPosition(source)
        patches = _create_mask_patches(mask, periodic, extent, source_pos, face_color=mask_color)
        for patch in patches:
            patch.set_zorder(0.5)
            ax.add_patch(patch)