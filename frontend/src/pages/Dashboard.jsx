
import { useCallback, useEffect, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

import {
  FolderKanban,
  ClipboardList,
  Play,
  Bug,
  Activity,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  SkipForward,
  Camera,
  Download,
} from "lucide-react";



import api from "../api";
import Header from "../components/Header";
import StatCard from "../components/StatCard";

function formatDate(dateValue) {
  if (!dateValue) return "Not available";

  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) return "Not available";

  return date.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}


function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;

  document.body.appendChild(link);
  link.click();
  link.remove();

  URL.revokeObjectURL(url);
}

function exportAgentJSON(result) {
  if (!result) return;

  const exportData = {
    project_name: result.project_name,
    project_id: result.project_id,
    test_run_id: result.test_run_id,
    workflow_status: result.workflow_status,
    discovered_features: result.discovered_features,
    total_generated_tests: result.total_generated_tests,
    execution_results: result.execution_results,
    bug_reports: result.bug_reports,
    qa_report: result.qa_report,
    errors: result.errors,
    exported_at: new Date().toISOString(),
  };

  downloadFile(
    JSON.stringify(exportData, null, 2),
    `QA_Evidence_Run_${result.test_run_id}.json`,
    "application/json"
  );
}

function exportAgentCSV(result) {
  if (!result?.execution_results) return;

  const headers = [
    "Test Result ID",
    "Test Case ID",
    "Test Name",
    "Status",
    "Actual Result",
    "Passed Checks",
    "Failed Checks",
    "Total Checks",
    "Duration (ms)",
    "Error",
    "Screenshot Filename",
  ];

  const escapeCSV = (value) =>
    `"${String(value ?? "").replace(/"/g, '""')}"`;

  const rows = result.execution_results.map((test) => {
    const checks = test.checks || [];
    const passed = checks.filter((check) => check.passed).length;
    const failed = checks.filter((check) => !check.passed).length;

    const screenshot = test.screenshot_path
      ? test.screenshot_path.split(/[\\/]/).pop()
      : "";

    return [
      test.test_result_id,
      test.test_case_id,
      test.title,
      test.status,
      test.actual_result,
      passed,
      failed,
      checks.length,
      test.duration_ms,
      test.error_message,
      screenshot,
    ].map(escapeCSV).join(",");
  });

  const csvContent = [
    headers.map(escapeCSV).join(","),
    ...rows,
  ].join("\n");

  downloadFile(
    "\uFEFF" + csvContent,
    `QA_Evidence_Run_${result.test_run_id}.csv`,
    "text/csv;charset=utf-8"
  );
}


function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [testCases, setTestCases] = useState([]);
  const [testRuns, setTestRuns] = useState([]);
  const [bugs, setBugs] = useState([]);
  const [projectAnalytics, setProjectAnalytics] = useState([]);
  const [executionTrendData, setExecutionTrendData] = useState([]);
  const [qaAnalytics, setQaAnalytics] = useState({
  totalTests: 0,
  passed: 0,
  failed: 0,
  skipped: 0,
  passRate: 0,
  loading: true,
});

  const [latestReport, setLatestReport] = useState(null);
  const [reportError, setReportError] = useState("");

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  // Autonomous QA Agent
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [agentRunning, setAgentRunning] = useState(false);
  const [agentResult, setAgentResult] = useState(null);
  const [agentError, setAgentError] = useState("");
  const [bugAnalytics, setBugAnalytics] = useState(null);

  const fetchDashboardData = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");
      setReportError("");

      const [
  projectRes,
  caseRes,
  runRes,
  bugRes,
  bugAnalyticsRes
] = await Promise.all([
  api.get("/api/projects/"),
  api.get("/api/test-cases/"),
  api.get("/api/test-runs/"),
  api.get("/api/bug-reports/"),
  api.get("/api/bug-reports/analytics"),
]);

      const projectData = Array.isArray(projectRes.data)
        ? projectRes.data
        : [];

      const caseData = Array.isArray(caseRes.data)
        ? caseRes.data
        : [];

      const runData = Array.isArray(runRes.data)
        ? runRes.data
        : [];

      const bugData = Array.isArray(bugRes.data)
        ? bugRes.data
        : [];

      setProjects(projectData);
      setTestCases(caseData);
      setTestRuns(runData);
      setBugs(bugData);
      setBugAnalytics(bugAnalyticsRes.data);


// Calculate historical QA analytics.
// Exclude run 17 because it was a synthetic verification test.
const analyticsRuns = runData.filter(
  (run) => Number(run.id) !== 17
);

// Prepare separate statistics for every project.
const projectTotals = new Map(
  projectData.map((project) => [
    project.id,
    {
      projectId: project.id,
      name: `${project.name} (#${project.id})`,
      testRuns: 0,
      totalTests: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
    },
  ])
);

// Fetch all test-run summaries.
const summaryResults = await Promise.allSettled(
  analyticsRuns.map(async (run) => {
    const response = await api.get(
      `/api/test-runs/${run.id}/summary`
    );

    return {
  projectId: run.project_id,
  runId: run.id,
  startedAt: run.started_at,
  status: run.status,
  summary: response.data,
};
  })
);

// Prepare chronological execution trend data.
const trendData = summaryResults
  .filter((result) => result.status === "fulfilled")
  .map((result) => {
    const { runId, startedAt, summary } = result.value;

    const total = summary.total_tests || 0;
    const passed = summary.passed || 0;
    const failed = summary.failed || 0;

    return {
      runId,
      runLabel: `Run #${runId}`,
      startedAt,
      passed,
      failed,
      total,
      passRate:
        total > 0
          ? Number(((passed / total) * 100).toFixed(2))
          : 0,
    };
  })
  .sort(
    (a, b) =>
      new Date(a.startedAt).getTime() -
      new Date(b.startedAt).getTime()
  );

setExecutionTrendData(trendData);

// Calculate overall and project-wise statistics.
const totals = {
  totalTests: 0,
  passed: 0,
  failed: 0,
  skipped: 0,
  failedRequests: 0,
};

summaryResults.forEach((result) => {
  if (result.status !== "fulfilled") {
    console.error("Test-run summary failed:", result.reason);
    totals.failedRequests += 1;
    return;
  }

  const { projectId, summary } = result.value;
  const project = projectTotals.get(projectId);

  if (project) {
    project.testRuns += 1;
    project.totalTests += summary.total_tests || 0;
    project.passed += summary.passed || 0;
    project.failed += summary.failed || 0;
    project.skipped += summary.skipped || 0;
  }

  totals.totalTests += summary.total_tests || 0;
  totals.passed += summary.passed || 0;
  totals.failed += summary.failed || 0;
  totals.skipped += summary.skipped || 0;
});

setProjectAnalytics(Array.from(projectTotals.values()));

const passRate =
  totals.totalTests > 0
    ? Number(
        ((totals.passed / totals.totalTests) * 100).toFixed(2)
      )
    : 0;

setQaAnalytics({
  totalTests: totals.totalTests,
  passed: totals.passed,
  failed: totals.failed,
  skipped: totals.skipped,
  passRate,
  loading: false,
  failedRequests: totals.failedRequests,
});


      // The backend returns the newest runs first.
      // Sort again to make sure the latest run is selected.
      const sortedRuns = [...runData].sort(
        (a, b) =>
          new Date(b.started_at || 0).getTime() -
          new Date(a.started_at || 0).getTime()
      );

      const latestRun = sortedRuns[0];

      if (latestRun?.id) {
        try {
          const reportRes = await api.get(
            `/api/qa-reports/projects/${latestRun.project_id}/runs/${latestRun.id}`
          );

          setLatestReport(reportRes.data);
        } catch (reportErr) {
          console.error("Latest QA report error:", reportErr);
          setLatestReport(null);
          setReportError(
            "Latest QA report is not available for this test run."
          );
        }
      } else {
        setLatestReport(null);
      }
    } catch (err) {
      console.error("Dashboard API error:", err);

      setError(
        "Unable to load dashboard data. Please check the backend connection."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  useEffect(() => {
  if (!selectedProjectId && projects.length > 0) {
    setSelectedProjectId(String(projects[0].id));
  }
}, [projects, selectedProjectId]);

  const startAutonomousQA = async () => {
  if (!selectedProjectId || agentRunning) {
    return;
  }

  try {
    setAgentRunning(true);
    setAgentError("");
    setAgentResult(null);

    const response = await api.post(
      `/api/agent/run/${selectedProjectId}`
    );

    setAgentResult(response.data);

    // Refresh dashboard statistics and execution history.
    await fetchDashboardData(true);

  } catch (err) {
    console.error("Autonomous QA error:", err);

    setAgentError(
      err.response?.data?.detail ||
      "Unable to execute the Autonomous QA Agent. Check the backend."
    );
  } finally {
    setAgentRunning(false);
  }
};

  const openBugs = bugs.filter(
    (bug) => bug.status?.toLowerCase() === "open"
  ).length;

  const projectChartData = projectAnalytics.map((project) => ({
  name: project.name,
  passed: project.passed,
  failed: project.failed,
}));

  const runChartData = [
    {
      name: "Completed",
      total: testRuns.filter(
        (run) => run.status?.toLowerCase() === "completed"
      ).length,
    },
    {
      name: "Running",
      total: testRuns.filter(
        (run) => run.status?.toLowerCase() === "running"
      ).length,
    },
    {
      name: "Failed",
      total: testRuns.filter(
        (run) => run.status?.toLowerCase() === "failed"
      ).length,
    },
  ];

  const severityData = [
    {
      name: "Critical",
      total: bugs.filter(
        (bug) => bug.severity?.toLowerCase() === "critical"
      ).length,
    },
    {
      name: "High",
      total: bugs.filter(
        (bug) => bug.severity?.toLowerCase() === "high"
      ).length,
    },
    {
      name: "Medium",
      total: bugs.filter(
        (bug) => bug.severity?.toLowerCase() === "medium"
      ).length,
    },
    {
      name: "Low",
      total: bugs.filter(
        (bug) => bug.severity?.toLowerCase() === "low"
      ).length,
    },
  ];

  const latestExecution = latestReport?.execution_summary;

  const sortedRuns = [...testRuns].sort(
    (a, b) =>
      new Date(b.started_at || 0).getTime() -
      new Date(a.started_at || 0).getTime()
  );

  return (
    <div className="dashboard-page">
      <Header
        title="Dashboard Overview"
        subtitle="Monitor your automated testing and quality metrics."
      />

      {loading ? (
        <div className="loading-message">
          Loading dashboard data...
        </div>
      ) : error ? (
        <div className="dashboard-error">{error}</div>
      ) : (
        <>
          <section className="dashboard-toolbar">
            <span className="dashboard-empty">
              Last refreshed: {new Date().toLocaleTimeString("en-IN")}
            </span>

            <button
              className="dashboard-refresh"
              onClick={() => fetchDashboardData(true)}
              disabled={refreshing}
            >
              <RefreshCw
                size={16}
                className={refreshing ? "refresh-spinning" : ""}
              />
              {refreshing ? "Refreshing..." : "Refresh Dashboard"}
            </button>
          </section>

          <section className="welcome-section">
            <div>
              <span className="welcome-label">
                WORKSPACE OVERVIEW
              </span>

              <h2>Welcome back, Hari Krishna 👋</h2>

              <p>
                Here's what's happening with your testing projects.
              </p>
            </div>

            <div className="system-status">
              <span className="status-indicator"></span>
              Backend connected
            </div>
          </section>

          <section className="stats-grid">
            <StatCard
              title="Total Projects"
              value={projects.length}
              subtitle="Registered websites"
              icon={FolderKanban}
              color="purple"
            />

            <StatCard
              title="Test Cases"
              value={testCases.length}
              subtitle="Available test scenarios"
              icon={ClipboardList}
              color="blue"
            />

            <StatCard
              title="Test Runs"
              value={testRuns.length}
              subtitle="Recorded executions"
              icon={Play}
              color="green"
            />

            <StatCard
              title="Open Bugs"
              value={openBugs}
              subtitle={`${bugs.length} total bug reports`}
              icon={Bug}
              color="orange"
            />
            <StatCard
  title="Total Tests Executed"
  value={qaAnalytics.loading ? "..." : qaAnalytics.totalTests}
  subtitle="Across historical test runs"
  icon={Activity}
  color="blue"
/>

<StatCard
  title="Passed Tests"
  value={qaAnalytics.loading ? "..." : qaAnalytics.passed}
  subtitle="Successfully executed tests"
  icon={CheckCircle2}
  color="green"
/>

<StatCard
  title="Failed Tests"
  value={qaAnalytics.loading ? "..." : qaAnalytics.failed}
  subtitle="Tests requiring investigation"
  icon={XCircle}
  color="orange"
/>

<StatCard
  title="Overall Pass Rate"
  value={qaAnalytics.loading ? "..." : `${qaAnalytics.passRate}%`}
  subtitle="Historical QA success rate"
  icon={Activity}
  color="purple"
/>
          </section>


{/* Overall QA Performance */}
<section className="qa-performance-panel">
  <div className="qa-performance-header">
    <div>
      <h2>Overall QA Performance</h2>
      <p>Historical test execution statistics</p>
    </div>
    <span className="qa-performance-badge">
      Live Analytics
    </span>
  </div>

  {qaAnalytics.loading ? (
    <p>Calculating QA performance...</p>
  ) : (
    <>
      <div className="qa-performance-score">
        <div>
          <strong>{qaAnalytics.passRate}%</strong>
          <span>Overall Pass Rate</span>
        </div>
        <div className="qa-performance-total">
          <strong>{qaAnalytics.totalTests}</strong>
          <span>Total Tests</span>
        </div>
      </div>

      <div
        className="qa-progress-track"
        role="progressbar"
        aria-valuenow={qaAnalytics.passRate}
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div
          className="qa-progress-passed"
          style={{ width: `${qaAnalytics.passRate}%` }}
        />
      </div>

      <div className="qa-performance-legend">
        <div>
          <span className="qa-dot qa-dot-passed" />
          Passed <strong>{qaAnalytics.passed}</strong>
        </div>
        <div>
          <span className="qa-dot qa-dot-failed" />
          Failed <strong>{qaAnalytics.failed}</strong>
        </div>
        <div>
          <span className="qa-dot qa-dot-skipped" />
          Skipped <strong>{qaAnalytics.skipped}</strong>
        </div>
      </div>

      {qaAnalytics.failedRequests > 0 && (
        <p className="qa-analytics-warning">
          Some test-run summaries could not be loaded.
          Displayed totals may be incomplete.
        </p>
      )}
    </>
  )}
</section>


          {/* Autonomous QA Agent */}
<section className="autonomous-agent-card">
  <div className="agent-header">
    <div>
      <span className="agent-label">AI-POWERED TESTING</span>
      <h3>Autonomous QA Agent</h3>
      <p>
        Explore your website, generate test scenarios,
        execute browser tests and investigate failures.
      </p>
    </div>

    <div className="agent-icon">
      <Activity size={26} />
    </div>
  </div>

  <div className="agent-controls">
    <div className="agent-project-select">
      <label htmlFor="agent-project">
        Select Website Project
      </label>

      <select
        id="agent-project"
        value={selectedProjectId}
        onChange={(e) => {
          setSelectedProjectId(e.target.value);
          setAgentResult(null);
          setAgentError("");
        }}
        disabled={agentRunning}
      >
        <option value="">Choose a project</option>

        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name} — Project #{project.id}
          </option>
        ))}
      </select>
    </div>

    <button
      className="agent-run-button"
      onClick={startAutonomousQA}
      disabled={!selectedProjectId || agentRunning}
    >
      {agentRunning ? (
        <>
          <RefreshCw size={17} className="refresh-spinning" />
          Running QA Workflow...
        </>
      ) : (
        <>
          <Play size={17} />
          Start Autonomous QA
        </>
      )}
    </button>
  </div>

  {agentRunning && (
    <div className="agent-running-message">
      <RefreshCw size={18} className="refresh-spinning" />
      <span>
        The agent is exploring your website and executing tests.
        Please wait...
      </span>
    </div>
  )}

  {agentError && (
    <div className="agent-error">
      <XCircle size={18} />
      {agentError}
    </div>
  )}

  {agentResult && (
    <div className="agent-results">

      <div className="agent-result-heading">
        <div>
          <h4>Autonomous Execution Results</h4>
          <p>
            {agentResult.project_name} · Run #
            {agentResult.test_run_id}
          </p>
        </div>
        <div className="agent-export-actions">
  <button
    className="agent-export-button"
    onClick={() => exportAgentJSON(agentResult)}
  >
    <Download size={16} />
    Download JSON
  </button>

  <button
    className="agent-export-button"
    onClick={() => exportAgentCSV(agentResult)}
  >
    <Download size={16} />
    Download CSV
  </button>
</div>

        <span
          className={`run-status ${
            agentResult.workflow_status === "completed"
              ? "completed"
              : "failed"
          }`}
        >
          {agentResult.workflow_status}
        </span>
      </div>

      {agentResult.errors?.length > 0 && (
        <div className="agent-error">
          {agentResult.errors.map((item, index) => (
            <p key={index}>{item}</p>
          ))}
        </div>
      )}

      <div className="agent-feature-section">
        <h4>Discovered Website Features</h4>

        <div className="agent-feature-list">
          {(agentResult.discovered_features || []).map(
            (feature, index) => (
              <span key={index} className="agent-feature">
                {feature}
              </span>
            )
          )}
        </div>
      </div>

      <div className="agent-result-metrics">
        <div>
          <span>Generated Tests</span>
          <strong>
            {agentResult.total_generated_tests ?? 0}
          </strong>
        </div>

        <div>
          <span>Passed</span>
          <strong className="agent-passed">
            {agentResult.qa_report?.execution_summary?.passed ?? 0}
          </strong>
        </div>

        <div>
          <span>Failed</span>
          <strong className="agent-failed">
            {agentResult.qa_report?.execution_summary?.failed ?? 0}
          </strong>
        </div>

        <div>
          <span>Pass Rate</span>
          <strong>
            {agentResult.qa_report?.execution_summary?.pass_percentage ?? 0}%
          </strong>
        </div>
      </div>

      <div className="agent-test-list">
  <h4>Detailed Browser Test Evidence</h4>

  {agentResult.execution_results?.length > 0 ? (
    agentResult.execution_results.map((result, index) => (
      <details
        className="agent-evidence-item"
        key={result.test_result_id || index}
      >
        <summary className="agent-evidence-summary">
          <div className="agent-evidence-title">
            <strong>
              {result.title || `Test Case #${result.test_case_id}`}
            </strong>

            <span>
              {result.actual_result || "No execution details"}
              {" · "}
              {result.duration_ms ?? 0} ms
            </span>
          </div>

          <span
            className={`run-status ${
              result.status?.toLowerCase() || "failed"
            }`}
          >
            {result.status || "Unknown"}
          </span>
        </summary>

        <div className="agent-evidence-details">

          <p>
            <strong>Test Case ID:</strong> #{result.test_case_id}
          </p>

          <p>
            <strong>Test Result ID:</strong> #{result.test_result_id}
          </p>

          <p>
            <strong>Execution:</strong> {result.actual_result}
          </p>

          {result.error_message && (
            <div className="agent-error">
              {result.error_message}
            </div>
          )}

          <h5>Individual Browser Checks</h5>

          {result.checks?.length > 0 ? (
            result.checks.map((check, checkIndex) => (
              <div
                className="agent-check-row"
                key={checkIndex}
              >
                <span>
                  {check.passed ? "✓" : "✕"}
                </span>

                <div>
                  <strong>{check.check}</strong>
                  <p>{check.details}</p>
                </div>

                <span
                  className={
                    check.passed
                      ? "agent-check-passed"
                      : "agent-check-failed"
                  }
                >
                  {check.passed ? "Passed" : "Failed"}
                </span>
              </div>
            ))
          ) : (
            <p className="dashboard-empty">
              Individual check details are not available.
            </p>
          )}

          {result.screenshot_path && (() => {
  const filename = result.screenshot_path
    .split(/[\\/]/)
    .pop();

  const screenshotUrl =
    `${api.defaults.baseURL}/api/evidence/screenshots/${encodeURIComponent(filename)}`;

  return (
    <div className="agent-screenshot-section">
      <h5>
        <Camera size={16} />
        Browser Screenshot Evidence
      </h5>

      <a
        href={screenshotUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="agent-screenshot-link"
      >
        Open Full Screenshot
      </a>

      <img
        src={screenshotUrl}
        alt={`Browser screenshot for ${result.title || "test execution"}`}
        className="agent-screenshot-image"
        loading="lazy"
      />
    </div>
  );
})()}

        </div>
      </details>
    ))
  ) : (
    <p className="dashboard-empty">
      No browser execution results were returned.
    </p>
  )}
</div>

      <div className="agent-bug-section">
        <h4>
          Investigated Bugs (
          {agentResult.bug_reports?.length || 0})
        </h4>

        {agentResult.bug_reports?.length > 0 ? (
          agentResult.bug_reports.map((bug, index) => (
            <div className="agent-bug-row" key={bug.bug_id || index}>
              <Bug size={18} />

              <div>
                <strong>{bug.title || "Unspecified issue"}</strong>
                <span>
                  {bug.severity || "Unclassified"} severity
                  {bug.root_cause
                    ? ` · ${bug.root_cause}`
                    : ""}
                </span>
              </div>
            </div>
          ))
        ) : (
          <p className="dashboard-empty">
            No bugs were identified in this execution.
          </p>
        )}
      </div>

      {agentResult.qa_report?.recommendations && (
        <div className="agent-recommendation">
          <strong>QA Recommendation</strong>
          <p>{agentResult.qa_report.recommendations}</p>
        </div>
      )}

    </div>
  )}
</section>

{/* Latest execution details */}
<section className="latest-run-card"></section>

          {/* Latest execution details */}
          <section className="latest-run-card">
            <div className="latest-run-header">
              <div>
                <h3>Latest Test Execution</h3>
                <p>
                  {latestReport
                    ? `Run #${latestReport.test_execution.test_run_id} · ${
                        latestReport.project.project_name
                      }`
                    : "Latest execution summary"}
                </p>
              </div>

              {latestReport && (
                <span
                  className={`run-status ${
                    latestReport.test_execution.run_status?.toLowerCase() ||
                    ""
                  }`}
                >
                  {latestReport.test_execution.run_status}
                </span>
              )}
            </div>

            {latestExecution ? (
              <>
                <div className="latest-run-metrics">
                  <div className="latest-run-metric">
                    <span>Total Tests</span>
                    <strong>
                      {latestExecution.total_tests}
                    </strong>
                  </div>

                  <div className="latest-run-metric">
                    <span>Passed</span>
                    <strong style={{ color: "#86efac" }}>
                      {latestExecution.passed}
                    </strong>
                  </div>

                  <div className="latest-run-metric">
                    <span>Failed</span>
                    <strong style={{ color: "#fca5a5" }}>
                      {latestExecution.failed}
                    </strong>
                  </div>

                  <div className="latest-run-metric">
                    <span>Pass Rate</span>
                    <strong style={{ color: "#b99aff" }}>
                      {latestExecution.pass_percentage}%
                    </strong>
                  </div>
                </div>

                <p className="dashboard-empty">
                  <Clock
                    size={13}
                    style={{
                      display: "inline",
                      verticalAlign: "middle",
                      marginRight: 5,
                    }}
                  />
                  Started:{" "}
                  {formatDate(
                    latestReport.test_execution.started_at
                  )}
                </p>
              </>
            ) : (
              <p className="dashboard-empty">
                {reportError ||
                  "No test execution report is available yet."}
              </p>
            )}
          </section>

          {/* Charts */}
          <section className="charts-grid">
            <div className="chart-card">
              <div className="section-heading">
                <div>
                  <h3>Test Execution Overview</h3>
                  <p>
                    Execution status across recorded runs
                  </p>
                </div>

                <Activity size={20} />
              </div>

              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={runChartData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#303044"
                  />

                  <XAxis
                    dataKey="name"
                    stroke="#9999ad"
                  />

                  <YAxis
                    allowDecimals={false}
                    stroke="#9999ad"
                  />

                  <Tooltip />

                  <Bar
                    dataKey="total"
                    fill="#8b5cf6"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>


{/* Bug Analytics Section */}

<div className="chart-card">
  <div className="section-heading">
    <div>
      <h3>Bug Status Distribution</h3>
      <p>Current lifecycle status of reported bugs</p>
    </div>
    <Bug size={20} />
  </div>

  <ResponsiveContainer width="100%" height={280}>
    <BarChart
      data={Object.entries(
        bugAnalytics?.status_breakdown || {}
      ).map(([name, total]) => ({
        name: name.replace("_", " "),
        total,
      }))}
    >
      <CartesianGrid strokeDasharray="3 3" stroke="#303044" />
      <XAxis dataKey="name" stroke="#9999ad" />
      <YAxis allowDecimals={false} stroke="#9999ad" />
      <Tooltip />
      <Bar
        dataKey="total"
        name="Bugs"
        fill="#8b5cf6"
        radius={[6, 6, 0, 0]}
      />
    </BarChart>
  </ResponsiveContainer>
</div>

<div className="chart-card">
  <div className="section-heading">
    <div>
      <h3>Bug Severity Analysis</h3>
      <p>Distribution by severity level</p>
    </div>
    <Activity size={20} />
  </div>

  <ResponsiveContainer width="100%" height={280}>
    <BarChart
      data={Object.entries(
        bugAnalytics?.severity_breakdown || {}
      ).map(([name, total]) => ({
        name,
        total,
      }))}
    >
      <CartesianGrid strokeDasharray="3 3" stroke="#303044" />
      <XAxis dataKey="name" stroke="#9999ad" />
      <YAxis allowDecimals={false} stroke="#9999ad" />
      <Tooltip />
      <Bar
        dataKey="total"
        name="Bugs"
        fill="#f59e0b"
        radius={[6, 6, 0, 0]}
      />
    </BarChart>
  </ResponsiveContainer>
</div>

<div className="chart-card">
  <div className="section-heading">
    <div>
      <h3>Failure Category Analysis</h3>
      <p>Types of failures detected by the investigator</p>
    </div>
    <Bug size={20} />
  </div>

  {!bugAnalytics?.failure_categories?.length ? (
    <p className="dashboard-empty">
      No failure category data available.
    </p>
  ) : (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={bugAnalytics.failure_categories}>
        <CartesianGrid strokeDasharray="3 3" stroke="#303044" />
        <XAxis dataKey="failure_type" stroke="#9999ad" />
        <YAxis allowDecimals={false} stroke="#9999ad" />
        <Tooltip />
        <Bar
          dataKey="count"
          name="Failures"
          fill="#06b6d4"
          radius={[6, 6, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )}
</div>

<div className="chart-card">
  <div className="section-heading">
    <div>
      <h3>Component-wise Failures</h3>
      <p>Components associated with reported bugs</p>
    </div>
    <Activity size={20} />
  </div>

  {!bugAnalytics?.component_breakdown?.length ? (
    <p className="dashboard-empty">
      No component data available.
    </p>
  ) : (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={bugAnalytics.component_breakdown}>
        <CartesianGrid strokeDasharray="3 3" stroke="#303044" />
        <XAxis
          dataKey="component"
          stroke="#9999ad"
          tick={{ fontSize: 11 }}
        />
        <YAxis allowDecimals={false} stroke="#9999ad" />
        <Tooltip />
        <Bar
          dataKey="count"
          name="Bugs"
          fill="#ec4899"
          radius={[6, 6, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )}
</div>

{/* Recurring Failure Analysis */}

<div className="chart-card">
  <div className="section-heading">
    <div>
      <h3>Recurring Failure Analysis</h3>
      <p>Repeated failure signatures identified by the system</p>
    </div>
    <RefreshCw size={20} />
  </div>

  {!bugAnalytics?.recurring_failures?.length ? (
    <p className="dashboard-empty">
      No recurring failures detected.
    </p>
  ) : (
    <div className="project-list">
      {bugAnalytics.recurring_failures.map((failure, index) => (
        <div className="project-row" key={`${failure.title}-${index}`}>
          <div className="project-avatar">
            <Bug size={20} />
          </div>

          <div className="project-info">
            <strong>{failure.title}</strong>
            <span>
              {failure.failure_type} · {failure.component}
            </span>
            <span>
              Bug IDs: {failure.bug_ids.join(", ")}
            </span>
          </div>

          <span className="project-id">
            {failure.count} occurrences
          </span>
        </div>
      ))}
    </div>
  )}
</div>


            <div className="chart-card">
              <div className="section-heading">
                <div>
                  <h3>Bug Severity</h3>
                  <p>
                    Distribution of recorded bug reports
                  </p>
                </div>

                <Bug size={20} />
              </div>

              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={severityData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#303044"
                  />

                  <XAxis
                    dataKey="name"
                    stroke="#9999ad"
                  />

                  <YAxis
                    allowDecimals={false}
                    stroke="#9999ad"
                  />

                  <Tooltip />

                  <Bar
                    dataKey="total"
                    fill="#f59e0b"
                    radius={[6, 6, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

{/* Project Performance Comparison */}
<div className="chart-card">
  <div className="section-heading">
    <div>
      <h3>Project Performance Comparison</h3>
      <p>
        Passed and failed tests across registered projects
      </p>
    </div>

    <FolderKanban size={20} />
  </div>

  {projectAnalytics.length === 0 ? (
    <p className="dashboard-empty">
      No project analytics available.
    </p>
  ) : (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart
        data={projectChartData}
        margin={{ top: 10, right: 10, left: 0, bottom: 45 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#303044"
        />

        <XAxis
          dataKey="name"
          stroke="#9999ad"
          angle={-15}
          textAnchor="end"
          interval={0}
          height={65}
          tick={{ fontSize: 11 }}
        />

        <YAxis
          allowDecimals={false}
          stroke="#9999ad"
        />

        <Tooltip />

        <Bar
          dataKey="passed"
          name="Passed Tests"
          fill="#22c55e"
          radius={[5, 5, 0, 0]}
        />

        <Bar
          dataKey="failed"
          name="Failed Tests"
          fill="#ef4444"
          radius={[5, 5, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )}
</div>


{/* Execution History Trend */}
<div className="chart-card">
  <div className="section-heading">
    <div>
      <h3>Execution History Trend</h3>
      <p>Passed and failed tests across historical runs</p>
    </div>
    <Activity size={20} />
  </div>

  {executionTrendData.length === 0 ? (
    <p className="dashboard-empty">
      No execution history available.
    </p>
  ) : (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={executionTrendData}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#303044"
        />
        <XAxis
          dataKey="runLabel"
          stroke="#9999ad"
        />
        <YAxis
          allowDecimals={false}
          stroke="#9999ad"
        />
        <Tooltip />
        <Legend />
        <Bar
          dataKey="passed"
          name="Passed"
          fill="#22c55e"
          radius={[4, 4, 0, 0]}
        />
        <Bar
          dataKey="failed"
          name="Failed"
          fill="#ef4444"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )}
</div>

{/* Pass Rate Trend */}
<div className="chart-card">
  <div className="section-heading">
    <div>
      <h3>Historical Pass Rate</h3>
      <p>Testing success percentage by execution</p>
    </div>
    <Activity size={20} />
  </div>

  {executionTrendData.length === 0 ? (
    <p className="dashboard-empty">
      No pass-rate history available.
    </p>
  ) : (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={executionTrendData}>
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#303044"
        />
        <XAxis
          dataKey="runLabel"
          stroke="#9999ad"
        />
        <YAxis
          domain={[0, 100]}
          unit="%"
          stroke="#9999ad"
        />
        <Tooltip formatter={(value) => `${value}%`} />
        <Legend />
        <Line
          type="monotone"
          dataKey="passRate"
          name="Pass Rate"
          stroke="#a78bfa"
          strokeWidth={3}
          dot={{ r: 4 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )}
</div>


          </section>

          {/* Recent executions */}
          <section className="recent-runs-card">
            <div className="section-heading">
              <div>
                <h3>Recent Test Executions</h3>
                <p>
                  Your latest recorded browser test runs
                </p>
              </div>
            </div>

            {sortedRuns.length === 0 ? (
              <p className="dashboard-empty">
                No test executions recorded yet.
              </p>
            ) : (
              sortedRuns.slice(0, 5).map((run) => (
                <div className="recent-run-row" key={run.id}>
                  <div className="recent-run-info">
                    <strong>
                      Test Run #{run.id}
                    </strong>

                    <span>
                      Project #{run.project_id} ·{" "}
                      {formatDate(run.started_at)}
                    </span>
                  </div>

                  <span
                    className={`run-status ${
                      run.status?.toLowerCase() || ""
                    }`}
                  >
                    {run.status}
                  </span>
                </div>
              ))
            )}
          </section>

          {/* Registered projects */}
          <section className="projects-card">
            <div className="section-heading">
              <div>
                <h3>Registered Projects</h3>
                <p>
                  Your websites connected to the QA platform
                </p>
              </div>
            </div>

            {projects.length === 0 ? (
              <p className="empty-message">
                No projects registered yet.
              </p>
            ) : (
              <div className="project-list">
                {projects.map((project) => (
                  <div
                    className="project-row"
                    key={project.id}
                  >
                    <div className="project-avatar">
                      <FolderKanban size={20} />
                    </div>

                    <div className="project-info">
                      <strong>{project.name}</strong>
                      <span>{project.base_url}</span>
                    </div>

                    <span className="project-id">
                      Project #{project.id}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}

export default Dashboard;
