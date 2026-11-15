
import { useEffect, useState } from "react";
import {
  ClipboardList,
  RefreshCw,
  Search,
  Filter,
  Plus,
  X,
  Eye,
  Trash2,
  Pencil,
} from "lucide-react";

import api from "../api";
import Header from "../components/Header";

function TestCases() {
  const [testCases, setTestCases] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  const [selectedProject, setSelectedProject] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [success, setSuccess] = useState("");
const [showForm, setShowForm] = useState(false);
const [selectedTestCase, setSelectedTestCase] = useState(null);
const [saving, setSaving] = useState(false);
const [editingTestCase, setEditingTestCase] = useState(null);

const [formData, setFormData] = useState({
  project_id: "",
  title: "",
  description: "",
  steps: "",
  expected_result: "",
  priority: "medium",
});

  const fetchData = async () => {
    try {
      setLoading(true);
      setError("");

      const [testCaseResponse, projectResponse] = await Promise.all([
        api.get("/api/test-cases/"),
        api.get("/api/projects/"),
      ]);

      setTestCases(testCaseResponse.data);
      setProjects(projectResponse.data);

} catch (err) {
  console.error("Error creating test case:", err);

  const detail = err.response?.data?.detail;

  console.log(
    "Backend validation response:",
    JSON.stringify(err.response?.data, null, 2)
  );

  let errorMessage = "Unable to create test case.";

  if (typeof detail === "string") {
    errorMessage = detail;
  } else if (Array.isArray(detail)) {
    errorMessage = detail
      .map((item) => item.msg || JSON.stringify(item))
      .join(", ");
  } else if (detail) {
    errorMessage = JSON.stringify(detail);
  }

  setError(errorMessage);
}

    finally {
      setLoading(false);
    }
  };

  const handleFormChange = (e) => {
  const { name, value } = e.target;

  setFormData((previous) => ({
    ...previous,
    [name]: value,
  }));
};


const handleSubmit = async (e) => {
  e.preventDefault();

  try {
    setSaving(true);
    setError("");
    setSuccess("");

    const payload = {
      ...formData,
      project_id: Number(formData.project_id),
    };

    if (editingTestCase) {
      await api.put(
        `/api/test-cases/${editingTestCase.id}`,
        payload
      );

      setSuccess("Test case updated successfully!");
    } else {
      await api.post("/api/test-cases/", payload);

      setSuccess("Test case created successfully!");
    }

    setFormData({
      project_id: "",
      title: "",
      description: "",
      steps: "",
      expected_result: "",
      priority: "medium",
    });

    setEditingTestCase(null);
    setShowForm(false);

    await fetchData();

  } catch (err) {
    console.error("Error saving test case:", err);

    const detail = err.response?.data?.detail;

    setError(
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((item) => item.msg).join(", ")
          : "Unable to save test case. Please try again."
    );

  } finally {
    setSaving(false);
  }
};

const handleEdit = (testCase) => {
  setEditingTestCase(testCase);

  setFormData({
    project_id: String(testCase.project_id),
    title: testCase.title || "",
    description: testCase.description || "",
    steps: testCase.steps || "",
    expected_result: testCase.expected_result || "",
    priority: testCase.priority?.toLowerCase() || "medium",
  });

  setError("");
  setSuccess("");
  setShowForm(true);
};

const handleDelete = async (testCaseId) => {
  const confirmed = window.confirm(
    "Are you sure you want to delete this test case? This action cannot be undone."
  );

  if (!confirmed) return;

  try {
    setError("");
    setSuccess("");

    await api.delete(`/api/test-cases/${testCaseId}`);

    setSuccess("Test case deleted successfully!");

    setSelectedTestCase(null);

    await fetchData();
  } catch (err) {
    console.error("Error deleting test case:", err);

    setError(
      err.response?.data?.detail ||
      "Unable to delete test case. Please try again."
    );
  }
};

  useEffect(() => {
    fetchData();
  }, []);

  const filteredTestCases = testCases.filter((testCase) => {
    const matchesProject =
      selectedProject === "all" ||
      String(testCase.project_id) === selectedProject;

    const matchesSearch =
      testCase.title?.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesProject && matchesSearch;
  });

  return (
    <div className="test-cases-page">
      <Header
        title="Test Case Management"
        subtitle="Create, organize, and manage automated test cases."
      />

      <div className="test-cases-toolbar">
  <div>
    <h2>Your Test Cases</h2>
    <p>
      {filteredTestCases.length} test cases displayed
    </p>
  </div>

  <div className="project-actions">
    <button
      className="refresh-button"
      onClick={fetchData}
      disabled={loading}
    >
      <RefreshCw size={16} />
      Refresh
    </button>

<button
  type="button"
  className="add-project-button"
  onClick={() => {
    console.log("Add Test Case button clicked");
    setError("");
    setSuccess("");
    setShowForm(true);
  }}
>
  <Plus size={18} />
  Add Test Case
</button>
  </div>
</div>



{showForm && (
  <div className="test-case-form-card">
    <div className="form-heading">
      <h3>
  {editingTestCase ? "Edit Test Case" : "Create New Test Case"}
</h3>

      <button
        type="button"
        className="close-form-button"
        onClick={() => setShowForm(false)}
      >
        <X size={20} />
      </button>
    </div>

    <form onSubmit={handleSubmit}>
      <label>Project</label>
      <select
        name="project_id"
        value={formData.project_id}
        onChange={handleFormChange}
        required
      >
        <option value="">Select Project</option>
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
          </option>
        ))}
      </select>

      <label>Test Case Title</label>
      <input
        name="title"
        value={formData.title}
        onChange={handleFormChange}
        placeholder="Enter test case title"
        required
      />

      <label>Description</label>
      <textarea
        name="description"
        value={formData.description}
        onChange={handleFormChange}
        placeholder="Describe the test case"
        required
      />

      <label>Test Steps</label>
      <textarea
        name="steps"
        value={formData.steps}
        onChange={handleFormChange}
        placeholder="Enter test steps"
        required
      />

      <label>Expected Result</label>
      <textarea
        name="expected_result"
        value={formData.expected_result}
        onChange={handleFormChange}
        placeholder="Enter expected result"
        required
      />

      <label>Priority</label>
      <select
        name="priority"
        value={formData.priority}
        onChange={handleFormChange}
      >
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
      </select>

      <button
        type="submit"
        className="add-project-button"
        disabled={saving}
      >
        {saving
  ? "Saving..."
  : editingTestCase
    ? "Update Test Case"
    : "Create Test Case"}
      </button>
    </form>
  </div>
)}

      <div className="test-case-filters">
        <div className="test-case-search">
          <Search size={17} />
          <input
            type="text"
            placeholder="Search test cases..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="test-case-project-filter">
          <Filter size={17} />
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
          >
            <option value="all">All Projects</option>

            {projects.map((project) => (
              <option key={project.id} value={String(project.id)}>
                {project.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {loading ? (
        <div className="empty-test-cases">Loading test cases...</div>
      ) : filteredTestCases.length === 0 ? (
        <div className="empty-test-cases">
          <ClipboardList size={35} />
          <h3>No Test Cases Found</h3>
          <p>Try changing your search or project filter.</p>
        </div>
      ) : (
        <div className="test-cases-table-container">
          <table className="test-cases-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Test Case</th>
                <th>Project</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {filteredTestCases.map((testCase) => {
                const project = projects.find(
                  (item) => item.id === testCase.project_id
                );

                return (
                  <tr key={testCase.id}>
                    <td>#{testCase.id}</td>
                    <td>
                      <strong>{testCase.title}</strong>
                      <p className="test-case-description">
                        {testCase.description || "No description"}
                      </p>
                    </td>
                    <td>{project?.name || `Project #${testCase.project_id}`}</td>
                    <td>
                      <span className={`priority-badge ${testCase.priority?.toLowerCase()}`}>
                        {testCase.priority}
                      </span>
                    </td>
                    <td>
                      <span className="test-status-badge">
                        {testCase.status}
                      </span>
                    </td>
                    <td>
  <button
    type="button"
    className="view-project-button"
    onClick={() => setSelectedTestCase(testCase)}
  >
    <Eye size={15} />
    View Details
  </button>
  <button
  type="button"
  className="edit-test-case-button"
  onClick={() => handleEdit(testCase)}
  title="Edit test case"
>
  <Pencil size={15} />
  Edit
</button>
  <button
  type="button"
  className="delete-project-button"
  onClick={() => handleDelete(testCase.id)}
  title="Delete test case"
>
  <Trash2 size={15} />
  Delete
</button>
</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {selectedTestCase && (
  <div className="project-modal-overlay">
    <div className="project-modal">
      <div className="form-heading">
        <h3>Test Case Details</h3>

        <button
          type="button"
          className="close-form-button"
          onClick={() => setSelectedTestCase(null)}
        >
          <X size={20} />
        </button>
      </div>

      <div className="detail-item">
        <span>Test Case ID</span>
        <strong>#{selectedTestCase.id}</strong>
      </div>

      <div className="detail-item">
        <span>Test Case Title</span>
        <strong>{selectedTestCase.title}</strong>
      </div>

      <div className="detail-item">
        <span>Project</span>
        <strong>
          {projects.find(
            (p) => p.id === selectedTestCase.project_id
          )?.name || `Project #${selectedTestCase.project_id}`}
        </strong>
      </div>

      <div className="detail-item">
        <span>Description</span>
        <strong>{selectedTestCase.description || "Not provided"}</strong>
      </div>

      <div className="detail-item">
        <span>Test Steps</span>
        <strong>{selectedTestCase.steps || "Not provided"}</strong>
      </div>

      <div className="detail-item">
        <span>Expected Result</span>
        <strong>{selectedTestCase.expected_result || "Not provided"}</strong>
      </div>

      <div className="detail-item">
        <span>Priority</span>
        <strong>{selectedTestCase.priority}</strong>
      </div>

      <div className="detail-item">
        <span>Status</span>
        <strong>{selectedTestCase.status}</strong>
      </div>

      <button
        type="button"
        className="add-project-button"
        onClick={() => setSelectedTestCase(null)}
      >
        Close
      </button>
    </div>
  </div>
)}
    </div>

  );
}

export default TestCases;
