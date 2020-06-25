import logging

from django.core.management.base import BaseCommand
from django.db import connection, connections, transaction

from usaspending_api.etl.broker_etl_helpers import dictfetchall
from usaspending_api.references.models import GTASSF133Balances

logger = logging.getLogger("console")

DERIVED_COLUMNS = {
    "obligations_incurred_total_cpe": [2190],
    "budget_authority_appropriation_amount_cpe": [1160, 1180, 1260, 1280],
    "other_budgetary_resources_amount_cpe": [1340, 1440, 1540, 1640, 1750, 1850],
    "gross_outlay_amount_by_tas_cpe": [3020],
    "unobligated_balance_cpe": [2490],
}


class Command(BaseCommand):
    help = "Update GTAS aggregations used as domain data"

    @transaction.atomic()
    def handle(self, *args, **options):
        logger.info("Creating broker cursor")
        broker_cursor = connections["data_broker"].cursor()

        logger.info("Running TOTAL_OBLIGATION_SQL")
        broker_cursor.execute(self.broker_fetch_sql())

        logger.info("Getting total obligation values from cursor")
        total_obligation_values = dictfetchall(broker_cursor)

        logger.info("Deleting all existing GTAS total obligation records in website")
        GTASSF133Balances.objects.all().delete()

        logger.info("Inserting GTAS total obligations records into website")
        total_obligation_objs = [GTASSF133Balances(**values) for values in total_obligation_values]
        GTASSF133Balances.objects.bulk_create(total_obligation_objs)

        with connection.cursor() as cursor:
            logger.info("Populating TAS foreign keys")
            cursor.execute(self.tas_fk_sql())

        logger.info("GTAS loader finished successfully!")

    def broker_fetch_sql(self):
        return f"""
            SELECT
                fiscal_year,
                period as fiscal_period,
                {self.column_statements()}
                disaster_emergency_fund_code,
                CASE WHEN tas.main_account_code is not null THEN
                    CONCAT(
                        CASE WHEN tas.allocation_transfer_agency is not null THEN CONCAT(tas.allocation_transfer_agency, '-') ELSE null END,
                        tas.agency_identifier, '-',
                        CASE WHEN tas.beginning_period_of_availa is not null THEN CONCAT(tas.beginning_period_of_availa, '/', tas.ending_period_of_availabil) ELSE tas.availability_type_code END,
                        '-', tas.main_account_code, '-', tas.sub_account_code)
                    ELSE
                        null
                    END
                as tas_rendering_label
            FROM
                sf_133 sf
            LEFT JOIN tas_lookup tas ON sf.tas_id = tas.tas_id
            GROUP BY
                fiscal_year,
                fiscal_period,
                disaster_emergency_fund_code,
                tas_rendering_label
            ORDER BY
                fiscal_year,
                fiscal_period;
        """

    def column_statements(self):
        return "\n".join(
            [
                f"""COALESCE(SUM(CASE WHEN line IN ({','.join([str(elem) for elem in val])}) THEN sf.amount ELSE 0 END), 0.0) AS {key},"""
                for key, val in DERIVED_COLUMNS.items()
            ]
        )

    def tas_fk_sql(self):
        return """UPDATE gtas_sf133_balances
                    SET treasury_account_identifier = tas.treasury_account_identifier
                    FROM treasury_appropriation_account tas
                    WHERE tas.tas_rendering_label = gtas_sf133_balances.tas_rendering_label;"""
