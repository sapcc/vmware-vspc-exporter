from aioprometheus import Gauge
import socket


# Define some constant labels that need to be added to all metrics
const_labels = {
    "kubernetes_pod_name": socket.gethostname(),
}


WaitingBytesInReceiveQueue = Gauge(
    'openstack_compute_vspc_waiting_bytes_in_receive_queue',
    'The number of bytes waiting in the receive queue',
    const_labels=const_labels,
)


ActiveConnections = Gauge(
    'openstack_compute_vspc_active_connections',
    'The number of active connections in Pod',
    const_labels=const_labels,
)


METRICS = {
    WaitingBytesInReceiveQueue.name: WaitingBytesInReceiveQueue,
    ActiveConnections.name: ActiveConnections,
}
