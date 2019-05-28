# -*- coding: utf-8 -*-
#
# test_GIDCollection.py
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
GIDCollection tests
"""

import unittest
import nest

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False


@nest.ll_api.check_stack
class TestGIDCollection(unittest.TestCase):
    """GIDCollection tests"""

    def setUp(self):
        nest.ResetKernel()

    def test_GIDCollection_to_list(self):
        """Conversion from GIDCollection to list"""

        n_neurons = 10
        n = nest.Create('iaf_psc_alpha', n_neurons)
        n_list = [x for x in n]
        self.assertEqual(n_list, list(range(1, n_neurons + 1)))

    def test_list_to_GIDCollection(self):
        """Conversion from list to GIDCollection"""

        gids_in = [5, 10, 15, 20]
        with self.assertRaises(nest.kernel.NESTError):
            gc = nest.GIDCollection(gids_in)

        n = nest.Create('iaf_psc_alpha', 20)
        gids_in = [5, 10, 15, 20]
        gc = nest.GIDCollection(gids_in)
        for gid, compare in zip(gc, gids_in):
            self.assertEqual(gid, compare)

        nest.ResetKernel()

        n = nest.Create('iaf_psc_alpha', 10)

        gids_in = [7, 3, 8, 5, 2]
        gc = nest.GIDCollection(gids_in)
        self.assertEqual([x for x in gc], [2, 3, 5, 7, 8])

    def test_equal(self):
        """Equality of GIDCollections"""

        n = nest.Create('iaf_psc_exp', 10)
        n_list = [x for x in n]

        nest.ResetKernel()

        n_new = nest.Create('iaf_psc_exp', 10)
        new_list = [x for x in n_new]
        self.assertEqual(n_list, new_list)
        self.assertEqual(n, n_new)

        nest.ResetKernel()

        gc = nest.Create("iaf_psc_alpha", 10)
        ngc = nest.GIDCollection(list(gc))
        self.assertEqual(gc, ngc)

        self.assertNotEqual(gc, n)

    def test_indexing(self):
        """Index of GIDCollections"""

        n = nest.Create('iaf_psc_alpha', 5)
        gc_0 = nest.GIDCollection([1])
        gc_2 = nest.GIDCollection([3])
        gc_4 = nest.GIDCollection([5])

        self.assertEqual(n[0], gc_0)
        self.assertEqual(n[2], gc_2)
        self.assertEqual(n[4], gc_4)
        self.assertEqual(n[-1], gc_4)
        self.assertEqual(n[-3], gc_2)
        with self.assertRaises(nest.kernel.NESTError):
            n[7]

        nest.ResetKernel()

        nodes = nest.Create("iaf_psc_alpha", 10)
        counter = 1
        for gid in nodes:
            self.assertEqual(gid, counter)
            counter += 1
        for i in range(10):
            gc = nest.GIDCollection([i+1])
            self.assertEqual(gc, nodes[i])

    def test_slicing(self):
        """Slices of GIDCollections"""

        n = nest.Create('iaf_psc_alpha', 10)
        n_slice = n[:5]
        n_list = [x for x in n_slice]
        self.assertEqual(n_list, [1, 2, 3, 4, 5])

        n_slice_middle = n[2:7]
        n_list_middle = [x for x in n_slice_middle]
        self.assertEqual(n_list_middle, [3, 4, 5, 6, 7])

        n_slice_skip = n[::2]
        n_list_skip = [x for x in n_slice_skip]
        self.assertEqual(n_list_skip, [1, 3, 5, 7, 9])

        n_slice_skip_part = n[1:6:3]
        n_list_skip_part = [x for x in n_slice_skip_part]
        self.assertEqual(n_list_skip_part, [2, 5])

        n_slice_end = n[5:]
        n_list_end = [x for x in n_slice_end]
        self.assertEqual(n_list_end, [6, 7, 8, 9, 10])

        n_slice_negative = n[-4:]
        n_list_negative = [x for x in n_slice_negative]
        self.assertEqual(n_list_negative, [7, 8, 9, 10])

        n_slice_negative_end = n[:-3:]
        n_list_negative_end = [x for x in n_slice_negative_end]
        self.assertEqual(n_list_negative_end, [1, 2, 3, 4, 5, 6, 7, 8])

        with self.assertRaises(nest.kernel.NESTError):
            n[::-3]

    def test_correct_index(self):
        """Multiple GIDCOllection calls give right indexing"""
        compare_begin = 1
        compare_end = 11
        for model in nest.Models(mtype='nodes'):
            n = nest.Create(model, 10)
            n_list = [x for x in n]
            compare = list(range(compare_begin, compare_end))
            compare_begin += 10
            compare_end += 10
            self.assertEqual(n_list, compare)

    def test_iterating(self):
        """Iteration of GIDCollections"""

        n = nest.Create('iaf_psc_alpha', 15)
        compare = 1
        for gid in n:
            self.assertEqual(gid, compare)
            compare += 1

    def test_GIDCollection_addition(self):
        """Addition of GIDCollections"""

        nodes_a = nest.Create("iaf_psc_alpha", 2)
        nodes_b = nest.Create("iaf_psc_alpha", 2)
        all_nodes = nodes_a + nodes_b
        all_nodes_list = [n for n in all_nodes]
        test_list = [1, 2, 3, 4]
        self.assertEqual(all_nodes_list, test_list)

        nest.ResetKernel()

        n_neurons_a = 10
        n_neurons_b = 15
        n_neurons_c = 7
        n_a_b = n_neurons_a + n_neurons_b
        n_a_b_c = n_a_b + n_neurons_c
        nodes_a = nest.Create('iaf_psc_alpha', n_neurons_a)
        nodes_b = nest.Create('iaf_psc_alpha', n_neurons_b)
        nodes_c = nest.Create('iaf_psc_exp', n_neurons_c)

        node_b_a = nodes_b + nodes_a
        node_b_a_list = [x for x in node_b_a]
        test_b_a_list = (list(range(1, n_neurons_a + 1)) +
                         list(range(n_neurons_a + 1, n_a_b + 1)))
        self.assertEqual(node_b_a_list, test_b_a_list)

        node_a_c = nodes_a + nodes_c
        node_a_c_list = [x for x in node_a_c]
        test_a_c_list = (list(range(1, n_neurons_a + 1)) +
                         list(range(n_a_b + 1, n_a_b_c + 1)))
        self.assertEqual(node_a_c_list, test_a_c_list)

        nest.ResetKernel()

        n_list = []
        n_models = 0
        for model in nest.Models(mtype='nodes'):
            n = nest.Create(model, 10)
            n_list += [x for x in n]
            n_models += 1

        compare_list = list(range(1, n_models * 10 + 1))
        self.assertEqual(n_list, compare_list)

        nest.ResetKernel()

        gc_a = nest.Create('iaf_psc_alpha', 10)
        gc_b = nest.Create('iaf_psc_exp', 7)
        gc_c = nest.GIDCollection([6, 8, 10, 12, 14])

        with self.assertRaises(nest.kernel.NESTError):
            gc_sum = gc_a + gc_b + gc_c

    def test_GIDCollection_membership(self):
        """Membership in GIDCollections"""

        nodes = nest.Create('iaf_psc_alpha', 10)

        self.assertTrue(5 in nodes)
        self.assertTrue(10 in nodes)
        self.assertFalse(11 in nodes)

    def test_correct_len_on_GIDCollection(self):
        """len function on GIDCollection"""

        a = nest.Create('iaf_psc_exp', 10)
        self.assertEqual(len(a), 10)

        b = nest.Create('iaf_psc_alpha', 7)
        nodes = a + b
        self.assertEqual(len(nodes), 17)

        c = nest.Create('iaf_psc_delta', 20)
        c = c[3:17:4]
        self.assertEqual(len(c), 4)

    def test_composite_GIDCollection(self):
        """Tests composite GIDCollection with patched GIDs"""

        num_a = 10
        num_b = 15
        num_c = 30

        n_a = nest.Create('iaf_psc_exp', num_a)
        n_b = nest.Create('iaf_psc_alpha', num_b)
        n_c = nest.Create('iaf_psc_delta', num_c)

        nodes = n_a + n_c
        nodes_step = nodes[::2]
        nodes_list = list(nodes_step)
        compare_list = (list(range(1, 11))[::2] + list(range(26, 55))[::2])
        self.assertEqual(nodes_list, compare_list)

        self.assertEqual(nodes_list[2], 5)
        self.assertEqual(nodes_list[5], 26)
        self.assertEqual(nodes_list[19], 54)

        ngc = nest.GIDCollection(nodes_list)
        self.assertEqual(nodes_step, ngc)

        n_slice_first = nodes[:10]
        n_slice_middle = nodes[2:7]
        n_slice_middle_jump = nodes[2:12:2]

        n_list_first = list(n_slice_first)
        n_list_middle = list(n_slice_middle)
        n_list_middle_jump = list(n_slice_middle_jump)

        compare_list_first = list(range(1, 11))
        compare_list_middle = list(range(3, 8))
        compare_list_middle_jump = [3, 5, 7, 9, 26]
        self.assertEqual(n_list_first, compare_list_first)
        self.assertEqual(n_list_middle, compare_list_middle)
        self.assertEqual(n_list_middle_jump, compare_list_middle_jump)

    def test_composite_wrong_slice(self):
        """
        A NESTError is raised when trying to add a sliced composite and
        GIDCollection
        """

        a = nest.Create('iaf_psc_alpha', 10)
        b = nest.Create('iaf_psc_exp', 7)
        c = a + b
        d = c[::2]
        e = nest.Create('iaf_psc_delta', 13)

        with self.assertRaises(nest.kernel.NESTError):
            f = d + e

    def test_modelID(self):
        """Correct GIDCollection modelID"""

        n = nest.Create('iaf_psc_alpha')

        nest.ll_api.sli_run("modeldict")
        model_dict = nest.ll_api.sli_pop()

        models = model_dict.keys()
        modelID = list(model_dict.values())

        for model in models:
            n += nest.Create(model)

        n = n[1:]

        self.assertTrue(len(n) > 0)

        count = 0
        for gid, mid in n.items():
            self.assertEqual(mid, modelID[count])
            count += 1

    def test_connect(self):
        """Connect works with GIDCollections"""

        n = nest.Create('iaf_psc_exp', 10)
        nest.Connect(n, n, {'rule': 'one_to_one'})
        connections = nest.GetKernelStatus('num_connections')
        self.assertEqual(connections, 10)

        for gid in n:
            nest.Connect(nest.GIDCollection([gid]), nest.GIDCollection([gid]))
        self.assertEqual(nest.GetKernelStatus('num_connections'), 20)

        nest.ResetKernel()

        n = nest.Create('iaf_psc_alpha', 2)
        nest.Connect(n[0], n[1])
        self.assertEqual(nest.GetKernelStatus('num_connections'), 1)

    def test_SetStatus_and_GetStatus(self):
        """
        Test that SetStatus and GetStatus works as expected with
        GIDCollection
        """

        num_nodes = 10
        n = nest.Create('iaf_psc_alpha', num_nodes)
        nest.SetStatus(n, {'V_m': 3.5})
        self.assertEqual(nest.GetStatus(n, 'V_m')[0], 3.5)

        V_m = [1., 2., 3., 4., 5., 6., 7., 8., 9., 10.]
        nest.SetStatus(n, 'V_m', V_m)
        for i in range(num_nodes):
            self.assertEqual(nest.GetStatus(n, 'V_m')[i], V_m[i])

        with self.assertRaises(TypeError):
            nest.SetStatus(n, [{'V_m': 34.}, {'V_m': -5.}])

        nest.ResetKernel()

        gc = nest.Create('iaf_psc_exp', 5)

        with self.assertRaises(nest.kernel.NESTError):
            nest.SetStatus(n, {'V_m': -40.})
        with self.assertRaises(nest.kernel.NESTError):
            nest.GetStatus(n)

        nest.ResetKernel()
        n = nest.Create('iaf_psc_alpha', 3)
        nest.SetStatus(n, [{'V_m': 10.}, {'V_m': -10.}, {'V_m': -20.}])
        self.assertEqual(nest.GetStatus(n, 'V_m'), (10., -10., -20.))

    def test_Convert_To_Numpy_Array(self):
        """
        Test that GIDCollection can be converted to numpy Array
        """

        n = nest.Create('iaf_psc_alpha', 5)
        ref = np.array([1, 2, 3, 4, 5])
        conv_arr = np.array(n)
        self.assertTrue((ref == conv_arr).all())

    def test_GetConnections(self):
        """
        GetConnection works as expected
        """

        n = nest.Create('iaf_psc_alpha', 3)
        nest.Connect(n, n)

        get_conn = nest.GetConnections()
        get_conn_all = nest.GetConnections(n, n)
        get_conn_list = nest.GetConnections([3, 1]).get()

        self.assertEqual(get_conn_all, get_conn)

        compare_source = [1, 1, 1, 3, 3, 3]
        compare_target = [1, 2, 3, 1, 2, 3]
        self.assertEqual(get_conn_list.get('source'), compare_source)
        self.assertEqual(get_conn_list.get('target'), compare_target)

        compare_list = [3, 1, 0, 0, 6]
        conn = [get_conn_list['source'][3],
                get_conn_list['target'][3],
                get_conn_list['target_thread'][3],
                get_conn_list['synapse_id'][3],
                get_conn_list['port'][3]]
        self.assertEqual(conn, compare_list)

        conns = nest.GetConnections(n[0]).get()

        connections = [[conns['source'][i],
                        conns['target'][i],
                        conns['target_thread'][i],
                        conns['synapse_id'][i],
                        conns['port'][i]]
                       for i in range(len(nest.GetConnections(n[0])))]

        ref = [[1, 1, 0, 0, 0], [1, 2, 0, 0, 1], [1, 3, 0, 0, 2]]
        for conn, conn_ref in zip(connections, ref):
            self.assertEqual(conn, conn_ref)

    def test_GetConnections_bad_source(self):
        """
        GetConnection raises a TypeError when called with 0
        """

        n = nest.Create('iaf_psc_alpha', 3)
        nest.Connect(n, n)

        with self.assertRaises(TypeError):
            nest.GetConnections([0, 1])

    def test_senders_and_targets(self):
        """
        Senders and targets for weight recorder works as GIDCollection and list
        """

        wr = nest.Create('weight_recorder')
        pre = nest.Create("parrot_neuron", 5)
        post = nest.Create("parrot_neuron", 5)

        # Senders and targets lists empty
        self.assertFalse(nest.GetStatus(wr, "senders")[0])
        self.assertFalse(nest.GetStatus(wr, "targets")[0])

        nest.SetStatus(wr, {"senders": pre[1:3], "targets": post[3:]})

        gss = nest.GetStatus(wr, "senders")[0]
        gst = nest.GetStatus(wr, "targets")[0]

        self.assertEqual([x for x in gss], [3, 4])
        self.assertEqual([x for x in gst], [10, 11])

        nest.SetStatus(wr, {"senders": [2, 6], "targets": [8, 9]})
        gss = nest.GetStatus(wr, "senders")[0]
        gst = nest.GetStatus(wr, "targets")[0]
        self.assertEqual([x for x in gss], [2, 6])
        self.assertEqual([x for x in gst], [8, 9])


def suite():
    suite = unittest.makeSuite(TestGIDCollection, 'test')
    return suite


def run():
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())


if __name__ == "__main__":
    run()