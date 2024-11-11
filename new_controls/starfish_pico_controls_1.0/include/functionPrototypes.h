#ifndef functionPrototypes_h
#define functionPrototypes_h

void pinActivate();
void readInput();
void parseCommand(String commandInput, int commandListLength);
void coilActuation();
void coilDeactivation();
void runCommand(String storedCommand);
void resetVariables();


#endif