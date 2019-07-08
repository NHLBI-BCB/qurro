#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Copyright (c) 2018--, Qurro development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
#
# Generates two JSON files: one for a rank plot and one for a sample
# scatterplot of log ratios.
#
# A lot of the code for processing input data in Qurro was based on code by
# Jamie Morton, some of which is now located in ipynb/Figure3.ipynb in
# https://github.com/knightlab-analyses/reference-frames.
# ----------------------------------------------------------------------------

import os
import logging

from distutils.dir_util import copy_tree
import pandas as pd
import altair as alt
from qurro._rank_utils import filter_unextreme_features
from qurro._json_utils import replace_js_json_definitions
from qurro._df_utils import (
    replace_nan,
    validate_df,
    biom_table_to_sparse_df,
    remove_empty_samples_and_features,
    match_table_and_data,
    merge_feature_metadata,
    sparsify_count_dict,
)


def process_and_generate(
    feature_ranks,
    sample_metadata,
    biom_table,
    output_dir,
    feature_metadata=None,
    extreme_feature_count=None,
):
    """Just calls process_input() and gen_visualization()."""
    U, V, ranking_ids, feature_metadata_cols, processed_table = process_input(
        feature_ranks,
        sample_metadata,
        biom_table,
        feature_metadata,
        extreme_feature_count,
    )
    return gen_visualization(
        V, ranking_ids, feature_metadata_cols, processed_table, U, output_dir
    )


def process_input(
    feature_ranks,
    sample_metadata,
    biom_table,
    feature_metadata=None,
    extreme_feature_count=None,
):
    """Validates/processes the input files and parameter(s) to Qurro.

       In particular, this function

       1. Calls validate_df() on all of the input DataFrames passed
          (feature ranks, sample metadata, feature metadata if passed).

       2. Calls replace_nan() on the metadata DataFrame(s), so that all
          missing values are represented consistently with a None (which
          will be represented as a null in JSON/JavaScript).

       3. Converts the BIOM table to a SparseDataFrame by calling
          biom_table_to_sparse_df().

       4. Matches up the table with the feature ranks and sample metadata by
          calling match_table_and_data().

       5. Calls filter_unextreme_features() using the provided
          extreme_feature_count. (If it's None, then nothing will be done.)

       6. Calls remove_empty_samples_and_features() to filter empty samples
          (and features). This is purposefully done *after*
          filter_unextreme_features() is called.

       7. Calls merge_feature_metadata() on the feature ranks and feature
          metadata. (If feature metadata is None, nothing will be done.)

       Returns
       -------
       output_metadata: pd.DataFrame
            Sample metadata, but matched with the table and with empty samples
            removed.

       output_ranks: pd.DataFrame
            Feature ranks, post-filtering and with feature metadata columns
            added in.

       ranking_ids
            The ranking columns' names in output_ranks.

       feature_metadata_cols: list
            The feature metadata columns' names in output_ranks.

       output_table: pd.SparseDataFrame
            The BIOM table, post matching with the feature ranks and sample
            metadata and with empty samples removed.
    """

    logging.debug("Starting processing input.")

    validate_df(feature_ranks, "feature ranks", 2, 1)
    validate_df(sample_metadata, "sample metadata", 1, 1)
    if feature_metadata is not None:
        # It's cool if there aren't any features actually described in the
        # feature metadata (hence why we pass in 0 as the minimum # of rows in
        # the feature metadata DataFrame), but we still pass it to
        # validate_df() in order to ensure that:
        #   1) there's at least one feature metadata column (because
        #      otherwise the feature metadata is useless)
        #   2) column names are unique
        validate_df(feature_metadata, "feature metadata", 0, 1)

    # Replace NaN values (which both _metadata_utils.read_metadata_file() and
    # qiime2.Metadata use to represent missing values, i.e. ""s) with None --
    # this is generally easier for us to handle in the JS side of things (since
    # it'll just be consistently converted to null by json.dumps()).
    sample_metadata = replace_nan(sample_metadata)
    if feature_metadata is not None:
        feature_metadata = replace_nan(feature_metadata)

    table = biom_table_to_sparse_df(biom_table)

    # Match up the table with the feature ranks and sample metadata.
    m_table, m_sample_metadata = match_table_and_data(
        table, feature_ranks, sample_metadata
    )

    # Note that although we always call filter_unextreme_features(), filtering
    # isn't necessarily always done (whether or not depends on the value of
    # extreme_feature_count and the contents of the table/ranks).
    filtered_table, filtered_ranks = filter_unextreme_features(
        m_table, feature_ranks, extreme_feature_count
    )

    # Filter now-empty samples (and empty features) from the BIOM table.
    output_table, output_metadata, u_ranks = remove_empty_samples_and_features(
        filtered_table, m_sample_metadata, filtered_ranks
    )

    # Save a list of ranking IDs (before we add in feature metadata)
    # TODO: just have merge_feature_metadata() give us this?
    ranking_ids = u_ranks.columns

    output_ranks, feature_metadata_cols = merge_feature_metadata(
        u_ranks, feature_metadata
    )

    logging.debug("Finished input processing.")
    return (
        output_metadata,
        output_ranks,
        ranking_ids,
        feature_metadata_cols,
        output_table,
    )


def gen_rank_plot(V, ranking_ids, feature_metadata_cols):
    """Generates altair.Chart object describing the rank plot.

    Arguments:

    V: pd.DataFrame
        feature ranks

    ranking_ids: pd.Index
        IDs of the actual "ranking" columns in V (since V can include
        feature metadata)

    feature_metadata_cols: pd.Index or list
        IDs of the feature metadata columns in V (if no such IDs present, an
        empty list should be passed)

    Returns:

    JSON describing a Vega-Lite specification for the rank plot.
    """

    rank_data = V.copy()

    # NOTE that until this point we've treated the actual rank values as just
    # "objects", as far as pandas is concerned. However, if we continue to
    # treat them as objects when sorting them, we'll get a list of feature
    # ranks in lexicographic order... which is not what we want. So we just
    # ensure that all of the columns contain numeric data.
    for col in ranking_ids:
        rank_data[col] = pd.to_numeric(rank_data[col])

    # The default rank column is just whatever the first rank is. This is what
    # the rank plot will use when it's first drawn.
    default_rank_col = ranking_ids[0]

    # Set default classification of every feature to "None"
    # (This value will be updated when a feature is selected in the rank plot
    # as part of the numerator, denominator, or both parts of the current log
    # ratio.)
    if "qurro_classification" in rank_data.columns:
        raise ValueError(
            "Feature rankings/metadata can't contain any columns called "
            "qurro_classification. Try changing the name of this column."
        )
    rank_data["qurro_classification"] = "None"

    # Replace "index" with "Feature ID". looks nicer in the visualization :)
    rank_data.rename_axis("Feature ID", axis="index", inplace=True)
    rank_data.reset_index(inplace=True)

    # Now, we can actually create the rank plot.
    rank_chart = (
        alt.Chart(
            rank_data,
            title="Feature Ranks",
            background="#FFFFFF",
            autosize=alt.AutoSizeParams(resize=True),
        )
        .mark_bar()
        .transform_window(
            sort=[alt.SortField(field=default_rank_col, order="ascending")],
            # We don't use an alt.WindowFieldDef here because python gets
            # confused when you use "as" as an actual argument name. So we just
            # use this syntax.
            window=[{"op": "row_number", "as": "qurro_x"}],
        )
        .encode(
            # type="ordinal" needed on the scale here to make bars adjacent;
            # see https://stackoverflow.com/a/55544817/10730311.
            x=alt.X(
                "qurro_x",
                title="Sorted Features",
                type="ordinal",
                scale=alt.Scale(paddingOuter=1, paddingInner=0, rangeStep=1),
                axis=alt.Axis(ticks=False, labelAngle=0),
            ),
            y=alt.Y(default_rank_col, type="quantitative"),
            color=alt.Color(
                "qurro_classification",
                scale=alt.Scale(
                    domain=["None", "Numerator", "Denominator", "Both"],
                    range=["#e0e0e0", "#f00", "#00f", "#949"],
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    field="qurro_x",
                    title="Current Ranking",
                    type="quantitative",
                ),
                alt.Tooltip(
                    field="qurro_classification",
                    title="Log Ratio Classification",
                    type="nominal",
                ),
                "Feature ID",
                *feature_metadata_cols,
            ],
        )
        .configure_axis(
            # Done in order to differentiate "None"-classification features
            # from grid lines
            gridColor="#f2f2f2",
            labelBound=True,
        )
        .interactive()
    )

    rank_chart_json = rank_chart.to_dict()
    rank_ordering = "qurro_rank_ordering"
    fm_col_ordering = "qurro_feature_metadata_ordering"
    # Note we don't use rank_data.columns for setting the rank ordering. This
    # is because rank_data's columns now include both the ranking IDs and the
    # "Feature ID" and "qurro_classification" columns (as well as any feature
    # metadata the user saw fit to pass in).
    rank_chart_json["datasets"][rank_ordering] = list(ranking_ids)
    rank_chart_json["datasets"][fm_col_ordering] = list(feature_metadata_cols)
    return rank_chart_json


def gen_sample_plot(table, metadata):
    """Generates altair.Chart object describing the sample scatterplot.

    Arguments:

    table: (Sparse)DataFrame representation of the processed BIOM table.
    metadata: DataFrame describing metadata for each sample.

    Returns:

    JSON describing altair.Chart for the sample plot.
    """

    sample_metadata = metadata.copy()

    # Used to set color
    default_metadata_col = sample_metadata.columns[0]

    # Since we don't bother setting a default log ratio, we set the balance for
    # every sample to None so that Vega* will filter them out (producing an
    # empty scatterplot by default, which makes sense).
    if "qurro_balance" in sample_metadata.columns:
        raise ValueError(
            "Sample metadata can't contain any columns called qurro_balance."
            "Try changing the name of this column."
        )
    sample_metadata["qurro_balance"] = None

    # "Reset the index" -- make the sample IDs a column (on the leftmost side)
    # First we rename the index "Sample ID", just on the off chance that
    # there's a metadata column called "index".
    # NOTE that there shouldn't be a metadata column called Sample ID or
    # something like that, since that should've been used in the merge with
    # df_balance above (and "Sample ID" follows the Q2 metadata conventions for
    # an "Identifier Column" name).
    sample_metadata.rename_axis("Sample ID", axis="index", inplace=True)
    sample_metadata.reset_index(inplace=True)

    # Very minor thing -- sort the samples by their IDs. This should ensure
    # that the sample plot output is deterministic.
    # NOTE: this is probably unnecessary due to the use of sort_keys in
    # _json_utils.try_to_replace_line_json(). Double-check if we can remove
    # this.
    sample_metadata.sort_values(by=["Sample ID"], inplace=True)

    # Create sample plot chart Vega-Lite spec using Altair.
    sample_chart = (
        alt.Chart(
            sample_metadata,
            title="Log Ratio of Abundances in Samples",
            background="#FFFFFF",
            autosize=alt.AutoSizeParams(resize=True),
        )
        .mark_circle()
        .encode(
            alt.X(
                default_metadata_col,
                type="nominal",
                axis=alt.Axis(labelAngle=-45),
            ),
            alt.Y(
                "qurro_balance:Q",
                title="log(Numerator / Denominator)",
                type="quantitative",
            ),
            color=alt.Color(default_metadata_col, type="nominal"),
            tooltip=["Sample ID:N", "qurro_balance:Q"],
        )
        .configure_range(
            ramp=alt.SchemeConfig(scheme="blues"),
            category=alt.SchemeConfig(scheme="tableau10"),
        )
        .configure_axis(labelBound=True)
        .interactive()
    )

    # Replace the "mark": "circle" definition with a more explicit one. This
    # will be useful when adding attributes to the boxplot mark in the
    # visualization. (We have to resort to this hack because I haven't been
    # able to successfully use alt.MarkDef in the alt.Chart definition above.)
    sample_chart_dict = sample_chart.to_dict()
    sample_chart_dict["mark"] = {"type": "circle"}
    # Sparsify the table's count data in order to cut down on the size of
    # main.js and make the Qurro visualization load faster.
    count_dict = table.T.to_dict()
    sparse_count_dict = sparsify_count_dict(count_dict)
    # Return the JSONs as dicts for 1) the sample plot JSON (which only
    # contains sample metadata), and 2) the sparsified sample counts per
    # feature (which will be stored separately from the sample plot JSON in
    # the hopes of not hitting performance too terribly).
    return sample_chart_dict, sparse_count_dict


def gen_visualization(
    V,
    ranking_ids,
    feature_metadata_cols,
    processed_table,
    df_sample_metadata,
    output_dir,
):
    """Creates a Qurro visualization.

       Returns
       -------

       index_path: str
            A path to the index.html file for the output visualization. This is
            needed when calling q2templates.render().
    """

    # https://altair-viz.github.io/user_guide/faq.html#disabling-maxrows
    alt.data_transformers.enable("default", max_rows=None)

    logging.debug("Generating rank plot JSON.")
    rank_plot_json = gen_rank_plot(V, ranking_ids, feature_metadata_cols)
    logging.debug("Generating sample plot (and count data) JSONs.")
    sample_plot_json, count_json = gen_sample_plot(
        processed_table, df_sample_metadata
    )
    logging.debug("Finished generating all JSONs.")

    # Copy support_files/ for the Qurro visualization to the output directory
    # First, identify the location of this particular file (generate.py).
    curr_loc = os.path.dirname(os.path.realpath(__file__))
    # Next, join curr_loc with support_files/, since support_files/ is located
    # within the same directory as this fiile (generate.py).
    support_files_loc = os.path.join(curr_loc, "support_files")
    # Finally, actually do the copying (saving the index path for future use)
    # We explictly ignore files starting with a period, like .DS_STORE. It's ok
    # if these files make their way into the output directory -- they shouldn't
    # mess anything up -- but there's no need to include them.

    # copy_tree() creates the output directory if it doesn't already exist.
    # (When Qurro is running as a QIIME 2 plugin, output_dir already exists and
    # we need to write stuff to it -- this is because output_dir is actually a
    # temporary folder that QIIME 2 creates.)
    # NOTE: Use of copy_tree() instead of shutil.copytree() (which throws an
    # error if output_dir already exists) is based on how
    # emperor.core.copy_support_files() works.
    copy_tree(support_files_loc, output_dir)
    index_path = os.path.join(output_dir, "index.html")

    # Write the plot and count JSONs to main.js so that they're loaded when
    # this Qurro visualization starts up
    exit_code = replace_js_json_definitions(
        os.path.join(output_dir, "main.js"),
        rank_plot_json,
        sample_plot_json,
        count_json,
    )
    if exit_code != 0:
        raise ValueError("Wasn't able to replace JSONs and write to main.js.")

    logging.debug("Finished writing the visualization contents.")

    return index_path
