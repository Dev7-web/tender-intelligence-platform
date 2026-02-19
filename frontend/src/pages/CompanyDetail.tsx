import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import CompanyDetailView from "@/components/companies/CompanyDetail";
import { useCompany } from "@/hooks/useCompanies";
import { fetchCompanySearchHistory } from "@/services/companyApi";

const CompanyDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const companyQuery = useCompany(id);

  const historyQuery = useQuery({
    queryKey: ["companies", id, "history"],
    queryFn: () => fetchCompanySearchHistory(id || ""),
    enabled: Boolean(id),
  });

  if (companyQuery.isLoading) {
    return <p className="text-sm text-muted">Loading company...</p>;
  }

  if (!companyQuery.data) {
    return <p className="text-sm text-muted">Company not found.</p>;
  }

  return (
    <div className="animate-rise">
      <CompanyDetailView
        company={companyQuery.data}
        searchHistory={historyQuery.data || []}
        onSearch={() => navigate(`/search?company=${companyQuery.data.company_id}`)}
      />
    </div>
  );
};

export default CompanyDetail;
