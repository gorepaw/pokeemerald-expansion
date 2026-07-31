#ifndef GUARD_CONSTANTS_LEGENDARY_SLOTS_H
#define GUARD_CONSTANTS_LEGENDARY_SLOTS_H

// emerald+: the rotating legendary slots.
//
// Every one of the 13 Gen 1-3 legendaries that had no home now sits in a
// designed spot, and each of those spots is a SLOT that later hosts the Gen 4-9
// legendaries in turn. Six rooms whose story legendary is long gone by the
// postgame - Sky Pillar, the three Regi chambers, Cave of Origin and the Sealed
// Chamber - are slots too, which is what brings the count to 19 and the queue
// length down to 5.
//
// The rule, per slot: clear the occupant (catch it or defeat it) and the spot
// stays empty until the next time Kanto's Champion falls. There is no need to
// clear every slot in a round - each one tracks its own progress.
//
// Species are a fixed authored table, never a random draw. That is deliberate:
// re-entering the room rerolls nature, IVs and shininess (CreateScriptedWildMon
// builds a fresh personality every call) but must NOT reroll which Pokemon is
// standing there, or the encounter could not be hunted.

enum LegendarySlot
{
    LEGENDARY_SLOT_SEAFOAM_ISLANDS,     // Articuno
    LEGENDARY_SLOT_POWER_PLANT,         // Zapdos
    LEGENDARY_SLOT_MT_EMBER,            // Moltres
    LEGENDARY_SLOT_CERULEAN_CAVE,       // Mewtwo
    LEGENDARY_SLOT_NAVEL_ROCK_BASE,     // Lugia
    LEGENDARY_SLOT_NAVEL_ROCK_SUMMIT,   // Ho-Oh
    LEGENDARY_SLOT_BIRTH_ISLAND,        // Deoxys
    LEGENDARY_SLOT_FARAWAY_ISLAND,      // Mew
    LEGENDARY_SLOT_NEW_MAUVILLE,        // Raikou    (emerald+ placement)
    LEGENDARY_SLOT_FIERY_PATH,          // Entei     (emerald+ placement)
    LEGENDARY_SLOT_SHOAL_CAVE,          // Suicune   (emerald+ placement)
    LEGENDARY_SLOT_VIRIDIAN_FOREST,     // Celebi    (emerald+ placement)
    LEGENDARY_SLOT_METEOR_FALLS,        // Jirachi   (emerald+ placement)
    LEGENDARY_SLOT_SKY_PILLAR,          // Rayquaza's room
    LEGENDARY_SLOT_DESERT_RUINS,        // Regirock's room
    LEGENDARY_SLOT_ISLAND_CAVE,         // Regice's room
    LEGENDARY_SLOT_ANCIENT_TOMB,        // Registeel's room
    LEGENDARY_SLOT_CAVE_OF_ORIGIN,      // postgame
    LEGENDARY_SLOT_SEALED_CHAMBER,      // postgame
    NUM_LEGENDARY_SLOTS
};

// Longest queue any slot has. 90 Gen 4-9 families over 19 slots.
#define MAX_LEGENDARY_QUEUE   5

// Every legendary in this system battles at this level, Gen 1-3 originals
// included. They are hard enough to catch without also being high level.
#define LEGENDARY_SLOT_LEVEL  70

// State byte layout, one per slot, in SaveBlock1.
//   bits 0-5  advance index. 0 means the slot's ORIGINAL legendary is the
//             occupant - that one is run by its own vanilla script, not by us.
//             index N >= 1 means queue entry N-1 is the occupant.
//   bit  6    the original has been cleared and that fact has been banked.
//   bit  7    armed: the current occupant is gone and the slot is waiting on
//             the next Kanto Champion win before it refills.
#define LEGENDARY_SLOT_INDEX_MASK   0x3F
#define LEGENDARY_SLOT_PREREQ_DONE  (1 << 6)
#define LEGENDARY_SLOT_ARMED        (1 << 7)

#endif // GUARD_CONSTANTS_LEGENDARY_SLOTS_H
