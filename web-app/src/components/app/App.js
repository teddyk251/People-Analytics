import React from 'react';
import './App.css';
import GraphVisualizer from "../graph/GraphVisualizer";
import Graph2dVis from "../graph/Graph2dVis";
import AuxiliaryGraph from "../graph/AuxiliaryGraph";
import NodeInfoCard from "../node/NodeInfoCard";

import connectedGraph from '../../resources/graphs/static/connected.json';
import {DataSet} from "vis";

import nodeScores from '../../resources/temporal_node_score_sequences/connected-2.json';

import graphs_ranges from "../../resources/graph_ranges/connected.json";




class App extends React.Component {
    constructor(props) {
        super(props);
       

        this.network = {nodes:new DataSet(connectedGraph.nodes), edges:new DataSet(connectedGraph.edges)};
        this.nodeScores = nodeScores;
        this.state = {
            show_2d_diagram: true,
            dataset2d: {"bc":[], "cc":[], "evc":[] },
            graph_2_nodes: new DataSet(),
            graph_2_edges: new DataSet(),
            selected_node:null
        }
        this.auxiliary_graph_ref = React.createRef();
        
    }
    render = () => {
        

        return (
    

            <div className="App">
                <header className="App-header">
       
                    <GraphVisualizer nodes={this.network.nodes} edges={this.network.edges} showNodeScoreDiagram={this.showNodeScoreDiagram} graph_name={"Connected"} />
                    {/* <NodeInfoCard isShowing={false} /> */}
                   
                    
                    <div style={{display:"flex",width:"100%",height:"60%"}}>
                        <Graph2dVis data={this.state.dataset2d} isShowing={this.state.show_2d_diagram} onLineSeriesClick={this.onLineSeriesClick} selected_node={this.state.selected_node}/>
                        <AuxiliaryGraph ref={this.auxiliary_graph_ref} nodes={this.state.graph_2_nodes} edges={this.state.graph_2_edges} showNodeScoreDiagram={this.showNodeScoreDiagram} />
                    </div>

                    
                    
                    
                </header>
            </div>
        );
    }
    onLineSeriesClick = (event) => {
        const graph_index = Math.floor( event.x );
        const promise = this.load_snapshot_graph(graph_index);
        promise.then(json => {
            
            this.auxiliary_graph_ref.current.update_network(json.default.nodes, json.default.edges, this.state.selected_node.id,graphs_ranges[graph_index]);
        })
    
    }

    async load_snapshot_graph(index) {
        return await import("../../resources/graphs/evolution-snapshots/jsons/connected/snapshot-"+index+".json")        
        
    }
    
    showNodeScoreDiagram = (selected_node) => {
        if (selected_node.length > 0) {
            selected_node = selected_node[0];
            const node_bc_data = this.nodeScores["betweenness_centrality"][selected_node];
            const node_cc_data = this.nodeScores["closeness_centrality"][selected_node];
            const node_evc_data = this.nodeScores["eigenvector_centrality"][selected_node];
           
            
            const current_node_data = this.network.nodes.get(selected_node);
            current_node_data.color = {
                highlight: '#848484',
                hover: '#d3d2cd',
                inherit: false,
                opacity: 1.0
            }
            this.network.nodes.update(current_node_data);
            this.setState({ show_2d_diagram: true, dataset2d: {"bc":node_bc_data, "cc":node_cc_data, "evc":node_evc_data}, selected_node: current_node_data })
            
            
        } else {
            this.setState({ show_2d_diagram: false, dataset2d: { "bc": [], "cc": [], "evc": [] } });
     
        }
        
    }
}

export default App;
