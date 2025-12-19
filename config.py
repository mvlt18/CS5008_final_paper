"""
This file contains the configuration for the simulation.
It includes the TIMEOUT_RANGE, CLUSTER_SIZES, and SIMULATION_TIMEOUT.

1) The TIMEOUT_RANGE specifies the range of timeouts for the election process, it is 
used to introduce randomness in the election process. It prevents multiple nodes from 
starting elections at the same time.

2) The SIMULATION_TIMEOUT specifies the maximum time allowed for the simulation to run. It is set to 45 seconds 
to allow for a reasonable amount of time for the election process to complete (especially for larger clusters).

3) The CLUSTER_SIZES specifies the range of cluster sizes to be tested in the simulation.
It starts at 3 and goes up to 201 with a step of 10. 
"""

TIMEOUT_RANGE = (.15, .30) # seconds 
SIMULATION_TIMEOUT = 45 # seconds
CLUSTER_SIZES = range(3, 201, 10) 
