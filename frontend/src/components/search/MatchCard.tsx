import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { SearchResult } from "@/types/search";

interface MatchCardProps {
  result: SearchResult;
  onView?: () => void;
}

const MatchCard = ({ result, onView }: MatchCardProps) => {
  const percent = Math.round(result.score * 100);
  return (
    <Card className="space-y-3" onClick={onView}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-muted">{result.bid_id}</p>
          <p className="text-lg font-semibold">Match Score</p>
        </div>
        <Badge className="bg-primary/10 text-primary">{percent}%</Badge>
      </div>
      <Progress value={percent} />
      <ul className="text-xs text-muted list-disc pl-4">
        {result.match_reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
    </Card>
  );
};

export default MatchCard;
