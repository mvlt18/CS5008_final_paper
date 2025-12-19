""" 
This file contains the implementation of a simplified version of the Raft consensus algorithm.

Focus: The leader election process and the state management of each node in the cluster.

It includes a RaftNode class that represents a node in the cluster, handles leader election, and manages the state of each node.

The simulation 
    - runs a cluster of nodes, where each node can be in one of three states: Follower, Candidate, or Leader.
    - will run until a leader is elected or a timeout occurs.
    - results are saved to a CSV file. 
"""

from typing import List, Dict

import threading 
import time
import random
import config

"""
The RaftNode class represents a node in the Raft consensus algorithm.

It includes methods for:
1) handling leader election
2) state management
3) communication with other nodes in the cluster.

Attributes:
    node_id: unique identifier for the node
    cluster: list of all nodes in the cluster
    state: current state of the node (Follower, Candidate, Leader)
    votes_received: number of votes received in the current election
    current_term: current term of the node
    voted_for: ID of the candidate the node voted for
    election_timeout: timeout for the election
    shared_cluster_flags: shared data between nodes
    election_count: number of elections held by this node

Methods:
    generate_election_timeout: generates a random timeout value within the specified range
    election_timer: checks if the election timeout is reached and starts a new election
    start_election: initiates a new election
    receive_vote_request: handles incoming vote requests from other nodes
    receive_vote: handles incoming votes from other nodes
    check_if_won: checks if the node has received a majority of votes
    become_leader: changes the node's state to Leader and starts sending heartbeats
    send_heartbeats: starts a background thread to send heartbeats to followers
    heartbeat: sends heartbeats to followers to maintain leadership
    reset_election_timeout: resets the election timeout for the node
"""
class RaftNode:

    """
    Initializes a new RaftNode instance. 

    Args:
        node_id (int): unique identifier for the node
        cluster (List[RaftNode]): list of all nodes in the cluster
        shared_cluster_flags (dict): shared data between nodes
    """
    def __init__(self, node_id: int, cluster: List["RaftNode"], shared_cluster_flags: Dict): 
        self.node_id = node_id # unique identifier for the node
        self.cluster = cluster # list of all nodes in the cluster
        self.state = 'Follower' # initial state of the node
        self.votes_received = 0 # number of votes received in the current election, initially 0
        self.current_term = 0 # current term of the node, initially 0
        self.voted_for = None # ID of the candidate the node voted for
        self.election_timeout = self.generate_election_timeout() # timeout for the election
        self.shared_cluster_flags = shared_cluster_flags # shared data between nodes
        self.election_count = 0 # number of elections held by this node, initially 0

        self.election_thread = threading.Thread(target=self.election_timer) # thread for election timeout
        self.election_thread.daemon = True # set as daemon thread
        self.election_thread.start() # start the election timer thread


    """
    Generates a new random election timeout (between TIMEOUT_RANGE). 

        Returns:
            float: A future timestamp when this node will timeout.
    """
    def generate_election_timeout(self):
        # get current time and add a random value within the timeout range
        return time.time() + random.uniform(*config.TIMEOUT_RANGE) 


    """
    Monitors the election timeout in a separate thread. Starts a new election if the timeout is reached and the node is not a leader.
    """
    def election_timer(self):
        while not self.shared_cluster_flags['stop']: # while the simulation is running
            time.sleep(0.05) # sleep for .05 seconds to avoid 'busy waiting' 
            if self.state != 'Leader' and time.time() > self.election_timeout: # if not leader and timeout reached
                self.start_election() # start a new election!


    """
    Starts a new election by changing the node's state to Candidate, incrementing the current term, and requesting votes from other nodes.

    Returns:
        None
    """
    def start_election(self):
        self.state = 'Candidate' # change state to Candidate
        self.current_term += 1 # increment the current term
        self.votes_received = 1 # reset votes received to 1 (vote for self)
        self.voted_for = self.node_id # vote for self, indicating that this node has voted for itself
        self.election_timeout = self.generate_election_timeout() # reset the election timeout to a new random value
        self.election_count += 1 # increment the election count
        # send vote requests to all other nodes in the cluster
        for node in self.cluster:
            if node.node_id != self.node_id:
                node.receive_vote_request(self.node_id, self.current_term)
        self.check_if_won() # check if the node has won the election


    """
    Handles a vote request from a candidate node.
    It checks if the request is valid (for this simple implementation this means): 
        1) the term is greater than the current term 
        AND
        2) the node has not voted yet
    
        Args:
            candidate_id (int): ID of the candidate requesting the vote
            term (int): term of the candidate requesting the vote

    Returns:
        None

    """
    def receive_vote_request(self, candidate_id: int, term: int):
        if term > self.current_term and self.voted_for is None: # check if the term is greater and not voted yet
            self.voted_for = candidate_id # vote for the candidate
            self.current_term = term # update the current term (can only vote for one candidate per term)
            for node in self.cluster: # send vote back to the candidate
                if node.node_id == candidate_id: 
                    node.receive_vote() 
                    break


    """
    Handles receiving a vote from another node. It increments the votes received and checks if the node has won the election.

    Returns:
        None
    """
    def receive_vote(self):
        self.votes_received += 1
        self.check_if_won()


    """
    Determines if the node has won the election by checking if it has received a majority of votes.
    If yes, becomes a leader and starts sending heartbeats to maintain leadership.

    Returns:
        None
    """
    def check_if_won(self):
        # majority is reached if votes received > half of the cluster size 
        if self.votes_received > len(self.cluster) // 2 and self.state == 'Candidate': # must also be a candidate
            self.become_leader() # become leader! Success. 


    """
    Changes the node's state to Leader and starts sending heartbeats to followers.

    Returns:
        None
    """
    def become_leader(self):
        self.state = 'Leader'  
        if not self.shared_cluster_flags['leader_elected']: 
            self.shared_cluster_flags['leader_elected'] = True
            self.shared_cluster_flags['time_to_leader'] = time.time() - self.shared_cluster_flags['start_time']
        self.send_heartbeats()  # Start a thread to send heartbeats to followers


    """
    Starts a background thread to send heartbeats to followers.

    Returns:
        None
    """
    def send_heartbeats(self):
        threading.Thread(target=self.heartbeat, daemon=True).start()


    """
    Continuously sends heartbeats to followers to maintain leadership.
    It resets the election timeout for each follower node (simple implementation).

    Returns:
        None
    """
    def heartbeat(self):
        while self.state == 'Leader' and not self.shared_cluster_flags['stop']:
            for node in self.cluster:
                if node.node_id != self.node_id:
                    node.reset_election_timeout()
            time.sleep(.1)  # Heartbeat interval


    """
    Resets the election timeout for the node.

    Returns:
        None
    """
    def reset_election_timeout(self):
        self.election_timeout = self.generate_election_timeout()
