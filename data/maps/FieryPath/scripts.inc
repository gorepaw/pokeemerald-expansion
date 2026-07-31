FieryPath_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, FieryPath_OnTransition
	.byte 0

FieryPath_OnTransition:
	call_if_unset FLAG_LANDMARK_FIERY_PATH, FieryPath_EventScript_MoveScottToFallarbor
	setflag FLAG_LANDMARK_FIERY_PATH
	setvar VAR_0x8004, LEGENDARY_SLOT_FIERY_PATH
	special UpdateLegendarySlot
	call_if_unset FLAG_EP_FOUGHT_ENTEI, FieryPath_EventScript_ShowEntei
	end

FieryPath_EventScript_MoveScottToFallarbor::
	setflag FLAG_HIDE_VERDANTURF_TOWN_SCOTT
	clearflag FLAG_HIDE_FALLARBOR_TOWN_BATTLE_TENT_SCOTT
	return


@ emerald+: rotating legendary slot. The shared encounter does the work.
FieryPath_EventScript_LegendarySlot::
	setvar VAR_0x8004, LEGENDARY_SLOT_FIERY_PATH
	goto EventScript_LegendarySlotEncounter
	end

@ emerald+: ENTEI - one of the five Gen 1-3 legendaries with nowhere to be
@ caught. Once it is resolved this spot becomes a rotating slot.
FieryPath_EventScript_Entei::
	lock
	faceplayer
	setwildbattle SPECIES_ENTEI, 70
	waitse
	playmoncry SPECIES_ENTEI, CRY_MODE_ENCOUNTER
	delay 40
	waitmoncry
	playbgm MUS_RG_ENCOUNTER_GYM_LEADER, 0
	waitbuttonpress
	setflag FLAG_SYS_CTRL_OBJ_DELETE
	special BattleSetup_StartLegendaryBattle
	clearflag FLAG_SYS_CTRL_OBJ_DELETE
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_eq VAR_RESULT, B_OUTCOME_WON, FieryPath_EventScript_EnteiDefeated
	goto_if_eq VAR_RESULT, B_OUTCOME_RAN, FieryPath_EventScript_EnteiFled
	goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, FieryPath_EventScript_EnteiFled
	setflag FLAG_EP_FOUGHT_ENTEI
	release
	end

FieryPath_EventScript_EnteiDefeated::
	setflag FLAG_EP_FOUGHT_ENTEI
	goto EventScript_RemoveStaticMon
	end

FieryPath_EventScript_EnteiFled::
	setvar VAR_0x8004, SPECIES_ENTEI
	goto EventScript_MonFlewAway
	end

FieryPath_EventScript_ShowEntei::
	clearflag FLAG_EP_HIDE_ENTEI
	return
