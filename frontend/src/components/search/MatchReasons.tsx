interface MatchReasonsProps {
  reasons: string[];
}

const MatchReasons = ({ reasons }: MatchReasonsProps) => {
  return (
    <ul className="list-disc pl-4 text-xs text-muted">
      {reasons.map((reason) => (
        <li key={reason}>{reason}</li>
      ))}
    </ul>
  );
};

export default MatchReasons;
