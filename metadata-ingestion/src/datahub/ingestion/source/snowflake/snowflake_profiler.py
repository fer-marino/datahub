import logging
from typing import Callable, Dict, Iterable, List, Optional

from snowflake.sqlalchemy import snowdialect
from sqlalchemy import create_engine, inspect
from sqlalchemy.sql import sqltypes

from datahub.ingestion.api.workunit import MetadataWorkUnit
from datahub.ingestion.source.ge_data_profiler import DatahubGEProfiler
from datahub.ingestion.source.snowflake.snowflake_config import SnowflakeV2Config
from datahub.ingestion.source.snowflake.snowflake_query import SnowflakeQuery
from datahub.ingestion.source.snowflake.snowflake_report import SnowflakeV2Report
from datahub.ingestion.source.snowflake.snowflake_schema import (
    SnowflakeDatabase,
    SnowflakeTable,
)
from datahub.ingestion.source.snowflake.snowflake_utils import SnowflakeCommonMixin
from datahub.ingestion.source.sql.sql_generic import BaseTable
from datahub.ingestion.source.sql.sql_generic_profiler import GenericProfiler
from datahub.ingestion.source.state.profiling_state_handler import ProfilingHandler

snowdialect.ischema_names["GEOGRAPHY"] = sqltypes.NullType
snowdialect.ischema_names["GEOMETRY"] = sqltypes.NullType

logger = logging.getLogger(__name__)


class SnowflakeProfiler(GenericProfiler, SnowflakeCommonMixin):
    def __init__(
        self,
        config: SnowflakeV2Config,
        report: SnowflakeV2Report,
        state_handler: Optional[ProfilingHandler] = None,
    ) -> None:
        super().__init__(config, report, self.platform, state_handler)
        self.config: SnowflakeV2Config = config
        self.report: SnowflakeV2Report = report
        self.logger = logger

    def get_workunits(
        self, database: SnowflakeDatabase, db_tables: Dict[str, List[SnowflakeTable]]
    ) -> Iterable[MetadataWorkUnit]:
        # Extra default SQLAlchemy option for better connection pooling and threading.
        # https://docs.sqlalchemy.org/en/14/core/pooling.html#sqlalchemy.pool.QueuePool.params.max_overflow
        if self.config.is_profiling_enabled():
            self.config.options.setdefault(
                "max_overflow", self.config.profiling.max_workers
            )

        profile_requests = []
        for schema in database.schemas:
            for table in db_tables[schema.name]:
                if (
                    not self.config.profiling.profile_external_tables
                    and table.type == "EXTERNAL TABLE"
                ):
                    logger.info(
                        f"Skipping profiling of external table {database.name}.{schema.name}.{table.name}"
                    )
                    self.report.profiling_skipped_other[schema.name] += 1
                    continue

                profile_request = self.get_profile_request(
                    table, schema.name, database.name
                )
                if profile_request is not None:
                    self.report.report_entity_profiled(profile_request.pretty_name)
                    profile_requests.append(profile_request)

        if len(profile_requests) == 0:
            return

        yield from self.generate_profile_workunits(
            profile_requests,
            max_workers=self.config.profiling.max_workers,
            db_name=database.name,
            platform=self.platform,
            profiler_args=self.get_profile_args(),
        )

    def get_dataset_name(self, table_name: str, schema_name: str, db_name: str) -> str:
        return self.get_dataset_identifier(table_name, schema_name, db_name)

    def get_batch_kwargs(
        self, table: BaseTable, schema_name: str, db_name: str
    ) -> dict:
        custom_sql = None
        if (
            not self.config.profiling.limit
            and self.config.profiling.use_sampling
            and table.rows_count
            and table.rows_count > self.config.profiling.sample_size
        ):
            # GX creates a temporary table from query if query is passed as batch kwargs.
            # We are using fraction-based sampling here, instead of fixed-size sampling because
            # Fixed-size sampling can be slower than equivalent fraction-based sampling
            # as per https://docs.snowflake.com/en/sql-reference/constructs/sample#performance-considerations
            sample_pc = 100 * self.config.profiling.sample_size / table.rows_count
            custom_sql = f'select * from "{db_name}"."{schema_name}"."{table.name}" TABLESAMPLE ({sample_pc:.8f})'
        return {
            **super().get_batch_kwargs(table, schema_name, db_name),
            # Lowercase/Mixedcase table names in Snowflake do not work by default.
            # We need to pass `use_quoted_name=True` for such tables as mentioned here -
            # https://github.com/great-expectations/great_expectations/pull/2023
            "use_quoted_name": (table.name != table.name.upper()),
            "custom_sql": custom_sql,
        }

    def get_profiler_instance(
        self, db_name: Optional[str] = None
    ) -> "DatahubGEProfiler":
        assert db_name

        url = self.config.get_sql_alchemy_url(
            database=db_name,
            username=self.config.username,
            password=self.config.password,
            role=self.config.role,
        )

        logger.debug(f"sql_alchemy_url={url}")

        engine = create_engine(
            url,
            creator=self.callable_for_db_connection(db_name),
            **self.config.get_options(),
        )
        conn = engine.connect()
        inspector = inspect(conn)

        return DatahubGEProfiler(
            conn=inspector.bind,
            report=self.report,
            config=self.config.profiling,
            platform=self.platform,
        )

    def callable_for_db_connection(self, db_name: str) -> Callable:
        def get_db_connection():
            conn = self.config.get_connection()
            conn.cursor().execute(SnowflakeQuery.use_database(db_name))
            return conn

        return get_db_connection
