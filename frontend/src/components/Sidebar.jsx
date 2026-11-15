
import {
  LayoutDashboard,
  FolderKanban,
  ClipboardList,
  Play,
  Bug,
  FileBarChart,
  Settings,
  Bot,
  ChevronLeft,
} from "lucide-react";

const menuItems = [
  { name: "Dashboard", icon: LayoutDashboard, path: "dashboard" },
  { name: "Projects", icon: FolderKanban, path: "projects" },
  { name: "Test Cases", icon: ClipboardList, path: "test-cases" },
  { name: "Test Execution", icon: Play, path: "execution" },
  { name: "Bug Reports", icon: Bug, path: "bugs" },
  { name: "QA Reports", icon: FileBarChart, path: "reports" },
];

function Sidebar({ activePage, setActivePage }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Bot size={25} />
        </div>
        <div>
          <h2>Autonomous QA</h2>
          <span>AI Testing Agent</span>
        </div>
      </div>

      <div className="sidebar-section-label">WORKSPACE</div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => {
          const Icon = item.icon;

          return (
            <button
              key={item.path}
              className={`nav-item ${
                activePage === item.path ? "active" : ""
              }`}
              onClick={() => setActivePage(item.path)}
            >
              <Icon size={19} />
              <span>{item.name}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <button
          className={`nav-item ${
            activePage === "settings" ? "active" : ""
          }`}
          onClick={() => setActivePage("settings")}
        >
          <Settings size={19} />
          <span>Settings</span>
        </button>

        <div className="sidebar-user">
          <div className="user-avatar">HK</div>
          <div className="user-info">
            <strong>Hari Krishna</strong>
            <span>Administrator</span>
          </div>
          <ChevronLeft size={17} />
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
