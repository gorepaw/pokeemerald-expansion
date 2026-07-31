@ emerald+: the rotating legendary slots.
@
@ One shared encounter rather than nineteen copies. Each host map carries only a
@ trampoline that names its slot; everything below is common. The slot is saved
@ in C when the battle is set up, so nothing has to survive the battle in a var.

EventScript_LegendarySlotEncounter::
	lock
	faceplayer
	special SetUpLegendarySlotBattle
	goto_if_eq VAR_RESULT, SPECIES_NONE, EventScript_LegendarySlotEmpty
	waitse
	special PlayLegendarySlotCry
	delay 40
	waitmoncry
	playbgm MUS_RG_ENCOUNTER_GYM_LEADER, 0
	waitbuttonpress
	setflag FLAG_SYS_CTRL_OBJ_DELETE
	special BattleSetup_StartLegendaryBattle
	clearflag FLAG_SYS_CTRL_OBJ_DELETE
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_eq VAR_RESULT, B_OUTCOME_WON, EventScript_LegendarySlotDefeated
	goto_if_eq VAR_RESULT, B_OUTCOME_RAN, EventScript_LegendarySlotFled
	goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, EventScript_LegendarySlotFled
	@ fallthrough: caught
	special ArmLegendarySlot
	release
	end

EventScript_LegendarySlotDefeated::
	special ArmLegendarySlot
	goto EventScript_RemoveStaticMon
	end

EventScript_LegendarySlotFled::
	release
	end

EventScript_LegendarySlotEmpty::
	release
	end
