using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace Lepthera
{
    /// <summary>
    /// Fungal vampirism resurrection: vanilla's resurrect ability, after which the caster's germline
    /// (endogenes and inheritable xenotype) overwrites the risen pawn's germline. Xenogenes are left
    /// alone, like a germline implant. The caster's genes do not need to regrow.
    /// </summary>
    public class CompProperties_FungalResurrect : CompProperties_AbilityEffect
    {
        public CompProperties_FungalResurrect()
        {
            compClass = typeof(CompAbilityEffect_FungalResurrect);
        }
    }

    public class CompAbilityEffect_FungalResurrect : CompAbilityEffect
    {
        public override void Apply(LocalTargetInfo target, LocalTargetInfo dest)
        {
            base.Apply(target, dest);
            if (!(target.Thing is Corpse corpse))
            {
                return;
            }
            Pawn risen = corpse.InnerPawn;
            if (!ResurrectionUtility.TryResurrectWithSideEffects(risen))
            {
                return;
            }
            ImplantGermline(parent.pawn, risen);
            Messages.Message("MessagePawnResurrected".Translate(risen), risen, MessageTypeDefOf.PositiveEvent);
            MoteMaker.MakeAttachedOverlay(risen, ThingDefOf.Mote_ResurrectFlash, Vector3.zero);
        }

        public override bool Valid(LocalTargetInfo target, bool throwMessages = false)
        {
            if (!(target.Thing is Corpse corpse))
            {
                return false;
            }
            if (corpse.GetRotStage() == RotStage.Dessicated)
            {
                if (throwMessages)
                {
                    Messages.Message("MessageCannotResurrectDessicatedCorpse".Translate(), corpse, MessageTypeDefOf.RejectInput, historical: false);
                }
                return false;
            }
            if (corpse.InnerPawn?.genes == null || !corpse.InnerPawn.RaceProps.Humanlike)
            {
                return false;
            }
            return base.Valid(target, throwMessages);
        }

        /// <summary>Replaces the recipient's endogenes with the caster's (removing before adding,
        /// so no gene is left marked as overridden by one that is about to go).</summary>
        public static void ImplantGermline(Pawn caster, Pawn recipient)
        {
            Pawn_GeneTracker from = caster?.genes;
            Pawn_GeneTracker to = recipient?.genes;
            if (from == null || to == null)
            {
                return;
            }
            List<GeneDef> germline = new List<GeneDef>();
            foreach (Gene gene in from.Endogenes)
            {
                germline.Add(gene.def);
            }
            for (int i = to.Endogenes.Count - 1; i >= 0; i--)
            {
                to.RemoveGene(to.Endogenes[i]);
            }
            foreach (GeneDef def in germline)
            {
                to.AddGene(def, xenogene: false);
            }
            if (from.Xenotype != null && from.Xenotype.inheritable)
            {
                to.SetXenotypeDirect(from.Xenotype);
                to.xenotypeName = from.xenotypeName;
                to.iconDef = from.iconDef;
            }
        }
    }

    /// <summary>
    /// Our copy of VRE - Fungoid's fungal flesh: eating fungus counts as eating human meat (for
    /// cannibal precepts). Fungoid also stops the normal "ate non-cannibal food" thought, which needs
    /// Harmony; this copy doesn't, so it only adds the cannibal event.
    /// </summary>
    public class Gene_FungalFlesh : Gene
    {
        public override void Notify_IngestedThing(Thing thing, int numTaken)
        {
            base.Notify_IngestedThing(thing, numTaken);
            if (!Active || thing?.def == null || !thing.def.IsFungus)
            {
                return;
            }
            pawn.mindState.lastHumanMeatIngestedTick = Find.TickManager.TicksGame;
            Find.HistoryEventsManager.RecordEvent(new HistoryEvent(HistoryEventDefOf.AteHumanMeat, pawn.Named(HistoryEventArgsNames.Doer)));
        }
    }
}
