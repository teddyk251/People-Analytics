import React from "react";
import vis from "vis"
import "./AuxiliaryGraph.css"
import Moment from 'moment';


class AuxiliaryGraph extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            nodes: props.nodes,
            edges: props.edges,
            drawn: false,
            snapshot_index: 0,
            selected_node_index: null,
            start_date: null,
            end_date:null
            
        }

    }
    add_edge(edge) {
        this.setState({ edges: this.state.edges.concat({from:edge.from, to:edge.to }) });
    }
    update_network(nodes, edges, selected_node_index, graph_range) {
        this.state.nodes.clear();
        this.state.nodes.add(nodes)
        this.state.edges.clear();
        this.state.edges.add(edges)
        this.state.start_date = new Date(graph_range.start * 1000);
        this.state.end_date = new Date(graph_range.end * 1000);
        this.setState({selected_node_index: selected_node_index });
    }
    componentDidMount() {
        
        this.setState({drawn:true})
    }

    render() {
        if (this.state.drawn) {
            const data = { nodes: this.state.nodes, edges: this.state.edges };
            
            const network = new vis.Network(this.refs.aux_container, data, {});
            if (this.state.selected_node_index != null) {

                const current_node_data = this.state.nodes.get(this.state.selected_node_index);
                if (current_node_data != null) {
                    current_node_data.color = {
                        background: '#dddd33',
                        hover: '#d3d2cd',
                        inherit: false,
                        opacity: 1.0,
                        focus: true
                    }
                    this.state.nodes.update(current_node_data);
                } else {
                    alert("Unable to find the selected!")
                }
                
            }
            network.on("stabilizationIterationsDone", function () {
                network.setOptions({ physics: false });
            });
            let $this = this;
            network.on('click', function (properties) {
                // var node_ids = properties.nodes;
                // $this.props.showNodeScoreDiagram(node_ids);

            });
        }
        
        return <div>
            {(this.state.start_date != null && this.state.end_date)
                ? <h6>{Moment(this.state.start_date).format('DD MMM YYYY')} -  {Moment(this.state.end_date).format('DD MMM YYYY')}</h6>
                :<h6>Snapshot Graph</h6>
            }
        
            <div ref="aux_container" className="AuxiliaryGraph" ></div>
        </div> 
          
        
    }
}

export default AuxiliaryGraph;