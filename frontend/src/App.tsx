/* ── Main App — routing, navigation, layout ── */
import { BrowserRouter, Routes, Route, Link, useNavigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import { useState, useEffect, type ReactNode } from "react";
import api from "./api";
import Landing from "./pages/Landing";
import Browse from "./pages/Browse";
import ListingDetail from "./pages/ListingDetail";
import CreateListing from "./pages/CreateListing";
import Requirements from "./pages/Requirements";
import CreateRequirement from "./pages/CreateRequirement";
import HowItWorks from "./pages/HowItWorks";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Orders from "./pages/Orders";
import OrderDetail from "./pages/OrderDetail";
import RecoveryJobs from "./pages/RecoveryJobs";
import RecoveryJobDetail from "./pages/RecoveryJobDetail";
import Messages from "./pages/Messages";
import AdminDashboard from "./pages/AdminDashboard";
import type { Notification } from "./types";
import "./index.css";

function DemoBanner() {
  return (
    <div className="demo-banner">
      ⚠️ <strong>Prototype / Demo</strong> — This is a demonstration with sample data. All businesses, transactions, and measurements are fictional.
    </div>
  );
}

function Nav() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [notifCount, setNotifCount] = useState(0);
  const location = useLocation();

  useEffect(() => { setOpen(false); }, [location.pathname]);

  useEffect(() => {
    if (user) {
      api.get("/notifications").then(r => {
        setNotifCount(r.data.filter((n: Notification) => !n.is_read).length);
      }).catch(() => {});
    }
  }, [user, location.pathname]);

  return (
    <nav className="bg-white border-b border-primary-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-9 h-9 rounded-xl bg-primary-700 flex items-center justify-center
                          text-white font-bold text-lg group-hover:bg-primary-600 transition-colors">
              W
            </div>
            <span className="text-xl font-bold text-primary-700">Wast-e</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            <NavLink to="/browse">Browse Materials</NavLink>
            <NavLink to="/requirements">Buyer Requirements</NavLink>
            <NavLink to="/how-it-works">How It Works</NavLink>
            {!user && <NavLink to="/create-listing">List a Batch</NavLink>}
          </div>

          <div className="hidden md:flex items-center gap-3">
            {user ? (
              <>
                <NavLink to="/dashboard">Dashboard</NavLink>
                <NavLink to="/orders">Orders</NavLink>
                {(user.is_operator || user.is_admin) && (
                  <NavLink to="/recovery">Recovery Jobs</NavLink>
                )}
                <NavLink to="/messages">Messages</NavLink>
                {user.is_admin && <NavLink to="/admin">Admin</NavLink>}
                <Link to="/dashboard" className="relative">
                  {notifCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full
                                   text-[10px] flex items-center justify-center font-bold">{notifCount}</span>
                  )}
                  <span className="text-lg">🔔</span>
                </Link>
                <div className="flex items-center gap-2 ml-2 pl-3 border-l border-gray-200">
                  <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center
                                text-primary-700 font-bold text-sm">
                    {user.full_name[0]}
                  </div>
                  <button onClick={logout} className="text-sm text-charcoal-lighter hover:text-charcoal">
                    Sign out
                  </button>
                </div>
              </>
            ) : (
              <Link to="/login" className="btn-primary text-sm !py-2 !px-4 !min-h-0">Sign In</Link>
            )}
          </div>

          {/* Mobile hamburger */}
          <button onClick={() => setOpen(!open)} className="md:hidden p-2 rounded-lg hover:bg-warm-50"
                  aria-label="Toggle menu">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {open ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden bg-white border-t border-gray-100 animate-fade-in">
          <div className="px-4 py-3 space-y-1">
            <MobileLink to="/browse">Browse Materials</MobileLink>
            <MobileLink to="/requirements">Buyer Requirements</MobileLink>
            <MobileLink to="/how-it-works">How It Works</MobileLink>
            <MobileLink to="/create-listing">List a Batch</MobileLink>
            {user ? (
              <>
                <div className="border-t border-gray-100 my-2" />
                <MobileLink to="/dashboard">Dashboard</MobileLink>
                <MobileLink to="/orders">Orders</MobileLink>
                {(user.is_operator || user.is_admin) && <MobileLink to="/recovery">Recovery Jobs</MobileLink>}
                <MobileLink to="/messages">Messages</MobileLink>
                {user.is_admin && <MobileLink to="/admin">Admin</MobileLink>}
                <div className="border-t border-gray-100 my-2" />
                <button onClick={logout} className="w-full text-left px-3 py-2 text-red-600 rounded-lg hover:bg-red-50">
                  Sign out
                </button>
              </>
            ) : (
              <MobileLink to="/login">Sign In</MobileLink>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}

function NavLink({ to, children }: { to: string; children: ReactNode }) {
  const location = useLocation();
  const active = location.pathname === to || location.pathname.startsWith(to + "/");
  return (
    <Link to={to} className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors
      ${active ? "bg-primary-50 text-primary-700" : "text-charcoal-light hover:bg-warm-50 hover:text-charcoal"}`}>
      {children}
    </Link>
  );
}

function MobileLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link to={to} className="block px-3 py-2.5 text-charcoal hover:bg-warm-50 rounded-lg font-medium">
      {children}
    </Link>
  );
}

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  useEffect(() => { if (!loading && !user) navigate("/login"); }, [user, loading, navigate]);
  if (loading) return <div className="page-container text-center py-20 text-charcoal-lighter">Loading...</div>;
  if (!user) return null;
  return <>{children}</>;
}

function Footer() {
  return (
    <footer className="bg-white border-t border-primary-100 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg bg-primary-700 flex items-center justify-center text-white font-bold">W</div>
              <span className="text-lg font-bold text-primary-700">Wast-e</span>
            </div>
            <p className="text-sm text-charcoal-lighter">A second chance for rejected materials.</p>
          </div>
          <div>
            <h4 className="font-semibold text-sm text-charcoal mb-3">Marketplace</h4>
            <div className="space-y-2">
              <Link to="/browse" className="block text-sm text-charcoal-lighter hover:text-primary-700">Browse Materials</Link>
              <Link to="/requirements" className="block text-sm text-charcoal-lighter hover:text-primary-700">Buyer Requirements</Link>
              <Link to="/create-listing" className="block text-sm text-charcoal-lighter hover:text-primary-700">List a Batch</Link>
            </div>
          </div>
          <div>
            <h4 className="font-semibold text-sm text-charcoal mb-3">Learn More</h4>
            <div className="space-y-2">
              <Link to="/how-it-works" className="block text-sm text-charcoal-lighter hover:text-primary-700">How It Works</Link>
            </div>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-gray-100 text-center text-xs text-charcoal-lighter">
          Wast-e Prototype — Demo Mode — All data is fictional
        </div>
      </div>
    </footer>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen flex flex-col">
          <DemoBanner />
          <Nav />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/browse" element={<Browse />} />
              <Route path="/listings/:id" element={<ListingDetail />} />
              <Route path="/create-listing" element={<ProtectedRoute><CreateListing /></ProtectedRoute>} />
              <Route path="/requirements" element={<Requirements />} />
              <Route path="/create-requirement" element={<ProtectedRoute><CreateRequirement /></ProtectedRoute>} />
              <Route path="/how-it-works" element={<HowItWorks />} />
              <Route path="/login" element={<Login />} />
              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/orders" element={<ProtectedRoute><Orders /></ProtectedRoute>} />
              <Route path="/orders/:id" element={<ProtectedRoute><OrderDetail /></ProtectedRoute>} />
              <Route path="/recovery" element={<ProtectedRoute><RecoveryJobs /></ProtectedRoute>} />
              <Route path="/recovery/:id" element={<ProtectedRoute><RecoveryJobDetail /></ProtectedRoute>} />
              <Route path="/messages" element={<ProtectedRoute><Messages /></ProtectedRoute>} />
              <Route path="/admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
            </Routes>
          </main>
          <Footer />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}
