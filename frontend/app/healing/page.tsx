
"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED";
type FilterStatus = "ALL" | ApprovalStatus;

interface HealingRequest {
  id: string;
  run_id: string;
  test_case_id?: string | null;
  test_name?: string | null;
  original_locator?: string | null;
  replacement_locator?: string | null;
  confidence?: number | null;
  ai_model?: string | null;
  ai_similarity?: number | null;
  ai_margin?: number | null;
  healing_decision?: string | null;
  healing_decision_reason?: string | null;
  reason?: string | null;
  source?: string | null;
  status: ApprovalStatus;
  created_at?: string | null;
  decided_at?: string | null;
  reviewed_by?: string | null;
}

interface RequestsResponse {
  requests: HealingRequest[];
}

function formatDate(value?: string | null): string {
  if (!value) return "Not available";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "Not available"
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

function formatConfidence(value?: number | null): string {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "Not available";
  }

  return `${(value * 100).toFixed(1)}%`;
}

function statusStyles(status: ApprovalStatus): string {
  if (status === "APPROVED") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
  }

  if (status === "REJECTED") {
    return "border-rose-500/30 bg-rose-500/10 text-rose-300";
  }

  return "border-amber-500/30 bg-amber-500/10 text-amber-300";
}

function SummaryCard({
  title,
  count,
  color,
}: {
  title: string;
  count: number;
  color: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-[#111A2B] p-6">
      <p className="text-sm text-slate-400">{title}</p>
      <p className={`mt-3 text-4xl font-bold ${color}`}>
        {count}
      </p>
    </div>
  );
}


// TEST_AI_AI_HEALING_UI_V1
function AIHealingDetails({
  request,
}: {
  request: HealingRequest;
}) {
  if (!request.ai_model) return null;

  return (
    <div className="mt-4 rounded-xl border border-violet-500/30 bg-violet-500/10 p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-sm font-semibold text-violet-200">
          AI Semantic Healing
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs text-slate-400">AI Model</p>
          <p className="break-all text-sm text-white">
            {request.ai_model}
          </p>
        </div>

        <div>
          <p className="text-xs text-slate-400">
            Semantic Similarity
          </p>
          <p className="text-lg font-semibold text-violet-200">
            {formatConfidence(request.ai_similarity)}
          </p>
        </div>

        <div>
          <p className="text-xs text-slate-400">
            Similarity Margin
          </p>
          <p className="text-sm text-white">
            {formatConfidence(request.ai_margin)}
          </p>
        </div>

        <div>
          <p className="text-xs text-slate-400">
            Recommendation
          </p>
          <p className="text-sm text-amber-300">
            {request.healing_decision || "Review required"}
          </p>
        </div>
      </div>

      <p className="mt-3 text-xs text-slate-400">
        AI similarity is a matching signal, not a probability
        of correctness. Approval does not automatically execute
        a replacement locator.
      </p>
    </div>
  );
}

export default function HealingPage() {
  const [requests, setRequests] = useState<HealingRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterStatus>("ALL");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadRequests = useCallback(async (silent = false) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    setError("");

    try {
      const response = await api<RequestsResponse>(
        "/api/healing/requests",
        { cache: "no-store" }
      );

      if (!Array.isArray(response.requests)) {
        throw new Error("Invalid healing API response.");
      }

      setRequests(response.requests);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load healing requests."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadRequests();
  }, [loadRequests]);

  async function reviewRequest(
    request: HealingRequest,
    decision: "approve" | "reject"
  ) {
    if (request.status !== "PENDING") return;

    const confirmed = window.confirm(
      `Are you sure you want to ${decision} this suggestion?\n\n` +
        `Test: ${request.test_name || "Unnamed test"}\n` +
        `Original: ${request.original_locator || "Unavailable"}\n` +
        `Replacement: ${request.replacement_locator || "Unavailable"}\n\n` +
        "This records a decision. It does not execute the test."
    );

    if (!confirmed) return;

    setBusyId(request.id);
    setError("");
    setMessage("");

    try {
      await api(
        `/api/healing/requests/${encodeURIComponent(request.id)}/${decision}`,
        {
          method: "POST",
        }
      );

      setMessage(
        `Suggestion ${
          decision === "approve" ? "approved" : "rejected"
        } successfully.`
      );

      await loadRequests(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to save your decision."
      );
    } finally {
      setBusyId(null);
    }
  }

  const stats = useMemo(() => {
    return {
      pending: requests.filter((r) => r.status === "PENDING").length,
      approved: requests.filter((r) => r.status === "APPROVED").length,
      rejected: requests.filter((r) => r.status === "REJECTED").length,
    };
  }, [requests]);

  const visibleRequests = useMemo(
    () =>
      requests.filter(
        (request) =>
          filter === "ALL" || request.status === filter
      ),
    [requests, filter]
  );

  return (
    <main className="min-h-screen bg-[#080D19] px-5 py-8 text-slate-100 md:px-10">
      <div className="mx-auto max-w-7xl">
        <header className="mb-9 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-sky-400">
              Test AI / Self-Healing
            </p>

            <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
              Healing Approvals
            </h1>

            <p className="mt-3 max-w-2xl text-sm text-slate-400">
              Review locator suggestions generated by your test
              executions. Decisions are recorded against your
              authenticated account.
            </p>
          </div>

          <div className="flex gap-3">
            <Link
              href="/dashboard"
              className="rounded-xl border border-slate-700 px-4 py-3 text-sm hover:bg-slate-800"
            >
              Dashboard
            </Link>

            <button
              type="button"
              onClick={() => void loadRequests(true)}
              disabled={loading || refreshing}
              className="rounded-xl bg-sky-500 px-5 py-3 text-sm font-semibold text-slate-950 hover:bg-sky-400 disabled:opacity-50"
            >
              {refreshing ? "Refreshing..." : "Refresh"}
            </button>
          </div>
        </header>

        {error && (
          <div
            role="alert"
            className="mb-5 rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300"
          >
            {error}
          </div>
        )}

        {message && (
          <div
            role="status"
            className="mb-5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-300"
          >
            {message}
          </div>
        )}

        <section className="mb-8 grid gap-4 sm:grid-cols-3">
          <SummaryCard
            title="Pending Review"
            count={stats.pending}
            color="text-amber-400"
          />
          <SummaryCard
            title="Approved"
            count={stats.approved}
            color="text-emerald-400"
          />
          <SummaryCard
            title="Rejected"
            count={stats.rejected}
            color="text-rose-400"
          />
        </section>

        <section className="overflow-hidden rounded-2xl border border-slate-800 bg-[#111A2B]">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 p-5">
            <div>
              <h2 className="text-lg font-semibold">
                Approval Queue
              </h2>
              <p className="mt-1 text-xs text-slate-400">
                Suggestions from your authorized test runs
              </p>
            </div>

            <select
              aria-label="Filter approval requests"
              value={filter}
              onChange={(event) =>
                setFilter(event.target.value as FilterStatus)
              }
              className="rounded-xl border border-slate-700 bg-[#080D19] px-4 py-2 text-sm text-white"
            >
              <option value="ALL">All requests</option>
              <option value="PENDING">Pending</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>

          {loading ? (
            <div className="p-12 text-center text-slate-400">
              Loading healing requests...
            </div>
          ) : visibleRequests.length === 0 ? (
            <div className="p-12 text-center">
              <h3 className="text-lg font-semibold">
                No healing requests found
              </h3>
              <p className="mx-auto mt-3 max-w-md text-sm text-slate-400">
                Requests appear when a real test execution
                discovers a locator replacement that needs review.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {visibleRequests.map((request) => (
                <article key={request.id} className="p-5 md:p-6">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <h3 className="font-semibold">
                        {request.test_name || "Unnamed test"}
                      </h3>

                      <p className="mt-2 break-all text-xs text-slate-500">
                        Run ID: {request.run_id}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">
                        Created: {formatDate(request.created_at)}
                      </p>
                    </div>

                    <span
                      className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusStyles(
                        request.status
                      )}`}
                    >
                      {request.status}
                    </span>
                  </div>

                  <div className="mt-5 grid gap-4 md:grid-cols-2">
                    <div className="min-w-0 rounded-xl border border-slate-800 bg-[#080D19] p-4">
                      <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">
                        Original Locator
                      </p>
                      <code className="break-all text-sm text-rose-300">
                        {request.original_locator || "Not available"}
                      </code>
                    </div>

                    <div className="min-w-0 rounded-xl border border-slate-800 bg-[#080D19] p-4">
                      <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">
                        Suggested Replacement
                      </p>
                      <code className="break-all text-sm text-emerald-300">
                        {request.replacement_locator || "Not available"}
                      </code>
                    </div>
                  </div>

                  <div className="mt-5">
                    <p className="text-xs text-slate-500">
                      Heuristic Confidence
                    </p>
                    <p className="mt-1 text-xl font-semibold text-sky-400">
                      {formatConfidence(request.confidence)}
                    </p>
                  </div>

                  <AIHealingDetails request={request} />

                  {request.reason && (
                    <p className="mt-4 rounded-xl bg-slate-800/50 p-4 text-sm text-slate-300">
                      {request.reason}
                    </p>
                  )}

                  {request.reviewed_by && (
                    <p className="mt-4 text-xs text-slate-400">
                      Reviewed by {request.reviewed_by}
                      {request.decided_at
                        ? ` · ${formatDate(request.decided_at)}`
                        : ""}
                    </p>
                  )}

                  {request.status === "PENDING" && (
                    <div className="mt-6 flex flex-wrap gap-3">
                      <button
                        type="button"
                        disabled={busyId !== null}
                        onClick={() =>
                          void reviewRequest(request, "approve")
                        }
                        className="rounded-xl bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
                      >
                        {busyId === request.id
                          ? "Saving..."
                          : "Approve"}
                      </button>

                      <button
                        type="button"
                        disabled={busyId !== null}
                        onClick={() =>
                          void reviewRequest(request, "reject")
                        }
                        className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-5 py-2.5 text-sm font-semibold text-rose-300 hover:bg-rose-500/20 disabled:opacity-50"
                      >
                        Reject
                      </button>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
