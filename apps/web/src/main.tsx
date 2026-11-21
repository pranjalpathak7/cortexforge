import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  Activity,
  Box,
  GitBranch,
  ShieldCheck,
  Terminal,
  Layers,
  Settings,
  Plus,
  CheckCircle2,
  Clock,
  FileCode2,
} from "lucide-react";
import "./style.css";

type Event = {
  id: number;
  time: string;
  kind: string;
  payload: Record<string, unknown>;
};
type Check = {
  operation: string;
  exit_code: number;
  output: string;
  duration_ms: number;
  executor: string;
  phase: string;
  iteration: number;
};
type Run = {
  id: string;
  requirement: string;
  state: string;
  mode: string;
  fault: string;
  created: string;
  branch: string;
  repairs: number;
  error?: string;
  diff?: string;
  summary?: string;
  risks?: string[];
  checks: Check[];
  baseline: Check[];
  events?: Event[];
  evidence_hash?: string;
  tree_hash?: string;
  rubric?: Record<string, unknown>;
  specification?: { questions: string[] };
  decision?: Record<string, unknown>;
};

export function Status({ value }: { value: string }) {
  return (
    <span
      className={`status ${/FAILED|BLOCKED|REJECTED/.test(value) ? "bad" : /APPROVED|HUMAN_APPROVAL/.test(value) ? "good" : ""}`}
    >
      {value.replaceAll("_", " ")}
    </span>
  );
}

export function RunMode({ mode, fault }: { mode: string; fault: string }) {
  return (
    <span>
      {mode === "demo" && fault !== "none"
        ? `Controlled demo · injected ${fault} scenario`
        : mode === "demo"
          ? "Fixture demo · no injected fault"
          : "Live AI"}
    </span>
  );
}
export function Diff({ text }: { text: string }) {
  return (
    <div className="diff">
      <div>
        <h3>Original / removed</h3>
        <pre>
          {text
            .split("\n")
            .filter((l) => !l.startsWith("+"))
            .join("\n") || "No removed lines"}
        </pre>
      </div>
      <div>
        <h3>Proposed / added</h3>
        <pre>
          {text
            .split("\n")
            .filter((l) => !l.startsWith("-"))
            .join("\n") || "No added lines"}
        </pre>
      </div>
    </div>
  );
}

export function App() {
  const cache = useQueryClient();
  const [token, setToken] = useState("");
  const [tokenInput, setTokenInput] = useState("");
  const [page, setPage] = useState("Overview");
  const [selected, setSelected] = useState("");
  const [tab, setTab] = useState("Workflow");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [repository, setRepository] = useState("");
  const [requirement, setRequirement] = useState(
    "Add apply_discount(amount: int, percent: int) -> int. Use integer paise, accept percentages 0 through 100, reject negative amounts and invalid percentages with ValueError, round down, and preserve total(). Add boundary tests.",
  );
  const [mode, setMode] = useState("live");
  const [fault, setFault] = useState("none");
  const [acceptanceProfile, setAcceptanceProfile] =
    useState("payments_discount");
  const [reviewer, setReviewer] = useState("");
  const [comment, setComment] = useState("");
  const api = async (path: string, body?: unknown) => {
    const response = await fetch("/api" + path, {
      method: body === undefined ? "GET" : "POST",
      headers: { "Content-Type": "application/json", "X-Review-Token": token },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!response.ok) {
      const e = await response.json();
      throw new Error(
        typeof e.detail === "string"
          ? e.detail
          : JSON.stringify(e.detail || "Request failed"),
      );
    }
    return response.json();
  };
  const health = useQuery({
    queryKey: ["health"],
    queryFn: () => api("/health"),
    refetchInterval: 15000,
  });
  const runs = useQuery<Run[]>({
    queryKey: ["runs", token],
    queryFn: () => api("/runs"),
    enabled: !!token,
    refetchInterval: 3000,
  });
  const detail = useQuery<Run>({
    queryKey: ["run", selected, token],
    queryFn: () => api("/runs/" + selected),
    enabled: !!selected && !!token,
    refetchInterval: 2000,
  });
  const act = async (action: () => Promise<unknown>) => {
    setBusy(true);
    setError("");
    try {
      await action();
      await cache.invalidateQueries();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const run = detail.data;
  const all = runs.data || [];
  const usages = run?.events?.filter((e) => e.kind === "model_usage") || [];
  return (
    <div className="shell">
      <aside>
        <a
          className="brand"
          href="#"
          onClick={() => {
            setPage("Overview");
            setSelected("");
          }}
        >
          <Box size={29} />
          <span>
            CortexForge<small>ENGINEERING CONTROL ROOM</small>
          </span>
        </a>
        <div className="workspace">
          LOCAL WORKSPACE <span>01</span>
        </div>
        <nav>
          {[
            { name: "Overview", icon: Layers },
            { name: "Create run", icon: Plus },
            { name: "Approval center", icon: ShieldCheck },
            { name: "Settings", icon: Settings },
          ].map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={page === name ? "active" : ""}
              onClick={() => {
                setPage(name);
                setSelected("");
              }}
            >
              <Icon size={18} />
              {name}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <ShieldCheck size={20} />
          <strong>Human authority, always.</strong>
          <p>Changes stay isolated until you review the evidence.</p>
          <span className="local">LOCAL DEVELOPMENT</span>
        </div>
      </aside>
      <main>
        <header>
          <span>
            Workspace <span className="slash">/</span>{" "}
            {selected ? "Run inspection" : page}
          </span>
          <span className="connection">
            <i className={health.data?.docker ? "online" : "offline"} />
            {health.error
              ? "Backend unavailable"
              : health.isLoading
                ? "Connecting…"
                : health.data?.docker
                  ? "Sandbox ready"
                  : "Sandbox unavailable"}
          </span>
        </header>
        <div className="content">
          <div className="title">
            <div>
              <p className="eyebrow">AUTONOMOUS ENTERPRISE ENGINEERING</p>
              <h1>
                {selected
                  ? "Engineering in motion."
                  : page === "Overview"
                    ? "Your engineering control room."
                    : page}
              </h1>
              <p className="muted">
                {selected
                  ? run?.requirement || "Loading run…"
                  : "From requirement to reviewed change. Every decision has a trace."}
              </p>
            </div>
            {page === "Overview" && !selected && (
              <button className="primary" onClick={() => setPage("Create run")}>
                <Plus size={18} /> New engineering run
              </button>
            )}
          </div>
          {!token && (
            <section className="notice">
              <strong>Connect your local session</strong>
              <p>
                Enter the REVIEW_TOKEN configured on your backend. It stays in
                memory and is never sent to a model.
              </p>
              <input
                aria-label="Review token"
                type="password"
                placeholder="Local review token"
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
              />
              <button
                className="primary"
                style={{ marginTop: 12 }}
                disabled={!tokenInput}
                onClick={() => setToken(tokenInput)}
              >
                Connect session
              </button>
            </section>
          )}
          {(error || runs.error || detail.error) && (
            <div role="alert" className="notice danger">
              {error ||
                (runs.error as Error)?.message ||
                (detail.error as Error)?.message}
            </div>
          )}
          {selected && run ? (
            <>
              <div className="run-meta">
                <Status value={run.state} />
                <span>
                  {run.mode === "demo"
                    ? "FIXTURE DEMO · NOT LIVE AI"
                    : "LIVE AI"}
                </span>
                <span>
                  <GitBranch size={14} /> {run.branch}
                </span>
                {!["APPROVED", "REJECTED", "FAILED", "CANCELLED"].includes(
                  run.state,
                ) && (
                  <button
                    disabled={
                      busy ||
                      run.events?.some(
                        (e) => e.kind === "cancellation_requested",
                      )
                    }
                    onClick={() => act(() => api(`/runs/${run.id}/cancel`, {}))}
                  >
                    {run.events?.some(
                      (e) => e.kind === "cancellation_requested",
                    )
                      ? "Cancellation requested"
                      : "Cancel run"}
                  </button>
                )}
              </div>
              {run.error && (
                <div className="notice danger">
                  {run.error}
                  {run.state === "BLOCKED" && (
                    <button
                      disabled={busy}
                      onClick={() =>
                        act(() =>
                          api(`/runs/${run.id}/resume`, {
                            clear_demo_fault:
                              run.mode === "demo" && run.fault === "provider",
                          }),
                        )
                      }
                    >
                      Retry / resume
                    </button>
                  )}
                </div>
              )}
              <div className="tabs">
                {[
                  "Workflow",
                  "Agents",
                  "Code review",
                  "Quality & security",
                  "Human review",
                ].map((t) => (
                  <button
                    key={t}
                    className={tab === t ? "selected" : ""}
                    onClick={() => setTab(t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
              {tab === "Workflow" && (
                <>
                  <div className="stages">
                    {[
                      "Analyst",
                      "Architect",
                      "Developer",
                      "QA",
                      "Security",
                      "Release",
                    ].map((stage, i) => (
                      <div key={stage}>
                        <span>{i + 1}</span>
                        <strong>{stage}</strong>
                        <small>
                          {run.events?.some(
                            (e) => e.payload.agent === stage.toLowerCase(),
                          )
                            ? "Evidence recorded"
                            : "Pending"}
                        </small>
                      </div>
                    ))}
                  </div>
                  <section>
                    <div className="section-heading">
                      <h2>Execution timeline</h2>
                      <span className="muted">
                        Persisted events · polls every 2s
                      </span>
                    </div>
                    {run.events
                      ?.slice()
                      .reverse()
                      .map((e) => (
                        <details key={e.id}>
                          <summary>
                            <span className="event-kind">
                              {e.kind.replaceAll("_", " ")}
                            </span>
                            <time>{new Date(e.time).toLocaleTimeString()}</time>
                          </summary>
                          <pre>{JSON.stringify(e.payload, null, 2)}</pre>
                        </details>
                      ))}
                  </section>
                  {run.state === "AWAITING_CLARIFICATION" && (
                    <section>
                      <h2>Clarification needed</h2>
                      <p>{run.specification?.questions.join(" ")}</p>
                      <textarea
                        aria-label="Clarification"
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                      />
                      <button
                        disabled={busy || !comment}
                        onClick={() =>
                          act(() =>
                            api(`/runs/${run.id}/clarify`, { answer: comment }),
                          )
                        }
                      >
                        Submit clarification
                      </button>
                    </section>
                  )}
                </>
              )}
              {tab === "Agents" && (
                <>
                  <div className="agent-grid">
                    {Object.entries(health.data?.agents || {}).map(
                      ([name, spec]) => (
                        <section key={name}>
                          <h2>{name}</h2>
                          <pre>{JSON.stringify(spec, null, 2)}</pre>
                        </section>
                      ),
                    )}
                  </div>
                  <section>
                    <h2>Model usage</h2>
                    <p>
                      {usages.length} recorded calls · {run.repairs} repair
                      attempts
                    </p>
                    <p className="muted">
                      Unknown values are not treated as zero. Configured pricing
                      produces estimates.
                    </p>
                    <table>
                      <thead>
                        <tr>
                          <th>Agent</th>
                          <th>Model</th>
                          <th>Tokens in / out</th>
                          <th>Latency</th>
                          <th>Cost USD</th>
                        </tr>
                      </thead>
                      <tbody>
                        {usages.map((e) => (
                          <tr key={e.id}>
                            <td>{String(e.payload.agent)}</td>
                            <td>{String(e.payload.model || "Unknown")}</td>
                            <td>
                              {String(e.payload.input_tokens ?? "?")} /{" "}
                              {String(e.payload.output_tokens ?? "?")}
                            </td>
                            <td>{String(e.payload.latency_ms)} ms</td>
                            <td>
                              {String(e.payload.cost_usd ?? "Unknown")} (
                              {String(e.payload.cost_status)})
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </section>
                  {run.events
                    ?.filter((e) =>
                      [
                        "agent_input",
                        "agent_output",
                        "validation_error",
                        "disagreement",
                      ].includes(e.kind),
                    )
                    .map((e) => (
                      <details key={e.id}>
                        <summary>
                          {String(e.payload.agent || "Resolution")} · {e.kind}
                        </summary>
                        <pre>{JSON.stringify(e.payload, null, 2)}</pre>
                      </details>
                    ))}
                </>
              )}
              {tab === "Code review" && (
                <section>
                  <h2>Proposed changes</h2>
                  <p>{run.summary || "No implementation yet."}</p>
                  <Diff text={run.diff || ""} />
                </section>
              )}
              {tab === "Quality & security" && (
                <>
                  <div className="metrics">
                    <Metric
                      title="Baseline checks passed"
                      value={String(
                        run.baseline.filter((c) => c.exit_code === 0).length,
                      )}
                    />
                    <Metric
                      title="Repair attempts"
                      value={String(run.repairs)}
                    />
                    <Metric
                      title="Recorded checks"
                      value={String(run.checks.length)}
                    />
                  </div>
                  {[...run.baseline, ...run.checks].map((c, i) => (
                    <section key={i}>
                      <div className="section-heading">
                        <h2>
                          {c.phase} · {c.operation}
                        </h2>
                        <Status
                          value={c.exit_code === 0 ? "PASSED" : "FAILED"}
                        />
                      </div>
                      <p className="muted">
                        {c.executor} · {c.duration_ms} ms · exit {c.exit_code} ·
                        iteration {c.iteration}
                      </p>
                      <pre>{c.output}</pre>
                    </section>
                  ))}
                </>
              )}
              {tab === "Human review" && (
                <section>
                  <h2>Release decision</h2>
                  <p>{run.summary || "Evidence is still being collected."}</p>
                  <ul>
                    {run.risks?.map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>
                  <pre>{JSON.stringify(run.rubric || {}, null, 2)}</pre>
                  <p className="muted">
                    Approval records a decision on this exact evidence. Merge
                    and deployment remain manual.
                  </p>
                  {run.evidence_hash && (
                    <p className="evidence-hash">
                      Evidence SHA-256: <code>{run.evidence_hash}</code>
                    </p>
                  )}
                  {run.tree_hash && (
                    <p className="evidence-hash">
                      Source SHA-256: <code>{run.tree_hash}</code>
                    </p>
                  )}
                  {run.state === "AWAITING_HUMAN_APPROVAL" && (
                    <>
                      <label>
                        Reviewer
                        <input
                          value={reviewer}
                          onChange={(e) => setReviewer(e.target.value)}
                        />
                      </label>
                      <label>
                        Review rationale
                        <textarea
                          value={comment}
                          onChange={(e) => setComment(e.target.value)}
                        />
                      </label>
                      <div className="actions">
                        {["approve", "reject"].map((decision) => (
                          <button
                            key={decision}
                            className={decision === "approve" ? "primary" : ""}
                            disabled={busy || !reviewer || !comment}
                            onClick={() =>
                              act(() =>
                                api(`/runs/${run.id}/review`, {
                                  decision,
                                  reviewer,
                                  comment,
                                  evidence_hash: run.evidence_hash,
                                }),
                              )
                            }
                          >
                            {decision === "approve"
                              ? "Approve reviewed change"
                              : "Reject change"}
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                  {run.decision && (
                    <pre>{JSON.stringify(run.decision, null, 2)}</pre>
                  )}
                  {run.state === "APPROVED" && (
                    <button
                      onClick={() =>
                        act(async () => {
                          const r = await fetch(`/api/runs/${run.id}/patch`, {
                            headers: { "X-Review-Token": token },
                          });
                          if (!r.ok) throw new Error("Patch export blocked");
                          const url = URL.createObjectURL(await r.blob());
                          const a = document.createElement("a");
                          a.href = url;
                          a.download = `${run.id}.patch`;
                          a.click();
                          URL.revokeObjectURL(url);
                        })
                      }
                    >
                      Export approved patch
                    </button>
                  )}
                </section>
              )}
            </>
          ) : selected ? (
            <section>Loading run evidence…</section>
          ) : (
            <>
              {page === "Overview" && (
                <>
                  <div className="metrics">
                    <Metric
                      title="Engineering runs"
                      value={String(all.length)}
                      icon={<Layers />}
                    />
                    <Metric
                      title="Awaiting human review"
                      value={String(
                        all.filter((r) => r.state === "AWAITING_HUMAN_APPROVAL")
                          .length,
                      )}
                      icon={<Clock />}
                    />
                    <Metric
                      title="Approved changes"
                      value={String(
                        all.filter((r) => r.state === "APPROVED").length,
                      )}
                      icon={<CheckCircle2 />}
                    />
                    <Metric
                      title="Stopped runs (includes injected demos)"
                      value={String(
                        all.filter((r) =>
                          ["FAILED", "BLOCKED"].includes(r.state),
                        ).length,
                      )}
                      icon={<ShieldCheck />}
                    />
                  </div>
                  <section>
                    <div className="section-heading">
                      <h2>Recent engineering runs</h2>
                      <span className="muted">Live workspace activity</span>
                    </div>
                    <RunList
                      runs={all}
                      select={(id) => {
                        setSelected(id);
                        setTab("Workflow");
                      }}
                      loading={runs.isLoading}
                    />
                  </section>
                  <div className="bottom-grid">
                    <section>
                      <Activity className="accent" />
                      <h2>Evidence at every hand-off</h2>
                      <p className="muted">
                        Inspect structured agent outputs, real tool results,
                        repair attempts and the decisions that connect them.
                      </p>
                    </section>
                    <section>
                      <Terminal className="accent" />
                      <h2>Execution stays contained</h2>
                      <p className="muted">
                        Separate Git worktrees. Docker-only checks. No automatic
                        merge, push or deployment.
                      </p>
                    </section>
                  </div>
                </>
              )}
              {page === "Create run" && (
                <section className="form">
                  <h2>Define the engineering task</h2>
                  <label>
                    Requirement
                    <textarea
                      rows={6}
                      value={requirement}
                      onChange={(e) => setRequirement(e.target.value)}
                    />
                  </label>
                  <label>
                    Committed local Git repository
                    <input
                      placeholder="C:\\path\\to\\sample"
                      value={repository}
                      onChange={(e) => setRepository(e.target.value)}
                    />
                  </label>
                  <div className="two-col">
                    <label>
                      Model mode
                      <select
                        value={mode}
                        onChange={(e) => {
                          setMode(e.target.value);
                          setFault("none");
                        }}
                      >
                        <option value="live">Live AI · Groq</option>
                        <option value="demo">Reproducible fixture demo</option>
                      </select>
                    </label>
                    <label>
                      Controlled fault
                      <select
                        disabled={mode !== "demo"}
                        value={fault}
                        onChange={(e) => setFault(e.target.value)}
                      >
                        {[
                          "none",
                          "test",
                          "security",
                          "malformed",
                          "provider",
                          "scope",
                          "repeat",
                          "disagree",
                        ].map((f) => (
                          <option key={f}>{f}</option>
                        ))}
                      </select>
                    </label>
                  </div>
                  {mode === "demo" && (
                    <p className="notice">
                      Fixtures support the bundled payments apply_discount task
                      only. Checks still require Docker.
                    </p>
                  )}
                  {mode === "live" && (
                    <label>
                      Independent acceptance profile
                      <select
                        aria-label="Independent acceptance profile"
                        value={acceptanceProfile}
                        onChange={(e) => setAcceptanceProfile(e.target.value)}
                      >
                        <option value="payments_discount">
                          Payments discount · 12 trusted cases
                        </option>
                        <option value="refunds">
                          Refund service · 20 trusted cases
                        </option>
                        <option value="none">
                          Generic repository · human semantic review required
                        </option>
                      </select>
                      <small>
                        Choose the profile matching your sample and requirement.
                        Trusted tests run against both the baseline and
                        candidate.
                      </small>
                    </label>
                  )}
                  <button
                    className="primary"
                    disabled={busy || !repository || !token}
                    onClick={() =>
                      act(async () => {
                        const r = await api("/runs", {
                          requirement,
                          repository,
                          mode,
                          fault,
                          acceptance_profile:
                            mode === "demo"
                              ? "payments_discount"
                              : acceptanceProfile,
                        });
                        setSelected(r.id);
                        setTab("Workflow");
                      })
                    }
                  >
                    Start engineering run
                  </button>
                </section>
              )}
              {page === "Approval center" && (
                <section>
                  <h2>Ready for your decision</h2>
                  <RunList
                    runs={all.filter((r) =>
                      [
                        "AWAITING_HUMAN_APPROVAL",
                        "APPROVED",
                        "REJECTED",
                      ].includes(r.state),
                    )}
                    select={(id) => {
                      setSelected(id);
                      setTab("Human review");
                    }}
                    loading={runs.isLoading}
                  />
                </section>
              )}
              {page === "Settings" && (
                <section className="form">
                  <h2>Local configuration</h2>
                  <p className="muted">
                    Provider credentials and execution settings are configured
                    in the backend environment. Restart the backend after
                    changing them.
                  </p>
                  <label>
                    Human review token
                    <input
                      type="password"
                      value={tokenInput}
                      onChange={(e) => setTokenInput(e.target.value)}
                    />
                  </label>
                  <button
                    disabled={!tokenInput}
                    onClick={() => setToken(tokenInput)}
                  >
                    Connect session
                  </button>
                  <dl>
                    <dt>Provider</dt>
                    <dd>Groq</dd>
                    <dt>Model</dt>
                    <dd>{health.data?.model || "Not configured"}</dd>
                    <dt>Live configuration</dt>
                    <dd>
                      {health.data?.live_configured
                        ? "Configured"
                        : "Missing key or model"}
                    </dd>
                    <dt>Repair budget</dt>
                    <dd>{health.data?.repair_limit ?? "Unknown"}</dd>
                    <dt>Execution</dt>
                    <dd>Docker · network disabled · 256 MB · 1 CPU</dd>
                  </dl>
                </section>
              )}
            </>
          )}
        </div>
        <footer>
          CortexForge <span>Controlled autonomy. Verifiable engineering.</span>
          <span>LOCAL / v0.1</span>
        </footer>
      </main>
    </div>
  );
}
function Metric({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon?: React.ReactNode;
}) {
  return (
    <section className="metric">
      <div>
        {title}
        {icon}
      </div>
      <strong>{value}</strong>
    </section>
  );
}
function RunList({
  runs,
  select,
  loading,
}: {
  runs: Run[];
  select: (id: string) => void;
  loading: boolean;
}) {
  return loading ? (
    <p>Loading runs…</p>
  ) : runs.length === 0 ? (
    <div className="empty">
      <FileCode2 size={32} />
      <h3>No runs here yet</h3>
      <p>Submit a requirement to begin collecting engineering evidence.</p>
    </div>
  ) : (
    <div className="run-list">
      {runs
        .slice()
        .reverse()
        .map((r) => (
          <button key={r.id} onClick={() => select(r.id)}>
            <span className="run-icon">
              <GitBranch size={20} />
            </span>
            <span>
              <strong>{r.requirement}</strong>
              <small>
                {r.id.slice(0, 8)} · <RunMode mode={r.mode} fault={r.fault} /> ·{" "}
                {new Date(r.created).toLocaleString()}
              </small>
            </span>
            <Status value={r.state} />
          </button>
        ))}
    </div>
  );
}

const root = document.getElementById("root");
if (root)
  createRoot(root).render(
    <React.StrictMode>
      <QueryClientProvider client={new QueryClient()}>
        <App />
      </QueryClientProvider>
    </React.StrictMode>,
  );
