window.onload = function () {
	var chart = new CanvasJS.Chart("chartContainer", {
		theme: "dark2",     
		exportFileName: "Doughnut Chart",  
		exportEnabled: true,  
		animationEnabled: true,  
		legend:{ 		
			cursor: "pointer", 
			itemclick: explodePie  
		},
    
		data: [{
			type: "doughnut",
			innerRadius: 90,
			showInLegend: true,
			toolTipContent: "<b>{name}</b>: ${y} (#percent%)",
			indexLabel: "{name} - #percent%",
			dataPoints: [
				{ y: 800, name: "Housing", color: "#a47012" },  
				{ y: 150, name: "Education", color: "#ffed32" }, 
				{ y: 150, name: "Shopping", color: "#fba110" }, 
				{ y: 250, name: "Others", color: "#a7a7a7" }   
			]
		}]  ,
    annotations: [{
			type: "text",
			text: "Total Expenses",   // متنی که می‌خواهید در وسط دایره نمایش داده شود
			fontSize: 24,
      color:"white",
			fontColor: "#FFFFFF",
			x: 50,  // مختصات x (نسبی)
			y: 50,  // مختصات y (نسبی)
			align: "center",
			verticalAlign: "center"
		}]  
	});
	chart.render();
	
	function explodePie (e) {
		if(typeof (e.dataSeries.dataPoints[e.dataPointIndex].exploded) === "undefined" || !e.dataSeries.dataPoints[e.dataPointIndex].exploded) {
			e.dataSeries.dataPoints[e.dataPointIndex].exploded = true;
		} else {
			e.dataSeries.dataPoints[e.dataPointIndex].exploded = false;
		}
		e.chart.render();
	}
}