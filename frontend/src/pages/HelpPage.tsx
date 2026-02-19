const FAQ_ITEMS = [
  {
    q: "How are tenders matched?",
    a: "Matches combine embedding similarity with metadata overlap (domains, technologies, certifications) and interest tag boosts.",
  },
  {
    q: "How often are tenders scraped?",
    a: "In MVP, scraping is manually triggered from the dashboard using 'Scrape & Analyze now'.",
  },
  {
    q: "What if AI analysis is missing details?",
    a: "AI replies include only available context. Always validate final decisions with the official tender documents.",
  },
];

const HelpPage = () => {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold text-[#232937] md:text-4xl">Help</h1>

      <div className="rounded-xl border border-[#d8dce6] bg-white p-5">
        <h2 className="text-xl font-semibold text-[#2b3040] md:text-2xl">Frequently Asked Questions</h2>
        <div className="mt-3 space-y-3">
          {FAQ_ITEMS.map((item) => (
            <div key={item.q} className="rounded-lg border border-[#e5e8ef] p-3">
              <p className="text-base font-medium text-[#232937]">{item.q}</p>
              <p className="mt-1 text-sm text-[#5d657b]">{item.a}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-[#d8dce6] bg-white p-5">
        <h2 className="text-xl font-semibold text-[#2b3040] md:text-2xl">Contact</h2>
        <p className="mt-2 text-sm text-[#5d657b]">Email: support@tenderagent.local</p>
        <p className="text-sm text-[#5d657b]">Response time: 1 business day</p>
      </div>
    </div>
  );
};

export default HelpPage;
