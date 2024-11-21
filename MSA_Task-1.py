import pandas as pd
import os
import numpy as np
import networkx as nx

# Function to import OMX matrices
def import_matrix(matfile):
    f = open(matfile, 'r')
    all_rows = f.read()
    blocks = all_rows.split('Origin')[1:]
    matrix = {}
    for k in range(len(blocks)):
        orig = blocks[k].split('\n')
        dests = orig[1:]
        orig = int(orig[0])
        d = [eval('{' + a.replace(';', ',').replace(' ', '') + '}') for a in dests]
        destinations = {}
        for i in d:
            destinations = {**destinations, **i}
        matrix[orig] = destinations
    zones = max(matrix.keys())
    mat = np.zeros((zones, zones))
    for i in range(zones):
        for j in range(zones):
            mat[i, j] = matrix.get(i+1, {}).get(j+1, 0)
    index = np.arange(zones) + 1
    return matrix, index

# Set up file paths
root = './'
city = 'SiouxFalls'

netfile = os.path.join(root, city, city + '_net.tntp')
ODfile = os.path.join(root, city, city + '_trips.tntp')

# Load network data
network = pd.read_csv(netfile, skiprows=8, sep='\t')
trimmed = [s.strip().lower() for s in network.columns]
network.columns = trimmed
network.drop(['~', ';'], axis=1, inplace=True)
network.rename(columns={'init_node': 'from', 'term_node': 'to'}, inplace=True)

# Build graph
NetGraph = nx.DiGraph()
edge_attr = {}
for row in network.itertuples():
    edge_attr[(row[1], row[2])] = {
        'capacity': row[3],
        'length': row[4],
        'FFT': row[5],
        'alpha': row[6],
        'beta': row[7],
        'type': row[10],
        'flow': 0,
        'cost': row[5],
        'Oflow': None
    }
edge = [(row[1], row[2]) for row in network.itertuples()]
NetGraph.add_edges_from(edge)
nx.set_edge_attributes(NetGraph, edge_attr)

# Load OD matrix
matrix, index = import_matrix(ODfile)
OD_raw = pd.DataFrame.from_dict(matrix, orient='index')
ODdemand = OD_raw.stack().reset_index()
ODdemand.columns = ['Origin', 'Destination', 'Demand']
ODdemand = {(row['Origin'], row['Destination']): row['Demand'] for _, row in ODdemand.iterrows()}
zones2cent = {zone: [zone] for zone in OD_raw.columns.to_list()}

# AON Function
def AONloading(G, zone2cent, Demand, computesptt=False):
    x_bar = {l: 0 for l in G.edges()}
    min_travel_time = {}
    SPTT = 0
    for ozone, onodes in zone2cent.items():
        sspso = [nx.single_source_dijkstra(G, onode, weight='cost') for onode in onodes]
        for dzone, dnodes in zone2cent.items():
            if ozone == dzone:
                continue
            try:
                dem = Demand[(ozone, dzone)]
            except KeyError:
                continue
            if dem <= 0:
                continue
            tempssps = [(sspso[i][0][dnode], sspso[i], dnode) for i in range(len(sspso)) for dnode in dnodes if dnode in sspso[i][0].keys()]
            tempssps = sorted(tempssps, key=lambda x: x[0])
            tt, ssps, dest = tempssps[0]
            min_travel_time[(ozone, dzone)] = tt
            path = ssps[1][dest]
            if computesptt:
                SPTT += tt * dem
            for i in range(len(path) - 1):
                x_bar[(path[i], path[i + 1])] += dem
    return SPTT, x_bar, min_travel_time

# MSA Traffic Assignment
def msa_traffic_assignment(G, zones2cent, Demand, max_iter=1000, tol=1e-4):
    x_current = {edge: 0 for edge in G.edges()}
    min_travel_times = {}
    rel_gap = float('inf')
    iteration = 0

    while iteration < max_iter and rel_gap > tol:
        # Step 1: AON assignment
        SPTT, x_bar, min_travel_time = AONloading(G, zones2cent, Demand, computesptt=True)
        min_travel_times.update(min_travel_time)

        # Step 2: Update flows using MSA
        step_size = 1 / (iteration + 1)
        for edge in G.edges():
            x_current[edge] = (1 - step_size) * x_current[edge] + step_size * x_bar[edge]

        # Step 3: Update edge costs
        for edge in G.edges():
            G[edge[0]][edge[1]]['cost'] = G[edge[0]][edge[1]]['FFT'] * (
                1 + G[edge[0]][edge[1]]['alpha'] * (x_current[edge] / G[edge[0]][edge[1]]['capacity']) ** G[edge[0]][edge[1]]['beta']
            )

        # Step 4: Convergence Check
        TSTT = sum(x_current[edge] * G[edge[0]][edge[1]]['cost'] for edge in G.edges())
        rel_gap = abs(TSTT - SPTT) / SPTT if SPTT > 0 else 0
        iteration += 1

        # Print progress every 10 iterations
        if iteration % 10 == 0 or iteration == 1:
            print(f"Iteration: {iteration}, Relative Gap: {rel_gap:.6f}")

    return x_current, min_travel_times, iteration, rel_gap

# Run MSA
final_flows, min_travel_times, total_iterations, final_gap = msa_traffic_assignment(NetGraph, zones2cent, ODdemand)

# Results
print(f"\nMSA Completed in {total_iterations} iterations with a final relative gap of {final_gap:.6f}")

print("\nFinal Edge Flows:")
for edge, flow in final_flows.items():
    print(f"Edge {edge}: Flow = {flow:.2f}")

print("\nMinimum Travel Times (OD Pairs):")
for od_pair, travel_time in min_travel_times.items():
    print(f"OD Pair {od_pair}: Travel Time = {travel_time:.2f}")
