#include <Arduino.h>
#include "variables.h"
#include "functionPrototypes.h"

const int arm_a[4] = {0, 1, 2, 3}; // pins numbers for arm a
const int arm_b[4] = {4, 5, 6, 7}; // pins numbers for arm b
const int arm_c[4] = {8, 9, 10, 11}; // pins numbers for arm c
const int arm_d[4] = {12, 13, 14, 15}; // pins numbers for arm d

const int dutyCycle = 100; // desired duty cycle (as a percent)
const int delayTime = 5000; // desired actuation time
int analogDutyCycle = (dutyCycle / 100) * 255; // duty cycle (for analog output out of 255)

String commandInput; // reads serial input
String storedCommand; // stores user inputted command when a valid command is entered
const String commandList[] = {"a1", "a2", "a3", "a4", "b1", "b2", "b3", "b4", "c1", "c2", "c3", "c4", "d1", "d2", "d3", "d4"}; // array for checking for valid command (might remove due to new functionality)
int commandListLength = sizeof(commandList) / sizeof(commandList[0]); // length of command input list for iteration
int acceptedInputCounter = 0; // reset counter for command inputs

CommandStruct commandDict[] = { // dictionary (structure) mapping pin numbers to user input commands
  {"a1", 0}, {"a2", 1}, {"a3", 2}, {"a4", 3},
  {"b1", 4}, {"b2", 5}, {"b3", 6}, {"b4", 7},
  {"c1", 8}, {"c2", 9}, {"c3", 10}, {"c4", 11},
  {"d1", 12}, {"d2", 13}, {"d3", 14}, {"d4", 15}
};
const int commandDictSize = sizeof(commandDict) / sizeof(commandDict[0]); // length of command dictionary

const char delimiter = ' '; // delimeter for parsing input string
bool validCondition = false; // condition for valid input

String commandInputList[] = { // list of invalid commands
  "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
};
int commandInputListLength = sizeof(commandInputList) / sizeof(commandInputList[0]); // length of command input list

String invalidCommandList[] = { // list of invalid commands
  "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
};

int invalidCounter = 0; // counter for invalid commands
bool initVar = false; // initialization variable for setup
int commaCounter = 0;
int blankCounter = 0;