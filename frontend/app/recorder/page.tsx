"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import type { Project } from "@/lib/types";


interface RecordingSession {
  session_id: string;
  project_id: string;
  name: string;
  target_url: string;
  status: string;
  browser_active: boolean;
  event_count: number;
}


interface StartResponse {
  message: string;

  session: RecordingSession;
}


interface StopResponse {
  message: string;

  test?: {
    id: string;
    project_id: string;
    name: string;
    target_url: string;
  };

  session: RecordingSession;
}


export default function RecorderPage() {
  const router = useRouter();

  const [projects, setProjects] =
    useState<Project[]>([]);

  const [projectId, setProjectId] =
    useState("");

  const [name, setName] =
    useState("");

  const [targetUrl, setTargetUrl] =
    useState("");

  const [session, setSession] =
    useState<RecordingSession | null>(
      null
    );

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [message, setMessage] =
    useState("");


  // ========================================================
  // LOAD PROJECTS
  // ========================================================

  useEffect(() => {
    loadProjects();
  }, []);


  async function loadProjects() {
    try {
      const response =
        await api<{
          projects: Project[];
        }>("/api/projects");

      setProjects(
        response.projects || []
      );

      if (
        response.projects &&
        response.projects.length > 0
      ) {
        setProjectId(
          response.projects[0].id
        );

        setTargetUrl(
          response.projects[0]
            .target_url || ""
        );
      }
    } catch (err) {
      console.error(err);

      setError(
        "Unable to load projects."
      );
    }
  }


  // ========================================================
  // PROJECT CHANGE
  // ========================================================

  function handleProjectChange(
    id: string
  ) {
    setProjectId(id);

    const selected =
      projects.find(
        (project) =>
          project.id === id
      );

    if (selected) {
      setTargetUrl(
        selected.target_url || ""
      );
    }
  }


  // ========================================================
  // START RECORDING
  // ========================================================

  async function startRecording(
    event: FormEvent
  ) {
    event.preventDefault();

    setError("");
    setMessage("");

    if (!projectId) {
      setError(
        "Please select a project."
      );

      return;
    }

    if (!name.trim()) {
      setError(
        "Please enter a test name."
      );

      return;
    }

    if (!targetUrl.trim()) {
      setError(
        "Please enter the website URL."
      );

      return;
    }

    setLoading(true);

    try {
      const response =
        await api<StartResponse>(
          "/api/recorder/start",
          {
            method: "POST",

            body: JSON.stringify({
              project_id: projectId,
              name: name.trim(),
              target_url:
                targetUrl.trim(),
            }),
          }
        );

      setSession(
        response.session
      );

      setMessage(
        "Recording started. Use the opened browser normally."
      );
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to start recording."
      );
    } finally {
      setLoading(false);
    }
  }


  // ========================================================
  // REFRESH RECORDING STATUS
  // ========================================================

  async function refreshSession() {
    if (!session) {
      return;
    }

    try {
      const response =
        await api<{
          session:
            RecordingSession;
        }>(
          `/api/recorder/${session.session_id}`
        );

      setSession(
        response.session
      );
    } catch (err) {
      console.error(err);
    }
  }


  // ========================================================
  // POLL EVENT COUNT
  // ========================================================

  useEffect(() => {
    if (
      !session ||
      session.status !== "recording"
    ) {
      return;
    }

    const timer =
      window.setInterval(
        refreshSession,
        1500
      );

    return () =>
      window.clearInterval(timer);
  }, [session?.session_id]);


  // ========================================================
  // STOP + SAVE
  // ========================================================

  async function stopRecording() {
    if (!session) {
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const response =
        await api<StopResponse>(
          `/api/recorder/${session.session_id}/stop`,
          {
            method: "POST",

            body: JSON.stringify({
              save_test: true,
            }),
          }
        );

      setSession(
        response.session
      );

      setMessage(
        "Recording saved successfully."
      );

      if (response.test?.id) {
        router.push(
          `/tests/${response.test.id}`
        );
      } else {
        router.push(
          "/tests"
        );
      }
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to stop recording."
      );
    } finally {
      setLoading(false);
    }
  }


  // ========================================================
  // CANCEL
  // ========================================================

  async function cancelRecording() {
    if (!session) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      await api(
        `/api/recorder/${session.session_id}`,
        {
          method: "DELETE",
        }
      );

      setSession(null);

      setMessage(
        "Recording cancelled."
      );
    } catch (err) {
      console.error(err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to cancel recording."
      );
    } finally {
      setLoading(false);
    }
  }


  // ========================================================
  // UI
  // ========================================================

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-5xl px-6 py-10">

        <div className="mb-10">

          <button
            onClick={() =>
              router.push(
                "/dashboard"
              )
            }
            className="mb-5 text-sm text-slate-400 hover:text-white"
          >
            ← Dashboard
          </button>

          <h1 className="text-3xl font-bold">
            Scriptless Test Recorder
          </h1>

          <p className="mt-2 text-slate-400">
            Record a real browser workflow
            without writing automation code.
          </p>

        </div>


        {error && (
          <div className="mb-6 rounded-xl border border-red-800 bg-red-950/40 p-4 text-red-300">
            {error}
          </div>
        )}


        {message && (
          <div className="mb-6 rounded-xl border border-emerald-800 bg-emerald-950/40 p-4 text-emerald-300">
            {message}
          </div>
        )}


        {!session ||
        session.status !==
          "recording" ? (

          <form
            onSubmit={
              startRecording
            }
            className="rounded-2xl border border-slate-800 bg-slate-900 p-7"
          >

            <div className="mb-6">

              <label className="mb-2 block text-sm font-medium">
                Project
              </label>

              <select
                value={projectId}
                onChange={(event) =>
                  handleProjectChange(
                    event.target.value
                  )
                }
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3"
              >

                {projects.length ===
                  0 && (
                  <option value="">
                    No projects available
                  </option>
                )}

                {projects.map(
                  (project) => (
                    <option
                      key={
                        project.id
                      }
                      value={
                        project.id
                      }
                    >
                      {project.name}
                    </option>
                  )
                )}

              </select>

            </div>


            <div className="mb-6">

              <label className="mb-2 block text-sm font-medium">
                Test Name
              </label>

              <input
                value={name}
                onChange={(event) =>
                  setName(
                    event.target.value
                  )
                }
                placeholder="Login workflow"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3"
              />

            </div>


            <div className="mb-7">

              <label className="mb-2 block text-sm font-medium">
                Website URL
              </label>

              <input
                value={targetUrl}
                onChange={(event) =>
                  setTargetUrl(
                    event.target.value
                  )
                }
                placeholder="https://your-website.com"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3"
              />

              <p className="mt-2 text-xs text-slate-500">
                Use the actual website or
                application that you want
                to test.
              </p>

            </div>


            <button
              type="submit"
              disabled={
                loading ||
                projects.length === 0
              }
              className="rounded-lg bg-blue-600 px-6 py-3 font-semibold hover:bg-blue-500 disabled:opacity-50"
            >
              {loading
                ? "Launching..."
                : "Start Recording"}
            </button>

          </form>

        ) : (

          <div className="rounded-2xl border border-blue-800 bg-slate-900 p-7">

            <div className="mb-7 flex items-center gap-3">

              <span className="h-3 w-3 animate-pulse rounded-full bg-red-500" />

              <span className="font-semibold text-red-400">
                RECORDING
              </span>

            </div>


            <h2 className="text-2xl font-semibold">
              {session.name}
            </h2>


            <p className="mt-2 break-all text-slate-400">
              {session.target_url}
            </p>


            <div className="mt-7 grid gap-4 sm:grid-cols-2">

              <div className="rounded-xl bg-slate-950 p-5">

                <div className="text-sm text-slate-500">
                  Browser
                </div>

                <div className="mt-1 text-lg font-semibold">
                  {session.browser_active
                    ? "Active"
                    : "Not detected"}
                </div>

              </div>


              <div className="rounded-xl bg-slate-950 p-5">

                <div className="text-sm text-slate-500">
                  Actions Captured
                </div>

                <div className="mt-1 text-2xl font-bold">
                  {session.event_count}
                </div>

              </div>

            </div>


            <div className="mt-7 rounded-xl border border-slate-800 bg-slate-950 p-5">

              <p className="font-semibold">
                Recording instructions
              </p>

              <p className="mt-2 text-sm leading-6 text-slate-400">
                Use the Chromium window
                opened by Test AI. Click,
                type, select options and
                navigate through the
                website exactly as a real
                tester would.
              </p>

            </div>


            <div className="mt-7 flex flex-wrap gap-3">

              <button
                onClick={
                  stopRecording
                }
                disabled={loading}
                className="rounded-lg bg-emerald-600 px-6 py-3 font-semibold hover:bg-emerald-500 disabled:opacity-50"
              >
                {loading
                  ? "Saving..."
                  : "Stop & Save Test"}
              </button>


              <button
                onClick={
                  cancelRecording
                }
                disabled={loading}
                className="rounded-lg border border-slate-700 px-6 py-3 font-semibold hover:bg-slate-800 disabled:opacity-50"
              >
                Cancel Recording
              </button>

            </div>

          </div>
        )}

      </div>
    </main>
  );
}