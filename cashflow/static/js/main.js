const { AgCharts } = agCharts;

const data = [
  { type: "test1", count: 6000 },
  { type: "test2", count: 5656 },
  { type: "test3", count: 8899 },
  { type: "test4", count: 15349 },
];

const numFormatter = new Intl.NumberFormat("en-US");
const total = data.reduce((sum, d) => sum + d["count"], 0);

const options = {
  container: document.getElementById("myChart"),
  data,
  title: {
    text: "هزینه",
    color: "white",
  },

  background: {
    color: "white",
    fill: "#353535",
  },

  series: [
    {
      type: "donut",
      calloutLabelKey: "type",
      angleKey: "count",
      sectorLabelKey: "count",
      color: "white",
      fill: "white",
      calloutLabel: {
        color: "white",
        fill: "white",

        enabled: false,
      },

      sectorLabel: {
        fontSize: 7,
        color: "black",
        fill: "white",

        formatter: ({ datum, sectorLabelKey }) => {
          const value = datum[sectorLabelKey];
          return numFormatter.format(value);
        },
      },
      title: {
        color: "white",
      },
      innerRadiusRatio: 0.68,

      innerLabels: [
        {
          text: "باقی مانده",
          fontSize: 15,
          color: "white",
        },
        {
          text: "تومان" + numFormatter.format(total),
          fontSize: 14,
          spacing: 10,
          color: "white",
        },
      ],
      tooltip: {
        renderer: ({ datum, calloutLabelKey, title, sectorLabelKey }) => {
          return {
            title,
            color: "white",
            content: `${datum[calloutLabelKey]}: ${numFormatter.format(
              datum[sectorLabelKey]
            )}`,
          };
        },
      },
      sectorSpacing: 0,

      color: "white",
      fills: ["#a7a7a7", "#fba110", "#ffed32", "#a47012"],
      strokes: ["#FFFFFF"],
    },
  ],
};
function formatNumber(value) {
  value /= 1000_000;
  return `${Math.floor(value)}M`;
}

const options2 = {
  container: document.getElementById("myChart2"),
  data: [
    { year: "2016", visitors: 46636720 },
    { year: "2017", visitors: 48772922 },
    { year: "2018", visitors: 8999999 },
    { year: "2019", visitors: 32000000 },
    { year: "2020", visitors: 47271912 },
    { year: "2021", visitors: 78000000 },
    { year: "2022", visitors: 49441678 },
    { year: "2023", visitors: 50368190 },
  ],

  series: [
    {
      type: "bar",
      xKey: "year",
      yKey: "visitors",
      label: {
        formatter: ({ value }) => formatNumber(value),
      },
      tooltip: {
        renderer: ({ datum, xKey, yKey }) => {
          return { title: datum[xKey], content: formatNumber(datum[yKey]) };
        },
      },
    },
  ],
  axes: [
    {
      type: "category",
      position: "bottom",
      title: {
        text: "Year",
      },
    },
    {
      type: "number",
      position: "left",
      title: {
        text: "Total Visitors",
      },
      label: {
        formatter: ({ value }) => formatNumber(value),
      },
    },
  ],
};

const tooltip = {
  renderer: (params) => {
    const {
      datum,
      xKey,
      xName,
      minKey,
      minName,
      q1Key,
      q1Name,
      medianKey,
      medianName,
      q3Key,
      q3Name,
      maxKey,
      maxName,
      yName,
    } = params;
    const values = [
      `${xName}: ${datum[xKey]}`,
      `${minName}: ${datum[minKey]}`,
      `${q1Name}: ${datum[q1Key]}`,
      `${medianName}: ${datum[medianKey]}`,
      `${q3Name}: ${datum[q3Key]}`,
      `${maxName}: ${datum[maxKey]}`,
    ];
    return `<div class="ag-chart-tooltip-title">${yName}</div><div class="ag-chart-tooltip-content">${values.join(
      "<br>"
    )}</div>`;
  },
};

const shared = {
  xKey: "countryOfArrival",
  xName: "Country Of Arrival",
  minKey: "min",
  minName: "Min",
  q1Key: "q1",
  q1Name: "Q1",
  medianKey: "median",
  medianName: "Median",
  q3Key: "q3",
  q3Name: "Q3",
  maxKey: "max",
  maxName: "Max",
  cornerRadius: 8,
  strokeOpacity: 0,
  whisker: {
    strokeOpacity: 1,
  },
  cap: {
    lengthRatio: 0,
  },
};

const options4 = {
  container: document.getElementById("myChart4"),
  data: [
    {
      month: "تیر",
      price: 28000,
      v: 25000,
      menDelta: 280000,
      womenDelta: 250000,
    },
    {
      month: "مرداد",
      price: 280000,
      v: 400000,
      menDelta: 280000,
      womenDelta: 400000,
    },
    {
      month: "شهریور",
      price: 320000,
      v: 30000,
      menDelta: 320000,
      womenDelta: 300000,
    },
  ],
  series: [
    {
      type: "bar",
      direction: "horizontal",
      xKey: "month",
      yKey: "menDelta",
      yName: "درامد",
      fill: "#284B63",
      // fill:"#3C6E71",
      cornerRadius: 20,
      label: {
        formatter: ({ value }) => value.toFixed(0),
      },
    },
    {
      type: "bar",
      direction: "horizontal",
      xKey: "month",
      yKey: "womenDelta",
      yName: "مصرف",
      fill: "#FcA311",
      cornerRadius: 20,
      label: {
        formatter: ({ value }) => value.toFixed(0),
      },
    },
  ],
  axes: [
    {
      type: "category",
      position: "left",
      line: {
        enabled: true,
      },
      label: {
        enabled: true,
      },
      // paddingInner: 0.2,
      // crossLines: [
      //   {
      //     type: "line",
      //     value: "تیر",
      //     strokeWidth: 0,
      //     fillOpacity: 0,
      //     label: {
      //       text: "تیر",
      //       position: "bottpm",
      //     },
      //   },
      //   {
      //     type: "range",
      //     range: ["مرداد", "مرداد"],
      //     strokeWidth: 0,
      //     fillOpacity: 0,
      //     label: {
      //       text: "مرداد",
      //       position: "insideRight",
      //     },
      //   },
      //   {
      //     type: "range",
      //     range: ["شهریور", "شهریور"],
      //     strokeWidth: 0,
      //     fillOpacity: 0,
      //     label: {
      //       text: "شهریور",
      //       position: "insideRight",
      //     },
      //   },
      //   {
      //     type: "range",
      //     range: ["تیر", "تیر"],
      //     strokeWidth: 0,
      //     fillOpacity: 0,

      //     label: {
      //       text: "→ تیر",
      //       position: "insideRight",
      //     },
      //   },

      // ],
    },
    {
      type: "number",
      position: "bottom",
      nice: false,
      min: 0,
      max: "100%",
      label: {
        enabled: false,
      },
    },
  ],
};

AgCharts.create(options4);

AgCharts.create(options2);

AgCharts.create(options);
