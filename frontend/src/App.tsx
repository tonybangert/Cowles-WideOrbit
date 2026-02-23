import { Routes, Route, NavLink } from 'react-router-dom';
import { BarChart3, MessageSquare, LayoutDashboard } from 'lucide-react';
import DashboardPage from './pages/DashboardPage';
import ChatPage from './pages/ChatPage';

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
    isActive
      ? 'bg-brand-purple/10 text-brand-purple'
      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
  }`;

export default function App() {
  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-purple to-brand-green flex items-center justify-center">
              <BarChart3 className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-semibold text-gray-900">
                Broadcast Revenue Intelligence
              </h1>
              <p className="text-xs text-gray-500">
                Cowles Project — Powered by Aplora AI
              </p>
            </div>
          </div>

          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={navLinkClass}>
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </NavLink>
            <NavLink to="/chat" className={navLinkClass}>
              <MessageSquare className="w-4 h-4" />
              Chat
            </NavLink>
          </nav>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/chat" element={<ChatPage />} />
        </Routes>
      </main>
    </div>
  );
}
