using System;
using System.Collections.Generic;
using System.Reflection;
using Verse;

namespace Lepthera
{
    // Mods/FacialAnimationExperimentals gives Lepthera_CompoundEyes carriers the Motz eye and lid types through FA's
    // targetGeneDefs. With the "use original eyes" setting on, those defs are pointed at a gene nobody has: FA then
    // offers them to no one (the gene-matched list needs a carried gene, the random list an empty targetGeneDefs),
    // so carriers keep the normal eyes. The defs stay loaded, so saves that reference them still load.
    // Startup only (the setting needs a restart). Reflection only: Facial Animation is optional.
    [StaticConstructorOnStartup]
    public static class CompoundEyeFaceTypes
    {
        static CompoundEyeFaceTypes()
        {
            if (!LeptheraMod.Settings.useOriginalEyes)
                return;
            Type faceTypeDef = GenTypes.GetTypeInAnyAssembly("FacialAnimation.FaceTypeDef");
            FieldInfo field = faceTypeDef?.GetField("targetGeneDefs", BindingFlags.Public | BindingFlags.Instance);
            if (field == null)
                return;
            foreach (Type type in faceTypeDef.AllSubclassesNonAbstract())
            {
                foreach (Def def in GenDefDatabase.GetAllDefsInDatabaseForDef(type))
                {
                    if (field.GetValue(def) is List<string> genes && genes.Remove("Lepthera_CompoundEyes"))
                        genes.Add("Lepthera_CompoundEyes_Disabled");
                }
            }
        }
    }
}
