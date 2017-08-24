var MA_str = `function MA(C) {
    C.OUT("BR", C.IN("HIGH")(C.P) + C.PARAM("N"));
};`
var MACD_str = `function MACD(C) {
    C.IN("CLOSE").setMemo("this is close");
    C.OUT("BR", C.IN("CLOSE")(C.P) + C.PARAM("N")).setColor(123).setWidth(4);
};`

var Indicator = {};
Indicator.SourceCode = [
    {
        name: "MA",
        code: MA_str
    },
    {
        name: "MACD",
        code: MACD_str
    }
]


// var ta_funcs = [ma, macd];
Indicator.Class = [
    {
        name: "MA",
        memo: "this is macd indicator",
        params: [
            {
                "name": "N",
                "default_value": 10,
                "min_value": 1
            },
        ],
        input_serials: [
            {
                "selector": "close",
                "reassign": 0,
                "memo": "this is M",
            },
        ],
        output_serials: [
            {
                "name": "MA",
                "style": "POLYLINE",
            }
        ]
    }, {
        name: "ARBR",
        memo: "this is ARBR indicator",
        params: [
            {
                "name": "N",
                "default_value": 10,
                "min_value": 10,
                "memo": "this is N",
            },
        ],
        input_serials: [
            {
                "selector": "OPEN.cu1703",
                "reassign": 0,
                "memo": "this is M",
            },
        ],
        output_serials: [
            {
                "name": "AR",
                "style": "POLYLINE",
            },
            {
                "name": "BR",
                "style": "POLYLINE",
            }
        ],
    }, {
        name: "KDJ",
        memo: "this is KDJ indicator",
        params: [
            {
                "name": "N",
                "default_value": 10,
                "min_value": 10,
                "memo": "this is N",
            },
        ],
        input_serials: [
            {
                "selector": "OPEN.cu1703",
                "reassign": 0,
                "memo": "this is M",
            },
        ],
        output_serials: [
            {
                "name": "K",
                "style": "POLYLINE",
            },
            {
                "name": "D",
                "style": "POLYLINE",
            },
            {
                "name": "J",
                "style": "POLYLINE",
            }
        ],
    }
];

Indicator.Instances = [
    {
        instance_id: "MA5",
        indicator_class: "MA",
        instrument: "IF1709",
        duration: 3600 * 1000 * 1000 * 1000,
        params: [{
            N: 5
        }],
        output: []
    },
    {
        instance_id: "MA10",
        indicator_class: "MA",
        instrument: "IF1709",
        duration: 3600 * 1000 * 1000 * 1000,
        params: [{
            N: 10
        }],
        output: []
    },
    {
        instance_id: "MA20",
        indicator_class: "MA",
        instrument: "IF1709",
        duration: 3600 * 1000 * 1000 * 1000,
        params: [{
            N: 20
        }],
        output: []
    }
];
