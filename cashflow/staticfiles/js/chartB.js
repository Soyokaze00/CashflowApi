window.onload = function () {
    var chart = new CanvasJS.Chart("chartContainer", {
        exportEnabled: true,
        animationEnabled: true,
        title:{
            text: ""
        },
        axisY: {
            // title: "Oil Filter - Units",
            titleFontColor: "#4F81BC",
            lineColor: "#4F81BC",
            labelFontColor: "#4F81BC",
            tickColor: "#4F81BC",
            includeZero: true
        },
        axisY2: {
            // title: "Clutch - Units",
            titleFontColor: "#C0504E",
            lineColor: "#FcA311",
            labelFontColor: "#C0504E",
            tickColor: "#C0504E",
            includeZero: true
        },
        toolTip: {
            bordeRadius:"20px",
            shared: true
        },
        legend: {
            cursor: "pointer",
            // width:"30px",
            itemclick: toggleDataSeries
        },
        data: [{
            type: "column",
            name: "مصرف",

            showInLegend: true,      
            color:"#FcA311", 
            yValueFormatString: "#,##0.# Units",
            dataPoints: [
                { label: "مهر", y: 25342 },
                { label: "آبان",  y: 20088 },
                { label: "آدر",  y: 28234 }
            ],  
          
            
        },

        {
            type: "column",
            name: "درآمد",
            axisYType: "secondary",
            color:"#284B63",
            showInLegend: true,
            yValueFormatString: "#,##0.# Units",
            dataPoints: [
                { label: "مهر", y: 425 },
                { label: "آبان", y: 130 },
                { label: "آدر", y: 528 }
            ],
           

        }],
        width: 700,  // عرض نمودار (می‌توانید مقدار آن را تغییر دهید)
        height: 400  // طول نمودار (می‌توانید مقدار آن را تغییر دهید)
    });
    chart.render();

    function toggleDataSeries(e) {
        if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
            e.dataSeries.visible = false;
        } else {
            e.dataSeries.visible = true;
        }
        e.chart.render();
    }
}
