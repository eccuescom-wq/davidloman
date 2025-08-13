import os, time, json
from typing import Set, Tuple, Optional, List
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

GOOGLE_SERVICE_JSON = os.environ.get("GOOGLE_SERVICE_JSON", "")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID", "")
GOOGLE_SHEET_NAME = os.environ.get("GOOGLE_SHEET_NAME", "").strip() or None
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "300"))  # 5 phút

def _normalize(s: str) -> str:
    return (s or "").strip().upper().replace(" ", "")

class CodesIndexGS:
    def __init__(self):
        if not GOOGLE_SERVICE_JSON or not GOOGLE_SHEET_ID:
            raise RuntimeError("Missing GOOGLE_SERVICE_JSON or GOOGLE_SHEET_ID")
        info = json.loads(GOOGLE_SERVICE_JSON)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        self.service = build("sheets", "v4", credentials=creds, cache_discovery=False)
        self.codes: Set[str] = set()
        self._loaded_at: float = 0.0
        self._sheet_name: Optional[str] = GOOGLE_SHEET_NAME

    def _get_first_sheet_title(self) -> str:
        meta = self.service.spreadsheets().get(spreadsheetId=GOOGLE_SHEET_ID).execute()
        sheets = meta.get("sheets", [])
        if not sheets:
            raise RuntimeError("No sheets found in spreadsheet")
        return sheets[0]["properties"]["title"]

    def _fetch_values(self) -> List[List[str]]:
        title = self._sheet_name or self._get_first_sheet_title()
        res = self.service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=title
        ).execute()
        return res.get("values", [])

    def load(self) -> Tuple[int, float]:
        values = self._fetch_values()
        newset: Set[str] = set()
        cnt = 0
        for row in values:
            for cell in row:
                norm = _normalize(cell)
                if norm:
                    newset.add(norm)
                    cnt += 1
        self.codes = newset
        self._loaded_at = time.time()
        return cnt, self._loaded_at

    def maybe_reload(self) -> bool:
        if time.time() - self._loaded_at > CACHE_TTL_SECONDS:
            self.load()
            return True
        return False

    def contains(self, code: str) -> bool:
        return _normalize(code) in self.codes
