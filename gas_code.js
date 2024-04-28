/**
 * Updates a Google Spreadsheet with data retrieved from an external API.
 * It processes rows with an empty "名称" column, calls an API with the text from "文字列インプット" column,
 * and updates the spreadsheet with the response. Schedule items get start/end times, title, and duration set,
 * while todos only update the title and input date.
 */

// Main function to update the spreadsheet based on results from an external API.
function updateSpreadsheetWithResults() {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var dataRange = sheet.getDataRange();
    var values = dataRange.getValues();

    // Identify column indexes based on header names.
    var nameColumnIndex = values[0].indexOf('名称');
    var startDateColumnIndex = values[0].indexOf('開始日時');
    var endDateColumnIndex = values[0].indexOf('終了日時');
    var remindSetColumnIndex = values[0].indexOf('リマインドセット');
    var inputTextColumnIndex = values[0].indexOf('文字列インプット');
    var inputStatuColumnIndex = values[0].indexOf('ステータス');
    var inputDateColumnIndex = values[0].indexOf('入力日時');
    var inputDurationColumnIndex = values[0].indexOf('日数');
    var translatedTextColumnIndex = values[0].indexOf('文字列インプットの英訳');  // 新しい列のインデックス

    // Loop through rows, skipping the header.
    for (var i = 1; i < values.length; i++) {
        var row = values[i];

        // Process rows where "名称" is empty and "文字列インプット" is not.
        if (row[nameColumnIndex] === '' && row[inputTextColumnIndex] !== '') {
            var result = callExternalAPI(row[inputTextColumnIndex]);

            // 翻訳を行い、結果を「文字列インプットの英訳」列にセット
            var translatedText = LanguageApp.translate(row[inputTextColumnIndex], 'ja', 'en');
            sheet.getRange(i + 1, translatedTextColumnIndex + 1).setValue(translatedText);

            // ログとその他の処理
            Logger.log(result[0]);
            
            if (result[0] === 'schedule') {
                // If schedule, set start/end times, title, remind flag, status, input date, and duration.
                var scheduleDetails = result[1];
                // 日時フォーマットを統一する
                var formattedStartDate = formatDate(scheduleDetails.DTSTART);
                var formattedEndDate = formatDate(scheduleDetails.DTEND);
                sheet.getRange(i + 1, startDateColumnIndex + 1).setValue(formattedStartDate);
                sheet.getRange(i + 1, endDateColumnIndex + 1).setValue(formattedEndDate);

                sheet.getRange(i + 1, nameColumnIndex + 1).setValue(scheduleDetails.title);
                sheet.getRange(i + 1, remindSetColumnIndex + 1).setValue(true);
                sheet.getRange(i + 1, inputStatuColumnIndex + 1).setValue(false);
                sheet.getRange(i + 1, inputDateColumnIndex + 1).setValue(new Date().toISOString());
                sheet.getRange(i + 1, inputDurationColumnIndex + 1).setValue(scheduleDetails.duration);
            } else {
                // If todo, only set title, status, and input date.
                sheet.getRange(i + 1, nameColumnIndex + 1).setValue(result[1]);
                sheet.getRange(i + 1, inputStatuColumnIndex + 1).setValue(false);
                sheet.getRange(i + 1, inputDateColumnIndex + 1).setValue(new Date().toISOString());
            }
        }
    }
}

// 日時フォーマットを統一するための補助関数
function formatDate(dateString) {
    var date = new Date(dateString);
    // "Asia/Tokyo"タイムゾーンを使用して日時をフォーマットする
    return Utilities.formatDate(date, "GMT", "yyyy-MM-dd'T'HH:mm:ss'Z'");
}


// Function to make a POST request to an external API and return the result.
function callExternalAPI(text) {
    var apiUrl = "https://eventplanner-m0az.onrender.com/process/";
    var options = {
        'method' : 'post',
        'contentType': 'application/json',
        'payload' : JSON.stringify({text: text})
    };

    var response = UrlFetchApp.fetch(apiUrl, options);
    var json = JSON.parse(response.getContentText());
    Logger.log(JSON.stringify(json));

    // Extract and return the relevant part of the API response.
    return json.result;
}
