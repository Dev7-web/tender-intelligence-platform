import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import TenderDetailView from "@/components/tenders/TenderDetail";
import { useReprocessTender, useTender } from "@/hooks/useTenders";
import { fetchTenderMatches } from "@/services/tenderApi";

const TenderDetail = () => {
  const { id } = useParams();
  const tenderQuery = useTender(id);
  const reprocess = useReprocessTender();

  const matchesQuery = useQuery({
    queryKey: ["tenders", id, "matches"],
    queryFn: () => fetchTenderMatches(id || "", 5),
    enabled: Boolean(id),
  });

  if (tenderQuery.isLoading) {
    return <p className="text-sm text-muted">Loading tender...</p>;
  }

  if (!tenderQuery.data) {
    return <p className="text-sm text-muted">Tender not found.</p>;
  }

  return (
    <div className="animate-rise">
      <TenderDetailView
        tender={tenderQuery.data}
        matches={matchesQuery.data?.results || []}
        onReprocess={() => id && reprocess.mutate(id)}
      />
    </div>
  );
};

export default TenderDetail;
