from collections import defaultdict
import abc
import numpy as np
from .graphs import Graph, WeightedGraph, MultiplexGraph
class TemporalGraph(Graph):
    """Parent class of all temporal graphs. This class provides  an interface to all other classes 
    which implement temporal graph networks.
    
    
    
    """
    def __init__(self,directed):
        """Initializes Temporal Graph object.

        
        Arguments:
            factory {type} -- Which factory to use as argument to the defaultdict initialization.
            directed {bool} -- True if the layers are directed graphs
        
        Returns:
        """
        super(TemporalGraph, self).__init__(directed)
        self.start_timestamp = np.finfo(float).max
        self.end_timestamp = -1
    
   
    @abc.abstractmethod
    def get_snapshot_graph(self, start_time, end_time):
        raise NotImplementedError("Not implemented yet")
    @abc.abstractmethod
    def get_evolution_snapshot_graph(self, timestamp):
        raise NotImplementedError("Not implemented yet")
    
class TemporalUnweightedGraph(TemporalGraph):
    def __init__(self, directed):
        super(TemporalUnweightedGraph, self).__init__(directed)
    def _get_factory(self):
        return defaultdict(set)
   
    def add_edge(self, edge):
        """Adds edge to this graph
        
        Arguments:
            edge {tuple} -- Edge to be added
        """
        source, target, time = edge
        if time < self.start_timestamp:
            self.start_timestamp = time
        if time > self.end_timestamp:
            self.end_timestamp = time
        self[source][target].add(time)
        if not self.directed:
            self[target][source].add(time)
        self.add_nodes([source, target])

    
    
    def delete_edge(self, edge):
        """Removes a given edge from this graph.
        Arguments:
            edge {tuple} -- Tuple representing the edge to be removed
        """
        # TODO: Change start and end timestamp
        source, target, time = edge
        self[source][target].remove(time)
       
        if not self.directed:
            self[target][source].remove(time)

  
    def get_edges(self, data=True, sum_weights=False):
        """Returns edges of this graph      
        Arguments:
            data {bool} -- If true includes edge weights
        Returns:
            list -- List of edges in this graph
        """
        output = []
        for n1 in self:
            for n2 in self[n1]:
                output.append((n1, n2, self[n1][n2]))
        return output
   
    
    def contains_edge(self, edge):
        """Check if a given edge exists in this graph
        
        Arguments:
            edge {tuple} -- An edge.
        
        Returns:
            bool -- True if this graph contains the given edge else false
        """
        source, target, time = edge
        if self.directed:
            if source in self and target in self[source] and time in self[source][target]:
                return True
            else:
                return False
        else:
            if source in self and target in self[source] and time in self[source][target]:
                return True
            elif target in self and source in self[target] and time in self[target][source]:
                return True
            else:
                return False
   
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
            return super(TemporalUnweightedGraph, self).copy(deep)
        output = TemporalUnweightedGraph(self.directed)
        output.add_edges(self.get_edges())
        return output
    def get_snapshot_graph(self, start_time, end_time):
        assert start_time < end_time, "Start time should be less than end time"
        output = WeightedGraph(self.directed, weight_is_list=False)
        for source in self:
            for target in self[source]:
                for time in self[source][target]:
                    if time >= start_time and time <= end_time:
                        output.add_edge((source, target, 1.0))
        return output
    def get_evolution_snapshot_graph(self, timestamp):
        output = WeightedGraph(self.directed, weight_is_list=False)
        for source in self:
            for target in self[source]:
                for time in self[source][target]:
                    if time <= timestamp:
                        output.add_edge((source, target, 1.0))
        return output
    def get_column_names(self):
        return ("source", "target", "timestamp")
    def get_edgelist(self, data=True, sum_weights=False):
        edges = self.get_edges()
        output = []
        for edge in edges:
            for time in edge[2]:
                output.append((edge[0], edge[1], time))
        return output
    def to_visjs_format(self):
        nodes = list(self.get_nodes())
        edges = []
        for source in self:
            for target in self[source]:
                for timestamp in self[source][target]:
                    edges.append({"from":source, "to":target, "timestamp":timestamp})
        return {"nodes": nodes, "edges": edges}
    def get_graph_type(self):
        return "temporal-unweighted"

class TemporalWeightedGraph(TemporalUnweightedGraph):
    def __init__(self, directed, weight_is_list):
        self.weight_is_list = weight_is_list
        super(TemporalWeightedGraph, self).__init__(directed)
    def _get_factory(self):
        if self.weight_is_list:
            return defaultdict(lambda: defaultdict(list))
        else:
            return defaultdict(lambda: defaultdict(float))
    
   
    def add_edge(self, edge):
        """Adds edge to this graph
        
        Arguments:
            edge {tuple} -- Edge to be added
        """
        source, target, time, weight = edge
        if time < self.start_timestamp:
            self.start_timestamp = time
        if time > self.end_timestamp:
            self.end_timestamp = time
        if type(weight) == dict:
            weight = weight["weight"]
        else:
            weight = weight
        if self.weight_is_list:
            self[source][target][time].append(weight)
        else:
            self[source][target][time] += weight
            
        if not self.directed:
            if self.weight_is_list:
                self[target][source][time].append(weight)
            else:
                self[target][source][time] += weight
        self.add_nodes([source, target])

    
    
    def delete_edge(self, edge):
        """Removes a given edge from this graph.
        Arguments:
            edge {tuple} -- Tuple representing the edge to be removed
        """
        source, target, time = edge
        self[source][target].pop(time)
       
        if not self.directed:
            self[target][source].pop(time)

  
    def get_edges(self, data=True, sum_weights=False):
        """Returns edges of this graph      
        Arguments:
            data {bool} -- If true includes edge weights
        Returns:
            list -- List of edges in this graph
        """
        output = []
        for source in self:
            for target in self[source]:
                for time in self[source][target]:
                    if self.weight_is_list:
                        if sum_weights:
                            output.append((source, target, time, np.sum(self[source][target][time])))
                        else:
                            output.append((source, target, time, np.mean(self[source][target][time])))
                    else:
                        output.append((source, target, time, self[source][target][time]))


                        
        return output
   
    
    def contains_edge(self, edge):
        """Check if a given edge exists in this graph
        
        Arguments:
            edge {tuple} -- An edge.
        
        Returns:
            bool -- True if this graph contains the given edge else false
        """
        source, target, time = edge
        if self.directed:
            if source in self and target in self[source] and time in self[source][target]:
                return True
            else:
                return False
        else:
            if source in self and target in self[source] and time in self[source][target]:
                return True
            elif target in self and source in self[target] and time in self[target][source]:
                return True
            else:
                return False
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
            return super(TemporalWeightedGraph, self).copy(deep)
        output = TemporalWeightedGraph(self.directed, self.weight_is_list)
        output.add_edges(self.get_edges())
        return output
    def get_snapshot_graph(self, start_time, end_time):
        assert start_time < end_time, "Start time should be less than end time"
        output = WeightedGraph(self.directed, weight_is_list=False)
        for source in self:
            for target in self[source]:
                for time in self[source][target]:
                    if time >= start_time and time <= end_time:
                        if self.weight_is_list:
                            weights = self[source][target][time]
                            if len(weights) > 0:
                                output.add_edge((source, target, np.mean(weights)))
                        else:
                            output.add_edge((source, target, self[source][target][time]))
        return output
    def get_evolution_snapshot_graph(self, timestamp):
        
        output = WeightedGraph(self.directed, weight_is_list=False)
        for source in self:
            for target in self[source]:
                for time in self[source][target]:
                    if time <= timestamp:
                        if self.weight_is_list:
                            weights = self[source][target][time]
                            if len(weights) > 0:
                                output.add_edge((source, target, np.mean(weights)))
                        else:
                            output.add_edge((source, target, self[source][target][time]))
        return output
    def get_column_names(self):
        return ("source", "target", "timestamp", "weight")
    def get_edgelist(self, data=True, sum_weights=False):
        return self.get_edges(data=data, sum_weights=sum_weights)
    def to_visjs_format(self):
        nodes = list(self.get_nodes())
        edges = []
        for source in self:
            for target in self[source]:
                for timestamp in self[source][target]:
                    edges.append({"from": source, "to": target, "timestamp": timestamp, "weight": self[source][target][timestamp]})
        return {"nodes":nodes, "edges":edges}
    def get_graph_type(self):
        return "temporal-weighted"
class TemporalMultiplexGraph(TemporalWeightedGraph):
    def __init__(self, directed, weight_is_list):
        self.weight_is_list = weight_is_list
        super(TemporalMultiplexGraph, self).__init__(directed, weight_is_list=weight_is_list)
    def _get_factory(self):
        if self.weight_is_list:
            return defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        else:
            return defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    
   
    def add_edge(self, edge):
        """Adds edge to this graph
        
        Arguments:
            edge {tuple} -- Edge to be added
        """
        source, target, relation, time, weight = edge
        if time < self.start_timestamp:
            self.start_timestamp = time
        if time > self.end_timestamp:
            self.end_timestamp = time
        if type(weight) == dict:
            weight = weight["weight"]
        else:
            weight = weight
        if self.weight_is_list:
            self[source][target][relation][time].append(weight)
        else:
            self[source][target][relation][time] += weight
            
        if not self.directed:
            if self.weight_is_list:
                self[target][source][relation][time].append(weight)
            else:
                self[target][source][relation][time] += weight
        self.add_nodes([source, target])

    
    
    def delete_edge(self, edge):
        """Removes a given edge from this graph.
        Arguments:
            edge {tuple} -- Tuple representing the edge to be removed
        """
        source, target, relation, time = edge
        self[source][target][relation].pop(time)
       
        if not self.directed:
            self[target][source][relation].pop(time)

  
    def get_edges(self, data=True, sum_weights=False):
        """Returns edges of this graph      
        Arguments:
            data {bool} -- If true includes edge weights
        Returns:
            list -- List of edges in this graph
        """
        output = []
        for source in self:
            for target in self[source]:
                for relation in self[source][target]:
                    for time in self[source][target][relation]:
                        if self.weight_is_list:
                            if sum_weights:
                                output.append((source, target, relation, time, np.sum(self[source][target][relation][time])))
                            else:
                                output.append((source, target, relation, time, np.mean(self[source][target][relation][time])))
                        else:
                            output.append((source, target, relation, time, self[source][target][relation][time]))

        return output
   
    
    def contains_edge(self, edge):
        """Check if a given edge exists in this graph
        
        Arguments:
            edge {tuple} -- An edge.
        
        Returns:
            bool -- True if this graph contains the given edge else false
        """
        source, target, relation, time = edge
        if self.directed:
            if source in self and target in self[source] and relation in self[source][target] and time in self[source][target][relation]:
                return True
            else:
                return False
        else:
            if source in self and target in self[source] and relation in self[source][target] and time in self[source][target][relation]:
                return True
            elif target in self and source in self[target] and relation in self[target][source] and  time in self[target][source][relation]:
                return True
            else:
                return False
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
            return super(TemporalMultiplexGraph, self).copy(deep)
        output = TemporalMultiplexGraph(self.directed, self.weight_is_list)
        output.add_edges(self.get_edges())
        return output
    def get_snapshot_graph(self, start_time, end_time):
        assert start_time < end_time, "Start time should be less than end time"
        output = MultiplexGraph(self.directed, weight_is_list=False)
        for source in self:
            for target in self[source]:
                for relation in self[source][target]:
                    for time in self[source][target][relation]:
                        if time >= start_time and time <= end_time:
                            if self.weight_is_list:
                                weights = self[source][target][relation][time]
                                if len(weights) > 0:
                                    output.add_edge((source, target, relation, np.mean(weights)))
                            else:
                                weights = self[source][target][relation][time]
                                output.add_edge((source, target, relation, weights))
                                
        return output
    def get_evolution_snapshot_graph(self, timestamp):
        output = MultiplexGraph(self.directed, weight_is_list=False)
        for source in self:
            for target in self[source]:
                for relation in self[source][target]:
                    for time in self[source][target][relation]:
                        if time <= timestamp:
                            if self.weight_is_list:
                                weights = self[source][target][relation][time]
                                if len(weights) > 0:
                                    output.add_edge((source, target, relation, np.mean(weights)))
                            else:
                                weights = self[source][target][relation][time]
                                output.add_edge((source, target, relation, weights))
                                
        return output
        
    def get_column_names(self):
        return ("source", "target", "relation", "timestamp", "weight")
    def get_edgelist(self, data=True, sum_weights=False):
        return self.get_edges(data=data, sum_weights=sum_weights)
    def to_visjs_format(self):
        nodes = list(self.get_nodes())
        edges = []
        for source in self:
            for target in self[source]:
                for relation in self[source][target]:
                    for timestamp in self[source][target][relation]:
                        edges.append({"from":source, "to":target, "relation":relation, "timestamp":timestamp, "weight":self[source][target][relation][timestamp]})
        return {"nodes": nodes, "edges": edges}
    def get_graph_type(self):
        return "temporal-multiplex"