// BTG AI Trader — passive Rico/MT5 market-data bridge for Sprint 1.
// Custom indicator only. Emits local market observations; no account or trading surface.
#property strict
#property indicator_chart_window
#property indicator_plots 0

input string TickBridgeFile = "btg_ai_trader\\rico_mt5_ticks.ndjson";
input string CandleBridgeFile = "btg_ai_trader\\rico_mt5_candles.ndjson";
input string DiscoveryBridgeFile = "btg_ai_trader\\rico_mt5_discovery.ndjson";
input string DiscoveryPrefix = "WIN";

int tick_bridge_handle = INVALID_HANDLE;
int candle_bridge_handle = INVALID_HANDLE;
long tick_bridge_sequence = 0;
long candle_bridge_sequence = 0;
datetime current_bar_open = 0;

string EscapeJson(string value)
{
   StringReplace(value, "\\", "\\\\");
   StringReplace(value, "\"", "\\\"");
   return value;
}

int OpenAppendBridge(string path)
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

bool WriteBridgeLine(const int handle, const string line)
{
   if(FileWriteString(handle, line + "\n") <= 0)
      return false;
   FileFlush(handle);
   return true;
}

void CloseBridge(const int handle)
{
   if(handle != INVALID_HANDLE)
   {
      FileFlush(handle);
      FileClose(handle);
   }
}

bool WriteDiscoverySnapshot()
{
   int handle = OpenAppendBridge(DiscoveryBridgeFile);
   if(handle == INVALID_HANDLE)
      return false;

   string snapshot_id = StringFormat(
      "%I64d-%I64u",
      (long)TimeLocal(),
      GetMicrosecondCount()
   );
   int total = SymbolsTotal(false);
   int prefix_matches = 0;
   int emitted_symbols = 0;
   int excluded_custom = 0;
   int prefix_errors = 0;
   int enumeration_errors = 0;

   string begin = StringFormat(
      "{\"schema\":1,\"record_type\":\"snapshot_begin\","
      "\"snapshot_id\":\"%s\",\"prefix\":\"%s\",\"server_symbol_total\":%d}",
      EscapeJson(snapshot_id),
      EscapeJson(DiscoveryPrefix),
      total
   );
   if(!WriteBridgeLine(handle, begin))
   {
      CloseBridge(handle);
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
      if(DiscoveryPrefix != "" && StringFind(name, DiscoveryPrefix) != 0)
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

      string line = StringFormat(
         "{\"schema\":1,\"record_type\":\"symbol\",\"snapshot_id\":\"%s\","
         "\"symbol\":\"%s\",\"custom\":false}",
         EscapeJson(snapshot_id),
         EscapeJson(name)
      );
      if(!WriteBridgeLine(handle, line))
      {
         CloseBridge(handle);
         return false;
      }
      emitted_symbols++;
   }

   string ending = StringFormat(
      "{\"schema\":1,\"record_type\":\"snapshot_end\","
      "\"snapshot_id\":\"%s\",\"prefix_matches\":%d,\"emitted_symbols\":%d,"
      "\"excluded_custom\":%d,\"prefix_errors\":%d,\"enumeration_errors\":%d}",
      EscapeJson(snapshot_id),
      prefix_matches,
      emitted_symbols,
      excluded_custom,
      prefix_errors,
      enumeration_errors
   );
   bool written = WriteBridgeLine(handle, ending);
   CloseBridge(handle);
   return written;
}

int OnInit()
{
   if(!WriteDiscoverySnapshot())
      return INIT_FAILED;

   tick_bridge_handle = OpenAppendBridge(TickBridgeFile);
   if(tick_bridge_handle == INVALID_HANDLE)
      return INIT_FAILED;

   candle_bridge_handle = OpenAppendBridge(CandleBridgeFile);
   if(candle_bridge_handle == INVALID_HANDLE)
   {
      CloseBridge(tick_bridge_handle);
      tick_bridge_handle = INVALID_HANDLE;
      return INIT_FAILED;
   }
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   CloseBridge(tick_bridge_handle);
   CloseBridge(candle_bridge_handle);
   tick_bridge_handle = INVALID_HANDLE;
   candle_bridge_handle = INVALID_HANDLE;
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
   if(tick_bridge_handle == INVALID_HANDLE || candle_bridge_handle == INVALID_HANDLE)
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
      tick_bridge_sequence++;
      string tick_line = StringFormat(
         "{\"schema\":1,\"provider\":\"rico-mt5\",\"symbol\":\"%s\","
         "\"time_msc\":%I64d,\"bid\":%s,\"ask\":%s,\"last\":%s,"
         "\"volume\":%I64u,\"volume_real\":%s,\"flags\":%u,"
         "\"bridge_sequence\":%I64d}",
         EscapeJson(_Symbol),
         tick.time_msc,
         DoubleToString(tick.bid, _Digits),
         DoubleToString(tick.ask, _Digits),
         DoubleToString(tick.last, _Digits),
         tick.volume,
         DoubleToString(tick.volume_real, 8),
         tick.flags,
         tick_bridge_sequence
      );
      if(!WriteBridgeLine(tick_bridge_handle, tick_line))
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
      candle_bridge_sequence++;
      string candle_line = StringFormat(
         "{\"schema\":1,\"provider\":\"rico-mt5\",\"symbol\":\"%s\","
         "\"interval_start\":%I64d,\"interval_end\":%I64d,"
         "\"timeframe_seconds\":%d,\"finality\":\"FINAL\","
         "\"open\":%s,\"high\":%s,\"low\":%s,\"close\":%s,"
         "\"tick_volume\":%I64d,\"volume\":%I64d,\"spread\":%d,"
         "\"bridge_sequence\":%I64d}",
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
         candle_bridge_sequence
      );
      if(!WriteBridgeLine(candle_bridge_handle, candle_line))
         return prev_calculated;
      current_bar_open = time[0];
   }

   return rates_total;
}
