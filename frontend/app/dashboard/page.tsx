"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { api } from "../../lib/api";

interface DashboardStats {
  total_projects: number;
  total_tests: number;
  total_runs: number;
  passed_runs: number;
  healed_runs: number;
  failed_runs: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    total_projects: 0,
    total_tests: 0,
    total_runs: 0,
    passed_runs: 0,
    healed_runs: 0,
    failed_runs: 0,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      setLoading(true);
      setError("");

      const data = await api("/api/dashboard/stats");

      setStats(data);
    } catch (err) {
      console.error("Dashboard error:", err);
      setError("Unable to load dashboard statistics.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#07090d",
        color: "#f5f7fa",
        display: "flex",
      }}
    >
      {/* ================================================= */}
      {/* SIDEBAR */}
      {/* ================================================= */}

      <aside
        style={{
          width: "240px",
          minHeight: "100vh",
          background: "#0d1117",
          borderRight: "1px solid #222936",
          padding: "24px 16px",
          position: "fixed",
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        {/* Logo */}
        <div
          style={{
            padding: "8px 12px 28px",
            borderBottom: "1px solid #222936",
            marginBottom: "20px",
          }}
        >
          <div
            style={{
              fontSize: "24px",
              fontWeight: 700,
              letterSpacing: "-0.5px",
            }}
          >
            Test AI
          </div>

          <div
            style={{
              marginTop: "5px",
              fontSize: "12px",
              color: "#8992a3",
            }}
          >
            Smart Testing Platform
          </div>
        </div>

        {/* Navigation */}
        <nav
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "6px",
          }}
        >
          <Link
            href="/dashboard"
            style={{
              padding: "12px 14px",
              borderRadius: "9px",
              background: "#171d29",
              color: "#ffffff",
              fontSize: "14px",
              fontWeight: 600,
            }}
          >
            Dashboard
          </Link>

          <Link
            href="/projects"
            style={{
              padding: "12px 14px",
              borderRadius: "9px",
              color: "#aab2c0",
              fontSize: "14px",
            }}
          >
            Projects
          </Link>

          <Link
            href="/recorder"
            style={{
              padding: "12px 14px",
              borderRadius: "9px",
              color: "#aab2c0",
              fontSize: "14px",
            }}
          >
            Recorder
          </Link>

          <Link
            href="/tests"
            style={{
              padding: "12px 14px",
              borderRadius: "9px",
              color: "#aab2c0",
              fontSize: "14px",
            }}
          >
            Tests
          </Link>

          <Link
            href="/runs"
            style={{
              padding: "12px 14px",
              borderRadius: "9px",
              color: "#aab2c0",
              fontSize: "14px",
            }}
          >
            Runs
          </Link>

          <Link
            href="/reports"
            style={{
              padding: "12px 14px",
              borderRadius: "9px",
              color: "#aab2c0",
              fontSize: "14px",
            }}
          >
            Reports
          </Link>
        </nav>

        {/* Bottom section */}
        <div
          style={{
            position: "absolute",
            bottom: "24px",
            left: "16px",
            right: "16px",
            padding: "14px",
            borderRadius: "10px",
            background: "#121720",
            border: "1px solid #222936",
          }}
        >
          <div
            style={{
              fontSize: "12px",
              color: "#8992a3",
            }}
          >
            Test AI
          </div>

          <div
            style={{
              marginTop: "4px",
              fontSize: "13px",
              color: "#d7dce5",
            }}
          >
            AI-assisted testing
          </div>
        </div>
      </aside>

      {/* ================================================= */}
      {/* MAIN CONTENT */}
      {/* ================================================= */}

      <main
        style={{
          marginLeft: "240px",
          width: "calc(100% - 240px)",
          padding: "48px",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "38px",
          }}
        >
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: "40px",
                fontWeight: 700,
                letterSpacing: "-1px",
              }}
            >
              Test AI Dashboard
            </h1>

            <p
              style={{
                marginTop: "10px",
                marginBottom: 0,
                color: "#8992a3",
                fontSize: "16px",
              }}
            >
              Overview of your testing activity
            </p>
          </div>

          <Link
            href="/projects"
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "11px 18px",
              borderRadius: "9px",
              background: "#8b7cf6",
              color: "#ffffff",
              fontSize: "14px",
              fontWeight: 600,
            }}
          >
            Open Projects
          </Link>
        </div>

        {/* Error */}
        {error && (
          <div
            style={{
              marginBottom: "24px",
              padding: "14px 16px",
              borderRadius: "10px",
              border: "1px solid rgba(248,113,113,0.35)",
              background: "rgba(248,113,113,0.08)",
              color: "#f87171",
            }}
          >
            {error}
          </div>
        )}

        {/* ================================================= */}
        {/* STATISTICS */}
        {/* ================================================= */}

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: "22px",
          }}
        >
          <StatCard
            title="Total Projects"
            value={loading ? "..." : stats.total_projects}
          />

          <StatCard
            title="Total Tests"
            value={loading ? "..." : stats.total_tests}
          />

          <StatCard
            title="Total Runs"
            value={loading ? "..." : stats.total_runs}
          />

          <StatCard
            title="Passed Runs"
            value={loading ? "..." : stats.passed_runs}
          />

          <StatCard
            title="Healed Runs"
            value={loading ? "..." : stats.healed_runs}
          />

          <StatCard
            title="Failed Runs"
            value={loading ? "..." : stats.failed_runs}
          />
        </div>

        {/* ================================================= */}
        {/* QUICK ACTIONS */}
        {/* ================================================= */}

        <section
          style={{
            marginTop: "42px",
          }}
        >
          <h2
            style={{
              margin: "0 0 18px",
              fontSize: "21px",
              fontWeight: 600,
            }}
          >
            Quick Actions
          </h2>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
              gap: "18px",
            }}
          >
            <QuickAction
              href="/projects"
              title="Projects"
              description="Create and manage your testing projects."
            />

            <QuickAction
              href="/recorder"
              title="Record a Test"
              description="Record real browser interactions without writing code."
            />

            <QuickAction
              href="/tests"
              title="Test Cases"
              description="View recorded tests and define expected results."
            />

            <QuickAction
              href="/runs"
              title="Test Runs"
              description="Review PASS, HEALED and FAIL executions."
            />

            <QuickAction
              href="/reports"
              title="Reports"
              description="Review testing results and execution evidence."
            />
          </div>
        </section>

        {/* ================================================= */}
        {/* REFRESH */}
        {/* ================================================= */}

        <button
          onClick={loadDashboard}
          disabled={loading}
          style={{
            marginTop: "32px",
            padding: "11px 18px",
            borderRadius: "9px",
            border: "1px solid #222936",
            background: "#121720",
            color: "#f5f7fa",
            fontSize: "14px",
            fontWeight: 500,
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? "Refreshing..." : "Refresh Dashboard"}
        </button>
      </main>
    </div>
  );
}


/* ================================================= */
/* STAT CARD */
/* ================================================= */

function StatCard({
  title,
  value,
}: {
  title: string;
  value: string | number;
}) {
  return (
    <div
      style={{
        minHeight: "150px",
        padding: "26px",
        borderRadius: "14px",
        background: "#0d1117",
        border: "1px solid #222936",
      }}
    >
      <div
        style={{
          color: "#8992a3",
          fontSize: "14px",
          marginBottom: "22px",
        }}
      >
        {title}
      </div>

      <div
        style={{
          fontSize: "38px",
          fontWeight: 600,
          color: "#f5f7fa",
        }}
      >
        {value}
      </div>
    </div>
  );
}


/* ================================================= */
/* QUICK ACTION */
/* ================================================= */

function QuickAction({
  href,
  title,
  description,
}: {
  href: string;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      style={{
        display: "block",
        padding: "20px",
        borderRadius: "12px",
        background: "#0d1117",
        border: "1px solid #222936",
        transition: "border-color 0.2s ease",
      }}
    >
      <div
        style={{
          fontSize: "16px",
          fontWeight: 600,
          color: "#f5f7fa",
          marginBottom: "8px",
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: "13px",
          lineHeight: 1.6,
          color: "#8992a3",
        }}
      >
        {description}
      </div>
    </Link>
  );
}