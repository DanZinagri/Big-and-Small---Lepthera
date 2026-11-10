using System.Reflection;
using HarmonyLib;
using Verse;

namespace Lepthera
{
    public class LeptheraMod : Mod
    {
        public LeptheraMod(ModContentPack content) : base(content)
        {
            // The assembly is passed explicitly: on .NET 10 (1.7) the parameterless PatchAll() reads the calling
            // assembly off the stack, which breaks when the JIT inlines the call (Harmony issue #395).
            new Harmony("DanZinagri.BigSmall.Lepthera").PatchAll(Assembly.GetExecutingAssembly());
        }
    }
}
