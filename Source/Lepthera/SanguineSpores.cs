using System.Collections.Generic;
using System.Linq;
using RimWorld;
using UnityEngine;
using Verse;

namespace Lepthera
{
    /// <summary>
    /// Spore lesion: a real injury (tendable, can get infected, merges with an untended lesion on the
    /// same part) that bleeds like a vanilla wound, except the spores die off after 4~6 hours and the
    /// bleeding stops then instead of after vanilla's 1.5+ days. Tending stops it at once (vanilla).
    /// A merge (recast on an untended lesion) resets ageTicks, so the timer restarts.
    /// </summary>
    public class Hediff_SporeLesion : Hediff_Injury
    {
        private const int MinBleedTicks = 10000;
        private const int MaxBleedTicks = 15000;

        private int bleedTicks = -1;

        private bool SporesDead => bleedTicks >= 0 && ageTicks >= bleedTicks;

        public override float BleedRate => SporesDead ? 0f : base.BleedRate;

        public override void PostAdd(DamageInfo? dinfo)
        {
            base.PostAdd(dinfo);
            if (bleedTicks < 0)
            {
                bleedTicks = Rand.RangeInclusive(MinBleedTicks, MaxBleedTicks);
            }
        }

        public override void TickInterval(int delta)
        {
            bool before = SporesDead;
            base.TickInterval(delta);
            if (before != SporesDead)
            {
                pawn.health.Notify_HediffChanged(this);
            }
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref bleedTicks, "leptheraBleedTicks", -1);
        }
    }

    /// <summary>
    /// Sanguine spores: gives every flesh pawn within the radius around the caster a spore lesion on
    /// a lung (or the torso if it has none). The rot stink and the red spore burst come from the
    /// ability's other comps.
    /// </summary>
    public class CompProperties_AbilitySporeBleed : CompProperties_AbilityEffect
    {
        public HediffDef hediff;

        public float radius = 3.5f;

        /// <summary>Lesion size in hit points; capped at 30% of the part's current health so one cast never destroys it.</summary>
        public float severity = 1.5f;

        /// <summary>Only pawns hostile to the caster bleed. The rot stink still reaches everyone.</summary>
        public bool onlyHostiles = true;

        public CompProperties_AbilitySporeBleed()
        {
            compClass = typeof(CompAbilityEffect_SporeBleed);
        }
    }

    public class CompAbilityEffect_SporeBleed : CompAbilityEffect
    {
        public new CompProperties_AbilitySporeBleed Props => (CompProperties_AbilitySporeBleed)props;

        public override void Apply(LocalTargetInfo target, LocalTargetInfo dest)
        {
            base.Apply(target, dest);
            Pawn caster = parent.pawn;
            Map map = caster?.Map;
            if (map == null || Props.hediff == null)
            {
                return;
            }
            List<Pawn> victims = new List<Pawn>();
            foreach (Thing thing in GenRadial.RadialDistinctThingsAround(caster.Position, map, Props.radius, useCenter: true))
            {
                if (thing is Pawn pawn && pawn != caster && !pawn.Dead && pawn.RaceProps.IsFlesh
                    && (!Props.onlyHostiles || pawn.HostileTo(caster)))
                {
                    victims.Add(pawn);
                }
            }
            foreach (Pawn pawn in victims)
            {
                BodyPartRecord part = pawn.health.hediffSet.GetNotMissingParts()
                    .Where(p => p.def.tags.Contains(BodyPartTagDefOf.BreathingSource) && p.coverageAbs > 0f)
                    .RandomElementWithFallback(pawn.RaceProps.body.corePart);
                if (part == null)
                {
                    continue;
                }
                Hediff lesion = HediffMaker.MakeHediff(Props.hediff, pawn, part);
                // Cap against the part's current health via the health tracker (Elite Bionics
                // Framework flags direct BodyPartDef.GetMaxHealth calls).
                float partHealth = pawn.health.hediffSet.GetPartHealth(part);
                if (partHealth <= 0f)
                {
                    continue;
                }
                lesion.Severity = Mathf.Min(Props.severity, partHealth * 0.3f);
                pawn.health.AddHediff(lesion, part);
            }
        }

        public override void DrawEffectPreview(LocalTargetInfo target)
        {
            GenDraw.DrawRadiusRing(parent.pawn.Position, Props.radius);
        }
    }
}
