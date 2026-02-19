import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface QueueItem {
  bid_id: string;
  scraped_info?: { items?: string };
  status?: { llm_processed?: boolean; last_error?: string | null };
}

interface ProcessingQueueProps {
  queue: QueueItem[];
}

const ProcessingQueue = ({ queue }: ProcessingQueueProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Processing Queue</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {(queue || []).map((item) => (
            <div key={item.bid_id} className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold text-text">{item.bid_id}</p>
                <p className="text-xs text-muted line-clamp-1">{item.scraped_info?.items}</p>
              </div>
              <Badge className="bg-warning/10 text-warning">Pending</Badge>
            </div>
          ))}
          {!queue?.length && <p className="text-sm text-muted">Queue is empty.</p>}
        </div>
      </CardContent>
    </Card>
  );
};

export default ProcessingQueue;
