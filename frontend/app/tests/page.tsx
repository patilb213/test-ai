"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";

type Project = {
  id: string;
  name: string;
  target_url?: string;
  description?: string;
};

type TestCase = {
  id: string;
  project_id: string;
  project_name?: string;
  name: string;
  target_url?: string;
  events?: unknown[];
  steps?: unknown[];
  created_at?: string;
  updated_at?: string;
};

export default function TestsPage() {
  const [tests, setTests] = useState<TestCase[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [selectedProject, setSelectedProject] = useState("all");

  // ==========================================================
  // LOAD PROJECTS
  // ==========================================================

  async function loadProjects() {
    try {
      const response = await api("/api/projects");

      const loadedProjects = Array.isArray(response?.projects)
        ? response.projects
        : [];

      setProjects(loadedProjects);
    } catch (err) {
      console.error("Unable to load projects:", err);
    }
  }

  // ==========================================================
  // LOAD TEST CASES
  // ==========================================================

  async function loadTests() {
    try {
      setLoading(true);
      setError("");

      const response = await api("/api/tests");

      console.log("Tests API response:", response);

      const loadedTests = Array.isArray(response?.tests)
        ? response.tests
        : Array.isArray(response)
        ? response
        : [];

      setTests(loadedTests);
    } catch (err) {
      console.error("Unable to load tests:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load test cases"
      );
    } finally {
      setLoading(false);
    }
  }

  // ==========================================================
  // INITIAL LOAD
  // ==========================================================

  useEffect(() => {
    loadProjects();
    loadTests();
  }, []);

  // ==========================================================
  // DELETE TEST
  // ==========================================================

  async function deleteTest(testId: string) {
    const confirmed = window.confirm(
      "Are you sure you want to delete this test case?"
    );

    if (!confirmed) {
      return;
    }

    try {
      setError("");
      setMessage("");

      await api(`/api/tests/${testId}`, {
        method: "DELETE",
      });

      setTests((currentTests) =>
        currentTests.filter((test) => test.id !== testId)
      );

      setMessage("Test case deleted successfully.");
    } catch (err) {
      console.error("Unable to delete test:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to delete test case"
      );
    }
  }

  // ==========================================================
  // GET PROJECT NAME
  // ==========================================================

  function getProjectName(projectId: string) {
    const project = projects.find(
      (item) => item.id === projectId
    );

    return project?.name || "Unknown project";
  }

  // ==========================================================
  // FILTER TESTS
  // ==========================================================

  const filteredTests =
    selectedProject === "all"
      ? tests
      : tests.filter(
          (test) =>
            test.project_id === selectedProject
        );

  // ==========================================================
  // GET NUMBER OF STEPS
  // ==========================================================

  function getStepCount(test: TestCase) {
    if (Array.isArray(test.events)) {
      return test.events.length;
    }

    if (Array.isArray(test.steps)) {
      return test.steps.length;
    }

    return 0;
  }

  // ==========================================================
  // FORMAT DATE
  // ==========================================================

  function formatDate(dateValue?: string) {
    if (!dateValue) {
      return "Not available";
    }

    try {
      return new Date(dateValue).toLocaleString();
    } catch {
      return dateValue;
    }
  }

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#07090d",
        color: "#f5f7fa",
        padding: "40px",
      }}
    >
      <div
        style={{
          maxWidth: "1200px",
          margin: "0 auto",
        }}
      >
        {/* HEADER */}

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: "20px",
            flexWrap: "wrap",
            marginBottom: "30px",
          }}
        >
          <div>
            <div
              style={{
                color: "#8b7cf6",
                fontSize: "14px",
                fontWeight: 700,
                letterSpacing: "1px",
                textTransform: "uppercase",
                marginBottom: "8px",
              }}
            >
              Test AI
            </div>

            <h1
              style={{
                fontSize: "32px",
                margin: 0,
                marginBottom: "8px",
              }}
            >
              Test Cases
            </h1>

            <p
              style={{
                color: "#8992a3",
                margin: 0,
              }}
            >
              Manage your recorded and reusable automated test cases.
            </p>
          </div>

          <Link
            href="/recorder"
            style={{
              textDecoration: "none",
              borderRadius: "10px",
              padding: "13px 20px",
              background: "#8b7cf6",
              color: "white",
              fontWeight: 700,
            }}
          >
            + Record new test
          </Link>
        </div>

        {/* ERROR */}

        {error && (
          <div
            style={{
              background: "rgba(248, 113, 113, 0.1)",
              border:
                "1px solid rgba(248, 113, 113, 0.35)",
              color: "#f87171",
              padding: "14px 16px",
              borderRadius: "10px",
              marginBottom: "20px",
            }}
          >
            {error}
          </div>
        )}

        {/* SUCCESS MESSAGE */}

        {message && (
          <div
            style={{
              background: "rgba(53, 211, 153, 0.1)",
              border:
                "1px solid rgba(53, 211, 153, 0.35)",
              color: "#35d399",
              padding: "14px 16px",
              borderRadius: "10px",
              marginBottom: "20px",
            }}
          >
            {message}
          </div>
        )}

        {/* FILTER SECTION */}

        <section
          style={{
            background: "#0d1117",
            border: "1px solid #222936",
            borderRadius: "16px",
            padding: "20px",
            marginBottom: "24px",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: "16px",
              flexWrap: "wrap",
            }}
          >
            <div
              style={{
                minWidth: "260px",
                flex: 1,
              }}
            >
              <label
                style={{
                  display: "block",
                  marginBottom: "8px",
                  color: "#c5cad4",
                  fontSize: "14px",
                }}
              >
                Filter by project
              </label>

              <select
                value={selectedProject}
                onChange={(event) =>
                  setSelectedProject(event.target.value)
                }
                style={{
                  width: "100%",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  border: "1px solid #222936",
                  background: "#121720",
                  color: "#f5f7fa",
                  outline: "none",
                }}
              >
                <option value="all">
                  All projects
                </option>

                {projects.map((project) => (
                  <option
                    key={project.id}
                    value={project.id}
                  >
                    {project.name}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={loadTests}
              disabled={loading}
              style={{
                marginTop: "26px",
                border: "1px solid #222936",
                borderRadius: "10px",
                padding: "12px 18px",
                background: "#121720",
                color: "#c5cad4",
                cursor: "pointer",
              }}
            >
              {loading
                ? "Loading..."
                : "Refresh tests"}
            </button>
          </div>
        </section>

        {/* TEST SUMMARY */}

        <div
          style={{
            marginBottom: "18px",
            color: "#8992a3",
            fontSize: "14px",
          }}
        >
          Showing {filteredTests.length} test
          {filteredTests.length === 1 ? "" : "s"}
        </div>

        {/* LOADING */}

        {loading ? (
          <section
            style={{
              background: "#0d1117",
              border: "1px solid #222936",
              borderRadius: "16px",
              padding: "50px",
              textAlign: "center",
              color: "#8992a3",
            }}
          >
            Loading test cases...
          </section>
        ) : filteredTests.length === 0 ? (
          /* EMPTY STATE */

          <section
            style={{
              background: "#0d1117",
              border: "1px solid #222936",
              borderRadius: "16px",
              padding: "60px 30px",
              textAlign: "center",
            }}
          >
            <h2
              style={{
                marginTop: 0,
                marginBottom: "10px",
              }}
            >
              No test cases found
            </h2>

            <p
              style={{
                color: "#8992a3",
                marginBottom: "24px",
              }}
            >
              Record browser actions and save them as reusable
              automated test cases.
            </p>

            <Link
              href="/recorder"
              style={{
                textDecoration: "none",
                display: "inline-block",
                borderRadius: "10px",
                padding: "13px 20px",
                background: "#8b7cf6",
                color: "white",
                fontWeight: 700,
              }}
            >
              Go to recorder
            </Link>
          </section>
        ) : (
          /* TEST LIST */

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fit, minmax(330px, 1fr))",
              gap: "18px",
            }}
          >
            {filteredTests.map((test) => (
              <article
                key={test.id}
                style={{
                  background: "#0d1117",
                  border: "1px solid #222936",
                  borderRadius: "16px",
                  padding: "22px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "16px",
                }}
              >
                {/* TOP */}

                <div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      gap: "12px",
                    }}
                  >
                    <div>
                      <div
                        style={{
                          color: "#8b7cf6",
                          fontSize: "12px",
                          fontWeight: 700,
                          textTransform: "uppercase",
                          letterSpacing: "0.8px",
                          marginBottom: "8px",
                        }}
                      >
                        {test.project_name ||
                          getProjectName(test.project_id)}
                      </div>

                      <h2
                        style={{
                          margin: 0,
                          fontSize: "20px",
                          wordBreak: "break-word",
                        }}
                      >
                        {test.name}
                      </h2>
                    </div>

                    <span
                      style={{
                        background:
                          "rgba(139, 124, 246, 0.12)",
                        color: "#a99cff",
                        padding: "6px 10px",
                        borderRadius: "20px",
                        fontSize: "12px",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {getStepCount(test)} step
                      {getStepCount(test) === 1
                        ? ""
                        : "s"}
                    </span>
                  </div>
                </div>

                {/* URL */}

                <div>
                  <div
                    style={{
                      color: "#8992a3",
                      fontSize: "12px",
                      marginBottom: "5px",
                    }}
                  >
                    Target website
                  </div>

                  <div
                    style={{
                      color: "#c5cad4",
                      fontSize: "13px",
                      wordBreak: "break-all",
                    }}
                  >
                    {test.target_url ||
                      "Target URL not available"}
                  </div>
                </div>

                {/* DATE */}

                <div>
                  <div
                    style={{
                      color: "#8992a3",
                      fontSize: "12px",
                      marginBottom: "5px",
                    }}
                  >
                    Created
                  </div>

                  <div
                    style={{
                      color: "#c5cad4",
                      fontSize: "13px",
                    }}
                  >
                    {formatDate(test.created_at)}
                  </div>
                </div>

                {/* ACTIONS */}

                <div
                  style={{
                    display: "flex",
                    gap: "10px",
                    marginTop: "auto",
                    flexWrap: "wrap",
                  }}
                >
                  <Link
                    href={`/tests/${test.id}`}
                    style={{
                      flex: 1,
                      minWidth: "120px",
                      textAlign: "center",
                      textDecoration: "none",
                      borderRadius: "10px",
                      padding: "11px 14px",
                      background: "#8b7cf6",
                      color: "white",
                      fontWeight: 700,
                      fontSize: "14px",
                    }}
                  >
                    View test
                  </Link>

                  <Link
                    href={`/tests/${test.id}`}
                    style={{
                      flex: 1,
                      minWidth: "120px",
                      textAlign: "center",
                      textDecoration: "none",
                      border: "1px solid #222936",
                      borderRadius: "10px",
                      padding: "11px 14px",
                      background: "#121720",
                      color: "#c5cad4",
                      fontWeight: 700,
                      fontSize: "14px",
                    }}
                  >
                    Run test
                  </Link>

                  <button
                    onClick={() => deleteTest(test.id)}
                    style={{
                      border:
                        "1px solid rgba(248, 113, 113, 0.35)",
                      borderRadius: "10px",
                      padding: "11px 14px",
                      background:
                        "rgba(248, 113, 113, 0.08)",
                      color: "#f87171",
                      fontWeight: 700,
                      cursor: "pointer",
                      fontSize: "14px",
                    }}
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}