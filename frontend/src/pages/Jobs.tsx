import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import JobControls from "@/components/jobs/JobControls";
import JobDetail from "@/components/jobs/JobDetail";
import JobList from "@/components/jobs/JobList";
import { useJob, useJobs, useSchedulerStatus, useTriggerProcess, useTriggerScrape } from "@/hooks/useJobs";
import { useWebSocket } from "@/hooks/useWebSocket";

const Jobs = () => {
  const [selectedJobId, setSelectedJobId] = useState<string | undefined>();
  const jobsQuery = useJobs({ skip: 0, limit: 20 });
  const jobQuery = useJob(selectedJobId);
  const schedulerStatus = useSchedulerStatus();
  const triggerScrape = useTriggerScrape();
  const triggerProcess = useTriggerProcess();
  const queryClient = useQueryClient();
  const wsMessage = useWebSocket();

  useEffect(() => {
    if (wsMessage?.event?.includes("job")) {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    }
  }, [wsMessage, queryClient]);

  return (
    <div className="space-y-6 animate-rise">
      <JobControls
        onScrape={() => triggerScrape.mutate()}
        onProcess={() => triggerProcess.mutate()}
        schedulerRunning={schedulerStatus.data?.running ?? false}
      />
      {jobsQuery.isLoading && <p className="text-sm text-muted">Loading jobs...</p>}
      {jobsQuery.data && (
        <JobList jobs={jobsQuery.data.items} onSelect={(id) => setSelectedJobId(id)} />
      )}
      <JobDetail job={jobQuery.data} />
    </div>
  );
};

export default Jobs;
