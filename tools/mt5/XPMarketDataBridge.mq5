// BTG AI Trader — persistent passive XP/MT5 market-data bridge for Sprint 1.
// Custom indicator only. Local file control; no account, position, or execution surface.
#property strict
#property indicator_chart_window
#property indicator_plots 0

const string PROVIDER_ID = "xp-mt5";
const string DISCOVERY_PREFIX = "WIN";
const string CONTROL_FILE = "btg_ai_trader\\capture-control.tsv";
const string STATUS_FILE = "btg_ai_trader\\capture-bridge-status.tsv";
const int CONTROL_POLL_MS = 250;

int tick_handle = INVALID_HANDLE;
int candle_handle = INVALID_HANDLE;
long tick_sequence = 0;
long candle_sequence = 0;
datetime current_bar_open = 0;
bool session_active = false;
string active_scope = "";
string active_instrument = "";
string blocked_scope = "";
long last_status_second = 0;

string EscapeJson(string value)
{
   StringReplace(value, "\\", "\\\\");
   StringReplace(value, "\"", "\\\"");
   return value;
}

int OpenAppend(const string path)
{
   int handle = FileOpen(
      path,
      FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_COMMON,
      0
   );
   if(handle == INVALID_HANDLE)
      return INVALID_HANDLE;
   if(!FileSeek(handle, 0, SEEK_END))
   {
      FileClose(handle);
      return INVALID_HANDLE;
   }
   return handle;
}

bool WriteLine(const int handle, const string line)
{
   if(FileWriteString(handle, line + "\n") <= 0)
      return false;
   FileFlush(handle);
   return true;
}

void CloseHandle(const int handle)
{
   if(handle != INVALID_HANDLE)
   {
      FileFlush(handle);
      FileClose(handle);
   }
}

bool IsDigits(const string value)
{
   if(StringLen(value) == 0)
      return false;
   for(int i = 0; i < StringLen(value); i++)
   {
      ushort code = (ushort)StringGetCharacter(value, i);
      if(code < 48 || code > 57)
         return false;
   }
   return true;
}

bool ValidScope(const string scope)
{
   string prefix = "s1-xp-capture-a";
   if(StringFind(scope, prefix) != 0)
      return false;
   return IsDigits(StringSubstr(scope, StringLen(prefix)));
}

bool ValidInstrument(const string symbol)
{
   if(StringLen(symbol) != 6 || StringSubstr(symbol, 0, 3) != "WIN")
      return false;
   ushort month_code = (ushort)StringGetCharacter(symbol, 3);
   ushort year_1 = (ushort)StringGetCharacter(symbol, 4);
   ushort year_2 = (ushort)StringGetCharacter(symbol, 5);
   return month_code >= 65 && month_code <= 90 &&
          year_1 >= 48 && year_1 <= 57 &&
          year_2 >= 48 && year_2 <= 57;
}

string ValueFor(const string field, const string key)
{
   string prefix = key + "=";
   if(StringFind(field, prefix) != 0)
      return "";
   return StringSubstr(field, StringLen(prefix));
}

bool ReadControl(string &scope, string &instrument)
{
   if(!FileIsExist(CONTROL_FILE, FILE_COMMON))
      return false;

   int handle = FileOpen(
      CONTROL_FILE,
      FILE_READ | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_COMMON,
      0
   );
   if(handle == INVALID_HANDLE)
      return false;

   string line = FileReadString(handle);
   FileClose(handle);
   string fields[];
   ushort separator = (ushort)StringGetCharacter("\t", 0);
   int count = StringSplit(line, separator, fields);
   if(count != 6 || fields[0] != "schema=1" || fields[1] != "state=ACTIVE")
      return false;

   scope = ValueFor(fields[2], "capture_scope");
   instrument = ValueFor(fields[3], "instrument");
   string provider = ValueFor(fields[4], "provider");
   string expiry_text = ValueFor(fields[5], "expires_epoch");
   if(!ValidScope(scope) || !ValidInstrument(instrument) || provider != PROVIDER_ID)
      return false;
   if(!IsDigits(expiry_text))
      return false;
   return (long)StringToInteger(expiry_text) > (long)TimeLocal();
}

bool WriteStatus(const string state, const string scope)
{
   int handle = FileOpen(
      STATUS_FILE,
      FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_COMMON,
      0
   );
   if(handle == INVALID_HANDLE)
      return false;

   string line = StringFormat(
      "schema=1\tstate=%s\tinstrument=%s\ttimeframe=%s\tprovider=%s\tcapture_scope=%s\tupdated_epoch=%I64d",
      state,
      _Symbol,
      EnumToString(_Period),
      PROVIDER_ID,
      scope,
      (long)TimeLocal()
   );
   bool ok = WriteLine(handle, line);
   CloseHandle(handle);
   return ok;
}

bool WriteDiscovery(const string path)
{
   int handle = OpenAppend(path);
   if(handle == INVALID_HANDLE)
      return false;

   string snapshot_id = StringFormat("%I64d-%I64u", (long)TimeLocal(), GetMicrosecondCount());
   int total = SymbolsTotal(false);
   int prefix_matches = 0;
   int emitted_symbols = 0;
   int excluded_custom = 0;
   int prefix_errors = 0;
   int enumeration_errors = 0;

   string begin = StringFormat(
      "{\"schema\":1,\"record_type\":\"snapshot_begin\",\"snapshot_id\":\"%s\","
      "\"prefix\":\"%s\",\"server_symbol_total\":%d}",
      EscapeJson(snapshot_id),
      EscapeJson(DISCOVERY_PREFIX),
      total
   );
   if(!WriteLine(handle, begin))
   {
      CloseHandle(handle);
      return false;
   }

   for(int i = 0; i < total; i++)
   {
      string name = SymbolName(i, false);
      if(name == "")
      {
         enumeration_errors++;
         continue;
      }
      if(StringFind(name, DISCOVERY_PREFIX) != 0)
         continue;

      prefix_matches++;
      bool custom = false;
      if(!SymbolExist(name, custom))
      {
         prefix_errors++;
         continue;
      }
      if(custom)
      {
         excluded_custom++;
         continue;
      }

      string row = StringFormat(
         "{\"schema\":1,\"record_type\":\"symbol\",\"snapshot_id\":\"%s\","
         "\"symbol\":\"%s\",\"custom\":false}",
         EscapeJson(snapshot_id),
         EscapeJson(name)
      );
      if(!WriteLine(handle, row))
      {
         CloseHandle(handle);
         return false;
      }
      emitted_symbols++;
   }

   string ending = StringFormat(
      "{\"schema\":1,\"record_type\":\"snapshot_end\",\"snapshot_id\":\"%s\","
      "\"prefix_matches\":%d,\"emitted_symbols\":%d,\"excluded_custom\":%d,"
      "\"prefix_errors\":%d,\"enumeration_errors\":%d}",
      EscapeJson(snapshot_id),
      prefix_matches,
      emitted_symbols,
      excluded_custom,
      prefix_errors,
      enumeration_errors
   );
   bool ok = WriteLine(handle, ending);
   CloseHandle(handle);
   return ok;
}

void StopSession()
{
   CloseHandle(tick_handle);
   CloseHandle(candle_handle);
   tick_handle = INVALID_HANDLE;
   candle_handle = INVALID_HANDLE;
   tick_sequence = 0;
   candle_sequence = 0;
   current_bar_open = 0;
   session_active = false;
   active_scope = "";
   active_instrument = "";
}

bool StartSession(const string scope, const string instrument)
{
   if(_Symbol != instrument || _Period != PERIOD_M1)
      return false;

   string root = "btg_ai_trader\\" + scope + "\\";
   string tick_path = root + "ticks.ndjson";
   string candle_path = root + "candles.ndjson";
   string discovery_path = root + "discovery.ndjson";
   if(FileIsExist(tick_path, FILE_COMMON) || FileIsExist(candle_path, FILE_COMMON) || FileIsExist(discovery_path, FILE_COMMON))
      return false;

   tick_handle = OpenAppend(tick_path);
   if(tick_handle == INVALID_HANDLE)
      return false;

   candle_handle = OpenAppend(candle_path);
   if(candle_handle == INVALID_HANDLE)
   {
      CloseHandle(tick_handle);
      tick_handle = INVALID_HANDLE;
      return false;
   }

   if(!WriteDiscovery(discovery_path))
   {
      StopSession();
      return false;
   }

   active_scope = scope;
   active_instrument = instrument;
   session_active = true;
   WriteStatus("ACTIVE", scope);
   return true;
}

void RefreshStatus()
{
   long now = (long)TimeLocal();
   if(now == last_status_second)
      return;
   last_status_second = now;
   WriteStatus(session_active ? "ACTIVE" : "IDLE", session_active ? active_scope : "");
}

void OnTimer()
{
   string scope = "";
   string instrument = "";
   bool has_control = ReadControl(scope, instrument);

   if(!has_control)
   {
      if(session_active)
         StopSession();
      blocked_scope = "";
      RefreshStatus();
      return;
   }

   if(session_active)
   {
      if(scope == active_scope && instrument == active_instrument)
      {
         RefreshStatus();
         return;
      }
      StopSession();
   }

   if(blocked_scope != scope && !StartSession(scope, instrument))
      blocked_scope = scope;
   RefreshStatus();
}

int OnInit()
{
   if(!EventSetMillisecondTimer(CONTROL_POLL_MS))
      return INIT_FAILED;
   WriteStatus("IDLE", "");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   StopSession();
   WriteStatus("OFFLINE", "");
}

int OnCalculate(
   const int rates_total,
   const int prev_calculated,
   const datetime &time[],
   const double &open[],
   const double &high[],
   const double &low[],
   const double &close[],
   const long &tick_volume[],
   const long &volume[],
   const int &spread[]
)
{
   if(!session_active || tick_handle == INVALID_HANDLE || candle_handle == INVALID_HANDLE)
      return prev_calculated;

   ArraySetAsSeries(time, true);
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);
   ArraySetAsSeries(tick_volume, true);
   ArraySetAsSeries(volume, true);
   ArraySetAsSeries(spread, true);

   MqlTick tick;
   if(SymbolInfoTick(_Symbol, tick))
   {
      tick_sequence++;
      string tick_line = StringFormat(
         "{\"schema\":1,\"provider\":\"%s\",\"symbol\":\"%s\",\"time_msc\":%I64d,"
         "\"bid\":%s,\"ask\":%s,\"last\":%s,\"volume\":%I64u,\"volume_real\":%s,"
         "\"flags\":%u,\"bridge_sequence\":%I64d}",
         PROVIDER_ID,
         EscapeJson(_Symbol),
         tick.time_msc,
         DoubleToString(tick.bid, _Digits),
         DoubleToString(tick.ask, _Digits),
         DoubleToString(tick.last, _Digits),
         tick.volume,
         DoubleToString(tick.volume_real, 8),
         tick.flags,
         tick_sequence
      );
      if(!WriteLine(tick_handle, tick_line))
         return prev_calculated;
   }

   if(rates_total < 2)
      return rates_total;
   if(current_bar_open == 0)
   {
      current_bar_open = time[0];
      return rates_total;
   }

   if(current_bar_open != time[0])
   {
      candle_sequence++;
      string candle_line = StringFormat(
         "{\"schema\":1,\"provider\":\"%s\",\"symbol\":\"%s\","
         "\"interval_start\":%I64d,\"interval_end\":%I64d,\"timeframe_seconds\":%d,"
         "\"finality\":\"FINAL\",\"open\":%s,\"high\":%s,\"low\":%s,\"close\":%s,"
         "\"tick_volume\":%I64d,\"volume\":%I64d,\"spread\":%d,\"bridge_sequence\":%I64d}",
         PROVIDER_ID,
         EscapeJson(_Symbol),
         (long)time[1],
         (long)time[0],
         PeriodSeconds(_Period),
         DoubleToString(open[1], _Digits),
         DoubleToString(high[1], _Digits),
         DoubleToString(low[1], _Digits),
         DoubleToString(close[1], _Digits),
         tick_volume[1],
         volume[1],
         spread[1],
         candle_sequence
      );
      if(!WriteLine(candle_handle, candle_line))
         return prev_calculated;
      current_bar_open = time[0];
   }

   return rates_total;
}