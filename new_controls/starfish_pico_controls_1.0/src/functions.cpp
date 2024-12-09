#include <Arduino.h>
#include "variables.h"
#include "functionPrototypes.h"


void pinActivate() {

  for (int i = 0; i < 4; i++) {
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

    splitString(commandInput, delimiter, commandInputList, commandInputListLength); // Splits the input string into an array

    parseCommand(commandInputList, commandListLength); // Function parses the command and ensures it is valid

  }

}


void parseCommand(String commandInputList[], int commandListLength) {

  alternativeInvalidChecker();

  for (int j = 0; j < commandInputListLength; j++) {

    for (int i = 0; i < commandListLength; i++) { // Cycles through command list to ensure input is valid

      if (commandInputList[j] == commandList[i]){

        acceptedInputCounter++;

      }
      else {

        acceptedInputCounter--;

      }

      if (acceptedInputCounter == -commandListLength) {
        acceptedInputCounter = 0;

        invalidCommandList[invalidCounter] = commandInputList[j];
        invalidCounter++;

      }

    }
    acceptedInputCounter = 0;
  }

  if (invalidCounter > 0){
    invalidDeclaration();
  }
  else{
    validCondition = true;
  }
}

void runCommand(String commandInputList[]) {
  if (validCondition == false) {

    return;
  }
  else {
    for (int i = 0; i < commandDictSize; i++) { // loops through commandDict struct to activate proper pin with PWM

      for (int j = 0; j < commandInputListLength; j++) {

        if (commandDict[i].name == commandInputList[j]) { 

          // Serial.println(commandDict[i].name);
          analogWrite(commandDict[i].pin, analogDutyCycle); // analogDutyCycle gives the proper analog output for PWM control

        }
      }
    }
  }

  Serial.print("Command(s) Executing: ");
  for (int i = 0; i < commandInputListLength; i++) {
      if (commandInputList[i] != "") {

        Serial.print(commandInputList[i]);
        Serial.print(", ");

      }
    }
  Serial.println();

  delay(delayTime); // delay for actuation time
  for (int i = 0; i < commandDictSize; i++) {
    analogWrite(commandDict[i].pin, 0); // deactivates the pin after the delay
  }

  if (validCondition == true) {
    Serial.println("Commands Completed");
    Serial.println();
  }
  
  resetVariables(); // resets variables for next command
  return; // Exit the function once the command is found
}

void resetVariables() {
  commandInput = "";
  storedCommand = "";
  acceptedInputCounter = 0;
  validCondition = false;
  for (int i = 0; i < commandInputListLength; ++i) {
    commandInputList[i] = "";
  }
  for (int i = 0; i < commandListLength; ++i) {
    invalidCommandList[i] = "";
  }
  invalidCounter = 0;
}

void splitString(String& commandInput, char delimiter, String commandInputList[], int& commandInputListLength) {
  int index = 0;
  int temp = commandInput.length() + 1;
  char input[temp];
  commandInput.toCharArray(input, commandInput.length() + 1); // Convert String to char array
  
  char delimiterStr[] = {delimiter, '\0'}; // Convert delimiter to char array
  char* token = strtok(input, delimiterStr); // Get the first token
  while (token != nullptr) {
    commandInputList[index++] = String(token); // Convert token back to String and store in result array
    token = strtok(nullptr, delimiterStr); // Get the next token
  }
  commandInputListLength = index; // Update size with the number of tokens found

  // for (int i = 0; i < commandInputListLength; i++) { // Print the results
  //   Serial.println(commandInputList[i]);
  // }
}

void initializationScript(){
  if (Serial.available()) {
    if (initVar == false){;
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

void alternativeInvalidChecker(){
  if (commandInputListLength <= 0){ // Checks for a blank command input
    invalidCounter++;
    blankCounter++;
  }

  for (int j = 0; j < commandInputListLength; j++) { // Checks for duplicates in the command input
    for (int k = j + 1; k < commandInputListLength; k++) {
      if (commandInputList[j] == commandInputList[k]) {

        invalidCommandList[invalidCounter] = commandInputList[j];
        invalidCounter++;
        dupeCounter++;
      }
    }
  }
}

void invalidCommandPrinter(){
  for (int i = 0; i < commandListLength; i++) {
    if (invalidCommandList[i] != "") {

      if (commaCounter == 1){
        Serial.print(", ");
      }
      Serial.print(invalidCommandList[i]);
      if (commaCounter > 0){
        Serial.print(", ");
      }
      commaCounter++;

    }
  }
}