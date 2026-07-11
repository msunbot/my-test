// Apps Script bound to the Google Sheet that collects Form responses.
// Sends the 4-column reading history as an Excel attachment after every
// new form submission. Runs entirely under the Sheet owner's Google
// account - no API keys, no separate hosting, no email credentials.

var RECIPIENT_EMAIL = 'sunmaggie.wl@gmail.com';
var RESPONSES_SHEET_NAME = 'Form Responses 1'; // update if your tab is named differently
var EXPORT_SHEET_NAME = 'Export';
var COLUMNS = ['Date', 'Time', 'Pressure Left', 'Pressure Right'];

function onFormSubmit(e) {
  sendUpdatedSpreadsheet();
}

// Run this once manually from the Apps Script editor to authorize
// permissions and confirm everything works before relying on the trigger.
function testSendNow() {
  sendUpdatedSpreadsheet();
}

function sendUpdatedSpreadsheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var responses = ss.getSheetByName(RESPONSES_SHEET_NAME);
  if (!responses) {
    throw new Error(
      'Could not find a sheet tab named "' + RESPONSES_SHEET_NAME + '". ' +
      'Check the exact tab name at the bottom of the spreadsheet and update RESPONSES_SHEET_NAME.'
    );
  }

  var data = responses.getDataRange().getValues();
  var headerRow = data[0];
  var colIndex = {};
  COLUMNS.forEach(function (name) {
    var idx = headerRow.indexOf(name);
    if (idx === -1) {
      throw new Error(
        'Could not find a column named "' + name + '" in the form responses. ' +
        'Make sure your form question titles are exactly: ' + COLUMNS.join(', ')
      );
    }
    colIndex[name] = idx;
  });

  var exportSheet = ss.getSheetByName(EXPORT_SHEET_NAME);
  if (exportSheet) {
    exportSheet.clear();
  } else {
    exportSheet = ss.insertSheet(EXPORT_SHEET_NAME);
  }

  exportSheet.appendRow(COLUMNS);
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    exportSheet.appendRow(COLUMNS.map(function (name) {
      return row[colIndex[name]];
    }));
  }
  SpreadsheetApp.flush();

  var excelBlob = exportSheetAsExcel(ss, exportSheet);

  GmailApp.sendEmail(
    RECIPIENT_EMAIL,
    'Eye Pressure Readings',
    'Attached is the latest eye pressure readings spreadsheet.\n\n' +
    'This was sent automatically after a new reading was submitted.',
    { attachments: [excelBlob], name: 'Eye Pressure Tracker' }
  );
}

function exportSheetAsExcel(ss, sheet) {
  var url = 'https://docs.google.com/spreadsheets/d/' + ss.getId() +
    '/export?format=xlsx&gid=' + sheet.getSheetId();
  var token = ScriptApp.getOAuthToken();
  var response = UrlFetchApp.fetch(url, {
    headers: { Authorization: 'Bearer ' + token }
  });
  return response.getBlob().setName('eye_pressure_readings.xlsx');
}
