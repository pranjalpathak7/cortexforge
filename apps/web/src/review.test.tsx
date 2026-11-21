// @vitest-environment jsdom
import React from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App, Diff, RunMode, Status } from "./main";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("review evidence", () => {
  it("identifies injected scenarios without hiding the real state", () => {
    render(
      <>
        <RunMode mode="demo" fault="security" />
        <Status value="FAILED" />
      </>,
    );
    expect(
      screen.getByText("Controlled demo · injected security scenario"),
    ).toBeTruthy();
    expect(screen.getByText("FAILED")).toBeTruthy();
  });
  it("shows failed state explicitly", () => {
    render(<Status value="BLOCKED" />);
    expect(screen.getByText("BLOCKED").className).toContain("bad");
  });
  it("keeps removed and added code in separate panes", () => {
    const { container } = render(
      <Diff text={"@@ hunk\n-old\n+new\n context"} />,
    );
    const panes = container.querySelectorAll("pre");
    expect(panes[0].textContent).toContain("-old");
    expect(panes[0].textContent).not.toContain("+new");
    expect(panes[1].textContent).toContain("+new");
    expect(panes[1].textContent).not.toContain("-old");
  });
});

describe("session and mode boundaries", () => {
  it("submits the selected trusted profile to the backend", async () => {
    const request = vi.fn(async (url: string, options?: RequestInit) => ({
      ok: true,
      json: async () =>
        url.endsWith("/health")
          ? { docker: true, agents: {} }
          : options?.method === "POST"
            ? { id: "created" }
            : [],
    }));
    vi.stubGlobal("fetch", request);
    const query = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={query}>
        <App />
      </QueryClientProvider>,
    );
    fireEvent.change(screen.getByLabelText("Review token"), {
      target: { value: "test-token" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Connect session" }));
    fireEvent.click(screen.getByRole("button", { name: "Create run" }));
    fireEvent.change(screen.getByLabelText("Committed local Git repository"), {
      target: { value: "sample" },
    });
    fireEvent.change(screen.getByLabelText("Independent acceptance profile"), {
      target: { value: "refunds" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Start engineering run" }),
    );
    await waitFor(() =>
      expect(
        request.mock.calls.some(
          ([url, options]) =>
            url === "/api/runs" &&
            options?.method === "POST" &&
            JSON.parse(String(options.body)).acceptance_profile === "refunds",
        ),
      ).toBe(true),
    );
    query.clear();
  });
  it("keeps token input mounted until explicitly connecting and defaults to live mode", async () => {
    const request = vi.fn(async (url: string) => ({
      ok: true,
      json: async () =>
        url.endsWith("/health") ? { docker: false, agents: {} } : [],
    }));
    vi.stubGlobal("fetch", request);
    const query = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={query}>
        <App />
      </QueryClientProvider>,
    );
    fireEvent.change(screen.getByLabelText("Review token"), {
      target: { value: "f" },
    });
    expect(screen.getByLabelText("Review token")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Review token"), {
      target: { value: "full-test-token" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Connect session" }));
    await waitFor(() =>
      expect(request.mock.calls.some(([url]) => url === "/api/runs")).toBe(
        true,
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Create run" }));
    expect(
      (screen.getByLabelText("Model mode") as HTMLSelectElement).value,
    ).toBe("live");
    expect(
      (screen.getByLabelText("Controlled fault") as HTMLSelectElement).disabled,
    ).toBe(true);
    fireEvent.change(screen.getByLabelText("Model mode"), {
      target: { value: "demo" },
    });
    expect(
      (screen.getByLabelText("Controlled fault") as HTMLSelectElement).disabled,
    ).toBe(false);
    query.clear();
  });
});
