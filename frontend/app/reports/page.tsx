
"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type RunStatus = "PASS" | "FAIL" | "HEALED" | "SKIPPED";

interface TestRun {
  id: string;
  test_case_id?: string;
  test_name?: string;
  target_url?: string;
  status?: string;
  started_at?: string;
  finished_at?: string;
  duration_ms?: number;
  healing_count?: number;
  approval_required_count?: number;
  verifications?: Array<{
    status?: string;
    passed?: boolean;
  }>;
}

interface RunsResponse {
  runs: TestRun[];
}

interface HealingRequestsResponse {
  requests: Array<{
    id: string;
    status: "PENDING" | "APPROVED" | "REJECTED";
  }>;
}

function normalizeStatus(value?: string): RunStatus {
  const status = (value || "").toUpperCase();

  if (status === "PASS") return "PASS";
  if (status === "HEALED") return "HEALED";
  if (status === "SKIPPED") return "SKIPPED";

  return "FAIL";
}

function formatDate(value?: string) {
  if (!value) return "—";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    });
}

function formatDuration(value?: number) {
  if (value === undefined || value === null) {
    return "—";
  }

  if (value < 1000) {
    return `${Math.round(value)} ms`;
  }

  return `${(value / 1000).toFixed(2)} s`;
}

function StatusBadge({ status }: { status: RunStatus }) {
  const styles: Record<RunStatus, string> = {
    PASS: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
    HEALED: "border-violet-500/30 bg-violet-500/10 text-violet-300",
    FAIL: "border-red-500/30 bg-red-500/10 text-red-300",
    SKIPPED: "border-slate-500/30 bg-slate-500/10 text-slate-300",
  };

  return (
    <span
      className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${styles[status]}`}
    >
      {status}
    </span>
  );
}

function MetricCard({
  title,
  value,
  subtitle,
  color = "text-white",
}: {
  title: string;
  value: string | number;
  subtitle: string;
  color?: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#111723] p-5">
      <p className="text-sm text-slate-400">{title}</p>

      <h2 className={`mt-3 text-3xl font-bold ${color}`}>
        {value}
      </h2>

      <p className="mt-2 text-xs text-slate-500">
        {subtitle}
      </p>
    </div>
  );
}

export default function ReportsPage() {
  const [runs, setRuns] = useState<TestRun[]>([]);

  const [healingRequests, setHealingRequests] =
    useState<HealingRequestsResponse["requests"]>([]);

  const approvalStats = {
    pending: healingRequests.filter(
      (item) => item.status === "PENDING"
    ).length,
    approved: healingRequests.filter(
      (item) => item.status === "APPROVED"
    ).length,
    rejected: healingRequests.filter(
      (item) => item.status === "REJECTED"
    ).length,
  };
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("ALL");

  const loadReports = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const [response, healingResponse] = await Promise.all([
        api<RunsResponse>("/api/runs"),
        api<HealingRequestsResponse>("/api/healing/requests"),
      ]);

      if (
        !Array.isArray(response.runs) ||
        !Array.isArray(healingResponse.requests)
      ) {
        throw new Error("Invalid reports API response.");
      }

      setRuns(response.runs);
      setHealingRequests(healingResponse.requests);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load execution reports."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadReports();
  }, [loadReports]);

  const stats = useMemo(() => {
    const total = runs.length;

    const passed = runs.filter(
      (run) => normalizeStatus(run.status) === "PASS"
    ).length;

    const healed = runs.filter(
      (run) => normalizeStatus(run.status) === "HEALED"
    ).length;

    const failed = runs.filter(
      (run) => normalizeStatus(run.status) === "FAIL"
    ).length;

    const skipped = runs.filter(
      (run) => normalizeStatus(run.status) === "SKIPPED"
    ).length;

    const completed = passed + healed + failed;

    const passRate = completed
      ? (((passed + healed) / completed) * 100).toFixed(1)
      : "0.0";

    const healingEvents = runs.reduce(
      (sum, run) => sum + (Number(run.healing_count) || 0),
      0
    );



    const durations = runs
      .map((run) => run.duration_ms)
      .filter(
        (value): value is number =>
          typeof value === "number" &&
          Number.isFinite(value) &&
          value >= 0
      );

    const averageDuration = durations.length
      ? durations.reduce((sum, value) => sum + value, 0) /
        durations.length
      : undefined;

    return {
      total,
      passed,
      healed,
      failed,
      skipped,
      completed,
      passRate,
      healingEvents,
      averageDuration,
    };
  }, [runs]);

  const filteredRuns = useMemo(() => {
    const selected = runs.filter(
      (run) =>
        filter === "ALL" ||
        normalizeStatus(run.status) === filter
    );

    return [...selected].sort((a, b) => {
      const dateA = Date.parse(a.started_at || "") || 0;
      const dateB = Date.parse(b.started_at || "") || 0;

      return dateB - dateA;
    });
  }, [runs, filter]);

  return (
    <main className="min-h-screen bg-[#080B12] px-5 py-8 text-white md:px-10">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-violet-400">
              Test AI / Analytics
            </p>

            <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
              Execution Reports
            </h1>

            <p className="mt-2 text-sm text-slate-400">
              Live execution statistics, verification outcomes,
              and self-healing activity.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link
              href="/runs"
              className="rounded-xl border border-white/10 bg-[#151B28] px-5 py-3 text-sm font-medium hover:bg-[#20283A]"
            >
              Run History
            </Link>

            <button
              onClick={() => void loadReports()}
              disabled={loading}
              className="rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold hover:bg-violet-500 disabled:opacity-50"
            >
              {loading ? "Loading..." : "Refresh Reports"}
            </button>
          </div>
        </div>

        {error && (
          <div
            role="alert"
            className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300"
          >
            {error}
          </div>
        )}

        {loading && runs.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-[#111723] p-12 text-center text-slate-400">
            Loading execution reports...
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                title="Total Executions"
                value={stats.total}
                subtitle="Recorded test executions"
              />

              <MetricCard
                title="Successful Executions"
                value={stats.passed + stats.healed}
                subtitle="Passed and healed runs"
                color="text-emerald-400"
              />

              <MetricCard
                title="Failed Executions"
                value={stats.failed}
                subtitle="Runs with failed status"
                color="text-red-400"
              />

              <MetricCard
                title="Pass Rate"
                value={`${stats.passRate}%`}
                subtitle="Excludes skipped executions"
                color="text-violet-400"
              />
            </div>

            <div className="mt-5 rounded-2xl border border-violet-500/20 bg-[#111723] p-5">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="font-semibold text-white">
                    AI Healing Recommendations
                  </h2>
                  <p className="mt-1 text-sm text-slate-400">
                    Review-required suggestions from recorded test executions
                  </p>
                </div>
                <div className="text-right">
                  <div className="flex flex-wrap gap-5">
                    <div>
                      <p className="text-3xl font-bold text-amber-300">
                        {approvalStats.pending}
                      </p>
                      <p className="text-xs text-slate-400">Pending</p>
                    </div>
                    <div>
                      <p className="text-3xl font-bold text-emerald-300">
                        {approvalStats.approved}
                      </p>
                      <p className="text-xs text-slate-400">Approved</p>
                    </div>
                    <div>
                      <p className="text-3xl font-bold text-red-300">
                        {approvalStats.rejected}
                      </p>
                      <p className="text-xs text-slate-400">Rejected</p>
                    </div>
                  </div>
                </div>
                <a
                  href="/healing"
                  className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-500"
                >
                  Open Healing Dashboard
                </a>
              </div>
            </div>

            <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-3">
              <section className="rounded-2xl border border-white/10 bg-[#111723] p-6 lg:col-span-2">
                <h2 className="text-lg font-semibold">
                  Execution Outcomes
                </h2>

                <p className="mt-1 text-sm text-slate-400">
                  Breakdown of stored test run statuses
                </p>

                {stats.total > 0 ? (
                  <>
                    <div className="mt-8 flex h-4 overflow-hidden rounded-full bg-slate-800">
                      <div
                        className="bg-emerald-500"
                        style={{
                          width: `${(stats.passed / stats.total) * 100}%`,
                        }}
                      />
                      <div
                        className="bg-violet-500"
                        style={{
                          width: `${(stats.healed / stats.total) * 100}%`,
                        }}
                      />
                      <div
                        className="bg-red-500"
                        style={{
                          width: `${(stats.failed / stats.total) * 100}%`,
                        }}
                      />
                      <div
                        className="bg-slate-500"
                        style={{
                          width: `${(stats.skipped / stats.total) * 100}%`,
                        }}
                      />
                    </div>

                    <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
                      {[
                        ["Passed", stats.passed, "text-emerald-400"],
                        ["Healed", stats.healed, "text-violet-400"],
                        ["Failed", stats.failed, "text-red-400"],
                        ["Skipped", stats.skipped, "text-slate-300"],
                      ].map(([label, value, color]) => (
                        <div key={String(label)}>
                          <p className="text-xs text-slate-400">
                            {label}
                          </p>
                          <p className={`mt-1 text-xl font-bold ${color}`}>
                            {value}
                          </p>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="mt-8 text-sm text-slate-500">
                    No execution results are available yet.
                  </p>
                )}
              </section>

              <section className="rounded-2xl border border-white/10 bg-[#111723] p-6">
                <h2 className="text-lg font-semibold">
                  Execution Insights
                </h2>

                <div className="mt-6 space-y-5">
                  <div>
                    <p className="text-sm text-slate-400">
                      Self-Healing Events
                    </p>
                    <p className="mt-1 text-2xl font-bold text-violet-400">
                      {stats.healingEvents}
                    </p>
                  </div>

                  <div className="border-t border-white/10 pt-5">
                    <p className="text-sm text-slate-400">
                      Average Run Duration
                    </p>
                    <p className="mt-1 text-2xl font-bold">
                      {formatDuration(stats.averageDuration)}
                    </p>
                  </div>

                  <div className="border-t border-white/10 pt-5">
                    <p className="text-sm text-slate-400">
                      Completed Executions
                    </p>
                    <p className="mt-1 text-2xl font-bold">
                      {stats.completed}
                    </p>
                  </div>
                </div>
              </section>
            </div>

            <section className="mt-6 overflow-hidden rounded-2xl border border-white/10 bg-[#111723]">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 p-6">
                <div>
                  <h2 className="text-lg font-semibold">
                    Execution History
                  </h2>
                  <p className="mt-1 text-sm text-slate-400">
                    Select a run to view its detailed report.
                  </p>
                </div>

                <select
                  aria-label="Filter execution status"
                  value={filter}
                  onChange={(event) => setFilter(event.target.value)}
                  className="rounded-xl border border-white/10 bg-[#0B101A] px-4 py-2 text-sm text-white outline-none focus:border-violet-500"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="PASS">Passed</option>
                  <option value="HEALED">Healed</option>
                  <option value="FAIL">Failed</option>
                  <option value="SKIPPED">Skipped</option>
                </select>
              </div>

              {filteredRuns.length === 0 ? (
                <div className="px-6 py-16 text-center">
                  <h3 className="font-semibold">
                    No execution reports found
                  </h3>
                  <p className="mt-2 text-sm text-slate-400">
                    {filter === "ALL"
                      ? "Run a saved test to generate execution data."
                      : "No executions match the selected status."}
                  </p>

                  <Link
                    href="/tests"
                    className="mt-5 inline-block rounded-xl bg-violet-600 px-5 py-3 text-sm font-semibold hover:bg-violet-500"
                  >
                    View Test Cases
                  </Link>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[760px] text-left text-sm">
                    <thead className="bg-white/[0.03] text-xs uppercase tracking-wide text-slate-400">
                      <tr>
                        <th className="px-6 py-4">Test Case</th>
                        <th className="px-6 py-4">Status</th>
                        <th className="px-6 py-4">Executed At</th>
                        <th className="px-6 py-4">Duration</th>
                        <th className="px-6 py-4">Healing</th>
                        <th className="px-6 py-4">Report</th>
                      </tr>
                    </thead>

                    <tbody>
                      {filteredRuns.map((run) => (
                        <tr
                          key={run.id}
                          className="border-t border-white/5 hover:bg-white/[0.03]"
                        >
                          <td className="px-6 py-4">
                            <p className="font-medium">
                              {run.test_name || "Unnamed Test"}
                            </p>
                            <p className="mt-1 max-w-[230px] truncate text-xs text-slate-500">
                              {run.target_url || "No target URL"}
                            </p>
                          </td>

                          <td className="px-6 py-4">
                            <StatusBadge
                              status={normalizeStatus(run.status)}
                            />
                          </td>

                          <td className="px-6 py-4 text-slate-300">
                            {formatDate(run.started_at)}
                          </td>

                          <td className="px-6 py-4 text-slate-300">
                            {formatDuration(run.duration_ms)}
                          </td>

                          <td className="px-6 py-4 text-violet-300">
                            {run.healing_count ?? 0}
                          </td>

                          <td className="px-6 py-4">
                            <Link
                              href={`/runs/${encodeURIComponent(run.id)}`}
                              className="font-semibold text-violet-400 hover:text-violet-300"
                            >
                              View Details
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}
