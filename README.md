# VMWARE VSPC EXPORTER

This is an exporter for openstack nova vspc, which exports the following metrics

- The number of bytes waiting in the receive queue to Pod
  - `openstack_compute_vspc_waiting_bytes_in_receive_queue`
- The number of active connections in Pod
  - `openstack_compute_vspc_active_connections`
