"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { api } from "@/lib/api";

import type {
  TestCase,
  VerificationStep,
  VerificationType,
} from "@/lib/types";

export default function TestDetailsPage() {
  const params = useParams();
  const router = useRouter();

  const testId = String(params.id);

  const [test, setTest] =
    useState<TestCase | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [running, setRunning] =
    useState(false);

  const [saving, setSaving] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const [verificationType, setVerificationType] =
    useState<VerificationType>("url");

  const [condition, setCondition] =
    useState<"contains" | "equals">("contains");

  const [verificationValue, setVerificationValue] =
    useState("");

  // ============================================================
  // LOAD TEST
  // ============================================================

  async function loadTest() {
    try {
      setLoading(true);
      setMessage("");

      const response =
        await api(`/api/tests/${testId}`);

      setTest({
        ...response.test,
        steps: response.test.steps || [],
        verifications:
          response.test.verifications || [],
      });
    } catch (error) {
      console.error(
        "Unable to load test:",
        error
      );

      setMessage(
        "Unable to load test case."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (testId) {
      loadTest();
    }
  }, [testId]);

  // ============================================================
  // SAVE VERIFICATIONS
  // ============================================================

  async function saveVerifications(
    verifications: VerificationStep[]
  ) {
    if (!test) return;

    await api(
      `/api/tests/${test.id}/verifications`,
      {
        method: "PUT",
        body: JSON.stringify({
          verifications,
        }),
      }
    );

    setTest({
      ...test,
      verifications,
    });
  }

  // ============================================================
  // ADD VERIFICATION
  // ============================================================

  async function addVerification() {
    if (!test) return;

    const value =
      verificationValue.trim();

    if (!value) {
      setMessage(
        "Please enter an expected value."
      );
      return;
    }

    const newVerification: VerificationStep = {
      type: verificationType,
      value,
    };

    if (
      verificationType === "url" ||
      verificationType === "text" ||
      verificationType === "page_title"
    ) {
      newVerification.condition =
        condition;
    }

    /*
      Element verification is temporarily stored
      using a human-readable target.

      Later our recorder will automatically capture
      the full element locator so testers will NOT
      need to write CSS/XPath/code.
    */
    if (verificationType === "element") {
      newVerification.target = {
        name: value,
      };
    }

    const updated = [
      ...(test.verifications || []),
      newVerification,
    ];

    try {
      setSaving(true);
      setMessage("");

      await saveVerifications(updated);

      setVerificationValue("");

      setMessage(
        "Expected result saved successfully."
      );
    } catch (error) {
      console.error(
        "Unable to save verification:",
        error
      );

      setMessage(
        "Unable to save expected result."
      );
    } finally {
      setSaving(false);
    }
  }

  // ============================================================
  // REMOVE VERIFICATION
  // ============================================================

  async function removeVerification(
    index: number
  ) {
    if (!test) return;

    const updated =
      test.verifications.filter(
        (_, currentIndex) =>
          currentIndex !== index
      );

    try {
      setSaving(true);
      setMessage("");

      await saveVerifications(updated);

      setMessage(
        "Expected result removed."
      );
    } catch (error) {
      console.error(
        "Unable to remove verification:",
        error
      );

      setMessage(
        "Unable to remove expected result."
      );
    } finally {
      setSaving(false);
    }
  }

  // ============================================================
  // RUN TEST
  // ============================================================

  async function runTest() {
    if (!test) return;

    if (test.steps.length === 0) {
      setMessage(
        "This test has no recorded actions."
      );
      return;
    }

    try {
      setRunning(true);
      setMessage("");

      const response =
        await api(
          `/api/tests/${test.id}/run`,
          {
            method: "POST",
          }
        );

      const runId =
        response.run?.id ||
        response.run?.test_run_id;

      if (!runId) {
        setMessage(
          "Execution completed but no run ID was returned."
        );
        return;
      }

      router.push(
        `/runs/${runId}`
      );
    } catch (error) {
      console.error(
        "Test execution failed:",
        error
      );

      setMessage(
        error instanceof Error
          ? error.message
          : "Test execution failed."
      );
    } finally {
      setRunning(false);
    }
  }

  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {
    return (
      <main style={styles.page}>
        <div style={styles.card}>
          Loading test case...
        </div>
      </main>
    );
  }

  // ============================================================
  // NOT FOUND
  // ============================================================

  if (!test) {
    return (
      <main style={styles.page}>
        <div style={styles.card}>
          <h1>Test case unavailable</h1>

          <p style={styles.muted}>
            {message ||
              "The requested test case could not be loaded."}
          </p>

          <button
            style={styles.primaryButton}
            onClick={() =>
              router.push("/tests")
            }
          >
            Back to Tests
          </button>
        </div>
      </main>
    );
  }

  // ============================================================
  // PAGE
  // ============================================================

  return (
    <main style={styles.page}>
      <div style={styles.container}>

        {/* HEADER */}

        <header style={styles.header}>
          <div>
            <p style={styles.eyebrow}>
              TEST CASE
            </p>

            <h1 style={styles.title}>
              {test.name}
            </h1>

            <p style={styles.url}>
              {test.target_url}
            </p>
          </div>

          <div style={styles.actions}>
            <button
              style={styles.secondaryButton}
              onClick={() =>
                router.push("/tests")
              }
            >
              Back
            </button>

            <button
              style={styles.secondaryButton}
              onClick={() =>
                router.push(
                  `/runs?test_id=${test.id}`
                )
              }
            >
              Run History
            </button>

            <button
              style={{
                ...styles.primaryButton,
                opacity: running ? 0.6 : 1,
              }}
              disabled={running}
              onClick={runTest}
            >
              {running
                ? "Running..."
                : "Run Test"}
            </button>
          </div>
        </header>

        {/* MESSAGE */}

        {message && (
          <div style={styles.message}>
            {message}
          </div>
        )}

        {/* TEST INFORMATION */}

        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>
            Test Information
          </h2>

          <div style={styles.infoGrid}>
            <Info
              label="Test Name"
              value={test.name}
            />

            <Info
              label="Target Website"
              value={test.target_url}
            />

            <Info
              label="Recorded Actions"
              value={String(
                test.steps.length
              )}
            />

            <Info
              label="Expected Results"
              value={String(
                test.verifications.length
              )}
            />
          </div>
        </section>

        {/* RECORDED ACTIONS */}

        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>
            Recorded Actions
          </h2>

          <p style={styles.muted}>
            These actions were captured
            automatically while the tester
            interacted with the website.
          </p>

          {test.steps.length === 0 ? (
            <div style={styles.empty}>
              No recorded actions are available.
            </div>
          ) : (
            test.steps.map(
              (step, index) => (
                <div
                  key={index}
                  style={styles.step}
                >
                  <div
                    style={styles.stepNumber}
                  >
                    {index + 1}
                  </div>

                  <div style={{ flex: 1 }}>
                    <strong>
                      {formatAction(
                        step.action
                      )}
                    </strong>

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

                    {step.ms !== undefined && (
                      <p style={styles.detail}>
                        Wait: {step.ms} ms
                      </p>
                    )}

                    {step.target && (
                      <p style={styles.detail}>
                        Target:{" "}
                        {getTargetName(
                          step.target
                        )}
                      </p>
                    )}
                  </div>
                </div>
              )
            )
          )}
        </section>

        {/* EXPECTED RESULTS */}

        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>
            Expected Results
          </h2>

          <p style={styles.muted}>
            Expected results determine
            whether this workflow should
            PASS or FAIL.
          </p>

          {test.verifications.length ===
          0 ? (
            <div style={styles.warning}>
              No expected results have been
              configured yet.
            </div>
          ) : (
            test.verifications.map(
              (verification, index) => (
                <div
                  key={index}
                  style={
                    styles.verification
                  }
                >
                  <div>
                    <strong>
                      {verificationLabel(
                        verification.type
                      )}
                    </strong>

                    {verification.condition && (
                      <span
                        style={
                          styles.condition
                        }
                      >
                        {
                          verification.condition
                        }
                      </span>
                    )}

                    <p style={styles.detail}>
                      Expected:{" "}
                      {verification.value ||
                        getTargetName(
                          verification.target
                        )}
                    </p>
                  </div>

                  <button
                    style={
                      styles.removeButton
                    }
                    disabled={saving}
                    onClick={() =>
                      removeVerification(
                        index
                      )
                    }
                  >
                    Remove
                  </button>
                </div>
              )
            )
          )}
        </section>

        {/* ADD EXPECTED RESULT */}

        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>
            Add Expected Result
          </h2>

          <p style={styles.muted}>
            Tell Test AI what should be true
            after the recorded workflow
            finishes. No programming is
            required.
          </p>

          <div style={styles.formGrid}>
            <div>
              <label style={styles.label}>
                Verification Type
              </label>

              <select
                style={styles.input}
                value={verificationType}
                onChange={(event) => {
                  setVerificationType(
                    event.target
                      .value as VerificationType
                  );

                  setVerificationValue(
                    ""
                  );
                }}
              >
                <option value="url">
                  URL
                </option>

                <option value="text">
                  Page Text
                </option>

                <option value="page_title">
                  Page Title
                </option>

                <option value="element">
                  Element Exists
                </option>
              </select>
            </div>

            {verificationType !==
              "element" && (
              <div>
                <label
                  style={styles.label}
                >
                  Condition
                </label>

                <select
                  style={styles.input}
                  value={condition}
                  onChange={(event) =>
                    setCondition(
                      event.target.value as
                        | "contains"
                        | "equals"
                    )
                  }
                >
                  <option value="contains">
                    Contains
                  </option>

                  <option value="equals">
                    Equals
                  </option>
                </select>
              </div>
            )}

            <div
              style={styles.fullWidth}
            >
              <label style={styles.label}>
                {verificationType ===
                "element"
                  ? "Element name"
                  : "Expected value"}
              </label>

              <input
                style={styles.input}
                value={verificationValue}
                onChange={(event) =>
                  setVerificationValue(
                    event.target.value
                  )
                }
                placeholder={getPlaceholder(
                  verificationType
                )}
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter"
                  ) {
                    addVerification();
                  }
                }}
              />
            </div>
          </div>

          <button
            style={{
              ...styles.primaryButton,
              opacity: saving ? 0.6 : 1,
            }}
            disabled={saving}
            onClick={addVerification}
          >
            {saving
              ? "Saving..."
              : "Add Expected Result"}
          </button>
        </section>

      </div>
    </main>
  );
}

// ============================================================
// HELPERS
// ============================================================

function formatAction(
  action?: string
) {
  if (!action) return "Action";

  return action
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    );
}

function verificationLabel(
  type: string
) {
  switch (type) {
    case "url":
      return "URL";

    case "text":
      return "Page Text";

    case "page_title":
      return "Page Title";

    case "element":
      return "Element Exists";

    default:
      return formatAction(type);
  }
}

function getTargetName(
  target?: {
    name?: string;
    label?: string;
    id?: string;
    css?: string;
    role?: string;
    placeholder?: string;
  }
) {
  if (!target) {
    return "Recorded element";
  }

  return (
    target.name ||
    target.label ||
    target.placeholder ||
    target.id ||
    target.css ||
    target.role ||
    "Recorded element"
  );
}

function getPlaceholder(
  type: VerificationType
) {
  switch (type) {
    case "url":
      return "/dashboard";

    case "text":
      return "Welcome";

    case "page_title":
      return "Dashboard";

    case "element":
      return "Login button";

    default:
      return "Expected value";
  }
}

function Info({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div style={styles.info}>
      <span style={styles.infoLabel}>
        {label}
      </span>

      <strong>{value}</strong>
    </div>
  );
}

// ============================================================
// STYLES
// ============================================================

const styles: Record<
  string,
  React.CSSProperties
> = {
  page: {
    minHeight: "100vh",
    padding: "32px 20px",
    background: "#07090d",
    color: "#f5f7fa",
  },

  container: {
    maxWidth: "1200px",
    margin: "0 auto",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "20px",
    flexWrap: "wrap",
    marginBottom: "24px",
  },

  eyebrow: {
    color: "#8b7cf6",
    fontSize: "12px",
    fontWeight: 800,
    letterSpacing: "1.5px",
    margin: 0,
  },

  title: {
    margin: "6px 0",
    fontSize: "30px",
  },

  url: {
    margin: 0,
    color: "#8992a3",
    wordBreak: "break-all",
  },

  actions: {
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
  },

  card: {
    background: "#0d1117",
    border: "1px solid #222936",
    borderRadius: "14px",
    padding: "24px",
    marginBottom: "20px",
  },

  sectionTitle: {
    margin: "0 0 8px",
    fontSize: "20px",
  },

  muted: {
    color: "#8992a3",
    lineHeight: 1.6,
  },

  message: {
    background: "#121720",
    border: "1px solid #222936",
    borderRadius: "9px",
    padding: "13px 15px",
    marginBottom: "20px",
  },

  infoGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(180px, 1fr))",
    gap: "12px",
    marginTop: "18px",
  },

  info: {
    background: "#121720",
    border: "1px solid #222936",
    borderRadius: "9px",
    padding: "14px",
  },

  infoLabel: {
    display: "block",
    color: "#8992a3",
    fontSize: "12px",
    marginBottom: "7px",
  },

  step: {
    display: "flex",
    gap: "14px",
    padding: "15px 0",
    borderBottom:
      "1px solid #222936",
  },

  stepNumber: {
    width: "32px",
    height: "32px",
    flexShrink: 0,
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#121720",
    color: "#8b7cf6",
    fontWeight: 800,
  },

  detail: {
    color: "#8992a3",
    margin: "6px 0 0",
    wordBreak: "break-word",
  },

  verification: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "15px",
    padding: "15px",
    marginTop: "10px",
    background: "#121720",
    border:
      "1px solid #222936",
    borderRadius: "10px",
  },

  condition: {
    marginLeft: "8px",
    padding: "3px 7px",
    borderRadius: "5px",
    background: "#07090d",
    color: "#8b7cf6",
    fontSize: "12px",
  },

  warning: {
    marginTop: "15px",
    color: "#f5b84b",
    padding: "14px",
    borderRadius: "9px",
    background:
      "rgba(245,184,75,0.07)",
    border:
      "1px solid rgba(245,184,75,0.2)",
  },

  empty: {
    marginTop: "15px",
    color: "#8992a3",
  },

  formGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "16px",
    margin: "20px 0",
  },

  fullWidth: {
    gridColumn: "1 / -1",
  },

  label: {
    display: "block",
    marginBottom: "7px",
    color: "#8992a3",
    fontSize: "13px",
  },

  input: {
    width: "100%",
    boxSizing: "border-box",
    padding: "12px",
    borderRadius: "8px",
    border:
      "1px solid #222936",
    background: "#07090d",
    color: "#f5f7fa",
    outline: "none",
  },

  primaryButton: {
    border: "none",
    borderRadius: "8px",
    padding: "11px 18px",
    background: "#8b7cf6",
    color: "white",
    fontWeight: 700,
    cursor: "pointer",
  },

  secondaryButton: {
    border:
      "1px solid #222936",
    borderRadius: "8px",
    padding: "11px 18px",
    background: "#121720",
    color: "#f5f7fa",
    cursor: "pointer",
  },

  removeButton: {
    border:
      "1px solid #5a2930",
    borderRadius: "7px",
    padding: "8px 12px",
    background: "transparent",
    color: "#f87171",
    cursor: "pointer",
  },
};