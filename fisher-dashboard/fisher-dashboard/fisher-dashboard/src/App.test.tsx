import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import App from "./App";

beforeEach(() => {
  localStorage.clear();
  document.documentElement.classList.remove("light-mode");
  window.location.hash = "";
});

describe("FISHER application shell", () => {
  it("displays login screen requiring username, email, and password when unauthenticated", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: /FISHER CCTV/i })).toBeVisible();
    expect(screen.getByLabelText(/Username/i)).toBeVisible();
    expect(screen.getByLabelText(/Authorized Email Address/i)).toBeVisible();
    expect(screen.getByLabelText(/Password/i)).toBeVisible();
    expect(screen.getByRole("button", { name: /Sign In/i })).toBeVisible();
  });

  it("renders the primary operational areas when authenticated", () => {
    localStorage.setItem("fisher_auth_token", "test-valid-session-token");
    localStorage.setItem(
      "fisher_user",
      JSON.stringify({
        id: "USR-001",
        name: "Security Administrator",
        email: "admin@fisher.cctv",
        username: "admin",
        role: "admin",
        status: "active",
      }),
    );

    render(<App />);

    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    expect(screen.getByRole("link", { name: /Live CCTV/i })).toBeVisible();
    expect(screen.getByRole("link", { name: /Alert Center/i })).toBeVisible();
    expect(
      screen.getByRole("link", { name: /Detection Results/i }),
    ).toBeVisible();
    expect(
      screen.getByRole("link", { name: /User Management/i }),
    ).toBeVisible();
  });

  it("switches the document theme from the top bar when authenticated", () => {
    localStorage.setItem("fisher_auth_token", "test-valid-session-token");
    localStorage.setItem(
      "fisher_user",
      JSON.stringify({
        id: "USR-001",
        name: "Security Administrator",
        email: "admin@fisher.cctv",
        username: "admin",
        role: "admin",
        status: "active",
      }),
    );

    render(<App />);

    const themeButton = screen.getByRole("button", {
      name: "Switch to light mode",
    });

    fireEvent.click(themeButton);

    expect(document.documentElement).toHaveClass("light-mode");
    expect(localStorage.getItem("fisher-theme")).toBe("light");
  });
});
