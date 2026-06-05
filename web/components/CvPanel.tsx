"use client";

import { useState } from "react";
import { Perk } from "@/lib/types";
import { matchCvToPerks, Provider } from "@/lib/cv-match";

export default function CvPanel({
  perks,
  onMatched,
}: {
  perks: Perk[];
  onMatched: (results: { id: string; fit: number; reason: string }[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const [cv, setCv] = useState("");
  const [provider, setProvider] = useState<Provider>("anthropic");
  const [key, setKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setError("");
    if (!cv.trim()) return setError("Paste your CV first.");
    if (!key.trim()) return setError("Enter your API key.");
    setLoading(true);
    try {
      const results = await matchCvToPerks(cv, perks, provider, key);
      if (!results.length)
        setError("No matches parsed — try again or check your key.");
      else onMatched(results);
    } catch (e: any) {
      setError(e?.message || "Request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="cv-panel">
      <div className="cv-head" onClick={() => setOpen((o) => !o)}>
        <h3>🎯 Match perks to your CV</h3>
        <span className="hint">{open ? "Hide" : "Paste your CV →"}</span>
      </div>
      {open && (
        <div className="cv-body">
          <textarea
            placeholder="Paste your CV / resume text here. Field, career stage, and nationality help the most."
            value={cv}
            onChange={(e) => setCv(e.target.value)}
          />
          <div className="cv-controls">
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value as Provider)}
            >
              <option value="anthropic">Anthropic (Claude)</option>
              <option value="openai">OpenAI (GPT)</option>
              <option value="google">Google (Gemini)</option>
            </select>
            <input
              type="password"
              placeholder={`Your ${provider} API key`}
              value={key}
              onChange={(e) => setKey(e.target.value)}
            />
            <button className="btn" onClick={run} disabled={loading}>
              {loading ? "Matching…" : "Match"}
            </button>
          </div>
          {error && <div className="err">{error}</div>}
          <p className="privacy">
            Your CV and API key stay in your browser — they go directly to the
            provider you choose and never to any server we run (there are none).
            Matching uses a small, low-cost model.
          </p>
        </div>
      )}
    </div>
  );
}
