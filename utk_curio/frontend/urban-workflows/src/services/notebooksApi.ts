import { apiFetch } from "../utils/authApi";
import type { TrillSpec } from "../NotebookConvertor";

export const notebooksApi = {
  convert(notebook: Record<string, unknown>, name: string): Promise<TrillSpec> {
    return apiFetch<TrillSpec>("/api/notebooks/convert", {
      method: "POST",
      body: JSON.stringify({ notebook, name }),
    });
  },
};
