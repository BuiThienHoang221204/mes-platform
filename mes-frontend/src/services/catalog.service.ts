import { getData } from "./http";
import type { ReasonGroupValue } from "@/constants/reasons";

export type CatalogReason = {
  id: number;
  group_code: string;
  name: string;
  is_active: boolean;
};

export const catalogService = {
  reasons: (group?: ReasonGroupValue) =>
    getData<CatalogReason[]>("/reasons", group ? { group } : undefined),
};
