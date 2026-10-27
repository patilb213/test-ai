"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api } from "../../lib/api";


type RunStatus =
  | "PASS"
  | "HEALED"
  | "FAIL"
  | "SKIPPED";


interface TestRun {
  id: string;
  test_case_id: string;
  test_name?: string;
  target_url?: string;
  status: RunStatus;
  started_at?: string;
  finished_at?: string;
  duration_ms?: number;
  healing_count?: number;
}


function statusClass(status: string) {
  if (status === "PASS") {
    return "pass";
  }

  if (status === "HEALED") {
    return "healed";
  }

  if (status === "FAIL") {
    return "fail";
  }

  return "neutral";
}


function formatDate(value?: string) {
  if (!value) return "—";

  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}


function formatDuration(ms?: number) {
  if (ms === undefined) {
    return "—";
  }

  if (ms < 1000) {
    return `${Math.round(ms)} ms`;
  }

  return `${(ms / 1000).toFixed(2)} s`;
}


export default function RunsPage() {
  const [runs, setRuns] =
    useState<TestRun[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  async function loadRuns() {
    try {
      setLoading(true);
      setError("");

      const response =
        await api("/api/runs");

      setRuns(
        response.runs || []
      );

    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load runs."
      );

    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadRuns();
  }, []);


  const total =
    runs.length;

  const passed =
    runs.filter(
      (run) =>
        run.status === "PASS"
    ).length;

  const healed =
    runs.filter(
      (run) =>
        run.status === "HEALED"
    ).length;

  const failed =
    runs.filter(
      (run) =>
        run.status === "FAIL"
    ).length;


  return (
    <main className="page">

      <header className="header">

        <div>

          <Link
            href="/dashboard"
            className="back"
          >
            ← Dashboard
          </Link>

          <h1>
            Test Runs
          </h1>

          <p>
            Execution history, verification
            results, self-healing and evidence.
          </p>

        </div>

        <button
          className="refresh"
          onClick={loadRuns}
        >
          Refresh
        </button>

      </header>


      <section className="stats">

        <Stat
          label="Total Runs"
          value={total}
        />

        <Stat
          label="Passed"
          value={passed}
        />

        <Stat
          label="Healed"
          value={healed}
        />

        <Stat
          label="Failed"
          value={failed}
        />

      </section>


      {loading ? (

        <div className="card">
          Loading test runs...
        </div>

      ) : error ? (

        <div className="card error">
          {error}
        </div>

      ) : runs.length === 0 ? (

        <div className="card empty">

          <h2>
            No test runs yet
          </h2>

          <p>
            Run a saved test case to see
            execution results here.
          </p>

          <Link
            href="/tests"
            className="primary"
          >
            Open Test Cases
          </Link>

        </div>

      ) : (

        <div className="run-list">

          {runs.map(
            (run) => (

              <Link
                key={run.id}
                href={`/runs/${run.id}`}
                className="run-card"
              >

                <div className="run-main">

                  <div>

                    <h2>
                      {run.test_name ||
                        "Unnamed Test"}
                    </h2>

                    <p>
                      {run.target_url ||
                        "Target URL unavailable"}
                    </p>

                  </div>

                  <span
                    className={`status ${statusClass(
                      run.status
                    )}`}
                  >
                    {run.status}
                  </span>

                </div>


                <div className="run-meta">

                  <span>
                    {formatDate(
                      run.started_at
                    )}
                  </span>

                  <span>
                    Duration:{" "}
                    {formatDuration(
                      run.duration_ms
                    )}
                  </span>

                  <span>
                    Healing:{" "}
                    {run.healing_count || 0}
                  </span>

                  <span>
                    View Details →
                  </span>

                </div>

              </Link>

            )
          )}

        </div>

      )}


      <style jsx>{styles}</style>

    </main>
  );
}


function Stat({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="stat">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


const styles = `
.page {
  min-height: 100vh;
  padding: 32px;
  background:
    radial-gradient(
      circle at 80% 0%,
      rgba(139, 124, 246, 0.08),
      transparent 30%
    ),
    #07090d;
  color: #f5f7fa;
}

.header {
  max-width: 1200px;
  margin: 0 auto 28px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 20px;
}

.back {
  color: #8992a3;
  font-size: 14px;
}

.header h1 {
  margin: 10px 0 5px;
  font-size: 32px;
}

.header p {
  margin: 0;
  color: #8992a3;
}

.refresh,
.primary {
  min-height: 42px;
  padding: 0 16px;
  border-radius: 9px;
  border: 1px solid #222936;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.refresh {
  background: #121720;
  color: #f5f7fa;
}

.primary {
  background: #8b7cf6;
  color: white;
  border-color: transparent;
}

.stats {
  max-width: 1200px;
  margin: 0 auto 22px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat {
  background: #0d1117;
  border: 1px solid #222936;
  border-radius: 12px;
  padding: 18px;
}

.stat span {
  display: block;
  color: #8992a3;
  font-size: 12px;
  margin-bottom: 8px;
}

.stat strong {
  font-size: 25px;
}

.card {
  max-width: 1200px;
  margin: 0 auto;
  padding: 25px;
  background: #0d1117;
  border: 1px solid #222936;
  border-radius: 14px;
}

.card h2 {
  margin-top: 0;
}

.card p {
  color: #8992a3;
}

.error {
  color: #f87171;
}

.empty {
  text-align: center;
}

.run-list {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.run-card {
  padding: 19px;
  background: #0d1117;
  border: 1px solid #222936;
  border-radius: 12px;
  transition: 0.15s ease;
}

.run-card:hover {
  border-color: #8b7cf6;
  transform: translateY(-1px);
}

.run-main {
  display: flex;
  justify-content: space-between;
  gap: 15px;
}

.run-main h2 {
  margin: 0;
  font-size: 16px;
}

.run-main p {
  margin: 7px 0 0;
  color: #8992a3;
  font-size: 13px;
  word-break: break-all;
}

.status {
  align-self: flex-start;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
}

.status.pass {
  color: #35d399;
  background: rgba(53, 211, 153, 0.1);
}

.status.healed {
  color: #f5b84b;
  background: rgba(245, 184, 75, 0.1);
}

.status.fail {
  color: #f87171;
  background: rgba(248, 113, 113, 0.1);
}

.status.neutral {
  color: #8992a3;
  background: rgba(137, 146, 163, 0.1);
}

.run-meta {
  display: flex;
  gap: 20px;
  margin-top: 15px;
  padding-top: 13px;
  border-top: 1px solid #222936;
  color: #8992a3;
  font-size: 12px;
  flex-wrap: wrap;
}

@media (max-width: 700px) {
  .page {
    padding: 18px;
  }

  .header {
    flex-direction: column;
    align-items: stretch;
  }

  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
}
`;