// Background service worker — handles messages from popup
chrome.runtime.onInstalled.addListener(() => {
  console.log("Everything Everywhere All At Once extension installed");
});
