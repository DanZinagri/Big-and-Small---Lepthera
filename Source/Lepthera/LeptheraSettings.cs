using Verse;

namespace Lepthera
{
    public class LeptheraSettings : ModSettings
    {
        // Off: compound-eye carriers get the Motz eye/lid types (FA Experimentals). On: they keep normal FA eyes.
        public bool useOriginalEyes;

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref useOriginalEyes, "useOriginalEyes", false);
        }
    }
}
