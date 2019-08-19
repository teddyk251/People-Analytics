import "react-vis/dist/style.css";
import React from "react";
import { XYPlot, XAxis, YAxis, HorizontalGridLines, VerticalGridLines, LineMarkSeries, DiscreteColorLegend } from 'react-vis';
class Graph2dVis extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            data: props.data,
            bc_selected:true,
            cc_selected: true,
            evc_selected:true,
            node_label:""
        }
        this.onLineSeriesClick = props.onLineSeriesClick;
        this.toggleBC = this.toggleBC.bind(this);
        this.toggleCC = this.toggleCC.bind(this);
        this.toggleEVC = this.toggleEVC.bind(this);


    }

    toggleBC(event){
            this.setState({bc_selected:!this.state.bc_selected});
        }
    toggleCC(event){
            this.setState({cc_selected:!this.state.cc_selected});
        }
    toggleEVC(event){
            this.setState({evc_selected:!this.state.evc_selected});
        }
    onSeriesMouseOver = node_label => {
       this.setState({node_label:node_label});
    }
    
    onSeriesMouseOut = empty => {
        this.setState({node_label:empty});
    }
    
    
    render() {
        
        const legendItems = [
            {
                title: 'Betweenness centrality',
                color: 'blue',
                strokeWidth: 6,
            },
            {
                title: 'Closeness centrality',
                color: 'red',
                strokeWidth: 6,
            },
            {
                title: 'Eigen Vector centrality',
                color: 'yellow',
                strokeWidth: 6,
            },
        ]
           
        let bc_data_item = [];
        let cc_data_item = [];
        let evc_data_item = [];
        if(this.props.selected_node.length>0){
            for(let i=0; i< this.props.selected_node.length; i++){
                bc_data_item[i] = this.props.data.bc[this.props.selected_node[i]];
                cc_data_item[i] = this.props.data.cc[this.props.selected_node[i]];
                evc_data_item[i] = this.props.data.evc[this.props.selected_node[i]];
            }
           
        }
        else{
            bc_data_item = []
            cc_data_item = []
            evc_data_item = []
        }
        
        

        return (
        
            <div>
                {/* {
                    this.props.selected_node != null
                        ? <h6>Centrality scores of: <ul>{this.items}</ul></h6>
                        : <h6> Centrality scores </h6>
                    
                } */}
                <div>
                    <label>Node Label:{this.state.node_label}</label><br/>
                </div>
                <div id="instanceCheckboxes" style={{ display: 'inline-flex', flexDirection: 'row'  }}>
                    <input type={"checkbox"} onChange={this.toggleBC} style={{ width: "23px", height: "23px", marginTop: 5 }}  checked={this.state.bc_selected}/><span style={{marginRight:10}}> B.C </span> 
                    <input type={"checkbox"} onChange={this.toggleCC} style={{ width: "23px", height: "23px", marginTop: 5 }} checked={this.state.cc_selected}/><span style={{marginRight:10}}> C.C </span> 
                    <input type={"checkbox"} onChange={this.toggleEVC} style={{ width: "23px", height: "23px", marginTop: 5 }} checked={this.state.evc_selected}/><span style={{marginRight:10}}> Ev.C </span> 
                    
                </div>
                < XYPlot height={600} width={800} className="Graph2DVisualizer">
                    <DiscreteColorLegend items={legendItems} />
                    
                    <VerticalGridLines />
                    <HorizontalGridLines />
                    <XAxis />
                    <YAxis />
                    
                    {
                        this.props.selected_node.map((item,index) => {
                            return (
                                
                                this.state.bc_selected&&<LineMarkSeries key={index} label={"Betweenness centrality"} onSeriesMouseOver={this.onSeriesMouseOver.bind(this, (this.props.network.nodes.get(item).label ))} 
                                onSeriesMouseOut={this.onSeriesMouseOut.bind(this, (""))} color={"blue"} curve={"curveMonotoneX"} onValueClick={this.onLineSeriesClick} data={bc_data_item.length>0?bc_data_item[index].map((data, i) => { return ({ x: i, y: data }) }):[] }/> 
                            )
                        })
                    }
                    {
                        this.props.selected_node.map((item,index) => {
                            return (
                                this.state.cc_selected&&<LineMarkSeries label={"Closeness centrality"} onSeriesMouseOver={this.onSeriesMouseOver.bind(this, (this.props.network.nodes.get(item).label ))} 
                                onSeriesMouseOut={this.onSeriesMouseOut.bind(this, (""))} color={"red"} curve={"curveMonotonex"} onValueClick={this.onLineSeriesClick} data={cc_data_item.length>0? cc_data_item[index].map((data,i) => { return ({x: i, y: data}) } ):[]}/>
                            )
                        })
                    }
                    {
                        this.props.selected_node.map((item,index) => {
                        return(
                            this.state.evc_selected&&<LineMarkSeries label={'Eigen Vector centrality'} onSeriesMouseOver={this.onSeriesMouseOver.bind(this, (this.props.network.nodes.get(item).label ))} 
                            onSeriesMouseOut={this.onSeriesMouseOut.bind(this, (""))} color={"yellow"} curve={"curveMonotonex"} onValueClick={this.onLineSeriesClick} data={evc_data_item.length>0? evc_data_item[index].map((data,i) => {return ({x: i, y: data})}):[]}/>
                        )
                    })}

                    
                    
                    
                    
                    
                </XYPlot >
            </div>
            )
    }
    
}

export default Graph2dVis;