import os
from datetime import datetime, timezone
from pathlib import Path
import pytest
import tempfile

from usaspending_api import settings
from usaspending_api.common.elasticsearch.client import instantiate_elasticsearch_client
from usaspending_api.common.helpers.text_helpers import generate_random_string
from usaspending_api.etl.rapidloader import Rapidloader
from model_mommy import mommy
from usaspending_api.etl.es_etl_helpers import configure_sql_strings


@pytest.fixture
def award_data_fixture(db):
    mommy.make("references.LegalEntity", legal_entity_id=1)
    mommy.make("awards.TransactionNormalized", id=1, award_id=1, action_date="2010-10-01", is_fpds=True, type="A")
    mommy.make(
        "awards.TransactionFPDS",
        transaction_id=1,
        legal_entity_zip5="abcde",
        piid="IND12PB00323",
        legal_entity_county_code="059",
        legal_entity_state_code="VA",
        legal_entity_congressional="11",
        legal_entity_country_code="USA",
        place_of_performance_state="VA",
        place_of_performance_congr="11",
        place_of_perform_country_c="USA",
        naics="331122",
        product_or_service_code="1510",
        type_set_aside="8AN",
        type_of_contract_pricing="2",
        extent_competed="F",
    )

    mommy.make("awards.TransactionNormalized", id=2, award_id=2, action_date="2016-10-01", is_fpds=False, type="02")
    mommy.make("awards.TransactionFABS", transaction_id=2, fain="P063P100612", cfda_number="84.063")

    mommy.make("references.ToptierAgency", toptier_agency_id=1, name="Department of Transportation")
    mommy.make("references.SubtierAgency", subtier_agency_id=1, name="Department of Transportation")
    mommy.make("references.Agency", id=1, toptier_agency_id=1, subtier_agency_id=1)
    mommy.make(
        "awards.Award",
        id=1,
        latest_transaction_id=1,
        recipient_id=1,
        is_fpds=True,
        type="A",
        piid="IND12PB00323",
        description="pop tarts and assorted cereals",
        total_obligation=500000.00,
        date_signed="2010-10-1",
        awarding_agency_id=1,
        funding_agency_id=1,
    )
    mommy.make(
        "awards.Award",
        id=2,
        latest_transaction_id=2,
        is_fpds=False,
        type="02",
        fain="P063P100612",
        total_obligation=1000000.00,
        date_signed="2016-10-1",
    )
    mommy.make("accounts.FederalAccount", id=1)
    mommy.make(
        "accounts.TreasuryAppropriationAccount",
        treasury_account_identifier=1,
        agency_id="097",
        main_account_code="4930",
        federal_account_id=1,
    )

    mommy.make("awards.FinancialAccountsByAwards", financial_accounts_by_awards_id=1, award_id=1, treasury_account_id=1)


config = {
    "root_index": "award-query",
    "processing_start_datetime": datetime(2019, 12, 13, 16, 10, 33, 729108, tzinfo=timezone.utc),
    "verbose": False,
    "type": "awards",
    "process_deletes": False,
    "directory": Path(settings.CSV_LOCAL_PATH),
    "skip_counts": False,
    "index_name": "test-{}-{}".format(
        datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M-%S-%f"), generate_random_string()
    ),
    "create_new_index": True,
    "snapshot": False,
    "fiscal_years": [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020],
    "starting_date": datetime(2007, 10, 1, 0, 0, tzinfo=timezone.utc),
    "max_query_size": 50000,
    "is_incremental_load": False,
}


def test_es_award_loader_class(db, award_data_fixture, elasticsearch_award_index, tmpdir):
    # os.mkdir(config["directory"] / "test")
    # config["directory"] = config["directory"] / "test"
    elasticsearch_client = instantiate_elasticsearch_client()
    loader = Rapidloader(config, elasticsearch_client)
    assert loader.__class__.__name__ == "Rapidloader"
    loader.run_load_steps()
    assert elasticsearch_client.indices.exists(config["index_name"])
    elasticsearch_client.indices.delete(index=config["index_name"], ignore_unavailable=False)
    # os.rmdir(config["directory"])


def test_es_transaction_loader_class(db, award_data_fixture, elasticsearch_transaction_index, tmpdir):
    # os.mkdir(config["directory"])
    # config["directory"] = config["directory"]
    config["root_index"] = "transaction-query"
    config["type"] = "transactions"
    elasticsearch_client = instantiate_elasticsearch_client()
    loader = Rapidloader(config, elasticsearch_client)
    assert loader.__class__.__name__ == "Rapidloader"
    loader.run_load_steps()
    assert elasticsearch_client.indices.exists(config["index_name"])
    elasticsearch_client.indices.delete(index=config["index_name"], ignore_unavailable=False)
    # os.rmdir(config["directory"])


def test_configure_sql_strings():
    config["fiscal_year"] = 2019
    config["root_index"] = "award-query"
    config["type"] = "awards"
    copy, id, count = configure_sql_strings(config, "filename", [1])
    copy_sql = """COPY (
    SELECT *
    FROM award_delta_view
    WHERE fiscal_year=2019 AND update_date >= '2007-10-01'
) TO 'filename' DELIMITER ',' CSV HEADER
"""
    count_sql = """
SELECT COUNT(*) AS count
FROM award_delta_view
WHERE fiscal_year=2019 AND update_date >= '2007-10-01'
"""
    assert copy == copy_sql
    assert count == count_sql
