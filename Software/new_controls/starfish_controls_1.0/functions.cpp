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

    parseCommand(commandInput, commandListLength); // Function parses the command and ensures it is valid

  }

}


void parseCommand(String commandInput, int commandListLength) {

  for (int i = 0; i < commandListLength; i++) { // Cycles through command list to ensure input is valid

    if (commandInput == commandInputList[i]){

      storedCommand = commandInput;
      acceptedInputCounter += 1; // reset condition helper

    }
  }

  if (acceptedInputCounter == 0){

    Serial.println("Invalid Command"); // if a valid command is not found, prints "invalid command"
  }

  acceptedInputCounter = 0; // resets command detected condition for next loop
}


void runCommand(String storedCommand) {
  for (int i = 0; i < commandDictSize; i++) { // loops through commandDict struct to activate proper pin with PWM

    if (commandDict[i].name == storedCommand) { 
      Serial.println(storedCommand);
      analogWrite(commandDict[i].pin, analogDutyCycle); // analogDutyCycle gives the proper analog output for PWM control
      delay(delayTime);

      return; // Exit the function once the command is found
    }
  }
}