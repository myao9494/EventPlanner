import re
import pendulum
import calendar

# 年に関して処理すべきリスト
nitigo = r"([0-9]{1,3})日後(.*)"
shu_go = r"([0-9]{1,3})週[間]?後(.*)"
tuki_go = r"([0-9]{1,3})[ヶ]?月後(.*)"
getsu_matsu = r"[今]?月末(.*)"
shu_matsu = r"[今]?週末(.*)"


li_p_1_y = [r"(.*)来年の(.*)", r"(.*)来年(.*月)"]  # +1年になる表現
li_p_2_y = [r"(.*)再来年(.*月)"]  # +2年になる表現
hosei_year = r"(.[0-9])年"  # 2桁で表示する場合に引っ掛ける


# 日付に関して処理すべきリスト
li_p_14 = [r"再来週.*[月火水木金土日]曜"]  # +14日となる表現
# li_p_next = [r"次の.*[月火水木金土日]曜",r"今度.*[月火水木金土日]曜"]
li_p_7 = [r"来週.*[月火水木金土日]曜"]  # +7日となる表現
li_p_0 = [r"今週.*[月火水木金土日]曜", r"次.*[月火水木金土日]曜", r"[月火水木金土日]曜"]  # +0日となる表現
li_today = [r"今日.*"]  # +0日となる表現(曜日指定なし)
# li_tommorow = [r"明日.*時"]#+1日となる表現(曜日指定なし)
# li_da_tommorow = [r"明後日.*時"]#+2日となる表現(曜日指定なし)
li_tommorow = [r"明日.*"]  # +1日となる表現(曜日指定なし)
li_da_tommorow = [r"明後日.*"]  # +2日となる表現(曜日指定なし)

# 時間に関して処理すべきリスト
li_p_12_ji = [r"午後(.*)時", r"夕方(.*)時", r"夜(.*)時", r"昼(.*)時"]  # 午後となる表現
li_tokushu_ji = {"正午": "12時"}  # 特殊な場合

# 年月日を引っ掛ける正規表現
y_p = r'([12]\d{3})[/\-年.]'  # 年を引っ掛ける
# y_wa_p = r'(明治|大正|昭和|平成|令和)\d{1,2}年'
m_p = r'(0?[1-9]|1[0-2])[/\-月.]'  # 月を引っ掛ける
# d_p =  r'([12][0-9]|3[01]|0?[1-9])'#日を引っ掛ける
d_p = r'([12][0-9]日?|3[01]日?|0?[1-9]日?)'  # 日を引っ掛ける
# h_p =  r'((0?|1)[0-9]|2[0-3])[:時]'
h_p = r'(0?|[0-9]|1[0-9]|2[0-9])[:時]'  # 時間を引っ掛ける
min_p = r'([0-5][0-9]|0?[0-9])'  # 分を引っ掛ける

# 予定の前にある削除すべき助詞リスト
jyoshi_li = [r"^から", r"^に", r"^は"]


def main(string, kiten_datetime):
    string = string.translate(str.maketrans(
        {chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))  # 半角に変換
    try:
        string = year_shori(string, kiten_datetime)  # 年の処理
        string = date_trans(string, kiten_datetime)  # 月と日の処理
        string = time_shori(string)  # 時間の処理
        print(string)
        datetime = _re_search(y_p+m_p+d_p+r".*"+h_p+min_p, string)
        if datetime:
            datetime_st = datetime.group().replace(" ", "")
            datetime_st = datetime_st.replace("　", "")
            y, datetime_st = _toridasi(datetime_st, y_p)
            M, datetime_st = _toridasi(datetime_st, m_p)
            d, datetime_st = _toridasi(datetime_st, d_p)
            h, datetime_st = _toridasi(datetime_st, h_p)
            mi, datetime_st = _toridasi(datetime_st, min_p)

            naiyo = string[datetime.end():]
            naiyo = naiyo.replace(" ", "")
            naiyo = naiyo.replace("　", "")
            result = _re_search(r"^分", naiyo)
            if result:
                naiyo = naiyo[result.end():]
            naiyo = _delete_jyosi(naiyo)

            out = y, M, d, h, mi, naiyo,string
        else:
            print("失敗")
            out = False, string, datetime
    except:
        print("dame")
        out = False,string,""

    return out


def get_last_date(dt):
    return dt.replace(day=calendar.monthrange(dt.year, dt.month)[1])


def _delete_jyosi(naiyo):
    for i in jyoshi_li:
        result = _re_search(i, naiyo)
        if result:
            print(naiyo)
            naiyo = naiyo[result.end():]
        else:
            naiyo = naiyo
    return naiyo


def year_shori(string, kiten_datetime):
    """年の曖昧な表現を明確にする関数(来年とか再来年とか、年が入ってないとか)

    Args:
        string (str): 曖昧な表現を含んだ文字列
        kiten_datetime (datetime): 起点となる文字列

    Returns:
        str: 年に関して曖昧な表現を含まない文字列
    """
    # x日後を表す表現の処理
    if _re_search(nitigo, string):
        days = re.sub(nitigo, r"\1", string)
        naiyo = re.sub(nitigo, r"\2", string)
        tg = kiten_datetime.add(days=int(days)).strftime('%Y年%m月%d')
        print(tg)
        string = re.sub(nitigo, tg, string) + naiyo
    # x週後を表す表現の処理
    if _re_search(shu_go, string):
        shu_su = re.sub(shu_go, r"\1", string)
        naiyo = re.sub(shu_go, r"\2", string)
        tg = kiten_datetime.add(weeks=int(shu_su)).strftime('%Y年%m月%d')
        print(tg)
        string = re.sub(shu_go, tg, string) + naiyo
    # x月後を表す表現の処理
    if _re_search(tuki_go, string):
        shu_su = re.sub(tuki_go, r"\1", string)
        naiyo = re.sub(tuki_go, r"\2", string)
        tg = kiten_datetime.add(months=int(shu_su)).strftime('%Y年%m月%d')
        print(tg)
        string = re.sub(tuki_go, tg, string) + naiyo

    # 月末を表す表現の処理
    if _re_search(getsu_matsu, string):
        # shu_su = re.sub(tuki_go, r"\1", string)
        naiyo = re.sub(getsu_matsu, r"\1", string)
        tg = get_last_date(kiten_datetime).strftime('%Y年%m月%d')
        print(tg)
        string = re.sub(getsu_matsu, tg, string) + naiyo

    # 週末を表す表現の処理
    if _re_search(shu_matsu, string):
        # shu_su = re.sub(tuki_go, r"\1", string)
        naiyo = re.sub(shu_matsu, r"\1", string)
        today = pendulum.today()
        sun = 6 - today.weekday()
        this_sun = today.add(days=sun)
        tg = this_sun.strftime('%Y年%m月%d')
        print(tg)
        string = re.sub(shu_matsu, tg, string) + naiyo

    # 2年後を表す表現の処理
    for i in li_p_2_y:  # 再来年は今の年+2年
        if _re_search(i, string):
            y = str(kiten_datetime.add(years=2).year)+"年"
            a = r'\1 '+y + r'\2'
            print(a)
            string = re.sub(i, a, string)[1:]
    # 1年後を表す表現の処理
    for i in li_p_1_y:  # 来年は今の年+1年（再来年を先に処理する）
        if _re_search(i, string):
            y = str(kiten_datetime.add(years=1).year)+"年"
            a = r'\1 '+y + r'\2'
            string = re.sub(i, a, string)[1:]
    # 年が2桁の場合は2000を足すにする
    result = _re_search(y_p, string)
    if not result:
        nen = _re_search(hosei_year, string)
        if nen:
            nen = re.sub(r"\D", "", nen.group())
            if len(nen) == 2:
                nen_temp = int(nen)+2000
                string = string.replace(nen, str(nen_temp))
    # 年がない場合は今年にする
    result = _re_search(y_p, string)
    if not result:
        if _re_search(m_p, string):
            string = str(kiten_datetime.year)+"年"+string
            datetime_st = _re_search(
                y_p+m_p+d_p, string).group().replace(" ", "")
            y, datetime_st = _toridasi(datetime_st, y_p)
            M, datetime_st = _toridasi(datetime_st, m_p)
            D, datetime_st = _toridasi(datetime_st, d_p)
            delta = (pendulum.datetime(int(y), int(M),
                     int(D), 0, 0, 0) - kiten_datetime).days

            if delta < 0:
                print("来年の話ですね！")
                string = string.replace(
                    str(kiten_datetime.year)+"年", str(kiten_datetime.year+1)+"年")
            else:
                pass
        else:
            string = str(kiten_datetime.year)+"年"+string
    return string


def date_trans(string, kiten_datetime):
    """日付に関する処理を実施

    Args:
        string (str): インプットの文字列(曖昧な指示の文字列)
        kiten_datetime (datetime)): 起点となる日付
    Returns:
        str: 日付に関して曖昧な表現を変換した文字列
    """
    flg = False
    for i in li_p_14:  # 再来週の月曜日、、とかを処理
        #         print(i)
        result = _re_search(i, string)
        if result:
            tg = _trans_yobi_to_date(result.group(), 7, kiten_datetime)
            string = string.replace(result.group(), tg+" ")
            flg = True
            break

    if not flg:
        for i in li_p_7:  # 来週の月曜日、、とかを処理
            #             print(i)
            result = _re_search(i, string)
            if result:
                tg = _trans_yobi_to_date(result.group(), 0, kiten_datetime)
                string = string.replace(result.group(), tg)
                flg = True
                break

    if not flg:
        for i in li_p_0:  # 今週の月曜日、、とかを処理
            #             print(i)
            result = _re_search(i, string)
            if result:
                tg = _trans_yobi_to_date(
                    result.group(), 0, kiten_datetime, next_week_opp=False, konsh_opp=True)
                string = string.replace(result.group(), tg)
                flg = True
                break

    if not flg:
        for i in li_today:  # 今日の10時、、、とかを処理
            #             print(i)
            result = _re_search(i, string)
            if result:
                tg = kiten_datetime.add(days=0).strftime('%m月%d')
                r_temp = re.search(i[:-3], result.group())
                string = string.replace(r_temp.group(), tg)
                flg = True
                break

    if not flg:
        for i in li_tommorow:  # 明日の10時、、、とかを処理
            #             print(i)
            result = _re_search(i, string)
            if result:
                tg = kiten_datetime.add(days=1).strftime('%m月%d')
                r_temp = re.search(i[:-3], result.group())
                string = string.replace(r_temp.group(), tg)
                flg = True
                break

    if not flg:
        for i in li_da_tommorow:  # 明後日の10時、、、とかを処理
            #             print(i)
            result = _re_search(i, string)
            if result:
                tg = kiten_datetime.add(days=2).strftime('%m月%d')
                r_temp = re.search(i[:-3], result.group())
                string = string.replace(r_temp.group(), tg)
                flg = True
                break
    return string


def time_shori(string):
    """時間に関する処理を実施 正午や半とか
    Args:
        string (str): インプットの文字列(曖昧な指示の文字列)
    Returns:
        str: 時間に関して曖昧な表現を変換した文字列
    """
    for word, read in li_tokushu_ji.items():  # 正午のような特殊文字を処理
        string = string.replace(word, read)

    string = _hun_hosei(string)  # 半を３０分とか、丁度の場合0分で補正

    for i in li_p_12_ji:  # 午後とか、昼のなどを処理
        result = _re_search(i, string)
        if result:
            jikan = re.findall(i, result.group())[0]
            jikan = result.group().replace(jikan, str(int(re.sub(r"\D", "", jikan))+12))
            string = string.replace(result.group(), jikan)

    if not _re_search(h_p+min_p, string):  # 時間が入ってない場合は、7：00にセット
        result = _re_search(y_p+m_p+d_p, string)
        if result:
            if string.find("/"):
                string = string.replace(
                    result.group(), result.group()+"日 7時0分")
            else:
                string = string.replace(result.group(), result.group()+" 7時0分")

    return string


def _hun_hosei(string):
    """分に関する曖昧表現除去 time_shoriの子関数

    Args:
        string (str): インプットの文字列(曖昧な指示の文字列)
    Returns:
        str: 分に関して曖昧な表現を変換した文字列
    """
    result_1 = _re_search(h_p, string)  # 時間でマッチ
    result_2 = _re_search(h_p+min_p, string)  # 時間と分でマッチ
    result_3 = _re_search(h_p+"半", string)  # 時間半があるかを確認

    if not result_1:
        pass
#         print("時間が指定されてないです")

    elif result_1 and not result_2:
        #         print("時間があって、分がないので、半があれば30分、その他は0分にします")
        if result_3:
            string = string.replace(result_3.group(), result_1.group()+"30分")
        else:
            string = string.replace(result_1.group(), result_1.group()+"0分")

    return string


def _re_search(pattern, string):
    """正規表現でマッチングを実施し、結果を返します(一応早いとのこと)

    Args:
        pattern (str): 正規表現のパターン
        string (str): 対象の文字列

    Returns:
        str or bool: 成功すれば結果(sarchの結果)を返す。失敗すればfalse
    """
    prog = re.compile(pattern)
    result = prog.search(string)
    if result:
        out = result
    else:
        out = False
    return out


def _trans_yobi_to_date(a, n, kiten_datetime, next_week_opp=True, konsh_opp=False):
    """曜日を起点に対してプラス処理して日付に変換する(例:日曜 → 12月15)

    Args:
        a (str): 対象の文字列
        n (int): 何日伸ばすか(来週なら7日、再来週なら14日)
        kiten_datetime(datetime): 起点となる日時
        next_week_opp (bool, optional): 次週を前提とする場合 このオプションを入れないと次の週にならない. Defaults to True.
        konsh_opp (bool, optional): 今週を前提とする場合 このオプションをつけないと必ず今週にならない. Defaults to False.

    Returns:
        str: 12月15 のような日付を返す
    """

    # 起点日時の次の指定曜日の日付を取得
    if "日曜" in a:
        tg = kiten_datetime.next(pendulum.SUNDAY)
    elif "月曜" in a:
        tg = kiten_datetime.next(pendulum.MONDAY)
    elif "火曜" in a:
        tg = kiten_datetime.next(pendulum.TUESDAY)
    elif "水曜" in a:
        tg = kiten_datetime.next(pendulum.WEDNESDAY)
    elif "木曜" in a:
        tg = kiten_datetime.next(pendulum.THURSDAY)
    elif "金曜" in a:
        tg = kiten_datetime.next(pendulum.FRIDAY)
    elif "土曜" in a:
        tg = kiten_datetime.next(pendulum.SATURDAY)

    if next_week_opp:  # 基準日時と同じ週番号であれば、7日足す　→　必ず来週を出す　日曜日起点であることを注意
        tg_shu = _nan_shu(tg)
        now_shu = _nan_shu(kiten_datetime)
        if tg_shu == now_shu:
            n = n+7

    if konsh_opp:  # 基準日と同じ週番号であれば、OK、異なる場合は、間違い入力と判断して7日たす(勝手に来週の予定にします)
        tg_shu = _nan_shu(tg)
        now_shu = _nan_shu(kiten_datetime)
        if tg_shu != now_shu:
            print("今週はマイナスの日だよ。勝手に来週にしちゃうね!")
            n = n+7
        if tg.weekday() == kiten_datetime.weekday():
            print("今日のことかと、、、")
            n = n-7

    return tg.add(days=n).strftime('%m月%d')


def _nan_shu(target_date):
    """  
    指定された日付からその月の「第N週」かを取得する
      Arguments:
          target_date {datetime} -- 第N週を取得する対象の日付情報

      Returns:
          int -- 第N週の`N`
    https://qiita.com/ksh-fthr/items/e07952619cc265dd5c32
    """
    # カレンダーを日曜日始まりで作成する( firstweekday=6 は日曜日始まりを指定 )
    cl = calendar.Calendar(firstweekday=6)

    # ここからが実際に第N週かを取得する処理
    month_cl = cl.monthdays2calendar(target_date.year, target_date.month)
    week_num = 1
    for week in month_cl:
        for day in week:
            if day[0] == target_date.day:
                return week_num
        week_num += 1
    return week_num


def _toridasi(datetime_st, seiki):
    result = _re_search(seiki, datetime_st)
    return _suji_nomi(re.findall(seiki, datetime_st)[0]), datetime_st[result.end():]


def _suji_nomi(string):
    return re.sub(r"\D", "", string)
