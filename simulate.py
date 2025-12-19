"""
This file simulates a Raft consensus algorithm cluster.

It runs a series of simulations with different cluster sizes and records results in a CSV file.
"""

from raft import RaftNode
import time
import csv
import config

# Initialize an empty list to store results
results = [] 

# Iterate over different cluster sizes
for size in config.CLUSTER_SIZES:
    # Initialize shared flags for the cluster
    shared_cluster_flags = { 
        'leader_elected': False,  
        'time_to_leader': None, 
        'start_time': time.time(), 
        'stop': False 
    }

    # Create a cluster of RaftNodes instances
    cluster = []
    for i in range(size):
        node = RaftNode(i, cluster, shared_cluster_flags)
        cluster.append(node)

    # Set the cluster attribute for each node
    for node in cluster:
        node.cluster = cluster
        
    # Start the simulation
    timeout = config.SIMULATION_TIMEOUT 
    start_wait = time.time()
    while not shared_cluster_flags['leader_elected'] and time.time() - start_wait < timeout:
        time.sleep(0.1) 

    # Stop all nodes after the simulation ends
    shared_cluster_flags['stop'] = True
    time.sleep(1)

    # Calculate the time taken to elect a leader
    total_elections = sum(node.election_count for node in cluster) 
    stable = total_elections == 1

    # Store results for the current cluster size
    results.append({
        'Cluster Size': size,
        'Time to Leader (s)': round(shared_cluster_flags['time_to_leader'], 2) if shared_cluster_flags['time_to_leader'] else None,
        'Elections Held': total_elections,
        'Stable Leader?': 'Yes' if stable else 'No'
    })

# Write CSV output
csv_path = "raft_simulation_results.csv"
with open(csv_path, "w", newline="") as csvfile:
    fieldnames = ['Cluster Size', 'Time to Leader (s)', 'Elections Held', 'Stable Leader?']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in results:
        writer.writerow(row)

print(f"\nSimulation complete. Results saved to {csv_path}")
