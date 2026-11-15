
import { useEffect, useState } from "react";
import {
  Bug,
  RefreshCw,
  Search,
  AlertCircle,
  CheckCircle,
  Clock,
  Eye,
  X,
  Sparkles,
} from "lucide-react";

import api from "../api";
import Header from "../components/Header";

function BugReports() {
  const [bugs, setBugs] = useState([]);
  const [testResults, setTestResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [investigating, setInvestigating] = useState(false);

  const [severityFilter, setSeverityFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  const [selectedBug, setSelectedBug] = useState(null);
  const [selectedResultId, setSelectedResultId] = useState("");

  const [resolutionNotes, setResolutionNotes] = useState("");
  const [savingResolutionNotes, setSavingResolutionNotes] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const getErrorMessage = (err) => {
    const detail = err.response?.data?.detail;

    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg).join(", ");
    }

    return detail || err.message || "Something went wrong.";
  };

  const fetchBugs = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/api/bug-reports/", {
        params: {
          severity: severityFilter || undefined,
          status: statusFilter || undefined,
        },
      });

      setBugs(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };


const fetchTestResults = async () => {
  try {
    const response = await api.get("/api/test-runs/");

    const runResponses = await Promise.all(
      response.data.map(async (run) => {
        const resultResponse = await api.get(
          `/api/test-runs/${run.id}/results`
        );

        return resultResponse.data.map((result) => ({
          ...result,
          run_id: run.id,
        }));
      })
    );

    const allResults = runResponses.flat();

    setTestResults(
      allResults.filter(
        (result) =>
          result.status?.toLowerCase() === "failed"
      )
    );
  } catch (err) {
    setError(getErrorMessage(err));
  }
};


  useEffect(() => {
    fetchBugs();
  }, [severityFilter, statusFilter]);

  useEffect(() => {
    fetchTestResults();
  }, []);

  const handleStatusChange = async (bugId, newStatus) => {
    try {
      setError("");
      setSuccess("");

      await api.patch(
  `/api/bug-reports/${bugId}/status`,
  null,
  {
    params: {
      status: newStatus,
    },
  }
);

      setSuccess(`Bug #${bugId} status updated to ${newStatus}.`);

      await fetchBugs();

      if (selectedBug?.id === bugId) {
        const updatedBug = await api.get(`/api/bug-reports/${bugId}`);
        setSelectedBug(updatedBug.data);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  const handleInvestigate = async () => {
    if (!selectedResultId) {
      setError("Please select a failed test result first.");
      return;
    }

    try {
      setInvestigating(true);
      setError("");
      setSuccess("");

      await api.post(
        `/api/bug-reports/investigate/${selectedResultId}`
      );

      setSuccess("Bug investigation completed successfully.");

      await fetchBugs();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setInvestigating(false);
    }
  };


const handleSaveResolutionNotes = async () => {
  if (!selectedBug) return;

  try {
    setSavingResolutionNotes(true);
    setError("");
    setSuccess("");

    const response = await api.patch(
      `/api/bug-reports/${selectedBug.id}/lifecycle`,
      {
        resolution_notes: resolutionNotes
      }
    );

    setSelectedBug(response.data);
    setResolutionNotes(response.data.resolution_notes || "");

    setSuccess(
      `Resolution notes saved for Bug #${selectedBug.id}.`
    );

    await fetchBugs();
  } catch (err) {
    setError(getErrorMessage(err));
  } finally {
    setSavingResolutionNotes(false);
  }
};


  const selectedBugResult = selectedBug
  ? testResults.find(
      (result) =>
        String(result.id) ===
        String(selectedBug.test_result_id)
    )
  : null;

  const filteredBugs = bugs.filter((bug) => {
    const search = searchTerm.toLowerCase();

    return (
      bug.title?.toLowerCase().includes(search) ||
      bug.description?.toLowerCase().includes(search) ||
      String(bug.id).includes(search)
    );
  });

  const totalBugs = bugs.length;
  const openBugs = bugs.filter(
    (bug) => bug.status?.toLowerCase() === "open"
  ).length;
  const resolvedBugs = bugs.filter(
    (bug) => bug.status?.toLowerCase() === "resolved"
  ).length;
  const mediumBugs = bugs.filter(
    (bug) => bug.severity?.toLowerCase() === "medium"
  ).length;

  const getSeverityClass = (severity) => {
    const value = severity?.toLowerCase();

    if (value === "critical") return "critical";
    if (value === "high") return "high";
    if (value === "medium") return "medium";

    return "low";
  };

  const getStatusClass = (status) => {
    const value = status?.toLowerCase();

    if (value === "resolved") return "resolved";
    if (value === "in_progress") return "in-progress";
    if (value === "open") return "open";

    return "pending";
  };

  return (
    <div className="bug-reports-page">
      <Header
        title="Bug Reports"
        subtitle="Investigate, manage and track website testing issues."
      />

      {error && (
        <div className="bug-message bug-error">
          <AlertCircle size={18} />
          <span>{error}</span>
          <button onClick={() => setError("")}>
            <X size={16} />
          </button>
        </div>
      )}

      {success && (
        <div className="bug-message bug-success">
          <CheckCircle size={18} />
          <span>{success}</span>
          <button onClick={() => setSuccess("")}>
            <X size={16} />
          </button>
        </div>
      )}

      <div className="bug-stats">
        <div className="bug-stat-card">
          <Bug size={22} />
          <div>
            <span>Total Bugs</span>
            <h3>{totalBugs}</h3>
          </div>
        </div>

        <div className="bug-stat-card">
          <AlertCircle size={22} />
          <div>
            <span>Open Bugs</span>
            <h3>{openBugs}</h3>
          </div>
        </div>

        <div className="bug-stat-card">
          <CheckCircle size={22} />
          <div>
            <span>Resolved</span>
            <h3>{resolvedBugs}</h3>
          </div>
        </div>

        <div className="bug-stat-card">
          <Clock size={22} />
          <div>
            <span>Medium Severity</span>
            <h3>{mediumBugs}</h3>
          </div>
        </div>
      </div>

      <div className="bug-toolbar">
        <div className="bug-search">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search bugs..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
        </div>

        <select
          value={severityFilter}
          onChange={(event) => setSeverityFilter(event.target.value)}
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>

        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
        </select>

        <button className="bug-refresh-button" onClick={fetchBugs}>
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      <div className="bug-section">
        <div className="bug-section-header">
          <div>
            <h3>Reported Issues</h3>
            <p>Review detected issues and manage their status.</p>
          </div>
          <span>{filteredBugs.length} issues</span>
        </div>

        {loading ? (
          <p className="bug-empty">Loading bug reports...</p>
        ) : filteredBugs.length === 0 ? (
          <p className="bug-empty">No bug reports found.</p>
        ) : (
          <div className="bug-table-wrapper">
            <table className="bug-table">
              <thead>
                <tr>
                  <th>Bug</th>
                  <th>Severity</th>
                  <th>Status</th>
                  <th>Test Result</th>
                  <th>Created</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {filteredBugs.map((bug) => (
                  <tr key={bug.id}>
                    <td>
                      <div className="bug-title-cell">
                        <strong>{bug.title}</strong>
                        <span>#{bug.id}</span>
                      </div>
                    </td>

                    <td>
                      <span
                        className={`bug-severity ${getSeverityClass(
                          bug.severity
                        )}`}
                      >
                        {bug.severity}
                      </span>
                    </td>

                    <td>
                      <span
                        className={`bug-status ${getStatusClass(
                          bug.status
                        )}`}
                      >
                        {bug.status?.replace("_", " ")}
                      </span>
                    </td>

                    <td>#{bug.test_result_id}</td>

                    <td>
                      {bug.created_at
                        ? new Date(bug.created_at).toLocaleDateString()
                        : "—"}
                    </td>

                    <td>
                      <button
                        className="bug-view-button"
                        onClick={() => {
  setSelectedBug(bug);
  setResolutionNotes(bug.resolution_notes || "");
}}
                      >
                        <Eye size={15} />
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="bug-section">
        <div className="bug-section-header">
          <div>
            <h3>AI Bug Investigation</h3>
            <p>
              Investigate failed test results and generate bug reports.
            </p>
          </div>
          <Sparkles size={21} />
        </div>

        <div className="bug-investigation">
          <div className="bug-investigation-select">
            <label htmlFor="failed-result">
              Select Failed Test Result
            </label>

            <select
              id="failed-result"
              value={selectedResultId}
              onChange={(event) =>
                setSelectedResultId(event.target.value)
              }
            >
              <option value="">Choose a failed result</option>

              {testResults.map((result) => (
                <option key={result.id} value={result.id}>
                  Result #{result.id} — Test Case #{result.test_case_id}
                </option>
              ))}
            </select>
          </div>

          <button
            className="bug-investigate-button"
            onClick={handleInvestigate}
            disabled={investigating || !selectedResultId}
          >
            {investigating ? (
              <>
                <RefreshCw size={16} className="spinning" />
                Investigating...
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Investigate Failure
              </>
            )}
          </button>
        </div>

        {testResults.length === 0 && (
          <p className="bug-empty">
            No failed test results are currently available for investigation.
          </p>
        )}
      </div>

      {selectedBug && (
        <div
          className="bug-modal-overlay"
          onClick={() => setSelectedBug(null)}
        >
          <div
            className="bug-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="bug-modal-header">
              <div>
                <span>BUG #{selectedBug.id}</span>
                <h2>{selectedBug.title}</h2>
              </div>

              <button onClick={() => setSelectedBug(null)}>
                <X size={20} />
              </button>
            </div>

            <div className="bug-modal-content">
              <div className="bug-detail-row">
                <div>
                  <label>Severity</label>
                  <span
                    className={`bug-severity ${getSeverityClass(
                      selectedBug.severity
                    )}`}
                  >
                    {selectedBug.severity}
                  </span>
                </div>

                <div>
                  <label>Status</label>
                  <span
                    className={`bug-status ${getStatusClass(
                      selectedBug.status
                    )}`}
                  >
                    {selectedBug.status?.replace("_", " ")}
                  </span>
                </div>
              </div>

              <div className="bug-detail-block">
                <label>Description</label>
                <p>{selectedBug.description || "No description available."}</p>
              </div>

              <div className="bug-detail-block">
                <label>Root Cause</label>
                <p>{selectedBug.root_cause || "Not identified."}</p>
              </div>

              <div className="bug-detail-block">
                <label>Suggested Fix</label>
                <p>{selectedBug.suggested_fix || "No fix suggested."}</p>
              </div>

             <div className="bug-detail-block">
  <label>Linked Test Result</label>
  <p>Result #{selectedBug.test_result_id}</p>
</div>

{selectedBugResult && (
  <>
    <div className="bug-detail-block">
      <label>Execution Run</label>
      <p>Run #{selectedBugResult.run_id}</p>
    </div>

    <div className="bug-detail-block">
      <label>Actual Execution Result</label>
      <p>
        {selectedBugResult.actual_result ||
          "No execution details available."}
      </p>
    </div>

    <div className="bug-detail-block">
      <label>Error Details</label>
      <p>
        {selectedBugResult.error_message ||
          "No error message recorded."}
      </p>
    </div>

    <div className="bug-detail-block">
      <label>Execution Duration</label>
      <p>
        {selectedBugResult.duration_ms != null
          ? `${selectedBugResult.duration_ms} ms`
          : "Not recorded"}
      </p>
    </div>


<div className="bug-detail-block">
  <label>Browser Screenshot Evidence</label>

  {selectedBugResult.screenshot_path ? (
    <a
      href={`${api.defaults.baseURL}/api/evidence/screenshots/${encodeURIComponent(
        selectedBugResult.screenshot_path.split(/[\\/]/).pop()
      )}`}
      target="_blank"
      rel="noopener noreferrer"
      className="bug-screenshot-link"
    >
      Open Failed Test Screenshot
    </a>
  ) : (
    <p className="screenshot-unavailable">
      Screenshot not available for this test result.
    </p>
  )}
</div>

  </>
)}


<div className="bug-detail-block">
  <label htmlFor="resolution-notes">Resolution Notes</label>

  <textarea
    id="resolution-notes"
    value={resolutionNotes}
    onChange={(event) => setResolutionNotes(event.target.value)}
    placeholder="Describe the investigation progress or solution..."
    rows={4}
  />

  <button
    type="button"
    className="bug-investigate-button"
    onClick={handleSaveResolutionNotes}
    disabled={savingResolutionNotes}
  >
    {savingResolutionNotes
      ? "Saving..."
      : "Save Resolution Notes"}
  </button>
</div>

<div className="bug-detail-block">
  <label>Failure Classification</label>
  <p>{selectedBug.failure_type || "Unknown"}</p>
</div>

<div className="bug-detail-block">
  <label>Affected Component</label>
  <p>{selectedBug.component || "Not identified"}</p>
</div>

<div className="bug-detail-block">
  <label>Reproduction Steps</label>
  <p>{selectedBug.reproduction_steps || "Not available"}</p>
</div>

<div className="bug-detail-block">
  <label>Resolved At</label>
  <p>
    {selectedBug.resolved_at
      ? new Date(selectedBug.resolved_at).toLocaleString()
      : "Not resolved"}
  </p>
</div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default BugReports;
