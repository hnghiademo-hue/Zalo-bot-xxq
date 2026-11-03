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
# 🚀 ZALO WEATHER, CHART & AI ASSISTANT BOT - VERSION 12.0 VIETNAM PRO
# 👨‍💻 Developer: Nguyen Huu Nghia
# ==============================================================================

DEV_NAME = "Nguyen Huu Nghia"
BOT_VERSION = "v12.0 Vietnam Pro"

BOT_TOKEN = "4600528661577218342:sGojQQEzTlHyasuDbXoIGdpCICBwBZTuPXItLkrLNkzgqiDqyKUldspwhzEnQNzG"
ZALO_API_BASE = f"https://bot-api.zapps.me/bot{BOT_TOKEN}"

OWM_API_KEY = "2de37a1d6a5323fcccbf92701e76d474"
GEMINI_API_KEY = "AQ.Ab8RN6JPvLme0w8a7dhuqQvtn9FLBeGGoiQD7mmk8juMTRifhQ"

DATA_FILE = "subscribers_multi.json"
CONFIG_FILE = "config_multi.json"
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

http_session = requests.Session()
http_session.headers.update({"User-Agent": "ZaloBot-V12-VietnamPro-NguyenHuuNghia/12.0"})

# Tọa độ chuẩn xác các tỉnh thành và các quận/huyện tại Việt Nam
GEO_CACHE = {
    "bắc ninh": {"name": "Bắc Ninh", "lat": 21.1861, "lon": 106.0763},
    "quế võ": {"name": "Quế Võ, Bắc Ninh", "lat": 21.1519, "lon": 106.1558},
    "bồng lai": {"name": "Bồng Lai, Quế Võ", "lat": 21.1180, "lon": 106.2050},
    "từ sơn": {"name": "Từ Sơn, Bắc Ninh", "lat": 21.1167, "lon": 105.9500},
    "yên phong": {"name": "Yên Phong, Bắc Ninh", "lat": 21.2014, "lon": 105.9961},
    "tiên du": {"name": "Tiên Du, Bắc Ninh", "lat": 21.1278, "lon": 106.0389},
    "thuận thành": {"name": "Thuận Thành, Bắc Ninh", "lat": 21.0333, "lon": 106.0833},
    "gia bình": {"name": "Gia Bình, Bắc Ninh", "lat": 21.0667, "lon": 106.2000},
    "lương tài": {"name": "Lương Tài, Bắc Ninh", "lat": 21.0167, "lon": 106.2333},
    "hà nội": {"name": "Hà Nội", "lat": 21.0285, "lon": 105.8542},
    "hải phòng": {"name": "Hải Phòng", "lat": 20.8449, "lon": 106.6881},
    "đà nẵng": {"name": "Đà Nẵng", "lat": 16.0544, "lon": 108.2022},
    "tp. hồ chí minh": {"name": "TP. Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297},
    "hồ chí minh": {"name": "TP. Hồ Chí Minh", "lat": 10.8231, "lon": 106.6297},
    "huế": {"name": "Thừa Thiên Huế", "lat": 16.4637, "lon": 107.5909},
    "cần thơ": {"name": "Cần Thơ", "lat": 10.0452, "lon": 105.7469},
    "nha trang": {"name": "Nha Trang, Khánh Hòa", "lat": 12.2388, "lon": 109.1967},
    "quảng ninh": {"name": "Quảng Ninh", "lat": 21.0069, "lon": 107.2925},
}
WEATHER_CACHE = {}

DEFAULT_TEMPLATES = {
    "check": (
        "🌟━━ Dự báo thời tiết -_- ━━🌟\n"
        "🏙️ Khu vực: {tinh}\n"
        "⏰ Giờ hiện tại: {gio_hien_tai}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "{icon} Trạng thái: {nang_mua}\n"
        "🌡️ Nhiệt độ: {nhiet_do}°C (Cảm giác thực: {cam_giac}°C)\n"
        "📊 Biên độ nhiệt: {min}°C ➔ {max}°C\n"
        "💨 Sức gió: {toc_do_gio} km/h ({mo_ta_gio})\n"
        "💧 Độ ẩm: {do_am}% | ☁️ Mây: {may}% | ☔ Lượng mưa: {kha_nang_mua}mm\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎉 Chúc bạn ngày hôm nay làm việc hiệu quả và tràn đầy năng lượng! 💖\n"
        "👨‍💻 Developer: Nguyen Huu Nghia"
    ),
    "morning": (
        "🌅━━ Mặt Trời Đã Mọc Chào Buổi Sáng━━☕\n"
        "📍 Khu vực: {tinh} ({gio_hien_tai})\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "{icon} Thời tiết sáng nay: {nang_mua}\n"
        "🌡️ Nhiệt độ: {nhiet_do}°C (Cảm giác: {cam_giac}°C)\n"
        "📈 Dự báo trong ngày: {min}°C ➔ {max}°C\n"
        "💨 Sức gió: {toc_do_gio} km/h ({mo_ta_gio})\n"
        "💧 Độ ẩm: {do_am}% | 🌧️ Lượng mưa: {kha_nang_mua}mm\n\n"
        "💡 Lời khuyên: {loi_khuyen}\n"
        "✨ Chúc bạn một ngày mới thật nhiều may mắn! 🍀\n"
        "👨‍💻 Developer: Nguyen Huu Nghia"
    ),
    "noon": (
        "☀️━━ Cập nhật thời tiết ━━🍱\n"
        "📍 Khu vực: {tinh} ({gio_hien_tai})\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "{icon} Tình hình: {nang_mua}\n"
        "🔥 Nhiệt độ: {nhiet_do}°C (Cảm giác oi bức: {cam_giac}°C)\n"
        "💨 Sức gió: {toc_do_gio} km/h ({mo_ta_gio})\n"
        "💧 Độ ẩm: {do_am}% | ☔ Dự báo mưa chiều: {kha_nang_mua}mm\n\n"
        "🍲 Chúc bạn có bữa trưa ngon miệng và nghỉ ngơi trọn vẹn! 💤\n"
        "👨‍💻 Developer: Nguyen Huu Nghia"
    ),
    "night": (
        "🌙━━ Chúc bạn ngủ ngon tối nay ━━🌟\n"
        "📍 Khu vực: {tinh} ({gio_hien_tai})\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🌌 Thời tiết đêm: {nang_mua}, nhiệt độ {nhiet_do}°C (Cảm giác: {cam_giac}°C)\n"
        "💨 Gió: {toc_do_gio} km/h ({mo_ta_gio}) | 💧 Độ ẩm: {do_am}%\n\n"
        "📅 Dự báo ngày mai tại {tinh}:\n"
        "• Trạng thái: {nang_mua_mai}\n"
        "• Nhiệt độ: {min_mai}°C ➔ {max_mai}°C\n\n"
        "🛌 Chúc bạn ngủ ngon và có một đêm thật sâu giấc! 🌙✨\n"
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


# ================= ĐỊNH VỊ TỌA ĐỘ CHUẨN VN =================
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


# ================= XỬ LÝ TRẠNG THÁI KHÍ HẬU CHUẨN XÁC VIỆT NAM =================
def determine_vietnam_weather_status(is_day, rain_mm, cloud_pct, humidity, owm_id=None):
    if owm_id is not None:
        if 200 <= owm_id < 300:
            return "Mưa dông nhiệt đới, có sấm chớp", "⛈️"
        if 300 <= owm_id < 400:
            return "Mưa phùn, ẩm ướt", "🌦️"
        if 500 <= owm_id < 600:
            if rain_mm > 8 or owm_id >= 502:
                return "Đang có mưa lớn / mưa tầm tã", "🌧️"
            return "Có mưa rào nhẹ", "🌦️"
        if 700 <= owm_id < 800:
            return "Sương mù / Sương muối", "🌫️"

    if rain_mm >= 5.0:
        return "Đang có mưa vừa đến mưa to", "🌧️"
    elif rain_mm >= 0.2:
        return "Có mưa nhỏ / mưa rào rải rác", "🌦️"

    if cloud_pct <= 20:
        return ("Trời quang mây, nắng gắt", "☀️") if is_day else ("Trời quang đãng, sao trời", "🌙")
    elif cloud_pct <= 55:
        return ("Trời nắng nhẹ, mây đan xen", "🌤️") if is_day else ("Trời có mây, thoáng mát", "☁️")
    elif cloud_pct <= 84:
        return ("Trời nhiều mây, nắng dịu", "⛅") if is_day else ("Trời nhiều mây", "☁️")
    else:
        return ("Trời âm u, oi bức nhiều mây", "☁️")


# ================= LẤY THỜI TIẾT CHUẨN XÁC (OPEN-METEO + OWM) =================
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

    # Lấy dữ liệu từ OpenWeatherMap
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
    tmr_min, tmr_max, tmr_rain_sum, tmr_status = 23, 29, 0.0, "Thời tiết ổn định 🌤️"
    hourly_labels, hourly_temps, hourly_rains = [], [], []

    # Lấy dữ liệu dự báo chính xác từ Open-Meteo (Model chuyên biệt khu vực Đông Nam Á)
    try:
        om_resp = http_session.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,cloud_cover,wind_speed_10m",
                "hourly": "temperature_2m,precipitation_probability,precipitation",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
                "timezone": "Asia/Ho_Chi_Minh",
                "forecast_days": 2,
            },
            timeout=5,
        )
        if om_resp.status_code == 200:
            om = om_resp.json()
            curr = om.get("current", {})
            daily = om.get("daily", {})
            hourly = om.get("hourly", {})

            if temp is None:
                temp = round(curr.get("temperature_2m", 26.0), 1)
                feels_like = round(curr.get("apparent_temperature", temp), 1)
                humidity = curr.get("relative_humidity_2m", 80)
                wind_kmh = round(curr.get("wind_speed_10m", 6.0), 1)
                cloud_pct = curr.get("cloud_cover", 50)
                rain_mm = curr.get("precipitation", 0.0)

            t_min = min(temp, round(daily.get("temperature_2m_min", [temp, temp])[0], 1))
            t_max = max(temp, round(daily.get("temperature_2m_max", [temp, temp])[0], 1))
            
            tmr_min = round(daily.get("temperature_2m_min", [23, 23])[1], 1)
            tmr_max = round(daily.get("temperature_2m_max", [29, 29])[1], 1)
            tmr_rain_sum = daily.get("precipitation_sum", [0, 0])[1]

            if tmr_rain_sum >= 5.0:
                tmr_status = "Có mưa rào và dông 🌧️"
            elif tmr_rain_sum >= 1.0:
                tmr_status = "Có mưa nhỏ rải rác 🌦️"
            else:
                tmr_status = "Trời tạnh ráo, nắng đẹp 🌤️"

            # Lấy dữ liệu 24h tiếp theo cho biểu đồ
            h_times = hourly.get("time", [])
            h_temps = hourly.get("temperature_2m", [])
            h_rains = hourly.get("precipitation", [])
            curr_hour_idx = now_vn.hour
            for idx in range(curr_hour_idx, min(curr_hour_idx + 24, len(h_times)), 3):
                label = h_times[idx].split("T")[-1][:5]
                hourly_labels.append(label)
                hourly_temps.append(round(h_temps[idx], 1))
                hourly_rains.append(round(h_rains[idx], 1))
    except Exception:
        pass

    if temp is None:
        return None, "Không thể kết nối máy chủ thời tiết lúc này."

    status_text, icon = determine_vietnam_weather_status(is_day, rain_mm, cloud_pct, humidity, owm_id)
    if wind_kmh < 10:
        wind_desc = "gió nhẹ 🍃"
    elif wind_kmh < 25:
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
        "rain_prob": rain_mm,
        "time_str": now_str,
        "tmr_status": tmr_status,
        "tmr_min": tmr_min,
        "tmr_max": tmr_max,
        "hourly_labels": hourly_labels or ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
        "hourly_temps": hourly_temps or [t_min, round((t_min + t_max) / 2, 1), t_max, t_max, round((t_min + t_max) / 2, 1), t_min],
        "hourly_rains": hourly_rains or [0.0] * 6,
    }
    WEATHER_CACHE[cache_key] = (now_ts, result)
    return result, None


def fetch_all_cities_parallel(user_cities, force_refresh=False):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_accurate_weather, c, force_refresh) for c in user_cities]
        return [f.result() for f in futures]


# ================= TẠO BIỂU ĐỒ THỐNG KÊ (/tk) =================
def generate_weather_chart(w):
    labels = w["hourly_labels"]
    temps = w["hourly_temps"]
    rains = w["hourly_rains"]

    min_t = min(temps) if temps else 20
    max_t = max(temps) if temps else 35

    bars_lines = []
    for lbl, t, r in zip(labels, temps, rains):
        rain_icon = "🌧️" if r >= 2.0 else ("🌦️" if r > 0 else "☀️")
        bars_lines.append(f"🕒 {lbl} | {t}°C ({rain_icon} {r}mm)")

    ascii_chart = "\n".join(bars_lines)

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
                    "label": "Lượng mưa (mm)",
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
            }
        },
    }
    encoded_cfg = urllib.parse.quote(json.dumps(chart_config, ensure_ascii=False))
    chart_url = f"https://quickchart.io/chart?w=650&h=380&c={encoded_cfg}"

    text_report = (
        f"📊━━ BIỂU ĐỒ THỜI TIẾT 24H ({w['name'].upper()}) ━━📊\n"
        f"⏰ Cập nhật: {w['time_str']}\n"
        f"🌡️ Hiện tại: {w['temp']}°C | {w['icon']} {w['status']}\n"
        f"📉 Thấp nhất: {w['min']}°C ➔ 📈 Cao nhất: {w['max']}°C\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 DIỄN BIẾN THEO GIỜ:\n{ascii_chart}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🖼️ Ảnh biểu đồ: {chart_url}\n"
        f"👨‍💻 Developer: {DEV_NAME}"
    )
    return text_report, chart_url


# ================= TRỢ LÝ ẢO AI =================
def smart_virtual_assistant(user_message, user_cities):
    results = fetch_all_cities_parallel(user_cities)
    weather_list = [w for w, _ in results if w]
    w_main = weather_list[0] if weather_list else None

    weather_lines = []
    for w in weather_list:
        weather_lines.append(
            f"- {w['name']}: {w['status']} {w['icon']}, nhiệt độ {w['temp']}°C "
            f"(cảm giác {w['feels_like']}°C, min {w['min']}°C - max {w['max']}°C), "
            f"gió {w['wind_speed']} km/h ({w['wind_desc']}), độ ẩm {w['humidity']}%, lượng mưa {w['rain_prob']}mm."
        )
    weather_summary = "\n".join(weather_lines)
    now_str = datetime.now(VN_TZ).strftime("%H:%M ngày %d/%m/%Y")

    system_prompt = (
        f"Bạn là Trợ lý ảo AI thời tiết Việt Nam (Phiên bản {BOT_VERSION}), được phát triển bởi Developer {DEV_NAME}.\n"
        f"Giờ hiện tại: {now_str}.\n"
        f"Thời tiết thực tế:\n{weather_summary}\n\n"
        f"Hãy trả lời tự nhiên, thân thiện bằng tiếng Việt, dùng emoji và không dùng dấu **."
    )

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

    try:
        resp = http_session.post(
            "https://text.pollinations.ai/openai",
            json={"model": "openai", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]},
            timeout=6,
        )
        if resp.status_code == 200:
            ans = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").replace("**", "").strip()
            if ans:
                return f"🤖 {ans}"
    except Exception:
        pass

    loc_name = w_main["name"] if w_main else "Việt Nam"
    temp_val = w_main["temp"] if w_main else 28
    return f"🤖 Chào bạn! Trợ lý AI ({DEV_NAME}) ghi nhận. Hiện tại tại {loc_name} đang {temp_val}°C. Gõ /menu hoặc /check để xem chi tiết thời tiết nhé!"


# ================= RENDER NỘI DUNG TIN NHẮN =================
def render_message(template_type, w):
    templates = load_data(CONFIG_FILE, DEFAULT_TEMPLATES)
    raw_tpl = templates.get(template_type, DEFAULT_TEMPLATES["check"])

    if "mưa" in w["status"].lower() or w["rain_prob"] >= 1.0:
        advice = "☔ Hôm nay có mưa, bạn nhớ mang theo ô hoặc áo mưa khi ra ngoài nhé!"
    elif w["temp"] >= 33:
        advice = "🕶️ Trời khá nắng nóng, bạn nhớ bổ sung nước khi di chuyển ngoài trời nhé!"
    elif w["temp"] <= 19:
        advice = "🧥 Trời se lạnh, bạn nhớ mặc ấm để giữ gìn sức khỏe nhé!"
    else:
        advice = "✨ Thời tiết thuận lợi cho mọi hoạt động di chuyển và công việc trong ngày!"

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
        )
    except Exception as e:
        return f"⚠️ Lỗi khớp mẫu câu ({e}). Gõ /resetmau để khôi phục mặc định."


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
    try:
        url = f"{ZALO_API_BASE}/sendPhoto"
        payload = {"chat_id": str(chat_id), "photo": photo_url, "caption": caption}
        resp = http_session.post(url, json=payload, timeout=8)
        return resp.json()
    except Exception as e:
        print(f"[Lỗi gửi ảnh]: {e}")
        return None


def send_charts_for_user(chat_id, user_cities):
    results = fetch_all_cities_parallel(user_cities, force_refresh=True)
    for (w, err), city_obj in zip(results, user_cities):
        if w:
            chart_text, chart_url = generate_weather_chart(w)
            send_message(chat_id, chart_text)
            send_photo(chat_id, chart_url, f"📊 Biểu đồ 24h tại {w['name']} (Dev: {DEV_NAME})")
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


# ================= XỬ LÝ LỆNH ZALO =================
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

    if text_lower in ["/menu", "/start", "menu"]:
        now_str = datetime.now(VN_TZ).strftime("%H:%M:%S - %d/%m/%Y")
        menu_msg = (
            f"🌟━━ BẢNG ĐIỀU KHIỂN THỜI TIẾT ({BOT_VERSION}) ━━🌟\n"
            f"👨‍💻 Developer: {DEV_NAME}\n"
            f"⏰ Giờ hiện tại: {now_str}\n"
            f"🏙️ Khu vực theo dõi ({len(user_cities)}/5): {city_names_str}\n"
            f"🔔 Lịch tự động: 05:00 sáng | 12:00 trưa | 21:00 tối\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ DANH SÁCH LỆNH:\n"
            f"• /check : Xem thời tiết, nhiệt độ & gió hiện tại\n"
            f"• /tk : Biểu đồ thống kê biến động 24h 📊\n"
            f"• /set [Tên TP] : Thêm khu vực (VD: /set Hà Nội)\n"
            f"• /xoa [Tên TP] : Xóa khu vực khỏi danh sách\n"
            f"• /huongdan : Tùy chỉnh mẫu tin nhắn\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 Nhắn tin bất kỳ để trò chuyện trực tiếp với Trợ lý AI!"
        )
        send_message(chat_id, menu_msg)
        return

    if text_lower in ["/tk", "/thongke", "/bieudo"]:
        send_charts_for_user(chat_id, user_cities)
        return

    if text_lower == "/check":
        results = fetch_all_cities_parallel(user_cities, force_refresh=True)
        messages = [render_message("check", w) if w else f"⚠️ Lỗi lấy dữ liệu: {err}" for (w, err), _ in zip(results, user_cities)]
        send_message(chat_id, "\n\n".join(messages))
        return

    if text_lower.startswith("/set "):
        q = text_clean[5:].strip()
        if not q:
            send_message(chat_id, "⚠️ Vui lòng nhập tên khu vực! Ví dụ: /set Hà Nội")
            return
        loc = geocode_city(q)
        if not loc:
            send_message(chat_id, f"❌ Không tìm thấy khu vực '{q}'.")
            return
        user_cities.append(loc)
        subscribers[chat_key] = user_cities
        save_data(DATA_FILE, subscribers)
        send_message(chat_id, f"✅ Đã thêm [{loc['name']}] vào danh sách theo dõi!")
        return

    if text_lower.startswith("/xoa "):
        target = text_clean[5:].strip().lower()
        matched = next((c for c in user_cities if target in c["name"].lower()), None)
        if not matched:
            send_message(chat_id, f"❌ Không tìm thấy khu vực cần xóa.")
            return
        if len(user_cities) <= 1:
            send_message(chat_id, "⚠️ Cần giữ lại ít nhất 1 khu vực!")
            return
        user_cities.remove(matched)
        subscribers[chat_key] = user_cities
        save_data(DATA_FILE, subscribers)
        send_message(chat_id, f"🗑️ Đã xóa [{matched['name']}] khỏi danh sách.")
        return

    if text_lower == "/huongdan":
        send_message(chat_id, f"✏️ Hướng dẫn tùy chỉnh mẫu câu:\nGõ /setcheck [Mẫu mới], /set5h [Mẫu mới], /resetmau để khôi phục mặc định.")
        return

    if text_lower == "/tat":
        if chat_key in subscribers:
            del subscribers[chat_key]
            save_data(DATA_FILE, subscribers)
        send_message(chat_id, "🔕 Đã tắt thông báo tự động.")
        return

    ai_reply = smart_virtual_assistant(text_clean, user_cities)
    send_message(chat_id, ai_reply)


# ================= HẸN GIỜ TỰ ĐỘNG =================
def scheduler_worker():
    last_run = ""
    while True:
        now = datetime.now(VN_TZ)
        hm = now.strftime("%H:%M")
        key = f"{now.strftime('%Y-%m-%d')}_{hm}"

        if hm in ["05:00", "12:00", "21:00"] and last_run != key:
            last_run = key
            subscribers = load_data(DATA_FILE, {})
            t_type = "morning" if hm == "05:00" else ("noon" if hm == "12:00" else "night")

            for chat_id, cities in subscribers.items():
                results = fetch_all_cities_parallel(cities, force_refresh=True)
                msgs = [render_message(t_type, w) for w, _ in results if w]
                if msgs:
                    send_message(chat_id, "\n\n".join(msgs))
                if hm == "05:00":
                    send_charts_for_user(chat_id, cities)
        time.sleep(10)


# ================= CỔNG WEB KEEP-ALIVE (FIX LỖI 501 HEAD) =================
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = f"<html><body><h1>🌟 Zalo Weather Bot ({BOT_VERSION}) Online 24/7!</h1><h3>Dev: {DEV_NAME}</h3></body></html>"
        self.wfile.write(html.encode("utf-8"))

    def do_HEAD(self):
        """Khắc phục triệt để lỗi 501 Not Implemented từ UptimeRobot"""
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

    def log_message(self, format, *args):
        pass


def run_keep_alive_server():
    try:
        port = int(os.environ.get("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
        server.serve_forever()
    except Exception:
        pass


# ================= KHỞI CHẠY HỆ THỐNG =================
def main():
    print("==========================================================")
    print(f"🚀 KHỞI ĐỘNG HỆ THỐNG THỜI TIẾT VIỆT NAM - {BOT_VERSION.upper()}")
    print(f"👨‍💻 DEVELOPER: {DEV_NAME.upper()}")
    print("==========================================================")

    init_bot()
    threading.Thread(target=scheduler_worker, daemon=True).start()
    threading.Thread(target=run_keep_alive_server, daemon=True).start()

    while True:
        updates = get_updates()
        for item in updates:
            msg_obj = item.get("message", item)
            chat = msg_obj.get("chat", {})
            chat_id = chat.get("id") or msg_obj.get("from", {}).get("id")
            text = msg_obj.get("text", "")

            if chat_id and text:
                threading.Thread(target=handle_message, args=(chat_id, text), daemon=True).start()


if __name__ == "__main__":
    main()
