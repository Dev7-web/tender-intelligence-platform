import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Company } from "@/types/company";

interface SearchPanelState {
  companyId: string;
  query: string;
  domains: string;
  certifications: string;
  limit: number;
}

interface SearchPanelProps extends SearchPanelState {
  companies: Company[];
  onChange: (next: Partial<SearchPanelState>) => void;
  onSearch: () => void;
}

const SearchPanel = ({
  companies,
  companyId,
  query,
  domains,
  certifications,
  limit,
  onChange,
  onSearch,
}: SearchPanelProps) => {
  return (
    <div className="rounded-2xl border border-border bg-white p-6 shadow-card space-y-4">
      <div>
        <label className="text-xs uppercase text-muted">Company</label>
        <select
          className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm"
          value={companyId}
          onChange={(event) => onChange({ companyId: event.target.value })}
        >
          <option value="">Select company</option>
          {companies.map((company) => (
            <option key={company.company_id} value={company.company_id}>
              {company.name || company.metadata?.company_name || company.company_id}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="text-xs uppercase text-muted">Query</label>
        <Input value={query} onChange={(event) => onChange({ query: event.target.value })} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label className="text-xs uppercase text-muted">Domains</label>
          <Input value={domains} onChange={(event) => onChange({ domains: event.target.value })} />
        </div>
        <div>
          <label className="text-xs uppercase text-muted">Certifications</label>
          <Input
            value={certifications}
            onChange={(event) => onChange({ certifications: event.target.value })}
          />
        </div>
      </div>
      <div>
        <label className="text-xs uppercase text-muted">Results limit</label>
        <Input
          type="number"
          value={limit}
          onChange={(event) => onChange({ limit: Number(event.target.value) })}
        />
      </div>
      <Button onClick={onSearch} disabled={!companyId}>
        Run Search
      </Button>
    </div>
  );
};

export default SearchPanel;
