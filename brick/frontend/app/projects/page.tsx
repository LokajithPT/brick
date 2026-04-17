"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getProjects, createProject, deleteProject, type Project } from "@/lib/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [newProjectName, setNewProjectName] = useState("");
  const [creating, setCreating] = useState(false);
  const router = useRouter();

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await getProjects();
      setProjects(data.projects || []);
    } catch (err) {
      console.error("Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    setCreating(true);
    try {
      const result = await createProject(newProjectName.trim());
      setProjects(prev => [result.project, ...prev]);
      setNewProjectName("");
      router.push(`/projects/${result.project.id}`);
    } catch (err) {
      console.error("Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (projectId: string) => {
    if (!confirm("Delete this project and all its documents?")) return;

    try {
      await deleteProject(projectId);
      setProjects(prev => prev.filter(p => p.id !== projectId));
    } catch (err) {
      console.error("Failed to delete project");
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-4xl mx-auto p-8">
        <div className="flex items-center gap-4 mb-8">
          <Link href="/" className="p-2 hover:bg-gray-800 rounded-lg">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Link>
          <h1 className="text-2xl font-bold">Projects</h1>
        </div>

        <form onSubmit={handleCreate} className="mb-8">
          <div className="flex gap-3">
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="New project name (e.g., Marlette Residence)"
              className="flex-1 p-4 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={creating}
            />
            <button
              type="submit"
              disabled={creating || !newProjectName.trim()}
              className="px-6 py-4 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg font-medium"
            >
              {creating ? "Creating..." : "Create Project"}
            </button>
          </div>
        </form>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent" />
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <p>No projects yet. Create one above to get started.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {projects.map(project => (
              <div
                key={project.id}
                className="bg-gray-800 rounded-lg p-6 flex items-center justify-between"
              >
                <div>
                  <Link
                    href={`/projects/${project.id}`}
                    className="text-xl font-semibold hover:text-blue-400 transition"
                  >
                    {project.name}
                  </Link>
                  <p className="text-gray-400 text-sm mt-1">
                    {project.documents?.length || 0} documents · Created {new Date(project.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Link
                    href={`/projects/${project.id}`}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm"
                  >
                    Open
                  </Link>
                  <button
                    onClick={() => handleDelete(project.id)}
                    className="p-2 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-red-400"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
