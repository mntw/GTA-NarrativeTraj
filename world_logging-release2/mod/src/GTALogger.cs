using GTA;
using GTA.Chrono;
using GTA.Native;
using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;
using System.Windows.Forms;

public class GTALogger : Script
{
    private static readonly CultureInfo invc = CultureInfo.InvariantCulture;
    private DateTime lastWritten = DateTime.Now;
    private static Ped player = Game.Player.Character;
    private static readonly WebClient webClient = new WebClient();
    private static readonly string uri = "http://localhost:8080";

    // Memory locations
    private static readonly long baseAddr = Process.GetProcessesByName("GTA5")[0].MainModule.BaseAddress.ToInt64();
    private static readonly IntPtr isSubtitlesActiveAddr = (IntPtr)(baseAddr + 0x2738650);
    private static readonly IntPtr SubtitlesAddr = (IntPtr)(baseAddr + 0x2738653);
    private static readonly IntPtr SoundBankAddr = (IntPtr)(baseAddr + 0x2088558);
    private static readonly int conversationLineOffset = 120;

    private string previousSubtitles = "";

    private int intervalMs = 500;

    public GTALogger()
    {
        Tick += OnTick;
        KeyUp += OnKeyUp;
        KeyDown += OnKeyDown;
        webClient.UploadString(uri, "char;time_ingame;time_rw;pos;vehicle;subtitles_text;speaker;soundbank");
    }

    private void OnTick(object sender, EventArgs e)
    {
        if ((DateTime.Now - lastWritten).Milliseconds >= intervalMs)
        {
            Log();
            lastWritten = DateTime.Now;
        }
    }

    private void OnKeyDown(object sender, KeyEventArgs e)
    {

    }

    private void OnKeyUp(object sender, KeyEventArgs e)
    {
        //if (e.KeyCode == Keys.PageUp)
        //{
        //    Log();
        //}
    }

    private void Log()
    {
        string pos = String.Format(invc, "{0},{1},{2}", player.Position.X, player.Position.Y, player.Position.Y);
        string time_ingame = DateTimeToHHMMSS(GameClock.Now);
        string time_rw = DateTimeToHHMMSS(DateTime.Now);

        string vehicle = "";
        if (player.IsInVehicle())
        {
            vehicle = String.Format("{0},{1},{2}", player.IsInVehicle(), player.CurrentVehicle.ClassType.ToString(), player.CurrentVehicle.DisplayName);
        }
        Process[] procs = Process.GetProcessesByName("GTA5");


        bool isSubtitlesActive = (Marshal.ReadByte(isSubtitlesActiveAddr) > 0) ? true : false;
        string subtitles = "";
        string soundbank = "";
        int conversationLine = Function.Call<int>(Hash.GET_CURRENT_SCRIPTED_CONVERSATION_LINE);
        if (isSubtitlesActive)
        {
            subtitles = GetTextFromMemoryAddr(SubtitlesAddr);
            if (conversationLine >= 0)
                soundbank = GetTextFromMemoryAddr(SoundBankAddr + (conversationLineOffset * conversationLine));
            else
                soundbank = "Cutscene"; // so far didn't find a way to detect current speaker during cutscene
                                        // since Ped.IsScriptedSpeechPlaying is not set
            if (subtitles.Equals(previousSubtitles) || subtitles.Contains("~"))
            {
                subtitles = "";
                soundbank = "";
            }
            else
            {
                previousSubtitles = subtitles;
            }
        }
        string to_write = String.Format("{0};{1};{2};{3};{4};{5};{6}", GetPlayerName(player), time_ingame, time_rw, pos, vehicle, subtitles, soundbank);
        webClient.UploadString(uri, to_write);
        
        
    }
    private string GetPlayerName(Ped player)
    {
        switch ((uint)player.Model.GetHashCode())
        {
            case (uint)PedHash.Michael:
                return "Michael";
            case (uint)PedHash.Trevor:
                return "Trevor";
            case (uint)PedHash.Franklin:
                return "Franklin";
            default:
                return "???";
        }
    }
    
    private string DateTimeToHHMMSS(DateTime date)
    {
        return date.ToString("HH:mm:ss");
    }

    private string DateTimeToHHMMSS(GameClockDateTime date)
    {
        return String.Format("{0:D2}:{1:D2}:{2:D2}", date.Hour, date.Minute, date.Second);
    }

    private string GetTextFromMemoryAddr(IntPtr startAddr)
    {
        return Marshal.PtrToStringAnsi(startAddr);
    }

}
