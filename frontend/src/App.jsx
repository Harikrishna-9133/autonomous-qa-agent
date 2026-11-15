
import { useState } from "react";
import {
  FolderKanban,
  ClipboardList,
  Play,
  Bug,
  FileBarChart,
  Settings,
} from "lucide-react";

import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Header from "./components/Header";
import Projects from "./pages/Projects";
import TestCases from "./pages/TestCases";
import Execution from "./pages/Execution";
import BugReports from "./pages/BugReports";
import QAReports from "./pages/QAReports";

const pageDetails = {
  projects: {
    title: "Projects",
    subtitle: "Manage your registered websites and testing projects.",
    icon: FolderKanban,
  },
  "test-cases": {
    title: "Test Cases",
    subtitle: "Create, manage and organize your test scenarios.",
    icon: ClipboardList,
  },
  execution: {
    title: "Test Execution",
    subtitle: "Monitor browser automation and test execution history.",
    icon: Play,
  },
  bugs: {
    title: "Bug Reports",
    subtitle: "Investigate, track and resolve reported bugs.",
    icon: Bug,
  },
  reports: {
    title: "QA Reports",
    subtitle: "Review detailed software quality reports.",
    icon: FileBarChart,
  },
  settings: {
    title: "Settings",
    subtitle: "Manage your QA Agent workspace settings.",
    icon: Settings,
  },
  "test-cases": {
  title: "Test Case Management",
  subtitle: "Create, organize, and manage automated test cases."
},
};

function App() {
  const [activePage, setActivePage] = useState("dashboard");

  const page = pageDetails[activePage];

  return (
    <div className="app-layout">
      <Sidebar
        activePage={activePage}
        setActivePage={setActivePage}
      />


<main className="main-content">
  {activePage === "dashboard" ? (
    <Dashboard />
  ) : activePage === "projects" ? (
    <Projects />
  ) : activePage === "test-cases" ? (
    <TestCases />
  ) : activePage === "execution" ? (
    <Execution />
  ) : activePage === "bugs" ? (
    <BugReports />
  ) : activePage === "reports" ? (
    <QAReports />
  ) : (
    <div className="placeholder-page">
      <Header
        title={page.title}
        subtitle={page.subtitle}
      />

      <div className="placeholder-card">
        <div className="placeholder-icon">
          <page.icon size={32} />
        </div>

        <h2>{page.title}</h2>

        <p>
          This module is under development. We will connect it
          to your FastAPI backend in the next development steps.
        </p>

        <button
          className="back-button"
          onClick={() => setActivePage("dashboard")}
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  )}
</main>

    </div>
  );
}

export default App;
