import logging
from os import chdir, getcwd, path

import ahjo.operations.general.alembic as alembic
import pytest
from sqlalchemy.exc import ProgrammingError

LATEST_REVISION = '46f7c0d382af'

@pytest.mark.mssql
class TestWithSQLServer():

    @pytest.fixture(scope='function', autouse=True)
    def alembic_mssql_setup_and_teardown(self, ahjo_config, mssql_sample, mssql_engine):
        self.config = ahjo_config(mssql_sample)
        self.alembic_table = self.config['alembic_version_table_schema'] + '.' + self.config['alembic_version_table']
        self.config_filepath = path.join(mssql_sample, 'config_development.jsonc')
        self.engine = mssql_engine
        old_cwd = getcwd()
        chdir(mssql_sample)
        yield
        chdir(old_cwd)

    def test_alembic_version_table_should_not_exist(self):
        query = f"SELECT * FROM {self.alembic_table}"
        with pytest.raises(ProgrammingError):
            self.engine.execute(query)

    def test_alembic_version_table_should_contain_latest_revision_after_upgrade_head(self):
        alembic.upgrade_db_to_latest_alembic_version(self.config_filepath)
        query = f"SELECT * FROM {self.alembic_table}"
        result = self.engine.execute(query)
        assert result.fetchone()[0] == LATEST_REVISION

    def test_alembic_version_table_should_be_empty_after_downgrade(self):
        alembic.downgrade_db_to_alembic_base(self.config_filepath)
        query = f"SELECT * FROM {self.alembic_table}"
        result = self.engine.execute(query)
        assert result.fetchone() is None    # no revisions

    def test_latest_revision_should_be_printed(self, caplog):
        caplog.set_level(logging.INFO)
        alembic.upgrade_db_to_latest_alembic_version(self.config_filepath)
        alembic.print_alembic_version(self.engine, self.alembic_table)
        assert f"Alembic version: {LATEST_REVISION}" in caplog.text

    def test_printing_alembic_version_should_fail(self):
        alembic.downgrade_db_to_alembic_base(self.config_filepath)
        query = f"DROP TABLE {self.alembic_table}"
        self.engine.execute(query)
        with pytest.raises(ProgrammingError):
            alembic.print_alembic_version(self.engine, self.alembic_table)

    def test_printing_alembic_version_should_tell_table_is_empty(self, caplog):
        caplog.set_level(logging.INFO)
        alembic.upgrade_db_to_latest_alembic_version(self.config_filepath)
        alembic.downgrade_db_to_alembic_base(self.config_filepath)
        alembic.print_alembic_version(self.engine, self.alembic_table)
        assert f"Table {self.alembic_table} is empty. No deployed revisions." in caplog.text
