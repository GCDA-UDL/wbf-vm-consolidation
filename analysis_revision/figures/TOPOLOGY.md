# Simulated topology (from the topology file)

- Topology file: ../../topologies/fatTreeTopology_k-2_g-2_s-2_hs-2_h-16.json
- info block: {'numHosts': 16, 'numSwitchs': 18, 'defaultWeightTree': 100, 'numNodes': 34, 'numLinks': 80, 'defaultWeightInterconnected': 1000}
- hosts: 16; switches: 18 (core 2, aggregation 8, edge 8); pods: 4 (each with 2 aggregation and 2 edge switches and 4 hosts)
- links: 40 undirected (80 directed entries): 8 aggregation-core (weight 1000, defaultWeightInterconnected); 16 edge-aggregation (weight 1000, defaultWeightInterconnected); 16 host-edge (weight 100, defaultWeight)
- degree: core [4]; aggregation [3]; edge [4]; host [1]
- host-to-host shortest path, in links (the simulator sets every link weight to 1 in TopologyHostDistanceManager and uses this value as the migration distance): 2 links for 8 host pairs; 4 links for 16 host pairs; 6 links for 96 host pairs; mean over the 120 pairs 5.47
