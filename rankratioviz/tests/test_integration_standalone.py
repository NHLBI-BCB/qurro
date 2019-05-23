from rankratioviz.tests.testing_utilities import run_integration_test


def test_byrd():
    """Tests rankratioviz' JSON generation on the Byrd et al. 2017 dataset.

       This is really a test to make sure that rankratioviz can properly handle
       songbird output.
    """
    run_integration_test(
        "byrd",
        "byrd",
        "byrd_differentials.tsv",
        "byrd_skin_table.biom",
        "byrd_metadata.txt",
    )


def test_sleep_apnea():
    """Tests rankratioviz' JSON generation on a "sleep apnea" dataset.

       This is really a test to make sure that rankratioviz can properly handle
       DEICODE output.
    """
    run_integration_test(
        "sleep_apnea",
        "sleep_apnea",
        "ordination.txt",
        "qiita_10422_table.biom",
        "qiita_10422_metadata.tsv",
        feature_metadata_name="taxonomy.tsv",
    )


def test_red_sea():
    """Tests rankratioviz' JSON generation on a dataset from a study of the Red
       Sea.

       This is really a test to make sure that rankratioviz can properly handle
       this sort of unconventionally-named-feature data.
    """
    run_integration_test(
        "red_sea",
        "red_sea",
        "differentials.tsv",
        "redsea.biom",
        "redsea_metadata.txt",
        feature_metadata_name="feature_metadata.txt",
    )
