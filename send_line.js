// スプレッドシートからデータを取得し、リマインダーの送信をチェックおよび実行する関数
function checkAndSendReminder() {
  // アクティブなスプレッドシートとそのアクティブなシートを取得
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  // シートの全データ範囲を取得
  const data = sheet.getDataRange().getValues();
  // 各カラムのインデックスを特定する
  const contentCol = data[0].indexOf("名称");
  const startDateCol = data[0].indexOf("開始日時");
  const reminderStatusCol = data[0].indexOf("リマインドステータス");
  // JSTのUTCオフセット(9時間)をミリ秒に変換
  const jstOffset = 9 * 60 * 60 * 1000;

  // データ行をループ処理
  for (let i = 1; i < data.length; i++) {
    const startDateStr = data[i][startDateCol];
    const content = data[i][contentCol];
    let reminderStatus = data[i][reminderStatusCol] || "";

    // 開始日時が設定されており、リマインダーステータスに「__終了__」が含まれていない場合
    if (startDateStr && !reminderStatus.includes("__終了__")) {
      const startDate = new Date(startDateStr);
      startDate.setTime(startDate.getTime() - jstOffset); // UTCからJSTに変換
      const now = new Date();

      // 現在時刻とイベント開始時刻との差を計算
      const diffDays = (startDate - now) / (1000 * 60 * 60 * 24);
      const diffHours = (startDate - now) / (1000 * 60 * 60);
      const diffMinutes = (startDate - now) / (1000 * 60);

      // リマインダーの条件をチェックし、必要に応じてリマインダーを送信
      if (
        diffDays <= 3 &&
        diffDays >= 2 &&
        !reminderStatus.includes("3日前__")
      ) {
        reminderStatus += "3日前__";
        sendLineMessage("3日前__" + content);
      } else if (
        diffDays <= 1 &&
        diffDays >= 0 &&
        !reminderStatus.includes("1日前__")
      ) {
        reminderStatus += "1日前__";
        sendLineMessage("1日前__" + content);
      } else if (
        diffHours < 1 &&
        diffHours >= 0 &&
        !reminderStatus.includes("1時間前__")
      ) {
        reminderStatus += "1時間前__";
        sendLineMessage("1時間前__" + content);
      } else if (
        diffMinutes < 20 &&
        diffMinutes >= 14 &&
        !reminderStatus.includes("15分前__")
      ) {
        reminderStatus += "15分前__";
        sendLineMessage("15分前__" + content);
      } else if (
        diffMinutes < 10 &&
        diffMinutes >= 0 &&
        !reminderStatus.includes("5分前__")
      ) {
        reminderStatus += "5〜10分前__";
        sendLineMessage("5〜10分前__" + content);
      }
      // スプレッドシートにリマインダーステータスを更新
      sheet.getRange(i + 1, reminderStatusCol + 1).setValue(reminderStatus);
    }
  }
}

// LINEにメッセージを送信する関数
function sendLineMessage(message) {
  var url = "https://notify-api.line.me/api/notify";
  var token = "lineのトークン"; // トークンはセキュリティの観点から公開しないように注意
  var options = {
    method: "post",
    headers: { Authorization: "Bearer " + token },
    payload: { message: message },
  };

  UrlFetchApp.fetch(url, options); // URL Fetchサービスを用いてLINE Notify APIにリクエストを送信
}
