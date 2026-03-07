import { describe, expect, it } from "vitest";

import { resolveApiBaseUrl } from "./api";

describe("resolveApiBaseUrl", () => {
  it("resolves SSR base URL from NEXT_PUBLIC_API_URL or API_URL fallback", () => {
    expect(
      resolveApiBaseUrl({
        isBrowser: false,
        nextPublicApiUrl: "https://api.example.com/api/v1",
        apiUrl: "http://internal-api:8000",
      }),
    ).toBe("https://api.example.com/api/v1");

    expect(
      resolveApiBaseUrl({
        isBrowser: false,
        apiUrl: "http://internal-api:8000",
      }),
    ).toBe("http://internal-api:8000/api/v1");
  });

  it("resolves browser base URL from NEXT_PUBLIC_API_URL or relative fallback", () => {
    expect(
      resolveApiBaseUrl({
        isBrowser: true,
        nextPublicApiUrl: "https://api.example.com/api/v1",
      }),
    ).toBe("https://api.example.com/api/v1");

    expect(resolveApiBaseUrl({ isBrowser: true })).toBe("/api/v1");
  });
});
