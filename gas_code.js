/**
 * 外部APIからデータを取得してGoogleスプレッドシートを更新します。
 * 「名称」列が空の行を処理し、「文字列インプット」列からAPIを呼び出し、
 * 応答をスプレッドシートに更新します。予定項目は開始/終了時刻、タイトル、
 * 期間が設定され、ToDoはタイトルと入力日のみ更新されます。
 */

// スプレッドシートを更新するメイン関数
function updateSpreadsheetWithResults() {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const scheduleSheet = ss.getSheetByName("スケジュール");
    const oldDataSheet = ss.getSheetByName("old_data");
    const dataRange = scheduleSheet.getDataRange();
    const values = dataRange.getValues();
    const oldDataRange = oldDataSheet.getDataRange();
    const oldValues = oldDataRange.getValues();

    // ヘッダー名に基づいて列インデックスを特定
    const headerIndexes = getHeaderIndexes(values[0]);

    // 新しい行が追加されているか確認し、追加されていれば古いシートにコピー
    copyNewRowsToOldDataSheet(scheduleSheet, oldDataSheet);

   // 削除された項目を特定し、LINEで通知し、old_dataから削除
    notifyAndCleanDeletedItems(scheduleSheet, oldDataSheet);

    // データ行をループ処理
    processRows( dataRange.getValues(), oldDataRange.getValues(), scheduleSheet, headerIndexes);

    // 古いデータをクリアして新しいデータで上書き
    refreshOldDataSheet(scheduleSheet, oldDataSheet);
}

// 削除された項目を特定してLINEで通知し、old_data シートからも削除する関数
function notifyAndCleanDeletedItems(scheduleSheet, oldDataSheet) {
    const scheduleValues = scheduleSheet.getDataRange().getValues();
    const oldValues = oldDataSheet.getDataRange().getValues();
    const scheduleNames = scheduleValues.map(row => row[3]); // 名称列が0番目だと仮定
    let rowsToDelete = [];

    oldValues.forEach((row, index) => {
        if (!scheduleNames.includes(row[3]) && row[3] !== '') {
            sendLineMessage(`削除された項目: ${row[3]}`);
            rowsToDelete.push(index + 1); // 行は1から始まるため
        }
    });

    // 行を後ろから削除する
    rowsToDelete.reverse().forEach(rowNum => {
        oldDataSheet.deleteRow(rowNum);
        scheduleSheet.deleteRow(rowNum);
    });
}
// ヘッダーから列インデックスを抽出する補助関数
function getHeaderIndexes(headers) {
    return {
        name: headers.indexOf('名称'),
        startDate: headers.indexOf('開始日時'),
        endDate: headers.indexOf('終了日時'),
        remindSet: headers.indexOf('リマインドセット'),
        inputText: headers.indexOf('文字列インプット'),
        status: headers.indexOf('ステータス'),
        remindStatus: headers.indexOf('リマインドステータス'),
        inputDate: headers.indexOf('入力日時'),
        duration: headers.indexOf('日数'),
        translatedText: headers.indexOf('文字列インプットの英訳')
    };
}

// 新しい行を古いデータシートにコピーする関数
function copyNewRowsToOldDataSheet(scheduleSheet, oldDataSheet) {
    const mainLastRow = scheduleSheet.getLastRow();
    const oldLastRow = oldDataSheet.getLastRow();
    if (mainLastRow > oldLastRow) {
        const newRows = scheduleSheet.getRange(oldLastRow + 1, 1, mainLastRow - oldLastRow, scheduleSheet.getLastColumn()).getValues();
        oldDataSheet.getRange(oldLastRow + 1, 1, newRows.length, newRows[0].length).setValues(newRows);
    }
}

// 行を処理する関数
function processRows(values, oldValues, sheet, indexes) {
    let processedRows = 0;
    for (let i = 1; i < values.length; i++) {
        if (values[i][indexes.name] === '' && values[i][indexes.inputText] !== '') {
            updateRowBasedOnAPIResponse(i, values[i], sheet, indexes);
            processedRows++;
        }
        checkAndUpdateDateChanges(i, values[i], oldValues[i], sheet, indexes);
    }
    if (processedRows > 0) {
        sendLineMessage(`Updated ${processedRows} rows.`);
    // } else {
    //     sendLineMessage("No rows needed updating.");
    }
}

// API応答に基づいて行を更新する関数
function updateRowBasedOnAPIResponse(rowIndex, row, sheet, indexes) {
    const result = callExternalAPI(row[indexes.inputText]);
    const translatedText = LanguageApp.translate(row[indexes.inputText], 'ja', 'en');
    sheet.getRange(rowIndex + 1, indexes.translatedText + 1).setValue(translatedText);
    Logger.log(result[0]);

    // 追加のデータをセットアップ
    if (result[0] === 'schedule') {
        const scheduleDetails = result[1];
        const formattedStartDate = formatDate(scheduleDetails.DTSTART);
        const formattedEndDate = formatDate(scheduleDetails.DTEND);
        sheet.getRange(rowIndex + 1, indexes.startDate + 1).setValue(formattedStartDate);
        sheet.getRange(rowIndex + 1, indexes.endDate + 1).setValue(formattedEndDate);
        sheet.getRange(rowIndex + 1, indexes.name + 1).setValue(scheduleDetails.title);
        sheet.getRange(rowIndex + 1, indexes.remindSet + 1).setValue(true);
        sheet.getRange(rowIndex + 1, indexes.status + 1).setValue(false);
        sheet.getRange(rowIndex + 1, indexes.inputDate + 1).setValue(new Date().toISOString());
        sheet.getRange(rowIndex + 1, indexes.duration + 1).setValue(scheduleDetails.duration);
    } else {
        sheet.getRange(rowIndex + 1, indexes.name + 1).setValue(result[1]);
        sheet.getRange(rowIndex + 1, indexes.status + 1).setValue(false);
        sheet.getRange(rowIndex + 1, indexes.inputDate + 1).setValue(new Date().toISOString());
    }
}

// 開始日または終了日が変更されているか確認し、必要に応じて更新
function checkAndUpdateDateChanges(rowIndex, row, oldRow, sheet, indexes) {
    if (row[indexes.startDate] !== oldRow[indexes.startDate] ||
        row[indexes.endDate] !== oldRow[indexes.endDate]) {
        sheet.getRange(rowIndex + 1, indexes.remindStatus + 1).setValue('');
        if (indexes.name != ""){
            sendLineMessage(`Updated ${row[indexes.name]} changes in Start/End dates.`);
        }
    }
}

// 既存データをクリアし新しいデータで更新する関数
function refreshOldDataSheet(scheduleSheet, oldDataSheet) {
    oldDataSheet.clear();
    const range = scheduleSheet.getDataRange();
    const data = range.getValues();
    oldDataSheet.getRange(1, 1, data.length, data[0].length).setValues(data);
}

// 日時をフォーマットする補助関数
function formatDate(dateString) {
    const date = new Date(dateString);
    return Utilities.formatDate(date, "Asia/Tokyo", "yyyy-MM-dd'T'HH:mm:ss'Z'");
}

// 外部APIを呼び出す関数
function callExternalAPI(text) {
    const apiUrl = "https://example.com/api";
    const options = {
        method: 'POST',
        contentType: 'application/json',
        payload: JSON.stringify({ text: text })
    };
    const response = UrlFetchApp.fetch(apiUrl, options);
    return JSON.parse(response.getContentText()).result;
}

// LINEへメッセージ送信
function sendLineMessage(message) {
    const lineNotifyToken = "YOUR_LINE_NOTIFY_TOKEN";
    const options = {
        method: 'post',
        headers: {'Authorization': 'Bearer ' + lineNotifyToken},
        payload: 'message=' + message
    };
    UrlFetchApp.fetch('https://notify-api.line.me/api/notify', options);
}
