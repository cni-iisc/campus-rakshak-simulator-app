function getRandomInt (min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}


function makeTraceTriplets(time, mean, pos_std, neg_std, label, plotColor=null, intervention=null){

    if (intervention == null){
        legend = label;
    }
    else{
        legend = intervention;
    }
    // console.log("in make trace triplets");
    // console.log(typeof(plotColor));
    // console.log(plotColor[0]);
    var r = getRandomInt(0, 251);
    var g = getRandomInt(0, 251);
    var b = getRandomInt(0, 251);
    if(plotColor != null){
        r = plotColor[0];
        g = plotColor[1];
        b = plotColor[2];
    }
    var pos_std_curve = {
        x: time,
        y: pos_std,
        opacity: 0,
        showlegend: false,
        line: { color:  "rgba("+ r +","+ g +"," + b +",0.2)",  },
        mode: "lines",
        type: "scatter"
    };

   var neg_std_curve = {
        x: time,
        y: neg_std,
        fill: 'tonexty',
        opacity: 0,
        showlegend: false,
        line: { color:  "rgba("+ r +","+ g +"," + b +",0.2)", },
        mode: "lines",
        type: "scatter"
    };

    var mean_curve = {
        type: 'line',
        x: time,
        y: mean,
        
        name: "" + legend,
        showlegend: true,
        line: {
            color: "rgb("+ r +","+ g +"," + b +")",
            width: 3
        }
    };

    return [pos_std_curve,  neg_std_curve, mean_curve]
}




function makePlot(data, title, label, idx){
    var layout = {
        title: title,
        plot_bgcolor: "rgb(229,229,229)",
        xaxis: {
            title: "Days",
            gridcolor: "rgb(255,255,255)",
            showgrid: true,
            showline: false,
            showticklabels: true,
            tickcolor: "rgb(127,127,127)",
            ticks: "outside",
            zeroline: false
        },
        yaxis: {
            title: "Num. " + label,
            gridcolor: "rgb(255,255,255)",
            showgrid: true,
            showline: false,
            showticklabels: true,
            tickcolor: "rgb(127,127,127)",
            ticks: "outside",
            zeroline: false
        }
    };
    var config = { responsive: true }
    var currDiv = document.createElement("div")
    currDiv.className = "col"
    currDiv.id="plot"+idx
    Plotly.newPlot(currDiv,data,layout,config)
    return currDiv
}










 
