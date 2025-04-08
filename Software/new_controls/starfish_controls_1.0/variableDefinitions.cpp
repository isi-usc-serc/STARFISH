#include <Arduino.h>
#include "variables.h"
#include "functionPrototypes.h"

const int arm_a[4] = {2, 3, 4, 5}; // pins numbers for arm a
const int arm_b[4] = {6, 7, 8, 9}; // pins numbers for arm b
const int arm_c[4] = {10, 11, 12, 13}; // pins numbers for arm c
const int arm_d[4] = {44, 45, 46, 47}; // pins numbers for arm d

const int dutyCycle = 100; // desired duty cycle (as a percent)
const int delayTime = 5000; // desired actuation time
int analogDutyCycle = (dutyCycle / 100) * 255; // duty cycle (for analog output out of 255)

String commandInput; // reads serial input
String storedCommand; // stores user inputted command when a valid command is entered
const String commandInputList[] = {"a1", "a2", "a3", "a4", "b1", "b2", "b3", "b4", "c1", "c2", "c3", "c4", "d1", "d2", "d3", "d4"}; // array for checking for valid command (might remove due to new functionality)
int commandListLength = sizeof(commandInputList) / sizeof(commandInputList[0]); // length of command input list for iteration
int acceptedInputCounter = 0; // reset counter for command inputs

CommandStruct commandDict[] = { // dictionary (structure) mapping pin numbers to user input commands
  {"a1", 2}, {"a2", 3}, {"a3", 4}, {"a4", 5},
  {"b1", 6}, {"b2", 7}, {"b3", 8}, {"b4", 9},
  {"c1", 10}, {"c2", 11}, {"c3", 12}, {"c4", 13},
  {"d1", 44}, {"d2", 45}, {"d3", 46}, {"d4", 47}
};

const int commandDictSize = sizeof(commandDict) / sizeof(commandDict[0]); // length of command dictionary