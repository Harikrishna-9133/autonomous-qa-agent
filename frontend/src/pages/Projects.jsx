
import { useEffect, useState } from "react";
import {
  FolderKanban,
  Plus,
  Globe,
  Trash2,
  RefreshCw,
  ExternalLink,
  X,
} from "lucide-react";

import api from "../api";
import Header from "../components/Header";

function Projects() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    base_url: "",
    description: "",
  });

  // Fetch all projects from FastAPI
  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/api/projects/");

      setProjects(
        Array.isArray(response.data) ? response.data : []
      );
    } catch (err) {
      console.error("Project loading error:", err);
      setError("Unable to load projects. Check your backend connection.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  // Handle form input changes
  const handleChange = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  };

  // Add a new project
  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      setSaving(true);
      setError("");
      setSuccess("");

      await api.post("/api/projects/", formData);

      setSuccess("Project created successfully!");

      setFormData({
        name: "",
        base_url: "",
        description: "",
      });

      setShowForm(false);

      await fetchProjects();
    } catch (err) {
      console.error("Project creation error:", err);

      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Unable to create project. Please check the information."
      );
    } finally {
      setSaving(false);
    }
  };

  // Delete a project
  const handleDelete = async (projectId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this project? This action cannot be undone."
    );

    if (!confirmed) return;

    try {
      setError("");
      setSuccess("");

      await api.delete(`/api/projects/${projectId}`);

      setSuccess("Project deleted successfully!");

      await fetchProjects();
    } catch (err) {
      console.error("Project deletion error:", err);

      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Unable to delete this project."
      );
    }
  };

  return (
    <div className="projects-page">
        {selectedProject && (
  <div className="project-modal-overlay">
    <div className="project-modal">
      <div className="form-heading">
        <h3>Project Details</h3>

        <button
          className="close-form-button"
          onClick={() => setSelectedProject(null)}
        >
          <X size={20} />
        </button>
      </div>

      <div className="detail-item">
        <span>Project ID</span>
        <strong>{selectedProject.id}</strong>
      </div>

      <div className="detail-item">
        <span>Project Name</span>
        <strong>{selectedProject.name}</strong>
      </div>

      <div className="detail-item">
        <span>Website URL</span>
        <a
          href={selectedProject.base_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          {selectedProject.base_url}
        </a>
      </div>

      <div className="detail-item">
        <span>Description</span>
        <strong>
          {selectedProject.description || "No description provided"}
        </strong>
      </div>

      <button
        className="add-project-button"
        onClick={() => setSelectedProject(null)}
      >
        Close
      </button>
    </div>
  </div>
)}
      <Header
        title="Projects Management"
        subtitle="Register and manage websites for automated testing."
      />

      <div className="projects-toolbar">
        <div>
          <h2>Your Projects</h2>
          <p>
            {projects.length} registered project
            {projects.length !== 1 ? "s" : ""}
          </p>
        </div>

        <div className="project-actions">
          <button
            className="refresh-button"
            onClick={fetchProjects}
            disabled={loading}
          >
            <RefreshCw size={16} />
            Refresh
          </button>

          <button
            className="add-project-button"
            onClick={() => {
              setError("");
              setSuccess("");
              setShowForm(true);
            }}
          >
            <Plus size={18} />
            Add Project
          </button>
        </div>
      </div>

      {error && <div className="project-alert error">{error}</div>}
      {success && <div className="project-alert success">{success}</div>}

      {showForm && (
        <div className="project-form-card">
          <div className="form-heading">
            <div>
              <h3>Register New Project</h3>
              <p>Add a website that you own or are authorized to test.</p>
            </div>

            <button
              className="close-form-button"
              onClick={() => setShowForm(false)}
              type="button"
              aria-label="Close form"
            >
              <X size={19} />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <label>Project Name</label>
            <input
              type="text"
              name="name"
              placeholder="Example: My Portfolio"
              value={formData.name}
              onChange={handleChange}
              required
            />

            <label>Website URL</label>
            <input
              type="url"
              name="base_url"
              placeholder="https://example.com"
              value={formData.base_url}
              onChange={handleChange}
              required
            />

            <label>Description</label>
            <textarea
              name="description"
              placeholder="Describe your website or testing project..."
              value={formData.description}
              onChange={handleChange}
              rows={3}
            />

            <button
              className="add-project-button submit-project-button"
              type="submit"
              disabled={saving}
            >
              {saving ? "Creating..." : "Create Project"}
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="loading-message">Loading projects...</div>
      ) : projects.length === 0 ? (
        <div className="empty-projects">
          <FolderKanban size={40} />
          <h3>No Projects Yet</h3>
          <p>Register your first website to start testing.</p>
        </div>
      ) : (
        <div className="projects-grid">
          {projects.map((project) => (
            <div className="project-management-card" key={project.id}>
              <div className="project-card-top">
                <div className="project-avatar">
                  <FolderKanban size={22} />
                </div>

                <span className="project-number">
                  PROJECT #{project.id}
                </span>
              </div>

              <h3>{project.name}</h3>
              <p className="project-id-detail">
                Project ID: {project.id}
              </p>

              <p className="project-description">
                {project.description || "No description provided."}
              </p>

              <a
                className="project-website"
                href={project.base_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Globe size={15} />
                <span>{project.base_url}</span>
                <ExternalLink size={14} />
              </a>

              <div className="project-card-footer">

                <button
                  className="view-project-button"
                  onClick={() => setSelectedProject(project)}
                >
                  View Details
                </button>

                <button
                  className="delete-project-button"
                  onClick={() => handleDelete(project.id)}
                  title="Delete project"
               >
                  <Trash2 size={17} />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Projects;
