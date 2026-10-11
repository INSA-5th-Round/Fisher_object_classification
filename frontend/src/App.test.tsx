import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import App from "./App";

beforeEach(() => {
  localStorage.clear();
  document.documentElement.classList.remove("light-mode");
  window.location.hash = "";
});

describe("FISHER application shell", () => {
  it("renders the primary operational areas", () => {
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

  it("switches the document theme from the top bar", () => {
    render(<App />);

    const themeButton = screen.getByRole("button", {
      name: "Switch to light mode",
    });

    fireEvent.click(themeButton);

    expect(document.documentElement).toHaveClass("light-mode");
    expect(localStorage.getItem("fisher-theme")).toBe("light");
  });
});
