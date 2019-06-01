import os
from pytest import approx
from click.testing import CliRunner
from biom import load_table
from qiime2 import Artifact, Metadata
from qiime2.plugins import qurro as q2qurro
import qurro.scripts._plot as rrvp
from qurro._rank_utils import read_rank_file
from qurro._plot_utils import get_jsons


def run_integration_test(
    input_dir_name,
    output_dir_name,
    ranks_name,
    table_name,
    sample_metadata_name,
    feature_metadata_name=None,
    use_q2=False,
    q2_ranking_tool="songbird",
    expected_unsupported_samples=0,
    expected_unsupported_features=0,
    expect_all_unsupported_samples=False,
):
    """Runs qurro, and validates the output somewhat."""

    in_dir = os.path.join("qurro", "tests", "input", input_dir_name)
    rloc = os.path.join(in_dir, ranks_name)
    tloc = os.path.join(in_dir, table_name)
    sloc = os.path.join(in_dir, sample_metadata_name)
    floc = None
    if feature_metadata_name is not None:
        floc = os.path.join(in_dir, feature_metadata_name)
    out_dir = os.path.join("docs", "demos", output_dir_name)

    rrv_qzv = result = None
    if use_q2:
        if q2_ranking_tool == "songbird":
            q2_action = q2qurro.actions.supervised_rank_plot
            q2_rank_type = "FeatureData[Differential]"
        elif q2_ranking_tool == "DEICODE":
            q2_action = q2qurro.actions.unsupervised_rank_plot
            q2_rank_type = "PCoAResults % Properties(['biplot'])"
        else:
            raise ValueError(
                "Unknown q2_ranking_tool: {}".format(q2_ranking_tool)
            )
        # Import all of these files as Q2 artifacts or metadata.
        rank_qza = Artifact.import_data(q2_rank_type, rloc)
        table_qza = Artifact.import_data("FeatureTable[Frequency]", tloc)
        sample_metadata = Metadata.load(sloc)
        feature_metadata = None
        if floc is not None:
            feature_metadata = Metadata.load(floc)

        # Now that everything's imported, try running qurro
        rrv_qzv = q2_action(
            ranks=rank_qza,
            table=table_qza,
            sample_metadata=sample_metadata,
            feature_metadata=feature_metadata,
        )
        # Output the contents of the visualization to out_dir.
        rrv_qzv.visualization.export_data(out_dir)
    else:
        # Run qurro "standalone" -- i.e. outside of QIIME 2
        runner = CliRunner()
        args = [
            "--ranks",
            rloc,
            "--table",
            tloc,
            "--sample-metadata",
            sloc,
            "--output-dir",
            out_dir,
        ]
        if floc is not None:
            args += ["--feature-metadata", floc]
        result = runner.invoke(rrvp.plot, args)
        # Validate that the correct exit code and output were recorded
        validate_standalone_result(
            result,
            expected_unsupported_samples=expected_unsupported_samples,
            expect_all_unsupported_samples=expect_all_unsupported_samples,
            expected_unsupported_features=expected_unsupported_features,
        )
    # If we expected this test to fail due to invalid inputs, don't bother
    # doing any JSON validation.
    # (Input validity checking is done in generate.process_input(), before
    # any output files are created in generate.gen_visualization() -- so no
    # output should be created anyway in these cases.)
    if expect_all_unsupported_samples or expected_unsupported_features > 0:
        return None, None
    else:
        rank_json, sample_json, count_json = validate_main_js(
            out_dir, rloc, tloc, sloc
        )
        return rank_json, sample_json, count_json


def validate_standalone_result(
    result,
    expected_unsupported_samples=0,
    expect_all_unsupported_samples=False,
    expected_unsupported_features=0,
):
    """Validates the result (exit code and output) of running rrv standalone.

       Parameters
       ----------
       result: click.testing.Result
          This is returned from click's CliRunner.invoke() method.

       expected_unsupported_samples: int
          The number of samples expected to be unsupported in the BIOM table.
          Defaults to 0 (i.e. all samples are expected to be supported).

       expect_all_unsupported_samples: bool
          Whether or not to expect *all* samples to be unsupported in the BIOM
          table. Defaults to False (i.e. at least one sample is expected to be
          supported). If this is set to True, expected_unsupported_samples will
          not be used.

       expected_unsupported_featuress: int
          The number of features expected to be unsupported in the BIOM table.
          Defaults to 0 (i.e. all features are expected to be supported).
    """
    # NOTE: we expect an error with unsupported feature(s) to take precedence
    # over an error with all unsupported samples. There isn't a super complex
    # reason for this aside from that being how I structured the order of
    # checks in qurro.generate.
    if expected_unsupported_features > 0:
        # The program should fail with a nonzero exit code (indicating some
        # sort of error).
        assert result.exit_code != 0
        assert type(result.exception) == ValueError
        word = "were"
        if expected_unsupported_features == 1:
            word = "was"
        expected_message = (
            "{} {} not present in the input BIOM "
            "table.".format(expected_unsupported_features, word)
        )
        # Checking .stderr didn't seem to work for me, so to check the text of
        # the ValueError we just use its .args property (which should contain
        # the message we passed when raising it)
        assert expected_message in result.exc_info[1].args[0]
    elif expect_all_unsupported_samples:
        assert result.exit_code != 0
        assert type(result.exception) == ValueError
        expected_message = (
            "None of the samples in the sample metadata file "
            "are present in the input BIOM table."
        )
        assert expected_message == result.exc_info[1].args[0]
    else:
        # There shouldn't be any errors in the output!
        # *Maybe* a warning about unsupported samples, but we know that at
        # least one sample should be supported (so rrv can still work).
        assert result.exit_code == 0
        validate_samples_supported_output(
            result.output, expected_unsupported_samples
        )


def validate_main_js(out_dir, rloc, tloc, sloc):
    """Takes care of extracting JSONs from main.js and validating them.

       Parameters
       ----------
       out_dir: str
           The output directory (containing the various "support files" of a
           qurro visualization, including main.js).

       rloc, tloc, sloc: str
           Paths to the ranks file (either DEICODE or songbird), BIOM table,
           and sample metadata file used as input to qurro.
    """

    main_loc = os.path.join(out_dir, "main.js")
    rank_json, sample_json, count_json = get_jsons(main_loc)

    # Validate plot JSONs
    validate_rank_plot_json(rloc, rank_json)
    validate_sample_plot_json(tloc, sloc, sample_json, count_json)

    return rank_json, sample_json, count_json


def validate_samples_supported_output(output, expected_unsupported_samples):
    """Checks that the correct message has been based on BIOM sample support.

       Parameters
       ----------
       output: str
          All of the printed output from running qurro.
          This can be obtained as result.output, if result is the return value
          of click's CliRunner.invoke().

       expected_unsupported_samples: int
          The number of samples expected to be unsupported in the BIOM table.
          If 0, expects all samples to be supported.
    """
    if expected_unsupported_samples > 0:
        expected_msg = (
            "NOTE: {} sample(s) in the sample metadata file were "
            "not present in the BIOM table, and have been "
            "removed from the visualization.".format(
                expected_unsupported_samples
            )
        )
        assert expected_msg in output


def basic_vegalite_json_validation(json_obj):
    """Basic validations of Vega-Lite JSON objects go here."""

    assert json_obj["$schema"].startswith("https://vega.github.io/schema")
    assert json_obj["$schema"].endswith(".json")


def validate_rank_plot_json(input_ranks_loc, rank_json):
    """Ensure that the rank plot JSON makes sense."""

    # TODO check that feature metadata annotations were properly applied to the
    # features. Will need the feature metadata file location to be passed here
    reference_features = read_rank_file(input_ranks_loc)
    # Validate some basic properties of the plot
    # (This is all handled by Altair, so these property tests aren't
    # exhaustive; they're mainly intended to verify that a general plot
    # matching our specs is being created)
    assert rank_json["mark"] == "bar"
    assert rank_json["title"] == "Feature Ranks"
    basic_vegalite_json_validation(rank_json)
    dn = rank_json["data"]["name"]
    # Check that we have the same count of ranked features as in the
    # input ranks file (no ranked features should be dropped during the
    # generation process -- there's an assertion in the code that checks
    # for this, actually)
    assert len(rank_json["datasets"][dn]) == len(reference_features)
    # Loop over every rank included in this JSON file.
    # TODO could probably make this more efficient with vectorized operations,
    # apply(), or something.
    rank_ordering = rank_json["datasets"]["qurro_rank_ordering"]
    for feature in rank_json["datasets"][dn]:
        feature_id = feature["Feature ID"]
        # Identify corresponding "reference" feature in the original data.
        #
        # We already should have asserted in the generation code that the
        # feature IDs were unique, so we don't need to worry about
        # accidentally using the same reference feature twice here.
        #
        # Also, we use .loc[feature ID] here in order to access a row of
        # the DataFrame. Because just straight indexing the DataFrame gives
        # you the column.
        reference_feature_series = reference_features.loc[feature_id]

        # Each rank value between the JSON and reference feature should
        # match.
        # We use pytest's approx class to get past floating point
        # imprecisions. Note that we just leave this at the default for
        # approx, so if this starts failing then adjusting the tolerances
        # in approx() might be needed.
        for r in range(len(rank_ordering)):
            actual_rank_val = reference_feature_series[r]
            assert actual_rank_val == approx(feature[rank_ordering[r]])


def validate_sample_plot_json(
    biom_table_loc, metadata_loc, sample_json, count_json
):
    assert sample_json["mark"] == {"type": "circle"}
    assert sample_json["title"] == "Log Ratio of Abundances in Samples"
    basic_vegalite_json_validation(sample_json)
    dn = sample_json["data"]["name"]

    # Check that each sample's metadata in the sample plot JSON matches with
    # its actual metadata.
    sample_metadata = Metadata.load(metadata_loc).to_dataframe()
    for sample in sample_json["datasets"][dn]:

        sample_id = sample["Sample ID"]

        for metadata_col in sample_metadata.columns:
            expected_md = sample_metadata.at[sample_id, metadata_col]
            actual_md = sample[metadata_col]
            try:
                assert expected_md == actual_md
            except AssertionError:
                # quick and dirty hack to actually give useful information when
                # something goes wrong
                print("PROBLEMATIC METADATA VALUE HERE")
                print(
                    expected_md, actual_md, type(expected_md), type(actual_md)
                )
                raise

        # Not really "metadata", but just as a sanity check verify that the
        # initial qurro_balance of each sample is null (aka None in
        # python) -- this ensures that no samples will show up when the
        # visualization is initially displayed, which is the intended behavior.
        assert sample["qurro_balance"] is None

    # Check that every entry (sample x feature) matches with the BIOM table.
    # If the BIOM table has, say, > 1 million entries, this might be excessive,
    # but the test data right now is small enough that this should be fine.
    table = load_table(biom_table_loc)

    # For each (ranked) feature...
    for feature_id in count_json:
        # For each sample, ensure that the count value in the JSON matches with
        # the count value in the BIOM table.
        for sample_id in count_json[feature_id]:
            actual_count = count_json[feature_id][sample_id]
            expected_count = table.get_value_by_ids(feature_id, sample_id)
            assert actual_count == expected_count