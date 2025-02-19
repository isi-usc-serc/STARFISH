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


void readInput() {
    if (Serial.available() > 0) {
        commandInput = Serial.readStringUntil('\n');
        commandInput.trim();  // Remove any whitespace
        
        // Clear previous command list
        commandInputList.clear();
        invalidCommandList.clear();
        validCondition = false;  // Reset validation flag
        
        // Only process if there's actual input
        if (commandInput.length() > 0) {
            splitString(commandInput, delimiter, commandInputList);
            parseCommand(commandInputList);
        }
    }
}


void parseCommand(std::vector<String>& commandInputList) {
  // Check for blank/duplicate commands first
  alternativeInvalidChecker();
  if (invalidCounter > 0) {
    invalidDeclaration();
    return;
  }

  std::unordered_set<std::string> commandSet;
  for (const auto& cmd : commandList) {
      commandSet.insert(std::string(cmd.c_str()));
  }
    invalidCommandList.clear();  // Clear invalid command list

  for (const auto& command : commandInputList) {
    if (commandSet.find(std::string(command.c_str())) == commandSet.end()) {
      invalidCommandList.push_back(command);
      }
  }

  validCondition = invalidCommandList.empty();
  if (!validCondition) {
      invalidDeclaration();
  }
}

void runCommand(std::vector<String>& commandInputList) {
    static bool isExecuting = false;
    
    // Prevent double execution
    if (isExecuting) {
        return;
    }
    
    isExecuting = true;
    
    // Regular command execution
    preRunCheck();
    
    for (const auto& pair : commandDict) {
        commandMap[std::string(pair.first.c_str())] = pair.second;
    }

    commandExecution(commandInputList);
    
    resetVariables();
    isExecuting = false;
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
  invalidCounter = 0;
  commaCounter = 0;
  blankCounter = 0;
  dupeCounter = 0;
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
  commandCount.clear();  // Add this line at the start of the function

  if (commandInputList.empty()) { // Checks for a blank command input
      invalidCounter++;
      blankCounter++;
  }


  for (const auto& command : commandInputList) {
      commandCount[std::string(command.c_str())]++;
  }

  for (const auto& entry : commandCount) {
      if (entry.second > 1) {  // If command appears more than once, it's a duplicate
        invalidCommandList.push_back(String(entry.first.c_str()));  // ✅ Convert std::string → Arduino String
        dupeCounter++;  // Increment only once per duplicate command type
          invalidCounter++;
      }
  }
}

void invalidCommandPrinter() {
  for (size_t i = 0; i < invalidCommandList.size(); i++) {
      Serial.print(invalidCommandList[i]);
      if (i < invalidCommandList.size() - 1) {
          Serial.print(", ");
      }
  }
}


void preRunCheck(){
  if (commandInputList.empty()) return;

  // Ensure the command list is not too large
  if (commandInputList.size() > 16) {
    Serial.println("Error: Too many commands");
    return;
  }

  // If there are invalid commands, do not proceed
  if (!validCondition) return;
  
}

void commandExecution(std::vector<String>& commandInputList) {
  int totalPins = commandInputList.size();
  std::vector<PinState> activeStates;
  
  // Initialize all pin states
  for (const auto& command : commandInputList) {
    if (commandMap.find(std::string(command.c_str())) != commandMap.end()) {
      int pin = commandMap[std::string(command.c_str())];
      if (pin >= 0 && pin <= MAX_PIN_NUMBER) {
        PinState pinState = {pin, 0, false};
        activeStates.push_back(pinState);
      }
    }
  }

  Serial.print("Executing Commands: ");
  
  unsigned long lastCheckTime = 0;
  const unsigned long CHECK_INTERVAL = 100;  // Check every 100ms
  
  // Start the first two pins
  unsigned long startTime = millis();
  int activeCount = 0;
  int pinIndex = 0;
  
  // Initial activation of up to 2 pins
  for (int i = 0; i < min(2, (int)activeStates.size()); i++) {
    activeStates[i].startTime = startTime;
    activeStates[i].isActive = true;
    activatePWM(activeStates[i].pin, analogDutyCycle, pinIndex++, totalPins);
    activeCount++;
  }

  // Main control loop
  while (!activeStates.empty()) {
    unsigned long currentTime = millis();
    
    // Only process updates at regular intervals
    if (currentTime - lastCheckTime >= CHECK_INTERVAL) {
      lastCheckTime = currentTime;
      
      // Process active pins
      for (auto& pinState : activeStates) {
        unsigned long elapsedTime = currentTime - pinState.startTime;
        if (pinState.isActive && elapsedTime >= static_cast<unsigned long>(delayTime)) {
          deactivatePWM(pinState.pin);
          pinState.isActive = false;
          activeCount--;
        }
      }
      
      // Activate new pins if we have less than 2 active
      for (auto& pinState : activeStates) {
        if (!pinState.isActive && activeCount < 2) {
          pinState.startTime = currentTime;
          pinState.isActive = true;
          activatePWM(pinState.pin, analogDutyCycle, pinIndex++, totalPins);
          activeCount++;
        }
      }
      
      // Remove completed pins
      activeStates.erase(
        std::remove_if(activeStates.begin(), activeStates.end(),
          [currentTime](const PinState& pinState) {
            return !pinState.isActive && 
                   (currentTime - pinState.startTime >= static_cast<unsigned long>(delayTime));
          }
        ),
        activeStates.end()
      );
    }
    
    // Let other tasks run
    yield();  // On platforms that support it
  }

  Serial.println("\nCommands Completed");
}

bool isValidPin(int pin) {
    return pin >= 0 && pin < MAX_PIN_NUMBER;
}

void activatePWM(int pin, int dutyCycle, int pinIndex, int totalPins) {
    if (!isValidPin(pin)) return;
    analogWrite(pin, dutyCycle);
}

void deactivatePWM(int pin) {
    if (!isValidPin(pin)) return;
    analogWrite(pin, 0);
}