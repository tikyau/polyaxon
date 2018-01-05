# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from datetime import datetime
from unittest.mock import patch

import mock

from polyaxon_schemas.polyaxonfile.specification import Specification

from experiments.models import ExperimentStatus, ExperimentJob, Experiment
from experiments.tasks import set_metrics
from factories.factory_repos import RepoFactory
from factories.fixtures import experiment_spec_content, exec_experiment_spec_content
from spawner.utils.constants import ExperimentLifeCycle, JobLifeCycle

from factories.factory_experiments import ExperimentFactory
from factories.factory_projects import ExperimentGroupFactory
from tests.fixtures import (
    start_experiment_value,
)
from tests.utils import BaseTest


class TestExperimentModel(BaseTest):
    def test_experiment_creation_triggers_status_creation_mocks(self):
        with patch('projects.tasks.start_group_experiments.apply_async') as _:
            experiment_group = ExperimentGroupFactory()

        with patch('experiments.tasks.start_experiment.delay') as mock_fct:
            with patch.object(Experiment, 'set_status') as mock_fct2:
                ExperimentFactory(experiment_group=experiment_group)

        assert mock_fct.call_count == 0
        assert mock_fct2.call_count == 1

    def test_experiment_creation_triggers_status_creation(self):
        with patch('projects.tasks.start_group_experiments.apply_async') as _:
            experiment_group = ExperimentGroupFactory()

        experiment = ExperimentFactory(experiment_group=experiment_group)

        assert ExperimentStatus.objects.filter(experiment=experiment).count() == 1
        assert experiment.last_status == ExperimentLifeCycle.CREATED

    def test_independent_experiment_creation_triggers_experiment_scheduling_mocks(self):
        with patch('projects.tasks.start_group_experiments.apply_async') as _:
            with patch('experiments.tasks.build_experiment.apply_async') as mock_fct:
                with patch.object(Experiment, 'set_status') as mock_fct2:
                    ExperimentFactory()

        assert mock_fct.call_count == 1
        assert mock_fct2.call_count == 1

    def test_independent_experiment_creation_triggers_experiment_scheduling(self):
        content = Specification.read(experiment_spec_content)
        experiment = ExperimentFactory(config=content.parsed_data)
        assert experiment.is_independent is True

        assert ExperimentStatus.objects.filter(experiment=experiment).count() == 2
        assert list(ExperimentStatus.objects.filter(experiment=experiment).values_list(
            'status', flat=True)) == [ExperimentLifeCycle.CREATED, ExperimentLifeCycle.SCHEDULED]
        assert experiment.last_status == ExperimentLifeCycle.SCHEDULED

        # Assert also that experiment is monitored
        assert experiment.last_status == ExperimentLifeCycle.SCHEDULED

    def test_independent_experiment_creation_with_run_triggers_experiment_building_scheduling(self):
        content = Specification.read(exec_experiment_spec_content)
        # Create a repo for the project
        repo = RepoFactory()

        with patch('repos.dockerize.build_experiment') as mock_docker_build:
            experiment = ExperimentFactory(config=content.parsed_data, project=repo.project)

        assert mock_docker_build.call_count == 1
        assert experiment.project.repo is not None
        assert experiment.is_independent is True

        assert ExperimentStatus.objects.filter(experiment=experiment).count() == 3
        assert list(ExperimentStatus.objects.filter(experiment=experiment).values_list(
            'status', flat=True)) == [ExperimentLifeCycle.CREATED,
                                      ExperimentLifeCycle.BUILDING,
                                      ExperimentLifeCycle.SCHEDULED]
        assert experiment.last_status == ExperimentLifeCycle.SCHEDULED

    @mock.patch('spawner.scheduler.K8SSpawner')
    def test_create_experiment_with_valid_spec(self, spawner_mock):
        mock_instance = spawner_mock.return_value
        mock_instance.start_experiment.return_value = start_experiment_value

        content = Specification.read(experiment_spec_content)
        experiment = ExperimentFactory(config=content.parsed_data)
        assert experiment.is_independent is True

        assert ExperimentStatus.objects.filter(experiment=experiment).count() == 3
        assert list(ExperimentStatus.objects.filter(experiment=experiment).values_list(
            'status', flat=True)) == [ExperimentLifeCycle.CREATED,
                                      ExperimentLifeCycle.SCHEDULED,
                                      ExperimentLifeCycle.STARTING]
        assert experiment.last_status == ExperimentLifeCycle.STARTING

        # Assert also that experiment is monitored
        assert experiment.last_status == ExperimentLifeCycle.STARTING
        # Assert also that experiment is monitored
        assert experiment.last_status == ExperimentLifeCycle.STARTING

        # Assert 3 job were created
        assert ExperimentJob.objects.filter(experiment=experiment).count() == 3
        jobs_statuses = ExperimentJob.objects.values_list('statuses__status', flat=True)
        assert set(jobs_statuses) == {JobLifeCycle.CREATED, }
        jobs = ExperimentJob.objects.filter(experiment=experiment)
        assert experiment.calculated_status == ExperimentLifeCycle.STARTING

        for job in jobs:
            # Assert the jobs status is created
            assert job.last_status == JobLifeCycle.CREATED

    def test_delete_experiment_triggers_experiment_stop_mocks(self):
        experiment = ExperimentFactory()
        with patch('spawner.scheduler.stop_experiment') as mock_fct:
            experiment.delete()

        assert mock_fct.call_count == 1

    def test_set_metrics(self):
        content = Specification.read(experiment_spec_content)
        experiment = ExperimentFactory(config=content.parsed_data)
        assert experiment.metrics.count() == 0

        create_at = datetime.utcnow()
        set_metrics(experiment_uuid=experiment.uuid.hex,
                    created_at=create_at,
                    metrics={'accuracy': 0.9, 'precision': 0.9})

        assert experiment.metrics.count() == 1