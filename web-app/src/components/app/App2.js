import "react-vis/dist/style.css"; 
import React from "react";

import { XYPlot, XAxis, YAxis, HorizontalGridLines, LineSeries, VerticalGridLines } from 'react-vis';

class App2 extends React.Component{
    
    render() {
        const data = [{ x: 0, y: 8 },
        { x: 1, y: 5 },
        { x: 2, y: 4 }]

        return (
           
                < XYPlot height = { 400} width = { 400} >
                    <VerticalGridLines />
                    <HorizontalGridLines />
                    <XAxis />
                    <YAxis />
                    <LineSeries data={data} />
                </XYPlot>
        )
    }
}
export default App2;