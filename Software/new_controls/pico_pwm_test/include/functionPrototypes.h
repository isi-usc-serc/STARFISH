#ifndef functionPrototypes_h
#define functionPrototypes_h

void pinActivate();
void readInput();
void parseCommand(std::vector<String>& commandInputList);
void coilActuation();
void coilDeactivation();
void runCommand(std::vector<String>& commandInputList);
void resetVariables();

void splitString(String& commandInput, char delimiter, std::vector<String>& commandInputList);

void initializationScript();
void invalidDeclaration();
void alternativeInvalidChecker();
void invalidCommandPrinter();

String trim(const String& str);

void preRunCheck();
void commandExecution(std::vector<String>& commandInputList);
void activatePWM(int pin, int dutyCycle, int pinIndex, int totalPins);
void deactivatePWM(int pin);



#endif