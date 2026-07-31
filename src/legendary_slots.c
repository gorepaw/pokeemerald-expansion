#include "global.h"
#include "event_data.h"
#include "item.h"
#include "sound.h"
#include "script_pokemon_util.h"
#include "constants/event_objects.h"
#include "constants/flags.h"
#include "constants/items.h"
#include "constants/legendary_slots.h"
#include "constants/species.h"
#include "constants/vars.h"

// emerald+: rotating legendary slots. See include/constants/legendary_slots.h
// for the rules; this file is the whole implementation.
//
// The feature is deliberately ADDITIVE. Not one of the existing legendary
// scripts is rewritten - Deoxys keeps its triangle puzzle, Mew keeps its grass
// sequence, the Regis keep their Braille doors. Each slot instead gains a
// SECOND object event on the same tile that only ever hosts the Gen 4-9
// successors, and the original legendary's own "resolved" flag becomes this
// slot's prerequisite. If anything here is wrong, vanilla still works.

struct LegendarySlotData
{
    u16 prereqFlag;                     // original cleared: caught or defeated
    u16 prereqFlag2;                    // some maps use a separate caught flag
    u16 hideFlag;                       // hide flag of the successor object
    u16 queue[MAX_LEGENDARY_QUEUE];     // SPECIES_NONE pads a short queue
};

// Rayquaza and the Regis set FLAG_DEFEATED_* on BOTH the caught and the
// defeated path, so one flag covers "resolved" for them. Lugia, Ho-Oh, Mew and
// Deoxys use a separate caught flag, hence prereqFlag2.
static const struct LegendarySlotData sLegendarySlots[NUM_LEGENDARY_SLOTS] =
{
    [LEGENDARY_SLOT_SEAFOAM_ISLANDS] = {
        FLAG_FOUGHT_ARTICUNO, 0, FLAG_EP_HIDE_SLOT_SEAFOAM_ISLANDS,
        { SPECIES_IRON_BUNDLE, SPECIES_GLASTRIER, SPECIES_KYUREM, SPECIES_BUZZWOLE, SPECIES_PHEROMOSA } },
    [LEGENDARY_SLOT_POWER_PLANT] = {
        FLAG_FOUGHT_ZAPDOS, 0, FLAG_EP_HIDE_SLOT_POWER_PLANT,
        { SPECIES_TAPU_KOKO, SPECIES_XURKITREE, SPECIES_ZERAORA, SPECIES_REGIELEKI, SPECIES_MIRAIDON } },
    [LEGENDARY_SLOT_MT_EMBER] = {
        FLAG_FOUGHT_MOLTRES, 0, FLAG_EP_HIDE_SLOT_MT_EMBER,
        { SPECIES_HEATRAN, SPECIES_VOLCANION, SPECIES_BLACEPHALON, SPECIES_IRON_MOTH, SPECIES_GOUGING_FIRE } },
    [LEGENDARY_SLOT_CERULEAN_CAVE] = {
        FLAG_FOUGHT_MEWTWO, 0, FLAG_EP_HIDE_SLOT_CERULEAN_CAVE,
        { SPECIES_UXIE, SPECIES_MESPRIT, SPECIES_AZELF, SPECIES_CRESSELIA, SPECIES_COSMOG } },
    [LEGENDARY_SLOT_NAVEL_ROCK_BASE] = {
        FLAG_DEFEATED_LUGIA, FLAG_CAUGHT_LUGIA, FLAG_EP_HIDE_SLOT_NAVEL_ROCK_BASE,
        { SPECIES_PHIONE, SPECIES_MANAPHY, SPECIES_TAPU_FINI, SPECIES_YVELTAL, SPECIES_IRON_JUGULIS } },
    [LEGENDARY_SLOT_NAVEL_ROCK_SUMMIT] = {
        FLAG_DEFEATED_HO_OH, FLAG_CAUGHT_HO_OH, FLAG_EP_HIDE_SLOT_NAVEL_ROCK_SUMMIT,
        { SPECIES_CHI_YU, SPECIES_REGIGIGAS, SPECIES_TYPE_NULL, SPECIES_SILVALLY, SPECIES_TERAPAGOS } },
    [LEGENDARY_SLOT_BIRTH_ISLAND] = {
        FLAG_DEFEATED_DEOXYS, FLAG_BATTLED_DEOXYS, FLAG_EP_HIDE_SLOT_BIRTH_ISLAND,
        { SPECIES_IRON_BOULDER, SPECIES_VICTINI, SPECIES_HOOPA, SPECIES_NECROZMA, SPECIES_MUNKIDORI } },
    [LEGENDARY_SLOT_FARAWAY_ISLAND] = {
        FLAG_DEFEATED_MEW, FLAG_CAUGHT_MEW, FLAG_EP_HIDE_SLOT_FARAWAY_ISLAND,
        { SPECIES_CALYREX, SPECIES_TAPU_LELE, SPECIES_IRON_LEAVES, SPECIES_SCREAM_TAIL, SPECIES_ZARUDE } },
    [LEGENDARY_SLOT_NEW_MAUVILLE] = {
        FLAG_EP_FOUGHT_RAIKOU, 0, FLAG_EP_HIDE_SLOT_NEW_MAUVILLE,
        { SPECIES_SANDY_SHOCKS, SPECIES_RAGING_BOLT, SPECIES_IRON_HANDS, SPECIES_ETERNATUS, SPECIES_OKIDOGI } },
    [LEGENDARY_SLOT_FIERY_PATH] = {
        FLAG_EP_FOUGHT_ENTEI, 0, FLAG_EP_HIDE_SLOT_FIERY_PATH,
        { SPECIES_GREAT_TUSK, SPECIES_ZAMAZENTA, SPECIES_KUBFU, SPECIES_SLITHER_WING, SPECIES_KORAIDON } },
    [LEGENDARY_SLOT_SHOAL_CAVE] = {
        FLAG_EP_FOUGHT_SUICUNE, 0, FLAG_EP_HIDE_SLOT_SHOAL_CAVE,
        { SPECIES_CHIEN_PAO, SPECIES_DARKRAI, SPECIES_GUZZLORD, SPECIES_WO_CHIEN, SPECIES_POIPOLE } },
    [LEGENDARY_SLOT_VIRIDIAN_FOREST] = {
        FLAG_EP_FOUGHT_CELEBI, 0, FLAG_EP_HIDE_SLOT_VIRIDIAN_FOREST,
        { SPECIES_TAPU_BULU, SPECIES_VIRIZION, SPECIES_KARTANA, SPECIES_BRUTE_BONNET, SPECIES_OGERPON } },
    [LEGENDARY_SLOT_METEOR_FALLS] = {
        FLAG_EP_FOUGHT_JIRACHI, 0, FLAG_EP_HIDE_SLOT_METEOR_FALLS,
        { SPECIES_DIALGA, SPECIES_STAKATAKA, SPECIES_COBALION, SPECIES_MELTAN, SPECIES_MELMETAL } },
    [LEGENDARY_SLOT_SKY_PILLAR] = {
        FLAG_DEFEATED_RAYQUAZA, 0, FLAG_EP_HIDE_SLOT_SKY_PILLAR,
        { SPECIES_RESHIRAM, SPECIES_ZEKROM, SPECIES_ZYGARDE, SPECIES_REGIDRAGO, SPECIES_ROARING_MOON } },
    [LEGENDARY_SLOT_DESERT_RUINS] = {
        FLAG_DEFEATED_REGIROCK, 0, FLAG_EP_HIDE_SLOT_DESERT_RUINS,
        { SPECIES_TERRAKION, SPECIES_DIANCIE, SPECIES_NIHILEGO, SPECIES_IRON_THORNS, SPECIES_NONE } },
    [LEGENDARY_SLOT_ISLAND_CAVE] = {
        FLAG_DEFEATED_REGICE, 0, FLAG_EP_HIDE_SLOT_ISLAND_CAVE,
        { SPECIES_XERNEAS, SPECIES_ZACIAN, SPECIES_IRON_VALIANT, SPECIES_FEZANDIPITI, SPECIES_NONE } },
    [LEGENDARY_SLOT_ANCIENT_TOMB] = {
        FLAG_DEFEATED_REGISTEEL, 0, FLAG_EP_HIDE_SLOT_ANCIENT_TOMB,
        { SPECIES_CELESTEELA, SPECIES_MAGEARNA, SPECIES_IRON_CROWN, SPECIES_GENESECT, SPECIES_NONE } },
    [LEGENDARY_SLOT_CAVE_OF_ORIGIN] = {
        FLAG_SYS_GAME_CLEAR, 0, FLAG_EP_HIDE_SLOT_CAVE_OF_ORIGIN,
        { SPECIES_PALKIA, SPECIES_WALKING_WAKE, SPECIES_IRON_TREADS, SPECIES_TING_LU, SPECIES_NONE } },
    [LEGENDARY_SLOT_SEALED_CHAMBER] = {
        FLAG_SYS_GAME_CLEAR, 0, FLAG_EP_HIDE_SLOT_SEALED_CHAMBER,
        { SPECIES_PECHARUNT, SPECIES_MARSHADOW, SPECIES_SPECTRIER, SPECIES_FLUTTER_MANE, SPECIES_NONE } },
};

// Handed out one per Kanto Champion win, in this order. Each unlocks a ferry
// destination that already exists in full - Lilycove and Vermilion both offer
// the routes, gated on holding the ticket.
static const u16 sEventTickets[][2] =
{
    { ITEM_MYSTIC_TICKET,  FLAG_ENABLE_SHIP_NAVEL_ROCK   },  // Lugia, Ho-Oh
    { ITEM_AURORA_TICKET,  FLAG_ENABLE_SHIP_BIRTH_ISLAND },  // Deoxys
    { ITEM_OLD_SEA_MAP,    FLAG_ENABLE_SHIP_FARAWAY_ISLAND }, // Mew
};

// The slot whose battle is currently running. Saved so the script does not have
// to carry the slot through the battle in a var - VAR_0x8004 is scratch and the
// battle is free to clobber it. Nothing can be saved or reloaded mid-encounter,
// so an EWRAM static is enough.
static u8 sActiveSlot;

static bool8 PrereqMet(u8 slot)
{
    const struct LegendarySlotData *s = &sLegendarySlots[slot];

    if (s->prereqFlag != 0 && FlagGet(s->prereqFlag))
        return TRUE;
    if (s->prereqFlag2 != 0 && FlagGet(s->prereqFlag2))
        return TRUE;
    return FALSE;
}

static u16 SlotOccupant(u8 slot)
{
    u8 state = gSaveBlock1Ptr->legendarySlots[slot];
    u8 index = state & LEGENDARY_SLOT_INDEX_MASK;

    if (state & LEGENDARY_SLOT_ARMED)
        return SPECIES_NONE;    // cleared, waiting on the next Champion win
    if (index == 0)
        return SPECIES_NONE;    // the original legendary still owns the spot
    if (index > MAX_LEGENDARY_QUEUE)
        return SPECIES_NONE;    // this slot's pool has run dry for good
    return sLegendarySlots[slot].queue[index - 1];
}

// Called from each host map's ON_TRANSITION with the slot in VAR_0x8004.
// Shows or hides the successor object and points it at the right species.
void UpdateLegendarySlot(void)
{
    u8 slot = gSpecialVar_0x8004;
    u16 species;

    if (slot >= NUM_LEGENDARY_SLOTS)
        return;

    // Clearing the original arms the slot exactly once, so that a spot whose
    // legendary was taken long ago still waits for a Champion win before it
    // refills - the same rule every later occupant follows.
    if (!(gSaveBlock1Ptr->legendarySlots[slot] & LEGENDARY_SLOT_PREREQ_DONE)
     && PrereqMet(slot))
    {
        gSaveBlock1Ptr->legendarySlots[slot] |=
            LEGENDARY_SLOT_PREREQ_DONE | LEGENDARY_SLOT_ARMED;
    }

    species = SlotOccupant(slot);
    if (species == SPECIES_NONE)
    {
        FlagSet(sLegendarySlots[slot].hideFlag);
    }
    else
    {
        FlagClear(sLegendarySlots[slot].hideFlag);
        // OBJ_EVENT_GFX_SPECIES() is a compile-time macro; at runtime the same
        // encoding is just the species plus the OBJ_EVENT_MON bit.
        VarSet(VAR_OBJ_GFX_ID_0, species + OBJ_EVENT_MON);
    }
}

// Builds the wild battle. setwildbattle reads its species as a literal
// halfword, so a slot whose occupant changes cannot use it.
void SetUpLegendarySlotBattle(void)
{
    u8 slot = gSpecialVar_0x8004;
    u16 species = (slot < NUM_LEGENDARY_SLOTS) ? SlotOccupant(slot) : SPECIES_NONE;

    gSpecialVar_Result = species;
    if (species == SPECIES_NONE)
        return;

    sActiveSlot = slot;

    // Fresh personality and fresh IVs every call, which is what makes these
    // huntable: re-entering the room rerolls nature and shininess while the
    // species stays put.
    SetScriptedWildMon(species, LEGENDARY_SLOT_LEVEL);
}

// Plays the cry of whatever is standing in the slot. playmoncry takes its
// species as a literal, so it cannot be used here either.
void PlayLegendarySlotCry(void)
{
    u16 species = SlotOccupant(sActiveSlot);

    if (species != SPECIES_NONE)
        PlayCry_Normal(species, 0);
}

// The occupant is gone - caught or defeated. Arm the slot.
void ArmLegendarySlot(void)
{
    if (sActiveSlot < NUM_LEGENDARY_SLOTS)
        gSaveBlock1Ptr->legendarySlots[sActiveSlot] |= LEGENDARY_SLOT_ARMED;
}

// Kanto's Champion has fallen. Every armed slot refills with its next
// occupant; slots the player has not cleared are untouched.
void AdvanceLegendarySlotsOnChampion(void)
{
    u8 slot;

    for (slot = 0; slot < NUM_LEGENDARY_SLOTS; slot++)
    {
        u8 state = gSaveBlock1Ptr->legendarySlots[slot];

        if (!(state & LEGENDARY_SLOT_ARMED))
            continue;

        state &= ~LEGENDARY_SLOT_ARMED;
        if ((state & LEGENDARY_SLOT_INDEX_MASK) <= MAX_LEGENDARY_QUEUE)
            state++;    // index lives in the low bits, so this is safe
        gSaveBlock1Ptr->legendarySlots[slot] = state;
    }
}

// Gives the next event ticket the player is missing. Returns the item in
// VAR_RESULT, or ITEM_NONE when all three have been handed out.
void GiveNextEventTicket(void)
{
    u8 i;

    gSpecialVar_Result = ITEM_NONE;
    for (i = 0; i < ARRAY_COUNT(sEventTickets); i++)
    {
        if (FlagGet(sEventTickets[i][1]))
            continue;
        if (!AddBagItem(sEventTickets[i][0], 1))
            return;     // no room; try again after the next Champion win
        FlagSet(sEventTickets[i][1]);
        gSpecialVar_Result = sEventTickets[i][0];
        return;
    }
}
