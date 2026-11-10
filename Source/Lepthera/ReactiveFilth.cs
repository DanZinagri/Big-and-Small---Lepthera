using RimWorld;
using Verse;

namespace Lepthera
{
    // Settings for Filth_Reactive, read from the filth ThingDef.
    // The filth reacts when it lands, and optionally each time more of it lands on the same pile.
    public class ReactiveFilthExtension : DefModExtension
    {
        // Chance to start a small fire in the cell when the filth reacts.
        public float igniteChance;

        // Size of that fire. Fire on bare ground with nothing to burn dies out quickly.
        public float fireSize = 0.3f;

        // Gas released in the cell when the filth reacts (255 = one full cell).
        public int gasAmount;

        public GasType gasType = GasType.ToxGas;

        // Whether adding to an existing pile reacts as well, not only a new pile.
        public bool reactOnThicken;
    }

    // Filth that starts a fire and/or releases gas where it lands. Used for the lepthera's ember
    // blood, fire vomit and tox blood (VEF's custom blood and vomit genes drop it like any filth).
    // No Harmony: it is the filth's own thingClass.
    public class Filth_Reactive : Filth
    {
        public override void SpawnSetup(Map map, bool respawningAfterLoad)
        {
            base.SpawnSetup(map, respawningAfterLoad);
            if (!respawningAfterLoad && !BeingTransportedOnGravship)
            {
                React();
            }
        }

        public override void ThickenFilth()
        {
            base.ThickenFilth();
            if (Spawned && def.GetModExtension<ReactiveFilthExtension>() is ReactiveFilthExtension ext && ext.reactOnThicken)
            {
                React();
            }
        }

        private void React()
        {
            if (Current.ProgramState != ProgramState.Playing)
            {
                return;
            }
            ReactiveFilthExtension ext = def.GetModExtension<ReactiveFilthExtension>();
            if (ext == null)
            {
                return;
            }
            Map map = Map;
            IntVec3 cell = Position;
            if (ext.gasAmount > 0)
            {
                GasUtility.AddGas(cell, map, ext.gasType, ext.gasAmount);
            }
            if (ext.igniteChance > 0f && Rand.Chance(ext.igniteChance))
            {
                TryIgnite(cell, map, ext.fireSize);
            }
        }

        // Spawns fire directly, since FireUtility.TryStartFireIn refuses cells with nothing
        // flammable in them. Never on water or where a fire already burns.
        private static void TryIgnite(IntVec3 cell, Map map, float fireSize)
        {
            if (!cell.InBounds(map) || cell.GetFirstThing<Fire>(map) != null)
            {
                return;
            }
            TerrainDef terrain = cell.GetTerrain(map);
            if (terrain != null && terrain.extinguishesFire)
            {
                return;
            }
            Fire fire = (Fire)ThingMaker.MakeThing(ThingDefOf.Fire);
            fire.fireSize = fireSize;
            GenSpawn.Spawn(fire, cell, map, Rot4.North);
        }
    }
}
