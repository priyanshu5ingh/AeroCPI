"""AeroCPI live fare collector -- observed search_timestamp discipline (4A.1)."""
from __future__ import annotations
import datetime as dt, hashlib, json, re, sys, time, uuid, gzip, pathlib
from selectolax.lexbor import LexborHTMLParser
from fast_flights import FlightQuery, Passengers, create_query, fetch_flights_html

# Project Root Relative Paths (Configurable via Environment Variables)
PROJECT_ROOT = pathlib.Path(os.getenv("AEROCPI_ROOT", pathlib.Path(__file__).resolve().parents[2]))
DATA_DIR = pathlib.Path(os.getenv("AEROCPI_DATA_DIR", PROJECT_ROOT / "data"))
RAW = pathlib.Path(os.getenv("AEROCPI_RAW_DIR", DATA_DIR / "raw" / "captures"))
OUT = pathlib.Path(os.getenv("AEROCPI_OUT_DIR", DATA_DIR / "out"))

IATA_CITY = {"DEL":"Delhi","BOM":"Mumbai","BLR":"Bangalore","MAA":"Chennai",
             "CCU":"Kolkata","HYD":"Hyderabad","GOI":"Goa","AMD":"Ahmedabad",
             "PNQ":"Pune","COK":"Kochi","JAI":"Jaipur","LKO":"Lucknow"}
CARRIER = {"IndiGo":"6E","Air India":"AI","Air India Express":"IX","SpiceJet":"SG",
           "Akasa Air":"QP","Alliance Air":"9I","Vistara":"UK","Star Air":"S5"}

def sha256(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def parse_duration(s: str):
    h = re.search(r"(\d+)\s*hr", s); m = re.search(r"(\d+)\s*min", s)
    if not h and not m: return None
    return (int(h.group(1))*60 if h else 0) + (int(m.group(1)) if m else 0)

def parse_stops(s: str):
    if "Nonstop" in s or "nonstop" in s: return 0
    m = re.search(r"(\d+)\s*stop", s)
    return int(m.group(1)) if m else None

def collect(origin: str, dest: str, apw: int, cabin: str = "economy"):
    """One collection event. search_timestamp is observed, never derived."""
    search_ts = dt.datetime.now(dt.timezone.utc)
    travel_date = (search_ts.date() + dt.timedelta(days=apw))
    q = create_query(flights=[FlightQuery(date=travel_date.strftime("%Y-%m-%d"),
                     from_airport=origin, to_airport=dest)],
                     trip="one-way", seat=cabin,
                     passengers=Passengers(adults=1), currency="INR")
    html = fetch_flights_html(q)
    raw_bytes = html.encode("utf-8", "replace")
    raw_payload_sha256 = sha256(raw_bytes)
    stamp = search_ts.strftime("%Y%m%dT%H%M%SZ")
    raw_path = RAW/f"{origin}-{dest}_apw{apw:02d}_{stamp}_{raw_payload_sha256[:12]}.html.gz"
    RAW.mkdir(parents=True, exist_ok=True)
    compressed_bytes = gzip.compress(raw_bytes)
    stored_file_sha256 = sha256(compressed_bytes)
    with open(raw_path, "wb") as f: f.write(compressed_bytes)

    rows, seen = [], set()
    for li in LexborHTMLParser(html).css("li.pIav2d"):
        t = li.text(strip=False)
        pm = re.search(r"₹([\d,]+)", t)
        if not pm: continue
        total = float(pm.group(1).replace(",", ""))
        airline = next((a for a in CARRIER if a in t), None)
        tm = re.findall(r"(\d{1,2}:\d{2}\s?[AP]M)", t)
        dep, arr = (tm[0] if tm else None), (tm[1] if len(tm) > 1 else None)
        fp = sha256(f"{origin}{dest}{travel_date}{airline}{dep}{arr}{total}".encode()).hexdigest() if False else \
             hashlib.sha256(f"{origin}{dest}{travel_date}{airline}{dep}{arr}{total}".encode()).hexdigest()
        if fp in seen: continue
        seen.add(fp)
        rows.append(dict(
            observation_id=str(uuid.uuid4()),
            search_timestamp=search_ts.isoformat(),          # OBSERVED
            travel_date=travel_date.isoformat(),
            advance_purchase_days=(travel_date - search_ts.date()).days,  # derived from observed ts
            origin_raw=origin, destination_raw=dest,
            origin_airport=origin, destination_airport=dest,
            route_id=f"{origin}-{dest}",
            carrier_code=CARRIER.get(airline), airline_name=airline,
            flight_number=None,                              # not exposed by source
            cabin_class=cabin.upper(), fare_class=None, fare_family=None,
            stops=parse_stops(t), duration_minutes=parse_duration(t),
            departure_time_local=dep, arrival_time_local=arr,
            base_fare=None, taxes_total=None, fees_charges=None,   # NULL, never invented
            gst_amount=None, fuel_surcharge=None,
            total_fare=total, currency="INR",
            source_platform="google_flights",
            source_url=f"https://www.google.com/travel/flights?q=Flights+to+{dest}+from+{origin}+on+{travel_date}",
            collection_method="html_fetch:fast-flights",
            raw_payload=str(raw_path.name),
            raw_payload_sha256=raw_payload_sha256,
            stored_file_sha256=stored_file_sha256,
            observation_key=f"{origin}-{dest}|{travel_date}|{apw}|{stamp}",
            quote_fingerprint=fp,
            normalization_status="NORMALIZED",
            validation_status="PENDING",
            validation_reasons=json.dumps(["fare_components_unavailable_from_source"]),
            horizon_code=f"H{apw:02d}", basket_status="CANDIDATE",
            fare_breakdown_status="TOTAL_ONLY",
        ))
    return rows, raw_path

if __name__ == "__main__":
    plan = json.loads(sys.argv[1])
    allrows = []
    for o, d, apw in plan:
        try:
            r, p = collect(o, d, apw)
            allrows += r
            print(f"OK {o}-{d} APW{apw}: {len(r)} quotes -> {p.name}", flush=True)
        except Exception as e:
            print(f"FAIL {o}-{d} APW{apw}: {type(e).__name__}: {e}", flush=True)
        time.sleep(2)
    OUT.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fp = OUT/f"aerocpi_observations_{ts}.jsonl"
    with open(fp, "w") as f:
        for r in allrows: f.write(json.dumps(r)+"\n")
    print("WROTE", fp, len(allrows))
