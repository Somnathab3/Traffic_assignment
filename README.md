# Traffic Assignment Using Method of Successive Averages (MSA)

This repository provides an implementation of **Traffic Assignment** using the **Method of Successive Averages (MSA)** algorithm. The code simulates user equilibrium in traffic networks, where no traveler can improve their travel time by switching routes.

---

## Overview

The program uses a directed graph to represent a transportation network and assigns traffic flows to edges based on travel demand between origin-destination (OD) pairs. The algorithm iteratively adjusts flows until convergence, following the principles of user equilibrium.

### Key Components
1. **Network Representation:**  
   The network is represented as a directed graph using **NetworkX**, with edges containing attributes such as capacity, length, and free-flow travel time.

2. **OD Matrix:**  
   The OD matrix specifies travel demand between origin and destination zones.

3. **All-Or-Nothing (AON) Assignment:**  
   Assigns all demand for each OD pair to the shortest path based on current travel times.

4. **MSA Algorithm:**  
   Iteratively adjusts flows using:
   - Shortest path assignment (AON).
   - Flow updates based on a weighted average.
   - Cost updates using the **BPR cost function**:
     \[
     \text{cost} = \text{FFT} \cdot \left( 1 + \alpha \cdot \left( \frac{\text{flow}}{\text{capacity}} \right)^\beta \right)
     \]

---

## Data Inputs

1. **Network File:**  
   A `.tntp` file containing information about road segments, including:
   - `from` and `to` nodes,
   - `capacity` (maximum flow),
   - `length` (distance),
   - `FFT` (free-flow travel time),
   - `alpha` and `beta` (BPR parameters for congestion modeling).

2. **OD Matrix File:**  
   A `.tntp` file specifying travel demand between origin and destination zones.

---

## Algorithm Workflow

### **Step 1: Data Preparation**
1. Load the network file and create a directed graph using **NetworkX**.
2. Load the OD matrix and store it in a dictionary format.
3. Initialize edge attributes (e.g., flow and cost) in the graph.

---

### **Step 2: All-Or-Nothing (AON) Assignment**
1. For each origin zone:
   - Compute the shortest path tree using Dijkstra’s algorithm.
2. For each destination zone:
   - Assign the entire demand to the shortest path and update edge flows.
3. Optionally, compute the **Shortest Path Total Travel Time (SPTT)**.

---

### **Step 3: MSA Traffic Assignment**
The **Method of Successive Averages (MSA)** algorithm iteratively adjusts flows to find equilibrium:

1. **Initialization:**
   - Start with zero flow on all edges.
   - Set an initial relative gap for convergence.

2. **Iterative Process:**
   - Perform **AON Assignment** to determine shortest path flows.
   - Update flows using the MSA formula:
     \[
     x_{\text{current}} = (1 - \text{step\_size}) \cdot x_{\text{current}} + \text{step\_size} \cdot x_{\text{AON}}
     \]
     where `step_size = 1 / (iteration + 1)`.
   - Update edge costs using the **BPR cost function**:
     \[
     \text{cost} = \text{FFT} \cdot \left( 1 + \alpha \cdot \left( \frac{\text{flow}}{\text{capacity}} \right)^\beta \right)
     \]
   - Compute the **Total System Travel Time (TSTT)** and check the relative gap:
     \[
     \text{rel\_gap} = \frac{|TSTT - SPTT|}{SPTT}
     \]
     Stop if the gap is below the tolerance or the maximum iterations are reached.

3. **Output:**
   - Final edge flows and minimum travel times for each OD pair.

---

## Outputs

1. **Final Edge Flows:**  
   Equilibrium flows for each road segment.

2. **Minimum Travel Times:**  
   Shortest path travel times for all OD pairs.

3. **Convergence Metrics:**  
   Total System Travel Time (TSTT) and relative gap at each iteration.

---

## Example Results

### **Final Edge Flows**
