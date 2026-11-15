
import { useEffect, useState } from "react";
import {
  FileBarChart,
  RefreshCw,
  Search,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Download,
  Bug,
  ClipboardList,
} from "lucide-react";

import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from "recharts";

import api from "../api";
import Header from "../components/Header";

function QAReports() {
  const [projects, setProjects] = useState([]);
  const [runs, setRuns] = useState([]);

  const [selectedProject, setSelectedProject] = useState("");
  const [selectedRun, setSelectedRun] = useState("");

  const [report, setReport] = useState(null);
  // Test execution comparison
const [compareRunA, setCompareRunA] = useState("");
const [compareRunB, setCompareRunB] = useState("");
const [comparison, setComparison] = useState(null);
const [comparing, setComparing] = useState(false);
const [comparisonError, setComparisonError] = useState("");

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
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

      const [projectResponse, runResponse] = await Promise.all([
        api.get("/api/projects/"),
        api.get("/api/test-runs/"),
      ]);

      setProjects(projectResponse.data);
      setRuns(runResponse.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const projectRuns = runs.filter(
    (run) =>
      String(run.project_id) === String(selectedProject)
  );

  const handleProjectChange = (event) => {
    setSelectedProject(event.target.value);
    setSelectedRun("");
    setReport(null);
    setError("");
    setSuccess("");
  };

  const handleGenerateReport = async () => {
    if (!selectedProject || !selectedRun) {
      setError("Please select both a project and an execution run.");
      return;
    }

    try {
      setGenerating(true);
      setError("");
      setSuccess("");
      setReport(null);

      const response = await api.get(
        `/api/qa-reports/projects/${selectedProject}/runs/${selectedRun}`
      );

      setReport(response.data);
      setSuccess("QA report generated successfully.");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  };

const handleGenerateLatestReport = async () => {
  const finishedRuns = runs
    .filter(
      (run) => run.status?.toLowerCase() !== "running"
    )
    .sort((a, b) => {
      const dateA = new Date(a.started_at || 0).getTime();
      const dateB = new Date(b.started_at || 0).getTime();

      return dateB - dateA || b.id - a.id;
    });

  const latestRun = finishedRuns[0];

  if (!latestRun) {
    setError("No completed or failed execution runs are available.");
    return;
  }

  try {
    setGenerating(true);
    setError("");
    setSuccess("");
    setReport(null);

    setSelectedProject(String(latestRun.project_id));
    setSelectedRun(String(latestRun.id));

    const response = await api.get(
      `/api/qa-reports/projects/${latestRun.project_id}/runs/${latestRun.id}`
    );

    setReport(response.data);

    setSuccess(
      `Latest autonomous QA report generated successfully for Run #${latestRun.id}.`
    );
  } catch (err) {
    setError(getErrorMessage(err));
  } finally {
    setGenerating(false);
  }
};


const handleCompareRuns = async () => {
  if (!selectedProject || !compareRunA || !compareRunB) {
    setComparisonError("Please select two execution runs.");
    return;
  }

  if (compareRunA === compareRunB) {
    setComparisonError("Please select two different execution runs.");
    return;
  }

  try {
    setComparing(true);
    setComparisonError("");
    setComparison(null);

    const [responseA, responseB] = await Promise.all([
      api.get(
        `/api/qa-reports/projects/${selectedProject}/runs/${compareRunA}`
      ),
      api.get(
        `/api/qa-reports/projects/${selectedProject}/runs/${compareRunB}`
      ),
    ]);

    const reportA = responseA.data;
    const reportB = responseB.data;

    const testsA = reportA.test_details || [];
    const testsB = reportB.test_details || [];

    const mapA = new Map(
      testsA.map((test) => [
        String(test.test_case_id),
        test,
      ])
    );

    const mapB = new Map(
      testsB.map((test) => [
        String(test.test_case_id),
        test,
      ])
    );

    const regressions = [];
    const fixed = [];
    const newTests = [];
    const removedTests = [];

    for (const [id, testB] of mapB) {
      const testA = mapA.get(id);

      if (!testA) {
        newTests.push(testB);
      } else {
        const oldStatus = testA.status?.toLowerCase();
        const newStatus = testB.status?.toLowerCase();

        if (
          oldStatus === "passed" &&
          newStatus === "failed"
        ) {
          regressions.push({ before: testA, after: testB });
        }

        if (
          oldStatus === "failed" &&
          newStatus === "passed"
        ) {
          fixed.push({ before: testA, after: testB });
        }
      }
    }

    for (const [id, testA] of mapA) {
      if (!mapB.has(id)) {
        removedTests.push(testA);
      }
    }

    setComparison({
      reportA,
      reportB,
      regressions,
      fixed,
      newTests,
      removedTests,
      passRateChange:
        Number(reportB.execution_summary.pass_percentage || 0) -
        Number(reportA.execution_summary.pass_percentage || 0),
    });

  } catch (err) {
    setComparisonError(getErrorMessage(err));
  } finally {
    setComparing(false);
  }
};


  const handlePrintReport = () => {
    window.print();
  };

  const getStatusClass = (status) => {
    const value = status?.toLowerCase();

    if (value === "passed" || value === "completed") {
      return "qa-passed";
    }

    if (value === "failed") {
      return "qa-failed";
    }

    if (value === "skipped") {
      return "qa-skipped";
    }

    return "qa-pending";
  };

  const chartData = report
    ? [
        { name: "Passed", value: report.execution_summary.passed },
        { name: "Failed", value: report.execution_summary.failed },
        { name: "Skipped", value: report.execution_summary.skipped },
      ].filter((item) => item.value > 0)
    : [];

  const chartColors = ["#22c55e", "#ef4444", "#f59e0b"];

  if (loading) {
    return (
      <div className="qa-reports-page">
        <Header
          title="QA Reports"
          subtitle="Generate and review detailed quality reports."
        />
        <p>Loading projects and execution history...</p>
      </div>
    );
  }

  return (
    <div className="qa-reports-page">
      <Header
        title="QA Reports"
        subtitle="Generate and review detailed software quality reports."
      />

      {error && (
        <div className="qa-message qa-error">
          <AlertCircle size={18} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="qa-message qa-success">
          <CheckCircle size={18} />
          <span>{success}</span>
        </div>
      )}

      <div className="qa-generator-section">
        <div className="qa-generator-heading">
          <div>
            <h3>Generate QA Report</h3>
            <p>
              Select a project and its completed test execution run.
            </p>
          </div>

          <FileBarChart size={25} />
        </div>

        <div className="qa-generator-controls">
          <div className="qa-form-group">
            <label htmlFor="qa-project">Select Project</label>

            <select
              id="qa-project"
              value={selectedProject}
              onChange={handleProjectChange}
            >
              <option value="">Choose a project</option>

              {projects.map((project) => (
  <option key={project.id} value={project.id}>
    {project.name} (Project #{project.id})
  </option>
))}
            </select>
          </div>

          <div className="qa-form-group">
            <label htmlFor="qa-run">Select Execution Run</label>

            <select
              id="qa-run"
              value={selectedRun}
              onChange={(event) => {
                setSelectedRun(event.target.value);
                setReport(null);
                setError("");
                setSuccess("");
              }}
              disabled={!selectedProject}
            >
              <option value="">Choose an execution run</option>

              {projectRuns.map((run) => (
                <option key={run.id} value={run.id}>
                  Run #{run.id} — {run.status}
                </option>
              ))}
            </select>
          </div>

          <button
            className="qa-generate-button"
            onClick={handleGenerateReport}
            disabled={generating || !selectedProject || !selectedRun}
          >
            {generating ? (
              <>
                <RefreshCw size={17} className="spinning" />
                Generating...
              </>
            ) : (
              <>
                <Search size={17} />
                Generate Report
              </>
            )}
          </button>

<button
  type="button"
  className="qa-latest-report-button"
  onClick={handleGenerateLatestReport}
  disabled={generating || runs.length === 0}
>
  {generating ? (
    <>
      <RefreshCw size={17} className="spinning" />
      Generating...
    </>
  ) : (
    <>
      <FileBarChart size={17} />
      Generate Latest Autonomous Report
    </>
  )}
</button>

        </div>

        {selectedProject && projectRuns.length === 0 && (
          <p className="qa-empty">
            No execution runs found for this project.
          </p>
        )}
      </div>


{/* Test Execution History Comparison */}
<div className="qa-comparison-section">
  <div className="qa-generator-heading">
    <div>
      <h3>Test Execution Comparison</h3>
      <p>
        Compare two execution runs and identify regressions,
        fixed tests and newly added tests.
      </p>
    </div>

    <FileBarChart size={25} />
  </div>

  <div className="qa-comparison-controls">
    <div className="qa-form-group">
      <label htmlFor="compare-run-a">Previous Execution</label>

      <select
        id="compare-run-a"
        value={compareRunA}
        onChange={(event) => {
          setCompareRunA(event.target.value);
          setComparison(null);
          setComparisonError("");
        }}
        disabled={!selectedProject || comparing}
      >
        <option value="">Select previous run</option>

        {projectRuns.map((run) => (
          <option key={run.id} value={run.id}>
            Run #{run.id} — {run.status}
          </option>
        ))}
      </select>
    </div>

    <div className="qa-form-group">
      <label htmlFor="compare-run-b">Latest Execution</label>

      <select
        id="compare-run-b"
        value={compareRunB}
        onChange={(event) => {
          setCompareRunB(event.target.value);
          setComparison(null);
          setComparisonError("");
        }}
        disabled={!selectedProject || comparing}
      >
        <option value="">Select latest run</option>

        {projectRuns.map((run) => (
          <option key={run.id} value={run.id}>
            Run #{run.id} — {run.status}
          </option>
        ))}
      </select>
    </div>

    <button
      className="qa-compare-button"
      onClick={handleCompareRuns}
      disabled={
        comparing ||
        !selectedProject ||
        !compareRunA ||
        !compareRunB
      }
    >
      {comparing ? (
        <>
          <RefreshCw size={17} className="spinning" />
          Comparing...
        </>
      ) : (
        <>
          <Search size={17} />
          Compare Runs
        </>
      )}
    </button>
  </div>

  {comparisonError && (
    <div className="qa-message qa-error">
      <AlertCircle size={18} />
      <span>{comparisonError}</span>
    </div>
  )}

  {comparison && (
    <div className="qa-comparison-results">

      <h3>Comparison Results</h3>

      <p className="qa-comparison-subtitle">
        Run #{comparison.reportA.test_execution.test_run_id}
        {" compared with "}
        Run #{comparison.reportB.test_execution.test_run_id}
      </p>

      <div className="qa-comparison-metrics">

        <div className="qa-comparison-metric">
          <span>Previous Pass Rate</span>
          <strong>
            {comparison.reportA.execution_summary.pass_percentage}%
          </strong>
        </div>

        <div className="qa-comparison-metric">
          <span>Latest Pass Rate</span>
          <strong>
            {comparison.reportB.execution_summary.pass_percentage}%
          </strong>
        </div>

        <div className="qa-comparison-metric">
          <span>Pass Rate Change</span>
          <strong
            className={
              comparison.passRateChange > 0
                ? "qa-comparison-positive"
                : comparison.passRateChange < 0
                  ? "qa-comparison-negative"
                  : ""
            }
          >
            {comparison.passRateChange > 0 ? "+" : ""}
            {comparison.passRateChange.toFixed(2)}%
          </strong>
        </div>

      </div>

      <div className="qa-comparison-categories">

        <div className="qa-comparison-category">
          <h4>Regressions</h4>
          <strong className="qa-comparison-negative">
            {comparison.regressions.length}
          </strong>
          <p>Previously passed, now failed</p>
        </div>

        <div className="qa-comparison-category">
          <h4>Fixed Tests</h4>
          <strong className="qa-comparison-positive">
            {comparison.fixed.length}
          </strong>
          <p>Previously failed, now passed</p>
        </div>

        <div className="qa-comparison-category">
          <h4>New Tests</h4>
          <strong>{comparison.newTests.length}</strong>
          <p>Newly included test cases</p>
        </div>

        <div className="qa-comparison-category">
          <h4>Removed Tests</h4>
          <strong>{comparison.removedTests.length}</strong>
          <p>Not included in the latest run</p>
        </div>

      </div>

      {comparison.regressions.length > 0 && (
        <div className="qa-comparison-list">
          <h4>Detected Regressions</h4>

          {comparison.regressions.map((item) => (
            <div
              className="qa-comparison-item"
              key={item.after.test_case_id}
            >
              <XCircle size={18} />

              <div>
                <strong>{item.after.test_title}</strong>
                <p>
                  Passed in previous run → Failed in latest run
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {comparison.fixed.length > 0 && (
        <div className="qa-comparison-list">
          <h4>Successfully Fixed Tests</h4>

          {comparison.fixed.map((item) => (
            <div
              className="qa-comparison-item"
              key={item.after.test_case_id}
            >
              <CheckCircle size={18} />

              <div>
                <strong>{item.after.test_title}</strong>
                <p>
                  Failed in previous run → Passed in latest run
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {comparison.newTests.length > 0 && (
        <div className="qa-comparison-list">
          <h4>Newly Added Tests</h4>

          {comparison.newTests.map((test) => (
            <div
              className="qa-comparison-item"
              key={test.test_case_id}
            >
              <ClipboardList size={18} />
              <div>
                <strong>{test.test_title}</strong>
                <p>New test case in the latest execution</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {comparison.removedTests.length > 0 && (
        <div className="qa-comparison-list">
          <h4>Tests Not Included in Latest Run</h4>

          {comparison.removedTests.map((test) => (
            <div
              className="qa-comparison-item"
              key={test.test_case_id}
            >
              <AlertCircle size={18} />
              <div>
                <strong>{test.test_title}</strong>
                <p>Present in previous run only</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {comparison.regressions.length === 0 &&
       comparison.fixed.length === 0 &&
       comparison.newTests.length === 0 &&
       comparison.removedTests.length === 0 && (
        <div className="qa-comparison-success">
          <CheckCircle size={20} />
          No test status or test coverage changes detected.
        </div>
      )}

    </div>
  )}
</div>


      {report && (
        <div className="qa-report-content">
          <div className="qa-report-header">
            <div>
              <span className="qa-report-label">GENERATED QA REPORT</span>
              <h2>{report.project.project_name}</h2>
              <p>{report.project.website_url}</p>
            </div>

            <button
              className="qa-print-button"
              onClick={handlePrintReport}
            >
              <Download size={17} />
              Print / Save PDF
            </button>
          </div>

          <div className="qa-execution-info">
            <div>
              <span>Run ID</span>
              <strong>#{report.test_execution.test_run_id}</strong>
            </div>

            <div>
              <span>Execution Status</span>
              <strong
                className={getStatusClass(
                  report.test_execution.run_status
                )}
              >
                {report.test_execution.run_status}
              </strong>
            </div>

            <div>
              <span>Started At</span>
              <strong>
                {report.test_execution.started_at
                  ? new Date(
                      report.test_execution.started_at
                    ).toLocaleString()
                  : "—"}
              </strong>
            </div>

            <div>
              <span>Completed At</span>
              <strong>
                {report.test_execution.completed_at
                  ? new Date(
                      report.test_execution.completed_at
                    ).toLocaleString()
                  : "—"}
              </strong>
            </div>
          </div>

          <div className="qa-stat-grid">
            <div className="qa-stat-card">
              <ClipboardList size={22} />
              <span>Total Tests</span>
              <h3>{report.execution_summary.total_tests}</h3>
            </div>

            <div className="qa-stat-card">
              <CheckCircle size={22} />
              <span>Passed</span>
              <h3>{report.execution_summary.passed}</h3>
            </div>

            <div className="qa-stat-card">
              <XCircle size={22} />
              <span>Failed</span>
              <h3>{report.execution_summary.failed}</h3>
            </div>

            <div className="qa-stat-card">
              <AlertCircle size={22} />
              <span>Skipped</span>
              <h3>{report.execution_summary.skipped}</h3>
            </div>
          </div>

          <div className="qa-report-grid">
<div className="qa-report-card">
  <h3>Test Execution Distribution</h3>

  <div className="qa-distribution-chart">
    {[
      {
        name: "Passed",
        value: report.execution_summary.passed,
        color: "#22c55e",
      },
      {
        name: "Failed",
        value: report.execution_summary.failed,
        color: "#ef4444",
      },
      {
        name: "Skipped",
        value: report.execution_summary.skipped,
        color: "#f59e0b",
      },
    ].map((item) => {
      const total = report.execution_summary.total_tests;
      const percentage =
        total > 0 ? (item.value / total) * 100 : 0;

      return (
        <div className="qa-distribution-row" key={item.name}>
          <div className="qa-distribution-label">
            <span>
              <span
                className="qa-distribution-dot"
                style={{ backgroundColor: item.color }}
              />
              {item.name}
            </span>

            <strong>{item.value}</strong>
          </div>

          <div className="qa-distribution-track">
            <div
              className="qa-distribution-fill"
              style={{
                width: `${percentage}%`,
                backgroundColor: item.color,
              }}
            />
          </div>
        </div>
      );
    })}
  </div>

  <div className="qa-pass-rate">
    <span>Pass Percentage</span>
    <strong>
      {report.execution_summary.pass_percentage}%
    </strong>
  </div>
</div>

            <div className="qa-report-card">
              <h3>Bug Summary</h3>

              <div className="qa-bug-total">
                <Bug size={25} />
                <div>
                  <span>Total Bugs</span>
                  <h2>{report.bug_summary.total_bugs}</h2>
                </div>
              </div>

              <div className="qa-bug-breakdown">
                <div>
                  <span>Critical</span>
                  <strong>{report.bug_summary.severity.critical}</strong>
                </div>

                <div>
                  <span>High</span>
                  <strong>{report.bug_summary.severity.high}</strong>
                </div>

                <div>
                  <span>Medium</span>
                  <strong>{report.bug_summary.severity.medium}</strong>
                </div>

                <div>
                  <span>Low</span>
                  <strong>{report.bug_summary.severity.low}</strong>
                </div>
              </div>

              <div className="qa-bug-breakdown">
                <div>
                  <span>Open</span>
                  <strong>{report.bug_summary.status.open}</strong>
                </div>

                <div>
                  <span>In Progress</span>
                  <strong>{report.bug_summary.status.in_progress}</strong>
                </div>

                <div>
                  <span>Resolved</span>
                  <strong>{report.bug_summary.status.resolved}</strong>
                </div>
              </div>
            </div>
          </div>

          <div className="qa-report-card qa-details-section">
            <h3>Individual Test Results</h3>

            {report.test_details.length === 0 ? (
              <p className="qa-empty">No test details available.</p>
            ) : (
              <div className="qa-table-wrapper">
                <table className="qa-table">
                  <thead>
                    <tr>
                      <th>Test Case</th>
                      <th>Status</th>
                      <th>Actual Result</th>
                      <th>Duration</th>
                    </tr>
                  </thead>

                  <tbody>
                    {report.test_details.map((test) => (
                      <tr key={test.test_result_id}>
                        <td>
                          <strong>{test.test_title}</strong>
                          <small>Case #{test.test_case_id}</small>
                        </td>

                        <td>
                          <span
                            className={`qa-status ${getStatusClass(
                              test.status
                            )}`}
                          >
                            {test.status}
                          </span>
                        </td>

                        <td>
                          {test.actual_result ||
                            test.error_message ||
                            "No details available"}
                        </td>

                        <td>
                          {test.duration_ms != null
                            ? `${test.duration_ms} ms`
                            : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="qa-report-card qa-details-section">
            <h3>Detected Bugs</h3>

            {report.bug_details.length === 0 ? (
              <p className="qa-empty">
                No bugs were recorded for this execution run.
              </p>
            ) : (
              <div className="qa-bug-list">
                {report.bug_details.map((bug) => (
                  <div className="qa-bug-item" key={bug.bug_id}>
                    <div>
                      <strong>{bug.title}</strong>
                      <p>{bug.description}</p>
                      <small>Root Cause: {bug.root_cause}</small>
                    </div>

                    <span className="bug-severity medium">
                      {bug.severity}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="qa-report-card qa-recommendations">
            <div className="qa-recommendation-heading">
              <AlertCircle size={21} />
              <h3>Recommendations</h3>
            </div>

            {report.recommendations.map((recommendation, index) => (
              <div className="qa-recommendation" key={index}>
                <CheckCircle size={17} />
                <p>{recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default QAReports;
