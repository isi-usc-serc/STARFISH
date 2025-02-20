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

void preCommandCheck();
void commandExecution();
void commandDeactivation();

#endif