#include <Arduino.h>
#include "variables.h"
#include "functionPrototypes.h"
#include <vector>
#include <string>
#include <unordered_map>

// System constants
constexpr int MAX_PIN_NUMBER = 16; // 28 pins on the pico, but only 16 are used

// Pin configurations
constexpr int arm_a[4] = {0, 1, 2, 3}; // pins numbers for arm a
constexpr int arm_b[4] = {4, 5, 6, 7}; // pins numbers for arm b
constexpr int arm_c[4] = {8, 9, 10, 11}; // pins numbers for arm c
constexpr int arm_d[4] = {12, 13, 14, 15}; // pins numbers for arm d

// Control parameters
const int dutyCycle = 50; // desired duty cycle (as a percent)
const int delayTime = 1000; // desired actuation time
int analogDutyCycle = (dutyCycle > 0 && dutyCycle <= 100) ? 
                     static_cast<int>((dutyCycle / 100.0) * 255) : 0;

// Command related variables
String commandInput; // reads serial input
String storedCommand; // stores user inputted command when a valid command is entered
const std::vector<String> commandList = {"a1", "a2", "a3", "a4", "b1", "b2", "b3", "b4",
                                   "c1", "c2", "c3", "c4", "d1", "d2", "d3", "d4"};
int acceptedInputCounter = 0; // reset counter for command inputs

std::unordered_map<std::string, int> commandDict = {
    {"a1", 0}, {"a2", 1}, {"a3", 2}, {"a4", 3}, 
    {"b1", 4}, {"b2", 5}, {"b3", 6}, {"b4", 7},
    {"c1", 8}, {"c2", 9}, {"c3", 10}, {"c4", 11},
    {"d1", 12}, {"d2", 13}, {"d3", 14}, {"d4", 15}
};

const size_t commandDictSize = commandDict.size(); // length of command dictionary

// Control flags and counters
const char delimiter = ' '; // delimeter for parsing input string
bool validCondition = false; // condition for valid input

std::vector<String> commandInputList; // list of input commands
std::vector<String> invalidCommandList; // list of invalid commands

int invalidCounter = 0; // counter for invalid commands
bool initVar = false; // initialization variable for setup
int commaCounter = 0;
int blankCounter = 0;
int dupeCounter = 0;

std::unordered_map<std::string, int> commandCount;
std::unordered_map<std::string, int> commandMap;
