export async function extractAllCookies(): Promise<chrome.cookies.Cookie[]> {
  const allCookies = await chrome.cookies.getAll({});

  // Deduplicate by name+domain+path
  const seen = new Set<string>();
  return allCookies.filter((c) => {
    const key = `${c.name}:${c.domain}:${c.path}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
