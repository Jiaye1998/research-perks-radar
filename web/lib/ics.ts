import type { Perk } from "./types";

// Generate and download an .ics calendar event for a perk's deadline.
// All client-side: builds a Blob and triggers a download. No server.

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function escapeText(s: string): string {
  return s.replace(/([,;\\])/g, "\\$1").replace(/\r?\n/g, "\\n");
}

// "2026-03-15" -> "20260315"
function ymd(isoDate: string): string {
  return isoDate.replace(/-/g, "");
}

// All-day DTEND is exclusive, so it's the day after the deadline.
function nextDayYmd(isoDate: string): string {
  const [y, m, d] = isoDate.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d + 1));
  return `${dt.getUTCFullYear()}${pad(dt.getUTCMonth() + 1)}${pad(dt.getUTCDate())}`;
}

function stampUtc(now: Date): string {
  return (
    `${now.getUTCFullYear()}${pad(now.getUTCMonth() + 1)}${pad(now.getUTCDate())}` +
    `T${pad(now.getUTCHours())}${pad(now.getUTCMinutes())}${pad(now.getUTCSeconds())}Z`
  );
}

export function perkToIcs(perk: Perk): string {
  const start = ymd(perk.deadline!);
  const end = nextDayYmd(perk.deadline!);
  const desc =
    `Apply: ${perk.url}` +
    (perk.amount ? `\nValue: ${perk.amount}` : "") +
    (perk.region_restrictions ? `\nRegion: ${perk.region_restrictions}` : "");
  return [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//research-perks-radar//EN",
    "BEGIN:VEVENT",
    `UID:${perk.id}@research-perks-radar`,
    `DTSTAMP:${stampUtc(new Date())}`,
    `DTSTART;VALUE=DATE:${start}`,
    `DTEND;VALUE=DATE:${end}`,
    `SUMMARY:${escapeText("Deadline: " + perk.title)}`,
    `DESCRIPTION:${escapeText(desc)}`,
    `URL:${perk.url}`,
    "END:VEVENT",
    "END:VCALENDAR",
  ].join("\r\n");
}

export function downloadIcs(perk: Perk): void {
  if (!perk.deadline) return;
  const blob = new Blob([perkToIcs(perk)], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${perk.id}.ics`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
