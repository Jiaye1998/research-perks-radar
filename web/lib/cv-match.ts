import type { Perk } from "./types";

export type Provider = "anthropic" | "openai" | "google";

export interface MatchResult {
  id: string;
  fit: number; // 0-100
  reason: string;
}

/**
 * Match perks to a CV by calling the user's chosen LLM provider DIRECTLY
 * from the browser. The CV text and API key never leave the user's machine
 * (they go straight to the provider's API, not to any server we control).
 */
export async function matchCvToPerks(
  cv: string,
  perks: Perk[],
  provider: Provider,
  apiKey: string
): Promise<MatchResult[]> {
  // Send a compact list so the prompt stays small/cheap.
  const slim = perks.slice(0, 60).map((p) => ({
    id: p.id,
    title: p.title,
    category: p.category,
    amount: p.amount,
    deadline: p.deadline,
    region: p.region_restrictions,
    summary: p.summary?.slice(0, 160),
  }));

  const system =
    "You are a matcher that scores research perks against a researcher's CV. " +
    "Return ONLY valid JSON: an array of objects with keys id, fit (0-100 integer), " +
    "and reason (max 12 words). Higher fit = more relevant to this person's field, " +
    "career stage, and eligibility (watch nationality/region constraints). " +
    "No markdown, no prose, no code fences.";

  const user =
    `CV:\n${cv.slice(0, 6000)}\n\nPERKS (JSON):\n${JSON.stringify(slim)}`;

  let raw = "";
  if (provider === "anthropic") raw = await callAnthropic(apiKey, system, user);
  else if (provider === "openai") raw = await callOpenAI(apiKey, system, user);
  else raw = await callGoogle(apiKey, system, user);

  return parseJsonArray(raw);
}

function parseJsonArray(text: string): MatchResult[] {
  const cleaned = text.replace(/```json|```/g, "").trim();
  const start = cleaned.indexOf("[");
  const end = cleaned.lastIndexOf("]");
  if (start === -1 || end === -1) return [];
  try {
    const arr = JSON.parse(cleaned.slice(start, end + 1));
    return arr
      .filter((x: any) => x && x.id)
      .map((x: any) => ({
        id: String(x.id),
        fit: Math.max(0, Math.min(100, Number(x.fit) || 0)),
        reason: String(x.reason || "").slice(0, 80),
      }));
  } catch {
    return [];
  }
}

async function callAnthropic(key: string, system: string, user: string) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": key,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify({
      model: "claude-3-5-haiku-20241022",
      max_tokens: 2000,
      system,
      messages: [{ role: "user", content: user }],
    }),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data?.error?.message || "Anthropic request failed");
  return (data.content || [])
    .filter((b: any) => b.type === "text")
    .map((b: any) => b.text)
    .join("\n");
}

async function callOpenAI(key: string, system: string, user: string) {
  const r = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${key}`,
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: system },
        { role: "user", content: user },
      ],
    }),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data?.error?.message || "OpenAI request failed");
  return data.choices?.[0]?.message?.content || "";
}

async function callGoogle(key: string, system: string, user: string) {
  const r = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${key}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: system }] },
        contents: [{ role: "user", parts: [{ text: user }] }],
      }),
    }
  );
  const data = await r.json();
  if (!r.ok) throw new Error(data?.error?.message || "Google request failed");
  return (
    data.candidates?.[0]?.content?.parts?.map((p: any) => p.text).join("\n") ||
    ""
  );
}
