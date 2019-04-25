define(["display", "mocha", "chai"], function(display, mocha, chai) {
    // Just the output from the python "matching" integration test
    // prettier-ignore
    var rankPlotJSON = {"config": {"view": {"width": 400, "height": 300}, "axis": {"gridColor": "#f2f2f2"}}, "data": {"name": "data-9a1dd79e18e69cf28db67fccfed0f389"}, "mark": "bar", "encoding": {"color": {"type": "nominal", "field": "Classification", "scale": {"domain": ["None", "Numerator", "Denominator", "Both"], "range": ["#e0e0e0", "#f00", "#00f", "#949"]}}, "size": {"value": 1.0}, "tooltip": [{"type": "quantitative", "field": "x"}, {"type": "nominal", "field": "Classification"}, {"type": "nominal", "field": "Feature ID"}], "x": {"type": "quantitative", "field": "x", "title": "Features"}, "y": {"type": "quantitative", "field": "Intercept"}}, "selection": {"selector007": {"type": "interval", "bind": "scales", "encodings": ["x", "y"]}}, "title": "Feature Ranks", "$schema": "https://vega.github.io/schema/vega-lite/v2.6.0.json", "datasets": {"data-9a1dd79e18e69cf28db67fccfed0f389": [{"Feature ID": "Taxon2", "x": 0, "Classification": "None", "Intercept": 1.0, "Rank 1": 2.0, "Rank 2": 3.0}, {"Feature ID": "Taxon3|Yeet|100", "x": 1, "Classification": "None", "Intercept": 4.0, "Rank 1": 5.0, "Rank 2": 6.0}, {"Feature ID": "Taxon1", "x": 2, "Classification": "None", "Intercept": 5.0, "Rank 1": 6.0, "Rank 2": 7.0}, {"Feature ID": "Taxon5", "x": 3, "Classification": "None", "Intercept": 6.0, "Rank 1": 5.0, "Rank 2": 4.0}, {"Feature ID": "Taxon4", "x": 4, "Classification": "None", "Intercept": 9.0, "Rank 1": 8.0, "Rank 2": 7.0}], "rankratioviz_rank_ordering": ["Intercept", "Rank 1", "Rank 2"]}};
    // prettier-ignore
    var samplePlotJSON = {"config": {"view": {"width": 400, "height": 300}}, "data": {"name": "data-20592a268a0aeac806b0cd7f1eb32da9"}, "mark": "circle", "encoding": {"color": {"type": "nominal", "field": "Metadata1"}, "tooltip": [{"type": "nominal", "field": "Sample ID"}], "x": {"type": "quantitative", "field": "Metadata1"}, "y": {"type": "quantitative", "field": "rankratioviz_balance", "title": "log(Numerator / Denominator)"}}, "title": "Log Ratio of Abundances in Samples", "$schema": "https://vega.github.io/schema/vega-lite/v2.6.0.json", "datasets": {"data-20592a268a0aeac806b0cd7f1eb32da9": [{"Sample ID": "Sample2", "rankratioviz_balance": null, "Metadata1": 4, "Metadata2": 5, "Metadata3": 6}, {"Sample ID": "Sample6", "rankratioviz_balance": null, "Metadata1": 16, "Metadata2": 17, "Metadata3": 18}, {"Sample ID": "Sample5", "rankratioviz_balance": null, "Metadata1": 13, "Metadata2": 14, "Metadata3": 15}, {"Sample ID": "Sample7", "rankratioviz_balance": null, "Metadata1": 19, "Metadata2": 20, "Metadata3": 21}, {"Sample ID": "Sample3", "rankratioviz_balance": null, "Metadata1": 7, "Metadata2": 8, "Metadata3": 9}, {"Sample ID": "Sample1", "rankratioviz_balance": null, "Metadata1": 1, "Metadata2": 2, "Metadata3": 3}], "rankratioviz_feature_col_ids": {"Taxon3|Yeet|100": "0", "Taxon4": "1", "Taxon5": "2", "Taxon1": "3", "Taxon2": "4"}, "rankratioviz_feature_counts": {"0": {"Sample2": 3.0, "Sample6": 3.0, "Sample5": 4.0, "Sample7": 2.0, "Sample3": 4.0, "Sample1": 2.0}, "1": {"Sample2": 1.0, "Sample6": 1.0, "Sample5": 1.0, "Sample7": 1.0, "Sample3": 1.0, "Sample1": 1.0}, "2": {"Sample2": 0.0, "Sample6": 0.0, "Sample5": 2.0, "Sample7": 0.0, "Sample3": 1.0, "Sample1": 0.0}, "3": {"Sample2": 1.0, "Sample6": 5.0, "Sample5": 4.0, "Sample7": 6.0, "Sample3": 2.0, "Sample1": 0.0}, "4": {"Sample2": 5.0, "Sample6": 1.0, "Sample5": 2.0, "Sample7": 0.0, "Sample3": 4.0, "Sample1": 6.0}}}};

    /* Convenience method. Since the feature column IDs aren't necessarily
     * going to be assigned the same way if you run rankratioviz multiple
     * times, this lets us ensure that we're using the same features in these
     * tests even if we update samplePlotJSON.
     */
    function featureColID(featureID) {
        return samplePlotJSON.datasets.rankratioviz_feature_col_ids[featureID];
    }
    describe("Dynamic RRVDisplay class functionality", function() {
        var rrv = new display.RRVDisplay(rankPlotJSON, samplePlotJSON);
        after(function() {
            rrv.destroy();
        });

        it("Initializes an RRVDisplay object", function() {
            // This test doesn't check much. Unit tests of the RRVDisplay
            // methods are needed to validate things more carefully.
            chai.assert.strictEqual(rrv.rankPlotJSON, rankPlotJSON);
            chai.assert.strictEqual(rrv.samplePlotJSON, samplePlotJSON);
            // RRVDisplay.onHigh indicates that the next "single"-selected
            // feature from the rank plot will be the numerator of a log
            // ratio
            chai.assert.isTrue(rrv.onHigh);
            chai.assert.exists(rrv.rankPlotView);
            chai.assert.exists(rrv.samplePlotView);
            // Check that DOM bindings were properly set
            chai.assert.isNotEmpty(rrv.elementsWithOnClickBindings);
            for (var i = 0; i < rrv.elementsWithOnClickBindings.length; i++) {
                chai.assert.isFunction(
                    document.getElementById(rrv.elementsWithOnClickBindings[i])
                        .onclick
                );
            }
        });

        it("Identifies nonexistent sample IDs", function() {
            chai.assert.doesNotThrow(function() {
                rrv.validateSampleID("Sample2");
            });
            chai.assert.throws(function() {
                rrv.validateSampleID("SuperFakeSampleName");
            });
        });

        describe("Computing sample log ratios", function() {
            describe("Single-feature selections", function() {
                it("Computes the correct sample log ratio", function() {
                    // Recall that .featureHighCol and .featureLowCol correspond to the
                    // feature column IDs (as an example, in this case:
                    // "0" -> "Taxon3|Yeet|100" and "1" -> "Taxon4").
                    rrv.featureHighCol = featureColID("Taxon3|Yeet|100");
                    rrv.featureLowCol = featureColID("Taxon4");
                    chai.assert.equal(
                        Math.log(3),
                        rrv.updateBalanceSingle({ "Sample ID": "Sample6" })
                    );
                    // Test that flipping the counts within the log ratio works
                    rrv.featureHighCol = featureColID("Taxon4");
                    rrv.featureLowCol = featureColID("Taxon3|Yeet|100");
                    chai.assert.equal(
                        -Math.log(3),
                        rrv.updateBalanceSingle({ "Sample ID": "Sample6" })
                    );
                    // Try the same stuff out with different features and sample
                    rrv.featureHighCol = featureColID("Taxon1");
                    rrv.featureLowCol = featureColID("Taxon2");
                    chai.assert.equal(
                        Math.log(2),
                        rrv.updateBalanceSingle({ "Sample ID": "Sample5" })
                    );
                    rrv.featureHighCol = featureColID("Taxon2");
                    rrv.featureLowCol = featureColID("Taxon1");
                    chai.assert.equal(
                        -Math.log(2),
                        rrv.updateBalanceSingle({ "Sample ID": "Sample5" })
                    );
                });
                it("Returns NaN when numerator and/or denominator is 0", function() {
                    // In this first case, only the numerator is a 0.
                    rrv.featureHighCol = featureColID("Taxon1");
                    rrv.featureLowCol = featureColID("Taxon2");
                    chai.assert.isNaN(
                        rrv.updateBalanceSingle({ "Sample ID": "Sample1" })
                    );
                    // In this next case, both the numerator and denominator are 0.
                    rrv.featureHighCol = featureColID("Taxon1");
                    rrv.featureLowCol = featureColID("Taxon1");
                    chai.assert.isNaN(
                        rrv.updateBalanceSingle({ "Sample ID": "Sample1" })
                    );
                });

                it("Throws an error if sample ID isn't present in data", function() {
                    chai.assert.throws(function() {
                        rrv.updateBalanceSingle({
                            "Sample ID": "lolthisisntreal"
                        });
                    });
                });
            });
            describe("Multi-feature selections", function() {
                it("Computes the correct sample log ratio", function() {
                    // Standard 2-taxon / 2-taxon case
                    rrv.topFeatures = ["Taxon1", "Taxon3|Yeet|100"];
                    rrv.botFeatures = ["Taxon2", "Taxon4"];
                    chai.assert.equal(
                        Math.log(2 / 7),
                        rrv.updateBalanceMulti({ "Sample ID": "Sample1" })
                    );
                    // only one feature over another (therefore should be equal to
                    // updateBalanceSingle -- this is the same test as done above)
                    rrv.topFeatures = ["Taxon3|Yeet|100"];
                    rrv.botFeatures = ["Taxon4"];
                    chai.assert.equal(
                        Math.log(2),
                        rrv.updateBalanceMulti({ "Sample ID": "Sample1" })
                    );
                });
                it("Returns NaN when numerator and/or denominator feature lists are empty", function() {
                    // Test what happens when numerator and/or denominator feature
                    // lists are empty. If either or both of these feature lists are
                    // empty, we should get a NaN balance (since that corresponds to
                    // the numerator and/or denominator of the log ratio being 0).
                    // 1. Both numerator and denominator are empty
                    rrv.topFeatures = [];
                    rrv.botFeatures = [];
                    chai.assert.isNaN(
                        rrv.updateBalanceMulti({ "Sample ID": "Sample1" })
                    );
                    // 2. Just numerator is empty
                    rrv.botFeatures = ["Taxon4"];
                    chai.assert.isNaN(
                        rrv.updateBalanceMulti({ "Sample ID": "Sample1" })
                    );
                    // 3. Just denominator is empty
                    rrv.topFeatures = ["Taxon2"];
                    rrv.botFeatures = [];
                    chai.assert.isNaN(
                        rrv.updateBalanceMulti({ "Sample ID": "Sample1" })
                    );
                });
                it("Throws an error if sample ID isn't present in data", function() {
                    // Same as in the updateBalanceSingle test -- verify that
                    // a nonexistent sample ID causes an error
                    chai.assert.throws(function() {
                        rrv.updateBalanceMulti({
                            "Sample ID": "lolthisisntreal"
                        });
                    });
                });
            });
            describe("Summing feature abundances in a sample", function() {
                it("Correctly sums feature abundances in a sample", function() {
                    // Check case when number of features is just one
                    chai.assert.equal(
                        6,
                        rrv.sumAbundancesForSampleFeatures(
                            { "Sample ID": "Sample1" },
                            ["Taxon2"]
                        )
                    );
                    // Check with multiple features
                    chai.assert.equal(
                        7,
                        rrv.sumAbundancesForSampleFeatures(
                            { "Sample ID": "Sample1" },
                            ["Taxon2", "Taxon4"]
                        )
                    );
                    chai.assert.equal(
                        7,
                        rrv.sumAbundancesForSampleFeatures(
                            { "Sample ID": "Sample1" },
                            ["Taxon2", "Taxon4", "Taxon1"]
                        )
                    );
                    // Check with another sample + an annotated feature
                    chai.assert.equal(
                        8,
                        rrv.sumAbundancesForSampleFeatures(
                            { "Sample ID": "Sample2" },
                            ["Taxon2", "Taxon3|Yeet|100"]
                        )
                    );
                });
                it("Returns 0 when the input list of features is empty", function() {
                    chai.assert.equal(
                        0,
                        rrv.sumAbundancesForSampleFeatures(
                            { "Sample ID": "Sample3" },
                            []
                        )
                    );
                });
                it("Throws an error if sample ID isn't present in data", function() {
                    // Check that an invalid sample ID causes an error
                    chai.assert.throws(function() {
                        rrv.sumAbundancesForSampleFeatures(
                            { "Sample ID": "lolthisisntreal" },
                            []
                        );
                    });
                });
            });
        });

        describe('Updating "feature text" DOM elements', function() {
            it("Works for single-feature selections", function() {
                rrv.newFeatureHigh = "New feature name high";
                rrv.newFeatureLow = "New feature name low";
                rrv.updateFeaturesTextDisplays(true);
                chai.assert.equal(
                    document.getElementById("topFeaturesDisplay").value,
                    rrv.newFeatureHigh
                );
                chai.assert.equal(
                    document.getElementById("botFeaturesDisplay").value,
                    rrv.newFeatureLow
                );
                // Check it again -- ensure that the updating action overwrites the
                // previous values
                rrv.newFeatureHigh = "Thing 1!";
                rrv.newFeatureLow = "Thing 2!";
                rrv.updateFeaturesTextDisplays(true);
                chai.assert.equal(
                    document.getElementById("topFeaturesDisplay").value,
                    rrv.newFeatureHigh
                );
                chai.assert.equal(
                    document.getElementById("botFeaturesDisplay").value,
                    rrv.newFeatureLow
                );
            });
            it("Works for multi-feature selections", function() {
                // Standard case
                rrv.topFeatures = ["abc", "def", "ghi", "lmno pqrs", "tuv"];
                rrv.botFeatures = ["asdf", "ghjk"];
                var expectedTopText = "abc\ndef\nghi\nlmno pqrs\ntuv";
                var expectedBotText = "asdf\nghjk";
                rrv.updateFeaturesTextDisplays();
                chai.assert.equal(
                    document.getElementById("topFeaturesDisplay").value,
                    expectedTopText
                );
                chai.assert.equal(
                    document.getElementById("botFeaturesDisplay").value,
                    expectedBotText
                );
                // Check case where there's only one feature in a list
                // In this case, the denominator + expected bottom text are the
                // same as before
                rrv.topFeatures = ["onlyfeature"];
                expectedTopText = "onlyfeature";
                rrv.updateFeaturesTextDisplays();
                chai.assert.equal(
                    document.getElementById("topFeaturesDisplay").value,
                    expectedTopText
                );
                chai.assert.equal(
                    document.getElementById("botFeaturesDisplay").value,
                    expectedBotText
                );
                // Check case where lists are empty
                rrv.topFeatures = [];
                rrv.botFeatures = [];
                rrv.updateFeaturesTextDisplays();
                chai.assert.isEmpty(
                    document.getElementById("topFeaturesDisplay").value
                );
                chai.assert.isEmpty(
                    document.getElementById("botFeaturesDisplay").value
                );
            });
            it('Clears the "feature text" DOM elements properly', function() {
                // Populate the DOM elements
                rrv.newFeatureHigh = "Thing 1!";
                rrv.newFeatureLow = "Thing 2!";
                rrv.updateFeaturesTextDisplays(true);
                // Check that clearing works
                rrv.updateFeaturesTextDisplays(false, true);
                chai.assert.isEmpty(
                    document.getElementById("topFeaturesDisplay").value
                );
                chai.assert.isEmpty(
                    document.getElementById("botFeaturesDisplay").value
                );
                // Repopulate the DOM elements
                rrv.newFeatureHigh = "Thing 1!";
                rrv.newFeatureLow = "Thing 2!";
                rrv.updateFeaturesTextDisplays(true);
                // Check that clearing is done, even if "single" is true (the "clear" argument takes priority)
                rrv.updateFeaturesTextDisplays(true, true);
                chai.assert.isEmpty(
                    document.getElementById("topFeaturesDisplay").value
                );
                chai.assert.isEmpty(
                    document.getElementById("botFeaturesDisplay").value
                );
            });
        });
        describe("Updating feature rank colors", function() {
            it("Works for single-feature selections", function() {
                rrv.newFeatureHigh = "FH";
                rrv.newFeatureLow = "FL";
                chai.assert.equal(
                    "Numerator",
                    rrv.updateRankColorSingle({ "Feature ID": "FH" })
                );
                chai.assert.equal(
                    "Denominator",
                    rrv.updateRankColorSingle({ "Feature ID": "FL" })
                );
                chai.assert.equal(
                    "None",
                    rrv.updateRankColorSingle({ "Feature ID": "FN" })
                );
                // Test "both" case
                rrv.newFeatureLow = "FH";
                chai.assert.equal(
                    "Both",
                    rrv.updateRankColorSingle({ "Feature ID": "FH" })
                );
            });

            it("Works for multi-feature selections", function() {
                rrv.topFeatures = ["Feature1", "Feature2", "Feature3"];
                rrv.botFeatures = ["Feature3", "Feature4"];
                chai.assert.equal(
                    "Numerator",
                    rrv.updateRankColorMulti({ "Feature ID": "Feature1" })
                );
                chai.assert.equal(
                    "Denominator",
                    rrv.updateRankColorMulti({ "Feature ID": "Feature4" })
                );
                chai.assert.equal(
                    "None",
                    rrv.updateRankColorMulti({ "Feature ID": "FeatureN" })
                );
                chai.assert.equal(
                    "Both",
                    rrv.updateRankColorMulti({ "Feature ID": "Feature3" })
                );
            });
        });
        describe("Selecting features to update the plots", function() {
            describe("Single-feature selections", function() {
                // TODO refactor display callback code to make it more easily
                // testable (won't have to rely on clicks)
            });
            describe("Multi-feature selections", function() {
                // Should be able to just call .click() on multiFeatureButton
                // (after populating search fields/types, of course)
            });
        });
        describe("Modifying plot signals", function() {
            // can use view.signal() to do this. Very feasible.
            describe("Changing the rank used on the rank plot", function() {});
            describe("Changing the x-axis used on the sample plot", function() {});
        });
    });
});