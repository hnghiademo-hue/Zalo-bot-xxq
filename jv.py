import os
import json
import time
import threading
import urllib.parse
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==============================================================================
# 🚀 ZALO WEATHER, CHART & AI ASSISTANT BOT - VERSION 11.0 PRO MAX
# 👨‍💻 Developer: Nguyen Huu Nghia
# ==============================================================================

DEV_NAME = "Nguyen Huu Nghia"
BOT_VERSION = "v11.0 Pro Max"

BOT_TOKEN = "4600528661577218342:sGojQQEzTlHyasuDbXoIGdpCICBwBZTuPXItLkrLNkzgqiDqyKUldspwhzEnQNzG"
ZALO_API_BASE = f"https://bot-api.zapps.me/bot{BOT_TOKEN}"

OWM_API_KEY = "2de37a1d6a5323fcccbf92701e76d474"
GEMINI_API_KEY = "AQ.Ab8RN6JPvLme0w8a7dhuqQvtn9FLBeGGoiQD7mmk8juMTRifhQ"

DATA_FILE = "subscribers_multi.json"
CONFIG_FILE = "config_multi.json"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

http_session = requests.Session()
http_session.headers.update({"User-Agent": "ZaloBot-V11-NguyenHuuNghia/11.0"})

# Bộ nhớ đệm tọa độ giúp tìm kiếm tức thì
GEO_CACHE = {
    "bắc ninh": {"name": "Bắc Ninh", "lat": 21.1861, "lon": 106.0763},
    "quế võ": {"name": "Quế Võ", "lat": 21.1519, "lon": 106.1558},
    "bồng lai": {"name": "Bồng Lai, Quế Võ", "lat": 21.1180, "lon": 106.2050},
    "từ sơn": {"name": "Từ Sơn", "lat": 21.1167, "lon": 105.9500},
    "yên phong": {"name": "Yên Phong", "lat": 21.2014, "lon": 105.9961},
    "tiên du": {"name": "Tiên Du", "lat": 21.1278, "lon": 106.0389},
    "thuận thành": {"name": "Thuận Thành", "lat": 21.0333, "lon": 106.0833},
    "gia bình": {"name": "Gia Bình", "lat": 21.0667, "lon": 106.2000},
    "lương tài": {"name": "Lương Tài", "lat": 21.0167, "lon": 106.2333},
    "hà nội": {"name": "Hà Nội", "lat": 21.0285, "lon": 105.8542},
    "hải phòng": {"name": "Hải Phòng", "lat": 20.8449, "lon": 106.6881},
    "đà nẵng": {"name": "Đà Nẵng", "lat": 16.0544, "lon": 108.2022},
    "tp. hồ chí minh": {"name": "TP. Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297},
    "hồ chí minh": {"name": "TP. Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297},
}
WEATHER_CACHE = {}

DEFAULT_TEMPLATES = {
    "check": (
        "🌟━━ BẢN TIN THỜI TIẾT V11 ━━🌟\n"
        "🏙️ Khu vực: {tinh}\n"
        "⏰ Giờ hiện tại: {gio_hien_tai}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "{icon} Trạng thái: {nang_mua}\n"
        "🌡️ Nhiệt độ: {nhiet_do}°C (Cảm giác thực: {cam_giac}°C)\n"
        "📊 Biên độ nhiệt: {min}°C ➔ {max}°C\n"
        "💨 Sức gió: {toc_do_gio} km/h ({mo_ta_gio})\n"
        "💧 Độ ẩm: {do_am}% | ☁️ Mây: {may}% | ☔ Mưa: {kha_nang_mua}%\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎉 Chúc bạn ngày hôm nay vui vẻ và tràn đầy năng lượng! 💖\n"
        "👨‍💻 Developer: Nguyen Huu Nghia"
    ),
    "morning": (
        "🌅━━ CHÀO BUỔI SÁNG VUI VẺ ━━☕\n"
        "📍 Khu vực: {tinh} ({gio_hien_tai})\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "{icon} Hôm nay: {nang_mua}\n"
        "🌡️ Nhiệt độ hiện tại: {nhiet_do}°C (Cảm giác: {cam_giac}°C)\n"
        "📈 Trong ngày: {min}°C ➔ {max}°C\n"
        "💨 Sức gió: {toc_do_gio} km/h ({mo_ta_gio})\n"
        "💧 Độ ẩm: {do_am}% | 🌧️ Khả năng mưa: {kha_nang_mua}%\n\n"
        "💡 Lời khuyên: {loi_khuyen}\n"
        "✨ Chúc bạn buổi sáng vui vẻ, may mắn và tốt lành! 🍀\n"
        "👨‍💻 Developer: Nguyen Huu Nghia"
    ),
    "noon": (
        "☀️━━ THỜI TIẾT 12H TRƯA ━━🍱\n"
        "📍 Khu vực: {tinh} ({gio_hien_tai})\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "{icon} Hiện tại: {nang_mua}\n"
        "🔥 Nhiệt độ: {nhiet_do}°C (Cảm giác: {cam_giac}°C)\n"
        "💨 Sức gió: {toc_do_gio} km/h ({mo_ta_gio})\n"
        "💧 Độ ẩm: {do_am}% | ☔ Khả năng mưa chiều: {kha_nang_mua}%\n\n"
        "🍲 Chúc bạn có bữa trưa ngon miệng và nghỉ ngơi thoải mái! 💤\n"
        "👨‍💻 Developer: Nguyen Huu Nghia"
    ),
    "night": (
        "🌙━━ BẢN TIN ĐÊM & NGỦ NGON ━━🌟\n"
        "📍 Khu vực: {tinh} ({gio_hien_tai})\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌌 Đêm nay: {nang_mua}, nhiệt độ {nhiet_do}°C (Cảm giác: {cam_giac}°C)\n"
        "💨 Gió: {toc_do_gio} km/h ({mo_ta_gio}) | 💧 Độ ẩm: {do_am}%\n\n"
        "📅 Dự báo ngày mai tại {tinh}:\n"
        "• Thời tiết: {nang_mua_mai}\n"
        "• Nhiệt độ: {min_mai}°C ➔ {max_mai}°C (Khả năng mưa: {mua_mai}%)\n\n"
        "🛌 Chúc bạn ngủ ngon {tinh} và có một đêm thật sâu giấc! 🌙✨\n"
        "👨‍💻 Developer: Nguyen Huu Nghia"
    ),
}


# ================= QUẢN LÝ FILE DỮ LIỆU =================
def load_data(filename, default_val):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_val.copy()
    return default_val.copy()


def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ================= ĐỊNH VỊ TỌA ĐỘ SIÊU TỐC =================
def geocode_city(query_name):
    key = query_name.strip().lower()
    if key in GEO_CACHE:
        return GEO_CACHE[key]

    try:
        resp = http_session.get(
            "http://api.openweathermap.org/geo/1.0/direct",
            params={"q": f"{query_name},VN", "limit": 1, "appid": OWM_API_KEY},
            timeout=4,
        )
        if resp.status_code == 200 and resp.json():
            item = resp.json()[0]
            loc = {
                "name": item.get("local_names", {}).get("vi", item["name"]),
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
            }
            GEO_CACHE[key] = loc
            return loc
    except Exception:
        pass

    try:
        resp = http_session.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{query_name}, Việt Nam", "format": "json", "limit": 1, "accept-language": "vi"},
            timeout=4,
        )
        if resp.status_code == 200 and resp.json():
            item = resp.json()[0]
            short_name = item.get("display_name", query_name).split(",")[0].strip()
            loc = {"name": short_name, "lat": float(item["lat"]), "lon": float(item["lon"])}
            GEO_CACHE[key] = loc
            return loc
    except Exception:
        pass

    return None


# ================= LẤY THỜI TIẾT & DỮ LIỆU BIỂU ĐỒ 24H =================
def determine_exact_status(is_day, rain_mm, cloud_pct, owm_id=None):
    if owm_id is not None:
        if 200 <= owm_id < 300:
            return "Mưa dông, có sấm chớp", "⛈️"
        if 300 <= owm_id < 400:
            return "Mưa phùn nhẹ", "🌦️"
        if 500 <= owm_id < 600:
            if rain_mm > 5 or owm_id >= 502:
                return "Đang có mưa to", "🌧️"
            return "Có mưa rào nhẹ", "🌦️"
        if 700 <= owm_id < 800:
            return "Trời có sương mù nhẹ", "🌫️"

    if rain_mm >= 4.0:
        return "Đang có mưa vừa đến mưa to", "🌧️"
    elif rain_mm >= 0.2:
        return "Có mưa nhỏ rải rác", "🌦️"

    if cloud_pct <= 20:
        return ("Trời quang mây, nắng đẹp", "☀️") if is_day else ("Trời quang đãng, ít mây", "🌙")
    elif cloud_pct <= 55:
        return ("Trời nắng nhẹ, mây rải rác", "🌤️") if is_day else ("Trời có mây rải rác, mát mẻ", "☁️")
    elif cloud_pct <= 84:
        return ("Trời nhiều mây, nắng dịu", "⛅") if is_day else ("Trời nhiều mây", "☁️")
    else:
        return ("Trời âm u, nhiều mây dày", "☁️")


def get_accurate_weather(city_info, force_refresh=False):
    if isinstance(city_info, str):
        loc = geocode_city(city_info)
        if not loc:
            return None, f"Không tìm thấy khu vực '{city_info}'."
    else:
        loc = city_info

    cache_key = f"{round(loc['lat'], 3)}_{round(loc['lon'], 3)}"
    now_ts = time.time()
    now_vn = datetime.now(VN_TZ)
    now_str = now_vn.strftime("%H:%M:%S - %d/%m/%Y")
    is_day = 6 <= now_vn.hour < 18

    if not force_refresh and cache_key in WEATHER_CACHE:
        cached_time, cached_data = WEATHER_CACHE[cache_key]
        if now_ts - cached_time < 300:
            cached_data["time_str"] = now_str
            return cached_data, None

    lat, lon, formal_name = loc["lat"], loc["lon"], loc["name"]
    temp, feels_like, humidity, wind_kmh, cloud_pct, rain_mm = None, None, None, None, 50, 0.0
    owm_id = None

    try:
        owm_resp = http_session.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"lat": lat, "lon": lon, "appid": OWM_API_KEY, "units": "metric", "lang": "vi"},
            timeout=4,
        )
        if owm_resp.status_code == 200:
            d = owm_resp.json()
            temp = round(d["main"]["temp"], 1)
            feels_like = round(d["main"]["feels_like"], 1)
            humidity = d["main"]["humidity"]
            wind_kmh = round(d.get("wind", {}).get("speed", 0) * 3.6, 1)
            cloud_pct = d.get("clouds", {}).get("all", 50)
            rain_mm = d.get("rain", {}).get("1h", 0.0)
            if d.get("weather"):
                owm_id = d["weather"][0]["id"]
    except Exception:
        pass

    t_min, t_max, rain_prob = (temp - 2 if temp else 23), (temp + 3 if temp else 29), 10
    tmr_min, tmr_max, tmr_rain, tmr_status = 23, 29, 10, "Thời tiết ổn định 🌤️"
    hourly_labels, hourly_temps, hourly_rains = [], [], []

    try:
        om_resp = http_session.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,cloud_cover,wind_speed_10m",
                "hourly": "temperature_2m,precipitation_probability",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
                "timezone": "Asia/Ho_Chi_Minh",
                "forecast_days": 2,
            },
            timeout=4,
        )
        if om_resp.status_code == 200:
            om = om_resp.json()
            curr = om.get("current", {})
            daily = om.get("daily", {})
            hourly = om.get("hourly", {})

            if temp is None:
                temp = round(curr.get("temperature_2m", 25.0), 1)
                feels_like = round(curr.get("apparent_temperature", temp), 1)
                humidity = curr.get("relative_humidity_2m", 75)
                wind_kmh = round(curr.get("wind_speed_10m", 5.0), 1)
                cloud_pct = curr.get("cloud_cover", 50)
                rain_mm = curr.get("precipitation", 0.0)

            t_min = min(temp, round(daily.get("temperature_2m_min", [temp, temp])[0], 1))
            t_max = max(temp, round(daily.get("temperature_2m_max", [temp, temp])[0], 1))
            rain_prob = daily.get("precipitation_probability_max", [10, 10])[0]

            tmr_min = round(daily.get("temperature_2m_min", [23, 23])[1], 1)
            tmr_max = round(daily.get("temperature_2m_max", [29, 29])[1], 1)
            tmr_rain = daily.get("precipitation_probability_max", [10, 10])[1]
            tmr_rain_sum = daily.get("precipitation_sum", [0, 0])[1]

            if tmr_rain >= 60 and tmr_rain_sum >= 2.0:
                tmr_status = "Có khả năng mưa rào 🌦️"
            elif tmr_rain >= 35:
                tmr_status = "Nhiều mây, có thể mưa nhẹ ⛅"
            else:
                tmr_status = "Trời tạnh ráo, nắng đẹp 🌤️"

            # Trích xuất dữ liệu 8 mốc giờ tiếp theo (cách nhau mỗi 3 tiếng) để vẽ biểu đồ /tk
            h_times = hourly.get("time", [])
            h_temps = hourly.get("temperature_2m", [])
            h_probs = hourly.get("precipitation_probability", [])
            curr_hour_idx = now_vn.hour
            for idx in range(curr_hour_idx, min(curr_hour_idx + 24, len(h_times)), 3):
                label = h_times[idx].split("T")[-1][:5]
                hourly_labels.append(label)
                hourly_temps.append(round(h_temps[idx], 1))
                hourly_rains.append(h_probs[idx])
    except Exception:
        pass

    if temp is None:
        return None, "Không thể kết nối máy chủ thời tiết lúc này."

    status_text, icon = determine_exact_status(is_day, rain_mm, cloud_pct, owm_id)
    if wind_kmh < 10:
        wind_desc = "gió nhẹ 🍃"
    elif wind_kmh < 24:
        wind_desc = "gió vừa 🌬️"
    else:
        wind_desc = "gió mạnh 💨"

    result = {
        "name": formal_name,
        "lat": lat,
        "lon": lon,
        "icon": icon,
        "status": status_text,
        "temp": temp,
        "feels_like": feels_like,
        "humidity": humidity,
        "wind_speed": wind_kmh,
        "wind_desc": wind_desc,
        "cloud": cloud_pct,
        "min": t_min,
        "max": t_max,
        "rain_prob": rain_prob,
        "time_str": now_str,
        "tmr_status": tmr_status,
        "tmr_min": tmr_min,
        "tmr_max": tmr_max,
        "tmr_rain": tmr_rain,
        "hourly_labels": hourly_labels or ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
        "hourly_temps": hourly_temps or [t_min, round((t_min + t_max) / 2, 1), t_max, t_max, round((t_min + t_max) / 2, 1), t_min],
        "hourly_rains": hourly_rains or [rain_prob] * 6,
    }
    WEATHER_CACHE[cache_key] = (now_ts, result)
    return result, None


def fetch_all_cities_parallel(user_cities, force_refresh=False):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_accurate_weather, c, force_refresh) for c in user_cities]
        return [f.result() for f in futures]


# ================= TẠO BIỂU ĐỒ THỐNG KÊ (/tk & 5H SÁNG) =================
def generate_weather_chart(w):
    """
    Tạo đồng thời:
    1. Biểu đồ cột trực quan ngay trong tin nhắn Zalo.
    2. Link ảnh biểu đồ đồ họa sắc nét (QuickChart) để hiển thị ảnh trên Zalo.
    """
    labels = w["hourly_labels"]
    temps = w["hourly_temps"]
    rains = w["hourly_rains"]

    # 1. Vẽ biểu đồ trực quan bằng ký tự khối đẹp mắt
    min_t = min(temps) if temps else 20
    max_t = max(temps) if temps else 35
    span = max(max_t - min_t, 1)

    bars_lines = []
    for lbl, t, r in zip(labels, temps, rains):
        bar_len = int(((t - min_t) / span) * 8) + 2
        bar_str = "🟧" * bar_len
        rain_icon = "🌧️" if r >= 50 else ("🌦️" if r >= 25 else "☀️")
        bars_lines.append(f"🕒 {lbl} | {bar_str} {t}°C ({rain_icon} {r}%)")

    ascii_chart = "\n".join(bars_lines)

    # 2. Tạo URL hình ảnh biểu đồ đồ họa độ phân giải cao qua QuickChart API
    chart_config = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "type": "line",
                    "label": "Nhiệt độ (°C)",
                    "borderColor": "#ff4500",
                    "backgroundColor": "rgba(255,69,0,0.15)",
                    "borderWidth": 3,
                    "fill": True,
                    "data": temps,
                    "yAxisID": "y1",
                },
                {
                    "type": "bar",
                    "label": "Khả năng mưa (%)",
                    "backgroundColor": "rgba(30,144,255,0.65)",
                    "data": rains,
                    "yAxisID": "y2",
                },
            ],
        },
        "options": {
            "title": {
                "display": True,
                "text": f"BIỂU ĐỒ THỜI TIẾT 24H - {w['name'].upper()} (Dev: {DEV_NAME})",
                "fontSize": 16,
            },
            "scales": {
                "yAxes": [
                    {"id": "y1", "type": "linear", "position": "left", "ticks": {"suggestedMin": min_t - 2, "suggestedMax": max_t + 2}},
                    {"id": "y2", "type": "linear", "position": "right", "ticks": {"min": 0, "max": 100}, "gridLines": {"drawOnChartArea": False}},
                ]
            },
        },
    }
    encoded_cfg = urllib.parse.quote(json.dumps(chart_config, ensure_ascii=False))
    chart_url = f"https://quickchart.io/chart?w=650&h=380&c={encoded_cfg}"

    text_report = (
        f"📊━━ BIỂU ĐỒ THỐNG KÊ 24H ({w['name'].upper()}) ━━📊\n"
        f"⏰ Cập nhật lúc: {w['time_str']}\n"
        f"🌡️ Hiện tại: {w['temp']}°C | {w['icon']} {w['status']}\n"
        f"📉 Thấp nhất: {w['min']}°C ➔ 📈 Cao nhất: {w['max']}°C\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 DIỄN BIẾN NHIỆT ĐỘ & MƯA THEO GIỜ:\n"
        f"{ascii_chart}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🖼️ Xem ảnh biểu đồ sắc nét: {chart_url}\n"
        f"👨‍💻 Developer: {DEV_NAME}"
    )
    return text_report, chart_url


# ================= TRỢ LÝ ẢO AI THÔNG MINH (KHÔNG BAO GIỜ LẶP LẠI BẢN TIN CŨ) =================
def smart_virtual_assistant(user_message, user_cities):
    """
    Xử lý mọi tin nhắn không có dấu '/' ở đầu như một trợ lý ảo thực thụ.
    Kết nối đa tầng AI + Bộ não phản hồi tiếng Việt thông minh.
    """
    results = fetch_all_cities_parallel(user_cities)
    weather_list = [w for w, _ in results if w]
    w_main = weather_list[0] if weather_list else None

    weather_lines = []
    for w in weather_list:
        weather_lines.append(
            f"- {w['name']}: {w['status']} {w['icon']}, nhiệt độ {w['temp']}°C "
            f"(cảm giác {w['feels_like']}°C, min {w['min']}°C - max {w['max']}°C), "
            f"gió {w['wind_speed']} km/h ({w['wind_desc']}), độ ẩm {w['humidity']}%, mưa {w['rain_prob']}%."
        )
    weather_summary = "\n".join(weather_lines)
    now_vn = datetime.now(VN_TZ)
    now_str = now_vn.strftime("%H:%M ngày %d/%m/%Y")

    system_prompt = (
        f"Bạn là Trợ lý ảo AI thông minh, hài hước và tận tâm trên Zalo (Phiên bản {BOT_VERSION}), "
        f"được sáng tạo và phát triển bởi Developer {DEV_NAME}.\n"
        f"Thời gian hiện tại: {now_str}.\n"
        f"Thông tin thời tiết nơi người dùng đang ở:\n{weather_summary}\n\n"
        f"Quy tắc trả lời:\n"
        f"1. Trò chuyện tự nhiên như một người bạn/trợ lý thực sự bằng tiếng Việt, dùng nhiều emoji đẹp mắt.\n"
        f"2. Giải đáp trực tiếp đúng trọng tâm câu hỏi của người dùng (dù họ hỏi chuyện đời sống, tâm sự, ăn uống, học tập, code hay thời tiết).\n"
        f"3. Tuyệt đối KHÔNG in lại nguyên bảng thông số thời tiết khô khan trừ khi người dùng hỏi trực tiếp về thời tiết.\n"
        f"4. Không dùng dấu ** trong văn bản."
    )

    # Tầng 1: Nếu người dùng dùng Gemini Key chuẩn AIza...
    if GEMINI_API_KEY.startswith("AIza"):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
            resp = http_session.post(
                url,
                json={"contents": [{"parts": [{"text": f"{system_prompt}\n\nNgười dùng nhắn: {user_message}"}]}]},
                timeout=6,
            )
            if resp.status_code == 200:
                ans = resp.json()["candidates"][0]["content"]["parts"][0]["text"].replace("**", "").strip()
                if ans:
                    return f"🤖 {ans}"
        except Exception:
            pass

    # Tầng 2: Cổng Pollinations Chat Completions chuẩn mới
    for endpoint in ["https://text.pollinations.ai/openai/chat/completions", "https://text.pollinations.ai/openai"]:
        try:
            resp = http_session.post(
                endpoint,
                json={
                    "model": "openai",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                },
                timeout=6,
            )
            if resp.status_code == 200:
                data = resp.json()
                ans = data.get("choices", [{}])[0].get("message", {}).get("content", "").replace("**", "").strip()
                if ans:
                    return f"🤖 {ans}"
        except Exception:
            pass

    # Tầng 3: Cổng Pollinations Direct GET (Rất ổn định, không cần key)
    try:
        short_prompt = (
            f"Bạn là trợ lý ảo Zalo do Developer {DEV_NAME} tạo ra. "
            f"Thời tiết hiện tại: {weather_summary}. "
            f"Hãy trả lời ngắn gọn, thân thiện, có emoji bằng tiếng Việt cho tin nhắn sau: {user_message}"
        )
        encoded_p = urllib.parse.quote(short_prompt)
        resp = http_session.get(f"https://text.pollinations.ai/{encoded_p}", timeout=6)
        if resp.status_code == 200 and len(resp.text.strip()) > 5 and "<html" not in resp.text.lower():
            return f"🤖 {resp.text.replace('**', '').strip()}"
    except Exception:
        pass

    # Tầng 4: Bộ não Trợ lý ảo nội bộ thông minh (Hiểu ngữ cảnh tiếng Việt khi đứt cáp quốc tế)
    msg_low = user_message.lower()
    loc_name = w_main["name"] if w_main else "Bắc Ninh"
    temp_val = w_main["temp"] if w_main else 28
    rain_val = w_main["rain_prob"] if w_main else 20
    status_val = w_main["status"] if w_main else "Nhiều mây"

    if any(k in msg_low for k in ["chào", "hi", "hello", "alo", "ê", "ơi"]):
        return (
            f"👋 Chào bạn nhé! Mình là Trợ lý ảo AI ({BOT_VERSION}) do Developer {DEV_NAME} phát triển.\n"
            f"Hiện tại ở {loc_name} trời đang {status_val.lower()} ({temp_val}°C). "
            f"Hôm nay của bạn thế nào, có chuyện gì vui hay cần mình tư vấn gì không? 💬✨"
        )
    if any(k in msg_low for k in ["ai tạo", "developer", "tác giả", "người tạo", "chủ nhân", "ai làm"]):
        return (
            f"👨‍💻 Mình được thiết kế và lập trình bởi Developer {DEV_NAME} (Phiên bản {BOT_VERSION})!\n"
            f"Mình có thể trò chuyện với bạn mọi lúc, dự báo thời tiết chuẩn xác và vẽ biểu đồ thống kê hằng ngày đó! 🚀"
        )
    if any(k in msg_low for k in ["mặc gì", "trang phục", "quần áo", "ra ngoài"]):
        outfit = (
            "mặc đồ thoáng mát, thấm hút mồ hôi và nhớ mang theo áo chống nắng nhé 👕🕶️"
            if temp_val >= 29
            else ("mặc áo khoác nhẹ hoặc đồ dài tay thoải mái nhé 🧥" if temp_val <= 22 else "mặc trang phục gọn gàng, năng động là chuẩn nhất ✨")
        )
        umbrella = " Đừng quên mang theo ô hoặc áo mưa vì khả năng mưa đang là " + f"{rain_val}% nhé! ☔" if rain_val >= 50 else ""
        return f"👗 Tư vấn trang phục tại {loc_name} ({temp_val}°C - {status_val}): Hôm nay bạn nên {outfit}.{umbrella}"

    if any(k in msg_low for k in ["ăn gì", "đói", "món gì", "ơm", "bữa"]):
        food = (
            "trời hơi oi nóng thế này làm bát bún chả, phở cuốn hoặc trà hoa quả mát lạnh là tuyệt cú mèo! 🍜🍹"
            if temp_val >= 30
            else "thời tiết này mà làm nồi lẩu ấm nóng, đồ nướng hoặc cơm sườn nóng hổi thì hết nước chấm! 🍲🥩"
        )
        return f"😋 Gợi ý ẩm thực cho bạn: Hiện tại ở {loc_name} đang {temp_val}°C ({status_val.lower()}), {food}"

    if any(k in msg_low for k in ["mưa", "nắng", "gió", "nhiệt độ", "thời tiết", "lạnh", "nóng"]):
        return (
            f"🌤️ Trợ lý ảo cập nhật nhanh cho bạn nhé: Tại {loc_name} lúc này trời {status_val.lower()}, "
            f"nhiệt độ khoảng {temp_val}°C, khả năng mưa là {rain_val}%. "
            f"{'Bạn nhớ mang theo áo mưa khi đi đường nhé! ☔' if rain_val >= 50 else 'Thời tiết khá ổn để bạn di chuyển đó! 🛵'}\n"
            f"(Gõ /tk nếu bạn muốn xem biểu đồ biến thiên 24h nhé!)"
        )

    return (
        f"💬 Trợ lý ảo AI ({DEV_NAME}) nghe rõ tin nhắn của bạn: \"{user_message}\"\n"
        f"✨ Hiện tại ở {loc_name} đang {temp_val}°C ({status_val.lower()}). "
        f"Bạn có thể hỏi mình về tư vấn ăn uống, trang phục, thời tiết, hoặc gõ /tk để xem biểu đồ thống kê 24h nhé! 💖"
    )


# ================= RENDER NỘI DUNG TIN NHẮN =================
def render_message(template_type, w):
    templates = load_data(CONFIG_FILE, DEFAULT_TEMPLATES)
    raw_tpl = templates.get(template_type, DEFAULT_TEMPLATES["check"])

    if "mưa" in w["status"].lower() or w["rain_prob"] >= 60:
        advice = "☔ Hôm nay có khả năng mưa, bạn nhớ mang theo ô hoặc áo mưa khi ra ngoài nhé!"
    elif w["temp"] >= 33:
        advice = "🕶️ Trời khá nóng, bạn nhớ bổ sung đủ nước và che chắn nắng khi di chuyển nhé!"
    elif w["temp"] <= 19:
        advice = "🧥 Trời se lạnh, bạn nhớ mặc ấm để giữ gìn sức khỏe nhé!"
    else:
        advice = "✨ Thời tiết rất đẹp và thuận lợi cho mọi công việc, học tập, di chuyển trong ngày!"

    try:
        return raw_tpl.format(
            tinh=w["name"],
            gio_hien_tai=w["time_str"],
            icon=w["icon"],
            nang_mua=w["status"],
            mo_ta_gio=w["wind_desc"],
            toc_do_gio=w["wind_speed"],
            nhiet_do=w["temp"],
            cam_giac=w["feels_like"],
            min=w["min"],
            max=w["max"],
            do_am=w["humidity"],
            may=w["cloud"],
            kha_nang_mua=w["rain_prob"],
            loi_khuyen=advice,
            nang_mua_mai=w["tmr_status"],
            min_mai=w["tmr_min"],
            max_mai=w["tmr_max"],
            mua_mai=w["tmr_rain"],
        )
    except Exception as e:
        return f"⚠️ Mẫu câu trả lời có từ khóa chưa khớp ({e}). Gõ /resetmau để khôi phục mặc định nhé!"


# ================= GIAO TIẾP ZALO BOT API =================
def init_bot():
    try:
        http_session.post(f"{ZALO_API_BASE}/deleteWebhook", json={}, timeout=5)
        print(f"⚡ Đã kết nối máy chủ Zalo Bot [{BOT_VERSION} - Developer: {DEV_NAME}]")
    except Exception as e:
        print(f"[Cảnh báo khởi tạo]: {e}")


def send_message(chat_id, text):
    try:
        url = f"{ZALO_API_BASE}/sendMessage"
        resp = http_session.post(url, json={"chat_id": str(chat_id), "text": text}, timeout=6)
        return resp.json()
    except Exception as e:
        print(f"[Lỗi gửi tin tới {chat_id}]: {e}")
        return None


def send_photo(chat_id, photo_url, caption=""):
    """Gửi ảnh biểu đồ trực tiếp lên khung chat Zalo."""
    try:
        url = f"{ZALO_API_BASE}/sendPhoto"
        payload = {"chat_id": str(chat_id), "photo": photo_url, "caption": caption}
        resp = http_session.post(url, json=payload, timeout=8)
        return resp.json()
    except Exception as e:
        print(f"[Thông báo gửi ảnh biểu đồ]: {e}")
        return None


def send_charts_for_user(chat_id, user_cities):
    """Hàm tạo và gửi biểu đồ thống kê cho tất cả thành phố của người dùng (Dùng cho /tk và 5h sáng)."""
    results = fetch_all_cities_parallel(user_cities, force_refresh=True)
    for (w, err), city_obj in zip(results, user_cities):
        if w:
            chart_text, chart_url = generate_weather_chart(w)
            send_message(chat_id, chart_text)
            send_photo(chat_id, chart_url, f"📊 Biểu đồ thời tiết 24h tại {w['name']} (Dev: {DEV_NAME})")
        else:
            send_message(chat_id, f"⚠️ Không thể tạo biểu đồ cho {city_obj['name']}: {err}")


def get_updates():
    try:
        resp = http_session.post(f"{ZALO_API_BASE}/getUpdates", json={"timeout": "25"}, timeout=30)
        data = resp.json()
        if data.get("ok") and data.get("result"):
            res = data["result"]
            return [res] if isinstance(res, dict) else res
    except requests.exceptions.ReadTimeout:
        pass
    except Exception as e:
        print(f"[Lỗi getUpdates]: {e}")
        time.sleep(1)
    return []


# ================= XỬ LÝ LỆNH & KẾT NỐI TRỢ LÝ ẢO =================
def handle_message(chat_id, text):
    start_t = time.time()
    subscribers = load_data(DATA_FILE, {})
    chat_key = str(chat_id)
    text_clean = text.strip()
    text_lower = text_clean.lower()

    if chat_key not in subscribers or not subscribers[chat_key]:
        subscribers[chat_key] = [{"name": "Bắc Ninh", "lat": 21.1861, "lon": 106.0763}]
        save_data(DATA_FILE, subscribers)

    user_cities = []
    for item in subscribers[chat_key]:
        if isinstance(item, str):
            loc = geocode_city(item) or {"name": item, "lat": 21.1861, "lon": 106.0763}
            user_cities.append(loc)
        elif isinstance(item, dict):
            user_cities.append(item)
    subscribers[chat_key] = user_cities

    city_names_str = ", ".join([c["name"] for c in user_cities])

    # 1. Lệnh /menu
    if text_lower in ["/menu", "/start", "menu"]:
        now_str = datetime.now(VN_TZ).strftime("%H:%M:%S - %d/%m/%Y")
        menu_msg = (
            f"🌟━━List Borum Dev CCV ━━🌟\n"
            f"👨‍💻 Developer: {DEV_NAME}\n"
            f"⏰ Giờ hiện tại: {now_str}\n"
            f"🏙️ Khu vực theo dõi ({len(user_cities)}/5): {city_names_str}\n"
            f"🔔 Lịch tự động hằng ngày:\n"
            f"  • 05:00 sáng: Báo thời tiết + Gửi biểu đồ thống kê 📊\n"
            f"  • 12:00 trưa: Báo thời tiết buổi trưa ☀️\n"
            f"  • 21:00 tối: Báo thời tiết đêm & Chúc ngủ ngon 🌙\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ DANH SÁCH LỆNH ĐIỀU KHIỂN:\n"
            f"• /check : Báo ngay gió, nắng mưa, nhiệt độ & giờ hiện tại\n"
            f"• /tk : Vẽ & gửi ngay Biểu đồ thống kê thời tiết 24h 📊\n"
            f"• /set [Tên TP] : Thêm thành phố (Tối đa 5 nơi, VD: /set Quế Võ)\n"
            f"• /xoa [Tên TP] : Xóa thành phố khỏi danh sách\n"
            f"• /test5h | /test12h | /test21h : Xem thử mẫu tin tự động\n"
            f"• /huongdan : Tự cài đặt mẫu câu trả lời theo ý thích\n"
            f"• /tat : Tắt thông báo tự động\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 TRỢ LÝ ẢO AI: Cứ nhắn bất kỳ câu gì KHÔNG có dấu '/' ở đầu, bạn sẽ được kết nối thẳng với Trợ lý ảo AI để trò chuyện! 💬✨"
        )
        send_message(chat_id, menu_msg)
        return

    # 2. Lệnh /tk (Gửi biểu đồ thống kê nhiệt độ & mưa 24h)
    if text_lower in ["/tk", "/thongke", "/bieudo"]:
        send_charts_for_user(chat_id, user_cities)
        print(f"📊 Đã gửi biểu đồ /tk trong {round(time.time() - start_t, 2)}s")
        return

    # 3. Lệnh /check
    if text_lower == "/check":
        results = fetch_all_cities_parallel(user_cities, force_refresh=True)
        messages = []
        for (w, err), city_obj in zip(results, user_cities):
            if w:
                messages.append(render_message("check", w))
            else:
                messages.append(f"⚠️ Không lấy được thời tiết {city_obj['name']}: {err}")

        send_message(chat_id, "\n\n".join(messages))
        return

    # 4. Lệnh /set <Tên thành phố>
    if text_lower.startswith("/set "):
        new_city_query = text_clean[5:].strip()
        if not new_city_query:
            send_message(chat_id, "⚠️ Vui lòng nhập tên thành phố! Ví dụ: /set Quế Võ")
            return

        if len(user_cities) >= 5:
            send_message(
                chat_id,
                f"⚠️ Bạn đã lưu đủ 5 thành phố ({city_names_str}).\n"
                f"Hãy gõ /xoa [Tên TP] để xóa bớt trước khi thêm mới nhé!",
            )
            return

        loc = geocode_city(new_city_query)
        if not loc:
            send_message(chat_id, f"❌ Không tìm thấy khu vực '{new_city_query}'. Vui lòng kiểm tra lại tên!")
            return

        if any(c["name"].lower() == loc["name"].lower() for c in user_cities):
            send_message(chat_id, f"ℹ️ Khu vực {loc['name']} đã có sẵn trong danh sách của bạn rồi!")
            return

        user_cities.append(loc)
        subscribers[chat_key] = user_cities
        save_data(DATA_FILE, subscribers)

        updated_names = ", ".join([c["name"] for c in user_cities])
        w, _ = get_accurate_weather(loc, force_refresh=True)
        preview = render_message("check", w) if w else ""

        send_message(
            chat_id,
            f"✅ Đã thêm [{loc['name']}] vào danh sách ({len(user_cities)}/5): {updated_names}\n\n{preview}",
        )
        return

    # 5. Lệnh /xoa <Tên thành phố>
    if text_lower.startswith("/xoa "):
        target = text_clean[5:].strip().lower()
        if not target:
            send_message(chat_id, "⚠️ Vui lòng nhập tên thành phố cần xóa! Ví dụ: /xoa Hà Nội")
            return

        matched_item = next(
            (c for c in user_cities if c["name"].lower() == target or target in c["name"].lower()),
            None,
        )

        if not matched_item:
            send_message(chat_id, f"❌ Không tìm thấy '{target}' trong danh sách ({city_names_str}).")
            return

        if len(user_cities) <= 1:
            send_message(chat_id, "⚠️ Bạn cần giữ lại ít nhất 1 thành phố trong danh sách!")
            return

        user_cities.remove(matched_item)
        subscribers[chat_key] = user_cities
        save_data(DATA_FILE, subscribers)
        updated_names = ", ".join([c["name"] for c in user_cities])
        send_message(
            chat_id,
            f"🗑️ Đã xóa [{matched_item['name']}] khỏi danh sách!\n"
            f"🏙️ Danh sách còn lại ({len(user_cities)}/5): {updated_names}",
        )
        return

    # 6. Lệnh /huongdan
    if text_lower == "/huongdan":
        guide = (
            f"✏️━━ HƯỚNG DẪN TÙY CHỈNH MẪU CÂU ━━✏️\n"
            f"👨‍💻 Developer: {DEV_NAME}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Các từ khóa tự động điền số liệu thật:\n"
            f"• {{tinh}} : Tên thành phố\n"
            f"• {{gio_hien_tai}} : Giờ & ngày hiện tại\n"
            f"• {{nang_mua}} : Trạng thái nắng/mưa chuẩn\n"
            f"• {{toc_do_gio}} : Tốc độ gió (km/h)\n"
            f"• {{mo_ta_gio}} : Mô tả gió (nhẹ/vừa/mạnh)\n"
            f"• {{nhiet_do}} : Nhiệt độ (°C) | {{cam_giac}} : Cảm giác thực (°C)\n"
            f"• {{min}} / {{max}} : Nhiệt độ thấp/cao nhất\n"
            f"• {{do_am}} : Độ ẩm (%) | {{kha_nang_mua}} : Khả năng mưa (%)\n\n"
            f"📌 LỆNH ĐẶT MẪU CÂU:\n"
            f"• /setcheck [Mẫu câu mới]\n"
            f"• /set5h [Mẫu câu mới]\n"
            f"• /set12h [Mẫu câu mới]\n"
            f"• /set21h [Mẫu câu mới]\n"
            f"• /resetmau : Khôi phục mặc định"
        )
        send_message(chat_id, guide)
        return

    # 7. Cài đặt mẫu câu tùy chỉnh
    tpl_cmds = {
        "/setcheck ": ("check", "lệnh /check"),
        "/set5h ": ("morning", "bản tin 5h sáng"),
        "/set12h ": ("noon", "bản tin 12h trưa"),
        "/set21h ": ("night", "bản tin 9h tối"),
    }
    for prefix, (t_key, label) in tpl_cmds.items():
        if text_lower.startswith(prefix):
            new_tpl = text_clean[len(prefix) :].strip()
            if not new_tpl:
                send_message(chat_id, f"⚠️ Vui lòng nhập nội dung sau lệnh {prefix.strip()}")
                return
            templates = load_data(CONFIG_FILE, DEFAULT_TEMPLATES)
            templates[t_key] = new_tpl
            save_data(CONFIG_FILE, templates)
            send_message(chat_id, f"✅ Đã lưu mẫu câu trả lời mới cho {label} thành công! 🎉")
            return

    if text_lower == "/resetmau":
        save_data(CONFIG_FILE, DEFAULT_TEMPLATES)
        send_message(chat_id, "🔄 Đã khôi phục toàn bộ mẫu câu trả lời về mặc định V11!")
        return

    if text_lower == "/tat":
        if chat_key in subscribers:
            del subscribers[chat_key]
            save_data(DATA_FILE, subscribers)
        send_message(chat_id, "🔕 Đã tắt báo thời tiết tự động. Gõ /menu bất kỳ lúc nào để bật lại!")
        return

    if text_lower in ["/test5h", "/test12h", "/test21h", "/thoitiet"]:
        t_type = "morning"
        if text_lower == "/test12h":
            t_type = "noon"
        elif text_lower == "/test21h":
            t_type = "night"

        results = fetch_all_cities_parallel(user_cities)
        msgs = [render_message(t_type, w) for w, _ in results if w]
        send_message(chat_id, "\n\n".join(msgs))
        # Nếu test5h thì gửi kèm luôn biểu đồ sáng sớm để xem thử
        if text_lower == "/test5h":
            send_charts_for_user(chat_id, user_cities)
        return

    # Nếu người dùng gõ sai một lệnh bắt đầu bằng dấu '/'
    if text_lower.startswith("/") and not text_lower.startswith("/ai "):
        send_message(
            chat_id,
            f"⚠️ Lệnh '{text_clean}' không tồn tại!\n"
            f"👉 Gõ /menu để xem danh sách lệnh, /tk để xem biểu đồ, hoặc nhắn tin bình thường (không có dấu '/') để trò chuyện với Trợ lý ảo AI nhé!",
        )
        return

    # 8. KẾT NỐI TRỰC TIẾP TRỢ LÝ ẢO AI (Mọi tin nhắn bình thường không có lệnh '/')
    user_query = text_clean[4:].strip() if text_lower.startswith("/ai ") else text_clean
    ai_reply = smart_virtual_assistant(user_query, user_cities)
    send_message(chat_id, ai_reply)
    print(f"🤖 Đã trả lời Trợ lý ảo trong {round(time.time() - start_t, 2)}s")


# ================= BỘ HẸN GIỜ TỰ ĐỘNG (5H SÁNG GỬI KÈM BIỂU ĐỒ) =================
def scheduler_worker():
    last_run = ""
    print("⏰ Bộ hẹn giờ tự động (05:00 sáng + Biểu đồ, 12:00 trưa, 21:00 tối) đã kích hoạt...")

    while True:
        now = datetime.now(VN_TZ)
        hm = now.strftime("%H:%M")
        key = f"{now.strftime('%Y-%m-%d')}_{hm}"

        if hm in ["05:00", "12:00", "21:00"] and last_run != key:
            last_run = key
            subscribers = load_data(DATA_FILE, {})
            print(f"📢 [Auto Broadcast] Đang gửi bản tin khung giờ {hm}...")

            t_type = "morning"
            if hm == "12:00":
                t_type = "noon"
            elif hm == "21:00":
                t_type = "night"

            for chat_id, cities in subscribers.items():
                results = fetch_all_cities_parallel(cities, force_refresh=True)
                msgs = [render_message(t_type, w) for w, _ in results if w]
                if msgs:
                    send_message(chat_id, "\n\n".join(msgs))

                # ĐẶC BIỆT: Cứ mỗi sáng sớm 05:00 sẽ tự động gửi kèm Biểu đồ thống kê 24h
                if hm == "05:00":
                    send_charts_for_user(chat_id, cities)

        time.sleep(10)


# ================= CỔNG WEB KEEP-ALIVE 24/7 (CHO RENDER / CLOUD VPS) =================
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = (
            f"<html><head><title>Zalo Bot {BOT_VERSION}</title></head>"
            f"<body style='font-family:sans-serif;text-align:center;padding-top:50px;'>"
            f"<h1>🌟 Zalo Weather, Chart & AI Bot ({BOT_VERSION}) đang hoạt động 24/7!</h1>"
            f"<h3>👨‍💻 Developer: {DEV_NAME}</h3>"
            f"</body></html>"
        )
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass


def run_keep_alive_server():
    try:
        port = int(os.environ.get("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
        print(f"🌐 Cổng Web Keep-Alive 24/7 đang mở tại port {port}...")
        server.serve_forever()
    except Exception as e:
        print(f"[Keep-Alive Port Info]: {e}")


# ================= KHỞI CHẠY HỆ THỐNG =================
def main():
    print("==========================================================")
    print(f"🚀 Run Build... {BOT_VERSION.upper()}")
    print(f"👨‍💻 DEVELOPER: {DEV_NAME.upper()}")
    print("==========================================================")

    init_bot()
    threading.Thread(target=scheduler_worker, daemon=True).start()
    threading.Thread(target=run_keep_alive_server, daemon=True).start()

    print("🤖 Hệ thống đã sẵn sàng! Hãy vào Zalo gõ /tk, /menu hoặc nhắn tin trò chuyện bất kỳ!")

    while True:
        updates = get_updates()
        for item in updates:
            msg_obj = item.get("message", item)
            chat = msg_obj.get("chat", {})
            chat_id = chat.get("id") or msg_obj.get("from", {}).get("id")
            text = msg_obj.get("text", "")

            if chat_id and text:
                print(f"💬 Tin nhắn từ [{chat_id}]: {text}")
                threading.Thread(target=handle_message, args=(chat_id, text), daemon=True).start()
            elif chat_id:
                send_message(
                    chat_id,
                    f"👋 Chào bạn! Đây là Bot Thời Tiết, Biểu Đồ & Trợ Lý Ảo ({BOT_VERSION}) - Dev: {DEV_NAME}.\n"
                    f"• Gõ /tk để xem biểu đồ thống kê 📊\n"
                    f"• Gõ /check để xem thời tiết 🌤️\n"
                    f"• Hoặc nhắn tin trực tiếp để trò chuyện với Trợ lý ảo nhé! 💬",
                )


if __name__ == "__main__":
    main()