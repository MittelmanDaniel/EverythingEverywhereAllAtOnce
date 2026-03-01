export interface HistoryEntry {
  url: string;
  title: string;
  visit_count: number;
  last_visit_time: string;
}

export async function extractBrowserHistory(maxResults = 5000): Promise<HistoryEntry[]> {
  const results = await chrome.history.search({
    text: "",
    maxResults,
    startTime: 0,
  });

  return results
    .filter((item) => item.url && item.title)
    .map((item) => ({
      url: item.url!,
      title: item.title || "",
      visit_count: item.visitCount || 0,
      last_visit_time: item.lastVisitTime
        ? new Date(item.lastVisitTime).toISOString()
        : "",
    }));
}
