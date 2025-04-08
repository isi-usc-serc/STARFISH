#include <Arduino.h>
#include "variables.h"
#include "functionPrototypes.h"

void setup() {
Serial.begin(9600);

delay(1000);
pinActivate();
initializationScript();

}

void loop() {
  readInput();
  // Only run commands if there are actually commands to process
  if (!commandInputList.empty() && validCondition) {
    runCommand(commandInputList);
  }
}
