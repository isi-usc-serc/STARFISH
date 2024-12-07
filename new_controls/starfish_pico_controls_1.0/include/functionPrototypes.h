#ifndef functionPrototypes_h
#define functionPrototypes_h

void pinActivate();
void readInput();
void parseCommand(String commandInputList[], int commandListLength);
void coilActuation();
void coilDeactivation();
void runCommand(String commandInputList[]);
void resetVariables();

void splitString(String& commandInput, char delimiter, String commandInputList[], int& commandInputListSize);

void initializationScript();
void invalidDeclaration();

#endif