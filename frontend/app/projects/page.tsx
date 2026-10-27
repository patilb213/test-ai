"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  FolderKanban,
  Plus,
  X,
  ExternalLink,
  Loader2,
  Globe,
} from "lucide-react";

import Navbar from "../../components/Navbar";
import Sidebar from "../../components/Sidebar";
import { api } from "../../lib/api";
import { Project } from "../../types";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [showForm, setShowForm] = useState(false);

  const [name, setName] = useState("");
  const [targetUrl, setTargetUrl] = useState("");
  const [description, setDescription] = useState("");

  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  async function loadProjects() {
    try {
      setLoading(true);
      setError("");

      const result = await api("/api/projects");

      setProjects(result.projects || []);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load projects"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadProjects();
  }, []);

  async function handleCreateProject(
    e: FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();

    setError("");
    setCreating(true);

    try {
      const query = new URLSearchParams({
        name,
        target_url: targetUrl,
        description,
      });

      await api(`/api/projects?${query.toString()}`, {
        method: "POST",
      });

      setName("");
      setTargetUrl("");
      setDescription("");
      setShowForm(false);

      await loadProjects();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create project"
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#07090d] text-white">
      <Navbar />
      <Sidebar />

      <main className="ml-60 pt-16">
        <div className="p-8">

          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">
                Projects
              </h1>

              <p className="mt-2 text-sm text-gray-400">
                Manage your web testing projects
              </p>
            </div>

            <button
              onClick={() => {
                setShowForm(true);
                setError("");
              }}
              className="flex items-center gap-2 rounded-xl bg-purple-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-purple-400"
            >
              <Plus size={18} />
              New Project
            </button>
          </div>

          {/* Error */}
          {error && (
            <div className="mt-6 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Create Form */}
          {showForm && (
            <div className="mt-8 rounded-2xl border border-white/10 bg-[#0d1117] p-6">

              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold">
                    Create New Project
                  </h2>

                  <p className="mt-1 text-sm text-gray-500">
                    Add the application you want to test
                  </p>
                </div>

                <button
                  onClick={() => setShowForm(false)}
                  className="rounded-lg p-2 text-gray-400 hover:bg-white/5 hover:text-white"
                >
                  <X size={20} />
                </button>
              </div>

              <form
                onSubmit={handleCreateProject}
                className="space-y-5"
              >

                <div>
                  <label className="mb-2 block text-sm text-gray-300">
                    Project Name
                  </label>

                  <input
                    type="text"
                    value={name}
                    onChange={(e) =>
                      setName(e.target.value)
                    }
                    placeholder="My Web Application"
                    required
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none placeholder:text-gray-600 focus:border-purple-500"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm text-gray-300">
                    Target URL
                  </label>

                  <input
                    type="url"
                    value={targetUrl}
                    onChange={(e) =>
                      setTargetUrl(e.target.value)
                    }
                    placeholder="https://example.com"
                    required
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none placeholder:text-gray-600 focus:border-purple-500"
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm text-gray-300">
                    Description
                  </label>

                  <textarea
                    value={description}
                    onChange={(e) =>
                      setDescription(e.target.value)
                    }
                    placeholder="Describe your testing project..."
                    rows={3}
                    className="w-full resize-none rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none placeholder:text-gray-600 focus:border-purple-500"
                  />
                </div>

                <div className="flex justify-end gap-3">

                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="rounded-xl border border-white/10 px-5 py-3 text-sm text-gray-300 hover:bg-white/5"
                  >
                    Cancel
                  </button>

                  <button
                    type="submit"
                    disabled={creating}
                    className="flex items-center gap-2 rounded-xl bg-purple-500 px-5 py-3 text-sm font-semibold hover:bg-purple-400 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {creating ? (
                      <>
                        <Loader2
                          size={17}
                          className="animate-spin"
                        />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Plus size={17} />
                        Create Project
                      </>
                    )}
                  </button>

                </div>
              </form>
            </div>
          )}

          {/* Projects */}
          <div className="mt-8">

            {loading ? (
              <div className="flex min-h-48 items-center justify-center rounded-2xl border border-white/10 bg-[#0d1117]">
                <Loader2
                  size={28}
                  className="animate-spin text-purple-400"
                />
              </div>
            ) : projects.length === 0 ? (

              <div className="flex min-h-72 flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 bg-[#0d1117] text-center">

                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-purple-500/10 text-purple-400">
                  <FolderKanban size={27} />
                </div>

                <h2 className="mt-5 text-lg font-semibold">
                  No projects yet
                </h2>

                <p className="mt-2 max-w-md text-sm text-gray-500">
                  Create your first project to start
                  recording and running automated tests.
                </p>

                <button
                  onClick={() => setShowForm(true)}
                  className="mt-6 flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black hover:bg-gray-200"
                >
                  <Plus size={17} />
                  Create Project
                </button>

              </div>

            ) : (

              <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">

                {projects.map((project) => (
                  <div
                    key={project.id}
                    className="rounded-2xl border border-white/10 bg-[#0d1117] p-6 transition hover:border-purple-500/30"
                  >

                    <div className="flex items-start justify-between">

                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400">
                        <FolderKanban size={22} />
                      </div>

                      <a
                        href={project.target_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded-lg p-2 text-gray-500 hover:bg-white/5 hover:text-white"
                        title="Open target URL"
                      >
                        <ExternalLink size={17} />
                      </a>

                    </div>

                    <h2 className="mt-5 text-lg font-semibold">
                      {project.name}
                    </h2>

                    {project.description && (
                      <p className="mt-2 text-sm leading-6 text-gray-500">
                        {project.description}
                      </p>
                    )}

                    <div className="mt-5 flex items-center gap-2 border-t border-white/5 pt-4 text-xs text-gray-500">
                      <Globe size={14} />
                      <span className="truncate">
                        {project.target_url}
                      </span>
                    </div>

                  </div>
                ))}

              </div>
            )}

          </div>
        </div>
      </main>
    </div>
  );
}