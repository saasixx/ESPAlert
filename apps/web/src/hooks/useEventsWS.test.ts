import { describe, expect, it } from "vitest";

import { resolveEventsWsUrl } from "./useEventsWS";

describe("resolveEventsWsUrl", () => {
  it("prioritizes NEXT_PUBLIC_WS_URL when it is defined", () => {
    expect(
      resolveEventsWsUrl({
        nextPublicWsUrl: "wss://stream.example.com/events",
        nextPublicApiUrl: "https://api.example.com/api/v1",
        locationProtocol: "https:",
        locationHost: "example.com",
      }),
    ).toBe("wss://stream.example.com/events");
  });

  it("falls back to NEXT_PUBLIC_API_URL and then window location", () => {
    expect(
      resolveEventsWsUrl({
        nextPublicApiUrl: "https://api.example.com/api/v1",
        locationProtocol: "https:",
      }),
    ).toBe("wss://api.example.com/api/v1/ws/events");

    expect(
      resolveEventsWsUrl({
        locationProtocol: "http:",
        locationHost: "localhost:3000",
      }),
    ).toBe("ws://localhost:3000/api/v1/ws/events");
  });
});
