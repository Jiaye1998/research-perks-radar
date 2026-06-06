import fs from "fs";
import path from "path";
import { PerksFeed } from "./types";

// Read the feed at build time from the public copy (the workflow / local build
// copies data/perks.json here). Falls back to an empty feed so builds never
// crash if the file is missing.
export function loadFeed(): PerksFeed {
  try {
    const raw = fs.readFileSync(
      path.join(process.cwd(), "public", "perks.json"),
      "utf-8"
    );
    return JSON.parse(raw) as PerksFeed;
  } catch {
    return {
      generated_at: "",
      count: 0,
      by_category: {} as PerksFeed["by_category"],
      perks: [],
    };
  }
}
