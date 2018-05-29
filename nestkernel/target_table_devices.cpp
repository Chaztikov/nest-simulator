/*
 *  target_table_devices.cpp
 *
 *  This file is part of NEST.
 *
 *  Copyright (C) 2004 The NEST Initiative
 *
 *  NEST is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  NEST is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with NEST.  If not, see <http://www.gnu.org/licenses/>.
 *
 */

#include "target_table_devices_impl.h"

// Includes from nestkernel:
#include "kernel_manager.h"
#include "connector_base.h"
#include "vp_manager_impl.h"

nest::TargetTableDevices::TargetTableDevices()
{
}

nest::TargetTableDevices::~TargetTableDevices()
{
}

void
nest::TargetTableDevices::initialize()
{
  const thread num_threads = kernel().vp_manager.get_num_threads();
  target_to_devices_.resize( num_threads );
  target_from_devices_.resize( num_threads );
  sending_devices_gids_.resize( num_threads );

#pragma omp parallel
  {
    const thread tid = kernel().vp_manager.get_thread_id();
    target_to_devices_[ tid ] =
      new std::vector< std::vector< ConnectorBase* > >( 0 );
    target_from_devices_[ tid ] =
      new std::vector< std::vector< ConnectorBase* > >( 0 );
    sending_devices_gids_[ tid ] = new std::vector< index >( 0 );
  } // of omp parallel
}

void
nest::TargetTableDevices::finalize()
{
  for (
    std::vector< std::vector< std::vector< ConnectorBase* > >* >::iterator it =
      target_to_devices_.begin();
    it != target_to_devices_.end();
    ++it )
  {
    for ( std::vector< std::vector< ConnectorBase* > >::iterator iit =
            ( *it )->begin();
          iit != ( *it )->end();
          ++iit )
    {
      for ( std::vector< ConnectorBase* >::iterator iiit = ( *iit ).begin();
            iiit != ( *iit ).end();
            ++iiit )
      {
        delete *iiit;
      }
      ( *iit ).clear();
    }
    delete *it;
  }
  target_to_devices_.clear();
  for (
    std::vector< std::vector< std::vector< ConnectorBase* > >* >::iterator it =
      target_from_devices_.begin();
    it != target_from_devices_.end();
    ++it )
  {
    for ( std::vector< std::vector< ConnectorBase* > >::iterator iit =
            ( *it )->begin();
          iit != ( *it )->end();
          ++iit )
    {
      for ( std::vector< ConnectorBase* >::iterator iiit = ( *iit ).begin();
            iiit != ( *iit ).end();
            ++iiit )
      {
        delete *iiit;
      }
      ( *iit ).clear();
    }
    delete *it;
  }
  target_from_devices_.clear();
  for ( std::vector< std::vector< index >* >::iterator it =
          sending_devices_gids_.begin();
        it != sending_devices_gids_.end();
        ++it )
  {
    delete *it;
  }
  sending_devices_gids_.clear();
}

void
nest::TargetTableDevices::resize_to_number_of_neurons()
{
  const thread num_threads = kernel().vp_manager.get_num_threads();
  for ( thread tid = 0; tid < num_threads; ++tid )
  {
    target_to_devices_[ tid ]->resize(
      kernel().node_manager.get_max_num_local_nodes() + 1 );
    target_from_devices_[ tid ]->resize(
      kernel().node_manager.get_num_local_devices() + 1 );
    sending_devices_gids_[ tid ]->resize(
      kernel().node_manager.get_num_local_devices() + 1 );
  }
}

void
nest::TargetTableDevices::resize_to_number_of_synapse_types()
{
  const thread num_threads = kernel().vp_manager.get_num_threads();
  for ( thread tid = 0; tid < num_threads; ++tid )
  {
    for ( index lid = 0; lid < target_to_devices_[ tid ]->size(); ++lid )
    {
      // make sure this device has support for all synapse types
      ( *target_to_devices_[ tid ] )[ lid ].resize(
        kernel().model_manager.get_num_synapse_prototypes(), NULL );
    }
    for ( index ldid = 0; ldid < target_from_devices_[ tid ]->size(); ++ldid )
    {
      // make sure this device has support for all synapse types
      ( *target_from_devices_[ tid ] )[ ldid ].resize(
        kernel().model_manager.get_num_synapse_prototypes(), NULL );
    }
  }
}

void
nest::TargetTableDevices::get_connections_to_devices_(
  const index requested_source_gid,
  const index requested_target_gid,
  const thread tid,
  const synindex syn_id,
  const long synapse_label,
  std::deque< ConnectionID >& conns ) const
{
  if ( requested_source_gid != 0 )
  {
    const index lid = kernel().vp_manager.gid_to_lid( requested_source_gid );
    get_connections_to_device_for_lid_(
      lid, requested_target_gid, tid, syn_id, synapse_label, conns );
  }
  else
  {
    for ( index lid = 0; lid < target_to_devices_[ tid ]->size(); ++lid )
    {
      get_connections_to_device_for_lid_(
        lid, requested_target_gid, tid, syn_id, synapse_label, conns );
    }
  }
}

void
nest::TargetTableDevices::get_connections_to_device_for_lid_( const index lid,
  const index requested_target_gid,
  const thread tid,
  const synindex syn_id,
  const long synapse_label,
  std::deque< ConnectionID >& conns ) const
{
  if ( ( *target_to_devices_[ tid ] )[ lid ].size() > 0 )
  {
    const index source_gid = kernel().vp_manager.lid_to_gid( lid );
    // not the root subnet and valid connector
    if ( source_gid > 0
      and ( *target_to_devices_[ tid ] )[ lid ][ syn_id ] != NULL )
    {
      ( *target_to_devices_[ tid ] )[ lid ][ syn_id ]->get_all_connections(
        source_gid, requested_target_gid, tid, syn_id, synapse_label, conns );
    }
  }
}

void
nest::TargetTableDevices::get_connections_from_devices_(
  const index requested_source_gid,
  const index requested_target_gid,
  const thread tid,
  const synindex syn_id,
  const long synapse_label,
  std::deque< ConnectionID >& conns ) const
{
  for ( std::vector< index >::const_iterator it =
          sending_devices_gids_[ tid ]->begin();
        it != sending_devices_gids_[ tid ]->end();
        ++it )
  {
    const index source_gid = *it;
    if ( source_gid > 0
      and ( requested_source_gid == source_gid or requested_source_gid == 0 ) )
    {
      const Node* source =
        kernel().node_manager.get_node_or_proxy( source_gid, tid );
      const index ldid = source->get_local_device_id();

      if ( ( *target_from_devices_[ tid ] )[ ldid ].size() > 0 )
      {
        // not the root subnet and valid connector
        if ( ( *target_from_devices_[ tid ] )[ ldid ][ syn_id ] != NULL )
        {
          ( *target_from_devices_[ tid ] )[ ldid ][ syn_id ]
            ->get_all_connections( source_gid,
              requested_target_gid,
              tid,
              syn_id,
              synapse_label,
              conns );
        }
      }
    }
  }
}

void
nest::TargetTableDevices::get_connections( const index requested_source_gid,
  const index requested_target_gid,
  const thread tid,
  const synindex syn_id,
  const long synapse_label,
  std::deque< ConnectionID >& conns ) const
{
  // collect all connections from neurons to devices
  get_connections_to_devices_( requested_source_gid,
    requested_target_gid,
    tid,
    syn_id,
    synapse_label,
    conns );

  // collect all connections from devices
  get_connections_from_devices_( requested_source_gid,
    requested_target_gid,
    tid,
    syn_id,
    synapse_label,
    conns );
}