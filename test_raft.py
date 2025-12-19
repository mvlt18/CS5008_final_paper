import unittest
import time
import config
from raft import RaftNode


class TestRaftNodeMethods(unittest.TestCase):
    """Unit tests for methods of RaftNode."""

    def setUp(self):
        config.TIMEOUT_RANGE = (0.05, 0.1)
        self.shared_flags = {
            'stop': False,
            'leader_elected': False,
            'start_time': time.time(),
            'time_to_leader': None
        }
        # single node for testing
        self.node = RaftNode(node_id=0, cluster=[], shared_cluster_flags=self.shared_flags)

    def test_generate_election_timeout(self):
        """Test that timeout is in the expected future range."""
        now = time.time()
        timeout = self.node.generate_election_timeout()
        self.assertTrue(now + 0.05 <= timeout <= now + 0.1)

    def test_start_election_initializes_state(self):
        """Test that start_election() sets candidate state and self-votes."""
        node2 = RaftNode(node_id=1, cluster=[], shared_cluster_flags=self.shared_flags)
        self.node.cluster = [self.node, node2] 
        node2.cluster = [self.node, node2]

        self.node.start_election()

        self.assertIn(self.node.state, ['Candidate', 'Leader'])
        self.assertEqual(self.node.voted_for, self.node.node_id)
        self.assertEqual(self.node.votes_received, 2)
        self.assertGreaterEqual(self.node.current_term, 1)

    def test_receive_vote_request_grants_vote(self):
        """Node should grant vote if it hasn’t voted and term is higher."""
        self.node.current_term = 1
        self.node.voted_for = None

        candidate = RaftNode(node_id=1, cluster=[self.node], shared_cluster_flags=self.shared_flags)
        candidate.votes_received = 0
        self.node.cluster = [self.node, candidate]

        self.node.receive_vote_request(candidate_id=1, term=2)

        self.assertEqual(self.node.voted_for, 1)
        self.assertEqual(self.node.current_term, 2)

    def test_receive_vote_increments_vote_count(self):
        """Candidate should count incoming vote."""
        self.node.state = 'Candidate'
        self.node.votes_received = 1
        self.node.cluster = [self.node] * 3 

        self.node.receive_vote()
        self.assertEqual(self.node.votes_received, 2)

    def test_check_if_won_becomes_leader(self):
        """If candidate has majority, it becomes leader."""
        self.node.state = 'Candidate'
        self.node.votes_received = 2
        self.node.cluster = [self.node] * 3  

        self.node.check_if_won()
        self.assertEqual(self.node.state, 'Leader')

    def test_become_leader_sets_flag_and_starts_heartbeat(self):
        """Should set leader_elected flag and run heartbeat thread."""
        self.node.cluster = [self.node]
        self.node.become_leader()

        self.assertEqual(self.node.state, 'Leader')
        self.assertTrue(self.shared_flags['leader_elected'])
        self.assertIsNotNone(self.shared_flags['time_to_leader'])


if __name__ == '__main__':
    unittest.main()
