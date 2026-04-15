import zoneinfo
from datetime import datetime
try:
    tz = zoneinfo.ZoneInfo("America/Argentina/Buenos_Aires")
    print(f"Time: {datetime.now(tz)}")
except Exception as e:
    print(f"Error: {e}")
