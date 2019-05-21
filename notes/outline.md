# 0. Very Brief Introduction
I will try to address two classical invert problems
Chinese-Postman Problem (CPP) and Travelling-Salesman Problem (TSP).
In CPP the task to create a route along all the roads in some area
such that it covers each road exactly once.
In TSP one has to creat a route to get to all the cities within some area,
in such way that travelling time is minimum.
Both problems are considered NP-hard problems. 'P' means that time
to get an optimal solution seems to be polinomial
of the number of roads or cities in those problems,
'N' means that nobody really has proven that.
In reality, people are sattisfied with some suboptimal solutions — 
travel along all the roads (possibly more than once),
but try to minimise the extra travelling.
Those solutions cost money. To the best of my knowledge,
one such solution offers a sustom-made app at approximately €50 000 per year;
another offers a route generation for as little as €400 per route.

In here I will use a simulation to show how these two problems can be solved
(it is just a solution, not a panacea, though).
Unlike simulated data,
the algorithms themselves are pretty real though and are in constant use. 

I will also introduce some graph theory concepts essential for understanding.
Not too much, though, because I don't know too much about them.

Finally, I will try to design some simple test cases,
cases which are easy to visualise and understand.

# 1. Get Random City and Random District
First, I will model a random city —
some area, where you can get from any node to any node.
Then, I will select a random district in the city.
Importantly, it may be impossible to get to any node within the district
without crossing its boarders.

To make it more realistic, I included both one-way and two-way streets,
as well as exclude some segments completely.

## 1.A. Visualise City
## 1.B. Get City Statistics
# 2. Graph Introduction
Graph is a set of dots (nodes), some of which are connected by segments (edges).
## 2.A. Directed Graph Vs Undirected Graph
In undirected graph an edge between two nodes (a and b) indicates that each node
can be reached from another node, i.e. edges (a, b) and (b, a) are equal.
In directed graph any edge between two nodes has a direction,
with a source node known as tail and target node known as head.
In directed graph edges (a, b) and (b, a) have opposit directions
and are not equal.
## 2.B. Strongly Connected Graph
## 2.C. Graph Representation in NetworkX
Essentially, a graph is comprised of two collections — collection of nodes
(each node has a unique name, and some node attributes) and collection of edges
(each edge is uniquely defined by the nodes it connects, and some edge
attributes).
Node attributes can be anything including node coordinates. Importantly,
two nodes with identical coordinates but different names, are different nodes.
## 2.D. Links
# 2. Get City and District Graphs
## 2.A. Visualise 