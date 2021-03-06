import logging

from django.contrib.postgres.fields import JSONField
from django.db import models

from db.models.abstract_jobs import AbstractJobStatus, JobMixin
from db.models.plugins import PluginJobBase
from libs.spec_validation import validate_notebook_spec_config
from polyaxon_schemas.polyaxonfile.specification import NotebookSpecification
from polyaxon_schemas.polyaxonfile.utils import cached_property

_logger = logging.getLogger('db.notebooks')


class NotebookJob(PluginJobBase, JobMixin):
    """A model that represents the configuration for tensorboard job."""
    JOBS_NAME = 'notebooks'

    project = models.ForeignKey(
        'db.Project',
        on_delete=models.CASCADE,
        related_name='notebook_jobs')
    config = JSONField(
        help_text='The compiled polyaxonfile for the notebook job.',
        validators=[validate_notebook_spec_config])
    status = models.OneToOneField(
        'db.NotebookJobStatus',
        related_name='+',
        blank=True,
        null=True,
        editable=True,
        on_delete=models.SET_NULL)

    class Meta:
        app_label = 'db'

    def __str__(self):
        return '{}.notebooks.{}'.format(self.project.unique_name, self.sequence)

    def save(self, *args, **kwargs):  # pylint:disable=arguments-differ
        if self.pk is None:
            last = NotebookJob.objects.filter(project=self.project).last()
            self.sequence = 1
            if last:
                self.sequence = last.sequence + 1

        super(NotebookJob, self).save(*args, **kwargs)

    @cached_property
    def specification(self):
        return NotebookSpecification(values=self.config)

    def set_status(self, status, message=None, details=None):  # pylint:disable=arguments-differ
        return self._set_status(status_model=NotebookJobStatus,
                                logger=_logger,
                                status=status,
                                message=message,
                                details=details)


class NotebookJobStatus(AbstractJobStatus):
    """A model that represents notebook job status at certain time."""
    job = models.ForeignKey(
        'db.NotebookJob',
        on_delete=models.CASCADE,
        related_name='statuses')

    class Meta(AbstractJobStatus.Meta):
        app_label = 'db'
        verbose_name_plural = 'Notebook Job Statuses'
