using System.Reflection;
using HarmonyLib;
using UnityEngine;
using Verse;

namespace Lepthera
{
    public class LeptheraMod : Mod
    {
        public static LeptheraSettings Settings;

        public LeptheraMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<LeptheraSettings>();
            // The assembly is passed explicitly: on .NET 10 (1.7) the parameterless PatchAll() reads the calling
            // assembly off the stack, which breaks when the JIT inlines the call (Harmony issue #395).
            new Harmony("DanZinagri.BigSmall.Lepthera").PatchAll(Assembly.GetExecutingAssembly());
        }

        public override string SettingsCategory() => Content.Name;

        public override void DoSettingsWindowContents(Rect inRect)
        {
            Listing_Standard list = new Listing_Standard();
            list.Begin(inRect);
            list.CheckboxLabeled("Lepthera_Settings_UseOriginalEyes".Translate(), ref Settings.useOriginalEyes,
                "Lepthera_Settings_UseOriginalEyes_Desc".Translate());
            list.End();
        }
    }
}
