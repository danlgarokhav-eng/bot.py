/*
 * Этот файл больше НЕ обращается напрямую к Wildberries.
 *
 * Прямой запрос из Google Apps Script к WB мог сам создавать
 * дополнительные запросы и получать 429.
 *
 * Если позже разместишь свой feed.json/API на сервере,
 * укажи его URL в FEED_URL.
 */

var FEED_URL = "";

function doGet(e) {
  if (!FEED_URL) {
    return ContentService
      .createTextOutput(JSON.stringify({
        ok: false,
        error: "FEED_URL не настроен"
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  try {
    var response = UrlFetchApp.fetch(FEED_URL, {
      muteHttpExceptions: true
    });

    return ContentService
      .createTextOutput(response.getContentText())
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({
        ok: false,
        error: String(error)
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
