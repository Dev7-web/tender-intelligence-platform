import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import SearchPanel from "@/components/search/SearchPanel";
import SearchResults from "@/components/search/SearchResults";
import { useCompanies } from "@/hooks/useCompanies";
import { useSearch } from "@/hooks/useSearch";

const Search = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { data: companiesData } = useCompanies({ skip: 0, limit: 50 });
  const searchMutation = useSearch();

  const [state, setState] = useState({
    companyId: "",
    query: "",
    domains: "",
    certifications: "",
    limit: 20,
  });

  useEffect(() => {
    const preset = searchParams.get("company");
    if (preset) {
      setState((prev) => ({ ...prev, companyId: preset }));
    }
  }, [searchParams]);

  const handleSearch = () => {
    if (!state.companyId) {
      return;
    }
    searchMutation.mutate({
      companyId: state.companyId,
      params: {
        query: state.query || undefined,
        domains: state.domains ? state.domains.split(",").map((d) => d.trim()) : undefined,
        certifications: state.certifications
          ? state.certifications.split(",").map((c) => c.trim())
          : undefined,
        limit: state.limit,
      },
    });
  };

  const results = useMemo(() => searchMutation.data?.results || [], [searchMutation.data]);

  return (
    <div className="space-y-6 animate-rise">
      <SearchPanel
        companies={companiesData?.items || []}
        companyId={state.companyId}
        query={state.query}
        domains={state.domains}
        certifications={state.certifications}
        limit={state.limit}
        onChange={(next) => setState((prev) => ({ ...prev, ...next }))}
        onSearch={handleSearch}
      />
      {searchMutation.isPending && <p className="text-sm text-muted">Running search...</p>}
      {searchMutation.data && (
        <SearchResults
          results={results}
          onSelect={(tenderId) => navigate(`/tenders/${tenderId}`)}
        />
      )}
    </div>
  );
};

export default Search;
