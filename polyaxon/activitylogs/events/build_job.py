import activitylogs

from event_manager.events import build_job

activitylogs.subscribe(build_job.BuildJobStartedTriggeredEvent)
activitylogs.subscribe(build_job.BuildJobSoppedTriggeredEvent)
activitylogs.subscribe(build_job.BuildJobViewedEvent)
