import os
import sys

from datetime import datetime

import pytest

from pyspark.sql.session import SparkSession
from pyspark.sql.types import *

from deep_attribution.feature_engineering.feature_engineering import (
    create_conversion_id_field,
    create_campaign_index_in_journey_field,
    create_journey_id_field,
    get_campaign_nm_to_one_hot_index,
    get_campaigns_at_journey_level,
    get_conversion_status_at_journey_level,
    join_at_journey_level,
    pad_journey_length
)

os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

SPARK = SparkSession.builder.getOrCreate()

def test_create_conversion_id_field():

    INPUT = SPARK.createDataFrame(
        [
            (1, False, to_datetime("1970-01-01 01:03:42"), "google"),
            (1, True, to_datetime("1970-01-01 01:03:09"), "display"),
            (1, False, to_datetime("1970-01-01 01:02:25"), "facebook"),
            (2, False, to_datetime("1970-01-01 01:02:47"), "google"),
            (2, False, to_datetime("1970-01-01 01:02:25"), "facebook"),
            (2, False, to_datetime("1970-01-01 01:01:28"), "display")
        ],
        StructType([
            StructField("uid", IntegerType(), False),
            StructField("conversion", BooleanType(), False),
            StructField("datetime", TimestampType(), False),
            StructField("campaign", StringType(), False)
        ])
    )

    EXPECTED = SPARK.createDataFrame(
        [
            (1, False, to_datetime("1970-01-01 01:03:42"), "google", 0),
            (1, True, to_datetime("1970-01-01 01:03:09"), "display", 1),
            (1, False, to_datetime("1970-01-01 01:02:25"), "facebook", 1),
            (2, False, to_datetime("1970-01-01 01:02:47"), "google", 0),
            (2, False, to_datetime("1970-01-01 01:02:25"), "facebook", 0),
            (2, False, to_datetime("1970-01-01 01:01:28"), "display", 0)
        ],
        StructType([
            StructField("uid", IntegerType(), False),
            StructField("conversion", BooleanType(), False),
            StructField("datetime", TimestampType(), False),
            StructField("campaign", StringType(), False),
            StructField("conversion_id", IntegerType(), True)
        ])
    )


    obtained = create_conversion_id_field(
        INPUT,
        SPARK
        )

    assert check_dataframes_schema_are_equal(EXPECTED, obtained)

    assert check_dataframes_data_are_equal(EXPECTED, obtained)


def test_create_journey_id_field():

    INPUT = SPARK.createDataFrame(
        [
            (1, False, to_datetime("1970-01-01 01:03:42"), "google", 0),
            (1, True, to_datetime("1970-01-01 01:03:09"), "display", 1),
            (1, False, to_datetime("1970-01-01 01:02:25"), "facebook", 1),
            (2, False, to_datetime("1970-01-01 01:02:47"), "google", 0),
            (2, False, to_datetime("1970-01-01 01:02:25"), "facebook", 0),
            (2, False, to_datetime("1970-01-01 01:01:28"), "display", 0)
        ],
        StructType([
            StructField("uid", IntegerType(), False),
            StructField("conversion", BooleanType(), False),
            StructField("datetime", TimestampType(), False),
            StructField("campaign", StringType(), False),
            StructField("conversion_id", IntegerType(), True)
        ])
    )

    EXPECTED = SPARK.createDataFrame(
        [
            (False, to_datetime("1970-01-01 01:03:42"), "google", 10),
            (True, to_datetime("1970-01-01 01:03:09"), "display", 11),
            (False, to_datetime("1970-01-01 01:02:25"), "facebook", 11),
            (False, to_datetime("1970-01-01 01:02:47"), "google", 20),
            (False, to_datetime("1970-01-01 01:02:25"), "facebook", 20),
            (False, to_datetime("1970-01-01 01:01:28"), "display", 20)
        ],
        StructType([
            StructField("conversion", BooleanType(), False),
            StructField("datetime", TimestampType(), False),
            StructField("campaign", StringType(), False),
            StructField("journey_id", IntegerType(), False)
        ])
    )

    obtained = create_journey_id_field(INPUT, SPARK)

    assert check_dataframes_schema_are_equal(EXPECTED, obtained)

    assert check_dataframes_data_are_equal(EXPECTED, obtained)


def test_create_campaign_index_in_journey_field():

    INPUT = SPARK.createDataFrame(
        [
            (False, to_datetime("1970-01-01 01:03:42"), "google", 10),
            (True, to_datetime("1970-01-01 01:03:09"), "display", 11),
            (False, to_datetime("1970-01-01 01:02:25"), "facebook", 11),
            (False, to_datetime("1970-01-01 01:02:47"), "google", 20),
            (False, to_datetime("1970-01-01 01:02:25"), "facebook", 20),
            (False, to_datetime("1970-01-01 01:01:28"), "display", 20)
        ],
        StructType([
            StructField("conversion", BooleanType(), False),
            StructField("datetime", TimestampType(), False),
            StructField("campaign", StringType(), False),
            StructField("journey_id", IntegerType(), False)
        ])
    )

    EXPECTED = SPARK.createDataFrame(
        [
            (10, False, "google", 1),
            (11, True, "display", 2),
            (11, False, "facebook", 1),
            (20, False, "google", 3),
            (20, False, "facebook", 2),
            (20, False, "display", 1)
        ],
        StructType([
            StructField("journey_id", IntegerType(), False),
            StructField("conversion", BooleanType(), False),
            StructField("campaign", StringType(), False),
            StructField("campaign_index_in_journey", IntegerType(), False)
        ])
    )

    obtained = create_campaign_index_in_journey_field(INPUT, SPARK)

    assert check_dataframes_schema_are_equal(EXPECTED, obtained)

    assert check_dataframes_data_are_equal(EXPECTED, obtained)



def test_pad_journey_length():

    INPUT = SPARK.createDataFrame(
        [
            (10, False, "google", 1),
            (11, True, "display", 2),
            (11, False, "facebook", 1),
            (20, False, "google", 3),
            (20, False, "facebook", 2),
            (20, False, "display", 1)
        ],
        StructType([
            StructField("journey_id", IntegerType(), False),
            StructField("conversion", BooleanType(), False),
            StructField("campaign", StringType(), False),
            StructField("campaign_index_in_journey", IntegerType(), False)
        ])
    )

    JOURNEY_MAX_LEN = 2


    EXPECTED = SPARK.createDataFrame(
        [
            (False, "google", 10, 1),
            (True, "display", 11, 2),
            (False, "facebook", 11, 1),
            (False, "facebook", 20, 2),
            (False, "display", 20, 1)
        ],
        StructType([
            StructField("conversion", BooleanType(), False),
            StructField("campaign", StringType(), False),
            StructField("journey_id", IntegerType(), False),
            StructField("campaign_index_in_journey", IntegerType(), False)
        ])
    )

    obtained = pad_journey_length(INPUT, SPARK, JOURNEY_MAX_LEN)

    assert check_dataframes_schema_are_equal(EXPECTED, obtained)

    assert check_dataframes_data_are_equal(EXPECTED, obtained)


def test_get_campaign_nm_to_one_hot_index():

    INPUT = SPARK.createDataFrame(
        [
            (False, "google", 10, 1),
            (True, "display", 11, 2),
            (False, "facebook", 11, 1),
            (False, "facebook", 20, 2),
            (False, "display", 20, 1)
        ],
        StructType([
            StructField("conversion", BooleanType(), False),
            StructField("campaign", StringType(), False),
            StructField("journey_id", IntegerType(), False),
            StructField("campaign_index_in_journey", IntegerType(), False)
        ])
    )

    EXPECTED = {
        "display":0,
        "facebook":1,
        "google":2
    }

    obtained = get_campaign_nm_to_one_hot_index(INPUT)

    assert EXPECTED == obtained



def test_get_conversion_status_at_journey_level():

    INPUT = SPARK.createDataFrame(
        [
            (False, "google", 10, 1),
            (True, "display", 11, 2),
            (False, "facebook", 11, 1),
            (False, "facebook", 20, 2),
            (False, "display", 20, 1)
        ],
        StructType([
            StructField("conversion", BooleanType(), False),
            StructField("campaign", StringType(), False),
            StructField("journey_id", IntegerType(), False),
            StructField("campaign_index_in_journey", IntegerType(), False)
        ])
    )

    EXPECTED = SPARK.createDataFrame(
        [
            (10, False),
            (11, True),
            (20, False)
        ],
        StructType([
            StructField("journey_id", IntegerType(), False),
            StructField("conversion_status", BooleanType(), False)
        ])
    )

    obtained = get_conversion_status_at_journey_level(INPUT, SPARK)

    assert check_dataframes_schema_are_equal(EXPECTED, obtained)

    assert check_dataframes_data_are_equal(EXPECTED, obtained)


def test_get_campaigns_at_journey_level():
 
    INPUT = SPARK.createDataFrame(
        [
            (False, "google", 10, 1),
            (True, "display", 11, 2),
            (False, "facebook", 11, 1),
            (False, "facebook", 20, 2),
            (False, "display", 20, 1)
        ],
        StructType([
            StructField("conversion", BooleanType(), False),
            StructField("campaign", StringType(), False),
            StructField("journey_id", IntegerType(), False),
            StructField("campaign_index_in_journey", IntegerType(), False)
        ])
    )

    JOURNEY_MAX_LEN = 2
    
    EXPECTED = SPARK.createDataFrame(
        [
            ( 10, "google", None),
            (11,"facebook", "display"),
            (20, "display", "facebook")
        ],
        StructType([
            StructField("journey_id", IntegerType(), False),
            StructField("campaign_nm_at_index_1_in_journey", StringType(), False),
            StructField("campaign_nm_at_index_2_in_journey", StringType(), True),
        ])
    )

    obtained = get_campaigns_at_journey_level(INPUT, SPARK, JOURNEY_MAX_LEN)

    assert check_dataframes_schema_are_equal(EXPECTED, obtained)

    assert check_dataframes_data_are_equal(EXPECTED, obtained)


def test_join_at_journey_level():

    LEFT = SPARK.createDataFrame(
        [
            (10, "google", None),
            (11,"facebook", "display"),
            (20, "display", "facebook")
        ],
        StructType([
            StructField("journey_id", IntegerType(), False),
            StructField("campaign_nm_at_index_1_in_journey", StringType(), False),
            StructField("campaign_nm_at_index_2_in_journey", StringType(), True),
        ])
    )

    RIGHT = SPARK.createDataFrame(
        [
            (10, False),
            (11, True),
            (20, False)
        ],
        StructType([
            StructField("journey_id", IntegerType(), False),
            StructField("conversion_status", BooleanType(), False)
        ])
    )

    EXPECTED = SPARK.createDataFrame(
        [
            (10, "google", None, False),
            (11, "facebook", "display", True),
            (20, "display", "facebook", False)
        ],
        StructType([
            StructField("journey_id", IntegerType(), False),
            StructField("campaign_nm_at_index_1_in_journey", StringType(), False),
            StructField("campaign_nm_at_index_2_in_journey", StringType(), True),
            StructField("conversion_status", BooleanType(), False)
        ])
    )

    obtained = join_at_journey_level(LEFT, RIGHT)

    assert check_dataframes_schema_are_equal(EXPECTED, obtained)

    assert check_dataframes_data_are_equal(EXPECTED, obtained)


def to_datetime(string):
    return datetime.strptime(string, "%Y-%m-%d %H:%M:%S")

def check_dataframes_schema_are_equal(ref, test):

    field_to_list_transfo = lambda field: (field.name, field.dataType, field.nullable)

    ref_fields = [*map(field_to_list_transfo, ref.schema.fields)]
    test_fields = [*map(field_to_list_transfo, test.schema.fields)]

    print(ref_fields, test_fields)

    return set(ref_fields) == set(test_fields)


def check_dataframes_data_are_equal(ref, test):

    ref = ref.collect()
    test = test.collect()

    return set(ref) == set(test)