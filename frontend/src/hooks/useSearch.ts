import { useMutation } from "@tanstack/react-query";

import { searchTenders, SearchParams } from "@/services/searchApi";

export const useSearch = () => {
  return useMutation({
    mutationFn: ({ companyId, params }: { companyId: string; params: SearchParams }) =>
      searchTenders(companyId, params),
  });
};
