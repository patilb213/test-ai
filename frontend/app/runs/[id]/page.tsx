
"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { CSSProperties } from "react";
import { api, fetchEvidenceBlob } from "@/lib/api";

type Status = "PASS" | "FAIL" | "HEALED" | "SKIPPED" | string;

type Healing = {
  healed?: boolean;
  original_locator?: string | Record<string, unknown>;
  replacement_locator?: string | Record<string, unknown>;
  confidence?: number;
  reason?: string;
};

type Step = {
  step?: number;
  action?: string;
  status?: Status;
  url?: string;
  value?: string;
  message?: string;
  error?: string;
  screenshot?: string;
  healing?: Healing;
  duration_ms?: number;
};

type Verification = {
  type?: string;
  condition?: string;
  expected?: string;
  actual?: string;
  value?: string;
  matched?: boolean;
  status?: Status;
  message?: string;
  error?: string;
  screenshot?: string;
  healing?: Healing;
};

type Evidence = {
  url?: string;
  name?: string;
  type?: string;
};

type Run = {
  id?: string;
  test_run_id?: string;
  test_case_id?: string;
  test_name?: string;
  target_url?: string;
  test?: {
    name?: string;
    target_url?: string;
  };
  status?: Status;
  message?: string;
  steps?: Step[];
  verifications?: Verification[];
  evidence?: Evidence[];
  screenshot?: string;
  comparison_summary?: {
    total?: number;
    executed?: number;
    passed?: number;
    failed?: number;
    skipped?: number;
  };
  healed?: boolean;
  healing_count?: number;
  healing_details?: Healing[];
  duration_ms?: number;
  started_at?: string;
  finished_at?: string;
  error?: string;
};

const API =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

const COLORS = {
  background: "#07090d",
  card: "#0d1117",
  surface: "#121720",
  border: "#222936",
  text: "#f5f7fa",
  muted: "#8992a3",
  purple: "#8b7cf6",
  green: "#35d399",
  red: "#f87171",
  yellow: "#f5b84b",
};

function statusColor(status?: string) {
  switch (status) {
    case "PASS":
      return COLORS.green;
    case "FAIL":
      return COLORS.red;
    case "HEALED":
      return COLORS.yellow;
    default:
      return COLORS.muted;
  }
}

function statusIcon(status?: string) {
  switch (status) {
    case "PASS":
      return "✓";
    case "FAIL":
      return "✕";
    case "HEALED":
      return "↻";
    default:
      return "•";
  }
}

function formatAction(value?: string) {
  if (!value) return "Unknown";

  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value?: string) {
  if (!value) return "—";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? value
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

function formatDuration(ms?: number) {
  if (ms === undefined || ms === null) return "—";

  return ms < 1000
    ? `${Math.round(ms)} ms`
    : `${(ms / 1000).toFixed(2)} s`;
}

function formatLocator(
  value?: string | Record<string, unknown>
) {
  if (!value) return "Unavailable";

  return typeof value === "string"
    ? value
    : JSON.stringify(value);
}


function useEvidenceObjectUrl(
  path?: string,
  runId?: string
) {
  const [url, setUrl] = useState("");

  useEffect(() => {
    if (!path || !runId) {
      setUrl("");
      return;
    }

    let cancelled = false;
    let objectUrl = "";

    setUrl("");

    fetchEvidenceBlob(runId, path)
      .then((blob) => {
        if (cancelled) return;

        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch((error) => {
        if (!cancelled) {
          console.warn(
            "Screenshot unavailable:",
            error
          );
        }
      });

    return () => {
      cancelled = true;

      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [path, runId]);

  return url;
}

function EvidenceTile({
  item,
  runId,
}: {
  item: Evidence;
  runId: string;
}) {
  const url = useEvidenceObjectUrl(
    item.url,
    runId
  );

  return (
    <a
      href={url || undefined}
      target="_blank"
      rel="noopener noreferrer"
      style={styles.evidenceCard}
    >
      {url ? (
        <img
          src={url}
          alt={item.name || "Execution evidence"}
          style={styles.evidenceImage}
        />
      ) : (
        <div
          style={{
            ...styles.evidenceImage,
            padding: 16,
            color: COLORS.muted,
          }}
        >
          Loading evidence or screenshot unavailable
        </div>
      )}

      <div style={styles.evidenceInfo}>
        <small style={{ color: COLORS.purple }}>
          {formatAction(item.type)}
        </small>

        <strong>
          {item.name || "Test Evidence"}
        </strong>
      </div>
    </a>
  );
}

function StatusBadge({ status }: { status?: Status }) {
  const current = status || "SKIPPED";
  const color = statusColor(current);

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "6px 11px",
        borderRadius: 999,
        border: `1px solid ${color}`,
        color,
        fontSize: 12,
        fontWeight: 800,
        whiteSpace: "nowrap",
      }}
    >
      {statusIcon(current)} {current}
    </span>
  );
}

function SummaryCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <div style={styles.summaryCard}>
      <span style={styles.smallLabel}>{label}</span>
      <strong
        style={{
          fontSize: 24,
          color: color || COLORS.text,
          overflowWrap: "anywhere",
        }}
      >
        {value}
      </strong>
    </div>
  );
}

function InfoItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div style={styles.infoItem}>
      <span style={styles.smallLabel}>{label}</span>
      <strong style={{ overflowWrap: "anywhere" }}>
        {value}
      </strong>
    </div>
  );
}

function HealingBox({ healing }: { healing: Healing }) {
  return (
    <div style={styles.healingBox}>
      <strong style={{ color: COLORS.yellow }}>
        ↻ Self-healing applied
      </strong>

      {healing.original_locator && (
        <p style={styles.detail}>
          Original locator:{" "}
          {formatLocator(healing.original_locator)}
        </p>
      )}

      {healing.replacement_locator && (
        <p style={styles.detail}>
          Replacement locator:{" "}
          {formatLocator(healing.replacement_locator)}
        </p>
      )}

      {typeof healing.confidence === "number" && (
        <p style={styles.detail}>
          Confidence:{" "}
          {healing.confidence <= 1
            ? (healing.confidence * 100).toFixed(1)
            : healing.confidence.toFixed(1)}
          %
        </p>
      )}

      {healing.reason && (
        <p style={styles.detail}>
          Reason: {healing.reason}
        </p>
      )}
    </div>
  );
}

function Screenshot({
  path,
  title,
  runId,
}: {
  path?: string;
  title: string;
  runId: string;
}) {
  const url = useEvidenceObjectUrl(path, runId);
  if (!path) return null;

  return (
    <div style={{ marginTop: 15 }}>
      <p style={styles.detail}>{title}</p>

      <a
        href={url || undefined}
        target="_blank"
        rel="noopener noreferrer"
      >
        <img
          src={url || undefined}
          alt={title}
          style={styles.screenshot}
        />
      </a>
    </div>
  );
}

function ComparisonValue({
  label,
  value,
}: {
  label: string;
  value?: string;
}) {
  return (
    <div style={styles.comparisonValue}>
      <span style={styles.smallLabel}>{label}</span>

      <div style={styles.valueText}>
        {value !== undefined && value !== null
          ? value
          : "Not available"}
      </div>
    </div>
  );
}

function VerificationCard({
  verification,
  index,
  runId,
}: {
  verification: Verification;
  index: number;
  runId: string;
}) {
  const expected =
    verification.expected ?? verification.value;

  const actual = verification.actual;

  const status = verification.status || "SKIPPED";

  return (
    <div
      style={{
        ...styles.verificationCard,
        borderLeft: `3px solid ${statusColor(status)}`,
      }}
    >
      <div style={styles.itemHeader}>
        <div>
          <strong>
            Verification {index + 1}:{" "}
            {formatAction(verification.type)}
          </strong>

          <p style={styles.detail}>
            Condition:{" "}
            {formatAction(verification.condition || "contains")}
          </p>
        </div>

        <StatusBadge status={status} />
      </div>

      <div style={styles.comparisonGrid}>
        <ComparisonValue
          label="EXPECTED RESULT"
          value={expected}
        />

        <ComparisonValue
          label="ACTUAL RESULT"
          value={actual}
        />
      </div>

      <div style={styles.comparisonFooter}>
        <strong
          style={{
            color: statusColor(status),
          }}
        >
          {status === "PASS"
            ? "Comparison matched"
            : status === "HEALED"
            ? "Comparison passed with self-healing"
            : status === "FAIL"
            ? "Comparison failed"
            : "Comparison not executed"}
        </strong>

        {verification.message && (
          <p style={styles.detail}>
            {verification.message}
          </p>
        )}

        {verification.error && (
          <p style={styles.errorText}>
            {verification.error}
          </p>
        )}
      </div>

      {verification.healing?.healed && (
        <HealingBox healing={verification.healing} />
      )}

      <Screenshot
        path={verification.screenshot}
        title={`Verification ${index + 1} evidence`}
        runId={runId}
      />
    </div>
  );
}

export default function RunDetailsPage() {
  const params = useParams();
  const runId = String(params.id || "");

  const [run, setRun] = useState<Run | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadRun = useCallback(async () => {
    if (!runId) return;

    try {
      setLoading(true);
      setError("");

      const response = await api(
        `/api/runs/${encodeURIComponent(runId)}`
      );

      setRun(response.run as Run);
    } catch (err) {
      console.error("Failed to load run:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load test run."
      );

      setRun(null);
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    void loadRun();
  }, [loadRun]);

  if (loading) {
    return (
      <main style={styles.page}>
        <div style={styles.container}>
          <div style={styles.card}>
            Loading test execution...
          </div>
        </div>
      </main>
    );
  }

  if (!run) {
    return (
      <main style={styles.page}>
        <div style={styles.container}>
          <div style={styles.card}>
            <h1>Unable to load run</h1>

            <p style={styles.muted}>
              {error || "Test run not found."}
            </p>

            <button
              style={styles.primaryButton}
              onClick={() => void loadRun()}
            >
              Retry
            </button>
          </div>
        </div>
      </main>
    );
  }

  const steps = run.steps || [];
  const verifications = run.verifications || [];
  const evidence = run.evidence || [];

  const passedSteps = steps.filter(
    (step) => step.status === "PASS"
  ).length;

  const healedSteps = steps.filter(
    (step) => step.status === "HEALED"
  ).length;

  const failedSteps = steps.filter(
    (step) => step.status === "FAIL"
  ).length;

  const comparison = run.comparison_summary;

  const totalComparisons =
    comparison?.total ?? verifications.length;

  const executedComparisons =
    comparison?.executed ?? verifications.length;

  const passedComparisons =
    comparison?.passed ??
    verifications.filter(
      (item) =>
        item.status === "PASS" ||
        item.status === "HEALED"
    ).length;

  const failedComparisons =
    comparison?.failed ??
    verifications.filter(
      (item) => item.status === "FAIL"
    ).length;

  const skippedComparisons =
    comparison?.skipped ??
    Math.max(
      0,
      totalComparisons - executedComparisons
    );

  const screenshotPaths = new Set<string>();

  const screenshotItems: Evidence[] = [];

  function addEvidence(
    path?: string,
    name?: string,
    type?: string
  ) {
    if (!path || screenshotPaths.has(path)) return;

    screenshotPaths.add(path);

    screenshotItems.push({
      url: path,
      name,
      type,
    });
  }

  evidence.forEach((item) =>
    addEvidence(item.url, item.name, item.type)
  );

  steps.forEach((step, index) =>
    addEvidence(
      step.screenshot,
      `Step ${index + 1} evidence`,
      "step"
    )
  );

  verifications.forEach((item, index) =>
    addEvidence(
      item.screenshot,
      `Verification ${index + 1} evidence`,
      "verification"
    )
  );

  addEvidence(
    run.screenshot,
    "Final execution screenshot",
    "final"
  );

  return (
    <main style={styles.page}>
      <div style={styles.container}>

        {/* HEADER */}

        <header style={styles.header}>
          <div>
            <Link href="/runs" style={styles.backLink}>
              ← Back to Runs
            </Link>

            <div style={styles.titleRow}>
              <h1 style={styles.title}>
                {run.test_name ||
                  run.test?.name ||
                  "Test Execution"}
              </h1>

              <StatusBadge status={run.status} />
            </div>

            <p style={styles.muted}>
              {run.target_url ||
                run.test?.target_url ||
                "Target URL unavailable"}
            </p>
          </div>

          <div style={styles.actions}>
            <button
              style={styles.secondaryButton}
              onClick={() => void loadRun()}
            >
              Refresh
            </button>

            {run.test_case_id && (
              <Link
                href={`/tests/${run.test_case_id}`}
                style={styles.primaryLink}
              >
                Open Test Case
              </Link>
            )}
          </div>
        </header>

        {/* OVERALL SUMMARY */}

        <section style={styles.summaryGrid}>
          <SummaryCard
            label="Overall Result"
            value={run.status || "Unknown"}
            color={statusColor(run.status)}
          />

          <SummaryCard
            label="Passed Steps"
            value={passedSteps}
            color={COLORS.green}
          />

          <SummaryCard
            label="Healed Steps"
            value={healedSteps}
            color={COLORS.yellow}
          />

          <SummaryCard
            label="Failed Steps"
            value={failedSteps}
            color={COLORS.red}
          />

          <SummaryCard
            label="Expected Results"
            value={totalComparisons}
          />

          <SummaryCard
            label="Duration"
            value={formatDuration(run.duration_ms)}
          />
        </section>

        {/* EXECUTION RESULT */}

        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>
            Execution Result
          </h2>

          <div
            style={{
              ...styles.resultBox,
              borderColor: statusColor(run.status),
            }}
          >
            <StatusBadge status={run.status} />

            <p style={styles.resultText}>
              {run.message ||
                (run.status === "PASS"
                  ? "The workflow and expected results completed successfully."
                  : run.status === "HEALED"
                  ? "The test completed successfully with self-healing."
                  : "The test failed or an expected result did not match.")}
            </p>
          </div>
        </section>

        {/* EXPECTED VS ACTUAL COMPARISON */}

        <section style={styles.card}>
          <div style={styles.sectionHeader}>
            <div>
              <h2 style={styles.sectionTitle}>
                Expected vs Actual Comparison
              </h2>

              <p style={styles.muted}>
                Actual website behavior captured by Playwright
                compared against saved expected results.
              </p>
            </div>
          </div>

          <div style={styles.comparisonSummaryGrid}>
            <SummaryCard
              label="Total Checks"
              value={totalComparisons}
            />

            <SummaryCard
              label="Executed"
              value={executedComparisons}
            />

            <SummaryCard
              label="Passed"
              value={passedComparisons}
              color={COLORS.green}
            />

            <SummaryCard
              label="Failed"
              value={failedComparisons}
              color={COLORS.red}
            />

            <SummaryCard
              label="Skipped"
              value={skippedComparisons}
              color={COLORS.yellow}
            />
          </div>

          {skippedComparisons > 0 && (
            <div style={styles.warning}>
              {skippedComparisons} verification(s) were
              not executed. Check whether a recorded
              workflow step failed before verification.
            </div>
          )}

          {verifications.length === 0 ? (
            <div style={styles.empty}>
              No executed verification results are
              available for this run.
            </div>
          ) : (
            verifications.map((verification, index) => (
              <VerificationCard
                key={index}
                verification={verification}
                index={index}
                runId={runId}
              />
            ))
          )}
        </section>

        {/* RUN INFORMATION */}

        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>
            Run Information
          </h2>

          <div style={styles.infoGrid}>
            <InfoItem
              label="Run ID"
              value={run.id || run.test_run_id || "—"}
            />

            <InfoItem
              label="Test Case ID"
              value={run.test_case_id || "—"}
            />

            <InfoItem
              label="Started"
              value={formatDate(run.started_at)}
            />

            <InfoItem
              label="Finished"
              value={formatDate(run.finished_at)}
            />

            <InfoItem
              label="Healing Count"
              value={String(
                run.healing_count ?? healedSteps
              )}
            />

            <InfoItem
              label="Total Executed Steps"
              value={String(steps.length)}
            />
          </div>
        </section>

        {/* EXECUTION STEPS */}

        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>
            Execution Steps
          </h2>

          <p style={styles.muted}>
            Actual execution results for each recorded
            browser action.
          </p>

          {steps.length === 0 ? (
            <div style={styles.empty}>
              No execution steps were recorded.
            </div>
          ) : (
            steps.map((step, index) => (
              <div key={index} style={styles.step}>
                <div style={styles.stepNumber}>
                  {index + 1}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={styles.itemHeader}>
                    <strong>
                      {formatAction(step.action)}
                    </strong>

                    <StatusBadge status={step.status} />
                  </div>

                  {step.url && (
                    <p style={styles.detail}>
                      URL: {step.url}
                    </p>
                  )}

                  {step.value && (
                    <p style={styles.detail}>
                      Value: {step.value}
                    </p>
                  )}

                  {step.message && (
                    <p style={styles.detail}>
                      {step.message}
                    </p>
                  )}

                  {step.duration_ms !== undefined && (
                    <p style={styles.detail}>
                      Duration:{" "}
                      {formatDuration(step.duration_ms)}
                    </p>
                  )}

                  {step.error && (
                    <div style={styles.errorBox}>
                      <strong>Step Failure</strong>
                      <p>{step.error}</p>
                    </div>
                  )}

                  {step.healing?.healed && (
                    <HealingBox healing={step.healing} />
                  )}

                  <Screenshot
                    path={step.screenshot}
                    title={`Step ${index + 1} evidence`}
                    runId={runId}
                  />
                </div>
              </div>
            ))
          )}
        </section>

        {/* SCREENSHOT EVIDENCE */}

        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>
            Execution Evidence
          </h2>

          <p style={styles.muted}>
            Screenshots captured during browser
            execution and expected-result verification.
          </p>

          {screenshotItems.length === 0 ? (
            <div style={styles.empty}>
              No screenshot evidence is available
              for this run.
            </div>
          ) : (
            <div style={styles.evidenceGrid}>
              {screenshotItems.map((item, index) => (
                <EvidenceTile
                  key={index}
                  item={item}
                  runId={runId}
                />
              ))}
            </div>
          )}
        </section>

        {/* EXECUTION ERROR */}

        {run.error && (
          <section style={styles.card}>
            <h2
              style={{
                ...styles.sectionTitle,
                color: COLORS.red,
              }}
            >
              Execution Error
            </h2>

            <pre style={styles.errorPre}>
              {run.error}
            </pre>
          </section>
        )}

      </div>
    </main>
  );
}

const styles: Record<string, CSSProperties> = {
  page: {
    minHeight: "100vh",
    padding: "32px 20px",
    background: COLORS.background,
    color: COLORS.text,
  },

  container: {
    maxWidth: 1200,
    margin: "0 auto",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-end",
    flexWrap: "wrap",
    gap: 20,
    marginBottom: 24,
  },

  backLink: {
    color: COLORS.muted,
    textDecoration: "none",
  },

  titleRow: {
    display: "flex",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 14,
    marginTop: 12,
  },

  title: {
    margin: 0,
    fontSize: 30,
    fontWeight: 800,
  },

  actions: {
    display: "flex",
    gap: 10,
    flexWrap: "wrap",
  },

  primaryLink: {
    display: "inline-flex",
    alignItems: "center",
    padding: "11px 18px",
    background: COLORS.purple,
    color: "white",
    borderRadius: 8,
    fontWeight: 700,
    textDecoration: "none",
  },

  primaryButton: {
    padding: "11px 18px",
    background: COLORS.purple,
    color: "white",
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    fontWeight: 700,
  },

  secondaryButton: {
    padding: "11px 18px",
    background: COLORS.surface,
    color: COLORS.text,
    border: `1px solid ${COLORS.border}`,
    borderRadius: 8,
    cursor: "pointer",
  },

  card: {
    background: COLORS.card,
    border: `1px solid ${COLORS.border}`,
    borderRadius: 14,
    padding: 24,
    marginBottom: 20,
  },

  sectionHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 15,
    flexWrap: "wrap",
  },

  sectionTitle: {
    fontSize: 20,
    margin: "0 0 10px",
  },

  muted: {
    color: COLORS.muted,
    lineHeight: 1.6,
    overflowWrap: "anywhere",
  },

  summaryGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(150px, 1fr))",
    gap: 12,
    marginBottom: 20,
  },

  summaryCard: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    padding: 18,
    background: COLORS.card,
    border: `1px solid ${COLORS.border}`,
    borderRadius: 12,
  },

  smallLabel: {
    display: "block",
    fontSize: 12,
    fontWeight: 600,
    color: COLORS.muted,
    marginBottom: 7,
  },

  resultBox: {
    marginTop: 16,
    padding: 16,
    background: COLORS.surface,
    border: "1px solid",
    borderRadius: 10,
  },

  resultText: {
    color: "#a7afbd",
    lineHeight: 1.6,
    marginBottom: 0,
  },

  comparisonSummaryGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(130px, 1fr))",
    gap: 12,
    margin: "20px 0",
  },

  verificationCard: {
    padding: 18,
    marginTop: 14,
    background: COLORS.surface,
    border: `1px solid ${COLORS.border}`,
    borderRadius: 10,
  },

  itemHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    flexWrap: "wrap",
    gap: 14,
  },

  comparisonGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(250px, 1fr))",
    gap: 12,
    marginTop: 18,
  },

  comparisonValue: {
    background: COLORS.background,
    border: `1px solid ${COLORS.border}`,
    borderRadius: 9,
    padding: 15,
    minWidth: 0,
  },

  valueText: {
    fontSize: 14,
    color: COLORS.text,
    whiteSpace: "pre-wrap",
    overflowWrap: "anywhere",
    maxHeight: 180,
    overflowY: "auto",
    lineHeight: 1.6,
  },

  comparisonFooter: {
    marginTop: 15,
    paddingTop: 12,
    borderTop: `1px solid ${COLORS.border}`,
  },

  infoGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(200px, 1fr))",
    gap: 12,
    marginTop: 18,
  },

  infoItem: {
    padding: 14,
    background: COLORS.surface,
    border: `1px solid ${COLORS.border}`,
    borderRadius: 9,
  },

  step: {
    display: "flex",
    gap: 14,
    padding: "18px 0",
    borderBottom: `1px solid ${COLORS.border}`,
  },

  stepNumber: {
    width: 34,
    height: 34,
    flexShrink: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    borderRadius: "50%",
    background: COLORS.surface,
    color: COLORS.purple,
    fontWeight: 800,
  },

  detail: {
    color: COLORS.muted,
    lineHeight: 1.6,
    margin: "8px 0 0",
    overflowWrap: "anywhere",
  },

  healingBox: {
    marginTop: 14,
    padding: 14,
    borderRadius: 9,
    background: "rgba(245,184,75,0.06)",
    border: "1px solid rgba(245,184,75,0.25)",
  },

  errorBox: {
    marginTop: 14,
    padding: 14,
    borderRadius: 9,
    background: "rgba(248,113,113,0.06)",
    border: "1px solid rgba(248,113,113,0.25)",
    color: COLORS.red,
  },

  errorText: {
    color: COLORS.red,
    lineHeight: 1.6,
    overflowWrap: "anywhere",
  },

  warning: {
    marginTop: 14,
    padding: 14,
    borderRadius: 9,
    background: "rgba(245,184,75,0.06)",
    border: "1px solid rgba(245,184,75,0.25)",
    color: COLORS.yellow,
  },

  empty: {
    marginTop: 16,
    color: COLORS.muted,
  },

  screenshot: {
    width: 350,
    maxWidth: "100%",
    borderRadius: 8,
    border: `1px solid ${COLORS.border}`,
  },

  evidenceGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(220px, 1fr))",
    gap: 14,
    marginTop: 18,
  },

  evidenceCard: {
    display: "block",
    overflow: "hidden",
    borderRadius: 10,
    background: COLORS.surface,
    border: `1px solid ${COLORS.border}`,
    color: COLORS.text,
    textDecoration: "none",
  },

  evidenceImage: {
    width: "100%",
    height: 180,
    objectFit: "cover",
    display: "block",
  },

  evidenceInfo: {
    display: "flex",
    flexDirection: "column",
    gap: 5,
    padding: 12,
    overflowWrap: "anywhere",
  },

  errorPre: {
    padding: 15,
    overflowX: "auto",
    whiteSpace: "pre-wrap",
    overflowWrap: "anywhere",
    background: COLORS.background,
    border: `1px solid ${COLORS.border}`,
    borderRadius: 8,
    color: COLORS.red,
  },
};
