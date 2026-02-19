import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface TenderFiltersProps {
  search: string;
  status: string;
  domains: string;
  expired: string;
  onApply: () => void;
  onChange: (next: { search: string; status: string; domains: string; expired: string }) => void;
}

const TenderFilters = ({ search, status, domains, expired, onApply, onChange }: TenderFiltersProps) => {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-border bg-white p-4 shadow-card lg:flex-row lg:items-end">
      <div className="flex-1">
        <label className="text-xs uppercase text-muted">Search</label>
        <Input
          value={search}
          placeholder="Bid ID, title, department"
          onChange={(event) => onChange({ search: event.target.value, status, domains, expired })}
        />
      </div>
      <div className="w-full lg:w-60">
        <label className="text-xs uppercase text-muted">Domains</label>
        <Input
          value={domains}
          placeholder="IT, Software"
          onChange={(event) => onChange({ search, status, domains: event.target.value, expired })}
        />
      </div>
      <div className="w-full lg:w-48">
        <label className="text-xs uppercase text-muted">Status</label>
        <select
          className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm"
          value={status}
          onChange={(event) => onChange({ search, status: event.target.value, domains, expired })}
        >
          <option value="">All</option>
          <option value="processed">Processed</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
        </select>
      </div>
      <div className="w-full lg:w-40">
        <label className="text-xs uppercase text-muted">Expiry</label>
        <select
          className="h-10 w-full rounded-md border border-border bg-white px-3 text-sm"
          value={expired}
          onChange={(event) => onChange({ search, status, domains, expired: event.target.value })}
        >
          <option value="">All</option>
          <option value="false">Active</option>
          <option value="true">Expired</option>
        </select>
      </div>
      <Button onClick={onApply}>Apply Filters</Button>
    </div>
  );
};

export default TenderFilters;
