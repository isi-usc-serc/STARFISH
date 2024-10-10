#include <Arduino.h>
#include "variables.h"
#include "functionPrototypes.h"


void pinActivate() {

  for (int i = 0; i < 4; i++) {
    pinMode(arm1[i], OUTPUT);
    pinMode(arm2[i], OUTPUT);
    pinMode(arm3[i], OUTPUT);
    pinMode(arm4[i], OUTPUT);
  }

}

void readInput(){

  if (Serial.available()) {
    commandInput = Serial.readStringUntil('\n'); // Reads input string
    commandInput.trim(); // Trims out the whitespace from the input string

    // parseCommand(); // Function parses the command and ensures it is valid

    functionTest();
  }

}

void functionTest(){
  Serial.println("working as intended!");
}


void parseCommand() {
  // Want to set up like REACCH user input config
  // Based 
  Serial.println(1);
}