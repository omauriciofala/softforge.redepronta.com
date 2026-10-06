import { defineConfig } from "orval";

export default defineConfig({
  softforgeApi: {
    input: {
      target: "../api/openapi.json",
    },
    output: {
      mode: "tags-split",
      target: "./src/api/generated",
      schemas: "./src/api/generated/models",
      client: "react-query",
      httpClient: "axios",
      override: {
        mutator: {
          path: "./src/lib/api-client.ts",
          name: "customInstance",
        },
        query: {
          useQuery: true,
          useMutation: true,
        },
      },
    },
  },
});
