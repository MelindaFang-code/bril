#include <stdio.h>

double mult (double a, double b) {
    return a * b;
}

void tester(double num1, double num2) {
    double num3;
    num2 = mult(num1, num2);
    num2 = num1 * num2;
    printf("%lf\n", num2);
    num3 = num2 + num1;
    printf("%lf\n", num3);
    num3 = num3 / num2;
    printf("%lf\n", num3);
    num3 = num3 - num1;
    printf("%lf\n", num3);
}

int main()
{
    double num1 = 10.0;
    double num2 = 12.0;
    double num3;
    printf("%lf, %lf\n", num1, num2);
    tester(num1, num2);

    return 0;
}
