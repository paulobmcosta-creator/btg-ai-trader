// BTG AI Trader — passive Rico/MT5 market-data bridge for Sprint 1.
// Custom indicator only. Emits local market observations; no account or trading surface.
#property strict
#property indicator_chart_window
#property indicator_plots 0

input string BridgeFile = "btg_ai_trader\\rico_mt5_ticks.ndjson";

int bridge_handle = INVALID_HANDLE;
long bridge_sequence = 0;

string EscapeJson(string value)
{
   StringReplace(value, "\\", "\\\\");
   StringReplace(value, "\"", "\\\"");
   return value;
}

int OnInit()
{
   bridge_handle = FileOpen(
      BridgeFile,
      FILE_READ | FILE_WRITE | FILE_TXT | FILE_ANSI | FILE_SHARE_READ | FILE_COMMON,
      0
   );
   if(bridge_handle == INVALID_HANDLE)
      return INIT_FAILED;

   if(!FileSeek(bridge_handle, 0, SEEK_END))
   {
      FileClose(bridge_handle);
      bridge_handle = INVALID_HANDLE;
      return INIT_FAILED;
   }
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(bridge_handle != INVALID_HANDLE)
   {
      FileFlush(bridge_handle);
      FileClose(bridge_handle);
      bridge_handle = INVALID_HANDLE;
   }
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
   if(bridge_handle == INVALID_HANDLE)
      return prev_calculated;

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol, tick))
      return prev_calculated;

   bridge_sequence++;
   string line = StringFormat(
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
      bridge_sequence
   );

   if(FileWriteString(bridge_handle, line + "\n") <= 0)
      return prev_calculated;
   FileFlush(bridge_handle);
   return rates_total;
}
