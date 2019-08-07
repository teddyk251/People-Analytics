from collections import defaultdict
import abc
import numpy as np

class Graph(defaultdict):
    """Parent class of all graphs. This class provides  an interface to all other classes 
    which implement graph networks.
    
    Arguments:
        defaultdict {collections.defaultdict} -- Parent class
    
    """
    def __init__(self, directed):
        """Initializes Graph object.
        
        Arguments:
            factory {type} -- Which factory to use as argument to the defaultdict initialization.
            directed {bool} -- True if the layers are directed graphs
        
        Returns:
        """
        self.directed = directed
        self.factory = self._get_factory
        self._nodes = set()
        return super(Graph, self).__init__(self.factory)
    @abc.abstractmethod
    def get_column_names(self):
        raise NotImplementedError("Not implemented")
    @abc.abstractmethod
    def get_edgelist(self, data=True, sum_weights=False):
        raise NotImplementedError("Not implemented")
    @abc.abstractmethod
    def _get_factory(self):
        raise NotImplementedError("Not implemented")
    def add_node(self, node):
        """Adds a node to this graph
        
        Arguments:
            node {str, int} -- A node(an entity of a graph which interact with each other.).
        """
        self._nodes.add(node)
    def add_nodes(self, nodes):
        """Adds list of nodes to this graph
        
        Arguments:
            nodes {list} -- List  of nodes to add.
        """
        for node in nodes:
            self.add_node(node)
    @abc.abstractmethod
    def add_edge(self, edge):
        """Adds edge to this graph
        
        Arguments:
            edge {tuple} -- Edge to be added
        """
        return
    def add_edges(self, edges):
        """Adds multiple edge to this graph
        
        Arguments:
            edges {list} -- List of edges to be added
        """
        for edge in edges:
            self.add_edge(edge)
    def delete_node(self, node):
        """Removes a node from this graph. All edges that are incident to the given node are also get removed.
        
        Arguments:
            node {str, int} -- A node to remove from graph
        """
        self.pop(node, None)
        for n in self:
            if node in self[n]:
                self.delete_edge((n, node))
        self._nodes.remove(node)
    def delete_nodes(self, nodes):
        """Removes list of nodes and edges incident to these nodes from this graph.
        
        Arguments:
            nodes {list} -- List of node to remove.
        """
        for node in nodes:
            self.delete_node(node)
    @abc.abstractmethod
    def delete_edge(self, edge):
        """Removes a given edge from this graph.
        Arguments:
            edge {tuple} -- Tuple representing the edge to be removed
        """
        return
    def delete_edges(self, edges):
        """Removes multiple edges from this graph
        
        Arguments:
            edges {list} -- Edges to be removed from this graph
        """
        for edge in edges:
            self.delete_edge(edge)
    def get_nodes(self):
        """Returns nodes of this graph
        
        Returns:
            set -- Nodes of this graph
        """
        return self._nodes
    @abc.abstractmethod
    def get_edges(self, data=True, sum_weights=False):
        """Returns edges of this graph      
        Arguments:
            data {bool} -- If true includes edge weights
        Returns:
            list -- List of edges in this graph
        """
        return
    def get_neighbors(self, node, include_incoming_connection=True):
        """Returns nodes which share common edge with the given node
        
        Arguments:
            node {str, int} -- A node in this
        
        Returns:
            set -- Set of nodes which share common edge with given node
        """
        output = set([target for target in self[node]])
        if include_incoming_connection:
            for n in self:
                if node in self[n]:
                    output.add(n)
        return output
    def contains_node(self, node):
        """Check if node presents in this graph
        
        Arguments:
            node {str, int} -- A node 
        
        Returns:
            bool -- True if node exists in this graph else false.
        """
        return node in self._nodes
    @abc.abstractmethod
    def contains_edge(self, edge):
        """Check if a given edge exists in this graph
        
        Arguments:
            edge {tuple} -- An edge.
        
        Returns:
            bool -- True if this graph contains the given edge else false
        """
        return ;
    def copy(self, deep=False):
        """Returns shallow copy of this object
        
        Keyword Arguments:
            deep {bool} -- If true returns deep copy of this object and else returns shallow copy (default: {False})
        
        Raises:
            NotImplementedError: Deep copy should be implemented by classes which implement this class
        
        Returns:
            Graph -- Copy of this graph
        """
        if not deep:
            return self
        raise NotImplementedError("Not implemented for deep==True")
    @abc.abstractmethod
    def to_visjs_format(self):
        raise NotImplementedError("Not implemented yet")
    @abc.abstractmethod
    def get_graph_type(self):
        raise NotImplementedError("Not implemented yet")
class UnweightedGraph(Graph):
    def __init__(self, directed=False):
        super(UnweightedGraph, self).__init__(directed)
    def _get_factory(self):
        """Returns set object when called by defaultdict
        
        Returns:
            set -- Set object
        """
        return set()
    def add_edge(self, edge):
        source, target = edge
        self[source].add(target)
        if not self.directed:
            self[target].add(source)
        self.add_nodes([source, target])
    def delete_edge(self, edge):
        source, target = edge
        self[source].remove(target)
        if not self.directed:
            self[target].remove(source)
    def get_edges(self, data=False, sum_weights=False):
        output = []
        for node in self:
            for neighbor in self[node]:
                output.append((node, neighbor))
        return output
    def contains_edge(self, edge):
        source, target = edge
        if self.directed:
            return source in self and target in self[source]
        else:
            return (source in self and target in self[source]) or (target in self and source in self[target])
    def copy(self, deep=False):
        if not deep:
            return super(UnweightedGraph, self).copy(deep)
        output = UnweightedGraph(self.directed)
        output.add_edges(self.get_edges())
        return output
    def get_column_names(self):
        return ("source", "target")
    def get_edgelist(self, data=True, sum_weights=False):
        return self.get_edges()
    def to_visjs_format(self):
        nodes = list(self.get_nodes())
        edges = []
        for source in self:
            for target in self[source]:
                edges.append({"from":source, "to":target})
        return {"nodes":nodes, "edges":edges}
    def get_graph_type(self):
        return "unweighted"
class WeightedGraph(Graph):
    def __init__(self, directed=False, weight_is_list=False):
        self.weight_is_list = weight_is_list
        super(WeightedGraph, self).__init__( directed)
    def _get_factory(self):
        """Returns defaultdict object when called
        
        Returns:
            defaultdict -- defaultdict object
        """
        if self.weight_is_list:
            return defaultdict(list)
        else:
            return defaultdict(float)
    def add_edge(self, edge):
        source, target, data = edge
        if type(data) == dict:
            weight = data["weight"]
        else:
            weight = data
        if self.weight_is_list:
            self[source][target].append(weight)
        else:
            self[source][target] += weight
        if not self.directed:
            if self.weight_is_list:
                if type(weight) == list:
                    self[target][source].extend(weight)
                else:
                    self[target][source].append(weight)
            else:
                self[target][source] += weight
        self.add_nodes([source, target])
    def delete_edge(self, edge):
        if(len(edge)==2):
            source, target = edge
        elif len(edge)==3:
            source, target, weight = edge
        else:
            raise ValueError("Unexpected edge format: %s"%str(edge))
        self[source].pop(target, None)
        if not self.directed:
            self[target].pop(source, None)
    def get_edges(self, data=True, sum_weights=False):
        output = []
        for node in self:
            for neighbor in self[node]:
                if data:
                    if self.weight_is_list:
                        if sum_weights:
                            output.append((node, neighbor, np.sum(self[node][neighbor])))
                        else:
                            output.append((node, neighbor, np.mean(self[node][neighbor])))
                    else:
                        output.append((node, neighbor, self[node][neighbor]))

                else:
                    output.append((node, neighbor))

        return output
    def contains_edge(self, edge):
        source, target = edge
        if self.directed:
            return source in self and target in self[source]
        else:
            return (source in self and target in self[source]) or (target in self and source in self[target])
    def copy(self, deep=False):
        if not deep:
            return super(WeightedGraph, self).copy(deep)
        output = WeightedGraph(self.directed, self.weight_is_list)
        output.add_edges(self.get_edges())
        return output
    def random_walk_generator(self, p=1, q=1, walk_length=5):
        pass
    def get_column_names(self):
        return ("source", "target", "weight")
    def get_edgelist(self, data=True, sum_weights=False):
        return self.get_edges(data=data, sum_weights=sum_weights)
    def to_visjs_format(self):
        nodes = list(self.get_nodes())
        edges = []
        for source in self:
            for target in self[source]:
                edges.append({"from": source, "to": target, "weight": self[source][target]})
        return {"nodes": nodes, "edges": edges}
    def get_graph_type(self):
        return "weighted"
class MultiplexGraph(Graph):
    def __init__(self, directed=False, weight_is_list=False):
        """Datastructure that represents  multiplex multilayer graphs.
        
        Arguments:
            Graph {type} -- Parent class
        
        Keyword Arguments:
            directed {bool} -- True if graph is directed. (default: {False})
            weight_is_list {bool} -- True if weight of edge represented by list (default: {False})
        """
        self.weight_is_list = weight_is_list
        super(MultiplexGraph, self).__init__(directed)
    def _get_factory(self):
        if self.weight_is_list:
            return defaultdict(lambda: defaultdict(list))
        else:
            return defaultdict(lambda: defaultdict(float))

    def add_edge(self, edge):
        source, target, r_type, data = edge
        if type(data) == dict:
            weight = data["weight"]
        else:
            weight = data
        if not self.weight_is_list:
            self[source][target][r_type] += weight
            if not self.directed:
                self[target][source][r_type] += weight
        else:
            self[source][target][r_type].append(weight)
            if not self.directed:
                self[target][source][r_type].append(weight)
        self.add_nodes([source, target])
    def delete_edge(self, edge):
        if(len(edge)==3):
            source, target, rel = edge
        elif len(edge)==4:
            source, target, rel, weight = edge
        else:
            raise ValueError("Unexpected edge format: %s"%str(edge))
        self[source][target].pop(rel, None)
        if not self.directed:
            self[target][source].pop(rel, None)
    def get_edges(self, data=True, sum_weights=False):
        output = []
        for node in self:
            for neighbor in self[node]:
                for rel in self[node][neighbor]:
                    if data:
                        if sum_weights:
                            output.append((node, neighbor, rel, {"weight": np.sum(self[node][neighbor][rel])}))
                        else:
                            output.append((node, neighbor, rel, {"weight": np.mean(self[node][neighbor][rel])}))
                    else:
                        output.append((node, neighbor, rel))

        return output
    
    def contains_edge(self, edge):
        source, target, relation = edge
        if self.directed:
            return source in self and target in self[source] and relation in self[source][target]
        else:
            return (source in self and target in self[source] and relation in self[source][target]) or (target in self and source in self[target] and relation in self[target][source])
    def copy(self, deep=False):
        if not deep:
            return super(MultiplexGraph, self).copy(deep)
        output = MultiplexGraph(self.directed, self.weight_is_list)
        output.add_edges(self.get_edges())
        return output
    
    def get_layer(self, layer):
        """Contracts weighted graph from this graph where the edges are from specified layer of this graph.
        
        Arguments:
            layer {str} -- Layer name(relation type)
        
        Returns:
            [WeightedGraph] -- WeigthedGraph constructed from a given layer of this graph
        """
        output = WeightedGraph(self.directed, self.weight_is_list)
        for node in self:
            for neighbor in self[node]:
                if layer in self[node][neighbor]:
                    output.add_edge((node, neighbor, {"weight": self[node][neighbor][layer]}))
        return output
    def get_column_names(self):
        return ("source", "target", "relation", "weight")
    def get_edgelist(self, data=True, sum_weights=False):
        return self.get_edges(data=data, sum_weights=sum_weights)
    def to_visjs_format(self):
        nodes = list(self.get_nodes())
        edges = []
        for source in self:
            for target in self[source]:
                for relation in self[source][target]:
                    edges.append({"from":source, "to":target, "relation": relation, "weight":self[source][target][relation]})
        return {"nodes": nodes, "edges": edges}
    def get_graph_type(self):
        return "multiplex"