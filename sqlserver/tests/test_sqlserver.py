# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)

# stdlib
import copy
from nose.plugins.attrib import attr

# project
from tests.checks.common import AgentCheckTest


"""
Runs against AppVeyor's SQLServer setups with their default configurations
"""

CONFIG = {
    'init_config': {
        'custom_metrics': [
            {
                'name': 'sqlserver.clr.execution',
                'type': 'gauge',
                'counter_name': 'CLR Execution',
            },
            {
                'name': 'sqlserver.exec.in_progress',
                'type': 'gauge',
                'counter_name': 'OLEDB calls',
                'instance_name': 'Cumulative execution time (ms) per second',
            },
            {
                'name': 'sqlserver.db.commit_table_entries',
                'type': 'gauge',
                'counter_name': 'Log Flushes/sec',
                'instance_name': 'ALL',
                'tag_by': 'db',
            },
        ],
    }
}

SQL2008_INSTANCE = {
    'host': '(local)\SQL2008R2SP2',
    'username': 'sa',
    'password': 'Password12!',
}

SQL2012_INSTANCE = {
    'host': '(local)\SQL2012SP1',
    'username': 'sa',
    'password': 'Password12!',
}

SQL2014_INSTANCE = {
    'host': '(local)\SQL2014',
    'username': 'sa',
    'password': 'Password12!',
}

LINUX_INSTANCE = {
    'host': 'localhost',
    'username': 'sa',
    'password': 'dd-ci',
}

EXPECTED_METRICS = [
    'sqlserver.buffer.cache_hit_ratio',
    'sqlserver.buffer.page_life_expectancy',
    'sqlserver.stats.batch_requests',
    'sqlserver.stats.sql_compilations',
    'sqlserver.stats.sql_recompilations',
    'sqlserver.stats.connections',
    'sqlserver.stats.lock_waits',
    'sqlserver.access.page_splits',
    'sqlserver.stats.procs_blocked',
    'sqlserver.buffer.checkpoint_pages',
]


@attr('unix')
@attr('fixme')
@attr(requires='sqlserver')
class TestSqlserverLinux(AgentCheckTest):
    """Basic Test for sqlserver integration."""
    CHECK_NAME = 'sqlserver'

    def test_check(self):
        config = copy.deepcopy(CONFIG)
        config['instances'] = [LINUX_INSTANCE]

        self.run_check_twice(config, force_reload=True)

        # FIXME: assert something, someday


@attr('windows')
@attr(requires='sqlserver')
class TestSqlserver(AgentCheckTest):
    """Basic Test for sqlserver integration."""
    CHECK_NAME = 'sqlserver'

    def _test_check(self, config):
        self.run_check_twice(config, force_reload=True)

        # Check our custom metrics
        self.assertMetric('sqlserver.clr.execution')
        self.assertMetric('sqlserver.exec.in_progress')
        # Make sure the ALL custom metric is tagged by db
        self.assertMetricTagPrefix('sqlserver.db.commit_table_entries', tag_prefix='db')

        instance_tags = config['instances'][0].get('tags', [])
        expected_tags = instance_tags + ['host:{}'.format(config['instances'][0]['host']), 'db:master']
        for metric in EXPECTED_METRICS:
            self.assertMetric(metric, count=1)

        self.assertServiceCheckOK('sqlserver.can_connect', tags=expected_tags)

        self.coverage_report()

    @attr('fixme')
    def test_check_2008(self):
        config = copy.deepcopy(CONFIG)
        config['instances'] = [SQL2008_INSTANCE]
        self._test_check(config)

    def test_check_2012(self):
        config = copy.deepcopy(CONFIG)
        config['instances'] = [SQL2012_INSTANCE]
        self._test_check(config)

    @attr('fixme')
    def test_check_2014(self):
        config = copy.deepcopy(CONFIG)
        config['instances'] = [SQL2014_INSTANCE]
        self._test_check(config)

    def test_check_no_connection(self):
        config = copy.deepcopy(CONFIG)
        config['instances'] = [{
            'host': '(local)\SQL2012SP1',
            'username': 'sa',
            'password': 'InvalidPassword',
            'timeout': 1,
            'tags': ['optional:tag1'],
        }]

        with self.assertRaisesRegexp(Exception, 'Unable to connect to SQL Server'):
            self.run_check(config, force_reload=True)

        self.assertServiceCheckCritical('sqlserver.can_connect',
                                        tags=['host:(local)\SQL2012SP1', 'db:master', 'optional:tag1'])