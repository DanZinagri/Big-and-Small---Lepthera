using HarmonyLib;
using RimWorld;
using Verse;

namespace Lepthera
{
    // Lepthera eat cloth through FoodTypeFlags bit 8192, which has no enum name (see Lepthera_Race.xml and
    // Patches/Lepthera_ClothFood.xml). Vanilla's ToHumanString lists a hard-coded set of flags, so the
    // bit never showed in the info card's Diet entry or the "Can eat" tooltip. This appends it.
    // Callers that also benefit: RimHUD's food bar Diet line, OmniTab's food-type filter labels,
    // Chimera Creation's forced animal Diet entry (all call, none patch, checked 2026-11-10).
    [HarmonyPatch(typeof(FoodTypeFlagsExtension), nameof(FoodTypeFlagsExtension.ToHumanString))]
    public static class Patch_FoodTypeFlags_ToHumanString
    {
        public const FoodTypeFlags Cloth = (FoodTypeFlags)8192;

        public static void Postfix(FoodTypeFlags ft, ref string __result)
        {
            if ((ft & Cloth) == FoodTypeFlags.None)
            {
                return;
            }
            string cloth = "Lepthera_FoodTypeFlags_Cloth".Translate();
            __result = string.IsNullOrEmpty(__result) ? cloth : __result + ", " + cloth;
        }
    }
}
