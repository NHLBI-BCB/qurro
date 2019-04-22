requirejs.config({
    // https://github.com/vega/vega-embed/issues/8
    paths: {
        vega: "vendor/vega.min",
        "vega-lite": "vendor/vega-lite.min",
        "vega-embed": "vendor/vega-embed.min"
    },
    shim: {
        "vega-lite": { deps: ["vega"] },
        "vega-embed": { deps: ["vega-lite"] }
    }
});
requirejs(
    ["js/display", "js/feature_computation", "vega", "vega-lite", "vega-embed"],
    function(display, feature_computation, vega, vegaLite, vegaEmbed) {
        // DON'T CHANGE THESE LINES unless you know what you're doing -- the
        // "var rankPlotJSON = {};" and "var samplePlotJSON = {};" lines are
        // expected to contain that text by rankratioviz' python code, which
        // replaces the empty {}s with actual Vega-Lite specifications
        // generated by Altair.
        var rankPlotJSON = {};
        var samplePlotJSON = {};
        rrv = new display.RRVDisplay(rankPlotJSON, samplePlotJSON);
    }
);
