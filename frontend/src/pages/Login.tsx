/* ── Login / Register page ── */
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [isSeller, setIsSeller] = useState(true);
  const [isBuyer, setIsBuyer] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register({ email, password, full_name: name, org_name: orgName, is_seller: isSeller, is_buyer: isBuyer });
      }
      navigate("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container max-w-md mx-auto py-12 animate-fade-in">
      <div className="text-center mb-8">
        <div className="w-16 h-16 rounded-2xl bg-primary-700 flex items-center justify-center
                      text-white font-bold text-3xl mx-auto mb-4">W</div>
        <h1 className="text-2xl font-bold text-charcoal">
          {mode === "login" ? "Sign in to Wast-e" : "Create your account"}
        </h1>
      </div>

      <div className="card p-6 sm:p-8">
        {/* Demo accounts notice */}
        <div className="bg-primary-50 rounded-xl p-4 mb-6">
          <p className="text-sm font-semibold text-primary-700 mb-2">Demo Accounts</p>
          <div className="text-xs text-primary-600 space-y-1">
            <p><strong>Seller:</strong> seller@demo.waste.in</p>
            <p><strong>Buyer:</strong> buyer@demo.waste.in</p>
            <p><strong>Operator:</strong> operator@demo.waste.in</p>
            <p><strong>Admin:</strong> admin@demo.waste.in</p>
            <p><strong>Seller+Buyer:</strong> dual@demo.waste.in</p>
            <p className="mt-2 text-charcoal-lighter">Password for all: <code className="bg-white px-1 rounded">demo1234</code></p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "register" && (
            <>
              <div>
                <label className="input-label">Full Name</label>
                <input className="input-field" value={name} onChange={e => setName(e.target.value)} required />
              </div>
              <div>
                <label className="input-label">Business Name</label>
                <input className="input-field" value={orgName} onChange={e => setOrgName(e.target.value)} placeholder="Optional" />
              </div>
              <div>
                <label className="input-label">I want to...</label>
                <div className="flex gap-3 mt-1">
                  <label className={`flex-1 p-3 rounded-xl border-2 cursor-pointer text-center text-sm font-medium transition-colors ${
                    isSeller ? "border-primary-400 bg-primary-50 text-primary-700" : "border-gray-200 text-charcoal-lighter"}`}>
                    <input type="checkbox" checked={isSeller} onChange={e => setIsSeller(e.target.checked)} className="sr-only" />
                    Sell material
                  </label>
                  <label className={`flex-1 p-3 rounded-xl border-2 cursor-pointer text-center text-sm font-medium transition-colors ${
                    isBuyer ? "border-primary-400 bg-primary-50 text-primary-700" : "border-gray-200 text-charcoal-lighter"}`}>
                    <input type="checkbox" checked={isBuyer} onChange={e => setIsBuyer(e.target.checked)} className="sr-only" />
                    Buy material
                  </label>
                </div>
              </div>
            </>
          )}
          <div>
            <label className="input-label">Email</label>
            <input type="email" className="input-field" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="input-label">Password</label>
            <input type="password" className="input-field" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} />
          </div>

          {error && <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">{error}</div>}

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>

        <div className="text-center mt-4">
          <button onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
            className="text-sm text-primary-700 hover:underline">
            {mode === "login" ? "Don't have an account? Register" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
}
