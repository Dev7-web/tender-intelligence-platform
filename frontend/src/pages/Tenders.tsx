import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import TenderFilters from "@/components/tenders/TenderFilters";
import TenderList from "@/components/tenders/TenderList";
import { useTenders } from "@/hooks/useTenders";

const Tenders = () => {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({ search: "", status: "", domains: "", expired: "" });
  const [applied, setApplied] = useState(filters);

  const params = useMemo(
    () => ({
      skip: 0,
      limit: 50,
      status: applied.status || undefined,
      search: applied.search || undefined,
      domains: applied.domains ? applied.domains.split(",").map((d) => d.trim()) : undefined,
      expired: applied.expired ? applied.expired === "true" : undefined,
    }),
    [applied]
  );

  const { data, isLoading } = useTenders(params);

  return (
    <div className="space-y-6 animate-rise">
      <TenderFilters
        search={filters.search}
        status={filters.status}
        domains={filters.domains}
        expired={filters.expired}
        onChange={setFilters}
        onApply={() => setApplied(filters)}
      />
      {isLoading && <p className="text-sm text-muted">Loading tenders...</p>}
      {data && (
        <TenderList
          tenders={data.items}
          onSelect={(id) => navigate(`/tenders/${id}`)}
        />
      )}
    </div>
  );
};

export default Tenders;
