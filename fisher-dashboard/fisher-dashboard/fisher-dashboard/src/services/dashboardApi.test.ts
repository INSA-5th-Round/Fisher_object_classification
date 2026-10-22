import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, createRemoteUser, fetchCameras } from "./dashboardApi";

describe("dashboard API", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("sends typed API requests with JSON bodies", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          id: "USR-001",
          name: "Operator",
          role: "operator",
          status: "active",
        }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(createRemoteUser("Operator", "operator")).resolves.toMatchObject(
      {
        id: "USR-001",
        name: "Operator",
      },
    );

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/users$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ name: "Operator", role: "operator" }),
        headers: expect.objectContaining({
          Accept: "application/json",
          "Content-Type": "application/json",
        }),
      }),
    );
  });

  it("surfaces backend error messages and HTTP status", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      statusText: "Service Unavailable",
      text: () => Promise.resolve(JSON.stringify({ message: "Try again later" })),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchCameras()).rejects.toMatchObject({
      name: "ApiError",
      message: "Try again later",
      status: 503,
    } satisfies Partial<ApiError>);
  });
});
