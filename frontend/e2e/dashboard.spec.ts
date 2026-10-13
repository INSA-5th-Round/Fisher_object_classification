import { expect, test } from "@playwright/test";

test.describe("FISHER dashboard shell", () => {
  test("renders the primary workspace", async ({ page }) => {
    await page.goto("/");

    await expect(
      page.getByRole("heading", { name: "Dashboard", exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: /Alert Center/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Live CCTV Feed" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "User Management" }),
    ).toBeVisible();
  });

  test("switches to light mode", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: "Switch to light mode" }).click();

    await expect(page.locator("html")).toHaveClass(/light-mode/);
  });

  test("keeps the sidebar usable on mobile", async ({ page }) => {
    await page.goto("/");

    const sidebar = page.locator(".sidebar");
    await expect(sidebar).toBeVisible();
    await expect(
      page.getByRole("link", { name: /Alert Center/i }),
    ).toBeVisible();
  });
});
