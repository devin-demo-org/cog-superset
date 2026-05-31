# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import pytest

from superset.exceptions import InvalidPostProcessingError
from superset.utils.core import PostProcessingBoxplotWhiskerType
from superset.utils.pandas_postprocessing import boxplot
from tests.unit_tests.fixtures.dataframes import names_df


def test_boxplot_tukey():
    df = boxplot(
        df=names_df,
        groupby=["region"],
        whisker_type=PostProcessingBoxplotWhiskerType.TUKEY,
        metrics=["cars"],
    )
    columns = {column for column in df.columns}  # noqa: C416
    assert columns == {
        "cars__mean",
        "cars__median",
        "cars__q1",
        "cars__q3",
        "cars__max",
        "cars__min",
        "cars__count",
        "cars__outliers",
        "cars__whisker_method",
        "cars__whisker_description",
        "cars__lower_bound",
        "cars__upper_bound",
        "region",
    }
    assert len(df) == 4


def test_boxplot_min_max():
    df = boxplot(
        df=names_df,
        groupby=["region"],
        whisker_type=PostProcessingBoxplotWhiskerType.MINMAX,
        metrics=["cars"],
    )
    columns = {column for column in df.columns}  # noqa: C416
    assert columns == {
        "cars__mean",
        "cars__median",
        "cars__q1",
        "cars__q3",
        "cars__max",
        "cars__min",
        "cars__count",
        "cars__outliers",
        "cars__whisker_method",
        "cars__whisker_description",
        "cars__lower_bound",
        "cars__upper_bound",
        "region",
    }
    assert len(df) == 4


def test_boxplot_percentile():
    df = boxplot(
        df=names_df,
        groupby=["region"],
        whisker_type=PostProcessingBoxplotWhiskerType.PERCENTILE,
        metrics=["cars"],
        percentiles=[1, 99],
    )
    columns = {column for column in df.columns}  # noqa: C416
    assert columns == {
        "cars__mean",
        "cars__median",
        "cars__q1",
        "cars__q3",
        "cars__max",
        "cars__min",
        "cars__count",
        "cars__outliers",
        "cars__whisker_method",
        "cars__whisker_description",
        "cars__lower_bound",
        "cars__upper_bound",
        "region",
    }
    assert len(df) == 4


def test_boxplot_percentile_incorrect_params():
    with pytest.raises(InvalidPostProcessingError):
        boxplot(
            df=names_df,
            groupby=["region"],
            whisker_type=PostProcessingBoxplotWhiskerType.PERCENTILE,
            metrics=["cars"],
        )

    with pytest.raises(InvalidPostProcessingError):
        boxplot(
            df=names_df,
            groupby=["region"],
            whisker_type=PostProcessingBoxplotWhiskerType.PERCENTILE,
            metrics=["cars"],
            percentiles=[10],
        )

    with pytest.raises(InvalidPostProcessingError):
        boxplot(
            df=names_df,
            groupby=["region"],
            whisker_type=PostProcessingBoxplotWhiskerType.PERCENTILE,
            metrics=["cars"],
            percentiles=[90, 10],
        )

    with pytest.raises(InvalidPostProcessingError):
        boxplot(
            df=names_df,
            groupby=["region"],
            whisker_type=PostProcessingBoxplotWhiskerType.PERCENTILE,
            metrics=["cars"],
            percentiles=[10, 90, 10],
        )


def test_boxplot_tukey_transparency_metadata():
    df = boxplot(
        df=names_df,
        groupby=["region"],
        whisker_type=PostProcessingBoxplotWhiskerType.TUKEY,
        metrics=["cars"],
    )
    assert "cars__whisker_method" in df.columns
    assert "cars__whisker_description" in df.columns
    assert "cars__lower_bound" in df.columns
    assert "cars__upper_bound" in df.columns

    assert (df["cars__whisker_method"] == "Tukey IQR").all()
    assert (
        df["cars__whisker_description"].iloc[0].startswith("Outliers are points beyond")
    )

    for _, row in df.iterrows():
        q1 = row["cars__q1"]
        q3 = row["cars__q3"]
        iqr = q3 - q1
        assert row["cars__lower_bound"] == pytest.approx(q1 - 1.5 * iqr)
        assert row["cars__upper_bound"] == pytest.approx(q3 + 1.5 * iqr)


def test_boxplot_percentile_transparency_metadata():
    df = boxplot(
        df=names_df,
        groupby=["region"],
        whisker_type=PostProcessingBoxplotWhiskerType.PERCENTILE,
        metrics=["cars"],
        percentiles=[2, 98],
    )
    assert "cars__whisker_method" in df.columns
    assert (df["cars__whisker_method"] == "Percentile").all()
    assert "cars__lower_bound" in df.columns
    assert "cars__upper_bound" in df.columns


def test_boxplot_minmax_transparency_metadata():
    df = boxplot(
        df=names_df,
        groupby=["region"],
        whisker_type=PostProcessingBoxplotWhiskerType.MINMAX,
        metrics=["cars"],
    )
    assert "cars__whisker_method" in df.columns
    assert (df["cars__whisker_method"] == "Min/Max").all()
    assert "cars__whisker_description" in df.columns
    assert "No outlier detection" in df["cars__whisker_description"].iloc[0]


def test_boxplot_type_coercion():
    df = names_df
    df["cars"] = df["cars"].astype(str)
    df = boxplot(
        df=df,
        groupby=["region"],
        whisker_type=PostProcessingBoxplotWhiskerType.TUKEY,
        metrics=["cars"],
    )

    columns = {column for column in df.columns}  # noqa: C416
    assert columns == {
        "cars__mean",
        "cars__median",
        "cars__q1",
        "cars__q3",
        "cars__max",
        "cars__min",
        "cars__count",
        "cars__outliers",
        "cars__whisker_method",
        "cars__whisker_description",
        "cars__lower_bound",
        "cars__upper_bound",
        "region",
    }
    assert len(df) == 4
