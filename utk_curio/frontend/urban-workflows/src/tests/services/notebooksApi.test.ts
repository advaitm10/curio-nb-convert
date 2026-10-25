import { notebooksApi } from "../../services/notebooksApi";

describe("notebooksApi.convert", () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  test("sends notebook JSON to the Python conversion endpoint", async () => {
    const spec = {
      dataflow: {
        name: "example",
        nodes: [],
        edges: [],
        task: "",
        timestamp: 123,
        provenance_id: "example",
      },
    };
    const fetchMock = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => spec,
    });
    (global as unknown as { fetch: unknown }).fetch = fetchMock;
    const notebook = { cells: [], nbformat: 4, nbformat_minor: 5 };

    await expect(notebooksApi.convert(notebook, "example")).resolves.toEqual(spec);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/notebooks\/convert$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ notebook, name: "example" }),
      }),
    );
  });
});
