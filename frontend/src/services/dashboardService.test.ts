import { describe, expect, it } from "vitest";
import {
  createUser,
  getAlerts,
  getCameras,
  getDetections,
  getReports,
  getUsers,
  updateDetectionStatus,
  updateUser,
} from "./dashboardService";

describe("dashboard service", () => {
  it("exposes the complete mock dashboard domain", () => {
    expect(getCameras().length).toBeGreaterThan(0);
    expect(getDetections().length).toBeGreaterThan(0);
    expect(getAlerts().length).toBeGreaterThan(0);
    expect(getReports().length).toBeGreaterThan(0);
    expect(getUsers().length).toBeGreaterThan(0);
  });

  it("updates a detection status by id", () => {
    const detection = getDetections()[0];
    const originalStatus = detection.status;
    const nextStatus = originalStatus === "reviewed" ? "new" : "reviewed";

    expect(updateDetectionStatus(detection.id, nextStatus)).toBe(true);
    expect(
      getDetections().find((item) => item.id === detection.id)?.status,
    ).toBe(nextStatus);

    updateDetectionStatus(detection.id, originalStatus);
  });

  it("rejects unknown detection updates", () => {
    expect(updateDetectionStatus("DET-UNKNOWN", "reviewed")).toBe(false);
  });

  it("validates and creates users", () => {
    const userCount = getUsers().length;

    expect(createUser("   ", "viewer")).toBeNull();

    const user = createUser("Test Operator", "operator");
    expect(user).toMatchObject({
      name: "Test Operator",
      role: "operator",
      status: "active",
    });
    expect(getUsers()).toHaveLength(userCount + 1);
  });

  it("updates user access details", () => {
    const user = getUsers()[0];
    const originalRole = user.role;
    const originalStatus = user.status;

    expect(updateUser(user.id, "viewer", "inactive")).toBe(true);
    expect(getUsers().find((item) => item.id === user.id)).toMatchObject({
      role: "viewer",
      status: "inactive",
    });

    updateUser(user.id, originalRole, originalStatus);
  });
});
