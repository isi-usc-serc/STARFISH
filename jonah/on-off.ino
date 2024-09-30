const int mosfetPin = 13;
int duty_cycle;

void setup() {
  pinMode (mosfetPin, OUTPUT);
  // put your setup code here, to run once:

}

void loop() {
 //for (int dutyCycle = 10; dutyCycle <= 100; dutyCycle += 10) {
    analogWrite (mosfetPin, 255); //(dutyCycle / 100.0) * 255);
    delay(5000); // wait 5s

//End current
    analogWrite (mosfetPin, 0);
    delay (10000); //Wait 5s before the next cycle
  }
  // put your main code here, to run repeatedly:
