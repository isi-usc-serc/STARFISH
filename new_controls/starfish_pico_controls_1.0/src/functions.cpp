#include <Arduino.h>
#include "variables.h"
#include "functionPrototypes.h"
#include <algorithm>
#include <unordered_set>
#include <vector>
#include <string>
#include <unordered_map>

void pinActivate() {
  // Add pin validation
  for (int i = 0; i < 4; i++) {
    // Validate pin numbers before setting mode
    if (arm_a[i] >= MAX_PIN_NUMBER || arm_b[i] >= MAX_PIN_NUMBER || 
        arm_c[i] >= MAX_PIN_NUMBER || arm_d[i] >= MAX_PIN_NUMBER) {
      Serial.println("Error: Invalid pin number detected");
      return;
    }
    
    pinMode(arm_a[i], OUTPUT);
    pinMode(arm_b[i], OUTPUT);
    pinMode(arm_c[i], OUTPUT);
    pinMode(arm_d[i], OUTPUT);
  }
}


void readInput(){
  if (Serial.available()) {
    commandInput = Serial.readStringUntil('\n'); // Reads input string
    commandInput.trim(); // Trims out the whitespace from the input string

    Serial.print("Command(s) Input: ");
    Serial.println(commandInput);

    splitString(commandInput, delimiter, commandInputList); // Splits the input string into an array

    parseCommand(commandInputList); // Function parses the command and ensures it is valid
  }
}


void parseCommand(std::vector<String>& commandInputList) {
  // Reset all counters and lists at the start
  invalidCommandList.clear();
  invalidCounter = 0;
  blankCounter = 0;
  dupeCounter = 0;

  // Check for blank/duplicate/invalid commands
  alternativeInvalidChecker();
  if (invalidCounter > 0) {
    invalidDeclaration();
    return;
  }
  
  std::unordered_set<std::string> commandSet;
  for (const auto& cmd : commandList) {
      commandSet.insert(std::string(cmd.c_str()));
  }

  for (const auto& command : commandInputList) {
    if (commandSet.find(std::string(command.c_str())) == commandSet.end()) {
      invalidCommandList.push_back(command);
      invalidCounter++;  // Increment counter for each invalid command
    }
  }

  validCondition = invalidCommandList.empty();
  if (!validCondition) {
    invalidDeclaration();
  }
}


void runCommand(std::vector<String>& commandInputList) {
  // preCommandCheck();
  
  // If there are invalid commands, do not proceed
  if (!validCondition){
    return;
  }

  // Convert command dictionary to an unordered_map for fast lookup
  for (const auto& pair : commandDict) {
    commandMap[std::string(pair.first.c_str())] = pair.second;
  }

  commandExecution();

  commandDeactivation();
  
  Serial.println("Commands Completed\n");
  
  resetVariables();

}


void resetVariables() {
  // Ensure all pins are set to zero before resetting
  for (int i = 0; i < 16; i++) {
      analogWrite(i, 0);
  }
  
  // Clear all containers safely
  commandInputList.clear();
  invalidCommandList.clear();
  
  // Reset all flags and counters
  commandInput = "";
  storedCommand = "";
  acceptedInputCounter = 0;
  validCondition = false;
  commaCounter = 0;
}


void splitString(String& commandInput, char delimiter, std::vector<String>& commandInputList) {
  commandInputList.clear();  // Ensure the vector is empty before adding new elements
  int temp = commandInput.length() + 1;

  // Add size check to prevent buffer overflow
  if (temp > 256) { // Or whatever maximum size is appropriate
    Serial.println("Error: Input command too long");
    return;
  }
  
  // Use a vector for safe memory allocation
  std::vector<char> input(temp);

  // Copy the command input to the input vector
  strncpy(input.data(), commandInput.c_str(), temp);
  input[temp - 1] = '\0';

  // Create a delimiter string
  char delimiterStr[] = {delimiter, '\0'};

  // Tokenize the input string
  char* token = strtok(input.data(), delimiterStr);
  while (token != nullptr) {
    commandInputList.push_back(String(token));  // Use push_back to dynamically add elements
    token = strtok(nullptr, delimiterStr);
  }
}


void initializationScript(){
  if (Serial.available()) {
    if (initVar == false){
      Serial.println("Initilization Complete");
      Serial.println("Enter a command when ready:\n");
      initVar = true;
    }
  }
}


void invalidDeclaration(){ // All the serial printing for the invalid commands
  validCondition = false;
  if (blankCounter > 0){ // Blank command print
    validCondition = false;
    Serial.print("No Commands Entered");
    blankCounter = 0;
  }

  else if (dupeCounter > 0){ // Duplicate command print

    validCondition = false;
    Serial.println("Duplicate Commands Entered");
    Serial.print("Invalid Command(s): ");
    invalidCommandPrinter();
    dupeCounter = 0;
  }

  else{ // All other regular invalid command print statements

    Serial.print("Invalid Command(s): ");
    invalidCommandPrinter();
  }

  Serial.println("\n");
  Serial.println("Please re-enter commands:\n");
  commaCounter = 0;
}


void alternativeInvalidChecker() {
  commandCount.clear();
  invalidCommandList.clear();
  invalidCounter = 0;
  blankCounter = 0;
  dupeCounter = 0;

  if (commandInputList.empty()) {
    invalidCounter++;
    blankCounter++;
    return;  // Exit early if empty
  }

  std::unordered_set<std::string> commandSet;
  for (const auto& cmd : commandList) {
    commandSet.insert(std::string(cmd.c_str()));
  }

  for (const auto& command : commandInputList) {
    std::string commandStr = std::string(command.c_str());
    commandCount[commandStr]++;
    if (commandSet.find(commandStr) == commandSet.end()) {
      invalidCommandList.push_back(command);
      invalidCounter++;
    }
  }

  for (const auto& entry : commandCount) {
    if (entry.second > 1) {  // If command appears more than once, it's a duplicate
      invalidCommandList.push_back(String(entry.first.c_str()));
      dupeCounter++;  // Increment only once per duplicate command type
      invalidCounter++;
    }
  }
  // Serial.println(blankCounter);
  // Serial.println(dupeCounter);
  // Serial.println(invalidCounter);
}


void invalidCommandPrinter() {

  if (invalidCommandList.size() == 1) {

    Serial.print(invalidCommandList[0]);
  }
  else {
    for (size_t i = 0; i < invalidCommandList.size(); i++) {

      Serial.print(invalidCommandList[i]);
      if (i < invalidCommandList.size() - 1) {

        Serial.print(", ");
      }
    }
  }
}


void preCommandCheck(){
  
  // If there are invalid commands, do not proceed
  if (!validCondition){
    Serial.println("Error: Invalid command(s) detected");
    return;
  }

  if (commandInputList.empty()){
    validCondition = false;
    Serial.println("Error: No commands entered");
    return;
    }

  // Ensure the command list is not too large
  if (commandInputList.size() > 16) {
    validCondition = false;
    Serial.println("Error: Too many commands");
    return;
  }

}


void commandExecution(){
  Serial.print("Executing Commands: ");
  
  // Track valid commands for printing
  bool firstCommand = true;
  for (const auto& command : commandInputList) {
    // Check if command exists in the dictionary
    if (commandMap.find(std::string(command.c_str())) != commandMap.end()) {
      int pin = commandMap[std::string(command.c_str())];

      // Pin validation
      if (pin < 0 || pin > MAX_PIN_NUMBER) {
        Serial.print("Error: Invalid pin ");
        Serial.println(pin);
        continue;
      }

      // Execute command
      analogWrite(pin, analogDutyCycle);
      
      // Print command with appropriate separator
      if (!firstCommand) {
        Serial.print(", ");
      }
      Serial.print(command);
      firstCommand = false;
    }
  }
  Serial.println();

  delay(delayTime);
}


void commandDeactivation(){
  
  // **Deactivate all pins safely**
  for (const auto& cmd : commandMap) {

    int pin = cmd.second;
    if (pin >= 0 && pin <= MAX_PIN_NUMBER) {  // Validate before setting
      
      analogWrite(pin, 0);
    }
  }
}