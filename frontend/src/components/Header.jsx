
import { Search, Bell, Sparkles } from "lucide-react";

function Header({ title, subtitle }) {
  return (
    <header className="dashboard-header">
      <div className="header-title">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      <div className="header-actions">
        <div className="search-box">
          <Search size={17} />
          <input placeholder="Search anything..." />
        </div>

        <button className="icon-button" title="Notifications">
          <Bell size={19} />
        </button>

        <button className="ai-button">
          <Sparkles size={17} />
          AI Agent
        </button>
      </div>
    </header>
  );
}

export default Header;
