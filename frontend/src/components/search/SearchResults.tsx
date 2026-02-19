import MatchCard from "@/components/search/MatchCard";
import { SearchResult } from "@/types/search";

interface SearchResultsProps {
  results: SearchResult[];
  onSelect: (tenderId: string) => void;
}

const SearchResults = ({ results, onSelect }: SearchResultsProps) => {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {results.map((result) => (
        <MatchCard key={result.tender_id} result={result} onView={() => onSelect(result.tender_id)} />
      ))}
      {!results.length && <p className="text-sm text-muted">No results yet.</p>}
    </div>
  );
};

export default SearchResults;
