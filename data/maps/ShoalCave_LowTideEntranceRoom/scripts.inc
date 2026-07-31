ShoalCave_LowTideEntranceRoom_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, ShoalCave_LowTideEntranceRoom_OnTransition
	.byte 0

ShoalCave_LowTideEntranceRoom_OnTransition:
	special UpdateShoalTideFlag
	goto_if_set FLAG_SYS_SHOAL_TIDE, ShoalCave_LowTideEntranceRoom_EventScript_SetHighTide
	setvar VAR_0x8004, LEGENDARY_SLOT_SHOAL_CAVE
	special UpdateLegendarySlot
	call_if_unset FLAG_EP_FOUGHT_SUICUNE, ShoalCave_LowTideEntranceRoom_EventScript_ShowSuicune
	goto ShoalCave_LowTideEntranceRoom_EventScript_SetLowTide

ShoalCave_LowTideEntranceRoom_EventScript_SetHighTide::
	setmaplayoutindex LAYOUT_SHOAL_CAVE_HIGH_TIDE_ENTRANCE_ROOM
	end

ShoalCave_LowTideEntranceRoom_EventScript_SetLowTide::
	setmaplayoutindex LAYOUT_SHOAL_CAVE_LOW_TIDE_ENTRANCE_ROOM
	end

ShoalCave_LowTideEntranceRoom_EventScript_ShellBellExpert::
	lock
	faceplayer
	dotimebasedevents
	call_if_set FLAG_SYS_SHOAL_ITEM, ShoalCave_LowTideEntranceRoom_EventScript_ResetShoalItems
	checkitem ITEM_SHOAL_SALT, 4
	goto_if_eq VAR_RESULT, FALSE, ShoalCave_LowTideEntranceRoom_EventScript_NotEnoughShoalSaltOrShells
	checkitem ITEM_SHOAL_SHELL, 4
	goto_if_eq VAR_RESULT, FALSE, ShoalCave_LowTideEntranceRoom_EventScript_NotEnoughShoalSaltOrShells
	msgbox ShoalCave_LowTideEntranceRoom_Text_WouldYouLikeShellBell, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, NO, ShoalCave_LowTideEntranceRoom_EventScript_DeclineShellBell
	checkitemspace ITEM_SHELL_BELL
	call_if_eq VAR_RESULT, FALSE, ShoalCave_LowTideEntranceRoom_EventScript_CheckSpaceWillBeFreed
	goto_if_eq VAR_RESULT, 2, ShoalCave_LowTideEntranceRoom_EventScript_NoRoomForShellBell
	msgbox ShoalCave_LowTideEntranceRoom_Text_MakeShellBellRightAway, MSGBOX_DEFAULT
	removeitem ITEM_SHOAL_SALT, 4
	removeitem ITEM_SHOAL_SHELL, 4
	giveitem ITEM_SHELL_BELL
	goto_if_eq VAR_RESULT, FALSE, Common_EventScript_ShowBagIsFull  @ Never FALSE, we already made sure there will be room in the bag.
	msgbox ShoalCave_LowTideEntranceRoom_Text_ExplainShellBell, MSGBOX_DEFAULT
	setflag FLAG_TEMP_2  @ Not read. Perhaps meant to stop him from re-explaining the Shell Bell if multiple are received in one sitting.
	release
	end

@ If the bag is full, check if a slot will be freed when 4 Shoal Salt or Shells are given
ShoalCave_LowTideEntranceRoom_EventScript_CheckSpaceWillBeFreed::
	checkitem ITEM_SHOAL_SALT, 5
	goto_if_eq VAR_RESULT, TRUE, ShoalCave_LowTideEntranceRoom_EventScript_CheckSpaceWillBeFreedShells
	return

ShoalCave_LowTideEntranceRoom_EventScript_CheckSpaceWillBeFreedShells::
	checkitem ITEM_SHOAL_SHELL, 5
	goto_if_eq VAR_RESULT, TRUE, ShoalCave_LowTideEntranceRoom_EventScript_NoSpaceWillBeFreed
	return

ShoalCave_LowTideEntranceRoom_EventScript_NoSpaceWillBeFreed::
	setvar VAR_RESULT, 2
	return

ShoalCave_LowTideEntranceRoom_EventScript_NoRoomForShellBell::
	msgbox ShoalCave_LowTideEntranceRoom_Text_NoSpaceInYourBag, MSGBOX_DEFAULT
	release
	end

ShoalCave_LowTideEntranceRoom_EventScript_NotEnoughShoalSaltOrShells::
	checkitem ITEM_SHOAL_SALT
	goto_if_eq VAR_RESULT, TRUE, ShoalCave_LowTideEntranceRoom_EventScript_HasSomeShoalSaltOrShell
	checkitem ITEM_SHOAL_SHELL
	goto_if_eq VAR_RESULT, TRUE, ShoalCave_LowTideEntranceRoom_EventScript_HasSomeShoalSaltOrShell
	msgbox ShoalCave_LowTideEntranceRoom_Text_AreYouPlanningOnGoingInThere, MSGBOX_DEFAULT
	release
	end

ShoalCave_LowTideEntranceRoom_EventScript_HasSomeShoalSaltOrShell::
	msgbox ShoalCave_LowTideEntranceRoom_Text_BringMe4ShoalSaltAndShells, MSGBOX_DEFAULT
	release
	end

ShoalCave_LowTideEntranceRoom_EventScript_DeclineShellBell::
	msgbox ShoalCave_LowTideEntranceRoom_Text_WantedToMakeShellBell, MSGBOX_DEFAULT
	release
	end

ShoalCave_LowTideEntranceRoom_EventScript_ResetShoalItems::
	clearflag FLAG_RECEIVED_SHOAL_SALT_1
	clearflag FLAG_RECEIVED_SHOAL_SALT_2
	clearflag FLAG_RECEIVED_SHOAL_SALT_3
	clearflag FLAG_RECEIVED_SHOAL_SALT_4
	clearflag FLAG_RECEIVED_SHOAL_SHELL_1
	clearflag FLAG_RECEIVED_SHOAL_SHELL_2
	clearflag FLAG_RECEIVED_SHOAL_SHELL_3
	clearflag FLAG_RECEIVED_SHOAL_SHELL_4
	clearflag FLAG_SYS_SHOAL_ITEM
	return

@ emerald+: rotating legendary slot. The shared encounter does the work.
ShoalCave_LowTideEntranceRoom_EventScript_LegendarySlot::
	setvar VAR_0x8004, LEGENDARY_SLOT_SHOAL_CAVE
	goto EventScript_LegendarySlotEncounter
	end

@ emerald+: SUICUNE - one of the five Gen 1-3 legendaries with nowhere to be
@ caught. Once it is resolved this spot becomes a rotating slot.
ShoalCave_LowTideEntranceRoom_EventScript_Suicune::
	lock
	faceplayer
	setwildbattle SPECIES_SUICUNE, 70
	waitse
	playmoncry SPECIES_SUICUNE, CRY_MODE_ENCOUNTER
	delay 40
	waitmoncry
	playbgm MUS_RG_ENCOUNTER_GYM_LEADER, 0
	waitbuttonpress
	setflag FLAG_SYS_CTRL_OBJ_DELETE
	special BattleSetup_StartLegendaryBattle
	clearflag FLAG_SYS_CTRL_OBJ_DELETE
	specialvar VAR_RESULT, GetBattleOutcome
	goto_if_eq VAR_RESULT, B_OUTCOME_WON, ShoalCave_LowTideEntranceRoom_EventScript_SuicuneDefeated
	goto_if_eq VAR_RESULT, B_OUTCOME_RAN, ShoalCave_LowTideEntranceRoom_EventScript_SuicuneFled
	goto_if_eq VAR_RESULT, B_OUTCOME_PLAYER_TELEPORTED, ShoalCave_LowTideEntranceRoom_EventScript_SuicuneFled
	setflag FLAG_EP_FOUGHT_SUICUNE
	release
	end

ShoalCave_LowTideEntranceRoom_EventScript_SuicuneDefeated::
	setflag FLAG_EP_FOUGHT_SUICUNE
	goto EventScript_RemoveStaticMon
	end

ShoalCave_LowTideEntranceRoom_EventScript_SuicuneFled::
	setvar VAR_0x8004, SPECIES_SUICUNE
	goto EventScript_MonFlewAway
	end

ShoalCave_LowTideEntranceRoom_EventScript_ShowSuicune::
	clearflag FLAG_EP_HIDE_SUICUNE
	return
