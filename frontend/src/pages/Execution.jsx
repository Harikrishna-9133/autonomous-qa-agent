
import { useEffect, useState } from "react";
import {
  Play,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  ClipboardList,
  FolderKanban,
  AlertCircle,
} from "lucide-react";

import api from "../api";
import Header from "../components/Header";

function Execution() {
  const [projects, setProjects] = useState([]);
  const [testCases, setTestCases] = useState([]);
  const [runs, setRuns] = useState([]);

  const [selectedProject, setSelectedProject] = useState("");
  const [selectedRun, setSelectedRun] = useState(null);
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState(null);

  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const getErrorMessage = (err) => {
    const detail = err.response?.data?.detail;

    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg).join(", ");
    }

    return detail || err.message || "Something went wrong.";
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      setError("");

      const [projectResponse, caseResponse, runResponse] =
        await Promise.all([
          api.get("/api/projects/"),
          api.get("/api/test-cases/"),
          api.get("/api/test-runs/"),
        ]);

      setProjects(projectResponse.data);
      setTestCases(caseResponse.data);
      setRuns(runResponse.data);

      if (
        !selectedProject &&
        projectResponse.data.length > 0
      ) {
        setSelectedProject(String(projectResponse.data[0].id));
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const fetchRunDetails = async (runId) => {
    try {
      setError("");

      const [resultResponse, summaryResponse] = await Promise.all([
        api.get(`/api/test-runs/${runId}/results`),
        api.get(`/api/test-runs/${runId}/summary`),
      ]);

      setResults(resultResponse.data);
      setSummary(summaryResponse.data);
      setSelectedRun(runId);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const projectTestCases = testCases.filter(
    (testCase) =>
      String(testCase.project_id) === String(selectedProject)
  );

  const activeTestCases = projectTestCases.filter(
    (testCase) => testCase.status?.toLowerCase() !== "inactive"
  );

  const projectRuns = runs.filter(
    (run) => String(run.project_id) === String(selectedProject)
  );

  const handleExecute = async () => {
    if (!selectedProject) {
      setError("Please select a project first.");
      return;
    }

    if (activeTestCases.length === 0) {
      setError("This project has no active test cases to execute.");
      return;
    }

    try {
      setExecuting(true);
      setError("");
      setSuccess("");
      setResults([]);
      setSummary(null);
      setSelectedRun(null);

      // Step 1: Create a new test run.
      const runResponse = await api.post("/api/test-runs/", {
        project_id: Number(selectedProject),
      });

      const runId = runResponse.data.id;

      // Step 2: Execute all active test cases in this project.
      const executionResponse = await api.post(
        `/api/test-runs/${runId}/execute-generated-suite`
      );

      setSuccess(
        `Execution finished. Run #${runId} status: ${
          executionResponse.data.status || "completed"
        }.`
      );

      // Step 3: Load the saved results and summary.
      await fetchRunDetails(runId);

      // Step 4: Refresh the run history.
      const runHistoryResponse = await api.get("/api/test-runs/");
      setRuns(runHistoryResponse.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setExecuting(false);
    }
  };

  const getStatusClass = (status) => {
    const value = status?.toLowerCase();

    if (value === "passed" || value === "completed") return "passed";
    if (value === "failed") return "failed";
    if (value === "skipped") return "skipped";

    return "pending";
  };

  if (loading) {
    return (
      <div className="execution-page">
        <Header
          title="Test Execution"
          subtitle="Run and monitor your automated tests."
        />
        <p>Loading test execution data...</p>
      </div>
    );
  }

  return (
    <div className="execution-page">
      <Header
        title="Test Execution"
        subtitle="Execute test suites and monitor their results."
      />

      {error && (
        <div className="execution-message error-message">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="execution-message success-message">
          <CheckCircle size={18} />
          <span>{success}</span>
        </div>
      )}

      <div className="execution-toolbar">
        <div className="project-selector">
          <label htmlFor="execution-project">
            <FolderKanban size={16} />
            Select Project
          </label>

          <select
            id="execution-project"
            value={selectedProject}
            onChange={(event) => {
              setSelectedProject(event.target.value);
              setSelectedRun(null);
              setResults([]);
              setSummary(null);
              setError("");
              setSuccess("");
            }}
          >
            <option value="">Choose a project</option>

            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        <button
          className="run-button"
          onClick={handleExecute}
          disabled={
            executing ||
            !selectedProject ||
            activeTestCases.length === 0
          }
        >
          {executing ? (
            <>
              <RefreshCw size={17} className="spinning" />
              Executing Tests...
            </>
          ) : (
            <>
              <Play size={17} />
              Run All Active Tests
            </>
          )}
        </button>
      </div>

      <div className="execution-stats">
        <div className="execution-stat-card">
          <ClipboardList size={21} />
          <div>
            <span>Total Test Cases</span>
            <h3>{projectTestCases.length}</h3>
          </div>
        </div>

        <div className="execution-stat-card">
          <CheckCircle size={21} />
          <div>
            <span>Active Test Cases</span>
            <h3>{activeTestCases.length}</h3>
          </div>
        </div>

        <div className="execution-stat-card">
          <Clock size={21} />
          <div>
            <span>Total Runs</span>
            <h3>{projectRuns.length}</h3>
          </div>
        </div>
      </div>

      <div className="execution-section">
        <h3>Test Cases Ready for Execution</h3>
        <p className="execution-description">
          All active test cases belonging to the selected project will
          be included in the next run.
        </p>

        {activeTestCases.length === 0 ? (
          <p className="empty-state">
            No active test cases found for this project.
          </p>
        ) : (
          <div className="execution-table-wrapper">
            <table className="execution-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Test Case</th>
                  <th>Priority</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                {activeTestCases.map((testCase) => (
                  <tr key={testCase.id}>
                    <td>#{testCase.id}</td>
                    <td>{testCase.title}</td>
                    <td>{testCase.priority}</td>
                    <td>
                      <span className="execution-status active">
                        {testCase.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {summary && (
        <div className="execution-section">
          <h3>Execution Summary — Run #{selectedRun}</h3>

          <div className="execution-stats">
            <div className="execution-stat-card">
              <ClipboardList size={21} />
              <div>
                <span>Total Tests</span>
                <h3>{summary.total_tests ?? 0}</h3>
              </div>
            </div>

            <div className="execution-stat-card">
              <CheckCircle size={21} />
              <div>
                <span>Passed</span>
                <h3>{summary.passed ?? 0}</h3>
              </div>
            </div>

            <div className="execution-stat-card">
              <XCircle size={21} />
              <div>
                <span>Failed</span>
                <h3>{summary.failed ?? 0}</h3>
              </div>
            </div>

            <div className="execution-stat-card">
              <Clock size={21} />
              <div>
                <span>Skipped</span>
                <h3>{summary.skipped ?? 0}</h3>
              </div>
            </div>
          </div>

          <h4>Test Results</h4>

          <div className="execution-table-wrapper">
            <table className="execution-table">
              <thead>
                <tr>
                  <th>Test Case ID</th>
                  <th>Status</th>
                  <th>Actual Result</th>
                  <th>Duration</th>
                </tr>
              </thead>

              <tbody>
                {results.map((result) => (
                  <tr key={result.id}>
                    <td>#{result.test_case_id}</td>
                    <td>
                      <span
                        className={`execution-status ${getStatusClass(
                          result.status
                        )}`}
                      >
                        {result.status}
                      </span>
                    </td>
                    <td>
                      {result.actual_result ||
                        result.error_message ||
                        "No details available"}
                    </td>
                    <td>
                      {result.duration_ms != null
                        ? `${result.duration_ms} ms`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="execution-section">
        <h3>Recent Execution History</h3>

        {projectRuns.length === 0 ? (
          <p className="empty-state">
            No execution history for this project yet.
          </p>
        ) : (
          <div className="execution-table-wrapper">
            <table className="execution-table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Status</th>
                  <th>Started At</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {projectRuns.map((run) => (
                  <tr key={run.id}>
                    <td>#{run.id}</td>
                    <td>
                      <span
                        className={`execution-status ${getStatusClass(
                          run.status
                        )}`}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td>
                      {run.started_at
                        ? new Date(run.started_at).toLocaleString()
                        : "—"}
                    </td>
                    <td>
                      <button
                        className="view-run-button"
                        onClick={() => fetchRunDetails(run.id)}
                      >
                        View Results
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Execution;
