# -*- coding: utf-8 -*-
#
# hill_tononi_Vp.py
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
NEST spatial example: A case-based tutorial
===========================================

:Author: Hans Ekkehard Plesser
:Institution: Norwegian University of Life Sciences
:Version: 0.4
:Date: 21 November 2012
:Copyright: The NEST Initiative (2004)
:License: Creative Commons Attribution License

**NOTE:** The network generated by this script does generate
dynamics in which the activity of the entire system, especially
Rp and Vp oscillates with approx 5 Hz. This is different from
the full model. Deviations are due to the different model type
and the elimination of a number of connections, with no changes
to the weights.

Introduction
-------------

This tutorial shows you how to implement a simplified version of the
Hill-Tononi model of the early visual pathway using NEST. The model
is described in the paper

  S. L. Hill and G. Tononi.
  Modeling Sleep and Wakefulness in the Thalamocortical System.
  J Neurophysiology **93**:1671-1698 (2005).
  Freely available via `doi 10.1152/jn.00915.2004
  <http://dx.doi.org/10.1152/jn.00915.2004>`_.

We simplify the model somewhat both to keep this tutorial a bit
shorter, and because some details of the Hill-Tononi model are not
currently supported by NEST. Simplifications include:

1. We use the ``iaf_cond_alpha`` neuron model, which is
   simpler than the Hill-Tononi model.

#. As the ``iaf_cond_alpha`` neuron model only supports two
   synapses (labeled "ex" and "in"), we only include AMPA and
   GABA_A synapses.

#. We ignore the secondary pathway (Ts, Rs, Vs), since it adds just
   more of the same from a technical point of view.

#. Synaptic delays follow a Gaussian distribution in the HT
   model. This implies actually a Gaussian distributions clipped at
   some small, non-zero delay, since delays must be
   positive. Currently, there is a bug in the module when using clipped
   Gaussian distribution. We therefore draw delays from a
   uniform distribution.

#. Some further adaptations are given at the appropriate locations in
   the script.

This tutorial is divided in the following sections:

Philosophy_
   Discusses the philosophy applied to model implementation in this
   tutorial

Preparations_
   Neccessary steps to use NEST

`Configurable Parameters`_
   Define adjustable network parameters

`Neuron Models`_
   Define the neuron models needed by the network model

Populations_
   Create Populations

`Synapse models`_
   Define the synapse models used in the network model

Connections_
   Create Connections

`Example simulation`_
   Perform a small simulation for illustration. This
   section also discusses the setup for recording.

Philosophy
-----------

A network models has two essential components: *populations* and
*projections*.  We first use NEST's ``CopyModel()`` mechanism to
create specific models for all populations and subpopulations in
the network, and then create the populations using the
``Create()`` function.

We use a two-stage process to create the connections, mainly
because the same configurations are required for a number of
projections: we first define dictionaries specifying the
connections, then apply these dictionaries later.

The way in which we declare the network model here is an
example. You should not consider it the last word: we expect to see
a significant development in strategies and tools for network
descriptions in the future. The following contributions to CNS*09
seem particularly interesting

- Ralf Ansorg & Lars Schwabe. Declarative model description and
  code generation for hybrid individual- and population-based
  simulations of the early visual system (P57);
- Sharon Crook, R. Angus Silver, & Padraig Gleeson. Describing
  and exchanging models of neurons and neuronal networks with
  NeuroML (F1);

as well as the following paper which will apply in PLoS
Computational Biology shortly:

- Eilen Nordlie, Marc-Oliver Gewaltig, & Hans Ekkehard Plesser.
  Towards reproducible descriptions of neuronal network models.

Preparations
-------------

Please make sure that your ``PYTHONPATH`` is set correctly, so
that Python can find the NEST Python module.

**Note:** By default, the script does not show any graphics.
Set ``SHOW_FIGURES`` to ``True`` to activate graphics.
"""

from pprint import pprint
import numpy as np
import matplotlib.pyplot as plt

SHOW_FIGURES = False

if SHOW_FIGURES:
    plt.ion()
else:
    plt_show = plt.show

    def nop(s=None, block=None):
        pass

    plt.show = nop

##############################################################################
# This tutorial gives a brief introduction to the ConnPlotter
# toolbox. It is by no means complete.

# Load pynest
import nest

# Make sure we start with a clean slate, even if we re-run the script
# in the same Python session.
nest.ResetKernel()

# Import math, we need Pi
import math


##############################################################################
# Configurable Parameters
# -----------------------
#
# Here we define those parameters that we take to be
# configurable. The choice of configurable parameters is obviously
# arbitrary, and in practice one would have far more configurable
# parameters. We restrict ourselves to:
#
# - Network size in neurons ``N``, each layer is ``N x N``.
# - Network size in subtended visual angle ``visSize``, in degree.
# - Temporal frequency of drifting grating input ``f_dg``, in Hz.
# - Spatial wavelength and direction of drifting grating input,
#   ``lambda_dg`` and ``phi_dg``, in degree/radian.
# - Background firing rate of retinal nodes and modulation amplitude,
#   ``retDC`` and ``retAC``, in Hz.
# - Simulation duration ``simtime``; actual simulation is split into
#   intervals of ``sim_interval`` length, so that the network state
#   can be visualized in those intervals. Times are in ms.
# - Periodic boundary conditions, ``edge_wrap``.
Params = {'N': 40,
          'visSize': 8.0,
          'f_dg': 2.0,
          'lambda_dg': 2.0,
          'phi_dg': 0.0,
          'retDC': 30.0,
          'retAC': 30.0,
          'simtime': 100.0,
          'sim_interval': 1.0,
          'edge_wrap': True
          }


##############################################################################
# Neuron Models
# -------------
#
# We declare models in two steps:
#
# 1. We define a dictionary specifying the NEST neuron model to use
#    as well as the parameters for that model.
# #. We create three copies of this dictionary with parameters
#    adjusted to the three model variants specified in Table~2 of
#    Hill & Tononi (2005) (cortical excitatory, cortical inhibitory,
#    thalamic)
#
# In addition, we declare the models for the stimulation and
# recording devices.
#
# The general neuron model
# ------------------------
#
# We use the ``iaf_cond_alpha`` neuron, which is an
# integrate-and-fire neuron with two conductance-based synapses which
# have alpha-function time course.  Any input with positive weights
# will automatically directed to the synapse labeled ``_ex``, any
# with negative weights to the synapes labeled ``_in``.  We define
# **all** parameters explicitly here, so that no information is
# hidden in the model definition in NEST. ``V_m`` is the membrane
# potential to which the model neurons will be initialized.
# The model equations and parameters for the Hill-Tononi neuron model
# are given on pp. 1677f and Tables 2 and 3 in that paper. Note some
# peculiarities and adjustments:
#
# - Hill & Tononi specify their model in terms of the membrane time
#   constant, while the ``iaf_cond_alpha`` model is based on the
#   membrane capcitance. Interestingly, conducantces are unitless in
#   the H&T model. We thus can use the time constant directly as
#   membrane capacitance.
# - The model includes sodium and potassium leak conductances. We
#   combine these into a single one as follows:
#
# .. math::
#
#    -g_{NaL}(V-E_{Na}) - g_{KL}(V-E_K)
#     = -(g_{NaL}+g_{KL})
#    \left(V-\frac{g_{NaL}E_{NaL}+g_{KL}E_K}{g_{NaL}g_{KL}}\right)
#
# - We write the resulting expressions for g_L and E_L explicitly
#   below, to avoid errors in copying from our pocket calculator.
# - The paper gives a range of 1.0-1.85 for g_{KL}, we choose 1.5
#   here.
# - The Hill-Tononi model has no explicit reset or refractory
#   time. We arbitrarily set V_reset and t_ref.
# - The paper uses double exponential time courses for the synaptic
#   conductances, with separate time constants for the rising and
#   fallings flanks. Alpha functions have only a single time
#   constant: we use twice the rising time constant given by Hill and
#   Tononi.
# - In the general model below, we use the values for the cortical
#   excitatory cells as defaults. Values will then be adapted below.
#
nest.CopyModel('iaf_cond_alpha', 'NeuronModel',
               params={'C_m': 16.0,
                       'E_L': (0.2 * 30.0 + 1.5 * -90.0) / (0.2 + 1.5),
                       'g_L': 0.2 + 1.5,
                       'E_ex': 0.0,
                       'E_in': -70.0,
                       'V_reset': -60.0,
                       'V_th': -51.0,
                       't_ref': 2.0,
                       'tau_syn_ex': 1.0,
                       'tau_syn_in': 2.0,
                       'I_e': 0.0,
                       'V_m': -70.0})


##############################################################################
# Adaptation of models for different populations
# ----------------------------------------------
#
# We must copy the `NeuronModel` dictionary explicitly, otherwise
# Python would just create a reference.
#
# Cortical excitatory cells
# .........................
# Parameters are the same as above, so we need not adapt anything
nest.CopyModel('NeuronModel', 'CtxExNeuron')

# Cortical inhibitory cells
# .........................
nest.CopyModel('NeuronModel', 'CtxInNeuron',
               params={'C_m': 8.0,
                       'V_th': -53.0,
                       't_ref': 1.0})

# Thalamic cells
# ..............
nest.CopyModel('NeuronModel', 'ThalamicNeuron',
               params={'C_m': 8.0,
                       'V_th': -53.0,
                       't_ref': 1.0,
                       'E_in': -80.0})


##############################################################################
# Input generating nodes
# ----------------------
#
# Input is generated by sinusoidally modulate Poisson generators,
# organized in a square layer of retina nodes. These nodes require a
# slightly more complicated initialization than all other elements of
# the network:
#
# - Average firing rate ``rate``, firing rate modulation depth ``amplitude``,
#   and temporal modulation frequency ``frequency`` are the same for all
#   retinal nodes and are set directly below.
# - The temporal phase ``phase`` of each node depends on its position in
#   the grating and can only be assigned after the retinal layer has
#   been created.
nest.CopyModel('sinusoidal_poisson_generator', 'RetinaNode',
               params={'amplitude': Params['retAC'],
                       'rate': Params['retDC'],
                       'frequency': Params['f_dg'],
                       'phase': 0.0,
                       'individual_spike_trains': False})


##############################################################################
# Recording nodes
# ---------------
#
# We use the ``multimeter`` device for recording from the model
# neurons. At present, ``iaf_cond_alpha`` is one of few models
# supporting ``multimeter`` recording.  Support for more models will
# be added soon; until then, you need to use ``voltmeter`` to record
# from other models.
#
# We configure multimeter to record membrane potential to membrane
# potential at certain intervals to memory only. We record the node ID of
# the recorded neurons, but not the time.
nest.CopyModel('multimeter', 'RecordingNode',
               params={'interval': Params['sim_interval'],
                       'record_from': ['V_m'],
                       'record_to': 'memory'})


##############################################################################
# Populations
# -----------
#
# We now create the neuron populations in the model. We define
# them in order from eye via thalamus to cortex.
#
# We first define a spatial grid defining common positions and
# parameters for all populations
layerGrid = nest.spatial.grid(shape=[Params['N'], Params['N']],
                              extent=[Params['visSize'], Params['visSize']],
                              edge_wrap=Params['edge_wrap'])
# We can pass this object to the ``positions`` argument in ``Create``
# to define the positions of the neurons.


##############################################################################
# Retina
# ------
retina = nest.Create('RetinaNode', positions=layerGrid)

# Now set phases of retinal oscillators; we create a Parameter
# which represents the phase based on the spatial properties of
# the neuron.

retina_phase = 360.0 / Params['lambda_dg'] * (math.cos(Params['phi_dg']) * nest.spatial.pos.x +
                                              math.sin(Params['phi_dg']) * nest.spatial.pos.y)
retina.phase = retina_phase


##############################################################################
# Thalamus
# --------
#
# We first introduce specific neuron models for the thalamic relay
# cells and interneurons. These have identical properties, but by
# treating them as different populations, we can address them specifically
# when building connections.
for model_name in ('TpRelay', 'TpInter'):
    nest.CopyModel('ThalamicNeuron', model_name)

# Now we can create the layers, one with relay cells,
# and one with interneurons:
TpRelay = nest.Create('TpRelay', positions=layerGrid)
TpInter = nest.Create('TpInter', positions=layerGrid)


##############################################################################
# Reticular nucleus
# -----------------
nest.CopyModel('ThalamicNeuron', 'RpNeuron')
Rp = nest.Create('RpNeuron', positions=layerGrid)


##############################################################################
# Primary visual cortex
# ---------------------
#
# We follow again the same approach as with Thalamus. We differentiate
# neuron types between layers and between pyramidal cells and
# interneurons. We have two layers for pyramidal cells, and two layers for
# interneurons for each of layers 2-3, 4, and 5-6. Finally, we need to
# differentiate between vertically and horizontally tuned populations.
# When creating the populations, we create the vertically and the
# horizontally tuned populations as separate dictionaries holding the
# layers.
for layer in ('L23', 'L4', 'L56'):
    nest.CopyModel('CtxExNeuron', layer + 'pyr')
for layer in ('L23', 'L4', 'L56'):
    nest.CopyModel('CtxInNeuron', layer + 'in')

name_dict = {'L23pyr': 2, 'L23in': 1,
             'L4pyr': 2, 'L4in': 1,
             'L56pyr': 2, 'L56in': 1}

# Now we can create the populations, suffixes h and v indicate tuning
Vp_h_layers = {}
Vp_v_layers = {}
for layer_name, num_layers in name_dict.items():
    for i in range(num_layers):
        Vp_h_layers['{}_{}'.format(layer_name, i)] = nest.Create(layer_name, positions=layerGrid)
        Vp_v_layers['{}_{}'.format(layer_name, i)] = nest.Create(layer_name, positions=layerGrid)


##############################################################################
# Collect all populations
# -----------------------
#
# For reference purposes, e.g., printing, we collect all populations
# in a tuple:
populations = (retina, TpRelay, TpInter, Rp) + tuple(Vp_h_layers.values()) + tuple(Vp_v_layers.values())


##############################################################################
# Inspection
# ----------
#
# We can now look at the network using `PrintNodes`:
nest.PrintNodes()

# We can also try to plot a single layer in a network. All layers have
# equal positions of the nodes.
nest.PlotLayer(Rp)
plt.title('Layer Rp')


##############################################################################
# Synapse models
# =-------------
#
# Actual synapse dynamics, e.g., properties such as the synaptic time
# course, time constants, reversal potentials, are properties of
# neuron models in NEST and we set them in section `Neuron models`_
# above. When we refer to *synapse models* in NEST, we actually mean
# connectors which store information about connection weights and
# delays, as well as port numbers at the target neuron (``rport``)
# and implement synaptic plasticity. The latter two aspects are not
# relevant here.
#
# We just use NEST's ``static_synapse`` connector but copy it to
# synapse models ``AMPA`` and ``GABA_A`` for the sake of
# explicitness. Weights and delays are set as needed in section
# `Connections`_ below, as they are different from projection to
# projection. De facto, the sign of the synaptic weight decides
# whether input via a connection is handle by the ``_ex`` or the
# ``_in`` synapse.
nest.CopyModel('static_synapse', 'AMPA')
nest.CopyModel('static_synapse', 'GABA_A')


##############################################################################
# Connections
# --------------------
#
# Building connections is the most complex part of network
# construction. Connections are specified in Table 1 in the
# Hill-Tononi paper. As pointed out above, we only consider AMPA and
# GABA_A synapses here.  Adding other synapses is tedious work, but
# should pose no new principal challenges. We also use a uniform in
# stead of a Gaussian distribution for the weights.
#
# The model has two identical primary visual cortex populations,
# ``Vp_v`` and ``Vp_h``, tuned to vertical and horizonal gratings,
# respectively. The *only* difference in the connection patterns
# between the two populations is the thalamocortical input to layers
# L4 and L5-6 is from a population of 8x2 and 2x8 grid locations,
# respectively. Furthermore, inhibitory connection in cortex go to
# the opposing orientation population as to the own.
#
# To save us a lot of code doubling, we thus defined properties
# dictionaries for all connections first and then use this to connect
# both populations. We follow the subdivision of connections as in
# the Hill & Tononi paper.
#
# TODO: Rewrite this note.
# **Note:** Hill & Tononi state that their model spans 8 degrees of
# visual angle and stimuli are specified according to this. On the
# other hand, all connection patterns are defined in terms of cell
# grid positions. Since the NEST defines connection patterns in terms
# of the extent given in degrees, we need to apply the following
# scaling factor to all lengths in connections:
dpc = Params['visSize'] / (Params['N'] - 1)

# We will collect all same-orientation cortico-cortical connections in
ccConnections = []
# the cross-orientation cortico-cortical connections in
ccxConnections = []
# and all cortico-thalamic connections in
ctConnections = []


##############################################################################
# Horizontal intralaminar
# -----------------------
#
# *Note:* "Horizontal" means "within the same cortical layer" in this
# case.
#
# We first define dictionaries with the (most) common properties for
# horizontal intralaminar connection. We then create copies in which
# we adapt those values that need adapting, and
horIntra_conn_spec = {"rule": "pairwise_bernoulli",
                      "mask": {"circular": {"radius": 12.0 * dpc}},
                      "p": 0.05*nest.spatial_distributions.gaussian(nest.spatial.distance, std=7.5 * dpc)}

horIntra_syn_spec = {"synapse_model": "AMPA",
                     "weight": 1.0,
                     "delay": nest.random.uniform(min=1.75, max=2.25)}

# In a loop, we run over the sources and targets and the corresponding
# dictionaries with values that needs updating.
for conn in [{"sources": "L23pyr", "targets": "L23pyr", "conn_spec": {}},
             {"sources": "L23pyr", "targets": "L23in", "conn_spec": {}},
             {"sources": "L4pyr", "targets": "L4pyr", "conn_spec": {"mask": {"circular": {"radius": 7.0 * dpc}}}},
             {"sources": "L4pyr", "targets": "L4in", "conn_spec": {"mask": {"circular": {"radius": 7.0 * dpc}}}},
             {"sources": "L56pyr", "targets": "L56pyr", "conn_spec": {}},
             {"sources": "L56pyr", "targets": "L56in", "conn_spec": {}}]:
    conn_spec = horIntra_conn_spec.copy()
    conn_spec.update(conn['conn_spec'])
    ccConnections.append([conn['sources'], conn['targets'], conn_spec, horIntra_syn_spec])


##############################################################################
# Vertical intralaminar
# -----------------------
# *Note:* "Vertical" means "between cortical layers" in this
# case.
#
# We proceed as above.
verIntra_conn_spec = {"rule": "pairwise_bernoulli",
                      "mask": {"circular": {"radius": 2.0 * dpc}},
                      "p": nest.spatial_distributions.gaussian(nest.spatial.distance, std=7.5 * dpc)}

verIntra_syn_spec = {"synapse_model": "AMPA",
                     "weight": 2.0,
                     "delay": nest.random.uniform(min=1.75, max=2.25)}

for conn in [{"sources": "L23pyr", "targets": "L56pyr",
              "syn_spec": {"weight": 1.0}},
             {"sources": "L23pyr", "targets": "L23in",
              "syn_spec": {"weight": 1.0}},
             {"sources": "L4pyr", "targets": "L23pyr", "syn_spec": {}},
             {"sources": "L4pyr", "targets": "L23in", "syn_spec": {}},
             {"sources": "L56pyr", "targets": "L23pyr", "syn_spec": {}},
             {"sources": "L56pyr", "targets": "L23in", "syn_spec": {}},
             {"sources": "L56pyr", "targets": "L4pyr", "syn_spec": {}},
             {"sources": "L56pyr", "targets": "L4in", "syn_spec": {}}]:
    syn_spec = verIntra_syn_spec.copy()
    syn_spec.update(conn['syn_spec'])
    ccConnections.append([conn['sources'], conn['targets'], verIntra_conn_spec, syn_spec])


##############################################################################
# Intracortical inhibitory
# ------------------------
#
# We proceed as above, with the following difference: each connection
# is added to both the same-orientation and the cross-orientation list of
# connections.
#
# **Note:** Weights increased from -1.0 to -2.0, to make up for missing GabaB
#
# Note that we have to specify the **weight with negative sign** to make
# the connections inhibitory.
intraInh_conn_spec = {"rule": "pairwise_bernoulli",
                      "mask": {"circular": {"radius": 7.0 * dpc}},
                      "p": 0.25*nest.spatial_distributions.gaussian(nest.spatial.distance, std=7.5 * dpc)}

intraInh_syn_spec = {"synapse_model": "GABA_A",
                     "weight": -2.0,
                     "delay": nest.random.uniform(min=1.75, max=2.25)}

for conn in [{"sources": "L23in", "targets": "L23pyr", "conn_spec": {}},
             {"sources": "L23in", "targets": "L23in", "conn_spec": {}},
             {"sources": "L4in", "targets": "L4pyr", "conn_spec": {}},
             {"sources": "L4in", "targets": "L4in", "conn_spec": {}},
             {"sources": "L56in", "targets": "L56pyr", "conn_spec": {}},
             {"sources": "L56in", "targets": "L56in", "conn_spec": {}}]:
    conn_spec = intraInh_conn_spec.copy()
    conn_spec.update(conn['conn_spec'])
    ccConnections.append([conn['sources'], conn['targets'], conn_spec, intraInh_syn_spec])
    ccxConnections.append([conn['sources'], conn['targets'], conn_spec, intraInh_syn_spec])


##############################################################################
# Corticothalamic
# ---------------
# We proceed as above.
corThal_conn_spec = {"rule": "pairwise_bernoulli",
                     "mask": {"circular": {"radius": 5.0 * dpc}},
                     "p": 0.5*nest.spatial_distributions.gaussian(nest.spatial.distance, std=7.5 * dpc)}

corThal_syn_spec = {"synapse_model": "AMPA",
                    "weight": 1.0,
                    "delay": nest.random.uniform(min=7.5, max=8.5)}

for conn in [{"sources":  "L56pyr", "conn_spec": {}}]:
    conn_spec = intraInh_conn_spec.copy()
    conn_spec.update(conn['conn_spec'])
    syn_spec = intraInh_syn_spec.copy()
    ctConnections.append([conn['sources'], conn_spec, syn_spec])


##############################################################################
# Corticoreticular
# ----------------
#
# In this case, there is only a single connection, so we define the
# dictionaries directly; it is very similar to corThal, and to show that,
# we copy first, then update.
corRet = corThal_conn_spec.copy()
corRet_syn_spec = corThal_syn_spec.copy()
corRet_syn_spec.update({"weight": 2.5})


##############################################################################
# Build all connections beginning in cortex
# -----------------------------------------
#
# Cortico-cortical, same orientation
print("Connecting: cortico-cortical, same orientation")
for source, target, conn_spec, syn_spec in ccConnections:
    for src_i in range(name_dict[source]):
        for tgt_i in range(name_dict[target]):
            source_name = '{}_{}'.format(source, src_i)
            target_name = '{}_{}'.format(target, tgt_i)
            nest.Connect(Vp_h_layers[source_name], Vp_h_layers[target_name], conn_spec, syn_spec)
            nest.Connect(Vp_v_layers[source_name], Vp_v_layers[target_name], conn_spec, syn_spec)

# Cortico-cortical, cross-orientation
print("Connecting: cortico-cortical, other orientation")
for source, target, conn_spec, syn_spec in ccxConnections:
    for src_i in range(name_dict[source]):
        for tgt_i in range(name_dict[target]):
            source_name = '{}_{}'.format(source, src_i)
            target_name = '{}_{}'.format(target, tgt_i)
            nest.Connect(Vp_h_layers[source_name], Vp_v_layers[target_name], conn_spec, syn_spec)
            nest.Connect(Vp_v_layers[source_name], Vp_h_layers[target_name], conn_spec, syn_spec)

# Cortico-thalamic connections
print("Connecting: cortico-thalamic")
for source, conn_spec, syn_spec in ctConnections:
    for src_i in range(name_dict[source]):
        source_name = '{}_{}'.format(source, src_i)
        nest.Connect(Vp_h_layers[source_name], TpRelay, conn_spec, syn_spec)
        nest.Connect(Vp_h_layers[source_name], TpInter, conn_spec, syn_spec)
        nest.Connect(Vp_v_layers[source_name], TpRelay, conn_spec, syn_spec)
        nest.Connect(Vp_v_layers[source_name], TpInter, conn_spec, syn_spec)

for src_i in range(name_dict['L56pyr']):
    source_name = 'L56pyr_{}'.format(src_i)
    nest.Connect(Vp_h_layers[source_name], Rp, corRet, corRet_syn_spec)
    nest.Connect(Vp_v_layers[source_name], Rp, corRet, corRet_syn_spec)


##############################################################################
# Thalamo-cortical connections
# ----------------------------
#
# **Note:** According to the text on p. 1674, bottom right, of the Hill &
# Tononi paper, thalamocortical connections are created by selecting from
# the thalamic population for each L4 pyramidal cell. We must therefore
# specify that we want to select from the source neurons.
#
# We first handle the rectangular thalamocortical connections.
thalCorRect_conn_spec = {"rule": "pairwise_bernoulli",
                         "use_on_source": True}

thalCorRect_syn_spec = {"synapse_model": "AMPA",
                        "weight": 5.0,
                        "delay": nest.random.uniform(min=2.75, max=3.25)}

print("Connecting: thalamo-cortical")

# Horizontally tuned
thalCorRect_conn_spec.update(
    {"mask": {"rectangular": {"lower_left": [-4.0 * dpc, -1.0 * dpc],
                              "upper_right": [4.0 * dpc, 1.0 * dpc]}}})

for conn in [{"targets": "L4pyr", "conn_spec": {"p": 0.5}},
             {"targets": "L56pyr", "conn_spec": {"p": 0.3}}]:
    conn_spec = thalCorRect_conn_spec.copy()
    conn_spec.update(conn['conn_spec'])
    for trg_i in range(name_dict[conn['targets']]):
        target_name = '{}_{}'.format(conn['targets'], trg_i)
        nest.Connect(
            TpRelay, Vp_h_layers[target_name], conn_spec, thalCorRect_syn_spec)

# Vertically tuned
thalCorRect_conn_spec.update(
    {"mask": {"rectangular": {"lower_left": [-1.0 * dpc, -4.0 * dpc],
                              "upper_right": [1.0 * dpc, 4.0 * dpc]}}})

for conn in [{"targets": "L4pyr", "conn_spec": {"p": 0.5}},
             {"targets": "L56pyr", "conn_spec": {"p": 0.3}}]:
    conn_spec = thalCorRect_conn_spec.copy()
    conn_spec.update(conn['conn_spec'])
    for trg_i in range(name_dict[conn['targets']]):
        target_name = '{}_{}'.format(conn['targets'], trg_i)
        nest.Connect(
            TpRelay, Vp_v_layers[target_name], conn_spec, thalCorRect_syn_spec)

# Diffuse connections
thalCorDiff_conn_spec = {"rule": "pairwise_bernoulli",
                         "use_on_source": True,
                         "mask": {"circular": {"radius": 5.0 * dpc}},
                         "p": 0.1*nest.spatial_distributions.gaussian(nest.spatial.distance, std=7.5*dpc)}

thalCorDiff_syn_spec = {"synapse_model": "AMPA",
                        "weight": 5.0,
                        "delay": nest.random.uniform(min=2.75, max=3.25)}

for conn in [{"targets": "L4pyr"},
             {"targets": "L56pyr"}]:
    for trg_i in range(name_dict[conn['targets']]):
        target_name = '{}_{}'.format(conn['targets'], trg_i)
        nest.Connect(TpRelay, Vp_h_layers[target_name], thalCorDiff_conn_spec, thalCorDiff_syn_spec)
        nest.Connect(TpRelay, Vp_v_layers[target_name], thalCorDiff_conn_spec, thalCorDiff_syn_spec)


##############################################################################
# Thalamic connections
# --------------------
#
# Connections inside thalamus, including Rp.
#
# *Note:* In Hill & Tononi, the inhibition between Rp cells is mediated by
# GABA_B receptors. We use GABA_A receptors here to provide some
# self-dampening of Rp.
#
# **Note 1:** The following code had a serious bug in v. 0.1: During the first
# iteration of the loop, "synapse_model" and "weights" were set to "AMPA" and
# "0.1", respectively and remained unchanged, so that all connections were
# created as excitatory connections, even though they should have been
# inhibitory. We now specify synapse_model and weight explicitly for each
# connection to avoid this.
#
# **Note 2:** The following code also had a serious bug in v. 0.4: In the
# loop the connection dictionary would be updated directly, i.e. without
# making a copy. This lead to the entry ``'sources': 'TpInter'`` being
# left in the dictionary when connecting with ``Rp`` sources. Therefore no
# connections for the connections with ``Rp`` as source would be created
# here.

thal_conn_spec = {"rule": "pairwise_bernoulli"}
thal_syn_spec = {"delay": nest.random.uniform(min=1.75, max=2.25)}

print("Connecting: intra-thalamic")

for src, tgt, conn, syn in [(TpRelay, Rp,
                             {"mask": {"circular": {"radius": 2.0 * dpc}},
                              "p": nest.spatial_distributions.gaussian(
                                 nest.spatial.distance, std=7.5*dpc)},
                             {"synapse_model": "AMPA",
                              "weight": 2.0}),
                            (TpInter, TpRelay,
                             {"mask": {"circular": {"radius": 2.0 * dpc}},
                              "p": 0.25*nest.spatial_distributions.gaussian(
                                 nest.spatial.distance, std=7.5*dpc)},
                             {"synapse_model": "GABA_A",
                              "weight": -1.0}),
                            (TpInter, TpInter,
                             {"mask": {"circular": {"radius": 2.0 * dpc}},
                              "p": 0.25*nest.spatial_distributions.gaussian(
                                 nest.spatial.distance, std=7.5*dpc)},
                             {"synapse_model": "GABA_A", "weight": -1.0}),
                            (Rp, TpRelay, {"mask": {"circular": {"radius": 12.0 * dpc}},
                                           "p": 0.15*nest.spatial_distributions.gaussian(
                                               nest.spatial.distance, std=7.5*dpc)},
                             {"synapse_model": "GABA_A", "weight": -1.0}),
                            (Rp, TpInter, {"mask": {"circular": {"radius": 12.0 * dpc}},
                                           "p": 0.15*nest.spatial_distributions.gaussian(
                                               nest.spatial.distance, std=7.5*dpc)},
                             {"synapse_model": "GABA_A", "weight": -1.0}),
                            (Rp, Rp, {"mask": {"circular": {"radius": 12.0 * dpc}},
                                      "p": 0.5*nest.spatial_distributions.gaussian(
                                          nest.spatial.distance, std=7.5*dpc)},
                             {"synapse_model": "GABA_A", "weight": -1.0})
                            ]:
    conn_spec = thal_conn_spec.copy()
    conn_spec.update(conn)
    syn_spec = thal_syn_spec.copy()
    syn_spec.update(syn)
    nest.Connect(src, tgt, conn_spec, syn_spec)


##############################################################################
# Thalamic input
# --------------
#
# Input to the thalamus from the retina.
#
# **Note:** Hill & Tononi specify a delay of 0 ms for this connection.
# We use 1 ms here.
retThal_conn_spec = {"rule": "pairwise_bernoulli",
                     "mask": {"circular": {"radius": 1.0 * dpc}},
                     "p": 0.75*nest.spatial_distributions.gaussian(nest.spatial.distance, std=2.5*dpc)}

retThal_syn_spec = {"weight": 10.0,
                    "delay": 1.0,
                    "synapse_model": "AMPA"}

print("Connecting: retino-thalamic")

nest.Connect(retina, TpRelay, retThal_conn_spec, retThal_syn_spec)
nest.Connect(retina, TpInter, retThal_conn_spec, retThal_syn_spec)


##############################################################################
# Checks on connections
# ---------------------
#
# As a very simple check on the connections created, we inspect
# the connections from the central node of various layers.

# Connections from Retina to TpRelay
retina_ctr_node_id = nest.FindCenterElement(retina)
retina_ctr_index = retina.index(retina_ctr_node_id.global_id)
conns = nest.GetConnections(retina[retina_ctr_index], TpRelay)
nest.PlotTargets(retina[retina_ctr_index], TpRelay, 'AMPA')
plt.title('Connections Retina -> TpRelay')

# Connections from TpRelay to L4pyr in Vp (horizontally tuned)
TpRelay_ctr_node_id = nest.FindCenterElement(TpRelay)
TpRelay_ctr_index = TpRelay.index(TpRelay_ctr_node_id.global_id)
nest.PlotTargets(TpRelay[TpRelay_ctr_index], Vp_h_layers['L4pyr_0'], 'AMPA')
plt.title('Connections TpRelay -> Vp(h) L4pyr')

# Connections from TpRelay to L4pyr in Vp (vertically tuned)
nest.PlotTargets(TpRelay[TpRelay_ctr_index], Vp_v_layers['L4pyr_0'], 'AMPA')
plt.title('Connections TpRelay -> Vp(v) L4pyr')

# Block until the figures are closed before we continue.
plt.show(block=True)


##############################################################################
# Recording devices
# -----------------
#
# This recording device setup is a bit makeshift. For each population
# we want to record from, we create one ``multimeter``, then select
# all nodes of the right model from the target population and
# connect. ``loc`` is the subplot location for the layer.
print("Connecting: Recording devices")
recorders = {}

for name, loc, population in [('TpRelay', 0, TpRelay),
                              ('Rp', 1, Rp),
                              ('Vp_v L4pyr 1', 2, Vp_v_layers['L4pyr_0']),
                              ('Vp_v L4pyr 2', 3, Vp_v_layers['L4pyr_1']),
                              ('Vp_h L4pyr 1', 4, Vp_h_layers['L4pyr_0']),
                              ('Vp_h L4pyr 2', 5, Vp_h_layers['L4pyr_1'])]:
    recorders[name] = (nest.Create('RecordingNode'), loc)
    # one recorder to all targets
    nest.Connect(recorders[name][0], population)


##############################################################################
# Example simulation
# --------------------
#
# This simulation is set up to create a step-wise visualization of
# the membrane potential. To do so, we simulate ``sim_interval``
# milliseconds at a time, then read out data from the multimeters,
# clear data from the multimeters and plot the data as pseudocolor
# plots.

# show time during simulation
nest.SetKernelStatus({'print_time': True})

# lower and upper limits for color scale, for each of the
# populations recorded.
vmn = [-80, -80, -80, -80, -80, -80]
vmx = [-50, -50, -50, -50, -50, -50]

nest.Simulate(Params['sim_interval'])

# Set up the figure, assume six recorders.
fig, axes = plt.subplots(2, 3)
images = []

for i, ax in enumerate(axes.flat):
    # We initialize with an empty image
    images.append(ax.imshow([[0.]], aspect='equal', interpolation='nearest',
                            extent=(0, Params['N'] + 1, 0, Params['N'] + 1),
                            vmin=vmn[i], vmax=vmx[i], cmap='plasma'))
    fig.colorbar(images[-1], ax=ax)

# loop over simulation intervals
for t in np.arange(0, Params['simtime'], Params['sim_interval']):

    # do the simulation
    nest.Simulate(Params['sim_interval'])

    # now plot data from each recorder in turn
    for name, rec_item in recorders.items():
        recorder, subplot_pos = rec_item
        ax = axes.flat[subplot_pos]
        im = images[subplot_pos]

        d = recorder.get('events', 'V_m')
        # clear data from multimeter
        recorder.n_events = 0

        # update image data and title
        im.set_data(np.reshape(d, (Params['N'], Params['N'])))
        ax.set_title(name + ', t = %6.1f ms' % nest.GetKernelStatus()['time'])

    # We need to pause because drawing of the figure happens while the main code is sleeping
    plt.pause(0.0001)

# just for some information at the end
pprint(nest.GetKernelStatus())
